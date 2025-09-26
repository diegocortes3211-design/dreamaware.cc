/**
 * Fortress v4 Policy Enforcement Client
 * Lightweight Next.js wrapper for OPA policy evaluation
 */

import { loadPolicy } from '@open-policy-agent/opa-wasm';

export interface PolicyClient {
  evaluate(input: unknown): Promise<PolicyResult>;
  evaluateWithDetails(input: unknown): Promise<DetailedPolicyResult>;
}

export interface PolicyResult {
  allowed: boolean;
  violations?: string[];
}

export interface DetailedPolicyResult extends PolicyResult {
  metadata: {
    evaluationTime: number;
    policyVersion: string;
    timestamp: string;
  };
  debug?: {
    rules: Record<string, boolean>;
    traces: string[];
  };
}

export interface PolicyClientOptions {
  policyBundle?: ArrayBuffer;
  policyUrl?: string;
  enableDebug?: boolean;
  timeout?: number;
}

class FortressPolicyClient implements PolicyClient {
  private policy: any;
  private options: Required<PolicyClientOptions>;
  private initialized = false;

  constructor(options: PolicyClientOptions = {}) {
    this.options = {
      policyBundle: options.policyBundle,
      policyUrl: options.policyUrl,
      enableDebug: options.enableDebug ?? false,
      timeout: options.timeout ?? 5000,
      ...options
    } as Required<PolicyClientOptions>;
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      let policyData: ArrayBuffer;

      if (this.options.policyBundle) {
        policyData = this.options.policyBundle;
      } else if (this.options.policyUrl) {
        const response = await fetch(this.options.policyUrl);
        if (!response.ok) {
          throw new Error(`Failed to fetch policy: ${response.statusText}`);
        }
        policyData = await response.arrayBuffer();
      } else {
        throw new Error('Either policyBundle or policyUrl must be provided');
      }

      this.policy = await loadPolicy(policyData);
      this.initialized = true;
    } catch (error) {
      throw new Error(`Failed to initialize policy client: ${error.message}`);
    }
  }

  async evaluate(input: unknown): Promise<PolicyResult> {
    await this.initialize();

    const startTime = performance.now();
    
    try {
      // Set input data
      this.policy.setData(input);
      
      // Evaluate the allow rule
      const allowResult = this.policy.evaluate('allow');
      const allowed = allowResult[0]?.result === true;

      let violations: string[] = [];
      
      if (!allowed) {
        // Get violation details if available
        try {
          const violationResult = this.policy.evaluate('violation');
          violations = violationResult[0]?.result || [];
        } catch {
          // Violations rule may not exist, that's OK
        }
      }

      return {
        allowed,
        violations: violations.length > 0 ? violations : undefined
      };

    } catch (error) {
      throw new Error(`Policy evaluation failed: ${error.message}`);
    }
  }

  async evaluateWithDetails(input: unknown): Promise<DetailedPolicyResult> {
    const startTime = performance.now();
    const result = await this.evaluate(input);
    const evaluationTime = performance.now() - startTime;

    const detailedResult: DetailedPolicyResult = {
      ...result,
      metadata: {
        evaluationTime,
        policyVersion: '4.0.0',
        timestamp: new Date().toISOString()
      }
    };

    if (this.options.enableDebug) {
      // Add debug information if enabled
      detailedResult.debug = {
        rules: {}, // Could be populated with individual rule results
        traces: [] // Could be populated with evaluation traces
      };
    }

    return detailedResult;
  }
}

// Factory functions for different policy types
export const createLedgerPolicyClient = (options: PolicyClientOptions = {}): PolicyClient => {
  return new FortressPolicyClient({
    ...options,
    policyUrl: options.policyUrl || '/policy/ledger.wasm'
  });
};

export const createApiPolicyClient = (options: PolicyClientOptions = {}): PolicyClient => {
  return new FortressPolicyClient({
    ...options,
    policyUrl: options.policyUrl || '/policy/api.wasm'
  });
};

export const createRuntimePolicyClient = (options: PolicyClientOptions = {}): PolicyClient => {
  return new FortressPolicyClient({
    ...options,
    policyUrl: options.policyUrl || '/policy/runtime.wasm'
  });
};

// High-level convenience functions
export const evaluateLedgerPolicy = async (input: unknown): Promise<PolicyResult> => {
  const client = createLedgerPolicyClient();
  return client.evaluate(input);
};

export const evaluateApiPolicy = async (input: unknown): Promise<PolicyResult> => {
  const client = createApiPolicyClient();
  return client.evaluate(input);
};

export const evaluateRuntimePolicy = async (input: unknown): Promise<PolicyResult> => {
  const client = createRuntimePolicyClient();
  return client.evaluate(input);
};

export default FortressPolicyClient;