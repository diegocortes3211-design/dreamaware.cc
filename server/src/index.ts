import http from "node:http";
import { WebSocketServer, WebSocket } from "ws";
import { z } from "zod";
import { clamp, nowMs } from "./util.js";
import { ClientMsg, Hello, Credit, Pong, Welcome, Delta, Snapshot, Ping, Bye } from "./types.js";
import { Stream } from "./stream.js";
import { RollingSnapshotCache } from "./snapshotCache.js";
import { securityMiddleware, cspReportHandler } from "./middleware.js";

/** Config */
const PORT = 8080;
const STREAM_ID = "main_stream";

// Security middleware configuration
const security = securityMiddleware({
  hstsMaxAge: 31536000,
  hstsIncludeSubdomains: true,
  cspReportOnly: true,
  cspReportUri: '/api/csp-report'
});

// ... existing config from previous steps

const stream = new Stream(STREAM_ID); // simulate 500 deltas/sec; adjust to taste
stream.startSynthetic(500);

// ---- Rolling snapshot cache (Option A: 500ms)
const snapshotCache = new RollingSnapshotCache(
  () => {
    // Build the snapshot JSON OFF the hot path, every 500ms.
    const snap = stream.snapshot(); // { tickId, state: { count } } in starter
    // Validate shape with your Zod schema (keeps payload honest).
    const payload = Snapshot.parse({
      type: "snapshot",
      tickId: snap.tickId,
      state: { count: snap.state.count },
    });
    return { tickId: snap.tickId, json: JSON.stringify(payload) };
  },
  500
);
snapshotCache.start();

const server = http.createServer((req, res) => {
  // Apply security headers to all requests
  security(req, res);

  if (req.url === "/") {
    res.writeHead(200).end("ws-backpressure-server\n");
  } else if (req.url === "/healthz") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(snapshotCache.stats()));
  } else if (req.url === "/api/csp-report") {
    cspReportHandler(req, res);
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
  const view = snapshotCache.view(); // cached, ≤500ms fresh
  conn.sendQ.push({
    type: "snapshot",
    bytes: view.bytes.toString("utf8"),
    weight: 1
  });
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