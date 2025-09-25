import './style.css';
import { StreamClient } from './streamClient.ts';

const app = document.querySelector<HTMLDivElement>('#app')!;
const statusEl = app.querySelector<HTMLDivElement>('#status')!;
const tickEl = app.querySelector<HTMLDivElement>('#tick')!;
const stateEl = app.querySelector<HTMLDivElement>('#state')!;
const qLenEl = app.querySelector<HTMLDivElement>('#q_len')!;
const creditsEl = app.querySelector<HTMLDivElement>('#credits')!;
const logsEl = app.querySelector<HTMLPreElement>('#logs')!;
const pauseBtn = app.querySelector<HTMLButtonElement>('#pauseBtn')!;

const client = new StreamClient(
  'ws://localhost:8080',
  'main_stream',
  {
    onState: (state) => {
      tickEl.textContent = `Tick: ${state.tickId}`;
      stateEl.textContent = `State: ${state.count}`;
      log(`Applied state for tick ${state.tickId}`);
    },
    onStatus: (status) => {
      statusEl.textContent = status;
      log(`Status changed: ${status}`);
    },
    onMetrics: (metrics) => {
      creditsEl.textContent = `Credits: ${metrics.credits}`;
      qLenEl.textContent = `Client Q: ${metrics.qLen}`;
    }
  }
);

client.connect();

pauseBtn.addEventListener('click', () => {
  client.togglePause();
  pauseBtn.textContent = pauseBtn.textContent === 'Pause' ? 'Resume' : 'Pause';
});

function log(message: string) {
  const time = new Date().toLocaleTimeString();
  logsEl.textContent = `[${time}] ${message}\n` + logsEl.textContent;
}