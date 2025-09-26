import { PolicyEvaluator, PolicyInput, PolicyResult } from '../lib/policy/evaluator.js';
import { readFileSync } from 'fs';
import { join } from 'path';

// Test vectors for common use cases and edge cases
const testVectors: Array<{ name: string; input: PolicyInput; expectedAllow: boolean; expectedAudit?: boolean }> = [
  // Basic authentication tests
  {
    name: 'unauthenticated user denied',
    input: {
      user: { authenticated: false },
      action: 'read',
      resource: { id: 'resource1', visibility: 'public' }
    },
    expectedAllow: false
  },
  
  // Admin access tests
  {
    name: 'admin user allowed full access',
    input: {
      user: { id: 'admin1', authenticated: true, role: 'admin' },
      action: 'delete',
      resource: { id: 'resource1', owner: 'user1', sensitive: true }
    },
    expectedAllow: true,
    expectedAudit: true
  },
  
  // Service-to-service tests
  {
    name: 'valid service access allowed',
    input: {
      user: { 
        authenticated: true, 
        type: 'service', 
        service_id: 'fortress-core' 
      },
      action: 'read',
      resource: { id: 'resource1' }
    },
    expectedAllow: true
  },
  
  {
    name: 'invalid service denied',
    input: {
      user: { 
        authenticated: true, 
        type: 'service', 
        service_id: 'unauthorized-service' 
      },
      action: 'read',
      resource: { id: 'resource1' }
    },
    expectedAllow: false
  },
  
  // Regular user tests
  {
    name: 'user accessing public resource',
    input: {
      user: { id: 'user1', authenticated: true, role: 'user' },
      action: 'read',
      resource: { id: 'resource1', visibility: 'public' }
    },
    expectedAllow: true
  },
  
  {
    name: 'user accessing private resource denied',
    input: {
      user: { id: 'user1', authenticated: true, role: 'user' },
      action: 'read',
      resource: { id: 'resource1', visibility: 'private', owner: 'user2' }
    },
    expectedAllow: false
  },
  
  {
    name: 'user accessing owned resource',
    input: {
      user: { id: 'user1', authenticated: true, role: 'user' },
      action: 'write',
      resource: { id: 'resource1', owner: 'user1' }
    },
    expectedAllow: true
  },
  
  {
    name: 'user accessing shared resource with permission',
    input: {
      user: { id: 'user1', authenticated: true, role: 'user' },
      action: 'read',
      resource: { 
        id: 'resource1', 
        owner: 'user2',
        shared_with: ['user1'],
        allowed_actions: ['read', 'write']
      }
    },
    expectedAllow: true
  },
  
  {
    name: 'user accessing shared resource without permission',
    input: {
      user: { id: 'user1', authenticated: true, role: 'user' },
      action: 'delete',
      resource: { 
        id: 'resource1', 
        owner: 'user2',
        shared_with: ['user1'],
        allowed_actions: ['read']
      }
    },
    expectedAllow: false
  },
  
  // Rate limiting tests
  {
    name: 'rate limited user denied',
    input: {
      user: { id: 'user1', authenticated: true, role: 'user' },
      action: 'read',
      resource: { id: 'resource1', visibility: 'public' },
      rate_limit: { current: 100, max: 50 }
    },
    expectedAllow: false
  },
  
  // Audit requirement tests
  {
    name: 'sensitive resource requires audit',
    input: {
      user: { id: 'user1', authenticated: true, role: 'user' },
      action: 'read',
      resource: { id: 'resource1', owner: 'user1', sensitive: true }
    },
    expectedAllow: true,
    expectedAudit: true
  },
  
  {
    name: 'admin action requires audit',
    input: {
      user: { id: 'user1', authenticated: true, role: 'admin' },
      action: 'admin',
      resource: { id: 'resource1' }
    },
    expectedAllow: true,
    expectedAudit: true
  }
];

class TestRunner {
  private passedTests = 0;
  private failedTests = 0;
  private errors: string[] = [];

  async runParityTests(): Promise<void> {
    console.log('🧪 Running Policy Parity Tests');
    console.log('================================');
    
    // Check if WASM file exists for WASM tests
    const wasmExists = this.checkWasmExists();
    if (!wasmExists) {
      console.log('⚠️  WASM file not found. Running CLI-only tests.');
    }
    
    const evaluator = new PolicyEvaluator({
      enforcementMode: false // Don't fail on errors during testing
    });
    
    for (const testVector of testVectors) {
      await this.runSingleTest(evaluator, testVector, wasmExists);
    }
    
    this.printSummary();
  }
  
  private checkWasmExists(): boolean {
    try {
      const wasmPath = join(process.cwd(), 'policy/fortress/authz.wasm');
      readFileSync(wasmPath);
      return true;
    } catch {
      return false;
    }
  }
  
