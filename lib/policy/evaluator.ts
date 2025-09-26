import { readFileSync } from 'fs';
import { join } from 'path';
import { createHash } from 'crypto';
import { spawn } from 'child_process';
import { promisify } from 'util';

// Types for policy evaluation
export interface PolicyInput {
  user?: {
    id?: string;
    authenticated?: boolean;
    role?: string;
    type?: string;
    service_id?: string;
  };
  resource?: {
    id?: string;
    owner?: string;
    visibility?: string;
    sensitive?: boolean;
    shared_with?: string[];
    allowed_actions?: string[];
  };
  action?: string;
  rate_limit?: {
    current: number;
    max: number;
  };
  [key: string]: any;
}

export interface PolicyResult {
  allowed: boolean;
  audit_required?: boolean;
  decision_id: string;
  evaluation_time_ms: number;
  engine: 'wasm' | 'cli';
  errors?: string[];
}

export interface PolicyEvaluatorOptions {
  wasmPath?: string;
  wasmChecksumPath?: string;
  opaPath?: string;
  evaluationTimeout?: number;
  enforcementMode?: boolean;
}

export class PolicyEvaluator {
  private wasmPath: string;
  private wasmChecksumPath: string;
  private opaPath: string;
  private evaluationTimeout: number;
  private enforcementMode: boolean;
  private wasmModule: any = null;
  private wasmIntegrityVerified: boolean = false;

  constructor(options: PolicyEvaluatorOptions = {}) {
    this.wasmPath = options.wasmPath || join(process.cwd(), 'policy/fortress/authz.wasm');
    this.wasmChecksumPath = options.wasmChecksumPath || `${this.wasmPath}.sha256`;
    this.opaPath = options.opaPath || 'opa';
    this.evaluationTimeout = options.evaluationTimeout || 5000; // 5 seconds
    this.enforcementMode = options.enforcementMode || process.env.POLICY_ENFORCE === '1';
  }

  /**
   * Evaluate a policy decision with WASM-first approach, CLI fallback
   */
  async evaluate(input: PolicyInput): Promise<PolicyResult> {
    const startTime = Date.now();
    const decisionId = this.generateDecisionId(input);

    try {
      // First try WASM evaluation
      const result = await this.evaluateWithWasm(input, decisionId, startTime);
      this.logDecision(result, input);
      return result;
    } catch (wasmError: unknown) {
      const wasmErrorMessage = wasmError instanceof Error ? wasmError.message : 'Unknown WASM error';
      console.warn('WASM evaluation failed, falling back to CLI:', wasmErrorMessage);
      
      try {
        // Fallback to CLI evaluation
        const result = await this.evaluateWithCli(input, decisionId, startTime);
        this.logDecision(result, input);
        return result;
      } catch (cliError: unknown) {
        const evaluationTime = Date.now() - startTime;
        const cliErrorMessage = cliError instanceof Error ? cliError.message : 'Unknown CLI error';
        console.error('Both WASM and CLI evaluation failed:', { wasmError: wasmErrorMessage, cliError: cliErrorMessage });
        
        // In enforcement mode, deny by default if both engines fail
        if (this.enforcementMode) {
          const result: PolicyResult = {
            allowed: false,
            decision_id: decisionId,
            evaluation_time_ms: evaluationTime,
            engine: 'wasm',
            errors: [`WASM: ${wasmErrorMessage}`, `CLI: ${cliErrorMessage}`]
          };
          this.logDecision(result, input);
          return result;
        } else {
          throw new Error(`Policy evaluation failed: WASM: ${wasmErrorMessage}, CLI: ${cliErrorMessage}`);
        }
      }
    }
  }

