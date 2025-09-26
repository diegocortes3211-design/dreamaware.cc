/**
 * Fortress v4 Next.js API Middleware
 * Integrates policy enforcement into Next.js API routes
 */

import { NextRequest, NextResponse } from 'next/server';
import { evaluateApiPolicy, evaluateLedgerPolicy, PolicyResult } from './client';

export interface PolicyMiddlewareOptions {
  policyType: 'api' | 'ledger' | 'custom';
  customEvaluator?: (input: unknown) => Promise<PolicyResult>;
  onViolation?: (violations: string[], req: NextRequest) => NextResponse;
  enableAuditLog?: boolean;
  skipPaths?: string[];
}

export interface RequestContext {
  method: string;
  path: string;
  headers: Record<string, string>;
  remote_addr: string;
  rate_limits?: Record<string, number>;
  [key: string]: any;
}

// Convert NextRequest to policy evaluation context
export const extractRequestContext = (req: NextRequest): RequestContext => {
  const headers: Record<string, string> = {};
  req.headers.forEach((value, key) => {
    headers[key] = value;
  });

  // Extract client IP (handles various proxy headers)
  const getClientIP = (): string => {
    const xForwardedFor = req.headers.get('x-forwarded-for');
    const xRealIp = req.headers.get('x-real-ip');
    const cfConnectingIp = req.headers.get('cf-connecting-ip');
    
    if (xForwardedFor) {
      return xForwardedFor.split(',')[0].trim();
    }
    if (xRealIp) return xRealIp;
    if (cfConnectingIp) return cfConnectingIp;
    
    return req.ip || '127.0.0.1';
  };

  return {
    method: req.method,
    path: new URL(req.url).pathname,
    headers,
    remote_addr: getClientIP(),
    rate_limits: {} // This would be populated by your rate limiting service
  };
};

// Create policy middleware
export const withPolicyEnforcement = (options: PolicyMiddlewareOptions) => {
  return (handler: (req: NextRequest) => Promise<NextResponse>) => {
    return async (req: NextRequest): Promise<NextResponse> => {
      try {
        // Skip policy evaluation for certain paths
        const pathname = new URL(req.url).pathname;
        if (options.skipPaths?.some(path => pathname.startsWith(path))) {
          return handler(req);
        }

        // Extract request context for policy evaluation
        const context = extractRequestContext(req);
        
        // Evaluate policy
        let policyResult: PolicyResult;
        
        if (options.policyType === 'api') {
          policyResult = await evaluateApiPolicy(context);
        } else if (options.policyType === 'ledger') {
          policyResult = await evaluateLedgerPolicy(context);
        } else if (options.customEvaluator) {
          policyResult = await options.customEvaluator(context);
        } else {
          throw new Error('Invalid policy configuration');
        }

        // Handle policy violations
        if (!policyResult.allowed) {
          if (options.enableAuditLog) {
            console.log('Policy violation:', {
              timestamp: new Date().toISOString(),
              path: pathname,
              method: req.method,
              clientIP: context.remote_addr,
              violations: policyResult.violations,
              headers: Object.keys(context.headers) // Don't log header values for security
            });
          }

          // Use custom violation handler if provided
          if (options.onViolation) {
            return options.onViolation(policyResult.violations || [], req);
          }

          // Default violation response
          return NextResponse.json(
            {
              error: 'Request denied by policy',
              violations: policyResult.violations,
              timestamp: new Date().toISOString()
            },
            { status: 403 }
          );
        }

        // Policy allows request, proceed with handler
        return handler(req);

      } catch (error) {
        console.error('Policy enforcement error:', error);
        
        // In case of policy evaluation errors, you might want to:
        // - Allow the request (fail open)
        // - Deny the request (fail closed)  
        // - Return a specific error response
        
        // For security, we'll fail closed by default
        return NextResponse.json(
          {
            error: 'Policy evaluation failed',
            message: 'Unable to evaluate request against security policies'
          },
          { status: 500 }
        );
      }
    };
  };
};

// Specific middleware factories for common use cases
export const withApiPolicy = (options: Omit<PolicyMiddlewareOptions, 'policyType'> = {}) => {
  return withPolicyEnforcement({
    ...options,
    policyType: 'api'
  });
};

export const withLedgerPolicy = (options: Omit<PolicyMiddlewareOptions, 'policyType'> = {}) => {
  return withPolicyEnforcement({
    ...options,
    policyType: 'ledger'
  });
};

// Rate limiting helper (would integrate with your rate limiting service)
export const withRateLimit = (
  rateLimitService: (clientId: string) => Promise<{ count: number; limit: number; allowed: boolean }>
) => {
  return (middleware: (req: NextRequest) => Promise<NextResponse>) => {
    return async (req: NextRequest): Promise<NextResponse> => {
      try {
        const context = extractRequestContext(req);
        const clientId = context.headers.authorization?.replace('Bearer ', '') || context.remote_addr;
        
        const rateLimitResult = await rateLimitService(clientId);
        
        if (!rateLimitResult.allowed) {
          return NextResponse.json(
            {
              error: 'Rate limit exceeded',
              limit: rateLimitResult.limit,
              current: rateLimitResult.count,
              resetTime: Date.now() + 60000 // Assume 1 minute window
            },
            { 
              status: 429,
              headers: {
                'Retry-After': '60',
                'X-RateLimit-Limit': rateLimitResult.limit.toString(),
                'X-RateLimit-Remaining': (rateLimitResult.limit - rateLimitResult.count).toString()
              }
            }
          );
        }

        // Update request context with rate limiting info for policy evaluation
        (req as any).policyContext = {
          ...context,
          rate_limits: {
            [clientId]: rateLimitResult.count
          }
        };

        return middleware(req);
      } catch (error) {
        console.error('Rate limiting error:', error);
        return middleware(req); // Continue on rate limiting errors
      }
    };
  };
};

// Audit logging helper
export const withAuditLog = (
  auditLogger: (event: AuditEvent) => Promise<void>
) => {
  return (middleware: (req: NextRequest) => Promise<NextResponse>) => {
    return async (req: NextRequest): Promise<NextResponse> => {
      const startTime = Date.now();
      const context = extractRequestContext(req);
      
      try {
        const response = await middleware(req);
        
        // Log successful requests
        await auditLogger({
          timestamp: new Date().toISOString(),
          type: 'api_request',
          method: req.method,
          path: context.path,
          clientIP: context.remote_addr,
          statusCode: response.status,
          duration: Date.now() - startTime,
          userAgent: req.headers.get('user-agent') || 'unknown'
        });

        return response;
      } catch (error) {
        // Log errors
        await auditLogger({
          timestamp: new Date().toISOString(),
          type: 'api_error',
          method: req.method,
          path: context.path,
          clientIP: context.remote_addr,
          error: error.message,
          duration: Date.now() - startTime,
          userAgent: req.headers.get('user-agent') || 'unknown'
        });

        throw error;
      }
    };
  };
};

export interface AuditEvent {
  timestamp: string;
  type: 'api_request' | 'api_error' | 'policy_violation';
  method: string;
  path: string;
  clientIP: string;
  statusCode?: number;
  error?: string;
  duration: number;
  userAgent: string;
  violations?: string[];
}