const express = require('express');
const { Redis } = require('ioredis');
const jwt = require('jsonwebtoken');
const JwksRsa = require('jwks-rsa');
const crypto = require('crypto');

// --- Configuration from environment variables ---
const PORT = process.env.PORT || 3001;
const JWKS_URI = process.env.JWKS_URI;
const JWT_ISSUER = process.env.JWT_ISSUER;
const HMAC_SECRET = process.env.HMAC_DEFAULT_SECRET;
const SKEW_WINDOW_SEC = parseInt(process.env.SKEW_WINDOW_SEC, 10) || 300;

// --- Redis Sentinel Client Setup ---
// Parse comma-separated hosts for ioredis
const sentinelHosts = (process.env.REDIS_SENTINEL_HOSTS || '').split(',');
const sentinels = sentinelHosts.map(host => {
  const [hostname, port] = host.split(':');
  if (!hostname || !port) return null;
  return { host: hostname, port: parseInt(port, 10) };
}).filter(Boolean);

let redis;
if (sentinels.length > 0) {
    console.log(`Connecting to Redis via Sentinels. Master: ${process.env.REDIS_SENTINEL_MASTER_NAME}`);
    redis = new Redis({
        sentinels,
        name: process.env.REDIS_SENTINEL_MASTER_NAME,
        lazyConnect: true,
    });
} else {
    // Fallback for simpler, non-sentinel setup if needed
    console.log('Connecting to Redis via direct URL (no Sentinel).');
    redis = new Redis(process.env.REDIS_URL, { lazyConnect: true });
}

redis.on('connect', () => console.log('Successfully connected to Redis.'));
redis.on('error', (err) => console.error('Redis connection error:', err));

// --- JWKS Client for JWT Validation ---
const jwksClient = JwksRsa({
  cache: true,
  rateLimit: true,
  jwksRequestsPerMinute: 5,
  jwksUri: JWKS_URI,
});

function getKey(header, callback) {
  jwksClient.getSigningKey(header.kid, (err, key) => {
    if (err) {
      console.error("JWKS key retrieval error:", err);
      return callback(err);
    }
    const signingKey = key.publicKey || key.rsaPublicKey;
    callback(null, signingKey);
  });
}

// --- Express App Setup ---
const app = express();
// Use express.json() but also capture the raw body buffer for HMAC signing
app.use(express.json({
    verify: (req, res, buf) => {
        req.rawBody = buf;
    }
}));

// --- Authentication Middleware ---
async function authMiddleware(req, res, next) {
  try {
    // 1. JWT Validation
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Missing or malformed Authorization header' });
    }
    const token = authHeader.split(' ')[1];

    const decoded = await new Promise((resolve, reject) => {
      jwt.verify(token, getKey, { issuer: JWT_ISSUER, algorithms: ['RS256'] }, (err, decodedToken) => {
        if (err) return reject(err);
        resolve(decodedToken);
      });
    });

    // 2. JTI Replay Check
    const jti = decoded.jti;
    if (!jti) return res.status(401).json({ error: 'Missing JTI in token' });
    const jtiKey = `auth:jti:${decoded.iss}:${jti}`;
    const jtiReply = await redis.set(jtiKey, '1', 'EX', 60, 'NX');
    if (jtiReply === null) return res.status(401).json({ error: 'jti_replayed' });

    // 3. HMAC Header Validation
    const { 'x-hmac-kid': hmacKid, 'x-hmac-sig': hmacSig, 'x-hmac-ts': hmacTs, 'x-hmac-nonce': hmacNonce } = req.headers;
    if (!hmacKid || !hmacSig || !hmacTs || !hmacNonce) return res.status(401).json({ error: 'Missing HMAC headers' });

    // 4. Timestamp Skew Check
    const timestamp = parseInt(hmacTs, 10);
    if (isNaN(timestamp) || Math.abs(Math.floor(Date.now() / 1000) - timestamp) > SKEW_WINDOW_SEC) {
      return res.status(401).json({ error: 'timestamp_out_of_range' });
    }

    // 5. Nonce Replay Check
    const nonceKey = `auth:nonce:${hmacKid}:${hmacNonce}`;
    const nonceReply = await redis.set(nonceKey, '1', 'EX', SKEW_WINDOW_SEC, 'NX');
    if (nonceReply === null) return res.status(401).json({ error: 'nonce_replayed' });

    // 6. HMAC Signature Verification
    const bodyHash = crypto.createHash('sha256').update(req.rawBody || '').digest('hex');
    const stringToSign = [req.method.toUpperCase(), req.path, '', hmacTs, hmacNonce, bodyHash].join('\n');
    const expectedSig = crypto.createHmac('sha256', HMAC_SECRET).update(stringToSign).digest('hex');

    if (!crypto.timingSafeEqual(Buffer.from(hmacSig), Buffer.from(expectedSig))) {
      return res.status(401).json({ error: 'invalid_signature' });
    }

    next();
  } catch (err) {
    if (err instanceof jwt.JsonWebTokenError) {
      return res.status(401).json({ error: 'invalid_jwt', details: err.message });
    }
    console.error("Unhandled authentication error:", err);
    return res.status(500).json({ error: 'Internal server error during authentication' });
  }
}

// --- API Routes ---
app.get('/health', (req, res) => res.status(200).json({ status: 'ok' }));
app.post('/v1/protected', authMiddleware, (req, res) => res.status(200).json({ success: true, message: 'Access granted' }));

// --- Server Start ---
(async () => {
  try {
    await redis.connect();
    app.listen(PORT, () => {
      console.log(`Mock Gateway for testing listening on port ${PORT}`);
    });
  } catch (err) {
    console.error("Failed to connect to Redis. Gateway cannot start.", err);
    process.exit(1);
  }
})();