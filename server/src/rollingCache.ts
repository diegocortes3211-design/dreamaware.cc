export class RollingSnapshotCache {
    private cache: { bytes: Buffer } | null = null;
    private builder: () => string;
    private intervalMs: number;
    private timer: NodeJS.Timeout | null = null;

    constructor(builder: () => string, intervalMs = 500) {
        this.builder = builder;
        this.intervalMs = intervalMs;
    }

    start() {
        if (this.timer) return;
        this.buildSnapshot();
        this.timer = setInterval(() => {
            this.buildSnapshot();
        }, this.intervalMs);
    }

    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    private buildSnapshot() {
        try {
            const json = this.builder();
            this.cache = {
                bytes: Buffer.from(json, 'utf8')
            };
        } catch (error) {
            console.error('Snapshot build failed:', error);
        }
    }

    view() {
        return this.cache || { bytes: Buffer.from('{"error":"no cache"}') };
    }

    stats() {
        return {
            cached: !!this.cache,
            cacheSize: this.cache?.bytes.length || 0,
            interval: this.intervalMs
        };
    }
}