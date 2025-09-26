#!/usr/bin/env node

import pg from 'pg';

const { Client } = pg;

// Configuration from environment variables
const config = {
  database: {
    url: process.env.DATABASE_URL || 'postgresql://xikizpedia:devpassword123@localhost:5432/xikizpedia_dev',
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432', 10),
    name: process.env.DB_NAME || 'xikizpedia_dev',
    user: process.env.DB_USER || 'xikizpedia',
    password: process.env.DB_PASSWORD || 'devpassword123',
  }
};

const seedData = [
  {
    textContent: 'Welcome to Xikizpedia - a distributed knowledge system',
    metadata: { type: 'welcome', category: 'system' }
  },
  {
    textContent: 'The void gazes back into those who dare to explore its depths',
    metadata: { type: 'philosophy', category: 'void' }
  },
  {
    textContent: 'Knowledge fragments crystallize into wisdom through the process of iteration',
    metadata: { type: 'wisdom', category: 'learning' }
  },
  {
    textContent: 'Each thought creates a ripple in the collective consciousness',
    metadata: { type: 'metaphysics', category: 'consciousness' }
  },
  {
    textContent: 'The SHA-256 hash serves as both fingerprint and gateway to understanding',
    metadata: { type: 'technical', category: 'cryptography' }
  }
];

const seedUsers = [
  { username: 'admin', role: 'admin', metadata: { isSeeded: true } },
  { username: 'alice', role: 'user', metadata: { isSeeded: true } },
  { username: 'bob', role: 'user', metadata: { isSeeded: true } },
  { username: 'viewer', role: 'viewer', metadata: { isSeeded: true } }
];

async function generateVoidData(textContent) {
  const crypto = await import('crypto');
  const hash = crypto.createHash('sha256').update(textContent).digest('hex');
  const voidId = hash.slice(0, 8);
  
  return {
    voidId,
    shaHex: hash,
    receipt: {
      textContent,
      voidId,
      shaHex: hash,
      timestamp: new Date().toISOString()
    }
  };
}

async function seedDatabase() {
  const client = new Client({
    connectionString: config.database.url,
    host: config.database.host,
    port: config.database.port,
    database: config.database.name,
    user: config.database.user,
    password: config.database.password,
  });

  try {
    console.log('Connecting to database...');
    await client.connect();
    
    console.log('Seeding users...');
    for (const user of seedUsers) {
      try {
        await client.query(
          `INSERT INTO xikizpedia.users (username, role, metadata)
           VALUES ($1, $2, $3)
           ON CONFLICT (username) DO NOTHING`,
          [user.username, user.role, JSON.stringify(user.metadata)]
        );
        console.log(`  ✓ User: ${user.username} (${user.role})`);
      } catch (error) {
        console.log(`  - User ${user.username} already exists or error:`, error.message);
      }
    }

    console.log('Seeding Xikizpedia entries...');
    for (const entry of seedData) {
      try {
        const voidData = await generateVoidData(entry.textContent);
        
        await client.query(
          `INSERT INTO xikizpedia.entries (void_id, sha_hex, text_content, metadata, receipt)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (sha_hex) DO NOTHING`,
          [
            voidData.voidId,
            voidData.shaHex,
            entry.textContent,
            JSON.stringify(entry.metadata),
            JSON.stringify(voidData.receipt)
          ]
        );
        console.log(`  ✓ Entry: ${voidData.voidId} - ${entry.textContent.slice(0, 50)}...`);
      } catch (error) {
        console.log(`  - Entry already exists or error:`, error.message);
      }
    }

    // Add some analytics
    const userCount = await client.query('SELECT COUNT(*) as count FROM xikizpedia.users');
    const entryCount = await client.query('SELECT COUNT(*) as count FROM xikizpedia.entries');
    
    console.log(`\n📊 Database seeded successfully:`);
    console.log(`  - Users: ${userCount.rows[0].count}`);
    console.log(`  - Entries: ${entryCount.rows[0].count}`);
    
  } catch (error) {
    console.error('❌ Seeding failed:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  seedDatabase().catch(console.error);
}

export { seedDatabase };