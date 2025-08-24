-- ABOUTME: Authentication database schema for BETTY Memory System
-- ABOUTME: JWT-based authentication with RBAC, API keys, and session management

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- User management table
CREATE TABLE IF NOT EXISTS auth_users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'developer', -- admin, developer, reader
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_role CHECK (role IN ('admin', 'developer', 'reader')),
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$'),
    
    -- Indexes
    INDEX idx_auth_users_email (email),
    INDEX idx_auth_users_role (role),
    INDEX idx_auth_users_is_active (is_active),
    INDEX idx_auth_users_created_at (created_at),
    INDEX idx_auth_users_last_login (last_login_at)
);

-- Project access control (many-to-many: users can access multiple projects)
CREATE TABLE IF NOT EXISTS auth_project_permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    project_id VARCHAR(255) NOT NULL,
    permission_level VARCHAR(50) NOT NULL DEFAULT 'read', -- read, write, admin
    granted_by UUID REFERENCES auth_users(user_id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_permission_level CHECK (permission_level IN ('read', 'write', 'admin')),
    CONSTRAINT unique_user_project UNIQUE (user_id, project_id),
    
    -- Indexes
    INDEX idx_project_permissions_user_id (user_id),
    INDEX idx_project_permissions_project_id (project_id),
    INDEX idx_project_permissions_level (permission_level),
    INDEX idx_project_permissions_active (is_active),
    INDEX idx_project_permissions_expires (expires_at)
);

-- API Keys for service-to-service authentication
CREATE TABLE IF NOT EXISTS auth_api_keys (
    api_key_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE, -- Hashed API key
    key_prefix VARCHAR(10) NOT NULL, -- First few chars for identification (e.g., "betty_")
    owner_user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    scopes TEXT[] NOT NULL DEFAULT '{}', -- Array of permission scopes
    project_access TEXT[] NOT NULL DEFAULT '{}', -- Array of accessible project IDs
    is_active BOOLEAN NOT NULL DEFAULT true,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    last_used_at TIMESTAMP WITH TIME ZONE,
    last_used_ip INET,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Indexes
    INDEX idx_api_keys_key_hash (key_hash),
    INDEX idx_api_keys_key_prefix (key_prefix),
    INDEX idx_api_keys_owner_user_id (owner_user_id),
    INDEX idx_api_keys_is_active (is_active),
    INDEX idx_api_keys_expires_at (expires_at),
    INDEX idx_api_keys_last_used (last_used_at)
);

-- Refresh tokens for JWT authentication
CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
    token_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    device_info VARCHAR(255), -- User agent or device identifier
    ip_address INET,
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_refresh_tokens_token_hash (token_hash),
    INDEX idx_refresh_tokens_user_id (user_id),
    INDEX idx_refresh_tokens_is_active (is_active),
    INDEX idx_refresh_tokens_expires_at (expires_at)
);

-- Token blacklist for logout and security
CREATE TABLE IF NOT EXISTS auth_token_blacklist (
    jti VARCHAR(255) PRIMARY KEY, -- JWT ID claim
    user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
    token_type VARCHAR(20) NOT NULL, -- access, refresh
    blacklisted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    reason VARCHAR(255) DEFAULT 'logout',
    
    -- Indexes
    INDEX idx_token_blacklist_user_id (user_id),
    INDEX idx_token_blacklist_expires_at (expires_at),
    INDEX idx_token_blacklist_blacklisted_at (blacklisted_at)
);

-- Authentication audit log
CREATE TABLE IF NOT EXISTS auth_audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth_users(user_id),
    api_key_id UUID REFERENCES auth_api_keys(api_key_id),
    event_type VARCHAR(50) NOT NULL, -- login, logout, failed_login, api_access, token_refresh, etc.
    success BOOLEAN NOT NULL,
    ip_address INET,
    user_agent TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT auth_event_types CHECK (event_type IN (
        'login', 'logout', 'failed_login', 'password_reset', 'password_change',
        'token_refresh', 'api_access', 'account_lock', 'account_unlock',
        'permission_grant', 'permission_revoke', 'api_key_create', 'api_key_revoke'
    )),
    
    -- Indexes
    INDEX idx_auth_audit_user_id (user_id),
    INDEX idx_auth_audit_api_key_id (api_key_id),
    INDEX idx_auth_audit_event_type (event_type),
    INDEX idx_auth_audit_success (success),
    INDEX idx_auth_audit_created_at (created_at),
    INDEX idx_auth_audit_ip_address (ip_address)
);

