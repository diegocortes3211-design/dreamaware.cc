/**
 * Fortress v4 Policy Enforcement Library
 * Main entry point for the Next.js policy integration
 */

// Policy client exports
export {
  default as FortressPolicyClient,
  createLedgerPolicyClient,
  createApiPolicyClient, 
  createRuntimePolicyClient,
  evaluateLedgerPolicy,
  evaluateApiPolicy,
  evaluateRuntimePolicy
} from './client';

export type {
  PolicyClient,
  PolicyResult,
  DetailedPolicyResult,
  PolicyClientOptions
} from './client';

// Middleware exports  
export {
  withPolicyEnforcement,
  withApiPolicy,
  withLedgerPolicy,
  withRateLimit,
  withAuditLog,
  extractRequestContext
} from './middleware';

export type {
  PolicyMiddlewareOptions,
  RequestContext,
  AuditEvent
} from './middleware';

// Version information
export const FORTRESS_VERSION = '4.0.0';
export const POLICY_ENGINE = 'OPA';

// Default configuration
export const DEFAULT_CONFIG = {
  policyTimeout: 5000, // 5 seconds
  enableDebug: process.env.NODE_ENV === 'development',
  maxPolicyBundleSize: 1024 * 1024, // 1MB
  rateLimitWindow: 60 * 1000, // 1 minute
  auditLogEnabled: true
};

// Policy bundle URLs (configurable via environment variables)
export const POLICY_BUNDLE_URLS = {
  ledger: process.env.FORTRESS_LEDGER_POLICY_URL || '/policy/ledger.wasm',
  api: process.env.FORTRESS_API_POLICY_URL || '/policy/api.wasm',
  runtime: process.env.FORTRESS_RUNTIME_POLICY_URL || '/policy/runtime.wasm'
};

/**
 * Initialize Fortress v4 with custom configuration
 */
export interface FortressConfig {
  policyBundleBaseUrl?: string;
  enableDebug?: boolean;
  policyTimeout?: number;
  auditLogLevel?: 'none' | 'errors' | 'all';
  rateLimitDefaults?: {
    requests: number;
    window: number;
  };
}

let fortressConfig: Required<FortressConfig> = {
  policyBundleBaseUrl: '/policy',
  enableDebug: DEFAULT_CONFIG.enableDebug,
  policyTimeout: DEFAULT_CONFIG.policyTimeout,
  auditLogLevel: 'all',
  rateLimitDefaults: {
    requests: 60,
    window: 60000
  }
};

export const configureFortress = (config: Partial<FortressConfig>): void => {
  fortressConfig = { ...fortressConfig, ...config };
};

export const getFortressConfig = (): Required<FortressConfig> => {
  return { ...fortressConfig };
};

/**
 * Utility functions for policy development and testing
 */
export const PolicyUtils = {
  /**
   * Validate policy input structure
   */
  validateInput: (input: unknown, schema: Record<string, string>): boolean => {
    if (!input || typeof input !== 'object') return false;
    
    for (const [key, type] of Object.entries(schema)) {
      const value = (input as Record<string, any>)[key];
      if (typeof value !== type) return false;
    }
    return true;
  },

  /**
   * Format policy evaluation results for logging
   */
  formatResult: (result: PolicyResult): string => {
    const status = result.allowed ? 'ALLOW' : 'DENY';
    const violations = result.violations?.join(', ') || 'none';
    return `Policy: ${status}, Violations: ${violations}`;
  },

  /**
   * Create test input for policy evaluation
   */
  createTestInput: {
    ledger: (overrides: Partial<any> = {}) => ({
      operation: 'append',
      subject: 'test-subject',
      payload: 'dGVzdCBwYXlsb2Fk',
      meta: {},
      require_signature: true,
      ...overrides
    }),
    
    api: (overrides: Partial<any> = {}) => ({
      method: 'POST',
      path: '/api/test',
      headers: { 'Authorization': 'Bearer test-token' },
      remote_addr: '127.0.0.1',
      rate_limits: { 'test-token': 10 },
      ...overrides
    }),

    runtime: (overrides: Partial<any> = {}) => ({
      resource_type: 'memory',
      memory_mb: 256,
      memory_growth_rate: 0.05,
      cpu_percent: 50,
      cpu_sustained_duration: 60,
      connections_count: 100,
      bandwidth_mbps: 10,
      ...overrides
    })
  }
};

/**
 * Health check for policy engine
 */
export const checkPolicyEngineHealth = async (): Promise<{
  status: 'healthy' | 'degraded' | 'unhealthy';
  details: Record<string, any>;
}> => {
  const results = {
    ledgerPolicy: false,
    apiPolicy: false,
    runtimePolicy: false,
    lastChecked: new Date().toISOString()
  };

  try {
    // Test each policy with minimal input
    const testResults = await Promise.allSettled([
      evaluateLedgerPolicy(PolicyUtils.createTestInput.ledger()),
      evaluateApiPolicy(PolicyUtils.createTestInput.api()),
      evaluateRuntimePolicy(PolicyUtils.createTestInput.runtime())
    ]);

    results.ledgerPolicy = testResults[0].status === 'fulfilled';
    results.apiPolicy = testResults[1].status === 'fulfilled';
    results.runtimePolicy = testResults[2].status === 'fulfilled';

    const healthyCount = Object.values(results).filter(r => r === true).length;
    
    if (healthyCount === 3) {
      return { status: 'healthy', details: results };
    } else if (healthyCount > 0) {
      return { status: 'degraded', details: results };
    } else {
      return { status: 'unhealthy', details: results };
    }
  } catch (error) {
    return {
      status: 'unhealthy',
      details: { ...results, error: error.message }
    };
  }
};