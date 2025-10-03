const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = 9980;

// Serve static files from 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Store connected clients
const clients = new Set();

// WebSocket connection handling
wss.on('connection', (ws) => {
    console.log('New client connected');
    clients.add(ws);

    // Send welcome message
    ws.send(JSON.stringify({
        type: 'connection',
        message: 'Connected to TouchDesigner WebSocket Server',
        timestamp: Date.now()
    }));

    // Handle incoming messages
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            console.log('Received from client:', data);

            // Broadcast to all other clients (including TouchDesigner!)
            // This is crucial - messages from web UI need to reach TouchDesigner
            broadcastToOthers(ws, data);

        } catch (error) {
            console.error('Error parsing message:', error);
            ws.send(JSON.stringify({
                type: 'error',
                message: 'Invalid JSON format'
            }));
        }
    });

    // Handle client disconnect
    ws.on('close', () => {
        console.log('Client disconnected');
        clients.delete(ws);
    });

    // Handle errors
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
    });
});

// Broadcast to all connected clients
function broadcast(data) {
    const message = JSON.stringify(data);
    clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
}

// Broadcast to all clients except sender
function broadcastToOthers(sender, data) {
    const message = JSON.stringify(data);
    clients.forEach((client) => {
        if (client !== sender && client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
}

// Example: Send periodic updates (optional - remove if not needed)
// setInterval(() => {
//     broadcast({
//         type: 'heartbeat',
//         timestamp: Date.now()
//     });
// }, 5000);

// Start server
server.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log(`WebSocket server running on ws://localhost:${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM signal received: closing HTTP server');
    server.close(() => {
        console.log('HTTP server closed');
    });
});
