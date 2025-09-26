# DreamAware Xikizpedia Integration

A production-ready WebSocket server with PostgreSQL integration, featuring enterprise-grade security, RBAC, and real-time capabilities.

## 🚀 Features

- ✅ **Enterprise Security**: Helmet.js security headers, rate limiting, payload size controls
- ✅ **Database Integration**: PostgreSQL with JSONB GIN indexing and full-text search  
- ✅ **RBAC Support**: Role-based access control with development defaults
- ✅ **Real-time WebSocket**: Credit-based backpressure with rate limiting per role
- ✅ **RESTful API**: Complete CRUD operations for Xikizpedia entries
- ✅ **SHA-256 Addressing**: Content-addressed storage with 8-character void IDs
- ✅ **Docker Development**: One-command local PostgreSQL setup
- ✅ **CI/CD Ready**: Automated testing with database services

## 🏁 Quick Start

```bash
# Install dependencies
npm install && cd server && npm install && cd ../client && npm install && cd ..

# Start database
docker compose up -d postgres

# Setup database
npm run db:migrate && npm run db:seed  

# Start development servers
npm run dev
```

**Endpoints:**
- HTTP API: `http://localhost:8080`
- WebSocket: `ws://localhost:8080/stream` 
- Client: `http://localhost:3000`

## 📡 API Examples

```bash
# Health check
curl http://localhost:8080/health

# Create entry
curl -X POST http://localhost:8080/api/xikizpedia/entries \
  -H "Content-Type: application/json" \
  -d '{"textContent": "Your wisdom here", "metadata": {"type": "knowledge"}}'

# Search entries  
curl "http://localhost:8080/api/xikizpedia/search?q=wisdom"

# Get by void ID
curl http://localhost:8080/api/xikizpedia/entries/{voidId}
```

## 🏗️ Architecture

- **Backend**: Node.js + TypeScript + Express + WebSocket
- **Database**: PostgreSQL 15 with JSONB and full-text search
- **Security**: Helmet.js, express-rate-limit, Zod validation
- **Real-time**: WebSocket with credit-based flow control
- **Development**: Docker Compose, automated migrations

## 📚 Documentation

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup, testing, and deployment instructions.

---

*Built with enterprise-grade patterns for scalable, secure real-time applications.*