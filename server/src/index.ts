import http from "node:http";
import express from "express";
import { WebSocketServer, WebSocket } from "ws";
import { z } from "zod";
import { clamp, nowMs } from "./util.js";
import { ClientMsg, Hello, Credit, Pong, Welcome, Delta, Snapshot, Ping, Bye } from "./types.js";
import { Stream } from "./stream.js";
import { RollingSnapshotCache } from "./rollingCache.js";
import { config } from "./config/index.js";
import { db } from "./database/service.js";
import { xikizpediaService } from "./services/xikizpedia.js";
import { securityHeaders, rateLimiter, payloadSizeLimit, developmentRbac, errorHandler } from "./middleware/security.js";

/** Config */
const PORT = config.port;
const STREAM_ID = "xikizpedia_stream";

// Create Express app for HTTP endpoints
const app = express();

// Apply security middleware
app.use(securityHeaders);
app.use(rateLimiter);
app.use(express.json({ limit: config.security.maxPayloadSize }));
app.use(payloadSizeLimit);
app.use(developmentRbac);

// Health check endpoint
app.get('/health', async (req, res) => {
  const dbHealth = await db.healthCheck();
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    database: dbHealth ? 'connected' : 'disconnected',
    version: '1.0.0'
  });
});

// Xikizpedia API endpoints
app.post('/api/xikizpedia/entries', async (req, res) => {
  try {
    const { textContent, metadata } = req.body;
    
    if (!textContent || typeof textContent !== 'string') {
      return res.status(400).json({
        error: 'textContent is required and must be a string',
        timestamp: new Date().toISOString()
      });
    }

    if (textContent.length > 10000) {
      return res.status(400).json({
        error: 'textContent too long (max 10000 characters)',
        timestamp: new Date().toISOString()
      });
    }

    const entry = await xikizpediaService.createEntry({
      textContent: textContent.trim(),
      metadata
    });

    res.status(201).json(entry);
  } catch (error: any) {
    console.error('Error creating entry:', error);
    res.status(500).json({
      error: error.message || 'Failed to create entry',
      timestamp: new Date().toISOString()
    });
  }
});

app.get('/api/xikizpedia/entries/:voidId', async (req, res) => {
  try {
    const { voidId } = req.params;
    
    if (!/^[a-f0-9]{8}$/i.test(voidId)) {
      return res.status(400).json({
        error: 'Invalid void ID format',
        timestamp: new Date().toISOString()
      });
    }

    const entry = await xikizpediaService.getEntryByVoidId(voidId);
    
    if (!entry) {
      return res.status(404).json({
        error: 'Entry not found',
        timestamp: new Date().toISOString()
      });
    }

    res.json(entry);
  } catch (error: any) {
    console.error('Error fetching entry:', error);
    res.status(500).json({
      error: 'Failed to fetch entry',
      timestamp: new Date().toISOString()
    });
  }
});

app.get('/api/xikizpedia/search', async (req, res) => {
  try {
    const { q, limit = '20', offset = '0' } = req.query;
    
    if (!q || typeof q !== 'string') {
      return res.status(400).json({
        error: 'Search query (q) is required',
        timestamp: new Date().toISOString()
      });
    }

    const entries = await xikizpediaService.searchEntries(
      q,
      Math.min(parseInt(limit as string, 10) || 20, 100),
      Math.max(parseInt(offset as string, 10) || 0, 0)
    );

    res.json({
      query: q,
      results: entries,
      count: entries.length,
      timestamp: new Date().toISOString()
    });
  } catch (error: any) {
    console.error('Error searching entries:', error);
    res.status(500).json({
      error: 'Failed to search entries',
      timestamp: new Date().toISOString()
    });
  }
});

app.get('/api/xikizpedia/entries', async (req, res) => {
  try {
    const { limit = '50', offset = '0' } = req.query;
    
    const entries = await xikizpediaService.getRecentEntries(
      Math.min(parseInt(limit as string, 10) || 50, 100),
      Math.max(parseInt(offset as string, 10) || 0, 0)
    );

    const totalCount = await xikizpediaService.getEntryCount();

    res.json({
      entries,
      totalCount,
      timestamp: new Date().toISOString()
    });
  } catch (error: any) {
    console.error('Error fetching entries:', error);
    res.status(500).json({
      error: 'Failed to fetch entries',
      timestamp: new Date().toISOString()
    });
  }
});

// Apply error handler
app.use(errorHandler);

// Create HTTP server
const server = http.createServer(app);

// WebSocket Server Setup (existing functionality with enhancements)
const wss = new WebSocketServer({ server, path: "/stream" });

interface ConnState {
  id: string;
  ws: WebSocket;
  streamId: string;
  credits: number;
  maxWindow: number;
  sendQ: Array<{ type: string; bytes: string; weight: number }>;
  lastApplied: number;
  userId?: string;
  role?: string;
}

const conns = new Map<string, ConnState>();

