// server.js
// This script requires Node.js and the 'ws' library.
//
// 1. Install Node.js if you haven't already.
// 2. Open your terminal in the directory where this file is saved.
// 3. Initialize a project (if needed): npm init -y
// 4. Install the WebSocket library: npm install ws
// 5. Run the server: node server.js to test.  
// Afterwards follow the Readme for instructions on setting up the included bat file to auto-launch in the background.

const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// The folders next to this file:
//   custom    the control panel asks what images are in it
//   rundowns  saved Podcast Rundowns (one .json file each), saved and opened from the control panel
//   logs      show logs (one .csv file each), from Generate Log in the control panel
//   shows     saved shows (one .json file each, "001 - Title.json"): everything the panel is set to
const CUSTOM_DIR = path.join(__dirname, 'custom');
const RUNDOWN_DIR = path.join(__dirname, 'rundowns');
const LOG_DIR = path.join(__dirname, 'logs');
const SHOW_DIR = path.join(__dirname, 'shows');
function customImages() {
    try {
        return fs.readdirSync(CUSTOM_DIR)
            .filter(f => /\.(png|jpe?g|gif)$/i.test(f))
            .sort((a, b) => (a.toLowerCase() < b.toLowerCase() ? -1 : 1));
    } catch (err) {
        return [];
    }
}

// A safe file name for a rundown (letters, numbers, spaces, _ - .), or null
function rundownName(name) {
    const cleaned = String(name || '').replace(/[^A-Za-z0-9 _.-]/g, '').trim().replace(/^\.+|\.+$/g, '').slice(0, 60);
    return cleaned || null;
}

// Saved rundowns, newest first: name (without .json) and when it was saved (in seconds)
function rundownFiles() {
    try {
        return fs.readdirSync(RUNDOWN_DIR)
            .filter(f => /\.json$/i.test(f))
            .map(f => ({ name: f.slice(0, -5), saved: fs.statSync(path.join(RUNDOWN_DIR, f)).mtimeMs / 1000 }))
            .sort((a, b) => b.saved - a.saved);
    } catch (err) {
        return [];
    }
}

// Saved shows are numbered 001 to 999, one file per number: "<number> - <title>.json"
const SHOW_FILE = /^(\d{3}) - (.+)\.json$/i;
const showNumber = (n) => (typeof n === 'string' && /^\d{3}$/.test(n) && n !== '000' ? n : null);
// Saved shows, by number: number, title, file and when it was saved (in seconds)
function showFiles() {
    try {
        return fs.readdirSync(SHOW_DIR)
            .map(f => [f, SHOW_FILE.exec(f)])
            .filter(([, m]) => m && showNumber(m[1]))
            .map(([f, m]) => ({ number: m[1], title: m[2], file: f, saved: fs.statSync(path.join(SHOW_DIR, f)).mtimeMs / 1000 }))
            .sort((a, b) => (a.number < b.number ? -1 : a.number > b.number ? 1 : b.saved - a.saved));
    } catch (err) {
        return [];
    }
}
// showSave: writes the show, and takes away any other file with the same number (the panel asks first)
function saveShowFile(request) {
    const number = showNumber(request.number), title = rundownName(request.title);
    if (!number || !title || !request.data || typeof request.data !== 'object') return { mode: 'showSaved', ok: false, error: 'Needs a number (001 to 999), a title and the show' };
    const file = `${number} - ${title}.json`;
    try {
        fs.mkdirSync(SHOW_DIR, { recursive: true });
        fs.writeFileSync(path.join(SHOW_DIR, file), JSON.stringify(request.data, null, 2));
        for (const old of showFiles()) if (old.number === number && old.file !== file) fs.rmSync(path.join(SHOW_DIR, old.file), { force: true });
        return { mode: 'showSaved', ok: true, number, title, file };
    } catch (err) {
        return { mode: 'showSaved', ok: false, error: err.message };
    }
}
// showLoad: the show saved under that number
function loadShowFile(request) {
    const number = showNumber(request.number);
    const found = number && showFiles().find(f => f.number === number);
    if (!found) return { mode: 'showData', ok: false, error: `There's no show ${number || ''} in the shows folder` };
    try {
        const text = fs.readFileSync(path.join(SHOW_DIR, found.file), 'utf8');
        const data = JSON.parse(text.charCodeAt(0) === 0xFEFF ? text.slice(1) : text);
        return { mode: 'showData', ok: true, number, title: found.title, data };
    } catch (err) {
        return { mode: 'showData', ok: false, error: `Couldn't read ${found.file} (${err.code || err.name})` };
    }
}

