import crypto from 'crypto';
import { db } from '../database/service.js';

export interface XikizpediaEntry {
    id: string;
    voidId: string;
    shaHex: string;
    textContent: string;
    metadata: any;
    receipt: any;
    createdAt: Date;
    updatedAt: Date;
}

export interface CreateEntryInput {
    textContent: string;
    metadata?: any;
}

export class XikizpediaService {
    private static instance: XikizpediaService;

    private constructor() {}

    public static getInstance(): XikizpediaService {
        if (!XikizpediaService.instance) {
            XikizpediaService.instance = new XikizpediaService();
        }
        return XikizpediaService.instance;
    }

    /**
     * Create a new Xikizpedia entry
     */
    public async createEntry(input: CreateEntryInput): Promise<XikizpediaEntry> {
        const { textContent, metadata = {} } = input;

        // Generate SHA-256 hash
        const hash = crypto.createHash('sha256').update(textContent).digest('hex');
        const voidId = hash.slice(0, 8);

        // Create receipt
        const receipt = {
            textContent,
            voidId,
            shaHex: hash,
            timestamp: new Date().toISOString(),
        };

        try {
            const result = await db.query<XikizpediaEntry>(
                `INSERT INTO xikizpedia.entries (void_id, sha_hex, text_content, metadata, receipt)
                 VALUES ($1, $2, $3, $4, $5)
                 RETURNING id, void_id as "voidId", sha_hex as "shaHex", 
                          text_content as "textContent", metadata, receipt,
                          created_at as "createdAt", updated_at as "updatedAt"`,
                [voidId, hash, textContent, JSON.stringify(metadata), JSON.stringify(receipt)]
            );

            return result[0];
        } catch (error: any) {
            if (error.code === '23505') { // Unique violation
                throw new Error(`Entry with SHA-256 hash already exists: ${hash}`);
            }
            throw error;
        }
    }

    /**
     * Get entry by void ID
     */
    public async getEntryByVoidId(voidId: string): Promise<XikizpediaEntry | null> {
        const result = await db.query<XikizpediaEntry>(
            `SELECT id, void_id as "voidId", sha_hex as "shaHex", 
                    text_content as "textContent", metadata, receipt,
                    created_at as "createdAt", updated_at as "updatedAt"
             FROM xikizpedia.entries 
             WHERE void_id = $1`,
            [voidId]
        );

        return result[0] || null;
    }

    /**
     * Get entry by SHA-256 hash
     */
    public async getEntryBySha(shaHex: string): Promise<XikizpediaEntry | null> {
        const result = await db.query<XikizpediaEntry>(
            `SELECT id, void_id as "voidId", sha_hex as "shaHex", 
                    text_content as "textContent", metadata, receipt,
                    created_at as "createdAt", updated_at as "updatedAt"
             FROM xikizpedia.entries 
             WHERE sha_hex = $1`,
            [shaHex]
        );

        return result[0] || null;
    }

    /**
     * Search entries by text content
     */
    public async searchEntries(query: string, limit = 20, offset = 0): Promise<XikizpediaEntry[]> {
        const result = await db.query<XikizpediaEntry>(
            `SELECT id, void_id as "voidId", sha_hex as "shaHex", 
                    text_content as "textContent", metadata, receipt,
                    created_at as "createdAt", updated_at as "updatedAt",
                    ts_rank(to_tsvector('english', text_content), plainto_tsquery('english', $1)) as rank
             FROM xikizpedia.entries 
             WHERE to_tsvector('english', text_content) @@ plainto_tsquery('english', $1)
             ORDER BY rank DESC, created_at DESC
             LIMIT $2 OFFSET $3`,
            [query, limit, offset]
        );

        return result;
    }

    /**
     * Get recent entries
     */
    public async getRecentEntries(limit = 50, offset = 0): Promise<XikizpediaEntry[]> {
        const result = await db.query<XikizpediaEntry>(
            `SELECT id, void_id as "voidId", sha_hex as "shaHex", 
                    text_content as "textContent", metadata, receipt,
                    created_at as "createdAt", updated_at as "updatedAt"
             FROM xikizpedia.entries 
             ORDER BY created_at DESC
             LIMIT $1 OFFSET $2`,
            [limit, offset]
        );

        return result;
    }

    /**
     * Get entries by metadata query (JSONB)
     */
    public async getEntriesByMetadata(metadataQuery: any, limit = 20, offset = 0): Promise<XikizpediaEntry[]> {
        const result = await db.query<XikizpediaEntry>(
            `SELECT id, void_id as "voidId", sha_hex as "shaHex", 
                    text_content as "textContent", metadata, receipt,
                    created_at as "createdAt", updated_at as "updatedAt"
             FROM xikizpedia.entries 
             WHERE metadata @> $1
             ORDER BY created_at DESC
             LIMIT $2 OFFSET $3`,
            [JSON.stringify(metadataQuery), limit, offset]
        );

        return result;
    }

    /**
     * Get entry count
     */
    public async getEntryCount(): Promise<number> {
        const result = await db.query<{ count: string }>(
            'SELECT COUNT(*) as count FROM xikizpedia.entries'
        );

        return parseInt(result[0].count, 10);
    }
}

export const xikizpediaService = XikizpediaService.getInstance();