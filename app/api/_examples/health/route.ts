/**
 * Example API Route: Health Check with Runtime Policy Monitoring
 * Demonstrates real-time system monitoring and policy evaluation
 */

import { NextRequest, NextResponse } from 'next/server';
import { evaluateRuntimePolicy } from '../../../../lib/policy/client';

interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: {
    database: HealthStatus;
    memory: HealthStatus;
    cpu: HealthStatus;
    network: HealthStatus;
    policies: HealthStatus;
  };
  metrics: SystemMetrics;
  policyEvaluation?: {
    allowed: boolean;
    violations?: string[];
    alerts?: {
      security: boolean;
      performance: boolean;
    };
  };
}

interface HealthStatus {
  status: 'ok' | 'warning' | 'error';
  message: string;
  value?: number;
  threshold?: number;
}

interface SystemMetrics {
  memory: {
    used_mb: number;
    total_mb: number;
    usage_percent: number;
    growth_rate: number;
  };
  cpu: {
    usage_percent: number;
    sustained_duration: number;
  };
  network: {
    connections: number;
    bandwidth_mbps: number;
  };
  database: {
    pool_size: number;
    active_queries: number;
  };
  uptime_seconds: number;
}

// Mock system metrics collection (in production this would use actual system monitoring)
const collectSystemMetrics = async (): Promise<SystemMetrics> => {
  // In production, these would come from actual system monitoring
  // For demonstration, we'll use mock values with some variation
  const baseTime = Date.now();
  
  return {
    memory: {
      used_mb: 300 + Math.floor(Math.random() * 200), // 300-500 MB
      total_mb: 1024,
      usage_percent: 30 + Math.floor(Math.random() * 40), // 30-70%
      growth_rate: Math.random() * 0.1 // 0-10% growth
    },
    cpu: {
      usage_percent: 20 + Math.floor(Math.random() * 50), // 20-70%
      sustained_duration: Math.floor(Math.random() * 200) // 0-200 seconds
    },
    network: {
      connections: 100 + Math.floor(Math.random() * 400), // 100-500 connections
      bandwidth_mbps: Math.floor(Math.random() * 80) // 0-80 Mbps
    },
    database: {
      pool_size: 15 + Math.floor(Math.random() * 10), // 15-25 connections
      active_queries: Math.floor(Math.random() * 30) // 0-30 queries
    },
    uptime_seconds: Math.floor(baseTime / 1000) % 86400 // Uptime in seconds (mod 24h for demo)
  };
};

// Convert metrics to health status
const evaluateHealthStatus = (metrics: SystemMetrics): HealthCheckResponse['checks'] => {
  return {
    database: {
      status: metrics.database.pool_size > 25 || metrics.database.active_queries > 50 ? 'warning' : 'ok',
      message: `Pool: ${metrics.database.pool_size}/25, Queries: ${metrics.database.active_queries}`,
      value: metrics.database.pool_size,
      threshold: 25
    },
    memory: {
      status: metrics.memory.usage_percent > 80 ? 'error' : metrics.memory.usage_percent > 60 ? 'warning' : 'ok',
      message: `${metrics.memory.used_mb}MB used (${metrics.memory.usage_percent}%)`,
      value: metrics.memory.usage_percent,
      threshold: 80
    },
    cpu: {
      status: metrics.cpu.usage_percent > 80 ? 'error' : metrics.cpu.usage_percent > 60 ? 'warning' : 'ok',
      message: `${metrics.cpu.usage_percent}% usage`,
      value: metrics.cpu.usage_percent,
      threshold: 80
    },
    network: {
      status: metrics.network.connections > 1000 ? 'warning' : 'ok',
      message: `${metrics.network.connections} connections, ${metrics.network.bandwidth_mbps}Mbps`,
      value: metrics.network.connections,
      threshold: 1000
    },
    policies: {
      status: 'ok',
      message: 'Policy engine operational'
    }
  };
};

// Determine overall health status
const calculateOverallStatus = (checks: HealthCheckResponse['checks']): HealthCheckResponse['status'] => {
  const statuses = Object.values(checks).map(check => check.status);
  
  if (statuses.includes('error')) return 'unhealthy';
  if (statuses.includes('warning')) return 'degraded';
  return 'healthy';
};

export async function GET(req: NextRequest): Promise<NextResponse> {
  try {
    // Collect system metrics
    const metrics = await collectSystemMetrics();
    
    // Evaluate health status
    const checks = evaluateHealthStatus(metrics);
    
    // Evaluate runtime policies with current metrics
    let policyEvaluation;
    try {
      const runtimeContext = {
        resource_type: 'memory',
        memory_mb: metrics.memory.used_mb,
        memory_growth_rate: metrics.memory.growth_rate,
        cpu_percent: metrics.cpu.usage_percent,
        cpu_sustained_duration: metrics.cpu.sustained_duration,
        connections_count: metrics.network.connections,
        bandwidth_mbps: metrics.network.bandwidth_mbps,
        db_pool_size: metrics.database.pool_size,
        db_active_queries: metrics.database.active_queries,
        failed_auth_attempts: 0, // Would come from auth service
        suspicious_patterns: 0, // Would come from security monitoring
        payload_size: 1024,
        ws_connections: Math.floor(metrics.network.connections * 0.1), // Assume 10% are WebSocket
        ws_message_rate: 500,
        service_status: 'running',
        response_time_ms: 150 + Math.floor(Math.random() * 200), // 150-350ms
        error_rate: Math.random() * 0.1 // 0-10% error rate
      };

      const result = await evaluateRuntimePolicy(runtimeContext);
      
      policyEvaluation = {
        allowed: result.allowed,
        violations: result.violations,
        alerts: {
          security: false, // Would be determined by security_alert rule
          performance: !result.allowed // Simple mapping for demo
        }
      };

      // Update policy check status based on evaluation
      if (!result.allowed) {
        checks.policies = {
          status: 'warning',
          message: `Policy violations detected: ${result.violations?.join(', ') || 'Unknown'}`
        };
      }

    } catch (error) {
      console.error('Policy evaluation failed:', error);
      checks.policies = {
        status: 'error',
        message: 'Policy evaluation failed'
      };
    }

    const response: HealthCheckResponse = {
      status: calculateOverallStatus(checks),
      timestamp: new Date().toISOString(),
      checks,
      metrics,
      policyEvaluation
    };

    // Set appropriate HTTP status based on health
    const httpStatus = response.status === 'healthy' ? 200 : 
                      response.status === 'degraded' ? 200 : 503;

    return NextResponse.json(response, { 
      status: httpStatus,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'X-Health-Status': response.status
      }
    });

  } catch (error) {
    console.error('Health check error:', error);
    
    const errorResponse: HealthCheckResponse = {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      checks: {
        database: { status: 'error', message: 'Health check failed' },
        memory: { status: 'error', message: 'Health check failed' },
        cpu: { status: 'error', message: 'Health check failed' },
        network: { status: 'error', message: 'Health check failed' },
        policies: { status: 'error', message: 'Health check failed' }
      },
      metrics: {
        memory: { used_mb: 0, total_mb: 0, usage_percent: 0, growth_rate: 0 },
        cpu: { usage_percent: 0, sustained_duration: 0 },
        network: { connections: 0, bandwidth_mbps: 0 },
        database: { pool_size: 0, active_queries: 0 },
        uptime_seconds: 0
      }
    };

    return NextResponse.json(errorResponse, { status: 503 });
  }
}