// Requests from the control panel that the server answers itself (only to that panel).
// Returns the reply, or null for everything else (graphics, which get passed on).
function answerRequest(request) {
    if (!request || typeof request !== 'object') return null;
    if (request.mode === 'customList') return { mode: 'customFiles', files: customImages() };
    if (request.mode === 'rundownList') return { mode: 'rundownFiles', files: rundownFiles() };
    if (request.mode === 'showList') return { mode: 'showFiles', files: showFiles().map(({ file, ...f }) => f) };
    if (request.mode === 'showSave') return saveShowFile(request);
    if (request.mode === 'showLoad') return loadShowFile(request);
    if (request.mode === 'rundownSave') {
        const name = rundownName(request.name);
        if (!name || !request.data || typeof request.data !== 'object') return { mode: 'rundownSaved', ok: false, error: 'Needs a name and a rundown' };
        try {
            fs.mkdirSync(RUNDOWN_DIR, { recursive: true });
            fs.writeFileSync(path.join(RUNDOWN_DIR, name + '.json'), JSON.stringify(request.data, null, 2));
            return { mode: 'rundownSaved', ok: true, name };
        } catch (err) {
            return { mode: 'rundownSaved', ok: false, error: err.message };
        }
    }
    if (request.mode === 'logSave') {
        const name = rundownName(request.name);
        if (!name || typeof request.csv !== 'string') return { mode: 'logSaved', ok: false, error: 'Needs a name and a log' };
        try {
            fs.mkdirSync(LOG_DIR, { recursive: true });
            fs.writeFileSync(path.join(LOG_DIR, name + '.csv'), '\ufeff' + request.csv); // the mark helps Excel read it
            return { mode: 'logSaved', ok: true, name };
        } catch (err) {
            return { mode: 'logSaved', ok: false, error: err.message };
        }
    }
    if (request.mode === 'rundownLoad') {
        const name = rundownName(request.name);
        try {
            const data = JSON.parse(fs.readFileSync(path.join(RUNDOWN_DIR, (name || '') + '.json'), 'utf8'));
            return { mode: 'rundownData', ok: true, name, data };
        } catch (err) {
            return { mode: 'rundownData', ok: false, error: `Couldn't read ${name}.json (${err.code || err.name})` };
        }
    }
    // Break scenes and Scene cues need OBS's scenes and sources, which only server.py (running inside OBS) can see
    if (request.mode === 'obsScenes') {
        return { mode: 'obsSceneList', ok: false, scenes: [], error: "server.js runs outside OBS, so it can't see your scenes. Break scenes (and the break hotkeys) need server.py, run in OBS." };
    }
    if (request.mode === 'obsSources') {
        return { mode: 'obsSourceList', ok: false, sources: [], error: "server.js runs outside OBS, so it can't see your sources. The list needs server.py, run in OBS." };
    }
    // Firing a TAKE (and the tally of what's on program) needs server.py too
    if (request.mode === 'obsTake') {
        return { mode: 'obsTakeResult', ok: false, scene: '', error: "server.js runs outside OBS, so it can't switch scenes. Firing a TAKE needs server.py, run in OBS." };
    }
    if (request.mode === 'obsProgram') {
        return { mode: 'obsProgramScene', ok: false, scene: null };
    }
    if (request.mode === 'launchProjector') {
        return launchProjector();
    }
    return null;
}

