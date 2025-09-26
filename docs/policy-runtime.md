# Policy Runtime Documentation

This document describes the Fortress v4 policy runtime system, which provides a WASM-first policy evaluator with CLI fallback for authorization decisions.

## Overview

The policy runtime system consists of:

- **Runtime Evaluator**: TypeScript library that evaluates policies using WASM or OPA CLI
- **Reference Policy**: Rego policy defining authorization rules
- **Build Tools**: Scripts to compile policies to WASM bundles
- **Parity Tests**: Test suite ensuring consistency between WASM and CLI engines
- **CI/CD Integration**: Automated testing and security validation

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Build WASM Policy Bundle

```bash
# Install OPA CLI (required for building WASM and CLI fallback)
curl -L -o opa https://openpolicyagent.org/downloads/v0.57.0/opa_linux_amd64_static
chmod +x opa
sudo mv opa /usr/local/bin/

# Build WASM bundle
npm run policy:build:wasm
```

### 3. Run Tests

```bash
npm run test:policy
```

## Usage

### Basic Policy Evaluation

```typescript
import { PolicyEvaluator } from './lib/policy/evaluator.js';

const evaluator = new PolicyEvaluator();

const result = await evaluator.evaluate({
  user: {
    id: 'user123',
    authenticated: true,
    role: 'user'
  },
  action: 'read',
  resource: {
    id: 'resource456',
    visibility: 'public'
  }
});

console.log('Access allowed:', result.allowed);
console.log('Audit required:', result.audit_required);
console.log('Engine used:', result.engine);
console.log('Evaluation time:', result.evaluation_time_ms, 'ms');
```

### Configuration Options

```typescript
const evaluator = new PolicyEvaluator({
  wasmPath: './custom/path/to/policy.wasm',
  wasmChecksumPath: './custom/path/to/policy.wasm.sha256',
  opaPath: '/usr/local/bin/opa',
  evaluationTimeout: 10000, // 10 seconds
  enforcementMode: true // Fail closed on errors
});
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POLICY_ENFORCE` | Enable strict enforcement mode (`1` or `0`) | `0` |
| `OPA_PATH` | Path to OPA CLI binary | `opa` |
| `POLICY_TIMEOUT` | Evaluation timeout in milliseconds | `5000` |

### Enforcement Mode

When `POLICY_ENFORCE=1`:
- Policy evaluation failures result in denied access
- WASM integrity check failures cause startup to fail
- Both WASM and CLI engine failures result in denial

When `POLICY_ENFORCE=0` (default):
- Policy evaluation failures throw exceptions
- Engine failures are logged but may not block operations

## Policy Structure

The reference policy (`policy/fortress/authz.rego`) implements these rules:

### Authentication
- All requests require an authenticated user
- Unauthenticated requests are denied

### Authorization Levels

1. **Admin Users**: Full access to all resources
2. **Service Accounts**: Limited to specific services and actions
3. **Regular Users**: Access based on resource ownership and sharing

### Resource Access Rules

- **Public Resources**: Read access for authenticated users
- **Owned Resources**: Full access for resource owner
- **Shared Resources**: Access based on shared permissions
- **Private Resources**: Owner-only access

### Rate Limiting

- Requests are denied if rate limits are exceeded
- Rate limit checks are integrated into policy evaluation

### Audit Requirements

Audit logging is required for:
- Administrative actions (`admin`, `write`, `delete`)
- Access to sensitive resources (`resource.sensitive = true`)

## Build Process

### WASM Bundle Creation

```bash
./tools/policy/build-wasm.sh
```

This script:
1. Validates OPA CLI availability
2. Compiles Rego policy to WASM
3. Extracts WASM binary from bundle
4. Generates SHA-256 integrity checksum
5. Places files in `policy/fortress/`

### Manual Build

```bash
# Compile policy
opa build -t wasm -e "data.fortress.authz.allow" policy/fortress/authz.rego

# Extract WASM
tar -xzf bundle.tar.gz
mv policy.wasm policy/fortress/authz.wasm

# Generate checksum
sha256sum policy/fortress/authz.wasm > policy/fortress/authz.wasm.sha256
```

## Testing

### Parity Tests

The parity test suite (`__tests__/policy-parity.spec.ts`) verifies:

- WASM and CLI engines produce identical results
- Policy logic works correctly for all test cases
- Performance benchmarks meet requirements
- Error handling is consistent

```bash
npm run test:policy
```

### Test Vectors

The test suite includes vectors for:
- Basic authentication scenarios
- Role-based access control
- Resource ownership and sharing
- Service-to-service authentication
- Rate limiting behavior
- Audit requirement triggers

### Performance Benchmarking

Tests measure:
- Average evaluation time
- Throughput (decisions per second)
- Memory usage patterns
- Error recovery performance

## Security Features

### WASM Integrity Verification

- SHA-256 checksum validation before loading
- Runtime verification prevents tampered policies
- Checksum mismatch causes immediate failure

