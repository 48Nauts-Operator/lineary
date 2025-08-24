#!/usr/bin/env python3
"""
BETTY Memory System v2.0 - Database Schema Migration Tool

This tool handles database schema migration from v1.x to v2.0, including
table structure changes, data migration, and compatibility verification.
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import asyncpg
import yaml
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.database_service import DatabaseService


@dataclass
class MigrationStep:
    """Represents a single migration step."""
    name: str
    description: str
    sql_commands: List[str]
    rollback_commands: List[str]
    version: str
    required: bool = True
    depends_on: List[str] = None


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    step_name: str
    message: str
    execution_time: float
    rows_affected: Optional[int] = None
    error: Optional[str] = None


class SchemaMigrator:
    """
    Database schema migrator for BETTY Memory System v1.x to v2.0.
    
    Handles:
    - Schema version tracking
    - Step-by-step migration with rollback capability
    - Data integrity verification
    - Backup and restoration
    """
    
    def __init__(self, database_url: str, migration_config_path: str = None):
        """
        Initialize schema migrator.
        
        Args:
            database_url: PostgreSQL database connection URL
            migration_config_path: Path to migration configuration file
        """
        self.database_url = database_url
        self.migration_config_path = migration_config_path or self._get_default_config_path()
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Migration tracking
        self.migration_steps: List[MigrationStep] = []
        self.completed_steps: List[str] = []
        self.current_version: str = "1.0"
        self.target_version: str = "2.0"
        
        # Database connection
        self.db_connection: Optional[asyncpg.Connection] = None
        
        # Load migration configuration
        self._load_migration_config()
    
    def _get_default_config_path(self) -> str:
        """Get default migration configuration path."""
        return str(Path(__file__).parent / "migration_config.yaml")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for migration operations."""
        logger = logging.getLogger("SchemaMigrator")
        logger.setLevel(logging.INFO)
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = Path(__file__).parent / "migration.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _load_migration_config(self):
        """Load migration configuration from YAML file."""
        try:
            if not Path(self.migration_config_path).exists():
                self.logger.warning(f"Migration config not found: {self.migration_config_path}")
                self._create_default_config()
                return
            
            with open(self.migration_config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.current_version = config.get('current_version', '1.0')
            self.target_version = config.get('target_version', '2.0')
            
            # Load migration steps
            for step_config in config.get('migration_steps', []):
                step = MigrationStep(
                    name=step_config['name'],
                    description=step_config['description'],
                    sql_commands=step_config['sql_commands'],
                    rollback_commands=step_config.get('rollback_commands', []),
                    version=step_config.get('version', '2.0'),
                    required=step_config.get('required', True),
                    depends_on=step_config.get('depends_on', [])
                )
                self.migration_steps.append(step)
            
            self.logger.info(f"Loaded {len(self.migration_steps)} migration steps")
            
        except Exception as e:
            self.logger.error(f"Failed to load migration config: {e}")
            raise
    
    def _create_default_config(self):
        """Create default migration configuration."""
        default_config = {
            'current_version': '1.0',
            'target_version': '2.0',
            'migration_steps': [
                {
                    'name': 'create_migration_tracking',
                    'description': 'Create migration tracking table',
                    'version': '2.0',
                    'sql_commands': [
                        '''
                        CREATE TABLE IF NOT EXISTS schema_migrations (
                            id SERIAL PRIMARY KEY,
                            version VARCHAR(20) NOT NULL,
                            step_name VARCHAR(100) NOT NULL,
                            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            execution_time_ms INTEGER,
                            success BOOLEAN DEFAULT TRUE
                        );
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_schema_migrations_version 
                        ON schema_migrations(version);
                        '''
                    ],
                    'rollback_commands': [
                        'DROP TABLE IF EXISTS schema_migrations;'
                    ]
                },
                {
                    'name': 'add_user_authentication',
                    'description': 'Add user authentication tables for v2.0',
                    'version': '2.0',
                    'depends_on': ['create_migration_tracking'],
                    'sql_commands': [
                        '''
                        CREATE TABLE IF NOT EXISTS users (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            username VARCHAR(255) UNIQUE NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255),
                            role VARCHAR(50) NOT NULL DEFAULT 'user',
                            permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
                        '''
                    ],
                    'rollback_commands': [
                        'DROP TABLE IF EXISTS users;'
                    ]
                },
                {
                    'name': 'add_project_support',
                    'description': 'Add project support for knowledge organization',
                    'version': '2.0',
                    'depends_on': ['add_user_authentication'],
                    'sql_commands': [
                        '''
                        CREATE TABLE IF NOT EXISTS projects (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
                            settings JSONB DEFAULT '{}'::jsonb,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
                        '''
                    ],
                    'rollback_commands': [
                        'DROP TABLE IF EXISTS projects;'
                    ]
                },
                {
                    'name': 'enhance_knowledge_items',
                    'description': 'Enhance knowledge_items table for v2.0 features',
                    'version': '2.0',
                    'depends_on': ['add_project_support'],
                    'sql_commands': [
                        '''
                        ALTER TABLE knowledge_items 
                        ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE;
                        ''',
                        '''
                        ALTER TABLE knowledge_items 
                        ADD COLUMN IF NOT EXISTS knowledge_type VARCHAR(100) DEFAULT 'document';
                        ''',
                        '''
                        ALTER TABLE knowledge_items 
                        ADD COLUMN IF NOT EXISTS quality_score FLOAT DEFAULT 0.0;
                        ''',
                        '''
                        ALTER TABLE knowledge_items 
                        ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
                        ''',
                        '''
                        ALTER TABLE knowledge_items 
                        ADD COLUMN IF NOT EXISTS vector_embedding FLOAT[] DEFAULT NULL;
                        ''',
                        '''
                        UPDATE knowledge_items 
                        SET knowledge_type = COALESCE(type, 'document')
                        WHERE knowledge_type IS NULL;
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_knowledge_items_project 
                        ON knowledge_items(project_id);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_knowledge_items_type 
                        ON knowledge_items(knowledge_type);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_knowledge_items_quality 
                        ON knowledge_items(quality_score);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_knowledge_items_metadata 
                        ON knowledge_items USING GIN(metadata);
                        '''
                    ],
                    'rollback_commands': [
                        'ALTER TABLE knowledge_items DROP COLUMN IF EXISTS project_id;',
                        'ALTER TABLE knowledge_items DROP COLUMN IF EXISTS knowledge_type;',
                        'ALTER TABLE knowledge_items DROP COLUMN IF EXISTS quality_score;',
                        'ALTER TABLE knowledge_items DROP COLUMN IF EXISTS metadata;',
                        'ALTER TABLE knowledge_items DROP COLUMN IF EXISTS vector_embedding;'
                    ]
                },
                {
                    'name': 'add_batch_operations',
                    'description': 'Add tables for batch operation tracking',
                    'version': '2.0',
                    'depends_on': ['enhance_knowledge_items'],
                    'sql_commands': [
                        '''
                        CREATE TABLE IF NOT EXISTS batch_operations (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            operation_type VARCHAR(100) NOT NULL,
                            status VARCHAR(50) DEFAULT 'queued',
                            progress_percentage FLOAT DEFAULT 0.0,
                            total_items INTEGER DEFAULT 0,
                            processed_items INTEGER DEFAULT 0,
                            successful_items INTEGER DEFAULT 0,
                            failed_items INTEGER DEFAULT 0,
                            current_phase VARCHAR(100),
                            metadata JSONB DEFAULT '{}'::jsonb,
                            error_details TEXT,
                            started_at TIMESTAMP WITH TIME ZONE,
                            completed_at TIMESTAMP WITH TIME ZONE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_batch_operations_status 
                        ON batch_operations(status);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_batch_operations_type 
                        ON batch_operations(operation_type);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_batch_operations_created 
                        ON batch_operations(created_at);
                        '''
                    ],
                    'rollback_commands': [
                        'DROP TABLE IF EXISTS batch_operations;'
                    ]
                },
                {
                    'name': 'add_cross_project_features',
                    'description': 'Add cross-project intelligence tables',
                    'version': '2.0',
                    'depends_on': ['add_batch_operations'],
                    'sql_commands': [
                        '''
                        CREATE TABLE IF NOT EXISTS project_connections (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            source_project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                            target_project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                            connection_type VARCHAR(50) NOT NULL,
                            permissions JSONB DEFAULT '{}'::jsonb,
                            status VARCHAR(50) DEFAULT 'active',
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            UNIQUE(source_project_id, target_project_id)
                        );
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_project_connections_source 
                        ON project_connections(source_project_id);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_project_connections_target 
                        ON project_connections(target_project_id);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_project_connections_type 
                        ON project_connections(connection_type);
                        '''
                    ],
                    'rollback_commands': [
                        'DROP TABLE IF EXISTS project_connections;'
                    ]
                },
                {
                    'name': 'add_webhooks_support',
                    'description': 'Add webhook management tables',
                    'version': '2.0',
                    'depends_on': ['add_cross_project_features'],
                    'sql_commands': [
                        '''
                        CREATE TABLE IF NOT EXISTS webhooks (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                            name VARCHAR(255) NOT NULL,
                            url VARCHAR(500) NOT NULL,
                            events TEXT[] NOT NULL,
                            secret VARCHAR(255),
                            active BOOLEAN DEFAULT TRUE,
                            filters JSONB DEFAULT '{}'::jsonb,
                            headers JSONB DEFAULT '{}'::jsonb,
                            retry_config JSONB DEFAULT '{}'::jsonb,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                        ''',
                        '''
                        CREATE TABLE IF NOT EXISTS webhook_deliveries (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            webhook_id UUID REFERENCES webhooks(id) ON DELETE CASCADE,
                            event_type VARCHAR(100) NOT NULL,
                            payload JSONB NOT NULL,
                            status VARCHAR(50) DEFAULT 'pending',
                            response_code INTEGER,
                            response_body TEXT,
                            response_time_ms INTEGER,
                            attempt_count INTEGER DEFAULT 0,
                            max_attempts INTEGER DEFAULT 3,
                            next_retry_at TIMESTAMP WITH TIME ZONE,
                            delivered_at TIMESTAMP WITH TIME ZONE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_webhooks_user ON webhooks(user_id);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_webhooks_active ON webhooks(active);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook 
                        ON webhook_deliveries(webhook_id);
                        ''',
                        '''
                        CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_status 
                        ON webhook_deliveries(status);
                        '''
                    ],
                    'rollback_commands': [
                        'DROP TABLE IF EXISTS webhook_deliveries;',
                        'DROP TABLE IF EXISTS webhooks;'
                    ]
                },
                {
                    'name': 'migrate_existing_data',
                    'description': 'Migrate existing v1.x data to v2.0 format',
                    'version': '2.0',
                    'depends_on': ['add_webhooks_support'],
                    'sql_commands': [
                        '''
                        -- Create default project for existing knowledge items
                        INSERT INTO projects (id, name, description)
                        VALUES ('00000000-0000-0000-0000-000000000001', 'Default Project', 'Migrated from v1.x')
                        ON CONFLICT DO NOTHING;
                        ''',
                        '''
                        -- Update knowledge items to use default project
                        UPDATE knowledge_items 
                        SET project_id = '00000000-0000-0000-0000-000000000001'
                        WHERE project_id IS NULL;
                        ''',
                        '''
                        -- Migrate tags from array to metadata JSON
                        UPDATE knowledge_items 
                        SET metadata = jsonb_build_object(
                            'tags', COALESCE(tags, ARRAY[]::text[]),
                            'migrated_from', 'v1.x',
                            'migration_date', NOW()::text
                        )
                        WHERE metadata = '{}'::jsonb OR metadata IS NULL;
                        ''',
                        '''
                        -- Update sessions with migration metadata
                        UPDATE sessions 
                        SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                            'migrated_from', 'v1.x',
                            'migration_date', NOW()::text
                        )
                        WHERE metadata IS NULL OR NOT (metadata ? 'migrated_from');
                        '''
                    ],
                    'rollback_commands': [
                        'UPDATE knowledge_items SET project_id = NULL;',
                        'DELETE FROM projects WHERE id = \'00000000-0000-0000-0000-000000000001\';'
                    ]
                }
            ]
        }
        
        # Save default configuration
        with open(self.migration_config_path, 'w') as f:
            yaml.safe_dump(default_config, f, indent=2, sort_keys=False)
        
        self.logger.info(f"Created default migration config: {self.migration_config_path}")
        
        # Load the created config
        self._load_migration_config()
    
    async def connect_database(self):
        """Connect to the database."""
        try:
            self.db_connection = await asyncpg.connect(self.database_url)
            self.logger.info("Connected to database")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect_database(self):
        """Disconnect from the database."""
        if self.db_connection:
            await self.db_connection.close()
            self.logger.info("Disconnected from database")
    
    async def check_current_version(self) -> str:
        """Check current schema version."""
        try:
            # Check if migration tracking table exists
            result = await self.db_connection.fetchval('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'schema_migrations'
                );
            ''')
            
            if not result:
                return "1.0"  # No migration tracking = v1.0
            
            # Get latest migration version
            latest_version = await self.db_connection.fetchval('''
                SELECT version 
                FROM schema_migrations 
                WHERE success = TRUE 
                ORDER BY applied_at DESC 
                LIMIT 1;
            ''')
            
            return latest_version or "1.0"
            
        except Exception as e:
            self.logger.error(f"Failed to check current version: {e}")
            return "1.0"
    
    async def get_completed_steps(self) -> List[str]:
        """Get list of completed migration steps."""
        try:
            # Check if migration tracking exists
            has_tracking = await self.db_connection.fetchval('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'schema_migrations'
                );
            ''')
            
            if not has_tracking:
                return []
            
            completed = await self.db_connection.fetch('''
                SELECT step_name 
                FROM schema_migrations 
                WHERE success = TRUE 
                ORDER BY applied_at;
            ''')
            
            return [row['step_name'] for row in completed]
            
        except Exception as e:
            self.logger.error(f"Failed to get completed steps: {e}")
            return []
    
    async def create_backup(self, backup_path: str = None) -> str:
        """Create database backup before migration."""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"betty_backup_{timestamp}.sql"
        
        backup_path = str(Path(backup_path).resolve())
        
        try:
            # Extract database connection info
            import urllib.parse
            parsed = urllib.parse.urlparse(self.database_url)
            
            host = parsed.hostname
            port = parsed.port or 5432
            dbname = parsed.path[1:]  # Remove leading slash
            username = parsed.username
            password = parsed.password
            
            # Create pg_dump command
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password
            
            import subprocess
            
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', str(port),
                '-U', username,
                '-d', dbname,
                '-f', backup_path,
                '--verbose',
                '--no-owner',
                '--no-privileges'
            ]
            
            self.logger.info(f"Creating backup: {backup_path}")
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Backup failed: {e.stderr}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise
    
    async def execute_migration_step(self, step: MigrationStep) -> MigrationResult:
        """Execute a single migration step."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.info(f"Executing migration step: {step.name}")
            self.logger.info(f"Description: {step.description}")
            
            total_rows_affected = 0
            
            # Execute each SQL command in the step
            async with self.db_connection.transaction():
                for i, sql_command in enumerate(step.sql_commands):
                    self.logger.debug(f"Executing command {i+1}/{len(step.sql_commands)}")
                    
                    # Clean up the SQL command
                    sql_command = sql_command.strip()
                    if not sql_command:
                        continue
                    
                    try:
                        # Execute command and count affected rows if possible
                        result = await self.db_connection.execute(sql_command)
                        
                        # Extract affected rows from result
                        if result and result.startswith(('INSERT', 'UPDATE', 'DELETE')):
                            rows_affected = int(result.split()[-1])
                            total_rows_affected += rows_affected
                    
                    except Exception as e:
                        self.logger.error(f"SQL command failed: {sql_command[:100]}...")
                        raise
                
                # Record successful migration
                await self.db_connection.execute('''
                    INSERT INTO schema_migrations (version, step_name, execution_time_ms, success)
                    VALUES ($1, $2, $3, $4);
                ''', step.version, step.name, int((asyncio.get_event_loop().time() - start_time) * 1000), True)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            result = MigrationResult(
                success=True,
                step_name=step.name,
                message=f"Step completed successfully",
                execution_time=execution_time,
                rows_affected=total_rows_affected if total_rows_affected > 0 else None
            )
            
            self.logger.info(f"Step '{step.name}' completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            result = MigrationResult(
                success=False,
                step_name=step.name,
                message=f"Step failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.logger.error(f"Step '{step.name}' failed after {execution_time:.2f}s: {e}")
            
            # Record failed migration
            try:
                await self.db_connection.execute('''
                    INSERT INTO schema_migrations (version, step_name, execution_time_ms, success)
                    VALUES ($1, $2, $3, $4);
                ''', step.version, step.name, int(execution_time * 1000), False)
            except:
                pass  # Ignore if we can't record the failure
            
            return result
    
    async def rollback_migration_step(self, step: MigrationStep) -> MigrationResult:
        """Rollback a single migration step."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.info(f"Rolling back migration step: {step.name}")
            
            if not step.rollback_commands:
                return MigrationResult(
                    success=False,
                    step_name=step.name,
                    message="No rollback commands defined",
                    execution_time=0,
                    error="No rollback commands"
                )
            
            # Execute rollback commands
            async with self.db_connection.transaction():
                for sql_command in step.rollback_commands:
                    sql_command = sql_command.strip()
                    if sql_command:
                        await self.db_connection.execute(sql_command)
                
                # Remove migration record
                await self.db_connection.execute('''
                    DELETE FROM schema_migrations 
                    WHERE step_name = $1;
                ''', step.name)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            result = MigrationResult(
                success=True,
                step_name=step.name,
                message="Step rolled back successfully",
                execution_time=execution_time
            )
            
            self.logger.info(f"Step '{step.name}' rolled back in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            result = MigrationResult(
                success=False,
                step_name=step.name,
                message=f"Rollback failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.logger.error(f"Rollback of '{step.name}' failed after {execution_time:.2f}s: {e}")
            return result
    
    def _resolve_dependencies(self) -> List[MigrationStep]:
        """Resolve migration step dependencies and return ordered list."""
        resolved = []
        remaining = self.migration_steps.copy()
        resolved_names = set()
        
        while remaining:
            progress_made = False
            
            for step in remaining.copy():
                # Check if all dependencies are resolved
                if not step.depends_on or all(dep in resolved_names for dep in step.depends_on):
                    resolved.append(step)
                    resolved_names.add(step.name)
                    remaining.remove(step)
                    progress_made = True
            
            if not progress_made:
                # Circular dependency or missing dependency
                unresolved = [step.name for step in remaining]
                missing_deps = []
                for step in remaining:
                    if step.depends_on:
                        for dep in step.depends_on:
                            if dep not in resolved_names and dep not in [s.name for s in remaining]:
                                missing_deps.append(dep)
                
                if missing_deps:
                    raise ValueError(f"Missing dependencies: {missing_deps}")
                else:
                    raise ValueError(f"Circular dependencies detected in steps: {unresolved}")
        
        return resolved
    
    async def migrate_to_version(self, target_version: str = "2.0", dry_run: bool = False) -> Dict[str, Any]:
        """
        Migrate database to target version.
        
        Args:
            target_version: Target schema version
            dry_run: If True, only validate migration steps without executing
            
        Returns:
            Migration results summary
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Check current version
            current_version = await self.check_current_version()
            self.logger.info(f"Current schema version: {current_version}")
            self.logger.info(f"Target schema version: {target_version}")
            
            if current_version == target_version:
                return {
                    'success': True,
                    'message': f'Already at target version {target_version}',
                    'current_version': current_version,
                    'target_version': target_version,
                    'steps_executed': 0,
                    'execution_time': 0
                }
            
            # Get completed steps
            completed_steps = await self.get_completed_steps()
            self.logger.info(f"Completed steps: {len(completed_steps)}")
            
            # Resolve dependencies
            ordered_steps = self._resolve_dependencies()
            
            # Filter steps that need to be executed
            pending_steps = [
                step for step in ordered_steps 
                if step.name not in completed_steps and step.version == target_version
            ]
            
            self.logger.info(f"Pending steps: {len(pending_steps)}")
            
            if dry_run:
                return {
                    'success': True,
                    'message': f'Dry run completed. {len(pending_steps)} steps would be executed.',
                    'current_version': current_version,
                    'target_version': target_version,
                    'pending_steps': [
                        {
                            'name': step.name,
                            'description': step.description,
                            'required': step.required,
                            'depends_on': step.depends_on or []
                        }
                        for step in pending_steps
                    ],
                    'dry_run': True
                }
            
            if not pending_steps:
                return {
                    'success': True,
                    'message': 'No migration steps needed',
                    'current_version': current_version,
                    'target_version': target_version,
                    'steps_executed': 0,
                    'execution_time': 0
                }
            
            # Create backup before migration
            backup_path = await self.create_backup()
            self.logger.info(f"Backup created: {backup_path}")
            
            # Execute migration steps
            results = []
            successful_steps = 0
            
            for step in pending_steps:
                result = await self.execute_migration_step(step)
                results.append(result)
                
                if result.success:
                    successful_steps += 1
                else:
                    # Migration failed, stop here
                    self.logger.error(f"Migration failed at step: {step.name}")
                    break
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Final version check
            final_version = await self.check_current_version()
            
            migration_summary = {
                'success': successful_steps == len(pending_steps),
                'message': f'Migration {"completed" if successful_steps == len(pending_steps) else "failed"}',
                'current_version': current_version,
                'target_version': target_version,
                'final_version': final_version,
                'steps_executed': successful_steps,
                'total_steps': len(pending_steps),
                'execution_time': execution_time,
                'backup_path': backup_path,
                'step_results': [
                    {
                        'name': result.step_name,
                        'success': result.success,
                        'message': result.message,
                        'execution_time': result.execution_time,
                        'rows_affected': result.rows_affected,
                        'error': result.error
                    }
                    for result in results
                ]
            }
            
            self.logger.info(f"Migration summary: {successful_steps}/{len(pending_steps)} steps completed")
            return migration_summary
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            self.logger.error(f"Migration failed: {e}")
            
            return {
                'success': False,
                'message': f'Migration failed: {str(e)}',
                'current_version': current_version if 'current_version' in locals() else 'unknown',
                'target_version': target_version,
                'execution_time': execution_time,
                'error': str(e)
            }
    
    async def rollback_to_version(self, target_version: str = "1.0") -> Dict[str, Any]:
        """
        Rollback database to target version.
        
        Args:
            target_version: Target version to rollback to
            
        Returns:
            Rollback results summary
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            current_version = await self.check_current_version()
            self.logger.info(f"Current version: {current_version}")
            self.logger.info(f"Rolling back to version: {target_version}")
            
            if current_version == target_version:
                return {
                    'success': True,
                    'message': f'Already at version {target_version}',
                    'current_version': current_version,
                    'target_version': target_version
                }
            
            # Get completed steps in reverse order
            completed_steps = await self.get_completed_steps()
            
            # Find steps to rollback
            steps_to_rollback = []
            for step in reversed(self.migration_steps):
                if step.name in completed_steps:
                    steps_to_rollback.append(step)
                    if step.version == target_version:
                        break
            
            self.logger.info(f"Steps to rollback: {len(steps_to_rollback)}")
            
            # Create backup
            backup_path = await self.create_backup()
            
            # Execute rollbacks
            results = []
            successful_rollbacks = 0
            
            for step in steps_to_rollback:
                result = await self.rollback_migration_step(step)
                results.append(result)
                
                if result.success:
                    successful_rollbacks += 1
                else:
                    self.logger.error(f"Rollback failed at step: {step.name}")
                    break
            
            execution_time = asyncio.get_event_loop().time() - start_time
            final_version = await self.check_current_version()
            
            return {
                'success': successful_rollbacks == len(steps_to_rollback),
                'message': f'Rollback {"completed" if successful_rollbacks == len(steps_to_rollback) else "failed"}',
                'original_version': current_version,
                'target_version': target_version,
                'final_version': final_version,
                'steps_rolled_back': successful_rollbacks,
                'total_steps': len(steps_to_rollback),
                'execution_time': execution_time,
                'backup_path': backup_path,
                'rollback_results': results
            }
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            self.logger.error(f"Rollback failed: {e}")
            
            return {
                'success': False,
                'message': f'Rollback failed: {str(e)}',
                'execution_time': execution_time,
                'error': str(e)
            }
    
    async def validate_migration(self) -> Dict[str, Any]:
        """Validate database after migration."""
        try:
            validation_results = {
                'success': True,
                'checks': {},
                'errors': []
            }
            
            # Check table existence
            expected_tables = [
                'users', 'projects', 'knowledge_items', 'sessions',
                'batch_operations', 'project_connections', 'webhooks',
                'webhook_deliveries', 'schema_migrations'
            ]
            
            for table in expected_tables:
                exists = await self.db_connection.fetchval('''
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = $1
                    );
                ''', table)
                
                validation_results['checks'][f'table_{table}_exists'] = exists
                
                if not exists:
                    validation_results['success'] = False
                    validation_results['errors'].append(f'Missing table: {table}')
            
            # Check column existence
            column_checks = [
                ('knowledge_items', 'project_id'),
                ('knowledge_items', 'knowledge_type'),
                ('knowledge_items', 'quality_score'),
                ('knowledge_items', 'metadata'),
                ('users', 'permissions'),
                ('projects', 'settings')
            ]
            
            for table, column in column_checks:
                exists = await self.db_connection.fetchval('''
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = $1 AND column_name = $2
                    );
                ''', table, column)
                
                validation_results['checks'][f'column_{table}_{column}_exists'] = exists
                
                if not exists:
                    validation_results['success'] = False
                    validation_results['errors'].append(f'Missing column: {table}.{column}')
            
            # Check data integrity
            try:
                # Check if knowledge items have projects assigned
                orphaned_items = await self.db_connection.fetchval('''
                    SELECT COUNT(*) FROM knowledge_items WHERE project_id IS NULL;
                ''')
                
                validation_results['checks']['orphaned_knowledge_items'] = orphaned_items
                
                if orphaned_items > 0:
                    validation_results['errors'].append(f'{orphaned_items} knowledge items without project')
                
                # Check migration tracking
                migration_records = await self.db_connection.fetchval('''
                    SELECT COUNT(*) FROM schema_migrations WHERE success = TRUE;
                ''')
                
                validation_results['checks']['migration_records'] = migration_records
                
            except Exception as e:
                validation_results['errors'].append(f'Data integrity check failed: {e}')
            
            return validation_results
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Validation failed: {e}',
                'checks': {},
                'errors': [str(e)]
            }


async def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='BETTY Schema Migration Tool')
    parser.add_argument('--database-url', required=True, help='PostgreSQL database URL')
    parser.add_argument('--config', help='Migration configuration file path')
    parser.add_argument('--target-version', default='2.0', help='Target schema version')
    parser.add_argument('--dry-run', action='store_true', help='Dry run without executing')
    parser.add_argument('--rollback', action='store_true', help='Rollback to target version')
    parser.add_argument('--validate', action='store_true', help='Validate migration')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    migrator = SchemaMigrator(args.database_url, args.config)
    
    try:
        await migrator.connect_database()
        
        if args.validate:
            result = await migrator.validate_migration()
            print("\nValidation Results:")
            print(json.dumps(result, indent=2))
            
        elif args.rollback:
            result = await migrator.rollback_to_version(args.target_version)
            print("\nRollback Results:")
            print(json.dumps(result, indent=2, default=str))
            
        else:
            result = await migrator.migrate_to_version(args.target_version, args.dry_run)
            print("\nMigration Results:")
            print(json.dumps(result, indent=2, default=str))
    
    finally:
        await migrator.disconnect_database()


if __name__ == '__main__':
    asyncio.run(main())