"""Tiny Chrome DevTools driver: opens a page in headless Chrome and evaluates JavaScript in it (awaiting promises)."""
import asyncio, json, os, subprocess, time, urllib.request, itertools, shutil
import websockets

CHROME = os.environ.get("FXW_CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")  # scratch profiles go here (not in Git)


class Page:
    def __init__(self, url, size=(1920, 1080), port=9333, gpu=False, extra=()):
        os.makedirs(HERE, exist_ok=True)
        self.prof = os.path.join(HERE, f"prof{port}")
        shutil.rmtree(self.prof, ignore_errors=True)
        args = [CHROME, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={self.prof}",
                f"--window-size={size[0]},{size[1]}", "--allow-file-access-from-files", "--autoplay-policy=no-user-gesture-required",
                "--no-first-run", "--hide-scrollbars", *extra]
        if not gpu:
            args.append("--disable-gpu")
        self.proc = subprocess.Popen(args + ["about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                self.ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.1)
        self.ids = itertools.count(1)
        self.loop = asyncio.new_event_loop()
        self.ws = self.loop.run_until_complete(websockets.connect(self.ws_url, max_size=2 ** 30))
        self.send("Page.enable")
        self.send("Page.navigate", url=url)
        self.wait_event("Page.loadEventFired")

    def send(self, method, **params):
        return self.loop.run_until_complete(self._send(method, params))

    async def _send(self, method, params):
        i = next(self.ids)
        await self.ws.send(json.dumps({"id": i, "method": method, "params": params}))
        while True:
            m = json.loads(await self.ws.recv())
            if m.get("id") == i:
                if "error" in m:
                    raise RuntimeError(m["error"])
                return m.get("result", {})

    def wait_event(self, name, timeout=60):
        async def w():
            while True:
                m = json.loads(await self.ws.recv())
                if m.get("method") == name:
                    return m
        return self.loop.run_until_complete(asyncio.wait_for(w(), timeout))

    def js(self, expr, timeout=600):
        r = self.loop.run_until_complete(asyncio.wait_for(self._send("Runtime.evaluate", {
            "expression": expr, "awaitPromise": True, "returnByValue": True}), timeout))
        if "exceptionDetails" in r:
            raise RuntimeError(r["exceptionDetails"].get("exception", {}).get("description") or r["exceptionDetails"])
        return r["result"].get("value")

    def close(self):
        try:
            self.loop.run_until_complete(self.ws.close())
        except Exception:
            pass
        self.proc.kill()
        self.proc.wait()
        time.sleep(0.3)
        shutil.rmtree(self.prof, ignore_errors=True)
