// Security middleware for Node.js server
import { IncomingMessage, ServerResponse } from "http";

export interface SecurityConfig {
  hstsMaxAge?: number;
  hstsIncludeSubdomains?: boolean;
  hstsPreload?: boolean;
  cspReportOnly?: boolean;
  cspReportUri?: string;
  frameOptions?: 'DENY' | 'SAMEORIGIN';
  contentTypeOptions?: boolean;
  xssProtection?: boolean;
  referrerPolicy?: string;
}

const defaultConfig: Required<SecurityConfig> = {
  hstsMaxAge: 31536000, // 1 year
  hstsIncludeSubdomains: true,
  hstsPreload: false,
  cspReportOnly: true,
  cspReportUri: '/api/csp-report',
  frameOptions: 'DENY',
  contentTypeOptions: true,
  xssProtection: true,
  referrerPolicy: 'strict-origin-when-cross-origin'
};

export function securityMiddleware(config: SecurityConfig = {}) {
  const finalConfig = { ...defaultConfig, ...config };

  return (req: IncomingMessage, res: ServerResponse, next?: () => void) => {
    // HSTS - HTTP Strict Transport Security
    let hstsValue = `max-age=${finalConfig.hstsMaxAge}`;
    if (finalConfig.hstsIncludeSubdomains) hstsValue += '; includeSubDomains';
    if (finalConfig.hstsPreload) hstsValue += '; preload';
    res.setHeader('Strict-Transport-Security', hstsValue);

    // Content Security Policy
    const cspDirectives = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "connect-src 'self' ws: wss:",
      "font-src 'self'",
      "object-src 'none'",
      "media-src 'self'",
      "frame-src 'none'",
      "worker-src 'self'",
      "child-src 'none'",
      "base-uri 'self'",
      "form-action 'self'"
    ];

    if (finalConfig.cspReportUri) {
      cspDirectives.push(`report-uri ${finalConfig.cspReportUri}`);
    }

    const cspHeader = finalConfig.cspReportOnly 
      ? 'Content-Security-Policy-Report-Only' 
      : 'Content-Security-Policy';
    
    res.setHeader(cspHeader, cspDirectives.join('; '));

    // X-Frame-Options
    res.setHeader('X-Frame-Options', finalConfig.frameOptions);

    // X-Content-Type-Options
    if (finalConfig.contentTypeOptions) {
      res.setHeader('X-Content-Type-Options', 'nosniff');
    }

    // X-XSS-Protection (legacy)
    if (finalConfig.xssProtection) {
      res.setHeader('X-XSS-Protection', '1; mode=block');
    }

    // Referrer-Policy
    res.setHeader('Referrer-Policy', finalConfig.referrerPolicy);

    // Permissions-Policy
    const permissions = [
      'camera=()',
      'microphone=()',
      'geolocation=()',
      'payment=()',
      'usb=()',
      'bluetooth=()',
      'magnetometer=()',
      'gyroscope=()',
      'accelerometer=()',
      'ambient-light-sensor=()'
    ];
    res.setHeader('Permissions-Policy', permissions.join(', '));

    // Remove potentially leaky headers
    res.removeHeader('X-Powered-By');
    res.setHeader('Server', 'DreamAware/1.0');

    // Call next middleware if provided
    if (next) next();
  };
}

// CSP Report endpoint handler
export function cspReportHandler(req: IncomingMessage, res: ServerResponse) {
  if (req.method !== 'POST') {
    res.writeHead(405, { 'Allow': 'POST' });
    res.end();
    return;
  }

  let body = '';
  req.on('data', chunk => {
    body += chunk.toString();
  });

  req.on('end', () => {
    try {
      const report = JSON.parse(body);
      console.warn('[CSP Violation]', {
        timestamp: new Date().toISOString(),
        userAgent: req.headers['user-agent'],
        report: report['csp-report']
      });
      
      res.writeHead(204);
      res.end();
    } catch (error) {
      console.error('Invalid CSP report:', error);
      res.writeHead(400);
      res.end();
    }
  });
}