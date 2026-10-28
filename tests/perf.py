"""FX Wizard performance suite (see "Tests" in the README).

    python tests/perf.py                 every section
    python tests/perf.py canvas panel    just those

Sections: assets canvas display gpu panel leak offline servers. Needs Google Chrome (or set FXW_CHROME to its path),
Node.js (for server.js), and Python 3 with websockets (pip install websockets). OBS can stay open: the servers are
tested on ports 8092 and 8093, not 8080. Results go to tests/results/perf_results.json (merged with what's there).
Each section makes a throwaway copy of the panel (_perf_*.html) next to fx_wizard.html and deletes it after."""
import os, re, sys, json, time, subprocess, asyncio, statistics, threading, types, importlib.util, shutil
from cdp import Page

from cdp import CHROME

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(REPO, "tests", "results")
os.makedirs(HERE, exist_ok=True)
OUT = os.path.join(HERE, "perf_results.json")
results = json.load(open(OUT)) if os.path.exists(OUT) else {}
SRC = open(os.path.join(REPO, "fx_wizard.html"), encoding="utf-8").read()
BASE = '<base href="file:///' + REPO.replace("\\", "/") + '/">'


def test_page(name, seed=None):
    """A copy of the panel next to the real one (so assets resolve), with no WebSocket, and optional localStorage seed."""
    s = SRC.replace("connectWebSocket();\n        };", "};")
    pre = ''
    if seed is not None:
        pre = "<script>localStorage.clear();" + "".join(
            f"localStorage.setItem({json.dumps(k)}, {json.dumps(v if isinstance(v, str) else json.dumps(v))});" for k, v in seed.items()) + "</script>"
    s = s.replace("<head>", "<head>" + pre, 1)
    p = os.path.join(REPO, f"_perf_{name}.html")
    open(p, "w", encoding="utf-8").write(s)
    return p


def url(p, hash=""):
    return "file:///" + p.replace(os.sep, "/") + hash


def save():
    json.dump(results, open(OUT, "w"), indent=1)


# ---------------------------------------------------------------- A. canvas effects, frame by frame (software canvas, 1080p)
EFFECT_CASES = [
    ["confetti", 4, {}], ["colorwave", 4, {}], ["leaves", 4, {}], ["snow", 4, {}], ["fire", 4, {}], ["underwater", 4, {}],
    ["arrested", 4, {}], ["hottake", 4, {}], ["stpatricks", 4, {}], ["vhs", 4, {}], ["vday", 4, {}], ["rain", 4, {}],
    ["comic", 4, {}], ["disco", 4, {}],
    ["sports", 2.6, {"sport": "football"}], ["sports", 2.6, {"sport": "basketball"}], ["sports", 2.6, {"sport": "baseball"}],
    ["sports", 2.6, {"sport": "soccer"}], ["spring", 3, {}], ["storm", 2.8, {}], ["tvstatic", 1.8, {}], ["fireworks", 3, {}],
    ["medical", 2.4, {}], ["hearts", 2.6, {}], ["firestinger", 2.4, {}], ["pixel", 2.6, {}], ["cat", 2.8, {}],
    ["curtains", 3, {}], ["coffee", 3.4, {}], ["coffee", 3.4, {"label": "Happy Birthday"}],
    ["fire", 4, {"layer": "front"}], ["fire", 4, {"layer": "back"}], ["snow", 4, {"layer": "back"}],
]
BENCH = """<script>
(() => { try {
  const realNow = performance.now.bind(performance);
  let fake = 1000, pending = null;
  performance.now = () => fake;
  window.requestAnimationFrame = (cb) => { pending = cb; return 1; };
  window.cancelAnimationFrame = () => { pending = null; };
  const out = []; const probe = document.getElementById('fx-canvas').getContext('2d');
  for (let pass = 0; pass < 2; pass++) for (const [name, secs, opts] of %s) {
    FX.start(name, secs, opts);
    const costs = [];
    for (let f = 0; f < secs * 60 && pending; f++) {
      fake += 1000 / 60;
      const cb = pending; pending = null;
      const t0 = realNow(); cb(fake); probe.getImageData(0, 0, 1, 1); costs.push(realNow() - t0);
    }
    FX.stop();
    if (pass === 0) continue; // the first pass warms up (sprites, fonts, JIT)
    const sorted = [...costs].sort((a, b) => a - b);
    out.push({ name, opts, frames: costs.length, avg: costs.reduce((a, b) => a + b, 0) / costs.length,
      p95: sorted[Math.floor(sorted.length * 0.95)], max: sorted.at(-1), over16: costs.filter(c => c > 16.7).length, over33: costs.filter(c => c > 33.3).length });
  }
  document.documentElement.setAttribute('data-out', JSON.stringify(out));
} catch (e) { document.documentElement.setAttribute('data-out', JSON.stringify({ error: e.stack })); } })();
</script></body>"""


