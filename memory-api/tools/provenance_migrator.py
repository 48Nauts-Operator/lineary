#!/usr/bin/env python3
"""
ABOUTME: Migration tool for populating BETTY provenance system with existing data
ABOUTME: Backfills provenance records for existing knowledge items and establishes data lineage
"""

import argparse
import asyncio
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID, uuid4
from pathlib import Path

import asyncpg
from rich.console import Console
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table

console = Console()

class ProvenanceMigrator:
    """Tool for migrating existing data to the provenance system"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.db_connection = None
        
        # Default data sources for migration
        self.default_sources = {
            "legacy": {
                "source_name": "Legacy/Unknown",
                "source_type": "internal_patterns",
                "description": "Legacy data without clear provenance",
                "reliability_score": 0.5,
                "is_active": False
            },
            "137docs": {
                "source_name": "137docs",
                "source_type": "documentation",
                "description": "137docs platform knowledge patterns",
                "reliability_score": 0.9,
                "is_active": True,
                "base_url": "https://137docs.ai"
            },
            "context7": {
                "source_name": "Context7",
                "source_type": "documentation",
                "description": "Context7 AI documentation patterns",
                "reliability_score": 0.85,
                "is_active": True,
                "base_url": "https://context7.ai"
            },
            "stack_overflow": {
                "source_name": "Stack Overflow",
                "source_type": "qa_site",
                "description": "Stack Overflow question/answer patterns",
                "reliability_score": 0.8,
                "is_active": True,
                "base_url": "https://stackoverflow.com"
            },
            "owasp": {
                "source_name": "OWASP",
                "source_type": "security_framework",
                "description": "OWASP security patterns and guidelines",
                "reliability_score": 0.95,
                "is_active": True,
                "base_url": "https://owasp.org"
            }
        }
    
    async def connect(self):
        """Establish database connection"""
        try:
            self.db_connection = await asyncpg.connect(**self.db_config)
            console.print("[green]✓[/green] Connected to BETTY database")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection"""
        if self.db_connection:
            await self.db_connection.close()
            console.print("[green]✓[/green] Database connection closed")
    
    async def migrate_all(self, dry_run: bool = False, batch_size: int = 100):
        """Run complete migration process"""
        
        console.print("\n[bold blue]🚀 BETTY Provenance Migration[/bold blue]")
        console.print("=" * 50)
        
        if dry_run:
            console.print("[yellow]⚠️  Running in DRY RUN mode - no changes will be made[/yellow]")
        
        # Step 1: Setup data sources
        await self._setup_data_sources(dry_run)
        
        # Step 2: Create default extraction job
        default_job_id = await self._create_default_extraction_job(dry_run)
        
        # Step 3: Migrate knowledge items without provenance
        await self._migrate_knowledge_items(dry_run, batch_size, default_job_id)
        
        # Step 4: Create quality assessments for existing items
        await self._create_quality_assessments(dry_run, batch_size)
        
        # Step 5: Populate internal annotations for flagged items
        await self._create_migration_annotations(dry_run)
        
        # Step 6: Generate migration report
        await self._generate_migration_report()
        
        console.print("\n[bold green]✅ Migration completed successfully![/bold green]")
    
    async def _setup_data_sources(self, dry_run: bool):
        """Setup default data sources"""
        
        console.print("\n[bold yellow]📊 Setting up data sources...[/bold yellow]")
        
        for source_key, source_data in self.default_sources.items():
            exists_query = "SELECT id FROM data_sources WHERE source_name = $1"
            existing = await self.db_connection.fetchval(exists_query, source_data["source_name"])
            
            if existing:
                console.print(f"[dim]• {source_data['source_name']} already exists[/dim]")
                continue
            
            if not dry_run:
                insert_query = """
                INSERT INTO data_sources (
                    source_name, source_type, description, reliability_score, 
                    is_active, base_url, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """
                
                source_id = await self.db_connection.fetchval(
                    insert_query,
                    source_data["source_name"],
                    source_data["source_type"],
                    source_data["description"],
                    source_data["reliability_score"],
                    source_data["is_active"],
                    source_data.get("base_url"),
                    json.dumps({"migration_created": True})
                )
                
                console.print(f"[green]✓[/green] Created data source: {source_data['source_name']} ({source_id})")
            else:
                console.print(f"[cyan]→[/cyan] Would create data source: {source_data['source_name']}")
    
    async def _create_default_extraction_job(self, dry_run: bool) -> Optional[UUID]:
        """Create default extraction job for migration"""
        
        console.print("\n[bold yellow]⚙️  Creating default extraction job...[/bold yellow]")
        
        # Get legacy data source ID
        legacy_source_query = "SELECT id FROM data_sources WHERE source_name = 'Legacy/Unknown'"
        legacy_source_id = await self.db_connection.fetchval(legacy_source_query)
        
        if not legacy_source_id:
            console.print("[red]❌ Legacy data source not found[/red]")
            return None
        
        # Check if migration job already exists
        existing_job_query = "SELECT id FROM extraction_jobs WHERE job_name = 'Migration Job - Legacy Data'"
        existing_job = await self.db_connection.fetchval(existing_job_query)
        
        if existing_job:
            console.print(f"[dim]• Migration job already exists: {existing_job}[/dim]")
            return existing_job
        
        if not dry_run:
            job_id = uuid4()
            insert_job_query = """
            INSERT INTO extraction_jobs (
                id, job_name, job_type, data_source_id, extraction_method, 
                extraction_version, started_at, completed_at, status, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """
            
            migration_time = datetime.now(timezone.utc) - timedelta(days=1)
            
            created_job_id = await self.db_connection.fetchval(
                insert_job_query,
                job_id,
                "Migration Job - Legacy Data",
                "manual_import",
                legacy_source_id,
                "legacy_import",
                "1.0.0",
                migration_time,
                migration_time,
                "completed",
                json.dumps({"migration_job": True, "created_by": "provenance_migrator"})
            )
            
            console.print(f"[green]✓[/green] Created migration extraction job: {created_job_id}")
            return created_job_id
        else:
            console.print("[cyan]→[/cyan] Would create migration extraction job")
            return uuid4()  # Return dummy ID for dry run
    
    async def _migrate_knowledge_items(self, dry_run: bool, batch_size: int, default_job_id: UUID):
        """Migrate knowledge items without provenance"""
        
        console.print("\n[bold yellow]📚 Migrating knowledge items...[/bold yellow]")
        
        # Find knowledge items without provenance
        count_query = """
        SELECT COUNT(*)
        FROM knowledge_items ki
        LEFT JOIN knowledge_provenance kp ON ki.id = kp.knowledge_item_id AND kp.is_current_version = true
        WHERE kp.id IS NULL
        """
        
        total_items = await self.db_connection.fetchval(count_query)
        
        if total_items == 0:
            console.print("[green]✓[/green] All knowledge items already have provenance records")
            return
        
        console.print(f"Found {total_items} knowledge items without provenance")
        
        # Get items in batches
        fetch_query = """
        SELECT ki.id, ki.title, ki.content, ki.metadata, ki.created_at
        FROM knowledge_items ki
        LEFT JOIN knowledge_provenance kp ON ki.id = kp.knowledge_item_id AND kp.is_current_version = true
        WHERE kp.id IS NULL
        ORDER BY ki.created_at
        LIMIT $1 OFFSET $2
        """
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Migrating knowledge items...", total=total_items)
            
            offset = 0
            migrated_count = 0
            
            while offset < total_items:
                batch = await self.db_connection.fetch(fetch_query, batch_size, offset)
                
                if not batch:
                    break
                
                for item in batch:
                    success = await self._create_provenance_for_item(item, default_job_id, dry_run)
                    if success:
                        migrated_count += 1
                    
                    progress.advance(task, 1)
                
                offset += batch_size
        
        console.print(f"[green]✓[/green] Migrated provenance for {migrated_count} knowledge items")
    
    async def _create_provenance_for_item(
        self, 
        item: Dict[str, Any], 
        default_job_id: UUID, 
        dry_run: bool
    ) -> bool:
        """Create provenance record for a single knowledge item"""
        
        try:
            # Determine data source based on metadata or content
            source_id = await self._determine_data_source(item)
            
            # Generate content hashes
            content_hash = hashlib.sha256(item['content'].encode('utf-8')).hexdigest()
            
            # Determine original source URL
            original_url = self._extract_source_url(item)
            
            if not dry_run:
                provenance_id = uuid4()
                insert_query = """
                INSERT INTO knowledge_provenance (
                    id, knowledge_item_id, extraction_job_id, data_source_id,
                    original_source_url, original_content_hash, processed_content_hash,
                    extraction_timestamp, extraction_method_version, raw_content,
                    validation_status, internal_notes, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """
                
                await self.db_connection.execute(
                    insert_query,
                    provenance_id,
                    item['id'],
                    default_job_id,
                    source_id,
                    original_url,
                    content_hash,
                    content_hash,
                    item['created_at'],
                    "legacy_import",
                    item['content'],
                    "needs_review",
                    "Auto-generated provenance record during migration",
                    json.dumps({"migration_created": True, "original_metadata": item.get('metadata', {})})
                )
            
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to create provenance for {item['id']}: {e}")
            return False
    
    async def _determine_data_source(self, item: Dict[str, Any]) -> UUID:
        """Determine the most appropriate data source for an item"""
        
        metadata = item.get('metadata', {})
        content = item.get('content', '').lower()
        title = item.get('title', '').lower()
        
        # Check metadata for source hints
        if metadata:
            if 'source_url' in metadata:
                url = metadata['source_url'].lower()
                if '137docs' in url:
                    return await self._get_source_id("137docs")
                elif 'context7' in url:
                    return await self._get_source_id("Context7")
                elif 'stackoverflow' in url:
                    return await self._get_source_id("Stack Overflow")
                elif 'owasp' in url:
                    return await self._get_source_id("OWASP")
            
            if metadata.get('source') == '137docs':
                return await self._get_source_id("137docs")
        
        # Check content for source indicators
        if 'owasp' in content or 'security' in title:
            return await self._get_source_id("OWASP")
        elif 'stack overflow' in content or 'stackoverflow' in content:
            return await self._get_source_id("Stack Overflow")
        elif '137docs' in content:
            return await self._get_source_id("137docs")
        elif 'context7' in content:
            return await self._get_source_id("Context7")
        
        # Default to legacy source
        return await self._get_source_id("Legacy/Unknown")
    
    async def _get_source_id(self, source_name: str) -> UUID:
        """Get data source ID by name"""
        query = "SELECT id FROM data_sources WHERE source_name = $1"
        source_id = await self.db_connection.fetchval(query, source_name)
        if not source_id:
            raise ValueError(f"Data source not found: {source_name}")
        return source_id
    
    def _extract_source_url(self, item: Dict[str, Any]) -> str:
        """Extract or generate source URL for the item"""
        metadata = item.get('metadata', {})
        
        if 'source_url' in metadata:
            return metadata['source_url']
        
        # Generate a default URL based on item ID
        return f"internal://knowledge-item/{item['id']}"
    
    async def _create_quality_assessments(self, dry_run: bool, batch_size: int):
        """Create initial quality assessments for migrated items"""
        
        console.print("\n[bold yellow]⭐ Creating quality assessments...[/bold yellow]")
        
        # Find provenance records without quality assessments
        count_query = """
        SELECT COUNT(*)
        FROM knowledge_provenance kp
        LEFT JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id
        WHERE kp.is_current_version = true AND ql.id IS NULL
        """
        
        total_items = await self.db_connection.fetchval(count_query)
        
        if total_items == 0:
            console.print("[green]✓[/green] All provenance records have quality assessments")
            return
        
        console.print(f"Found {total_items} provenance records without quality assessments")
        
        if dry_run:
            console.print("[cyan]→[/cyan] Would create quality assessments")
            return
        
        # Create automated quality assessments
        fetch_query = """
        SELECT kp.id, kp.knowledge_item_id, ki.quality_score, ki.content, ki.title
        FROM knowledge_provenance kp
        JOIN knowledge_items ki ON kp.knowledge_item_id = ki.id
        LEFT JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id
        WHERE kp.is_current_version = true AND ql.id IS NULL
        ORDER BY kp.created_at
        LIMIT $1 OFFSET $2
        """
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Creating quality assessments...", total=total_items)
            
            offset = 0
            created_count = 0
            
            while offset < total_items:
                batch = await self.db_connection.fetch(fetch_query, batch_size, offset)
                
                if not batch:
                    break
                
                for record in batch:
                    success = await self._create_quality_assessment(record)
                    if success:
                        created_count += 1
                    
                    progress.advance(task, 1)
                
                offset += batch_size
        
        console.print(f"[green]✓[/green] Created {created_count} quality assessments")
    
    async def _create_quality_assessment(self, record: Dict[str, Any]) -> bool:
        """Create quality assessment for a provenance record"""
        
        try:
            # Calculate quality scores based on existing knowledge item data
            overall_score = record['quality_score'] or 0.5
            
            # Derive component scores from overall score and content analysis
            content_length = len(record['content']) if record['content'] else 0
            title_length = len(record['title']) if record['title'] else 0
            
            accuracy_score = min(overall_score + 0.1, 1.0)  # Slightly higher than overall
            completeness_score = min(content_length / 1000, 1.0)  # Based on content length
            relevance_score = overall_score  # Same as overall
            freshness_score = overall_score * 0.8  # Slightly lower for legacy data
            
            insert_query = """
            INSERT INTO quality_lineage (
                knowledge_provenance_id, assessment_type, assessor_name, assessor_type,
                overall_quality_score, accuracy_score, completeness_score, 
                relevance_score, freshness_score, quality_criteria, 
                assessment_results, approval_status, assessed_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """
            
            await self.db_connection.execute(
                insert_query,
                record['id'],  # knowledge_provenance_id
                "automated",
                "provenance_migrator",
                "system",
                overall_score,
                accuracy_score,
                completeness_score,
                relevance_score,
                freshness_score,
                json.dumps({
                    "migration_assessment": True,
                    "content_length": content_length,
                    "title_length": title_length
                }),
                json.dumps({
                    "method": "automated_migration",
                    "confidence": "medium"
                }),
                "pending",
                datetime.now(timezone.utc)
            )
            
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to create quality assessment for {record['id']}: {e}")
            return False
    
    async def _create_migration_annotations(self, dry_run: bool):
        """Create internal annotations for migration tracking"""
        
        console.print("\n[bold yellow]📝 Creating migration annotations...[/bold yellow]")
        
        if dry_run:
            console.print("[cyan]→[/cyan] Would create migration tracking annotations")
            return
        
        # Create annotation for migration summary
        migration_summary_query = """
        SELECT 
            COUNT(*) as total_provenance,
            COUNT(CASE WHEN kp.validation_status = 'needs_review' THEN 1 END) as needs_review,
            COUNT(CASE WHEN ds.source_name = 'Legacy/Unknown' THEN 1 END) as legacy_items
        FROM knowledge_provenance kp
        JOIN data_sources ds ON kp.data_source_id = ds.id
        WHERE kp.is_current_version = true
        """
        
        summary = await self.db_connection.fetchrow(migration_summary_query)
        
        # Create system-level annotation
        annotation_content = f"""Migration Summary:
- Total provenance records: {summary['total_provenance']}
- Items needing review: {summary['needs_review']}
- Legacy/unknown source items: {summary['legacy_items']}

Next steps:
1. Review items with 'needs_review' validation status
2. Identify proper sources for legacy items
3. Update quality assessments as needed
4. Validate data transformation accuracy
        """
        
        insert_annotation_query = """
        INSERT INTO internal_annotations (
            target_type, target_id, annotation_type, title, content,
            created_by, priority, tags
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        # Use first project ID as target for system annotation
        project_query = "SELECT id FROM projects LIMIT 1"
        project_id = await self.db_connection.fetchval(project_query)
        
        if project_id:
            await self.db_connection.execute(
                insert_annotation_query,
                "project",
                project_id,
                "note",
                "Provenance Migration Completed",
                annotation_content,
                "provenance_migrator",
                "normal",
                json.dumps(["migration", "provenance", "system"])
            )
            
            console.print("[green]✓[/green] Created migration summary annotation")
    
    async def _generate_migration_report(self):
        """Generate comprehensive migration report"""
        
        console.print("\n[bold blue]📊 Migration Report[/bold blue]")
        console.print("=" * 50)
        
        # Overall statistics
        stats_query = """
        SELECT 
            COUNT(DISTINCT ki.id) as total_knowledge_items,
            COUNT(DISTINCT kp.id) as total_provenance_records,
            COUNT(DISTINCT ds.id) as total_data_sources,
            COUNT(DISTINCT ej.id) as total_extraction_jobs,
            COUNT(DISTINCT ql.id) as total_quality_assessments,
            COUNT(DISTINCT ia.id) as total_annotations
        FROM knowledge_items ki
        LEFT JOIN knowledge_provenance kp ON ki.id = kp.knowledge_item_id AND kp.is_current_version = true
        LEFT JOIN data_sources ds ON kp.data_source_id = ds.id
        LEFT JOIN extraction_jobs ej ON kp.extraction_job_id = ej.id
        LEFT JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id
        LEFT JOIN internal_annotations ia ON ia.target_type = 'knowledge_item' AND ia.target_id = ki.id
        """
        
        stats = await self.db_connection.fetchrow(stats_query)
        
        # Create summary table
        summary_table = Table(title="Migration Summary", show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="green", justify="right")
        
        summary_table.add_row("Knowledge Items", f"{stats['total_knowledge_items']:,}")
        summary_table.add_row("Provenance Records", f"{stats['total_provenance_records']:,}")
        summary_table.add_row("Data Sources", f"{stats['total_data_sources']:,}")
        summary_table.add_row("Extraction Jobs", f"{stats['total_extraction_jobs']:,}")
        summary_table.add_row("Quality Assessments", f"{stats['total_quality_assessments']:,}")
        summary_table.add_row("Internal Annotations", f"{stats['total_annotations']:,}")
        
        console.print(summary_table)
        
        # Source distribution
        source_query = """
        SELECT ds.source_name, COUNT(*) as item_count
        FROM knowledge_provenance kp
        JOIN data_sources ds ON kp.data_source_id = ds.id
        WHERE kp.is_current_version = true
        GROUP BY ds.source_name
        ORDER BY item_count DESC
        """
        
        source_stats = await self.db_connection.fetch(source_query)
        
        if source_stats:
            console.print("\n[bold yellow]📊 Items by Data Source[/bold yellow]")
            
            source_table = Table()
            source_table.add_column("Source", style="cyan")
            source_table.add_column("Items", style="green", justify="right")
            source_table.add_column("Percentage", style="blue", justify="right")
            
            total_items = sum(row['item_count'] for row in source_stats)
            
            for row in source_stats:
                percentage = (row['item_count'] / total_items) * 100 if total_items > 0 else 0
                source_table.add_row(
                    row['source_name'],
                    f"{row['item_count']:,}",
                    f"{percentage:.1f}%"
                )
            
            console.print(source_table)
        
        # Validation status distribution
        validation_query = """
        SELECT validation_status, COUNT(*) as count
        FROM knowledge_provenance
        WHERE is_current_version = true
        GROUP BY validation_status
        ORDER BY count DESC
        """
        
        validation_stats = await self.db_connection.fetch(validation_query)
        
        if validation_stats:
            console.print("\n[bold yellow]✅ Validation Status Distribution[/bold yellow]")
            
            validation_table = Table()
            validation_table.add_column("Status", style="cyan")
            validation_table.add_column("Count", style="green", justify="right")
            
            for row in validation_stats:
                status_color = "green" if row['validation_status'] == 'passed' else "yellow" if row['validation_status'] == 'pending' else "red"
                validation_table.add_row(
                    f"[{status_color}]{row['validation_status']}[/{status_color}]",
                    f"{row['count']:,}"
                )
            
            console.print(validation_table)
        
        # Next steps recommendations
        recommendations_panel = Panel(
            "1. Review items with 'needs_review' validation status\n"
            "2. Update legacy/unknown source items with proper attribution\n"
            "3. Run quality assessment validation on migrated data\n"
            "4. Configure automated extraction jobs for active sources\n"
            "5. Set up monitoring for data quality and source reliability\n"
            "6. Train team on using provenance APIs and debugging tools",
            title="Next Steps",
            border_style="green"
        )
        console.print("\n")
        console.print(recommendations_panel)

async def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(description="BETTY Provenance Migration Tool")
    parser.add_argument("--db-host", default="localhost", help="Database host")
    parser.add_argument("--db-port", default="5432", help="Database port")
    parser.add_argument("--db-name", default="betty_memory", help="Database name")
    parser.add_argument("--db-user", default="postgres", help="Database user")
    parser.add_argument("--db-password", help="Database password (or set PGPASSWORD env var)")
    
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    
    args = parser.parse_args()
    
    # Database configuration
    db_config = {
        "host": args.db_host,
        "port": args.db_port,
        "database": args.db_name,
        "user": args.db_user,
        "password": args.db_password
    }
    
    migrator = ProvenanceMigrator(db_config)
    
    try:
        await migrator.connect()
        await migrator.migrate_all(dry_run=args.dry_run, batch_size=args.batch_size)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Migration cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Migration failed: {e}[/red]")
        raise
    finally:
        await migrator.disconnect()

if __name__ == "__main__":
    asyncio.run(main())