// The projector, opened from the control panel (launchProjector): fx_wizard.html#projector, next to this
// file, in Chrome as an app window (no tabs or address bar, just the page), or in Edge if there's no
// Chrome. The page and the options are fixed here: nothing from the panel goes into the command. It gets
// a browser profile of its own, so the window comes back where it was put, and starts at 800x800.
const PROJECTOR_PAGE = path.join(__dirname, 'fx_wizard.html');
function findBrowser() {
    const found = [];
    if (process.platform === 'win32') {
        for (const env of ['PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA']) {
            if (process.env[env]) found.push([path.join(process.env[env], 'Google', 'Chrome', 'Application', 'chrome.exe'), 'Chrome']);
        }
        for (const env of ['PROGRAMFILES(X86)', 'PROGRAMFILES']) {
            if (process.env[env]) found.push([path.join(process.env[env], 'Microsoft', 'Edge', 'Application', 'msedge.exe'), 'Edge']);
        }
    } else if (process.platform === 'darwin') {
        found.push(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'Chrome'],
            ['/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', 'Edge']);
    } else {
        for (const dir of (process.env.PATH || '').split(path.delimiter)) {
            for (const [cmd, name] of [['google-chrome', 'Chrome'], ['google-chrome-stable', 'Chrome'], ['chromium', 'Chrome'], ['chromium-browser', 'Chrome'], ['microsoft-edge', 'Edge']]) {
                found.push([path.join(dir, cmd), name]);
            }
        }
    }
    return found.find(([file]) => { try { return fs.statSync(file).isFile(); } catch (err) { return false; } }) || [null, null];
}
function launchProjector() {
    const failed = (error) => ({ mode: 'projectorLaunched', ok: false, error });
    const [browser, name] = findBrowser();
    if (!browser) return failed('Couldn\'t find Chrome (or Edge) on the computer running the server');
    if (!fs.existsSync(PROJECTOR_PAGE)) return failed('fx_wizard.html isn\'t next to server.js');
    const home = process.platform === 'win32' ? process.env.LOCALAPPDATA : null;
    const profile = path.join(home || path.join(require('os').homedir(), '.fxwizard'), 'FXWizard', 'projector-browser');
    const args = [`--app=${require('url').pathToFileURL(PROJECTOR_PAGE).href}#projector`, `--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check'];
    if (!fs.existsSync(profile)) args.push('--window-size=800,800'); // the first time; after that it remembers its own size and place
    try {
        require('child_process').spawn(browser, args, { detached: true, stdio: 'ignore' }).on('error', () => {}).unref();
    } catch (err) {
        return failed(`Couldn't open ${name} (${err.code || err.name})`);
    }
    return { mode: 'projectorLaunched', ok: true, browser: name };
}

// ---------------------------------------------------------------------------------------------
// AKTA break / return
//
// The control panel never holds the AKTA private key. It asks this server to start a break or a
// return, and this server signs the request and makes the call to AKTA itself. The settings (public
// key, private key, encoders) are kept in akta-config.json next to this file. Only this server ever
// reads the private key: no reply to the panel contains it, and it is never logged.
//
// Requests from the panel (the reply goes only to that panel):
//   aktaGet                      ->  aktaConfig        the saved settings, without the private key
//   aktaSave {config}            ->  aktaSaved         check and save the settings
//   aktaBreak {durationSeconds}  ->  aktaBreakResult   start a break on every enabled encoder
//   aktaReturn                   ->  aktaReturnResult  return from the break on every enabled encoder
// Any other mode starting with "akta" gets an aktaError reply (and is never passed on to the graphics).
// ---------------------------------------------------------------------------------------------
const AKTA_URL = process.env.AKTA_URL || 'http://nexstar-mcp.mp.lura.live/api';
const AKTA_CONFIG_FILE = process.env.AKTA_CONFIG_PATH || path.join(__dirname, 'akta-config.json');
const AKTA_TIMEOUT_MS = 8000; // so an AKTA host that has gone quiet can't leave the panel waiting
const AKTA_TEXT_MAX = 200;
const AKTA_ENCODERS_MAX = 20;

// What the settings are before anything has been saved
function aktaDefaults() {
    return { publicKey: '', privateKey: '', encoders: [], waitForTransition: false, delayMs: 0 };
}

