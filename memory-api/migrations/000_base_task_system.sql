-- ABOUTME: Base task management system setup before enhanced features
-- ABOUTME: Creates the core tasks table that other enhanced features depend on

BEGIN;

-- Create base tasks table if it doesn't exist
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 3,
    type VARCHAR(50) DEFAULT 'basic',
    created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'in_progress', 'completed', 'cancelled', 'blocked'
    )),
    CONSTRAINT valid_priority CHECK (priority >= 1 AND priority <= 5),
    CONSTRAINT valid_type CHECK (type IN (
        'basic', 'enhanced', 'feature', 'bug', 'enhancement', 'refactor', 'test', 'docs'
    ))
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created);

-- Create trigger for updated timestamp
CREATE OR REPLACE FUNCTION update_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_tasks_updated_at();

COMMIT;