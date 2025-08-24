#!/usr/bin/env python3
"""
ABOUTME: Comprehensive reporting and debugging tools for BETTY data provenance
ABOUTME: Command-line tools for analyzing data quality, source reliability, and debugging extraction issues
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
from pathlib import Path

import asyncpg
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich.tree import Tree
from rich import box

console = Console()

class ProvenanceReporter:
    """Comprehensive reporting tool for data provenance analysis"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.db_connection = None
    
    async def connect(self):
        """Establish database connection"""
        try:
            self.db_connection = await asyncpg.connect(**self.db_config)
            console.print("[green]✓[/green] Connected to BETTY database")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to connect to database: {e}")
            sys.exit(1)
    
    async def disconnect(self):
        """Close database connection"""
        if self.db_connection:
            await self.db_connection.close()
            console.print("[green]✓[/green] Database connection closed")
    
    async def generate_source_reliability_report(
        self, 
        output_format: str = "table",
        include_inactive: bool = False,
        export_file: Optional[str] = None
    ):
        """Generate comprehensive source reliability report"""
        
        console.print("\n[bold blue]BETTY Data Source Reliability Report[/bold blue]")
        console.print("=" * 50)
        
        query = """
        SELECT 
            ds.source_name,
            ds.source_type,
            ds.reliability_score,
            ds.is_active,
            ds.consecutive_failures,
            ds.last_successful_extraction,
            COUNT(DISTINCT ej.id) as total_jobs,
            COUNT(DISTINCT CASE WHEN ej.status = 'completed' THEN ej.id END) as successful_jobs,
            COUNT(DISTINCT CASE WHEN ej.status = 'failed' THEN ej.id END) as failed_jobs,
            AVG(ej.data_quality_score) as avg_data_quality,
            COUNT(DISTINCT kp.knowledge_item_id) as total_knowledge_items,
            AVG(ql.overall_quality_score) as avg_quality_score,
            MAX(ej.completed_at) as last_extraction
        FROM data_sources ds
        LEFT JOIN extraction_jobs ej ON ds.id = ej.data_source_id
        LEFT JOIN knowledge_provenance kp ON ej.id = kp.extraction_job_id AND kp.is_current_version = true
        LEFT JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id
        """
        
        if not include_inactive:
            query += " WHERE ds.is_active = true"
        
        query += """
        GROUP BY ds.id, ds.source_name, ds.source_type, ds.reliability_score, ds.is_active, ds.consecutive_failures, ds.last_successful_extraction
        ORDER BY ds.reliability_score DESC, total_knowledge_items DESC
        """
        
        rows = await self.db_connection.fetch(query)
        
        if output_format == "table":
            await self._display_source_reliability_table(rows)
        elif output_format == "json":
            await self._export_source_reliability_json(rows, export_file)
        elif output_format == "detailed":
            await self._display_detailed_source_analysis(rows)
    
    async def _display_source_reliability_table(self, rows):
        """Display source reliability in table format"""
        
        table = Table(title="Data Source Reliability Analysis", box=box.ROUNDED)
        table.add_column("Source", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Reliability", style="green", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Success Rate", style="blue", justify="center")
        table.add_column("Knowledge Items", style="yellow", justify="center")
        table.add_column("Quality Score", style="green", justify="center")
        table.add_column("Last Extraction", style="dim")
        
        for row in rows:
            success_rate = 0.0
            if row['total_jobs'] and row['total_jobs'] > 0:
                success_rate = (row['successful_jobs'] or 0) / row['total_jobs']
            
            status = "🟢 Active" if row['is_active'] else "🔴 Inactive"
            if row['consecutive_failures'] > 3:
                status = "⚠️  Issues"
            
            reliability_color = "green" if row['reliability_score'] >= 0.8 else "yellow" if row['reliability_score'] >= 0.6 else "red"
            
            table.add_row(
                row['source_name'],
                row['source_type'],
                f"[{reliability_color}]{row['reliability_score']:.2f}[/{reliability_color}]",
                status,
                f"{success_rate:.1%}",
                str(row['total_knowledge_items'] or 0),
                f"{row['avg_quality_score']:.2f}" if row['avg_quality_score'] else "N/A",
                row['last_extraction'].strftime('%Y-%m-%d') if row['last_extraction'] else "Never"
            )
        
        console.print("\n")
        console.print(table)
        
        # Summary statistics
        active_sources = len([r for r in rows if r['is_active']])
        total_sources = len(rows)
        avg_reliability = sum(r['reliability_score'] for r in rows) / total_sources if total_sources > 0 else 0
        
        summary_panel = Panel(
            f"📊 [bold]Summary[/bold]\n"
            f"Total Sources: {total_sources}\n"
            f"Active Sources: {active_sources}\n"
            f"Inactive Sources: {total_sources - active_sources}\n"
            f"Average Reliability: {avg_reliability:.2f}",
            title="Source Summary",
            border_style="blue"
        )
        console.print("\n")
        console.print(summary_panel)
    
    async def _display_detailed_source_analysis(self, rows):
        """Display detailed analysis for each source"""
        
        for row in rows:
            # Get additional details for this source
            source_details = await self._get_source_detailed_metrics(row['source_name'])
            
            console.print(f"\n[bold cyan]📊 {row['source_name']} Analysis[/bold cyan]")
            console.print("=" * 40)
            
            # Basic info
            info_table = Table(show_header=False, box=box.SIMPLE)
            info_table.add_column("Metric", style="cyan")
            info_table.add_column("Value", style="white")
            
            info_table.add_row("Source Type", row['source_type'])
            info_table.add_row("Reliability Score", f"{row['reliability_score']:.2f}")
            info_table.add_row("Status", "Active" if row['is_active'] else "Inactive")
            info_table.add_row("Consecutive Failures", str(row['consecutive_failures']))
            info_table.add_row("Total Extraction Jobs", str(row['total_jobs'] or 0))
            info_table.add_row("Success Rate", f"{(row['successful_jobs'] or 0) / max(row['total_jobs'] or 1, 1):.1%}")
            info_table.add_row("Knowledge Items", str(row['total_knowledge_items'] or 0))
            info_table.add_row("Average Quality", f"{row['avg_quality_score']:.2f}" if row['avg_quality_score'] else "N/A")
            
            console.print(info_table)
            
            # Recent activity
            if source_details['recent_jobs']:
                console.print("\n[bold yellow]Recent Activity[/bold yellow]")
                activity_table = Table(box=box.SIMPLE)
                activity_table.add_column("Date", style="dim")
                activity_table.add_column("Status")
                activity_table.add_column("Items")
                activity_table.add_column("Quality")
                
                for job in source_details['recent_jobs'][:5]:
                    status_color = "green" if job['status'] == 'completed' else "red"
                    activity_table.add_row(
                        job['started_at'].strftime('%Y-%m-%d %H:%M'),
                        f"[{status_color}]{job['status']}[/{status_color}]",
                        f"{job['items_successful']}/{job['items_processed']}",
                        f"{job['data_quality_score']:.2f}" if job['data_quality_score'] else "N/A"
                    )
                
                console.print(activity_table)
            
            # Issues and recommendations
            issues = await self._analyze_source_issues(row)
            if issues:
                console.print("\n[bold red]⚠️  Issues Found[/bold red]")
                for issue in issues:
                    console.print(f"• {issue}")
            
            recommendations = await self._generate_source_recommendations(row, source_details)
            if recommendations:
                console.print("\n[bold green]💡 Recommendations[/bold green]")
                for rec in recommendations:
                    console.print(f"• {rec}")
            
            console.print("\n" + "─" * 60)
    
    async def _get_source_detailed_metrics(self, source_name: str) -> Dict[str, Any]:
        """Get detailed metrics for a specific source"""
        
        query = """
        SELECT 
            ej.started_at,
            ej.status,
            ej.items_processed,
            ej.items_successful,
            ej.data_quality_score
        FROM extraction_jobs ej
        JOIN data_sources ds ON ej.data_source_id = ds.id
        WHERE ds.source_name = $1
        ORDER BY ej.started_at DESC
        LIMIT 10
        """
        
        recent_jobs = await self.db_connection.fetch(query, source_name)
        
        return {
            'recent_jobs': [dict(job) for job in recent_jobs]
        }
    
    async def _analyze_source_issues(self, source_data: Dict) -> List[str]:
        """Analyze potential issues with a data source"""
        issues = []
        
        if source_data['consecutive_failures'] > 3:
            issues.append(f"High consecutive failures ({source_data['consecutive_failures']})")
        
        if source_data['reliability_score'] < 0.6:
            issues.append(f"Low reliability score ({source_data['reliability_score']:.2f})")
        
        success_rate = 0.0
        if source_data['total_jobs']:
            success_rate = (source_data['successful_jobs'] or 0) / source_data['total_jobs']
        
        if success_rate < 0.8 and source_data['total_jobs'] > 5:
            issues.append(f"Low success rate ({success_rate:.1%})")
        
        if source_data['avg_quality_score'] and source_data['avg_quality_score'] < 0.6:
            issues.append(f"Low average quality score ({source_data['avg_quality_score']:.2f})")
        
        if source_data['last_successful_extraction']:
            days_since_extraction = (datetime.now(timezone.utc) - source_data['last_successful_extraction']).days
            if days_since_extraction > 30:
                issues.append(f"No successful extractions in {days_since_extraction} days")
        
        return issues
    
    async def _generate_source_recommendations(self, source_data: Dict, details: Dict) -> List[str]:
        """Generate recommendations for improving source reliability"""
        recommendations = []
        
        if source_data['consecutive_failures'] > 3:
            recommendations.append("Check source authentication and access permissions")
            recommendations.append("Verify source URL and endpoint availability")
        
        if source_data['reliability_score'] < 0.7:
            recommendations.append("Review and update reliability score based on recent performance")
        
        if not details['recent_jobs']:
            recommendations.append("Schedule regular extraction jobs for this source")
        
        success_rate = 0.0
        if source_data['total_jobs']:
            success_rate = (source_data['successful_jobs'] or 0) / source_data['total_jobs']
        
        if success_rate < 0.8:
            recommendations.append("Investigate extraction job failures and improve error handling")
        
        if source_data['avg_quality_score'] and source_data['avg_quality_score'] < 0.7:
            recommendations.append("Review data validation rules and quality standards")
            recommendations.append("Consider additional processing steps to improve data quality")
        
        return recommendations
    
    async def generate_extraction_performance_report(
        self, 
        days: int = 30,
        source_name: Optional[str] = None,
        output_format: str = "table"
    ):
        """Generate extraction performance report"""
        
        console.print(f"\n[bold blue]BETTY Extraction Performance Report[/bold blue]")
        console.print(f"Analysis Period: Last {days} days")
        console.print("=" * 50)
        
        date_cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        conditions = ["ej.started_at >= $1"]
        params = [date_cutoff]
        param_count = 1
        
        if source_name:
            param_count += 1
            conditions.append(f"ds.source_name = ${param_count}")
            params.append(source_name)
        
        # Daily performance query
        daily_query = f"""
        SELECT 
            DATE(ej.started_at) as extraction_date,
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN ej.status = 'completed' THEN 1 END) as successful_jobs,
            COUNT(CASE WHEN ej.status = 'failed' THEN 1 END) as failed_jobs,
            SUM(ej.items_successful) as total_items_extracted,
            SUM(ej.items_failed) as total_items_failed,
            AVG(EXTRACT(EPOCH FROM (ej.completed_at - ej.started_at))) as avg_duration_seconds,
            AVG(ej.data_quality_score) as avg_quality_score
        FROM extraction_jobs ej
        JOIN data_sources ds ON ej.data_source_id = ds.id
        WHERE {' AND '.join(conditions)}
        GROUP BY DATE(ej.started_at)
        ORDER BY extraction_date DESC
        LIMIT 30
        """
        
        daily_stats = await self.db_connection.fetch(daily_query, *params)
        
        # Overall statistics
        overall_query = f"""
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN ej.status = 'completed' THEN 1 END) as successful_jobs,
            COUNT(CASE WHEN ej.status = 'failed' THEN 1 END) as failed_jobs,
            SUM(ej.items_successful) as total_items_extracted,
            SUM(ej.items_failed) as total_items_failed,
            AVG(EXTRACT(EPOCH FROM (ej.completed_at - ej.started_at))) as avg_duration_seconds,
            AVG(ej.data_quality_score) as avg_quality_score,
            COUNT(DISTINCT ds.source_name) as unique_sources
        FROM extraction_jobs ej
        JOIN data_sources ds ON ej.data_source_id = ds.id
        WHERE {' AND '.join(conditions)}
        """
        
        overall_row = await self.db_connection.fetchrow(overall_query, *params)
        
        await self._display_performance_summary(overall_row)
        await self._display_daily_performance(daily_stats)
        
        # Source-wise performance
        if not source_name:
            await self._display_source_performance_breakdown(date_cutoff)
    
    async def _display_performance_summary(self, overall_stats):
        """Display overall performance summary"""
        
        success_rate = 0.0
        if overall_stats['total_jobs']:
            success_rate = overall_stats['successful_jobs'] / overall_stats['total_jobs']
        
        item_success_rate = 0.0
        total_items = (overall_stats['total_items_extracted'] or 0) + (overall_stats['total_items_failed'] or 0)
        if total_items > 0:
            item_success_rate = (overall_stats['total_items_extracted'] or 0) / total_items
        
        avg_duration = overall_stats['avg_duration_seconds'] or 0
        
        summary_panel = Panel(
            f"🔄 [bold]Extraction Jobs[/bold]: {overall_stats['total_jobs'] or 0} total, {overall_stats['successful_jobs'] or 0} successful\n"
            f"📊 [bold]Success Rate[/bold]: {success_rate:.1%} (jobs), {item_success_rate:.1%} (items)\n"
            f"📦 [bold]Items Processed[/bold]: {(overall_stats['total_items_extracted'] or 0):,} successful, {(overall_stats['total_items_failed'] or 0):,} failed\n"
            f"⏱️  [bold]Average Duration[/bold]: {avg_duration:.1f} seconds\n"
            f"⭐ [bold]Average Quality[/bold]: {overall_stats['avg_quality_score']:.2f}" if overall_stats['avg_quality_score'] else "⭐ [bold]Average Quality[/bold]: N/A\n"
            f"🎯 [bold]Data Sources[/bold]: {overall_stats['unique_sources'] or 0} sources active",
            title="Performance Summary",
            border_style="green"
        )
        console.print("\n")
        console.print(summary_panel)
    
    async def _display_daily_performance(self, daily_stats):
        """Display daily performance breakdown"""
        
        console.print("\n[bold yellow]📅 Daily Performance Breakdown[/bold yellow]")
        
        table = Table(box=box.ROUNDED)
        table.add_column("Date", style="cyan")
        table.add_column("Jobs", justify="center")
        table.add_column("Success Rate", style="green", justify="center")
        table.add_column("Items", justify="center")
        table.add_column("Quality", style="blue", justify="center")
        table.add_column("Avg Duration", justify="center")
        
        for row in daily_stats:
            success_rate = 0.0
            if row['total_jobs']:
                success_rate = row['successful_jobs'] / row['total_jobs']
            
            duration_str = f"{row['avg_duration_seconds']:.0f}s" if row['avg_duration_seconds'] else "N/A"
            quality_str = f"{row['avg_quality_score']:.2f}" if row['avg_quality_score'] else "N/A"
            
            success_color = "green" if success_rate >= 0.9 else "yellow" if success_rate >= 0.7 else "red"
            
            table.add_row(
                row['extraction_date'].strftime('%Y-%m-%d'),
                f"{row['total_jobs']}",
                f"[{success_color}]{success_rate:.1%}[/{success_color}]",
                f"{row['total_items_extracted'] or 0}",
                quality_str,
                duration_str
            )
        
        console.print(table)
    
    async def _display_source_performance_breakdown(self, date_cutoff):
        """Display performance breakdown by source"""
        
        console.print("\n[bold yellow]📊 Performance by Source[/bold yellow]")
        
        query = """
        SELECT 
            ds.source_name,
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN ej.status = 'completed' THEN 1 END) as successful_jobs,
            SUM(ej.items_successful) as total_items,
            AVG(ej.data_quality_score) as avg_quality
        FROM extraction_jobs ej
        JOIN data_sources ds ON ej.data_source_id = ds.id
        WHERE ej.started_at >= $1
        GROUP BY ds.source_name
        ORDER BY total_jobs DESC
        """
        
        source_stats = await self.db_connection.fetch(query, date_cutoff)
        
        table = Table(box=box.ROUNDED)
        table.add_column("Source", style="cyan")
        table.add_column("Jobs", justify="center")
        table.add_column("Success Rate", style="green", justify="center")
        table.add_column("Items", justify="center")
        table.add_column("Quality", style="blue", justify="center")
        
        for row in source_stats:
            success_rate = 0.0
            if row['total_jobs']:
                success_rate = row['successful_jobs'] / row['total_jobs']
            
            success_color = "green" if success_rate >= 0.9 else "yellow" if success_rate >= 0.7 else "red"
            
            table.add_row(
                row['source_name'],
                str(row['total_jobs']),
                f"[{success_color}]{success_rate:.1%}[/{success_color}]",
                f"{row['total_items'] or 0:,}",
                f"{row['avg_quality']:.2f}" if row['avg_quality'] else "N/A"
            )
        
        console.print(table)
    
    async def debug_knowledge_item(self, knowledge_item_id: UUID):
        """Debug a specific knowledge item's provenance"""
        
        console.print(f"\n[bold blue]🔍 Debugging Knowledge Item: {knowledge_item_id}[/bold blue]")
        console.print("=" * 70)
        
        # Get knowledge item details
        ki_query = """
        SELECT ki.*, p.name as project_name
        FROM knowledge_items ki
        LEFT JOIN projects p ON ki.project_id = p.id
        WHERE ki.id = $1
        """
        
        ki_row = await self.db_connection.fetchrow(ki_query, knowledge_item_id)
        if not ki_row:
            console.print("[red]❌ Knowledge item not found[/red]")
            return
        
        # Display knowledge item info
        ki_panel = Panel(
            f"📝 [bold]Title[/bold]: {ki_row['title']}\n"
            f"🏷️  [bold]Type[/bold]: {ki_row['knowledge_type']}\n"
            f"🏢 [bold]Project[/bold]: {ki_row['project_name'] or 'Unknown'}\n"
            f"📊 [bold]Quality Score[/bold]: {ki_row['quality_score']}\n"
            f"🔄 [bold]Usage Count[/bold]: {ki_row['usage_count']}\n"
            f"📅 [bold]Created[/bold]: {ki_row['created_at'].strftime('%Y-%m-%d %H:%M:%S')}",
            title="Knowledge Item Details",
            border_style="cyan"
        )
        console.print(ki_panel)
        
        # Get provenance information
        provenance_query = """
        SELECT kp.*, ds.source_name, ds.source_type, ds.reliability_score,
               ej.job_name, ej.extraction_method, ej.status as job_status
        FROM knowledge_provenance kp
        JOIN data_sources ds ON kp.data_source_id = ds.id
        JOIN extraction_jobs ej ON kp.extraction_job_id = ej.id
        WHERE kp.knowledge_item_id = $1 AND kp.is_current_version = true
        """
        
        prov_row = await self.db_connection.fetchrow(provenance_query, knowledge_item_id)
        if prov_row:
            await self._display_provenance_debug(prov_row)
            await self._display_transformation_debug(prov_row['id'])
            await self._display_quality_debug(prov_row['id'])
            await self._display_annotations_debug(knowledge_item_id)
            await self._display_update_history_debug(knowledge_item_id)
        else:
            console.print("\n[yellow]⚠️  No provenance information found[/yellow]")
        
        # Check for potential issues
        await self._analyze_knowledge_item_issues(ki_row, prov_row)
    
    async def _display_provenance_debug(self, prov_data):
        """Display provenance debugging information"""
        
        console.print("\n[bold green]📊 Provenance Information[/bold green]")
        
        tree = Tree("🌳 Provenance Tree")
        
        source_branch = tree.add(f"🔗 Source: [cyan]{prov_data['source_name']}[/cyan]")
        source_branch.add(f"Type: {prov_data['source_type']}")
        source_branch.add(f"Reliability: {prov_data['reliability_score']:.2f}")
        source_branch.add(f"Original URL: {prov_data['original_source_url']}")
        
        extraction_branch = tree.add(f"⚙️  Extraction: [magenta]{prov_data['job_name']}[/magenta]")
        extraction_branch.add(f"Method: {prov_data['extraction_method']}")
        extraction_branch.add(f"Status: {prov_data['job_status']}")
        extraction_branch.add(f"Extracted: {prov_data['extraction_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        validation_branch = tree.add(f"✅ Validation: [blue]{prov_data['validation_status']}[/blue]")
        if prov_data['validated_by']:
            validation_branch.add(f"Validated by: {prov_data['validated_by']}")
        if prov_data['validated_at']:
            validation_branch.add(f"Validated at: {prov_data['validated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        console.print(tree)
    
    async def _display_transformation_debug(self, provenance_id: UUID):
        """Display transformation step debugging"""
        
        query = """
        SELECT * FROM transformation_steps
        WHERE knowledge_provenance_id = $1
        ORDER BY step_order
        """
        
        steps = await self.db_connection.fetch(query, provenance_id)
        
        if steps:
            console.print("\n[bold yellow]🔄 Transformation Steps[/bold yellow]")
            
            table = Table(box=box.SIMPLE)
            table.add_column("Step", style="cyan")
            table.add_column("Processor", style="magenta")
            table.add_column("Status")
            table.add_column("Duration", justify="center")
            table.add_column("Quality Impact", justify="center")
            
            for step in steps:
                status_color = "green" if step['status'] == 'completed' else "red"
                duration_str = f"{step['execution_time_ms']}ms" if step['execution_time_ms'] else "N/A"
                quality_str = f"{step['quality_impact_score']:+.2f}" if step['quality_impact_score'] else "N/A"
                
                table.add_row(
                    f"{step['step_order']}. {step['step_name']}",
                    f"{step['processor_name']} v{step['processor_version']}",
                    f"[{status_color}]{step['status']}[/{status_color}]",
                    duration_str,
                    quality_str
                )
            
            console.print(table)
        else:
            console.print("\n[dim]No transformation steps found[/dim]")
    
    async def _display_quality_debug(self, provenance_id: UUID):
        """Display quality assessment debugging"""
        
        query = """
        SELECT * FROM quality_lineage
        WHERE knowledge_provenance_id = $1
        ORDER BY assessed_at DESC
        """
        
        quality_records = await self.db_connection.fetch(query, provenance_id)
        
        if quality_records:
            console.print("\n[bold blue]⭐ Quality Assessments[/bold blue]")
            
            for record in quality_records:
                quality_panel = Panel(
                    f"📊 [bold]Overall Score[/bold]: {record['overall_quality_score']:.2f}\n"
                    f"🎯 [bold]Accuracy[/bold]: {record['accuracy_score']:.2f}" if record['accuracy_score'] else "🎯 [bold]Accuracy[/bold]: N/A\n"
                    f"📝 [bold]Completeness[/bold]: {record['completeness_score']:.2f}" if record['completeness_score'] else "📝 [bold]Completeness[/bold]: N/A\n"
                    f"🔍 [bold]Relevance[/bold]: {record['relevance_score']:.2f}" if record['relevance_score'] else "🔍 [bold]Relevance[/bold]: N/A\n"
                    f"🕐 [bold]Freshness[/bold]: {record['freshness_score']:.2f}" if record['freshness_score'] else "🕐 [bold]Freshness[/bold]: N/A\n"
                    f"👤 [bold]Assessor[/bold]: {record['assessor_name']} ({record['assessor_type']})\n"
                    f"✅ [bold]Status[/bold]: {record['approval_status']}",
                    title=f"Assessment: {record['assessment_type']}",
                    border_style="blue"
                )
                console.print(quality_panel)
        else:
            console.print("\n[dim]No quality assessments found[/dim]")
    
    async def _display_annotations_debug(self, knowledge_item_id: UUID):
        """Display internal annotations debugging"""
        
        query = """
        SELECT * FROM internal_annotations
        WHERE target_type = 'knowledge_item' AND target_id = $1
        ORDER BY created_at DESC
        """
        
        annotations = await self.db_connection.fetch(query, knowledge_item_id)
        
        if annotations:
            console.print("\n[bold red]📝 Internal Annotations[/bold red]")
            
            for annotation in annotations:
                status_color = "green" if annotation['status'] == 'resolved' else "yellow" if annotation['status'] == 'active' else "dim"
                priority_emoji = "🔴" if annotation['priority'] == 'critical' else "🟡" if annotation['priority'] == 'high' else "🔵"
                
                annotation_panel = Panel(
                    f"{priority_emoji} [bold]{annotation['title'] or 'No Title'}[/bold]\n"
                    f"📝 {annotation['content']}\n"
                    f"👤 Created by: {annotation['created_by']}\n"
                    f"📅 Created: {annotation['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🏷️  Tags: {', '.join(annotation['tags']) if annotation['tags'] else 'None'}",
                    title=f"[{status_color}]{annotation['annotation_type']} ({annotation['status']})[/{status_color}]",
                    border_style=status_color
                )
                console.print(annotation_panel)
        else:
            console.print("\n[dim]No internal annotations found[/dim]")
    
    async def _display_update_history_debug(self, knowledge_item_id: UUID):
        """Display update history debugging"""
        
        query = """
        SELECT * FROM knowledge_update_history
        WHERE knowledge_item_id = $1
        ORDER BY updated_at DESC
        LIMIT 5
        """
        
        updates = await self.db_connection.fetch(query, knowledge_item_id)
        
        if updates:
            console.print("\n[bold magenta]📈 Recent Update History[/bold magenta]")
            
            table = Table(box=box.SIMPLE)
            table.add_column("Date", style="dim")
            table.add_column("Type", style="cyan")
            table.add_column("Updated By", style="magenta")
            table.add_column("Impact", justify="center")
            table.add_column("Fields Changed", justify="center")
            
            for update in updates:
                impact_color = "red" if update['impact_level'] == 'breaking' else "yellow" if update['impact_level'] == 'high' else "green"
                
                table.add_row(
                    update['updated_at'].strftime('%Y-%m-%d %H:%M'),
                    update['update_type'],
                    update['updated_by'],
                    f"[{impact_color}]{update['impact_level']}[/{impact_color}]",
                    str(len(update['fields_changed']) if update['fields_changed'] else 0)
                )
            
            console.print(table)
        else:
            console.print("\n[dim]No update history found[/dim]")
    
    async def _analyze_knowledge_item_issues(self, ki_data, prov_data):
        """Analyze potential issues with a knowledge item"""
        
        issues = []
        recommendations = []
        
        # Quality issues
        if ki_data['quality_score'] < 0.6:
            issues.append(f"Low quality score: {ki_data['quality_score']:.2f}")
            recommendations.append("Review and improve content quality")
        
        # Usage issues
        if ki_data['usage_count'] == 0 and ki_data['created_at'] < datetime.now(timezone.utc) - timedelta(days=30):
            issues.append("Knowledge item has never been used")
            recommendations.append("Consider improving discoverability or relevance")
        
        # Provenance issues
        if prov_data:
            if prov_data['validation_status'] in ['failed', 'needs_review']:
                issues.append(f"Validation status: {prov_data['validation_status']}")
                recommendations.append("Review and fix validation issues")
            
            if prov_data['reliability_score'] < 0.7:
                issues.append(f"Source reliability low: {prov_data['reliability_score']:.2f}")
                recommendations.append("Consider updating from more reliable source")
        
        if issues or recommendations:
            console.print("\n[bold red]⚠️  Issues Analysis[/bold red]")
            
            if issues:
                issues_text = "\n".join([f"• {issue}" for issue in issues])
                console.print(Panel(issues_text, title="Issues Found", border_style="red"))
            
            if recommendations:
                rec_text = "\n".join([f"• {rec}" for rec in recommendations])
                console.print(Panel(rec_text, title="Recommendations", border_style="green"))
        else:
            console.print("\n[green]✅ No issues found[/green]")
    
    async def validate_provenance_integrity(self):
        """Validate overall provenance data integrity"""
        
        console.print("\n[bold blue]🔍 BETTY Provenance Integrity Check[/bold blue]")
        console.print("=" * 50)
        
        issues_found = 0
        
        # Check 1: Knowledge items without provenance
        orphan_query = """
        SELECT COUNT(*)
        FROM knowledge_items ki
        LEFT JOIN knowledge_provenance kp ON ki.id = kp.knowledge_item_id AND kp.is_current_version = true
        WHERE kp.id IS NULL
        """
        
        orphan_count = await self.db_connection.fetchval(orphan_query)
        if orphan_count > 0:
            console.print(f"[red]❌ Found {orphan_count} knowledge items without provenance[/red]")
            issues_found += orphan_count
        else:
            console.print("[green]✅ All knowledge items have provenance records[/green]")
        
        # Check 2: Invalid extraction job references
        invalid_job_query = """
        SELECT COUNT(*)
        FROM knowledge_provenance kp
        LEFT JOIN extraction_jobs ej ON kp.extraction_job_id = ej.id
        WHERE ej.id IS NULL
        """
        
        invalid_job_count = await self.db_connection.fetchval(invalid_job_query)
        if invalid_job_count > 0:
            console.print(f"[red]❌ Found {invalid_job_count} provenance records with invalid extraction jobs[/red]")
            issues_found += invalid_job_count
        else:
            console.print("[green]✅ All provenance records have valid extraction jobs[/green]")
        
        # Check 3: Multiple current versions
        multiple_current_query = """
        SELECT knowledge_item_id, COUNT(*)
        FROM knowledge_provenance
        WHERE is_current_version = true
        GROUP BY knowledge_item_id
        HAVING COUNT(*) > 1
        """
        
        multiple_current = await self.db_connection.fetch(multiple_current_query)
        if multiple_current:
            console.print(f"[red]❌ Found {len(multiple_current)} knowledge items with multiple current provenance versions[/red]")
            issues_found += len(multiple_current)
        else:
            console.print("[green]✅ No duplicate current provenance versions found[/green]")
        
        # Check 4: Transformation steps without provenance
        orphan_steps_query = """
        SELECT COUNT(*)
        FROM transformation_steps ts
        LEFT JOIN knowledge_provenance kp ON ts.knowledge_provenance_id = kp.id
        WHERE kp.id IS NULL
        """
        
        orphan_steps = await self.db_connection.fetchval(orphan_steps_query)
        if orphan_steps > 0:
            console.print(f"[red]❌ Found {orphan_steps} orphaned transformation steps[/red]")
            issues_found += orphan_steps
        else:
            console.print("[green]✅ All transformation steps are properly linked[/green]")
        
        # Summary
        if issues_found == 0:
            console.print("\n[bold green]🎉 Provenance integrity check passed![/bold green]")
        else:
            console.print(f"\n[bold red]⚠️  Found {issues_found} integrity issues that need attention[/bold red]")
        
        return issues_found

async def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(description="BETTY Provenance Reporting and Debugging Tool")
    parser.add_argument("--db-host", default="localhost", help="Database host")
    parser.add_argument("--db-port", default="5432", help="Database port")
    parser.add_argument("--db-name", default="betty_memory", help="Database name")
    parser.add_argument("--db-user", default="postgres", help="Database user")
    parser.add_argument("--db-password", help="Database password (or set PGPASSWORD env var)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Source reliability report
    reliability_parser = subparsers.add_parser("source-reliability", help="Generate source reliability report")
    reliability_parser.add_argument("--format", choices=["table", "json", "detailed"], default="table")
    reliability_parser.add_argument("--include-inactive", action="store_true", help="Include inactive sources")
    reliability_parser.add_argument("--export", help="Export to file")
    
    # Extraction performance report
    performance_parser = subparsers.add_parser("extraction-performance", help="Generate extraction performance report")
    performance_parser.add_argument("--days", type=int, default=30, help="Analysis period in days")
    performance_parser.add_argument("--source", help="Filter by source name")
    performance_parser.add_argument("--format", choices=["table", "json"], default="table")
    
    # Debug knowledge item
    debug_parser = subparsers.add_parser("debug", help="Debug specific knowledge item")
    debug_parser.add_argument("knowledge_item_id", help="Knowledge item UUID to debug")
    
    # Integrity check
    subparsers.add_parser("integrity-check", help="Validate provenance data integrity")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Database configuration
    db_config = {
        "host": args.db_host,
        "port": args.db_port,
        "database": args.db_name,
        "user": args.db_user,
        "password": args.db_password
    }
    
    reporter = ProvenanceReporter(db_config)
    
    try:
        await reporter.connect()
        
        if args.command == "source-reliability":
            await reporter.generate_source_reliability_report(
                output_format=args.format,
                include_inactive=args.include_inactive,
                export_file=args.export
            )
        
        elif args.command == "extraction-performance":
            await reporter.generate_extraction_performance_report(
                days=args.days,
                source_name=args.source,
                output_format=args.format
            )
        
        elif args.command == "debug":
            try:
                knowledge_item_id = UUID(args.knowledge_item_id)
                await reporter.debug_knowledge_item(knowledge_item_id)
            except ValueError:
                console.print("[red]❌ Invalid knowledge item UUID format[/red]")
        
        elif args.command == "integrity-check":
            issues_count = await reporter.validate_provenance_integrity()
            if issues_count > 0:
                sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)
    finally:
        await reporter.disconnect()

if __name__ == "__main__":
    asyncio.run(main())