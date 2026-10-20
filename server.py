import obspython as obs
import asyncio
import base64
import hashlib
import hmac
import json
import math
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import websockets

clients = set()

# The folders next to this script:
#   custom    the control panel asks what images are in it
#   rundowns  saved Podcast Rundowns (one .json file each), saved and opened from the control panel
#   logs      show logs (one .csv file each), from Generate Log in the control panel
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = obs.script_path()
CUSTOM_DIR = os.path.join(BASE_DIR, "custom")
RUNDOWN_DIR = os.path.join(BASE_DIR, "rundowns")
LOG_DIR = os.path.join(BASE_DIR, "logs")
IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".gif")

def custom_images():
    """Image files in the custom folder, sorted by name."""
    try:
        return sorted((f for f in os.listdir(CUSTOM_DIR) if f.lower().endswith(IMAGE_TYPES)), key=str.lower)
    except OSError:
        return []

def rundown_name(name):
    """A safe file name for a rundown (letters, numbers, spaces, _ - .), or None."""
    cleaned = re.sub(r"[^A-Za-z0-9 _.\-]", "", str(name or "")).strip().strip(".")[:60]
    return cleaned or None

def rundown_files():
    """Saved rundowns, newest first: name (without .json) and when it was saved."""
    try:
        files = [f for f in os.listdir(RUNDOWN_DIR) if f.lower().endswith(".json")]
    except OSError:
        return []
    found = [{"name": f[:-5], "saved": os.path.getmtime(os.path.join(RUNDOWN_DIR, f))} for f in files]
    return sorted(found, key=lambda f: f["saved"], reverse=True)

def answer_request(message):
    """Requests from the control panel that the server answers itself (only to that panel).
    Returns the reply, or None for everything else (graphics, which get passed on)."""
    try:
        request = json.loads(message)
    except ValueError:
        return None
    if not isinstance(request, dict):
        return None
    mode = request.get("mode")
    if mode == "customList":
        return {"mode": "customFiles", "files": custom_images()}
    if mode == "rundownList":
        return {"mode": "rundownFiles", "files": rundown_files()}
    if mode == "rundownSave":
        name = rundown_name(request.get("name"))
        if not name or not isinstance(request.get("data"), dict):
            return {"mode": "rundownSaved", "ok": False, "error": "Needs a name and a rundown"}
        try:
            os.makedirs(RUNDOWN_DIR, exist_ok=True)
            with open(os.path.join(RUNDOWN_DIR, name + ".json"), "w", encoding="utf-8") as f:
                json.dump(request["data"], f, indent=2, ensure_ascii=False)
        except OSError as e:
            return {"mode": "rundownSaved", "ok": False, "error": str(e)}
        return {"mode": "rundownSaved", "ok": True, "name": name}
    if mode == "logSave":
        name = rundown_name(request.get("name"))
        if not name or not isinstance(request.get("csv"), str):
            return {"mode": "logSaved", "ok": False, "error": "Needs a name and a log"}
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            with open(os.path.join(LOG_DIR, name + ".csv"), "w", encoding="utf-8-sig", newline="") as f:
                f.write(request["csv"])
        except OSError as e:
            return {"mode": "logSaved", "ok": False, "error": str(e)}
        return {"mode": "logSaved", "ok": True, "name": name}
    if mode == "rundownLoad":
        name = rundown_name(request.get("name"))
        try:
            with open(os.path.join(RUNDOWN_DIR, (name or "") + ".json"), encoding="utf-8") as f:
                return {"mode": "rundownData", "ok": True, "name": name, "data": json.load(f)}
        except (OSError, ValueError) as e:
            return {"mode": "rundownData", "ok": False, "error": f"Couldn't read {name}.json ({e.__class__.__name__})"}
    if mode == "obsScenes":
        # For picking break scenes (see "OBS scenes" below)
        return {"mode": "obsSceneList", "ok": True, "scenes": list(scene_names)}
    return None

