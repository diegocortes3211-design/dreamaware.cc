import { createGzip } from 'node:zlib';
import { pipeline } from 'node:stream/promises';
import { Readable } from 'node:stream';

interface CachedSnapshot {
  tickId: number;
  timestamp: number;
  data: Buffer;  // gzipped JSON
  uncompressed: number; // original size bytes
}

interface GraphState {
  head: number;
  nodes: Map<string, any>;
  edges: Map<string, any>;
}

interface WebSocketConnection {
  id: string;
  sendQ: Array<{
    type: string;
    tickId?: number;
    bytes?: string;
    encoding?: string;
    size?: number;
    weight: number;
    message?: string;
    currentTick?: number;
    cacheTick?: number;
  }>;
}

export class SnapshotCache {
  private cache: CachedSnapshot | null = null;
  private building = false;
  private readonly cacheInterval: number;
  private timer: NodeJS.Timeout | null = null;
  private buildCount = 0;
  private errorCount = 0;

  constructor(
    private state: GraphState,
    cacheIntervalMs = 500
  ) {
    this.cacheInterval = cacheIntervalMs;
  }

  start() {
    if (this.timer) return; // Already started
    this.timer = setInterval(() => this.buildSnapshot(), this.cacheInterval);
    this.buildSnapshot(); // Initial build
    console.log(`SnapshotCache started with ${this.cacheInterval}ms interval`);
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
      console.log('SnapshotCache stopped');
    }
  }

  // Non-blocking: returns cached snapshot + deltas needed to catch up
  getSnapshot(): { snapshot: CachedSnapshot | null; deltasNeeded: number } {
    const deltasNeeded = this.cache ? this.state.head - this.cache.tickId : 0;
    return { snapshot: this.cache, deltasNeeded };
  }

  private async buildSnapshot() {
    if (this.building) return; // Skip if already building

    this.building = true;
    const startTime = process.hrtime.bigint();

    try {
      await this.buildInChunks();
      this.buildCount++;
    } catch (error) {
      this.errorCount++;
      console.error('Snapshot build failed:', error);
    } finally {
      this.building = false;

      const endTime = process.hrtime.bigint();
      const durationMs = Number(endTime - startTime) / 1000000;

      if (this.cache) {
        console.log(`Snapshot #${this.buildCount}: tick=${this.cache.tickId}, ${Math.round(this.cache.data.length/1024)}KB, ${durationMs.toFixed(1)}ms`);
      }
    }
  }

  private async buildInChunks() {
    const head = this.state.head;

    // Serialize incrementally to avoid blocking event loop
    const chunks: string[] = [];

    // JSON header
    chunks.push(`{"type":"snapshot","tickId":${head},"timestamp":${Date.now()},"state":{"nodes":[`);

    // Serialize nodes in chunks
    const nodeEntries = Array.from(this.state.nodes.entries());
    for (let i = 0; i < nodeEntries.length; i++) {
      if (i > 0) chunks.push(',');
      chunks.push(JSON.stringify(nodeEntries[i][1]));

      // Yield control every 50 items to keep event loop responsive
      if (i > 0 && i % 50 === 0) {
        await this.yieldControl();
      }
    }

    chunks.push('],"edges":[');

    // Serialize edges in chunks
    const edgeEntries = Array.from(this.state.edges.entries());
    for (let i = 0; i < edgeEntries.length; i++) {
      if (i > 0) chunks.push(',');
      chunks.push(JSON.stringify(edgeEntries[i][1]));

      // Yield control every 50 items
      if (i > 0 && i % 50 === 0) {
        await this.yieldControl();
      }
    }

    chunks.push(']}"}');

    // Compress the complete JSON
    const jsonStr = chunks.join('');
    const compressed = await this.compress(jsonStr);

    // Update cache atomically
    this.cache = {
      tickId: head,
      timestamp: Date.now(),
      data: compressed,
      uncompressed: Buffer.byteLength(jsonStr, 'utf8')
    };
  }

  private yieldControl(): Promise<void> {
    return new Promise(resolve => setImmediate(resolve));
  }

  private async compress(data: string): Promise<Buffer> {
    const chunks: Buffer[] = [];
    const readable = Readable.from([data]);
    const gzip = createGzip({
      level: 6, // Good compression without excessive CPU
      chunkSize: 16 * 1024 // 16KB chunks
    });

    await pipeline(
      readable,
      gzip,
      async function* (source) {
        for await (const chunk of source) {
          chunks.push(chunk as Buffer);
          yield chunk;
        }
      }
    );

    return Buffer.concat(chunks);
  }

  getStats() {
    const cacheAge = this.cache ? Date.now() - this.cache.timestamp : null;
    const compressionRatio = this.cache ?
      (this.cache.data.length / this.cache.uncompressed * 100) : null;

    return {
      cached: !!this.cache,
      building: this.building,
      buildCount: this.buildCount,
      errorCount: this.errorCount,
      cacheAge,
      cacheSize: this.cache?.data.length || 0,
      uncompressedSize: this.cache?.uncompressed || 0,
      compressionRatio: compressionRatio ? compressionRatio.toFixed(1) + '%' : null,
      interval: this.cacheInterval
    };
  }
}