-- Rate limiting tracking
CREATE TABLE IF NOT EXISTS auth_rate_limits (
    limit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    identifier VARCHAR(255) NOT NULL, -- IP address, user_id, or api_key_id
    limit_type VARCHAR(50) NOT NULL, -- login_attempts, api_requests
    request_count INTEGER NOT NULL DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    window_duration_minutes INTEGER NOT NULL DEFAULT 60,
    is_blocked BOOLEAN NOT NULL DEFAULT false,
    blocked_until TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT unique_identifier_type_window UNIQUE (identifier, limit_type, window_start),
    
    -- Indexes
    INDEX idx_rate_limits_identifier (identifier),
    INDEX idx_rate_limits_type (limit_type),
    INDEX idx_rate_limits_window (window_start),
    INDEX idx_rate_limits_blocked (is_blocked)
);

-- Create updated_at trigger function if not exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_auth_users_updated_at 
    BEFORE UPDATE ON auth_users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_auth_project_permissions_updated_at 
    BEFORE UPDATE ON auth_project_permissions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_auth_api_keys_updated_at 
    BEFORE UPDATE ON auth_api_keys 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Security functions

-- Function to increment failed login attempts and lock account if needed
CREATE OR REPLACE FUNCTION increment_failed_login_attempts(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    current_attempts INTEGER;
    max_attempts INTEGER := 5;
    lockout_minutes INTEGER := 15;
BEGIN
    -- Get current failed attempts
    SELECT failed_login_attempts INTO current_attempts
    FROM auth_users 
    WHERE user_id = p_user_id;
    
    -- Increment attempts
    current_attempts := current_attempts + 1;
    
    -- Check if we should lock the account
    IF current_attempts >= max_attempts THEN
        UPDATE auth_users 
        SET 
            failed_login_attempts = current_attempts,
            locked_until = NOW() + INTERVAL '1 minute' * lockout_minutes,
            updated_at = NOW()
        WHERE user_id = p_user_id;
        
        RETURN true; -- Account is now locked
    ELSE
        UPDATE auth_users 
        SET 
            failed_login_attempts = current_attempts,
            updated_at = NOW()
        WHERE user_id = p_user_id;
        
        RETURN false; -- Account not locked yet
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to reset failed login attempts on successful login
CREATE OR REPLACE FUNCTION reset_failed_login_attempts(p_user_id UUID, p_ip_address INET DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    UPDATE auth_users 
    SET 
        failed_login_attempts = 0,
        locked_until = NULL,
        last_login_at = NOW(),
        last_login_ip = p_ip_address,
        updated_at = NOW()
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user account is locked
CREATE OR REPLACE FUNCTION is_account_locked(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    lock_time TIMESTAMP WITH TIME ZONE;
BEGIN
    SELECT locked_until INTO lock_time
    FROM auth_users 
    WHERE user_id = p_user_id;
    
    -- If no lock time or lock time is in the past, account is not locked
    RETURN lock_time IS NOT NULL AND lock_time > NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired tokens and rate limits
CREATE OR REPLACE FUNCTION cleanup_expired_auth_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    temp_count INTEGER;
BEGIN
    -- Clean up expired refresh tokens
    DELETE FROM auth_refresh_tokens 
    WHERE expires_at < NOW();
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Clean up expired blacklisted tokens
    DELETE FROM auth_token_blacklist 
    WHERE expires_at < NOW();
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Clean up old audit logs (keep last 90 days)
    DELETE FROM auth_audit_log 
    WHERE created_at < NOW() - INTERVAL '90 days';
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Clean up old rate limit entries (keep last 24 hours)
    DELETE FROM auth_rate_limits 
    WHERE window_start < NOW() - INTERVAL '24 hours';
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Insert default admin user (password should be changed immediately)
-- Default password hash is for "ChangeMe123!" - MUST be changed in production
INSERT INTO auth_users (
    user_id,
    email, 
    full_name, 
    password_hash, 
    role, 
    is_active, 
    is_verified
) VALUES (
    'e8e3f2de-070d-4dbd-b899-e49745f1d29b', -- Andre's UUID from existing system
    'admin@betty.memory', 
    'BETTY Admin', 
    '$2b$12$LQv3c1yqBWVHxkd0LQ4lnOeuosQJNO6JxrO.NdKjzgEzqgzWUAGk6', -- bcrypt hash
    'admin', 
    true, 
    true
) ON CONFLICT (user_id) DO NOTHING;

-- Grant admin full access to all projects (wildcard)
INSERT INTO auth_project_permissions (
    user_id,
    project_id,
    permission_level,
    granted_at
) VALUES (
    'e8e3f2de-070d-4dbd-b899-e49745f1d29b',
    '*', -- Wildcard for all projects
    'admin',
    NOW()
) ON CONFLICT (user_id, project_id) DO NOTHING;