# ---------------------------------------------------------------------------------------------
# AKTA break / return
#
# The control panel never holds the AKTA private key. It asks this server to start a break or a
# return, and this server signs the request and makes the call to AKTA itself. The settings (public
# key, private key, encoders) are kept in akta-config.json next to this script. Only this server ever
# reads the private key: no reply to the panel contains it, and it is never printed.
#
# Requests from the panel (the reply goes only to that panel):
#   aktaGet                      ->  aktaConfig        the saved settings, without the private key
#   aktaSave {config}            ->  aktaSaved         check and save the settings
#   aktaBreak {durationSeconds}  ->  aktaBreakResult   start a break on every enabled encoder
#   aktaReturn                   ->  aktaReturnResult  return from the break on every enabled encoder
# Any other mode starting with "akta" gets an aktaError reply (and is never passed on to the graphics).
# server.js does exactly the same, so the panel works with either server.
# ---------------------------------------------------------------------------------------------
AKTA_URL = os.environ.get("AKTA_URL") or "http://nexstar-mcp.mp.lura.live/api"
AKTA_CONFIG_FILE = os.environ.get("AKTA_CONFIG_PATH") or os.path.join(BASE_DIR, "akta-config.json")
AKTA_TIMEOUT = 8  # seconds, so an AKTA host that has gone quiet can't leave the panel waiting
AKTA_TEXT_MAX = 200
AKTA_ENCODERS_MAX = 20
AKTA_ID = re.compile(r"[A-Za-z0-9_.-]{1,40}")
AKTA_REPLY_MODES = {"aktaGet": "aktaConfig", "aktaSave": "aktaSaved", "aktaBreak": "aktaBreakResult", "aktaReturn": "aktaReturnResult"}
# AKTA requests are answered on worker threads, so this makes them take turns with the settings file
AKTA_FILE_LOCK = threading.RLock()

def akta_defaults():
    """What the settings are before anything has been saved."""
    return {"publicKey": "", "privateKey": "", "encoders": [], "waitForTransition": False, "delayMs": 0}

def akta_check(value):
    """Checks settings that came from the panel (or from the file). Returns (config, None) when they are fine,
    or (None, what is wrong). A blank private key is allowed here: when saving it means "keep the saved one"."""
    if not isinstance(value, dict):
        return None, "The settings are missing"

    keys = {}
    for name, label in (("publicKey", "Public key"), ("privateKey", "Private key")):
        text = value.get(name)
        if name == "privateKey" and text is None:
            text = ""
        if not isinstance(text, str):
            return None, f"{label} must be text"
        text = text.strip()
        if len(text) > AKTA_TEXT_MAX:
            return None, f"{label} is too long ({AKTA_TEXT_MAX} characters at most)"
        keys[name] = text

    found = value.get("encoders")
    if not isinstance(found, list):
        return None, "Encoders must be a list"
    if len(found) > AKTA_ENCODERS_MAX:
        return None, f"Too many encoders ({AKTA_ENCODERS_MAX} at most)"
    encoders = []
    for number, enc in enumerate(found, start=1):
        label = f"Encoder {number}"
        if not isinstance(enc, dict):
            return None, f"{label} is not valid"
        enc_id = enc.get("id")
        enc_id = enc_id.strip() if isinstance(enc_id, str) else ""
        # Only these characters, so an id can never break out of the XML it is put into
        if not AKTA_ID.fullmatch(enc_id):
            return None, f"{label} needs an id of 1 to 40 letters, numbers, _ - or ."
        scope = enc.get("scope")
        if scope != "local" and scope != "national":
            return None, f"{label} scope must be local or national"
        if not isinstance(enc.get("enabled"), bool):
            return None, f"{label} enabled must be true or false"
        encoders.append({"id": enc_id, "scope": scope, "enabled": enc["enabled"]})

    wait = value.get("waitForTransition")
    if not isinstance(wait, bool):
        return None, "waitForTransition must be true or false"
    delay = value.get("delayMs")
    if isinstance(delay, float) and delay.is_integer():
        delay = int(delay)  # 5.0 is still the whole number 5
    if isinstance(delay, bool) or not isinstance(delay, int) or delay < 0 or delay > 60000:
        return None, "delayMs must be a whole number from 0 to 60000"

    return {"publicKey": keys["publicKey"], "privateKey": keys["privateKey"], "encoders": encoders, "waitForTransition": wait, "delayMs": delay}, None

