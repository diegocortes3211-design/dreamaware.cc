-- Xikizpedia Database Schema
-- This script sets up the database schema for the Xikizpedia integration

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create main schema
CREATE SCHEMA IF NOT EXISTS xikizpedia;

-- Create tables
CREATE TABLE IF NOT EXISTS xikizpedia.entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    void_id VARCHAR(8) NOT NULL,
    sha_hex VARCHAR(64) NOT NULL UNIQUE,
    text_content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    receipt JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_sha_hex CHECK (char_length(sha_hex) = 64),
    CONSTRAINT valid_void_id CHECK (char_length(void_id) = 8)
);

CREATE TABLE IF NOT EXISTS xikizpedia.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    CONSTRAINT valid_role CHECK (role IN ('admin', 'user', 'viewer'))
);

CREATE TABLE IF NOT EXISTS xikizpedia.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES xikizpedia.users(id) ON DELETE CASCADE,
    stream_id VARCHAR(100) NOT NULL,
    connection_info JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_entries_void_id ON xikizpedia.entries(void_id);
CREATE INDEX IF NOT EXISTS idx_entries_created_at ON xikizpedia.entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_entries_metadata_gin ON xikizpedia.entries USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_entries_receipt_gin ON xikizpedia.entries USING GIN(receipt);
CREATE INDEX IF NOT EXISTS idx_entries_text_search ON xikizpedia.entries USING gin(to_tsvector('english', text_content));

CREATE INDEX IF NOT EXISTS idx_users_username ON xikizpedia.users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON xikizpedia.users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON xikizpedia.users(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON xikizpedia.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_stream_id ON xikizpedia.sessions(stream_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON xikizpedia.sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_last_seen ON xikizpedia.sessions(last_seen DESC);

-- Create trigger for updating updated_at timestamps
CREATE OR REPLACE FUNCTION xikizpedia.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_entries_updated_at 
    BEFORE UPDATE ON xikizpedia.entries 
    FOR EACH ROW EXECUTE FUNCTION xikizpedia.update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON xikizpedia.users 
    FOR EACH ROW EXECUTE FUNCTION xikizpedia.update_updated_at_column();