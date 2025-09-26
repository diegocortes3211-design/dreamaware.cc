import http from "node:http";
import { WebSocketServer, WebSocket } from "ws";
import { securityMiddleware, cspReportHandler } from "./middleware.js";

/** Config */
const PORT = process.env.PORT || 8080;

// Security middleware configuration
const security = securityMiddleware({
  hstsMaxAge: 31536000,
  hstsIncludeSubdomains: true,
  cspReportOnly: true,
  cspReportUri: '/api/csp-report'
});

// Simple in-memory state for demonstration
let tickId = 0;
let connections = new Map();

const server = http.createServer((req, res) => {
  // Apply security headers to all requests
  security(req, res);

  if (req.url === "/") {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("DreamAware WebSocket Server with Security Hardening\n");
  } else if (req.url === "/healthz") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ 
      status: "healthy", 
      timestamp: Date.now(),
      connections: connections.size,
      tickId: tickId
    }));
  } else if (req.url === "/api/csp-report") {
    cspReportHandler(req, res);
  } else {
    res.writeHead(404).end("not found");
  }
});

const wss = new WebSocketServer({ server });

wss.on("connection", (ws, req) => {
  const connId = req.headers["sec-websocket-key"] || `conn-${Date.now()}`;
  
  console.log(`WebSocket connection established: ${connId}`);
  connections.set(connId, { ws, connectedAt: Date.now() });

  ws.on("message", (data) => {
    try {
      const message = JSON.parse(data.toString());
      console.log(`Received from ${connId}:`, message.type);
      
      // Echo back with security validation
      if (message.type === "ping") {
        ws.send(JSON.stringify({ type: "pong", tickId: tickId++ }));
      }
    } catch (error) {
      console.error(`Invalid message from ${connId}:`, error);
      ws.close(1003, "Invalid message format");
    }
  });

  ws.on("close", () => {
    console.log(`WebSocket connection closed: ${connId}`);
    connections.delete(connId);
  });

  ws.on("error", (error) => {
    console.error(`WebSocket error for ${connId}:`, error);
    connections.delete(connId);
  });

  // Send welcome message
  ws.send(JSON.stringify({ 
    type: "welcome", 
    connId, 
    timestamp: Date.now(),
    securityLevel: "hardened"
  }));
});

// Handle graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, closing server gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, closing server gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

server.listen(PORT, () => {
  console.log(`🔒 Hardened WebSocket server listening on port ${PORT}`);
  console.log(`🛡️  Security features enabled: HSTS, CSP (report-only), security headers`);
  console.log(`📊 Health check available at /healthz`);
});