def canvas():
    s = SRC.replace("<head>", "<head>" + BASE, 1).replace("connectWebSocket();\n        };", "};")
    i = s.rfind("</body>")
    s = s[:i] + BENCH % json.dumps(EFFECT_CASES) + s[i + 7:]
    p = os.path.join(REPO, "_perf_bench.html")
    open(p, "w", encoding="utf-8").write(s)
    o = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--window-size=1920,1080",
                        "--allow-file-access-from-files", "--dump-dom", url(p, "#display")], capture_output=True, text=True, encoding="utf-8", timeout=900).stdout
    os.remove(p)
    m = re.search(r"data-out='([^']*)'|data-out=\"([^\"]*)\"", o)
    raw = (m.group(1) or m.group(2)).replace("&quot;", '"').replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<")
    results["canvas"] = json.loads(raw)
    for r in results["canvas"]:
        print(f"{r['name']:12} {json.dumps(r['opts']):28} avg {r['avg']:6.2f}  p95 {r['p95']:6.2f}  max {r['max']:6.2f}  >16.7ms {r['over16']:3}/{r['frames']}")


# ---------------------------------------------------------------- B. the display in real time
DISPLAY_JS = r"""
window.rtTake = async (data, secs) => {
  const d = []; let last = performance.now(), run = true; const longs = [];
  const po = new PerformanceObserver(l => l.getEntries().forEach(e => longs.push(e.duration))); po.observe({ entryTypes: ['longtask'] });
  const f = (t) => { d.push(t - last); last = t; if (run) requestAnimationFrame(f); };
  requestAnimationFrame(f);
  const t0 = performance.now(); showDisplay(data); const call = performance.now() - t0;
  await new Promise(r => setTimeout(r, secs * 1000));
  run = false; po.disconnect();
  showDisplay({ mode: 'clear' }); await new Promise(r => setTimeout(r, 900));
  const s = d.slice(2).sort((a, b) => a - b);
  return { call, frames: d.length, avg: s.reduce((a, b) => a + b, 0) / s.length, p95: s[Math.floor(s.length * .95)], max: s.at(-1), janks: s.filter(x => x > 25).length, longTasks: longs.length, longest: Math.max(0, ...longs) };
};
window.videoStart = (bg) => new Promise(res => {
  const v = $('l3-video'); const t0 = performance.now(); let done = false;
  showDisplay({ mode: 'l3', label: 'Test Name', title: 'Title', location: 'Bottom Left', bgStyle: bg, fontStyle: 'font-default', fontColor: '', animationStyle: 'anim-fade', duration: 2 });
  v.requestVideoFrameCallback(() => { if (!done) { done = true; res({ bg, firstFrame: performance.now() - t0, duration: v.duration, w: v.videoWidth, h: v.videoHeight }); } });
  setTimeout(() => { if (!done) { done = true; res({ bg, firstFrame: -1 }); } }, 6000);
});
"""


