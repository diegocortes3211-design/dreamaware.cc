# WebSocket Client - Backpressure Demo

Interactive demonstration of WebSocket backpressure handling with credit-based flow control.

## Features

- **Credit-Based Flow Control**: Client manages server send rate via credits
- **Visual Metrics**: Real-time display of queue length, credits, and message counts
- **Backpressure Simulation**: Pause/resume message processing to test flow control
- **Message Types**: Handles deltas, snapshots, and control messages
- **Performance Monitoring**: Tracks snapshots applied and deltas processed

## Development

```bash
# From repository root (requires websocket-server running)
npm run dev:client

# Or from this directory
npm run dev
```

## Building

```bash
npm run build
```

## Usage

1. Start the WebSocket server first: `npm run dev:server`
2. Start this client: `npm run dev:client`
3. Open http://localhost:3000
4. Observe real-time metrics
5. Click "Pause Drain" to simulate backpressure
6. Watch queue length grow while tickId continues updating
7. Click "Resume Drain" to process queued messages

## Configuration

- **Port**: 3000 (development)
- **Server**: ws://localhost:8080/stream
- **Build Output**: `dist/`
- **Technologies**: TypeScript, Vite, Zod

## Message Flow

1. Client connects and sends initial credit
2. Server streams deltas at high frequency
3. Client processes messages and grants more credits
4. When paused, client stops draining but server continues sending snapshots
5. Resume processes all queued deltas rapidly

## Architecture

- `src/main.ts` - Application entry point and DOM manipulation
- `src/streamClient.ts` - WebSocket client implementation  
- `src/types.ts` - Message type definitions with Zod schemas
- `index.html` - UI layout and styling