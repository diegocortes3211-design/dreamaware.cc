#!/usr/bin/env node

import { readFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import pg from 'pg';
import { config } from '../server/src/config/index.js';

const { Client } = pg;

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = dirname(__dirname);

async function runMigrations() {
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
    
    console.log('Running database migrations...');
    const migrationSQL = await readFile(join(projectRoot, 'database', 'init.sql'), 'utf8');
    
    await client.query(migrationSQL);
    console.log('✅ Database migrations completed successfully');
    
  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runMigrations().catch(console.error);
}

export { runMigrations };