// Checks settings that came from the panel (or from the file). Returns { config } when they are fine,
// or { error } saying what is wrong. A blank private key is allowed here: when saving it means "keep the saved one".
function aktaCheck(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) return { error: 'The settings are missing' };

    const keys = {};
    for (const [name, label] of [['publicKey', 'Public key'], ['privateKey', 'Private key']]) {
        let value = input[name];
        if (name === 'privateKey' && (value === undefined || value === null)) value = '';
        if (typeof value !== 'string') return { error: `${label} must be text` };
        value = value.trim();
        if (value.length > AKTA_TEXT_MAX) return { error: `${label} is too long (${AKTA_TEXT_MAX} characters at most)` };
        keys[name] = value;
    }

    if (!Array.isArray(input.encoders)) return { error: 'Encoders must be a list' };
    if (input.encoders.length > AKTA_ENCODERS_MAX) return { error: `Too many encoders (${AKTA_ENCODERS_MAX} at most)` };
    const encoders = [];
    for (const [i, enc] of input.encoders.entries()) {
        const label = `Encoder ${i + 1}`;
        if (!enc || typeof enc !== 'object' || Array.isArray(enc)) return { error: `${label} is not valid` };
        const id = typeof enc.id === 'string' ? enc.id.trim() : '';
        // Only these characters, so an id can never break out of the XML it is put into
        if (!/^[A-Za-z0-9_.-]{1,40}$/.test(id)) return { error: `${label} needs an id of 1 to 40 letters, numbers, _ - or .` };
        if (enc.scope !== 'local' && enc.scope !== 'national') return { error: `${label} scope must be local or national` };
        if (typeof enc.enabled !== 'boolean') return { error: `${label} enabled must be true or false` };
        encoders.push({ id, scope: enc.scope, enabled: enc.enabled });
    }

    if (typeof input.waitForTransition !== 'boolean') return { error: 'waitForTransition must be true or false' };
    if (!Number.isInteger(input.delayMs) || input.delayMs < 0 || input.delayMs > 60000) return { error: 'delayMs must be a whole number from 0 to 60000' };

    return { config: { publicKey: keys.publicKey, privateKey: keys.privateKey, encoders, waitForTransition: input.waitForTransition, delayMs: input.delayMs } };
}

// The saved settings. A missing or damaged file counts as "nothing saved yet" (the next save replaces it).
function aktaLoad() {
    try {
        const text = fs.readFileSync(AKTA_CONFIG_FILE, 'utf8');
        const saved = JSON.parse(text.charCodeAt(0) === 0xFEFF ? text.slice(1) : text); // some editors add a byte order mark at the start
        return aktaCheck(saved).config || aktaDefaults();
    } catch (err) {
        return aktaDefaults();
    }
}

// Writes the settings so that, where the system supports it, only the account running this server can read them.
// They go to a side file first and are then moved into place, so a crash can't leave half a file behind.
function aktaStore(config) {
    const side = AKTA_CONFIG_FILE + '.tmp';
    try {
        fs.mkdirSync(path.dirname(AKTA_CONFIG_FILE), { recursive: true });
        fs.rmSync(side, { force: true });
        fs.writeFileSync(side, JSON.stringify(config, null, 2), { mode: 0o600 });
        fs.renameSync(side, AKTA_CONFIG_FILE);
    } catch (err) {
        try { fs.rmSync(side, { force: true }); } catch (ignored) { /* nothing more to clean up */ }
        throw err;
    }
}

// The settings as the panel may see them: everything except the private key itself
function aktaMasked(config) {
    return {
        publicKey: config.publicKey,
        hasPrivateKey: config.privateKey !== '',
        encoders: config.encoders,
        waitForTransition: config.waitForTransition,
        delayMs: config.delayMs
    };
}

// aktaSave: check the settings from the panel and, only if all of them are fine, save them
function aktaSave(input) {
    const stored = aktaLoad();
    const checked = aktaCheck(input);
    if (!checked.config) return { mode: 'aktaSaved', ok: false, error: checked.error, config: aktaMasked(stored) };
    const config = checked.config;
    if (config.privateKey === '') config.privateKey = stored.privateKey; // blank means keep the saved key
    try {
        aktaStore(config);
    } catch (err) {
        return { mode: 'aktaSaved', ok: false, error: `Couldn't save the AKTA settings (${err.code || err.name})`, config: aktaMasked(stored) };
    }
    return { mode: 'aktaSaved', ok: true, config: aktaMasked(config) };
}

