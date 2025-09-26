import pg from 'pg';
import { config } from '../config/index.js';

const { Pool } = pg;

export class DatabaseService {
    private static instance: DatabaseService;
    private pool: pg.Pool;

    private constructor() {
        this.pool = new Pool({
            connectionString: config.database.url,
            host: config.database.host,
            port: config.database.port,
            database: config.database.name,
            user: config.database.user,
            password: config.database.password,
            max: 20,
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 2000,
        });

        this.pool.on('error', (err) => {
            console.error('Unexpected error on idle client', err);
            process.exit(-1);
        });
    }

    public static getInstance(): DatabaseService {
        if (!DatabaseService.instance) {
            DatabaseService.instance = new DatabaseService();
        }
        return DatabaseService.instance;
    }

    public async query<T = any>(text: string, params?: any[]): Promise<T[]> {
        const start = Date.now();
        const client = await this.pool.connect();
        
        try {
            const res = await client.query(text, params);
            const duration = Date.now() - start;
            console.log('Query executed', { text, duration, rows: res.rowCount });
            return res.rows;
        } finally {
            client.release();
        }
    }

    public async getClient() {
        return this.pool.connect();
    }

    public async healthCheck(): Promise<boolean> {
        try {
            await this.query('SELECT 1');
            return true;
        } catch (error) {
            console.error('Database health check failed:', error);
            return false;
        }
    }

    public async close(): Promise<void> {
        await this.pool.end();
    }
}

export const db = DatabaseService.getInstance();