  private async runSingleTest(
    evaluator: PolicyEvaluator, 
    testVector: { name: string; input: PolicyInput; expectedAllow: boolean; expectedAudit?: boolean },
    testWasm: boolean
  ): Promise<void> {
    console.log(`📋 ${testVector.name}`);
    
    try {
      // Test with current evaluator (WASM-first with CLI fallback)
      const result = await evaluator.evaluate(testVector.input);
      
      // Validate results
      const allowMatch = result.allowed === testVector.expectedAllow;
      const auditMatch = testVector.expectedAudit === undefined || 
                        result.audit_required === testVector.expectedAudit;
      
      if (allowMatch && auditMatch) {
        console.log(`  ✅ PASS (${result.engine}, ${result.evaluation_time_ms}ms)`);
        this.passedTests++;
      } else {
        console.log(`  ❌ FAIL (${result.engine})`);
        console.log(`     Expected: allow=${testVector.expectedAllow}, audit=${testVector.expectedAudit}`);
        console.log(`     Got: allow=${result.allowed}, audit=${result.audit_required}`);
        this.failedTests++;
        this.errors.push(`${testVector.name}: Expected allow=${testVector.expectedAllow}, got ${result.allowed}`);
      }
      
      // If we have WASM available, also test CLI directly for parity
      if (testWasm && result.engine === 'wasm') {
        await this.testCliParity(evaluator, testVector, result);
      }
      
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.log(`  ❌ ERROR: ${errorMessage}`);
      this.failedTests++;
      this.errors.push(`${testVector.name}: ${errorMessage}`);
    }
    
    console.log(''); // Empty line for readability
  }
  
  private async testCliParity(
    evaluator: PolicyEvaluator,
    testVector: { name: string; input: PolicyInput; expectedAllow: boolean; expectedAudit?: boolean },
    wasmResult: PolicyResult
  ): Promise<void> {
    try {
      // Force CLI evaluation by using a separate evaluator with invalid WASM path
      const cliEvaluator = new PolicyEvaluator({
        wasmPath: '/invalid/path',
        enforcementMode: false
      });
      
      const cliResult = await cliEvaluator.evaluate(testVector.input);
      
      if (cliResult.allowed === wasmResult.allowed && 
          cliResult.audit_required === wasmResult.audit_required) {
        console.log(`  🔄 WASM/CLI Parity: ✅`);
      } else {
        console.log(`  🔄 WASM/CLI Parity: ❌`);
        console.log(`     WASM: allow=${wasmResult.allowed}, audit=${wasmResult.audit_required}`);
        console.log(`     CLI:  allow=${cliResult.allowed}, audit=${cliResult.audit_required}`);
        this.errors.push(`${testVector.name} parity: WASM and CLI results differ`);
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.log(`  🔄 CLI Test Failed: ${errorMessage}`);
    }
  }
  
  private printSummary(): void {
    console.log('Test Summary');
    console.log('============');
    console.log(`✅ Passed: ${this.passedTests}`);
    console.log(`❌ Failed: ${this.failedTests}`);
    console.log(`📊 Total:  ${this.passedTests + this.failedTests}`);
    
    if (this.errors.length > 0) {
      console.log('\\nErrors:');
      this.errors.forEach(error => console.log(`  - ${error}`));
    }
    
    if (this.failedTests > 0) {
      process.exit(1);
    }
  }
}

// Benchmarking function
async function runBenchmark(): Promise<void> {
  console.log('\\n🏃 Running Performance Benchmark');
  console.log('=================================');
  
  const evaluator = new PolicyEvaluator();
  const iterations = 100;
  
  // Simple test case for benchmarking
  const benchmarkInput: PolicyInput = {
    user: { id: 'user1', authenticated: true, role: 'user' },
    action: 'read',
    resource: { id: 'resource1', visibility: 'public' }
  };
  
  const startTime = Date.now();
  
  for (let i = 0; i < iterations; i++) {
    await evaluator.evaluate(benchmarkInput);
  }
  
  const endTime = Date.now();
  const totalTime = endTime - startTime;
  const avgTime = totalTime / iterations;
  
  console.log(`Evaluated ${iterations} decisions in ${totalTime}ms`);
  console.log(`Average evaluation time: ${avgTime.toFixed(2)}ms`);
  console.log(`Throughput: ${(1000 / avgTime).toFixed(0)} decisions/second`);
}

// Main execution
async function main(): Promise<void> {
  const testRunner = new TestRunner();
  
  try {
    await testRunner.runParityTests();
    await runBenchmark();
    
    console.log('\\n🎉 All tests completed successfully!');
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('\\n💥 Test execution failed:', errorMessage);
    process.exit(1);
  }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}