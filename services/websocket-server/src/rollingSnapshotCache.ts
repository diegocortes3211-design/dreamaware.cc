export class RollingSnapshotCache {
  private cache: { tickId: number; json: string; timestamp: number } | null = null;
  private timer: NodeJS.Timeout | null = null;

  constructor(
    private buildFn: () => { tickId: number; json: string },
    private intervalMs: number = 500
  ) {}

  start() {
    if (this.timer) return;
    this.timer = setInterval(() => {
      try {
        const result = this.buildFn();
        this.cache = {
          ...result,
          timestamp: Date.now()
        };
      } catch (error) {
        console.error('Snapshot build failed:', error);
      }
    }, this.intervalMs);
    
    // Build initial cache
    try {
      const result = this.buildFn();
      this.cache = {
        ...result,
        timestamp: Date.now()
      };
    } catch (error) {
      console.error('Initial snapshot build failed:', error);
    }

    console.log(`RollingSnapshotCache started with ${this.intervalMs}ms interval`);
  }

  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
      console.log('RollingSnapshotCache stopped');
    }
  }

  view(): { tickId: number; json: string; bytes: Buffer; timestamp: number } | null {
    if (!this.cache) return null;
    return {
      ...this.cache,
      bytes: Buffer.from(this.cache.json, 'utf8')
    };
  }

  stats() {
    return {
      cached: !!this.cache,
      interval: this.intervalMs,
      cacheAge: this.cache ? Date.now() - this.cache.timestamp : null,
      cacheSize: this.cache ? this.cache.json.length : 0,
      lastTickId: this.cache?.tickId || null
    };
  }
}