// The XML AKTA wants for a break (a slate shown for durationSeconds) and for the return. The id and
// scope were checked when the settings were saved, so nothing in here can break out of the XML.
function aktaBreakBody(enc, durationSeconds) {
    return [
        '<?xml version="1.0"?>',
        '<request>',
        '    <type>cue_stream</type>',
        '    <params>',
        `        <encoder_id>${enc.id}</encoder_id>`,
        `        <cue type="break" scope="${enc.scope}"></cue>`,
        '        <content type="slate">',
        '            <slate_id>local-break</slate_id>',
        `            <duration>${durationSeconds}s</duration>`,
        '        </content>',
        '    </params>',
        '</request>'
    ].join('\n');
}

function aktaReturnBody(enc) {
    return [
        '<?xml version="1.0"?>',
        '<request>',
        '    <type>cue_stream</type>',
        '    <params>',
        `        <encoder_id>${enc.id}</encoder_id>`,
        '        <cue type="return"></cue>',
        '    </params>',
        '</request>'
    ].join('\n');
}

// What is inside <tag>...</tag> in AKTA's answer (empty if it isn't there). Kept short because it goes to the panel.
function aktaTag(answer, tag) {
    const found = new RegExp('<' + tag + '[^>]*>([^<]*)</' + tag + '>', 'i').exec(answer);
    return found ? found[1].trim().slice(0, AKTA_TEXT_MAX) : '';
}

// Signs and sends one call to AKTA. It never throws: the answer says what happened.
async function aktaSend(config, xml) {
    const timestamp = Math.floor(Date.now() / 1000);
    // The signature covers exactly the text that is sent, plus the time
    const signature = crypto.createHmac('sha256', config.privateKey).update(xml + timestamp).digest('base64');
    const url = `${AKTA_URL}?id=${encodeURIComponent(config.publicKey)}&ts=${timestamp}&sgn=${encodeURIComponent(signature)}`;
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/xml' },
            body: xml,
            signal: AbortSignal.timeout(AKTA_TIMEOUT_MS)
        });
        const answer = await response.text().catch(() => '');
        const sent = response.ok ? { success: true } : { success: false, error: `HTTP ${response.status}` };
        for (const tag of ['result', 'status', 'message']) {
            const value = aktaTag(answer, tag);
            if (value) sent[tag] = value; // only these bits of the answer go on to the panel, never the whole thing
        }
        return sent;
    } catch (err) {
        let error = String(err && err.message ? err.message : err);
        if (err && err.cause && err.cause.code) error += ` (${err.cause.code})`;
        // A mistyped AKTA_URL can put the signed address into the message: never pass the signature on
        error = error.split(signature).join('[hidden]').split(encodeURIComponent(signature)).join('[hidden]');
        return { success: false, error: error.slice(0, AKTA_TEXT_MAX) };
    }
}

// Starts a break (kind 'break', for durationSeconds) or the return (kind 'return') on every enabled
// encoder, one after another. ok is true only when at least one encoder was tried and all of them worked.
async function aktaCue(kind, durationSeconds) {
    const failed = (error) => ({ ok: false, error, results: [] });
    let seconds = 0;
    if (kind === 'break') {
        if (typeof durationSeconds !== 'number' || !Number.isFinite(durationSeconds)) return failed('durationSeconds must be a number');
        seconds = Math.min(86400, Math.max(0, Math.round(durationSeconds)));
    }
    const config = aktaLoad();
    if (!config.publicKey || !config.privateKey) return failed('Missing API Keys');
    const encoders = config.encoders.filter(enc => enc.enabled);
    if (!encoders.length) return failed('No Akta encoders enabled');

    const results = [];
    for (const enc of encoders) {
        const sent = await aktaSend(config, kind === 'break' ? aktaBreakBody(enc, seconds) : aktaReturnBody(enc));
        results.push({ id: enc.id, ...sent });
    }
    const problems = results.filter(r => !r.success).map(r => `Encoder ${r.id}: ${r.error}`);
    return problems.length ? { ok: false, error: problems.join('; '), results } : { ok: true, results };
}

