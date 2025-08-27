-- Create docs table for project documentation
CREATE TABLE IF NOT EXISTS docs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    related_issues JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_docs_project_id ON docs(project_id);
CREATE INDEX idx_docs_category ON docs(category);
CREATE INDEX idx_docs_title ON docs(title);

-- Full text search index
CREATE INDEX idx_docs_search ON docs USING GIN(to_tsvector('english', title || ' ' || content));