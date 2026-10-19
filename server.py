import obspython as obs
import asyncio
import json
import os
import re
import threading
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
    return None

async def socket_handler(websocket):
    clients.add(websocket)
    print(f"FXWizard: Client Connected. Total: {len(clients)}")
    try:
        async for message in websocket:
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

def script_description():
    return "FXWizard WebSocket Server"

def script_load(settings):
    new_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_server_thread, args=(new_loop,), daemon=True)
    t.start()