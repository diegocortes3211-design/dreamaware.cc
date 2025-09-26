# Xikizpedia Integration - Local Development Guide

## Overview

This repository contains the Xikizpedia integration with enterprise-ready features including:

- ✅ **Runtime Guardrails**: RBAC, security headers, rate limiting, payload size limits
- ✅ **Database Layer**: PostgreSQL with JSONB GIN indexes and full-text search
- ✅ **Local Development**: Docker Compose setup for Postgres
- ✅ **CI/CD**: Automated testing with database services
- ✅ **API Endpoints**: RESTful API for creating and searching entries

## Quick Start

### 1. Prerequisites

- Node.js 20+
- Docker and Docker Compose
- npm or yarn

### 2. Setup Local Development

```bash
# Clone and install dependencies
npm install
cd server && npm install
cd ../client && npm install
cd ..

# Start local Postgres database
docker-compose up -d postgres

# Wait for database to be ready (check with)
docker-compose logs postgres

# Run database migrations
npm run db:migrate

# Seed initial data
npm run db:seed

# Start development servers (both client and server)
npm run dev
```

The server will be available at:
- HTTP API: `http://localhost:8080`
- WebSocket: `ws://localhost:8080/stream`
- Client: `http://localhost:3000`

### 3. Environment Configuration

Copy `.env.example` to `.env` and adjust settings:

```bash
cp .env.example .env
```

Key environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `NODE_ENV`: development/production
- `ENABLE_RBAC`: Enable role-based access control
- `RATE_LIMIT_MAX_REQUESTS`: Rate limiting threshold

## API Smoke Testing

### Health Check
```bash
curl http://localhost:8080/health
```

### Create a Xikizpedia Entry
```bash
curl -X POST http://localhost:8080/api/xikizpedia/entries \
  -H "Content-Type: application/json" \
  -d '{
    "textContent": "The universe speaks in patterns, and we are its listeners",
    "metadata": {
      "category": "philosophy",
      "type": "wisdom"
    }
  }'
```

### Get Entry by Void ID
```bash
# Use the voidId from the previous response
curl http://localhost:8080/api/xikizpedia/entries/{voidId}
```

### Search Entries
```bash
curl "http://localhost:8080/api/xikizpedia/search?q=universe&limit=10"
```

### List Recent Entries
```bash
curl "http://localhost:8080/api/xikizpedia/entries?limit=20"
```

## WebSocket Testing

You can test the WebSocket connection with the client at `http://localhost:3000` or use a WebSocket client:

```javascript
const ws = new WebSocket('ws://localhost:8080/stream');

ws.onopen = () => {
  // Send hello message
  ws.send(JSON.stringify({
    type: 'hello',
    streamId: 'test',
    wantWindow: 10
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

## Database Schema

The integration creates the following main tables:

- `xikizpedia.entries`: Main content storage with SHA-256 hashes
- `xikizpedia.users`: User management with RBAC
- `xikizpedia.sessions`: WebSocket session tracking

### Key Indexes
- GIN indexes on JSONB fields for fast metadata queries
- Full-text search indexes on content
- Performance indexes on common query patterns

## Security Features

### Runtime Guardrails
- **Security Headers**: Helmet.js with CSP, XSS protection
- **Rate Limiting**: IP-based request throttling
- **Payload Limits**: Configurable size limits for requests
- **RBAC**: Role-based access control (admin, user, viewer)

### Development vs Production
- Development mode sets default RBAC roles
- Production requires proper authentication headers
- Environment-specific error reporting

## Monitoring and Observability

### Health Endpoints
- `/health`: Basic service health check
- WebSocket server includes connection metrics

### Database Monitoring
- Connection pooling with configurable limits
- Query performance logging
- Error tracking and reporting

## Troubleshooting

### Database Connection Issues
```bash
# Check if Postgres is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Build Issues
```bash
# Clean and rebuild
rm -rf server/dist client/dist
npm run build
```

### Port Conflicts
- Server: Port 8080 (configurable via PORT env var)
- Client: Port 3000
- Postgres: Port 5432

Change ports in `docker-compose.yml` or environment variables as needed.

## Production Deployment

### Environment Setup
1. Set `NODE_ENV=production`
2. Configure production database URL
3. Set up proper authentication/authorization
4. Configure rate limits for production load
5. Set up monitoring and logging

### CI/CD Pipeline
The GitHub Actions workflow:
1. Runs tests with PostgreSQL service
2. Applies database migrations
3. Seeds test data
4. Builds and tests the application
5. Deploys static assets to GitHub Pages

## Next Steps

This integration provides a solid foundation for:
- Scaling to handle larger datasets
- Adding more sophisticated search capabilities
- Implementing advanced RBAC features
- Building analytics and reporting
- Adding real-time collaboration features

## Architecture Decisions

- **PostgreSQL**: Chosen for JSONB support and full-text search
- **Express + WebSocket**: RESTful API with real-time capabilities
- **TypeScript**: Type safety and better development experience
- **Docker Compose**: Simplified local development
- **Zod**: Runtime type validation for API requests