def akta_load():
    """The saved settings. A missing or damaged file counts as "nothing saved yet" (the next save replaces it)."""
    with AKTA_FILE_LOCK:
        try:
            with open(AKTA_CONFIG_FILE, encoding="utf-8-sig") as f:  # utf-8-sig also copes with a byte order mark at the start
                config, _ = akta_check(json.load(f))
        except Exception:
            return akta_defaults()
    return config or akta_defaults()

def akta_store(config):
    """Writes the settings so that, where the system supports it, only the account running OBS can read them.
    They go to a side file first and are then moved into place, so a crash can't leave half a file behind."""
    side = AKTA_CONFIG_FILE + ".tmp"
    try:
        os.makedirs(os.path.dirname(AKTA_CONFIG_FILE) or ".", exist_ok=True)
        if os.path.exists(side):
            os.remove(side)
        with os.fdopen(os.open(side, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8", newline="\n") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        os.replace(side, AKTA_CONFIG_FILE)
    except OSError:
        try:
            if os.path.exists(side):
                os.remove(side)
        except OSError:
            pass  # nothing more to clean up
        raise

def akta_masked(config):
    """The settings as the panel may see them: everything except the private key itself."""
    return {
        "publicKey": config["publicKey"],
        "hasPrivateKey": config["privateKey"] != "",
        "encoders": config["encoders"],
        "waitForTransition": config["waitForTransition"],
        "delayMs": config["delayMs"],
    }

def akta_save(value):
    """aktaSave: check the settings from the panel and, only if all of them are fine, save them."""
    with AKTA_FILE_LOCK:
        stored = akta_load()
        config, error = akta_check(value)
        if config is None:
            return {"mode": "aktaSaved", "ok": False, "error": error, "config": akta_masked(stored)}
        if config["privateKey"] == "":
            config["privateKey"] = stored["privateKey"]  # blank means keep the saved key
        try:
            akta_store(config)
        except OSError as e:
            return {"mode": "aktaSaved", "ok": False, "error": f"Couldn't save the AKTA settings ({e.__class__.__name__})", "config": akta_masked(stored)}
        return {"mode": "aktaSaved", "ok": True, "config": akta_masked(config)}

def akta_break_body(enc, seconds):
    """The XML AKTA wants for a break (a slate shown for the given number of seconds). The id and scope
    were checked when the settings were saved, so nothing in here can break out of the XML."""
    enc_id, scope = enc["id"], enc["scope"]
    return "\n".join([
        '<?xml version="1.0"?>',
        "<request>",
        "    <type>cue_stream</type>",
        "    <params>",
        f"        <encoder_id>{enc_id}</encoder_id>",
        f'        <cue type="break" scope="{scope}"></cue>',
        '        <content type="slate">',
        "            <slate_id>local-break</slate_id>",
        f"            <duration>{seconds}s</duration>",
        "        </content>",
        "    </params>",
        "</request>",
    ])

def akta_return_body(enc):
    """The XML AKTA wants for the return from a break."""
    enc_id = enc["id"]
    return "\n".join([
        '<?xml version="1.0"?>',
        "<request>",
        "    <type>cue_stream</type>",
        "    <params>",
        f"        <encoder_id>{enc_id}</encoder_id>",
        '        <cue type="return"></cue>',
        "    </params>",
        "</request>",
    ])

def akta_tag(answer, tag):
    """What is inside <tag>...</tag> in AKTA's answer (empty if it isn't there). Kept short because it goes to the panel."""
    found = re.search("<" + tag + "[^>]*>([^<]*)</" + tag + ">", answer, re.IGNORECASE)
    return found.group(1).strip()[:AKTA_TEXT_MAX] if found else ""

def akta_read(response):
    """The start of AKTA's answer as text (empty if it can't be read). Only a little of it is ever looked at."""
    try:
        return response.read(100000).decode("utf-8", errors="replace")
    except Exception:
        return ""

def akta_escape(text):
    """Makes text safe to put in a web address, the same way JavaScript's encodeURIComponent does."""
    return urllib.parse.quote(text, safe="!*'()~")

def akta_send(config, xml):
    """Signs and sends one call to AKTA. It never raises: the answer says what happened."""
    timestamp = int(time.time())
    # The signature covers exactly the text that is sent, plus the time
    digest = hmac.new(config["privateKey"].encode("utf-8"), (xml + str(timestamp)).encode("utf-8"), hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode("ascii")
    public_key = akta_escape(config["publicKey"])
    url = f"{AKTA_URL}?id={public_key}&ts={timestamp}&sgn={akta_escape(signature)}"
    try:
        request = urllib.request.Request(url, data=xml.encode("utf-8"), headers={"Content-Type": "application/xml"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=AKTA_TIMEOUT) as response:
                status = response.status
                answer = akta_read(response)
        except urllib.error.HTTPError as e:
            # AKTA did answer, but with an error status
            status = e.code
            answer = akta_read(e)
            e.close()
        sent = {"success": True} if 200 <= status < 300 else {"success": False, "error": f"HTTP {status}"}
        for tag in ("result", "status", "message"):
            found = akta_tag(answer, tag)
            if found:
                sent[tag] = found  # only these bits of the answer go on to the panel, never the whole thing
        return sent
    except Exception as e:
        # For a network problem urllib puts the real cause in .reason
        error = str(getattr(e, "reason", None) or e) or e.__class__.__name__
        # A mistyped AKTA_URL can put the signed address into the message: never pass the signature on
        error = error.replace(signature, "[hidden]").replace(akta_escape(signature), "[hidden]")
        return {"success": False, "error": error[:AKTA_TEXT_MAX]}

def akta_seconds(value):
    """A break length from the panel as whole seconds from 0 to 86400, or None when it isn't a usable number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        value = math.floor(value + 0.5)  # halves round up, the way JavaScript rounds
    return min(86400, max(0, value))

def akta_cue(kind, duration_seconds=None):
    """Starts a break (kind "break", for duration_seconds) or the return (kind "return") on every enabled
    encoder, one after another. ok is True only when at least one encoder was tried and all of them worked."""
    def failed(error):
        return {"ok": False, "error": error, "results": []}

    seconds = 0
    if kind == "break":
        seconds = akta_seconds(duration_seconds)
        if seconds is None:
            return failed("durationSeconds must be a number")
    config = akta_load()
    if not config["publicKey"] or not config["privateKey"]:
        return failed("Missing API Keys")
    encoders = [enc for enc in config["encoders"] if enc["enabled"]]
    if not encoders:
        return failed("No Akta encoders enabled")

    results = []
    for enc in encoders:
        sent = akta_send(config, akta_break_body(enc, seconds) if kind == "break" else akta_return_body(enc))
        results.append({"id": enc["id"], **sent})
    problems = [f"Encoder {r['id']}: {r['error']}" for r in results if not r["success"]]
    if problems:
        return {"ok": False, "error": "; ".join(problems), "results": results}
    return {"ok": True, "results": results}

def is_akta_request(request):
    """True for any request whose mode starts with "akta" (in any capitals). These are always answered here
    and never passed on to the other clients, so a mistyped mode can't leak the private key."""
    return isinstance(request, dict) and isinstance(request.get("mode"), str) and request["mode"].lower().startswith("akta")

def answer_akta(request):
    """The answer to an AKTA request. The call to AKTA waits on the network, so the server runs this on a worker thread."""
    reply_mode = AKTA_REPLY_MODES.get(request["mode"])
    if reply_mode is None:
        return {"mode": "aktaError", "ok": False, "error": "Unknown AKTA request"}
    try:
        if reply_mode == "aktaConfig":
            return {"mode": reply_mode, "ok": True, "config": akta_masked(akta_load())}
        if reply_mode == "aktaSaved":
            return akta_save(request.get("config"))
        kind = "break" if reply_mode == "aktaBreakResult" else "return"
        done = akta_cue(kind, request.get("durationSeconds"))
        if done["ok"]:
            print(f"FXWizard: AKTA {kind}: sent to {len(done['results'])} encoder(s)")
        else:
            print(f"FXWizard: AKTA {kind} problem: {done['error']}")
        return {"mode": reply_mode, **done}
    except Exception as e:
        reply = {"mode": reply_mode, "ok": False, "error": f"AKTA request failed ({e.__class__.__name__})"}
        if reply_mode.endswith("Result"):
            reply["results"] = []
        return reply

akta_tasks = set()  # keeps the AKTA calls that are in flight from being cleaned up before they finish

async def reply_akta(websocket, request):
    """Answers one AKTA request on a worker thread (the call to AKTA waits on the network) and sends the answer to the panel that asked."""
    akta_reply = await asyncio.get_running_loop().run_in_executor(None, answer_akta, request)
    try:
        await websocket.send(json.dumps(akta_reply))
    except Exception:
        pass  # the panel went away while the call to AKTA was in flight

async def socket_handler(websocket):
    clients.add(websocket)
    print(f"FXWizard: Client Connected. Total: {len(clients)}")
    try:
        async for message in websocket:
            # AKTA requests can carry the private key, so they are read first and answered here, only to the
            # panel that asked. They are never passed on to the other clients (and never printed).
            try:
                request = json.loads(message)
            except ValueError:
                request = None
            if is_akta_request(request):
                # Not awaited here, so a slow AKTA call never holds up the graphics commands from the same panel
                task = asyncio.get_running_loop().create_task(reply_akta(websocket, request))
                akta_tasks.add(task)
                task.add_done_callback(akta_tasks.discard)
                continue

            # The control panel asking for the custom images or a rundown file: answer only it
            reply = answer_request(message)
            if reply is not None:
                await websocket.send(json.dumps(reply))
                continue

            # BROADCAST LOGIC
            if clients:
                print(f"FXWizard: Broadcasting to {len(clients)} clients...")
                # We create a list from the set to prevent 'size changed' errors
                for client in list(clients):
                    try:
                        # Direct send; if the client is dead, it will trigger the except
                        await client.send(message)
                    except Exception:
                        # Clean up dead clients on the fly
                        clients.discard(client)
    except Exception as e:
        print(f"FXWizard Socket Error: {e}")
    finally:
        clients.discard(websocket)
        print(f"FXWizard: Client Disconnected. Total: {len(clients)}")

async def main_async_entry(host, port):
    async with websockets.serve(socket_handler, host, port):
        await asyncio.Future()  # Keep server alive

def start_server_thread(loop):
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_async_entry("0.0.0.0", 8080))
    except Exception as e:
        print(f"FXWizard Thread Error: {e}")

# ---------------------------------------------------------------------------------------------
# OBS hotkeys
#
# Three hotkeys (OBS Settings > Hotkeys) that make the control panel do something, so a break can be
# started or reset from a keyboard or a Stream Deck. The panel listens for
# {"mode": "timerCommand", "action": "start-break" | "reset-break" | "toggle-akta"}.
# ---------------------------------------------------------------------------------------------
HOTKEYS = (
    ("fxwizard_start_break", "FX Wizard: Start Break (next available)", "start-break"),
    ("fxwizard_reset_break", "FX Wizard: Reset Break (last triggered)", "reset-break"),
    ("fxwizard_toggle_akta", "FX Wizard: Toggle AKTA control", "toggle-akta"),
)
hotkey_ids = {}  # hotkey name -> the id OBS gave it
server_loop = None  # the event loop the server runs on (made in script_load)

async def broadcast(message):
    """Sends a message to every connected client, dropping any that have gone."""
    for client in list(clients):
        try:
            await client.send(message)
        except Exception:
            clients.discard(client)

def send_to_panels(data, what):
    """Sends a message to every connected client (the control panels act on it; the graphics ignore it)."""
    if server_loop is None:
        return
    try:
        # OBS calls hotkeys and its events from its own thread, so the message is handed over to the thread the server runs on
        asyncio.run_coroutine_threadsafe(broadcast(json.dumps(data)), server_loop)
    except Exception as e:
        print(f"FXWizard: Couldn't send the {what} ({e.__class__.__name__})")

def send_timer_command(action):
    """Tells every connected control panel to do something."""
    send_to_panels({"mode": "timerCommand", "action": action}, "hotkey command")

def make_hotkey_callback(action):
    def callback(pressed):
        if pressed:  # OBS calls this again when the key is let go
            send_timer_command(action)
    return callback

def register_hotkeys(settings):
    """Adds the hotkeys to OBS and gives them back the keys the user chose for them."""
    for name, description, action in HOTKEYS:
        try:
            hotkey_id = obs.obs_hotkey_register_frontend(name, description, make_hotkey_callback(action))
            hotkey_ids[name] = hotkey_id
            saved = obs.obs_data_get_array(settings, name)
            obs.obs_hotkey_load(hotkey_id, saved)
            obs.obs_data_array_release(saved)
        except Exception as e:
            print(f"FXWizard: Couldn't set up the hotkey {name} ({e.__class__.__name__})")

# ---------------------------------------------------------------------------------------------
# OBS scenes, for break scenes
#
# The control panel can start the next break when OBS goes to one of its break scenes. This script
# runs inside OBS, so it hears about it and tells every connected panel:
#   {"mode": "obsScene", "scene": "<name>"}   OBS went to that scene (its transition has started)
#   {"mode": "obsTransitionEnd"}             the transition has finished
# The panel's obsScenes request gets the scene names, for picking the break scenes.
# ---------------------------------------------------------------------------------------------
scene_names = []  # kept up to date on OBS's own thread, so the server never has to ask OBS from its thread
obs_busy = True   # while OBS starts up or changes scene collection, a "scene change" isn't someone taking a scene

def refresh_scene_names():
    global scene_names
    try:
        scene_names = [name for name in (obs.obs_frontend_get_scene_names() or []) if isinstance(name, str)]
    except Exception as e:
        print(f"FXWizard: Couldn't read the scene names ({e.__class__.__name__})")

def current_scene_name():
    """The scene on program now (in studio mode too), or None."""
    source = obs.obs_frontend_get_current_scene()
    if source is None:
        return None
    try:
        return obs.obs_source_get_name(source)
    finally:
        obs.obs_source_release(source)

def on_frontend_event(event):
    global obs_busy
    try:
        if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
            name = None if obs_busy else current_scene_name()
            if name:
                send_to_panels({"mode": "obsScene", "scene": name}, "scene change")
        elif event == obs.OBS_FRONTEND_EVENT_TRANSITION_STOPPED:
            if not obs_busy:
                send_to_panels({"mode": "obsTransitionEnd"}, "end of the transition")
        elif event in (obs.OBS_FRONTEND_EVENT_FINISHED_LOADING, obs.OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED):
            obs_busy = False
            refresh_scene_names()
        elif event == obs.OBS_FRONTEND_EVENT_SCENE_LIST_CHANGED:
            refresh_scene_names()
        elif event == getattr(obs, "OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGING", None):  # not in very old versions of OBS
            obs_busy = True
    except Exception as e:
        print(f"FXWizard: Couldn't pass on an OBS event ({e.__class__.__name__})")

def script_description():
    return ("FXWizard WebSocket Server. It also adds three hotkeys to OBS (see Settings, Hotkeys): FX Wizard: Start Break, "
            "Reset Break and Toggle AKTA control, and tells the control panel when OBS changes scene (for break scenes).")

def script_load(settings):
    global server_loop, obs_busy
    server_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_server_thread, args=(server_loop,), daemon=True)
    t.start()

    # The hotkeys are added after the server is on its way, so a problem with them can never hold it up
    register_hotkeys(settings)

    # Scene changes, for break scenes. If OBS has already loaded (the script was added or reloaded
    # later), its scenes are there now; otherwise they come with the "finished loading" event.
    try:
        obs.obs_frontend_add_event_callback(on_frontend_event)
        refresh_scene_names()
        if scene_names:
            obs_busy = False
    except Exception as e:
        print(f"FXWizard: Couldn't listen for scene changes ({e.__class__.__name__})")

def script_unload():
    try:
        obs.obs_frontend_remove_event_callback(on_frontend_event)
    except Exception:
        pass  # OBS removes it by itself as well

def script_save(settings):
    """OBS calls this when it saves, so the keys the user gave the hotkeys are remembered."""
    for name, hotkey_id in hotkey_ids.items():
        try:
            saved = obs.obs_hotkey_save(hotkey_id)
            obs.obs_data_set_array(settings, name, saved)
            obs.obs_data_array_release(saved)
        except Exception as e:
            print(f"FXWizard: Couldn't save the hotkey {name} ({e.__class__.__name__})")