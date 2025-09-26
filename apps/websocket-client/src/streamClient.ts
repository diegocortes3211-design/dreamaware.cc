import { ServerMsg, Snapshot, Delta } from "./types";

type State = {
  tickId: number;
  count: number;
};

type Events = {
  onState: (state: State) => void;
  onStatus: (status: string) => void;
  onMetrics: (metrics: { credits: number, qLen: number }) => void;
};

export class StreamClient {
  private ws: WebSocket | null = null;
  private state: State = { tickId: 0, count: 0 };
  private credits = 0;
  private maxWindow = 16;
  private creditThreshold = 8;
  private paused = false;
  private msgQueue: (Delta | Snapshot)[] = [];

  constructor(
    private url: string,
    private streamId: string,
    private events: Events
  ) {}

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => {
      this.events.onStatus("Connected");
      this.send({
        type: "hello",
        streamId: this.streamId,
        wantWindow: this.maxWindow,
        resume: { lastApplied: this.state.tickId },
      });
    };
    this.ws.onmessage = (event) => this.onMessage(event.data);
    this.ws.onclose = () => {
      this.events.onStatus("Disconnected");
      setTimeout(() => this.connect(), 2000);
    };
    this.ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      this.events.onStatus("Error");
    };
  }

  togglePause() {
    this.paused = !this.paused;
    this.events.onStatus(this.paused ? "Paused" : "Running");
    if (!this.paused) {
      this.processQueue();
    }
  }

  private send(msg: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  private onMessage(raw: string) {
    const msg = JSON.parse(raw) as ServerMsg;
    switch (msg.type) {
      case "welcome":
        this.maxWindow = msg.maxWindow;
        this.creditThreshold = Math.max(1, Math.floor(msg.maxWindow / 2));
        this.credits = msg.maxWindow;
        this.events.onMetrics({ credits: this.credits, qLen: this.msgQueue.length });
        break;
      case "ping":
        this.send({ type: "pong", t: msg.t });
        break;
      case "snapshot":
      case "delta":
        this.msgQueue.push(msg);
        this.msgQueue.sort((a, b) => a.tickId - b.tickId);
        if (!this.paused) {
          this.processQueue();
        }
        break;
      case "bye":
        this.ws?.close();
        break;
    }
  }

  private processQueue() {
    while (this.msgQueue.length > 0) {
      const msg = this.msgQueue[0];
      if (msg.tickId > this.state.tickId) {
        if (msg.type === 'snapshot') {
          this.state.tickId = msg.tickId;
          this.state.count = msg.state.count;
        } else if (msg.type === 'delta' && msg.tickId === this.state.tickId + 1) {
          this.state.tickId = msg.tickId;
          this.state.count = msg.payload.count;
        } else {
          // out of order delta, wait for snapshot or correct delta
          break;
        }
        this.msgQueue.shift();
        this.credits--;
      } else {
        // old message, discard
        this.msgQueue.shift();
      }
    }

    this.events.onState(this.state);
    this.events.onMetrics({ credits: this.credits, qLen: this.msgQueue.length });

    if (this.credits < this.creditThreshold) {
      const toAdd = this.maxWindow - this.credits;
      this.send({ type: "credit", n: toAdd, lastApplied: this.state.tickId });
      this.credits += toAdd;
      this.events.onMetrics({ credits: this.credits, qLen: this.msgQueue.length });
    }
  }
}