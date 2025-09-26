# DreamAware Interactive Experience

A modern monorepo containing interactive visual applications with real-time WebSocket streaming, particle effects, and cryptographic ledger services.

## 🏗️ Repository Structure

```
dreamaware.cc/
├── apps/                           # Frontend Applications
│   ├── main-app/                   # React particle effects demo
│   │   ├── src/                    # React components & logic
│   │   ├── public/                 # Static assets
│   │   └── package.json
│   ├── websocket-client/           # WebSocket backpressure demo
│   │   ├── src/                    # Client implementation
│   │   └── package.json
│   └── orb-demo.html              # Standalone HTML/JS demo
├── services/                       # Backend Services
│   ├── websocket-server/          # WebSocket server with flow control
│   │   ├── src/                   # TypeScript server code
│   │   └── package.json
│   └── ledger/                    # Cryptographic ledger service
│       ├── server.go              # Go implementation
│       └── package.json
├── packages/                       # Shared libraries (future)
├── tools/                         # Build tools & scripts (future)
├── docs/                          # Documentation (future)
└── package.json                   # Workspace root
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ for web applications
- Go 1.19+ for ledger service
- CockroachDB for ledger persistence (optional)

### Development

```bash
# Install all dependencies
npm run install-all

# Start the main React app (particle effects)
npm run dev:main

# Start the WebSocket demo client
npm run dev:client  

# Start the WebSocket server
npm run dev:server

# Start the Go ledger service
npm run dev:ledger
```

### Building

```bash
# Build all projects
npm run build

# Build specific projects
npm run build:main
npm run build:client
npm run build:server
```

## 🎨 Applications

### Main App (`apps/main-app`)
Interactive particle effects system with:
- Real-time particle physics
- Customizable visual presets (LSD, MDMA, Ket themes)
- Mouse-driven particle spawning
- React + TypeScript + Vite

**URL**: `http://localhost:5173`

### WebSocket Client (`apps/websocket-client`)
Demonstrates backpressure handling with:
- Credit-based flow control
- Queue length visualization
- Pause/resume functionality
- Real-time metrics display

**URL**: `http://localhost:3000`

### Standalone Orb Demo (`apps/orb-demo.html`)
Complete HTML/JS implementation featuring:
- Canvas-based particle system
- Text orbit animations
- Interactive controls
- No build step required

## 🔧 Services

### WebSocket Server (`services/websocket-server`)
High-performance streaming server with:
- Credit-based backpressure management
- Rolling snapshot cache (500ms intervals)
- Non-blocking delta streaming
- TypeScript + Node.js

**Port**: `8080`

### Ledger Service (`services/ledger`)
Cryptographic ledger with:
- Vault Transit Ed25519 signatures
- CockroachDB persistence
- RESTful append-only API
- Go implementation

**Port**: `8088`

## 🛠️ Development Tools

### Code Quality
```bash
# Format all code
npm run format

# Check formatting
npm run format:check

# Lint (basic setup)
npm run lint

# Clean build artifacts
npm run clean
```

### Configuration Files
- **Prettier**: `.prettierrc` - Code formatting rules
- **ESLint**: `.eslintrc.json` - Basic linting (needs TypeScript setup)
- **TypeScript**: `tsconfig.json` - Individual per-app configs
- **Vite**: `vite.config.ts` - Build configuration for web apps

## 🏃‍♂️ Running Everything Together

For full-stack development:

```bash
# Terminal 1: WebSocket Server
npm run dev:server

# Terminal 2: Ledger Service  
npm run dev:ledger

# Terminal 3: WebSocket Client
npm run dev:client

# Terminal 4: Main App
npm run dev:main
```

## 📋 Features

### Visual Effects
- ✅ Particle physics simulation
- ✅ Mouse interaction
- ✅ Color themes and presets
- ✅ Trail effects and glows
- ✅ Real-time parameter adjustment

### WebSocket Streaming
- ✅ Credit-based flow control
- ✅ Backpressure handling
- ✅ Rolling snapshots
- ✅ Delta compression
- ✅ Client pause/resume

### Cryptography
- ✅ Ed25519 signatures via HashiCorp Vault
- ✅ Append-only ledger
- ✅ Secure payload handling
- ✅ Database transactions

## 🎯 Future Enhancements

- [ ] Shared TypeScript types package
- [ ] CI/CD pipeline setup
- [ ] Docker containerization  
- [ ] Comprehensive test suites
- [ ] Performance monitoring
- [ ] Security audit tooling
- [ ] Documentation site generation

## 📄 License

ISC License - see LICENSE file for details.

## 🤝 Contributing

This repository is organized as a modern monorepo with clear separation of concerns. Each application and service is self-contained with its own build process and dependencies.

For development:
1. Choose the app/service you want to work on
2. Navigate to its directory
3. Review its individual README (coming soon)
4. Use the appropriate npm workspace commands from the root

---

Built with ❤️ for interactive visual experiences and real-time data streaming.