const stream = new Stream(STREAM_ID);
stream.startSynthetic(100); // Lower frequency for production

const snapshotCache = new RollingSnapshotCache(
  () => {
    const snap = stream.snapshot();
    const payload = Snapshot.parse({
      type: "snapshot",
      tickId: snap.tickId,
      state: snap.state
    });
    return JSON.stringify(payload);
  },
  500 // 500ms cache
);

snapshotCache.start();

wss.on("connection", (ws, req) => {
  const connId = `conn-${Math.random().toString(36).slice(2, 15)}`;
  console.log(`[${connId}] connected from ${req.socket.remoteAddress}`);

  let conn: ConnState | undefined;

  ws.on("message", async (data) => {
    try {
      const raw = JSON.parse(data.toString());
      const msg = ClientMsg.parse(raw);

      if (msg.type === "hello") {
        if (conn) {
          ws.send(JSON.stringify(Bye.parse({ type: "bye", reason: "already connected" })));
          return;
        }

        // Extract user info from headers or message
        const userId = req.headers['x-user-id'] as string || 'anonymous';
        const role = req.headers['x-user-role'] as string || config.rbac.defaultRole;

        conn = {
          id: connId,
          ws,
          streamId: msg.streamId,
          credits: 0,
          maxWindow: Math.min(msg.wantWindow, 1000),
          sendQ: [],
          lastApplied: msg.resume?.lastApplied || 0,
          userId,
          role
        };

        conns.set(connId, conn);

        // Welcome message with security features
        const welcome = Welcome.parse({
          type: "welcome",
          streamId: STREAM_ID,
          maxWindow: conn.maxWindow,
          features: ["xikizpedia", "rbac", "rate-limited"]
        });

        ws.send(JSON.stringify(welcome));

        // Send initial snapshot
        enqueueSnapshot(conn);

        console.log(`[${connId}] authenticated as ${userId} with role ${role}`);
      }

      if (msg.type === "credit" && conn) {
        conn.credits += msg.n;
        conn.lastApplied = msg.lastApplied;
        console.log(`[${connId}] +${msg.n} credits, total: ${conn.credits}`);
      }

      if (msg.type === "pong" && conn) {
        console.log(`[${connId}] pong received`);
      }
    } catch (error) {
      console.error(`[${connId}] Invalid message:`, error);
      if (conn) {
        ws.send(JSON.stringify(Bye.parse({ type: "bye", reason: "invalid message" })));
      }
    }
  });

  ws.on("close", () => {
    if (conn) {
      conns.delete(connId);
      console.log(`[${connId}] disconnected`);
    }
  });

  ws.on("error", (error) => {
    console.error(`[${connId}] WebSocket error:`, error);
    if (conn) {
      conns.delete(connId);
    }
  });
});

function enqueueSnapshot(conn: ConnState) {
  const view = snapshotCache.view();
  conn.sendQ.push({
    type: "snapshot",
    bytes: view.bytes.toString("utf8"),
    weight: 1
  });
}

// Enhanced scheduler with rate limiting per connection
setInterval(() => {
  for (const conn of conns.values()) {
    if (conn.credits <= 0 || conn.sendQ.length === 0) continue;

    // Respect rate limits based on user role
    const maxSendsPerTick = conn.role === 'admin' ? 10 : 3;
    let sent = 0;

    while (conn.sendQ.length > 0 && conn.credits > 0 && sent < maxSendsPerTick) {
      const msg = conn.sendQ.shift()!;
      try {
        conn.ws.send(msg.bytes);
        conn.credits -= msg.weight;
        sent++;
      } catch (error) {
        console.error(`[${conn.id}] Send error:`, error);
        conns.delete(conn.id);
        break;
      }
    }

    // Coalesce to snapshot if queue is too large
    if (conn.sendQ.length > 50) {
      console.log(`[${conn.id}] Queue overloaded, coalescing to snapshot`);
      conn.sendQ.length = 0;
      enqueueSnapshot(conn);
    }
  }
}, 20);

// Ping interval
setInterval(() => {
  for (const conn of conns.values()) {
    try {
      const ping = Ping.parse({ type: "ping", t: nowMs() });
      conn.ws.send(JSON.stringify(ping));
    } catch (error) {
      console.error(`[${conn.id}] Ping error:`, error);
      conns.delete(conn.id);
    }
  }
}, 30000);

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully');
  
  // Close WebSocket server
  wss.close(() => {
    console.log('WebSocket server closed');
  });

  // Close database connection
  await db.close();
  
  // Close HTTP server
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});

// Start server
server.listen(PORT, () => {
  console.log(`[server] HTTP server listening on http://localhost:${PORT}`);
  console.log(`[server] WebSocket server listening on ws://localhost:${PORT}/stream`);
  console.log(`[server] Environment: ${config.nodeEnv}`);
  console.log(`[server] Database: ${config.database.host}:${config.database.port}/${config.database.name}`);
  console.log(`[server] RBAC enabled: ${config.rbac.enabled}`);
});