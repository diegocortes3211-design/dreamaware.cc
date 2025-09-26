# Multi-stage Dockerfile for security hardening
# Build stage
FROM node:20-alpine AS build

# Create non-root user for build process
RUN addgroup -g 1001 -S nodejs && \
    adduser -S dreamaware -u 1001 -G nodejs

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY client/package*.json ./client/

# Install dependencies (including dev dependencies for build)
RUN npm ci --only=production --no-audit --no-fund && \
    cd client && npm ci --only=production --no-audit --no-fund

# Copy source code
COPY . .
RUN chown -R dreamaware:nodejs /app

# Switch to non-root user
USER dreamaware

# Build the application
RUN npm run build && \
    cd client && npm run build && \
    cd .. && npx vite build

# Production stage
FROM node:20-alpine AS production

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S dreamaware -u 1001 -G nodejs

# Set working directory
WORKDIR /app

# Copy package.json for production dependencies only
COPY package*.json ./
COPY client/package*.json ./client/

# Install only production dependencies
RUN npm ci --only=production --no-audit --no-fund && \
    cd client && npm ci --only=production --no-audit --no-fund && \
    npm cache clean --force

# Copy built application from build stage
COPY --from=build --chown=dreamaware:nodejs /app/dist ./dist
COPY --from=build --chown=dreamaware:nodejs /app/client/dist ./client/dist

# Copy necessary runtime files
COPY --chown=dreamaware:nodejs server ./server

# Remove unnecessary files and create secure directories
RUN rm -rf /home/dreamaware/.npm /tmp/* /var/cache/apk/* && \
    mkdir -p /app/logs /app/tmp && \
    chown -R dreamaware:nodejs /app

# Security hardening
RUN chmod -R 750 /app && \
    chmod -R 640 /app/dist /app/client/dist

# Switch to non-root user
USER dreamaware

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/healthz', (r) => { process.exit(r.statusCode === 200 ? 0 : 1) })"

# Expose port (non-privileged)
EXPOSE 3000

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Set resource limits and run application
CMD ["node", "--max-old-space-size=256", "server/dist/index.js"]