def display():
    p = test_page("display")
    pg = Page(url(p, "#display"))
    pg.js(DISPLAY_JS)
    time.sleep(1.5)
    out = {"video": [], "takes": []}
    bgs = pg.js("BG_VIDEOS")
    for bg in bgs:  # each a new file, so a cold start
        r = pg.js(f"videoStart({json.dumps(bg)})")
        pg.js("hideLowerThird()"); time.sleep(0.9)
        out["video"].append(r); print("video", r)
    l3 = lambda bg, anim="anim-slideLeft": {"mode": "l3", "label": "Jenny Parker", "title": "Host", "location": "Bottom Left", "bgStyle": bg,
                                             "fontStyle": "font-default", "fontColor": "", "animationStyle": anim, "duration": 3}
    cases = [("L3 blue / slide", l3("blue"), 3), ("L3 code (25 MB video)", l3("code"), 3), ("L3 cafe / glitch", l3("cafe", "anim-glitch"), 3),
             ("L3 custom image", {**l3("custom"), "customBg": "ryan3.jpg"}, 3)]
    for ov in ["stinger", "ghost", "colorbars", "xmas", "l3Large", "l3Gif", "breaking", "social", "locpin",
               "fire", "hottake", "disco", "comic", "firestinger", "cat", "curtains", "coffee", "storm", "sportsfx"]:
        cases.append((ov, {"mode": "overlay", "overlay": ov, "label": "Test", "title": "", "duration": 3, "sport": "basketball"}, 3.2))
    for name, data, secs in cases:
        r = pg.js(f"rtTake({json.dumps(data)}, {secs})", timeout=60)
        r["name"] = name
        out["takes"].append(r); print(name, {k: round(v, 1) if isinstance(v, float) else v for k, v in r.items()})
    pg.close(); os.remove(p)
    results["display"] = out


