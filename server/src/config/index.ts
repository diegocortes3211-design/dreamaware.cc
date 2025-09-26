import { config as dotenvConfig } from 'dotenv';

// Load environment variables
dotenvConfig();

export const config = {
    port: parseInt(process.env.PORT || '8080', 10),
    nodeEnv: process.env.NODE_ENV || 'development',
    
    database: {
        url: process.env.DATABASE_URL || 'postgresql://xikizpedia:devpassword123@localhost:5432/xikizpedia_dev',
        host: process.env.DB_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT || '5432', 10),
        name: process.env.DB_NAME || 'xikizpedia_dev',
        user: process.env.DB_USER || 'xikizpedia',
        password: process.env.DB_PASSWORD || 'devpassword123',
    },

    security: {
        rateLimitWindowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000', 10), // 15 minutes
        rateLimitMaxRequests: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100', 10),
        maxPayloadSize: parseInt(process.env.MAX_PAYLOAD_SIZE || '1048576', 10), // 1MB
    },

    rbac: {
        defaultRole: process.env.DEFAULT_ROLE || 'user',
        adminRole: process.env.ADMIN_ROLE || 'admin',
        enabled: process.env.ENABLE_RBAC === 'true',
    },

    logging: {
        level: process.env.LOG_LEVEL || 'info',
    },

    isDevelopment: () => config.nodeEnv === 'development',
    isProduction: () => config.nodeEnv === 'production',
};