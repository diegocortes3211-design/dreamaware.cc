import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { Request, Response, NextFunction } from 'express';
import { config } from '../config/index.js';

// Security headers middleware
export const securityHeaders = helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'", "ws:", "wss:"],
        },
    },
    crossOriginEmbedderPolicy: false,
});

// Rate limiting middleware
export const rateLimiter = rateLimit({
    windowMs: config.security.rateLimitWindowMs,
    max: config.security.rateLimitMaxRequests,
    message: {
        error: 'Too many requests from this IP',
        retryAfter: Math.ceil(config.security.rateLimitWindowMs / 1000),
    },
    standardHeaders: true,
    legacyHeaders: false,
});

// Payload size middleware
export const payloadSizeLimit = (req: Request, res: Response, next: NextFunction) => {
    const contentLength = req.get('content-length');
    if (contentLength && parseInt(contentLength, 10) > config.security.maxPayloadSize) {
        return res.status(413).json({
            error: 'Payload too large',
            maxSize: config.security.maxPayloadSize,
            receivedSize: parseInt(contentLength, 10),
        });
    }
    next();
};

// RBAC middleware for development
export const developmentRbac = (req: Request, res: Response, next: NextFunction) => {
    if (config.isDevelopment() && config.rbac.enabled) {
        // In development, assign default role if none exists
        if (!req.headers.authorization && !req.headers['x-user-role']) {
            req.headers['x-user-role'] = config.rbac.defaultRole;
            req.headers['x-user-id'] = 'dev-user-' + Date.now();
        }
    }
    next();
};

// Structured error response middleware
export const errorHandler = (error: any, req: Request, res: Response, next: NextFunction) => {
    console.error('Error occurred:', error);
    
    const isDev = config.isDevelopment();
    
    if (error.type === 'entity.parse.failed') {
        return res.status(400).json({
            error: 'Invalid JSON payload',
            message: isDev ? error.message : 'Malformed request body',
            timestamp: new Date().toISOString(),
        });
    }

    if (error.name === 'ValidationError') {
        return res.status(400).json({
            error: 'Validation failed',
            details: error.details || [],
            timestamp: new Date().toISOString(),
        });
    }

    // Default error response
    res.status(error.status || 500).json({
        error: error.message || 'Internal server error',
        ...(isDev && { stack: error.stack }),
        timestamp: new Date().toISOString(),
    });
};