### Evaluation Timeouts

- Configurable timeout prevents DoS attacks
- Default 5-second timeout for policy evaluation
- Timeout triggers fallback to CLI engine

### Decision Logging

All policy decisions are logged with:
- Unique decision ID for tracking
- User and resource identifiers
- Evaluation engine and timing
- Audit requirement flags
- Error details if applicable

### Fail-Safe Design

- WASM-first with automatic CLI fallback
- Configurable enforcement modes
- Default deny for evaluation failures
- Comprehensive error handling

## Integration Examples

### Express.js Middleware

```typescript
import express from 'express';
import { PolicyEvaluator } from './lib/policy/evaluator.js';

const app = express();
const evaluator = new PolicyEvaluator();

async function authorize(req, res, next) {
  try {
    const result = await evaluator.evaluate({
      user: req.user,
      action: req.method.toLowerCase(),
      resource: {
        id: req.params.resourceId,
        // ... other resource properties
      }
    });

    if (!result.allowed) {
      return res.status(403).json({ error: 'Access denied' });
    }

    // Log audit events if required
    if (result.audit_required) {
      console.log('AUDIT_EVENT:', {
        decision_id: result.decision_id,
        user_id: req.user.id,
        resource_id: req.params.resourceId,
        action: req.method
      });
    }

    next();
  } catch (error) {
    console.error('Policy evaluation failed:', error);
    res.status(500).json({ error: 'Authorization service unavailable' });
  }
}

app.get('/api/resources/:resourceId', authorize, (req, res) => {
  // Your protected resource handler
});
```

### GraphQL Resolver Protection

```typescript
import { PolicyEvaluator } from './lib/policy/evaluator.js';

const evaluator = new PolicyEvaluator();

const resolvers = {
  Query: {
    resource: async (parent, args, context) => {
      const result = await evaluator.evaluate({
        user: context.user,
        action: 'read',
        resource: { id: args.id }
      });

      if (!result.allowed) {
        throw new Error('Access denied');
      }

      return getResource(args.id);
    }
  }
};
```

### Batch Evaluation

```typescript
async function evaluateBatch(requests) {
  const evaluator = new PolicyEvaluator();
  
  const results = await Promise.all(
    requests.map(request => evaluator.evaluate(request))
  );
  
  return results.map((result, index) => ({
    request: requests[index],
    allowed: result.allowed,
    decision_id: result.decision_id
  }));
}
```

## Troubleshooting

### WASM Loading Issues

```bash
# Verify WASM file exists and is valid
ls -la policy/fortress/authz.wasm
file policy/fortress/authz.wasm

# Check integrity
sha256sum -c policy/fortress/authz.wasm.sha256
```

### CLI Fallback Issues

```bash
# Test OPA CLI directly
echo '{"input": {"user": {"authenticated": true}}}' | opa eval -d policy/fortress/authz.rego -i - "data.fortress.authz.allow"

# Check OPA version
opa version
```

### Performance Issues

- Enable debug logging: `DEBUG=policy npm start`
- Monitor evaluation times in decision logs
- Use performance profiling tools
- Consider caching for repeated evaluations

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `WASM integrity check failed` | Corrupted or modified WASM file | Rebuild WASM bundle |
| `OPA command failed` | OPA CLI not installed or policy syntax error | Install OPA, check policy syntax |
| `WASM evaluation timeout` | Complex policy or infinite loop | Optimize policy, increase timeout |
| `Both WASM and CLI evaluation failed` | Policy syntax error or missing files | Rebuild policy, check file permissions |

## Monitoring and Observability

### Metrics to Track

- Policy evaluation latency (p50, p95, p99)
- Engine usage ratio (WASM vs CLI)
- Error rates by engine type
- Cache hit/miss rates
- Decision audit event volume

### Alerting Recommendations

- High evaluation latency (>100ms p95)
- Frequent CLI fallback usage (>10%)
- WASM integrity check failures
- High error rates (>1%)
- Audit event anomalies

### Log Analysis

Decision logs can be parsed for:
- Access pattern analysis
- Security incident investigation
- Performance optimization
- Compliance reporting

## Contributing

### Adding New Policy Rules

1. Update `policy/fortress/authz.rego`
2. Add corresponding test vectors to `__tests__/policy-parity.spec.ts`
3. Rebuild WASM bundle: `npm run policy:build:wasm`
4. Run tests: `npm run test:policy`
5. Update documentation if needed

### Policy Testing Best Practices

- Include both positive and negative test cases
- Test edge cases and boundary conditions
- Verify audit requirement logic
- Test rate limiting scenarios
- Include performance benchmarks

## References

- [Open Policy Agent Documentation](https://www.openpolicyagent.org/docs/)
- [Rego Language Reference](https://www.openpolicyagent.org/docs/latest/policy-reference/)
- [WASM Integration Guide](https://www.openpolicyagent.org/docs/latest/integration/#webassembly)