// True for any request whose mode starts with "akta" (in any capitals). These are always answered here
// and never passed on to the other clients, so a mistyped mode can't leak the private key.
function isAktaRequest(request) {
    return !!request && typeof request === 'object' && typeof request.mode === 'string' && /^akta/i.test(request.mode);
}

// The answer to each AKTA request (resolves with the reply, never rejects)
async function answerAkta(request) {
    const replyModes = { aktaGet: 'aktaConfig', aktaSave: 'aktaSaved', aktaBreak: 'aktaBreakResult', aktaReturn: 'aktaReturnResult' };
    const replyMode = Object.prototype.hasOwnProperty.call(replyModes, request.mode) ? replyModes[request.mode] : null;
    if (!replyMode) return { mode: 'aktaError', ok: false, error: 'Unknown AKTA request' };
    try {
        if (request.mode === 'aktaGet') return { mode: replyMode, ok: true, config: aktaMasked(aktaLoad()) };
        if (request.mode === 'aktaSave') return aktaSave(request.config);
        const kind = request.mode === 'aktaBreak' ? 'break' : 'return';
        const done = await aktaCue(kind, request.durationSeconds);
        console.log(done.ok ? `AKTA ${kind}: sent to ${done.results.length} encoder(s)` : `AKTA ${kind} problem: ${done.error}`);
        return { mode: replyMode, ...done };
    } catch (err) {
        const reply = { mode: replyMode, ok: false, error: `AKTA request failed (${(err && err.name) || 'Error'})` };
        return replyMode.endsWith('Result') ? { ...reply, results: [] } : reply;
    }
}

// Set up the WebSocket server on port 8080 or change the port as needed
const wss = new WebSocket.Server({ port: 8080 });

// This Set will hold all connected client sockets
const clients = new Set(); 
const STUCK_BYTES = 8 * 1024 * 1024; // a client this far behind on reading gets skipped (see the broadcast below)

console.log("WebSocket Server started on ws://localhost:8080.");
console.log("Waiting for connections from fx_wizard.html...");

wss.on('connection', function connection(ws) {
    // 1. Add new client to the set
    clients.add(ws);
    console.log(`Client connected. Total active clients: ${clients.size}`);

    // 2. Handle incoming messages from any client
    ws.on('message', function incoming(message) {
        const messageText = message.toString();

        // Read the message before logging it. AKTA requests can carry the private key, so only their
        // mode is logged, and they are answered here: they are never passed on to the other clients.
        let request = null;
        try { request = JSON.parse(messageText); } catch (err) { /* not JSON: just pass it on */ }

        if (isAktaRequest(request)) {
            console.log(`Received message: [akta request: ${request.mode.replace(/[^A-Za-z0-9_]/g, '?').slice(0, 30)}]`);
            answerAkta(request).then(aktaReply => {
                // The panel may have gone while the call to AKTA was in flight
                if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(aktaReply));
            }).catch(err => console.error('Could not send the AKTA reply:', (err && err.code) || (err && err.name) || 'error'));
            return;
        }

        console.log(`Received message: ${messageText}`);

        // The control panel asking for the custom images or a rundown file: answer only it
        const reply = answerRequest(request);
        if (reply) {
            ws.send(JSON.stringify(reply));
            return;
        }

        // 3. Broadcast the message to ALL connected clients. send() never waits, so one window that has
        // stopped reading (a tablet asleep with the projector open) can't hold up the others; one that's
        // fallen more than STUCK_BYTES behind is skipped until it catches up, so its queue can't grow forever.
        clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN && client.bufferedAmount < STUCK_BYTES) {
                client.send(messageText);
            }
        });
        console.log(`Broadcasted message to all ${clients.size} clients.`);
    });

    // 4. Handle client disconnection
    ws.on('close', function close() {
        clients.delete(ws);
        console.log(`Client disconnected. Remaining active clients: ${clients.size}`);
    });

    // 5. Handle errors
    ws.on('error', function error(err) {
        console.error("WebSocket error:", err);
    });
});