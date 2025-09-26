type Listener = (tickId: number, delta: { count: number }) => void;

export class Stream {
  readonly id: string;
  private head = 1; // Start with 1 to satisfy Zod validation
  private state = { count: 0 };
  private listeners = new Set<Listener>();

  constructor(id: string) {
    this.id = id;
  }

  subscribe(cb: Listener) {
    this.listeners.add(cb);
    return () => this.listeners.delete(cb);
  }

  headTick(): number { return this.head; }

  snapshot() {
    return { tickId: this.head, state: { ...this.state } };
  }

  startSynthetic(ratePerSec: number) {
    const interval = Math.max(1, Math.floor(1000 / ratePerSec));
    setInterval(() => {
      this.head += 1;
      this.state.count += 1;
      const delta = { count: this.state.count };
      for (const l of this.listeners) l(this.head, delta);
    }, interval);
  }
}