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

// The folders next to this file:
//   custom    the control panel asks what images are in it
//   rundowns  saved Podcast Rundowns (one .json file each), saved and opened from the control panel
const CUSTOM_DIR = path.join(__dirname, 'custom');
const RUNDOWN_DIR = path.join(__dirname, 'rundowns');
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

// Requests from the control panel that the server answers itself (only to that panel).
// Returns the reply, or null for everything else (graphics, which get passed on).
function answerRequest(request) {
    if (!request || typeof request !== 'object') return null;
    if (request.mode === 'customList') return { mode: 'customFiles', files: customImages() };
    if (request.mode === 'rundownList') return { mode: 'rundownFiles', files: rundownFiles() };
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
    if (request.mode === 'rundownLoad') {
        const name = rundownName(request.name);
        try {
            const data = JSON.parse(fs.readFileSync(path.join(RUNDOWN_DIR, (name || '') + '.json'), 'utf8'));
            return { mode: 'rundownData', ok: true, name, data };
        } catch (err) {
            return { mode: 'rundownData', ok: false, error: `Couldn't read ${name}.json (${err.code || err.name})` };
        }
    }
    return null;
}

// Set up the WebSocket server on port 8080 or change the port as needed
const wss = new WebSocket.Server({ port: 8080 });

// This Set will hold all connected client sockets
const clients = new Set(); 

console.log("WebSocket Server started on ws://localhost:8080.");
console.log("Waiting for connections from websocket_demo.html...");

wss.on('connection', function connection(ws) {
    // 1. Add new client to the set
    clients.add(ws);
    console.log(`Client connected. Total active clients: ${clients.size}`);

    // 2. Handle incoming messages from any client
    ws.on('message', function incoming(message) {
        const messageText = message.toString();
        console.log(`Received message: ${messageText}`);

        // The control panel asking for the custom images or a rundown file: answer only it
        let request = null;
        try { request = JSON.parse(messageText); } catch (err) { /* not JSON: just pass it on */ }
        const reply = answerRequest(request);
        if (reply) {
            ws.send(JSON.stringify(reply));
            return;
        }

        // 3. Broadcast the message to ALL connected clients
        clients.forEach(client => {
            // Check if the client connection is open before sending
            if (client.readyState === WebSocket.OPEN) {
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