#!/usr/bin/env python3
"""
BETTY Memory System v2.0 - Data Converter

This tool handles data transformation from v1.x format to v2.0 format,
including knowledge items, metadata, relationships, and batch processing.
"""

import os
import sys
import json
import sqlite3
import asyncio
import logging
import argparse
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

import aiosqlite
import asyncpg

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class ConversionStats:
    """Statistics for data conversion operation."""
    total_items: int = 0
    processed_items: int = 0
    converted_items: int = 0
    skipped_items: int = 0
    error_items: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate conversion success rate."""
        if self.processed_items == 0:
            return 0.0
        return (self.converted_items / self.processed_items) * 100
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate conversion duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class ConversionRule:
    """Rule for data conversion between formats."""
    source_field: str
    target_field: str
    transform_function: Optional[str] = None
    required: bool = True
    default_value: Any = None
    validation_pattern: Optional[str] = None


class DataConverter:
    """
    Convert data from BETTY v1.x format to v2.0 format.
    
    Handles:
    - Knowledge items and content transformation
    - Metadata format updates
    - Relationship mapping
    - Batch processing with progress tracking
    - Error handling and recovery
    """
    
    def __init__(
        self,
        v1_db_path: str,
        v2_db_config: Dict[str, Any],
        batch_size: int = 100,
        log_level: str = "INFO"
    ):
        """
        Initialize data converter.
        
        Args:
            v1_db_path: Path to v1.x SQLite database
            v2_db_config: v2.0 PostgreSQL connection configuration
            batch_size: Number of items to process per batch
            log_level: Logging level
        """
        self.v1_db_path = Path(v1_db_path)
        self.v2_db_config = v2_db_config
        self.batch_size = batch_size
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Conversion statistics
        self.stats = ConversionStats()
        
        # Error tracking
        self.errors: List[Dict[str, Any]] = []
        self.max_errors = 1000
        
        # Define conversion rules
        self.knowledge_rules = self._define_knowledge_conversion_rules()
        self.metadata_rules = self._define_metadata_conversion_rules()
    
    def _define_knowledge_conversion_rules(self) -> List[ConversionRule]:
        """Define conversion rules for knowledge items."""
        return [
            ConversionRule("id", "v1_id", required=True),
            ConversionRule("title", "title", required=True),
            ConversionRule("content", "content", required=True),
            ConversionRule("type", "knowledge_type", transform_function="map_knowledge_type"),
            ConversionRule("created_at", "created_at", transform_function="parse_timestamp"),
            ConversionRule("updated_at", "updated_at", transform_function="parse_timestamp"),
            ConversionRule("tags", "metadata.tags", transform_function="convert_tags"),
            ConversionRule("metadata", "metadata", transform_function="merge_metadata"),
            ConversionRule("project_id", "project_id", default_value="default"),
            ConversionRule("user_id", "created_by", required=True),
        ]
    
    def _define_metadata_conversion_rules(self) -> List[ConversionRule]:
        """Define conversion rules for metadata."""
        return [
            ConversionRule("source", "source_info.type"),
            ConversionRule("source_url", "source_info.url"),
            ConversionRule("source_id", "source_info.external_id"),
            ConversionRule("importance", "priority", transform_function="map_importance"),
            ConversionRule("category", "categories", transform_function="convert_to_array"),
            ConversionRule("keywords", "extracted_keywords", transform_function="convert_to_array"),
        ]
    
    async def convert_all_data(self) -> ConversionStats:
        """
        Convert all data from v1.x to v2.0 format.
        
        Returns:
            ConversionStats: Statistics about the conversion process
        """
        self.logger.info("Starting data conversion from v1.x to v2.0")
        self.stats.start_time = datetime.now()
        
        try:
            # Connect to databases
            await self._connect_databases()
            
            # Count total items
            await self._count_total_items()
            
            # Convert knowledge items
            await self._convert_knowledge_items()
            
            # Convert relationships
            await self._convert_relationships()
            
            # Convert user data
            await self._convert_user_data()
            
            # Validate conversion results
            await self._validate_conversion()
            
            self.stats.end_time = datetime.now()
            
            self.logger.info(f"Data conversion completed successfully")
            self.logger.info(f"Converted {self.stats.converted_items}/{self.stats.total_items} items")
            self.logger.info(f"Success rate: {self.stats.success_rate:.2f}%")
            self.logger.info(f"Duration: {self.stats.duration:.2f} seconds")
            
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Data conversion failed: {e}")
            self.stats.end_time = datetime.now()
            raise
        finally:
            await self._close_databases()
    
    async def _connect_databases(self):
        """Connect to source and target databases."""
        self.logger.info("Connecting to databases...")
        
        # Connect to v1.x SQLite database
        if not self.v1_db_path.exists():
            raise FileNotFoundError(f"v1.x database not found: {self.v1_db_path}")
        
        self.v1_db = await aiosqlite.connect(str(self.v1_db_path))
        
        # Connect to v2.0 PostgreSQL database
        self.v2_db = await asyncpg.connect(
            host=self.v2_db_config["host"],
            port=self.v2_db_config["port"],
            user=self.v2_db_config["user"],
            password=self.v2_db_config["password"],
            database=self.v2_db_config["database"]
        )
        
        self.logger.info("Database connections established")
    
    async def _close_databases(self):
        """Close database connections."""
        if hasattr(self, 'v1_db'):
            await self.v1_db.close()
        
        if hasattr(self, 'v2_db'):
            await self.v2_db.close()
    
    async def _count_total_items(self):
        """Count total items to be converted."""
        self.logger.info("Counting items for conversion...")
        
        # Count knowledge items
        async with self.v1_db.execute("SELECT COUNT(*) FROM knowledge") as cursor:
            knowledge_count = (await cursor.fetchone())[0]
        
        # Count relationships
        async with self.v1_db.execute("SELECT COUNT(*) FROM relationships") as cursor:
            relationships_count = (await cursor.fetchone())[0]
        
        # Count users
        async with self.v1_db.execute("SELECT COUNT(*) FROM users") as cursor:
            users_count = (await cursor.fetchone())[0]
        
        self.stats.total_items = knowledge_count + relationships_count + users_count
        
        self.logger.info(f"Found {knowledge_count} knowledge items, "
                        f"{relationships_count} relationships, "
                        f"{users_count} users to convert")
    
    async def _convert_knowledge_items(self):
        """Convert knowledge items from v1.x to v2.0 format."""
        self.logger.info("Converting knowledge items...")
        
        # Get knowledge items in batches
        offset = 0
        
        while True:
            # Fetch batch of items
            query = """
                SELECT k.*, u.username as creator_username
                FROM knowledge k
                LEFT JOIN users u ON k.user_id = u.id
                LIMIT ? OFFSET ?
            """
            
            async with self.v1_db.execute(query, (self.batch_size, offset)) as cursor:
                rows = await cursor.fetchall()
                
                if not rows:
                    break
                
                # Get column names
                columns = [description[0] for description in cursor.description]
                
                # Convert batch
                converted_batch = []
                
                for row in rows:
                    try:
                        item_data = dict(zip(columns, row))
                        converted_item = await self._convert_knowledge_item(item_data)
                        converted_batch.append(converted_item)
                        self.stats.converted_items += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to convert knowledge item {row[0]}: {e}")
                        self._record_error("knowledge_item", row[0], str(e))
                        self.stats.error_items += 1
                    
                    self.stats.processed_items += 1
                
                # Insert converted batch into v2.0 database
                if converted_batch:
                    await self._insert_knowledge_batch(converted_batch)
                
                self.logger.info(f"Processed {self.stats.processed_items}/{self.stats.total_items} items")
                
                offset += self.batch_size
    
    async def _convert_knowledge_item(self, v1_item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single knowledge item from v1.x to v2.0 format."""
        converted = {}
        
        # Apply conversion rules
        for rule in self.knowledge_rules:
            try:
                value = self._extract_value(v1_item, rule.source_field)
                
                if value is None and rule.required:
                    if rule.default_value is not None:
                        value = rule.default_value
                    else:
                        raise ValueError(f"Required field {rule.source_field} is missing")
                
                # Apply transformation if specified
                if rule.transform_function and value is not None:
                    value = await self._apply_transformation(rule.transform_function, value, v1_item)
                
                # Set target field
                self._set_nested_value(converted, rule.target_field, value)
                
            except Exception as e:
                if rule.required:
                    raise
                self.logger.warning(f"Failed to convert field {rule.source_field}: {e}")
        
        # Add v2.0 specific fields
        converted.update({
            "id": None,  # Will be generated by database
            "version": "2.0",
            "status": "active",
            "embeddings": None,  # Will be generated by v2.0 system
            "relationships": [],  # Will be populated separately
            "access_control": {
                "owner_id": converted.get("created_by"),
                "visibility": "private",
                "permissions": []
            }
        })
        
        return converted
    
    async def _convert_relationships(self):
        """Convert relationships from v1.x to v2.0 format."""
        self.logger.info("Converting relationships...")
        
        query = """
            SELECT r.*, 
                   k1.title as source_title,
                   k2.title as target_title
            FROM relationships r
            LEFT JOIN knowledge k1 ON r.source_id = k1.id
            LEFT JOIN knowledge k2 ON r.target_id = k2.id
        """
        
        async with self.v1_db.execute(query) as cursor:
            relationships = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
        
        converted_relationships = []
        
        for rel_row in relationships:
            try:
                rel_data = dict(zip(columns, rel_row))
                
                converted_rel = {
                    "source_knowledge_id": rel_data["source_id"],
                    "target_knowledge_id": rel_data["target_id"],
                    "relationship_type": self._map_relationship_type(rel_data.get("type", "related")),
                    "strength": rel_data.get("strength", 0.5),
                    "metadata": {
                        "v1_id": rel_data["id"],
                        "created_at": rel_data.get("created_at"),
                        "direction": rel_data.get("direction", "bidirectional")
                    },
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                converted_relationships.append(converted_rel)
                
            except Exception as e:
                self.logger.error(f"Failed to convert relationship {rel_row[0]}: {e}")
                self._record_error("relationship", rel_row[0], str(e))
        
        # Insert relationships into v2.0 database
        if converted_relationships:
            await self._insert_relationships_batch(converted_relationships)
        
        self.logger.info(f"Converted {len(converted_relationships)} relationships")
    
    async def _convert_user_data(self):
        """Convert user data from v1.x to v2.0 format."""
        self.logger.info("Converting user data...")
        
        async with self.v1_db.execute("SELECT * FROM users") as cursor:
            users = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
        
        converted_users = []
        
        for user_row in users:
            try:
                user_data = dict(zip(columns, user_row))
                
                converted_user = {
                    "v1_id": user_data["id"],
                    "username": user_data["username"],
                    "email": user_data.get("email"),
                    "role": self._map_user_role(user_data.get("role", "user")),
                    "permissions": self._map_user_permissions(user_data.get("permissions", [])),
                    "profile": {
                        "display_name": user_data.get("display_name", user_data["username"]),
                        "preferences": user_data.get("preferences", {}),
                        "metadata": {
                            "migrated_from_v1": True,
                            "v1_created_at": user_data.get("created_at")
                        }
                    },
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "is_active": user_data.get("active", True)
                }
                
                converted_users.append(converted_user)
                
            except Exception as e:
                self.logger.error(f"Failed to convert user {user_row[0]}: {e}")
                self._record_error("user", user_row[0], str(e))
        
        # Insert users into v2.0 database
        if converted_users:
            await self._insert_users_batch(converted_users)
        
        self.logger.info(f"Converted {len(converted_users)} users")
    
    async def _insert_knowledge_batch(self, batch: List[Dict[str, Any]]):
        """Insert batch of converted knowledge items into v2.0 database."""
        insert_query = """
            INSERT INTO knowledge_items (
                v1_id, title, content, knowledge_type, project_id,
                created_by, metadata, status, version, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        
        values = []
        for item in batch:
            values.append([
                item.get("v1_id"),
                item.get("title"),
                item.get("content"),
                item.get("knowledge_type"),
                item.get("project_id"),
                item.get("created_by"),
                json.dumps(item.get("metadata", {})),
                item.get("status"),
                item.get("version"),
                item.get("created_at"),
                item.get("updated_at")
            ])
        
        await self.v2_db.executemany(insert_query, values)
        self.logger.debug(f"Inserted batch of {len(batch)} knowledge items")
    
    async def _insert_relationships_batch(self, batch: List[Dict[str, Any]]):
        """Insert batch of converted relationships into v2.0 database."""
        insert_query = """
            INSERT INTO knowledge_relationships (
                source_knowledge_id, target_knowledge_id, relationship_type,
                strength, metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        values = []
        for rel in batch:
            values.append([
                rel["source_knowledge_id"],
                rel["target_knowledge_id"],
                rel["relationship_type"],
                rel["strength"],
                json.dumps(rel["metadata"]),
                rel["created_at"],
                rel["updated_at"]
            ])
        
        await self.v2_db.executemany(insert_query, values)
        self.logger.debug(f"Inserted batch of {len(batch)} relationships")
    
    async def _insert_users_batch(self, batch: List[Dict[str, Any]]):
        """Insert batch of converted users into v2.0 database."""
        insert_query = """
            INSERT INTO users (
                v1_id, username, email, role, permissions, profile,
                created_at, updated_at, is_active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        
        values = []
        for user in batch:
            values.append([
                user["v1_id"],
                user["username"],
                user["email"],
                user["role"],
                json.dumps(user["permissions"]),
                json.dumps(user["profile"]),
                user["created_at"],
                user["updated_at"],
                user["is_active"]
            ])
        
        await self.v2_db.executemany(insert_query, values)
        self.logger.debug(f"Inserted batch of {len(batch)} users")
    
    async def _validate_conversion(self):
        """Validate conversion results."""
        self.logger.info("Validating conversion results...")
        
        # Check knowledge items count
        v2_knowledge_count = await self.v2_db.fetchval(
            "SELECT COUNT(*) FROM knowledge_items WHERE v1_id IS NOT NULL"
        )
        
        # Check relationships count
        v2_relationships_count = await self.v2_db.fetchval(
            "SELECT COUNT(*) FROM knowledge_relationships WHERE metadata->>'v1_id' IS NOT NULL"
        )
        
        # Check users count
        v2_users_count = await self.v2_db.fetchval(
            "SELECT COUNT(*) FROM users WHERE v1_id IS NOT NULL"
        )
        
        self.logger.info(f"Validation results:")
        self.logger.info(f"  Knowledge items in v2.0: {v2_knowledge_count}")
        self.logger.info(f"  Relationships in v2.0: {v2_relationships_count}")
        self.logger.info(f"  Users in v2.0: {v2_users_count}")
        
        # Check for data integrity issues
        integrity_issues = await self._check_data_integrity()
        
        if integrity_issues:
            self.logger.warning(f"Found {len(integrity_issues)} data integrity issues")
            for issue in integrity_issues[:10]:  # Log first 10 issues
                self.logger.warning(f"  {issue}")
        else:
            self.logger.info("No data integrity issues found")
    
    async def _check_data_integrity(self) -> List[str]:
        """Check for data integrity issues after conversion."""
        issues = []
        
        # Check for orphaned relationships
        orphaned_rels = await self.v2_db.fetch("""
            SELECT r.id, r.source_knowledge_id, r.target_knowledge_id
            FROM knowledge_relationships r
            LEFT JOIN knowledge_items k1 ON r.source_knowledge_id = k1.id
            LEFT JOIN knowledge_items k2 ON r.target_knowledge_id = k2.id
            WHERE k1.id IS NULL OR k2.id IS NULL
        """)
        
        for rel in orphaned_rels:
            issues.append(f"Orphaned relationship: {rel['id']}")
        
        # Check for duplicate knowledge items
        duplicates = await self.v2_db.fetch("""
            SELECT v1_id, COUNT(*) as count
            FROM knowledge_items
            WHERE v1_id IS NOT NULL
            GROUP BY v1_id
            HAVING COUNT(*) > 1
        """)
        
        for dup in duplicates:
            issues.append(f"Duplicate knowledge item with v1_id: {dup['v1_id']}")
        
        return issues
    
    def _extract_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Extract value from nested dictionary using dot notation."""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any):
        """Set value in nested dictionary using dot notation."""
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    async def _apply_transformation(self, transform_function: str, value: Any, context: Dict[str, Any]) -> Any:
        """Apply transformation function to value."""
        if transform_function == "map_knowledge_type":
            return self._map_knowledge_type(value)
        elif transform_function == "parse_timestamp":
            return self._parse_timestamp(value)
        elif transform_function == "convert_tags":
            return self._convert_tags(value)
        elif transform_function == "merge_metadata":
            return self._merge_metadata(value, context)
        elif transform_function == "map_importance":
            return self._map_importance(value)
        elif transform_function == "convert_to_array":
            return self._convert_to_array(value)
        else:
            return value
    
    def _map_knowledge_type(self, v1_type: str) -> str:
        """Map v1.x knowledge type to v2.0 knowledge type."""
        type_mapping = {
            "note": "document",
            "document": "document",
            "snippet": "code",
            "code": "code",
            "link": "reference",
            "reference": "reference",
            "image": "media",
            "file": "media"
        }
        return type_mapping.get(v1_type, "document")
    
    def _parse_timestamp(self, timestamp: str) -> str:
        """Parse and format timestamp for v2.0."""
        if not timestamp:
            return datetime.now().isoformat()
        
        try:
            # Try parsing different timestamp formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            return datetime.now().isoformat()
            
        except Exception:
            return datetime.now().isoformat()
    
    def _convert_tags(self, tags: Union[str, List[str]]) -> List[str]:
        """Convert tags to v2.0 format."""
        if isinstance(tags, str):
            # Handle comma-separated tags
            return [tag.strip() for tag in tags.split(',') if tag.strip()]
        elif isinstance(tags, list):
            return tags
        else:
            return []
    
    def _merge_metadata(self, metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Merge metadata from v1.x with additional context."""
        merged = {}
        
        if isinstance(metadata, dict):
            merged.update(metadata)
        
        # Add migration metadata
        merged.update({
            "migrated_from_v1": True,
            "migration_timestamp": datetime.now().isoformat(),
            "v1_id": context.get("id")
        })
        
        return merged
    
    def _map_importance(self, importance: Union[int, str]) -> int:
        """Map v1.x importance to v2.0 priority."""
        if isinstance(importance, str):
            importance_map = {
                "low": 1,
                "medium": 2,
                "high": 3,
                "critical": 4
            }
            return importance_map.get(importance.lower(), 2)
        elif isinstance(importance, int):
            return max(1, min(4, importance))  # Clamp to 1-4 range
        else:
            return 2  # Default to medium priority
    
    def _convert_to_array(self, value: Union[str, List[str]]) -> List[str]:
        """Convert value to array format."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        elif isinstance(value, list):
            return value
        else:
            return []
    
    def _map_relationship_type(self, v1_type: str) -> str:
        """Map v1.x relationship type to v2.0 relationship type."""
        type_mapping = {
            "related": "related_to",
            "references": "references",
            "child": "contains",
            "parent": "contained_by",
            "similar": "similar_to",
            "duplicate": "duplicate_of"
        }
        return type_mapping.get(v1_type, "related_to")
    
    def _map_user_role(self, v1_role: str) -> str:
        """Map v1.x user role to v2.0 user role."""
        role_mapping = {
            "admin": "admin",
            "moderator": "moderator",
            "user": "user",
            "guest": "viewer"
        }
        return role_mapping.get(v1_role, "user")
    
    def _map_user_permissions(self, v1_permissions: List[str]) -> List[str]:
        """Map v1.x user permissions to v2.0 permissions."""
        permission_mapping = {
            "read": "knowledge:read",
            "write": "knowledge:write",
            "delete": "knowledge:delete",
            "admin": "system:admin",
            "moderate": "system:moderate"
        }
        
        v2_permissions = []
        for perm in v1_permissions:
            if perm in permission_mapping:
                v2_permissions.append(permission_mapping[perm])
        
        return v2_permissions
    
    def _record_error(self, item_type: str, item_id: str, error_message: str):
        """Record conversion error."""
        if len(self.errors) < self.max_errors:
            self.errors.append({
                "type": item_type,
                "id": item_id,
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            })
    
    def save_error_report(self, output_path: str):
        """Save error report to file."""
        report = {
            "conversion_stats": asdict(self.stats),
            "errors": self.errors,
            "generated_at": datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Error report saved to {output_path}")


async def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Convert BETTY v1.x data to v2.0 format")
    parser.add_argument("--v1-db", required=True, help="Path to v1.x SQLite database")
    parser.add_argument("--v2-host", required=True, help="v2.0 PostgreSQL host")
    parser.add_argument("--v2-port", type=int, default=5432, help="v2.0 PostgreSQL port")
    parser.add_argument("--v2-user", required=True, help="v2.0 PostgreSQL username")
    parser.add_argument("--v2-password", required=True, help="v2.0 PostgreSQL password")
    parser.add_argument("--v2-database", required=True, help="v2.0 PostgreSQL database")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--error-report", help="Path to save error report")
    
    args = parser.parse_args()
    
    # Configure v2.0 database connection
    v2_config = {
        "host": args.v2_host,
        "port": args.v2_port,
        "user": args.v2_user,
        "password": args.v2_password,
        "database": args.v2_database
    }
    
    # Create converter and run conversion
    converter = DataConverter(
        v1_db_path=args.v1_db,
        v2_db_config=v2_config,
        batch_size=args.batch_size,
        log_level=args.log_level
    )
    
    try:
        stats = await converter.convert_all_data()
        
        print(f"\nConversion completed:")
        print(f"  Total items: {stats.total_items}")
        print(f"  Converted: {stats.converted_items}")
        print(f"  Errors: {stats.error_items}")
        print(f"  Success rate: {stats.success_rate:.2f}%")
        print(f"  Duration: {stats.duration:.2f} seconds")
        
        # Save error report if requested
        if args.error_report:
            converter.save_error_report(args.error_report)
        
    except Exception as e:
        print(f"Conversion failed: {e}")
        
        if args.error_report:
            converter.save_error_report(args.error_report)
        
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())