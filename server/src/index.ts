import http from "node:http";
import { WebSocketServer, WebSocket } from "ws";
import { z } from "zod";
import { clamp, nowMs } from "./util.js";
import { ClientMsg, Hello, Credit, Pong, Welcome, Delta, Snapshot, Ping, Bye } from "./types.js";
import { Stream } from "./stream.js";
import { SnapshotCache } from "./snapshotCache.js";

/** Config */
const PORT = 8080;
const STREAM_ID = "main_stream";

// ... existing config from previous steps

const stream = new Stream(STREAM_ID); // simulate 500 deltas/sec; adjust to taste
stream.startSynthetic(500);

// Create a simple state wrapper for the stream data
const graphState = {
  head: 0,
  nodes: new Map(),
  edges: new Map()
};

// Update graph state when stream changes
stream.subscribe((tickId, delta) => {
  graphState.head = tickId;
  graphState.nodes.set('count', { id: 'count', value: delta.count });
});

// ---- Rolling snapshot cache (Option A: 500ms)
const snapshotCache = new SnapshotCache(graphState, 500);
snapshotCache.start();

const server = http.createServer((req, res) => {
  // Set CORS headers for API endpoints
  if (req.url?.startsWith('/api/')) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
      res.writeHead(200).end();
      return;
    }
  }

  if (req.url === "/") {
    res.writeHead(200).end("ws-backpressure-server\n");
  } else if (req.url === "/healthz") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(snapshotCache.getStats()));
  } else if (req.url === "/api/_csp-report" && req.method === "POST") {
    // CSP violation reporting endpoint
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    
    req.on('end', () => {
      try {
        const report = JSON.parse(body);
        const timestamp = new Date().toISOString();
        
        // Log CSP violation (in production, you might want to send to a monitoring service)
        console.warn(`[CSP-VIOLATION] ${timestamp}:`, {
          documentUri: report['csp-report']?.['document-uri'],
          violatedDirective: report['csp-report']?.['violated-directive'], 
          blockedUri: report['csp-report']?.['blocked-uri'],
          sourceFile: report['csp-report']?.['source-file'],
          lineNumber: report['csp-report']?.['line-number'],
          originalPolicy: report['csp-report']?.['original-policy']
        });
        
        res.writeHead(204).end(); // No content response
      } catch (error) {
        console.error('[CSP-REPORT] Invalid report format:', error);
        res.writeHead(400).end('Invalid report format');
      }
    });
  } else {
    res.writeHead(404).end("not found");
  }
});

const wss = new WebSocketServer({ server });

type ConnState = {
  id: string;
  ws: WebSocket;
  lastSeenMs: number;
  credits: number;
  sendQ: any[];
  lastApplied: number;
}

const conns = new Map<string, ConnState>();

wss.on("connection", (ws, req) => {
  const connId = req.headers["sec-websocket-key"]!;
  console.log(`[${connId}] connected`);
  // ... rest of the connection logic
});

/** Build & enqueue snapshot for a connection */
function enqueueSnapshot(conn: ConnState) {
  const { snapshot } = snapshotCache.getSnapshot();
  if (snapshot) {
    conn.sendQ.push({
      type: "snapshot",
      bytes: snapshot.data.toString("utf8"),
      weight: 1
    });
  } else {
    // No snapshot available yet, send error or wait
    conn.sendQ.push({
      type: "snapshot_pending",
      weight: 1
    });
  }
}

/** Global scheduler: round-robin send respecting credits */
setInterval(() => {
  for (const conn of conns.values()) {
    // ... rest of the scheduler logic
  }
}, 20);

server.listen(PORT, () => {
  console.log(`[server] listening on http://localhost:${PORT}`);
});