  /**
   * Evaluate policy using WASM engine
   */
  private async evaluateWithWasm(input: PolicyInput, decisionId: string, startTime: number): Promise<PolicyResult> {
    // Initialize WASM module if not already done
    if (!this.wasmModule) {
      await this.initializeWasm();
    }

    // Evaluate with timeout
    const evaluationPromise = this.performWasmEvaluation(input);
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error('WASM evaluation timeout')), this.evaluationTimeout);
    });

    const wasmResult = await Promise.race([evaluationPromise, timeoutPromise]);
    const evaluationTime = Date.now() - startTime;

    return {
      allowed: wasmResult.allow || false,
      audit_required: wasmResult.audit_required || false,
      decision_id: decisionId,
      evaluation_time_ms: evaluationTime,
      engine: 'wasm'
    };
  }

  /**
   * Evaluate policy using OPA CLI
   */
  private async evaluateWithCli(input: PolicyInput, decisionId: string, startTime: number): Promise<PolicyResult> {
    const inputJson = JSON.stringify({ input });
    
    // Run OPA eval with timeout
    const result = await this.runOpaCommand(['eval', '-d', 'policy/fortress/authz.rego', '-i', '-', 'data.fortress.authz'], inputJson);
    
    const evaluationTime = Date.now() - startTime;
    const output = JSON.parse(result);
    
    return {
      allowed: output.result?.[0]?.expressions?.[0]?.value?.allow || false,
      audit_required: output.result?.[0]?.expressions?.[0]?.value?.audit_required || false,
      decision_id: decisionId,
      evaluation_time_ms: evaluationTime,
      engine: 'cli'
    };
  }

  /**
   * Initialize WASM module with integrity verification
   */
  private async initializeWasm(): Promise<void> {
    try {
      // Verify WASM file integrity
      if (!this.wasmIntegrityVerified) {
        await this.verifyWasmIntegrity();
        this.wasmIntegrityVerified = true;
      }

      // Load WASM module (this would require @open-policy-agent/opa-wasm in a real implementation)
      const wasmBuffer = readFileSync(this.wasmPath);
      
      // For now, we'll simulate the WASM loading since we don't have the actual OPA WASM runtime
      // In a real implementation, you would use:
      // const { loadPolicy } = require('@open-policy-agent/opa-wasm');
      // this.wasmModule = await loadPolicy(wasmBuffer);
      
      // Simulated initialization
      this.wasmModule = {
        evaluate: (input: any) => {
          // This would be the actual WASM evaluation
          // For demo purposes, we'll implement basic logic
          return this.simulateWasmEvaluation(input);
        }
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new Error(`Failed to initialize WASM module: ${errorMessage}`);
    }
  }

  /**
   * Verify WASM file integrity using SHA-256 checksum
   */
  private async verifyWasmIntegrity(): Promise<void> {
    try {
      const wasmBuffer = readFileSync(this.wasmPath);
      const actualHash = createHash('sha256').update(wasmBuffer).digest('hex');
      
      const expectedHash = readFileSync(this.wasmChecksumPath, 'utf8').trim();
      
      if (actualHash !== expectedHash) {
        throw new Error(`WASM integrity check failed. Expected: ${expectedHash}, Got: ${actualHash}`);
      }
    } catch (error: unknown) {
      if (error instanceof Error && (error as any).code === 'ENOENT') {
        throw new Error('WASM file or checksum file not found');
      }
      throw error;
    }
  }

  /**
   * Perform WASM evaluation (simulated for demo)
   */
  private async performWasmEvaluation(input: PolicyInput): Promise<any> {
    if (!this.wasmModule) {
      throw new Error('WASM module not initialized');
    }

    return this.wasmModule.evaluate(input);
  }

  /**
   * Simulate WASM evaluation with basic policy logic
   * In a real implementation, this would be handled by the OPA WASM runtime
   */
  private simulateWasmEvaluation(input: PolicyInput): any {
    const allow = this.evaluatePolicyLogic(input);
    const audit_required = input.action && ['write', 'delete', 'admin'].includes(input.action) ||
                          input.resource?.sensitive === true;
    
    return { allow, audit_required };
  }

  /**
   * Basic policy logic implementation (for simulation)
   */
  private evaluatePolicyLogic(input: PolicyInput): boolean {
    // Not authenticated
    if (!input.user?.authenticated) {
      return false;
    }

    // Admin users can access everything
    if (input.user.role === 'admin') {
      return true;
    }

    // Service-to-service authentication
    if (input.user.type === 'service' && input.user.service_id) {
      const validServices = ['fortress-core', 'fortress-gateway', 'fortress-worker'];
      const validActions = ['read', 'write', 'execute'];
      return validServices.includes(input.user.service_id) && 
             (!input.action || validActions.includes(input.action));
    }

    // Regular users
    if (input.user.role === 'user' && input.resource) {
      // Read access to public resources
      if (input.action === 'read' && input.resource.visibility === 'public') {
        return true;
      }
      
      // Full access to owned resources
      if (input.resource.owner === input.user.id) {
        return true;
      }
      
      // Shared resource access
      if (input.resource.shared_with?.includes(input.user.id || '') &&
          (!input.action || input.resource.allowed_actions?.includes(input.action))) {
        return true;
      }
    }

    // Rate limiting check
    if (input.rate_limit && input.rate_limit.current >= input.rate_limit.max) {
      return false;
    }

    return false;
  }

  /**
   * Run OPA command with timeout
   */
  private async runOpaCommand(args: string[], stdin?: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const child = spawn(this.opaPath, args, {
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: this.evaluationTimeout
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve(stdout);
        } else {
          reject(new Error(`OPA command failed with code ${code}: ${stderr}`));
        }
      });

      child.on('error', (error) => {
        reject(new Error(`Failed to run OPA command: ${error.message}`));
      });

      if (stdin) {
        child.stdin.write(stdin);
        child.stdin.end();
      }
    });
  }

  /**
   * Generate a unique decision ID for tracking
   */
  private generateDecisionId(input: PolicyInput): string {
    const timestamp = Date.now();
    const inputHash = createHash('md5').update(JSON.stringify(input)).digest('hex').slice(0, 8);
    return `decision_${timestamp}_${inputHash}`;
  }

  /**
   * Log policy decision for audit purposes
   */
  private logDecision(result: PolicyResult, input: PolicyInput): void {
    const logEntry = {
      timestamp: new Date().toISOString(),
      decision_id: result.decision_id,
      allowed: result.allowed,
      audit_required: result.audit_required,
      engine: result.engine,
      evaluation_time_ms: result.evaluation_time_ms,
      user_id: input.user?.id,
      resource_id: input.resource?.id,
      action: input.action,
      errors: result.errors
    };

    // In a production environment, this would be sent to a proper logging system
    console.log('POLICY_DECISION:', JSON.stringify(logEntry));
  }
}

export default PolicyEvaluator;