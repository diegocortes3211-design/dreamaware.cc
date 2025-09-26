# WebSocket Server - Streaming with Backpressure

High-performance WebSocket server implementing credit-based flow control and rolling snapshots.

## Features

- **Credit-Based Flow Control**: Prevents overwhelming slow clients
- **Rolling Snapshots**: Non-blocking cached snapshots every 500ms
- **Delta Streaming**: Efficient incremental updates
- **Connection Management**: Handles multiple clients with individual flow control
- **Performance Optimized**: Non-blocking operations for high throughput

## Development

```bash
# From repository root
npm run dev:server

# Or from this directory
npm run dev
```

## Building

```bash
npm run build
```

## Configuration

- **Port**: 8080
- **Endpoint**: `/stream`  
- **Snapshot Interval**: 500ms
- **Delta Rate**: 500/sec (configurable)
- **Technologies**: Node.js, TypeScript, WS library, Zod

## Architecture

- `src/index.ts` - Main server setup and client connection handling
- `src/stream.ts` - Delta stream simulation and state management
- `src/snapshotCache.ts` - Rolling snapshot cache implementation
- `src/types.ts` - Message schemas and type definitions
- `src/util.ts` - Utility functions

## Message Types

### Client → Server
- `hello` - Initial connection with protocol info
- `credit` - Grant credits for server to send messages
- `pong` - Heartbeat response

### Server → Client  
- `welcome` - Connection acknowledgment
- `delta` - Incremental state update
- `snapshot` - Full state at point in time
- `ping` - Heartbeat request
- `bye` - Clean disconnection

## Flow Control

1. Client connects and sends `hello`
2. Server responds with `welcome`
3. Client grants initial credits
4. Server sends deltas consuming credits
5. Client processes messages and grants more credits
6. Server falls back to snapshots when no credits available

## Extending

To add new delta types, update:
1. `src/stream.ts` - Add new state fields and delta generation
2. `src/types.ts` - Define new message schemas
3. Client code - Handle new message types