export class StreamServer {
  private snapshotCache: SnapshotCache;
  private readonly STALENESS_LIMIT = 100; // ticks
  private readonly LARGE_SNAPSHOT_THRESHOLD = 512 * 1024; // 512KB

  constructor(private state: GraphState) {
    this.snapshotCache = new SnapshotCache(state, 500);
  }

  start() {
    this.snapshotCache.start();
  }

  stop() {
    this.snapshotCache.stop();
  }

  // Handle snapshot request from client (non-blocking)
  handleSnapshotRequest(conn: WebSocketConnection, clientTickId: number = 0) {
    const { snapshot, deltasNeeded } = this.snapshotCache.getSnapshot();

    if (!snapshot) {
      // No cache available yet
      conn.sendQ.push({
        type: 'snapshot_pending',
        message: 'Snapshot building, sending deltas...',
        weight: 1
      });
      return false;
    }

    const staleness = this.state.head - snapshot.tickId;

    if (staleness > this.STALENESS_LIMIT) {
      // Cache too stale, send fresh deltas instead
      conn.sendQ.push({
        type: 'snapshot_stale',
        currentTick: this.state.head,
        cacheTick: snapshot.tickId,
        message: `Cache ${staleness} ticks behind, sending deltas`,
        weight: 1
      });
      return false;
    }

    // Send cached snapshot
    this.sendSnapshot(conn, snapshot);
    return true;
  }

  private sendSnapshot(conn: WebSocketConnection, snapshot: CachedSnapshot) {
    const compressed = snapshot.data;
    const isLarge = compressed.length > this.LARGE_SNAPSHOT_THRESHOLD;
    const base64Data = compressed.toString('base64');
    const weight = Math.max(1, Math.ceil(compressed.length / (64 * 1024)));

    const message = {
      type: isLarge ? 'snapshot_large' : 'snapshot',
      tickId: snapshot.tickId,
      bytes: base64Data,
      encoding: 'gzip+base64',
      size: compressed.length,
      weight
    };

    conn.sendQ.push(message);

    console.log(`Sent ${isLarge ? 'large ' : ''}snapshot to ${conn.id}: tick=${snapshot.tickId}, ${Math.round(compressed.length/1024)}KB, weight=${weight}`);
  }

  // Health check endpoint data
  getHealth() {
    const cacheStats = this.snapshotCache.getStats();
    const stateStats = {
      head: this.state.head,
      nodes: this.state.nodes.size,
      edges: this.state.edges.size
    };

    return {
      snapshot: cacheStats,
      state: stateStats,
      limits: {
        stalenessLimit: this.STALENESS_LIMIT,
        largeThreshold: this.LARGE_SNAPSHOT_THRESHOLD
      },
      uptime: process.uptime()
    };
  }

  // Metrics for monitoring
  getMetrics() {
    const stats = this.snapshotCache.getStats();
    return {
      snapshot_builds_total: stats.buildCount,
      snapshot_errors_total: stats.errorCount,
      snapshot_cache_age_ms: stats.cacheAge || 0,
      snapshot_cache_size_bytes: stats.cacheSize,
      snapshot_compression_ratio: parseFloat(stats.compressionRatio?.replace('%', '') || '0'),
      graph_nodes_total: this.state.nodes.size,
      graph_edges_total: this.state.edges.size,
      graph_head_tick: this.state.head
    };
  }
}
// Export with alias for backwards compatibility
export const RollingSnapshotCache = SnapshotCache;
