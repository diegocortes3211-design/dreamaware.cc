/**
 * Example API Route: Ledger Append with Policy Enforcement
 * Demonstrates Fortress v4 policy integration
 */

import { NextRequest, NextResponse } from 'next/server';
import { withLedgerPolicy, withAuditLog } from '../../../../../lib/policy/middleware';

interface LedgerAppendRequest {
  subject: string;
  payload: string; // base64 encoded
  meta?: Record<string, any>;
  require_signature?: boolean;
}

interface LedgerAppendResponse {
  success: boolean;
  id?: string;
  timestamp?: string;
  signature?: string;
  violations?: string[];
}

// Mock ledger service (in production this would call your actual ledger service)
const appendToLedger = async (request: LedgerAppendRequest): Promise<{
  id: string;
  timestamp: string;
  signature: string;
}> => {
  // Simulate ledger append operation
  const id = `txn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const timestamp = new Date().toISOString();
  
  // In production, this would integrate with your Vault signing service
  // like the one shown in services/ledger/server.go
  const signature = `vault:v1:${btoa(`signature_for_${request.subject}_${Date.now()}`)}`;
  
  // Simulate database write delay
  await new Promise(resolve => setTimeout(resolve, 10));
  
  return { id, timestamp, signature };
};

// Audit logger (in production this would integrate with your audit system)
const auditLogger = async (event: any) => {
  console.log('AUDIT:', JSON.stringify(event, null, 2));
  // In production: await auditService.log(event);
};

const handler = async (req: NextRequest): Promise<NextResponse> => {
  if (req.method !== 'POST') {
    return NextResponse.json(
      { error: 'Method not allowed' },
      { status: 405 }
    );
  }

  try {
    const body: LedgerAppendRequest = await req.json();
    
    // Validate request structure
    if (!body.subject || !body.payload) {
      return NextResponse.json(
        { 
          error: 'Invalid request', 
          message: 'subject and payload are required' 
        },
        { status: 400 }
      );
    }

    // Prepare policy evaluation context
    // The middleware will have already evaluated API-level policies
    // Now we evaluate ledger-specific policies
    const ledgerContext = {
      operation: 'append',
      subject: body.subject,
      payload: body.payload,
      meta: body.meta || {},
      require_signature: body.require_signature !== false // default true
    };

    // Note: In this example, ledger policy evaluation is handled by the middleware
    // The request reaches here only if policies allow it
    
    // Append to ledger
    const result = await appendToLedger(body);
    
    const response: LedgerAppendResponse = {
      success: true,
      id: result.id,
      timestamp: result.timestamp,
      signature: result.signature
    };

    return NextResponse.json(response, { status: 201 });

  } catch (error) {
    console.error('Ledger append error:', error);
    
    if (error.name === 'SyntaxError') {
      return NextResponse.json(
        { error: 'Invalid JSON in request body' },
        { status: 400 }
      );
    }

    return NextResponse.json(
      { 
        error: 'Internal server error',
        message: 'Failed to append to ledger'
      },
      { status: 500 }
    );
  }
};

// Apply policy enforcement and audit logging
export const POST = withAuditLog(auditLogger)(
  withLedgerPolicy({
    enableAuditLog: true,
    onViolation: (violations, req) => {
      return NextResponse.json(
        {
          success: false,
          error: 'Request violates ledger policies',
          violations,
          timestamp: new Date().toISOString()
        },
        { status: 403 }
      );
    }
  })(handler)
);