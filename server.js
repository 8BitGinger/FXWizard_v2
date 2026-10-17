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