# ---------------------------------------------------------------- C. the control panel
def saved(n):
    return [{"id": 1000 + i, "mode": "l3", "label": f"Guest {i}", "title": "Author" if i % 2 else "", "location": "Bottom Left", "bgStyle": ["blue", "cafe", "space"][i % 3],
             "fontStyle": "font-default", "fontColor": "", "duration": 5, "animationStyle": "anim-fade"} if i % 4 else
            {"id": 1000 + i, "mode": "overlay", "overlay": ["confetti", "fire", "curtains", "coffee"][i % 4 // 1 % 4], "label": "", "title": "", "duration": 8} for i in range(n)]


def rundown(n):
    blocks = ["A", "B", "C", "D", "E"]
    return [{**g, "block": blocks[i * 5 // n], "sid": f"s{i}"} for i, g in enumerate(saved(n))]


PANEL_JS = r"""
window.settle = () => new Promise(r => requestAnimationFrame(() => setTimeout(r, 0)));
window.timeIt = async (fn, reps = 5) => { const t = []; for (let i = 0; i < reps; i++) { await settle(); const t0 = performance.now(); fn(); const sync = performance.now() - t0; await settle(); t.push([sync, performance.now() - t0]); } return { sync: Math.min(...t.map(x => x[0])), toFrame: Math.min(...t.map(x => x[1])) }; };
window.pickTab = (v) => { const r = document.querySelector(`input[name="mode"][value="${v}"]`); r.checked = true; r.dispatchEvent(new Event('change', { bubbles: true })); };
window.loadInfo = () => { const n = performance.getEntriesByType('navigation')[0]; const res = performance.getEntriesByType('resource').map(r => ({ name: r.name.split('/').slice(-1)[0].slice(0, 60), host: (r.name.match(/^https?:\/\/([^/]+)/) || [])[1] || 'local', dur: r.duration, size: r.transferSize }));
  return { dcl: n.domContentLoadedEventEnd, loadStart: n.loadEventStart, loadEnd: n.loadEventEnd, initView: n.loadEventEnd - n.loadEventStart, res, nodes: document.getElementsByTagName('*').length }; };
"""


def panel():
    out = {}
    # (Until 2026-10-22 Tailwind came from its CDN and this also ran without it, to see what it cost. It's a local file now.)
    for tag in ("local",):
        r = {}
        for n in (0, 100, 500):
            p = test_page(f"panel{n}", seed={"studio_buttons": saved(n), "fx_show": rundown(min(n, 300)), "fx_blocks": ["A", "B", "C", "D", "E"]})
            pg = Page(url(p), size=(500, 1000))
            time.sleep(1.0)
            pg.js(PANEL_JS)
            info = pg.js("loadInfo()")
            row = {"load": info}
            row["renderSaved"] = pg.js("timeIt(() => renderButtons(loadButtonsFromStorage()))")
            row["toRundownTab"] = pg.js("(async () => { await settle(); const t0 = performance.now(); pickTab('show'); await settle(); return performance.now() - t0; })()")
            row["renderRundown"] = pg.js("timeIt(() => renderShow())")
            row["backToL3Tab"] = pg.js("(async () => { await settle(); const t0 = performance.now(); pickTab('l3'); await settle(); return performance.now() - t0; })()")
            row["overlayTab"] = pg.js("(async () => { await settle(); const t0 = performance.now(); pickTab('overlay'); await settle(); return performance.now() - t0; })()")
            row["storageKB"] = pg.js("Math.round(Object.keys(localStorage).reduce((s, k) => s + k.length + localStorage.getItem(k).length, 0) * 2 / 1024)")
            if n == 0:
                row["setItemPatched"] = pg.js("(() => { const t0 = performance.now(); for (let i = 0; i < 2000; i++) localStorage.setItem('fx_perf', 'x' + i); return (performance.now() - t0) / 2000 * 1000; })()")
                row["simpleOn"] = pg.js("(async () => { saveButtonsToStorage(Array.from({ length: 20 }, (_, i) => ({ id: i, mode: 'l3', label: 'G' + i, title: '', simple: true, theme: 'classic' }))); await settle(); const t0 = performance.now(); setSimpleOn(true); await settle(); const on = performance.now() - t0; const t1 = performance.now(); pickTheme('lifestyle'); await settle(); return { on, theme: performance.now() - t1 }; })()")
            r[str(n)] = row
            print(tag, n, {k: v for k, v in row.items() if k != "load"}, "load", round(info["loadEnd"]), "init", round(info["initView"]))
            pg.close(); os.remove(p)
        out[tag] = r
    results["panel"] = out


# ---------------------------------------------------------------- D. memory over many takes
def leak():
    p = test_page("leak")
    pg = Page(url(p, "#display"))
    time.sleep(1.5)
    pg.send("HeapProfiler.enable")
    def heap():
        pg.send("HeapProfiler.collectGarbage"); time.sleep(0.3)
        return pg.send("Runtime.getHeapUsage")["usedSize"] / 1e6
    def dom():
        return pg.js("document.getElementsByTagName('*').length")
    before, dom0 = heap(), dom()
    keys = pg.js("Object.keys(OVERLAYS)")
    bgs = pg.js("BG_VIDEOS")
    rounds = 3
    script = """(async (keys, bgs) => { for (const k of keys) { showDisplay({ mode: 'overlay', overlay: k, label: 'T', title: '', duration: 1, sport: 'soccer', customBg: 'ryan3.jpg' });
      await new Promise(r => setTimeout(r, 120)); }
      for (const b of bgs) { showDisplay({ mode: 'l3', label: 'T', title: 'x', location: 'Bottom Left', bgStyle: b, fontStyle: 'font-fun', fontColor: '', animationStyle: 'anim-glitch', duration: 1 }); await new Promise(r => setTimeout(r, 120)); }
      showDisplay({ mode: 'clear' }); await new Promise(r => setTimeout(r, 1500)); })(%s, %s)""" % (json.dumps(keys), json.dumps(bgs))
    steps = []
    for i in range(rounds):
        pg.js(script, timeout=120)
        steps.append(round(heap(), 2))
    results["leak"] = {"before": round(before, 2), "afterRounds": steps, "takesPerRound": len(keys) + len(bgs), "domBefore": dom0, "domAfter": dom()}
    print(results["leak"])
    pg.close(); os.remove(p)


# ---------------------------------------------------------------- E. the servers: relay time
async def relay_test(port, n=400, big=False):
    import websockets
    ctrl = await websockets.connect(f"ws://127.0.0.1:{port}", max_size=2 ** 24)
    disp = await websockets.connect(f"ws://127.0.0.1:{port}", max_size=2 ** 24)
    under = await websockets.connect(f"ws://127.0.0.1:{port}", max_size=2 ** 24)
    await asyncio.sleep(0.3)
    lat = []
    pad = "x" * 20000 if big else ""
    async def drain(ws):
        try:
            while True:
                await asyncio.wait_for(ws.recv(), 0.0001 + 2)
        except Exception:
            pass
    for i in range(n):
        msg = json.dumps({"mode": "l3", "label": f"Guest {i}", "title": pad, "location": "Bottom Left", "bgStyle": "blue", "duration": 5, "i": i})
        t0 = time.perf_counter()
        await ctrl.send(msg)
        while True:
            m = json.loads(await disp.recv())
            if m.get("i") == i:
                break
        lat.append((time.perf_counter() - t0) * 1000)
        # the sender and the underlay get it too; read them so nothing backs up
        await ctrl.recv(); await under.recv()
    # a burst: 200 at once, time to the last arriving
    t0 = time.perf_counter()
    for i in range(200):
        await ctrl.send(json.dumps({"mode": "overlay", "overlay": "confetti", "duration": 8, "b": i}))
    got = 0
    while got < 200:
        m = json.loads(await disp.recv())
        if "b" in m:
            got += 1
    burst = (time.perf_counter() - t0) * 1000
    for ws in (ctrl, disp, under):
        await ws.close()
    s = sorted(lat)
    return {"n": n, "median": statistics.median(s), "p95": s[int(len(s) * 0.95)], "max": s[-1], "burst200": burst, "payloadKB": round(len(msg) / 1024, 1)}


async def slow_client_test(port):
    """One client that never reads (a frozen projector, say): does it hold up the display?"""
    import websockets
    ctrl = await websockets.connect(f"ws://127.0.0.1:{port}", max_size=2 ** 24)
    disp = await websockets.connect(f"ws://127.0.0.1:{port}", max_size=2 ** 24)
    raw = await asyncio.open_connection("127.0.0.1", port)  # a client that handshakes, then never reads
    reader, writer = raw
    writer.write(b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n")
    await writer.drain()
    await asyncio.sleep(0.3)
    lat = []
    pad = "y" * 60000
    for i in range(150):  # ~9 MB pushed at the client that never reads
        t0 = time.perf_counter()
        await ctrl.send(json.dumps({"mode": "note", "pad": pad, "i": i}))
        try:
            while True:
                m = json.loads(await asyncio.wait_for(disp.recv(), 5))
                if m.get("i") == i:
                    break
        except asyncio.TimeoutError:
            lat.append(5000); break
        lat.append((time.perf_counter() - t0) * 1000)
        try:
            while True:
                await asyncio.wait_for(ctrl.recv(), 0.001)
        except Exception:
            pass
    writer.close()
    for ws in (ctrl, disp):
        await ws.close()
    return {"sent": len(lat), "median": statistics.median(lat), "max": max(lat), "stalled": lat[-1] >= 5000}


def servers():
    out = {}
    # server.js, a copy on port 8092 (OBS holds 8080)
    js = open(os.path.join(REPO, "server.js"), encoding="utf-8").read().replace("port: 8080", "port: 8092")
    jsp = os.path.join(REPO, "_perf_server.js")
    open(jsp, "w", encoding="utf-8").write(js)
    proc = subprocess.Popen(["node", jsp], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    try:
        out["server.js"] = asyncio.run(relay_test(8092))
        out["server.js big"] = asyncio.run(relay_test(8092, 150, big=True))
        out["server.js slow client"] = asyncio.run(slow_client_test(8092))
    finally:
        proc.kill(); os.remove(jsp)
    # server.js again with its console logging silenced, to see what logging costs
    js2 = js.replace("console.log(", "(()=>{})(")
    open(jsp, "w", encoding="utf-8").write(js2)
    proc = subprocess.Popen(["node", jsp], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    try:
        out["server.js no logging"] = asyncio.run(relay_test(8092))
        out["server.js no logging big"] = asyncio.run(relay_test(8092, 150, big=True))
    finally:
        proc.kill(); os.remove(jsp)
    # server.py, outside OBS: obspython stubbed, on its own thread like in OBS, port 8093
    stub = types.ModuleType("obspython")
    stub.__getattr__ = lambda name: (lambda *a, **k: None)
    sys.modules["obspython"] = stub
    spec = importlib.util.spec_from_file_location("fxserver", os.path.join(REPO, "server.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    loop = asyncio.new_event_loop()
    def run():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(mod.main_async_entry("127.0.0.1", 8093))
    th = threading.Thread(target=run, daemon=True); th.start(); time.sleep(0.8)
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):  # it prints every broadcast
        out["server.py"] = asyncio.run(relay_test(8093))
        out["server.py big"] = asyncio.run(relay_test(8093, 150, big=True))
        out["server.py slow client"] = asyncio.run(slow_client_test(8093))
    loop.call_soon_threadsafe(lambda: mod.server_stop.set_result(None))
    for k, v in out.items():
        print(k, {a: round(b, 2) if isinstance(b, float) else b for a, b in v.items()})
    results["servers"] = out


# ---------------------------------------------------------------- G. the same heavy effects with GPU drawing (as OBS does by default)
def gpu():
    out = {}
    for on in (False, True):
        p = test_page("gpu")
        pg = Page(url(p, "#display"), gpu=on, extra=("--enable-gpu-rasterization", "--ignore-gpu-blocklist") if on else ())
        pg.js(DISPLAY_JS); time.sleep(1.5)
        renderer = pg.js("(() => { const g = document.createElement('canvas').getContext('webgl'); const e = g && g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : 'none'; })()")
        rows = []
        for ov in ["hottake", "underwater", "vhs", "storm", "sportsfx", "spring", "hearts", "fire", "curtains", "coffee", "stinger", "ghost"]:
            r = pg.js(f"rtTake({json.dumps({'mode': 'overlay', 'overlay': ov, 'label': '', 'title': '', 'duration': 3, 'sport': 'baseball'})}, 3)", timeout=60)
            rows.append({"name": ov, "fps": round(1000 / r["avg"], 1), "janks": r["janks"], "longest": r["longest"]})
        out["gpu" if on else "software"] = {"renderer": renderer, "rows": rows}
        print("GPU" if on else "SOFTWARE", renderer)
        for r in rows:
            print("  ", r)
        pg.close(); os.remove(p)
    results["gpu"] = out


# ---------------------------------------------------------------- H. no internet: everything still works
def offline():
    """Every web address blocked (http and https; the page's own files still load). The display, underlay and
    content pages show nothing but graphics, the panel keeps its layout, the fonts load, and the page asks the web for nothing."""
    out = {}
    for hash in ("#display", "#underlay", "#content", ""):
        p = test_page("offline")
        pg = Page("about:blank", size=(1280, 720))
        pg.send("Network.enable")
        pg.send("Network.setBlockedURLs", urls=["http://*", "https://*"])
        pg.send("Page.navigate", url=url(p, hash)); time.sleep(2.5)
        row = {"webRequests": pg.js("performance.getEntriesByType('resource').filter(r => /^https?:/.test(r.name)).length")}
        if hash:
            shown = pg.js("[...document.querySelectorAll('body *')].filter(e => e.offsetParent !== null && e.getBoundingClientRect().width > 0 && !e.closest('#display-view')).map(e => e.id || e.tagName)")
            row["shownOutsideGraphics"] = [s for s in shown if s != "app"]
            row["ok"] = not row["shownOutsideGraphics"] and not row["webRequests"]
        else:
            row["layout"] = pg.js("getComputedStyle(document.getElementById('mode-tabs')).display")  # 'grid': Tailwind's classes are there
            row["fonts"] = pg.js("""(async () => { const out = {};
                for (const f of ['Lobster', 'Bona Nova SC', 'VT323', 'Newsreader']) out[f] = (await document.fonts.load(`20px "${f}"`)).length > 0;
                return out; })()""")
            row["ok"] = row["layout"] == "grid" and all(row["fonts"].values()) and not row["webRequests"]
        out[hash or "panel"] = row
        print(hash or "panel", row)
        pg.close(); os.remove(p)
    results["offline"] = out


# ---------------------------------------------------------------- F. file sizes
def assets():
    out = {}
    for rel in ["fx_wizard.html", "css/styles.css", "server.js", "server.py"]:
        out[rel] = os.path.getsize(os.path.join(REPO, rel))
    for d in ["assets", "assets/sounds", "custom"]:
        for f in sorted(os.listdir(os.path.join(REPO, d))):
            fp = os.path.join(REPO, d, f)
            if os.path.isfile(fp):
                out[f"{d}/{f}"] = os.path.getsize(fp)
    results["assets"] = out
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    for sec in sys.argv[1:] or ["assets", "canvas", "display", "gpu", "panel", "leak", "offline", "servers"]:
        t0 = time.time()
        globals()[sec]()
        results.setdefault("_ran", {})[sec] = time.strftime("%Y-%m-%d %H:%M")
        save()
        print(f"== {sec} done in {time.time() - t0:.0f}s")
