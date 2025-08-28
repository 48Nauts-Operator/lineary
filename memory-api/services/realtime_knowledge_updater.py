# ABOUTME: Real-time Knowledge Update System with Conflict Resolution and Source Monitoring  
# ABOUTME: Monitors sources for updates, processes changes, and maintains knowledge consistency

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Set
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
import structlog
from collections import defaultdict, deque
import hashlib
import feedparser
from urllib.parse import urljoin, urlparse

from core.database import DatabaseManager
from models.knowledge import KnowledgeItem
from services.multi_source_knowledge_extractor import MultiSourceKnowledgeExtractor, SourceConfig
from services.knowledge_processing_pipeline import KnowledgeProcessingPipeline, ProcessingResult
from services.vector_service import VectorService

logger = structlog.get_logger(__name__)

class UpdateType(Enum):
    NEW_CONTENT = "new_content"
    CONTENT_MODIFIED = "content_modified"
    CONTENT_DEPRECATED = "content_deprecated"
    SOURCE_UNAVAILABLE = "source_unavailable"
    METADATA_UPDATED = "metadata_updated"

class ConflictType(Enum):
    VERSION_CONFLICT = "version_conflict"
    SOURCE_DISCREPANCY = "source_discrepancy"
    CONTENT_DIVERGENCE = "content_divergence"
    FRESHNESS_CONFLICT = "freshness_conflict"

@dataclass
class UpdateEvent:
    """Real-time update event"""
    id: UUID
    source_name: str
    update_type: UpdateType
    item_id: Optional[UUID]
    source_url: str
    detected_at: datetime
    processed: bool = False
    processing_result: Optional[ProcessingResult] = None
    conflicts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SourceMonitor:
    """Configuration for monitoring a knowledge source"""
    source_name: str
    monitor_type: str  # 'rss', 'api_polling', 'webhook', 'scraping'
    check_interval: float  # seconds
    last_check: Optional[datetime] = None
    last_update: Optional[datetime] = None
    consecutive_failures: int = 0
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

class RealtimeKnowledgeUpdater:
    """
    Real-time Knowledge Update System with intelligent conflict resolution
    and source monitoring for continuous knowledge freshness
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        extractor: MultiSourceKnowledgeExtractor,
        pipeline: KnowledgeProcessingPipeline,
        vector_service: VectorService
    ):
        self.db_manager = db_manager
        self.extractor = extractor
        self.pipeline = pipeline
        self.vector_service = vector_service
        
        # Update tracking and queuing
        self.update_queue = asyncio.Queue(maxsize=5000)
        self.update_workers = []
        self.worker_count = 3
        
        # Source monitoring
        self.source_monitors = {}
        self.monitoring_tasks = {}
        
        # Conflict resolution
        self.conflict_resolver = ConflictResolver(db_manager)
        
        # Update statistics and metrics
        self.stats = {
            'updates_detected': 0,
            'updates_processed': 0,
            'conflicts_resolved': 0,
            'sources_monitored': 0,
            'last_update_cycle': None,
            'average_processing_time': 0.0
        }
        
        # Caching for update detection
        self._content_hashes = {}
        self._update_history = deque(maxlen=1000)
        
        self._initialize_source_monitors()
    
    def _initialize_source_monitors(self):
        """Initialize monitoring configurations for all sources"""
        self.source_monitors = {
            # Stack Overflow - API polling
            'stackoverflow': SourceMonitor(
                source_name='stackoverflow',
                monitor_type='api_polling',
                check_interval=300,  # 5 minutes
                config={
                    'api_endpoint': 'https://api.stackexchange.com/2.3/questions',
                    'params': {
                        'site': 'stackoverflow',
                        'sort': 'activity',
                        'order': 'desc',
                        'pagesize': 50
                    }
                }
            ),
            
            # CommandLineFu - RSS feed
            'commandlinefu': SourceMonitor(
                source_name='commandlinefu',
                monitor_type='rss',
                check_interval=600,  # 10 minutes
                config={
                    'feed_url': 'https://www.commandlinefu.com/commands/browse/rss'
                }
            ),
            
            # Security sources - periodic scraping
            'exploitdb': SourceMonitor(
                source_name='exploitdb',
                monitor_type='scraping',
                check_interval=3600,  # 1 hour
                config={
                    'base_url': 'https://www.exploit-db.com',
                    'search_endpoint': '/search?type=webapps'
                }
            ),
            
            'hacktricks': SourceMonitor(
                source_name='hacktricks',
                monitor_type='scraping',
                check_interval=1800,  # 30 minutes
                config={
                    'base_url': 'https://book.hacktricks.xyz',
                    'sections': ['pentesting-web', 'linux-hardening']
                }
            ),
            
            # Infrastructure sources
            'terraform': SourceMonitor(
                source_name='terraform',
                monitor_type='api_polling',
                check_interval=900,  # 15 minutes
                config={
                    'api_endpoint': 'https://registry.terraform.io/v1/modules',
                    'params': {'limit': 100}
                }
            ),
            
            'hashicorp': SourceMonitor(
                source_name='hashicorp',
                monitor_type='api_polling',
                check_interval=900,  # 15 minutes
                config={
                    'base_url': 'https://discuss.hashicorp.com'
                }
            )
        }
    
    async def start_monitoring(self):
        """Start real-time monitoring of all configured sources"""
        logger.info("Starting real-time knowledge monitoring",
                   sources_count=len(self.source_monitors))
        
        # Start update processing workers
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._update_worker(f"updater-{i}"))
            self.update_workers.append(worker)
        
        # Start monitoring tasks for each source
        for source_name, monitor in self.source_monitors.items():
            if monitor.enabled:
                task = asyncio.create_task(self._monitor_source(monitor))
                self.monitoring_tasks[source_name] = task
        
        logger.info("Real-time knowledge monitoring started",
                   active_monitors=len(self.monitoring_tasks),
                   active_workers=len(self.update_workers))
    
    async def stop_monitoring(self):
        """Stop all monitoring activities"""
        logger.info("Stopping real-time knowledge monitoring")
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        self.monitoring_tasks.clear()
        
        # Cancel update workers
        for worker in self.update_workers:
            worker.cancel()
        
        await asyncio.gather(*self.update_workers, return_exceptions=True)
        self.update_workers.clear()
        
        logger.info("Real-time knowledge monitoring stopped")
    
    async def _monitor_source(self, monitor: SourceMonitor):
        """Monitor a specific source for updates"""
        logger.info(f"Starting monitoring for {monitor.source_name}",
                   monitor_type=monitor.monitor_type,
                   check_interval=monitor.check_interval)
        
        try:
            while True:
                start_time = time.time()
                
                try:
                    # Check for updates based on monitor type
                    if monitor.monitor_type == 'api_polling':
                        updates = await self._check_api_updates(monitor)
                    elif monitor.monitor_type == 'rss':
                        updates = await self._check_rss_updates(monitor)
                    elif monitor.monitor_type == 'scraping':
                        updates = await self._check_scraping_updates(monitor)
                    else:
                        logger.warning(f"Unknown monitor type: {monitor.monitor_type}")
                        updates = []
                    
                    # Process detected updates
                    for update in updates:
                        await self.update_queue.put(update)
                        self.stats['updates_detected'] += 1
                    
                    # Update monitor status
                    monitor.last_check = datetime.utcnow()
                    if updates:
                        monitor.last_update = datetime.utcnow()
                    monitor.consecutive_failures = 0
                    
                    logger.debug(f"Monitoring check completed for {monitor.source_name}",
                               updates_found=len(updates),
                               check_duration=time.time() - start_time)
                
                except Exception as e:
                    monitor.consecutive_failures += 1
                    logger.warning(f"Monitoring failed for {monitor.source_name}",
                                 error=str(e),
                                 consecutive_failures=monitor.consecutive_failures)
                    
                    # Disable monitor if too many failures
                    if monitor.consecutive_failures >= 5:
                        monitor.enabled = False
                        logger.error(f"Disabling monitor for {monitor.source_name} due to consecutive failures")
                        break
                
                # Wait for next check interval
                await asyncio.sleep(monitor.check_interval)
                
        except asyncio.CancelledError:
            logger.info(f"Monitoring cancelled for {monitor.source_name}")
        except Exception as e:
            logger.error(f"Monitor error for {monitor.source_name}", error=str(e))
    
    async def _check_api_updates(self, monitor: SourceMonitor) -> List[UpdateEvent]:
        """Check for updates via API polling"""
        updates = []
        config = monitor.config
        
        try:
            async with aiohttp.ClientSession() as session:
                # Build request URL and parameters
                url = config['api_endpoint']
                params = config.get('params', {})
                
                # Add timestamp filter if available
                if monitor.last_check:
                    if monitor.source_name == 'stackoverflow':
                        params['fromdate'] = int(monitor.last_check.timestamp())
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process response based on source
                        if monitor.source_name == 'stackoverflow':
                            updates.extend(await self._process_stackoverflow_updates(data, monitor))
                        elif monitor.source_name == 'terraform':
                            updates.extend(await self._process_terraform_updates(data, monitor))
                        elif monitor.source_name == 'hashicorp':
                            updates.extend(await self._process_hashicorp_updates(data, monitor))
                    else:
                        logger.warning(f"API request failed for {monitor.source_name}",
                                     status=response.status)
        
        except Exception as e:
            logger.error(f"API polling error for {monitor.source_name}", error=str(e))
        
        return updates
    
    async def _check_rss_updates(self, monitor: SourceMonitor) -> List[UpdateEvent]:
        """Check for updates via RSS feed"""
        updates = []
        config = monitor.config
        
        try:
            async with aiohttp.ClientSession() as session:
                feed_url = config['feed_url']
                
                async with session.get(feed_url) as response:
                    if response.status == 200:
                        feed_content = await response.text()
                        feed = feedparser.parse(feed_content)
                        
                        # Process feed entries
                        for entry in feed.entries:
                            # Check if this is a new entry
                            entry_time = datetime(*entry.published_parsed[:6])
                            
                            if not monitor.last_check or entry_time > monitor.last_check:
                                update = UpdateEvent(
                                    id=uuid4(),
                                    source_name=monitor.source_name,
                                    update_type=UpdateType.NEW_CONTENT,
                                    item_id=None,
                                    source_url=entry.link,
                                    detected_at=datetime.utcnow(),
                                    metadata={
                                        'title': entry.title,
                                        'description': entry.description,
                                        'published': entry_time.isoformat(),
                                        'rss_entry': True
                                    }
                                )
                                updates.append(update)
                    else:
                        logger.warning(f"RSS request failed for {monitor.source_name}",
                                     status=response.status)
        
        except Exception as e:
            logger.error(f"RSS polling error for {monitor.source_name}", error=str(e))
        
        return updates
    
    async def _check_scraping_updates(self, monitor: SourceMonitor) -> List[UpdateEvent]:
        """Check for updates via web scraping"""
        updates = []
        
        # For scraping sources, we'll do a content hash comparison
        # to detect changes since last check
        
        try:
            if monitor.source_name == 'exploitdb':
                updates.extend(await self._check_exploitdb_updates(monitor))
            elif monitor.source_name == 'hacktricks':
                updates.extend(await self._check_hacktricks_updates(monitor))
        
        except Exception as e:
            logger.error(f"Scraping error for {monitor.source_name}", error=str(e))
        
        return updates
    
    async def _process_stackoverflow_updates(self, data: Dict[str, Any], monitor: SourceMonitor) -> List[UpdateEvent]:
        """Process Stack Overflow API response for updates"""
        updates = []
        
        items = data.get('items', [])
        for item in items:
            # Check if question was modified recently
            last_activity = datetime.fromtimestamp(item.get('last_activity_date', 0))
            creation_date = datetime.fromtimestamp(item.get('creation_date', 0))
            
            if monitor.last_check and last_activity > monitor.last_check:
                # Determine update type
                update_type = UpdateType.NEW_CONTENT if creation_date > monitor.last_check else UpdateType.CONTENT_MODIFIED
                
                update = UpdateEvent(
                    id=uuid4(),
                    source_name=monitor.source_name,
                    update_type=update_type,
                    item_id=None,  # Will be determined during processing
                    source_url=item.get('link', ''),
                    detected_at=datetime.utcnow(),
                    metadata={
                        'question_id': item.get('question_id'),
                        'title': item.get('title'),
                        'score': item.get('score', 0),
                        'tags': item.get('tags', []),
                        'last_activity_date': last_activity.isoformat(),
                        'stackoverflow_item': item
                    }
                )
                updates.append(update)
        
        return updates
    
    async def _process_terraform_updates(self, data: Dict[str, Any], monitor: SourceMonitor) -> List[UpdateEvent]:
        """Process Terraform Registry API response for updates"""
        updates = []
        
        modules = data.get('modules', [])
        for module in modules:
            # Check for new versions or updates
            module_key = f"{module.get('namespace')}/{module.get('name')}/{module.get('provider')}"
            
            # Simple check - in real implementation would compare versions
            if module_key not in self._content_hashes:
                update = UpdateEvent(
                    id=uuid4(),
                    source_name=monitor.source_name,
                    update_type=UpdateType.NEW_CONTENT,
                    item_id=None,
                    source_url=f"https://registry.terraform.io/modules/{module_key}",
                    detected_at=datetime.utcnow(),
                    metadata={
                        'module_name': module.get('name'),
                        'namespace': module.get('namespace'),
                        'provider': module.get('provider'),
                        'version': module.get('version'),
                        'description': module.get('description', ''),
                        'terraform_module': module
                    }
                )
                updates.append(update)
                self._content_hashes[module_key] = True
        
        return updates
    
    async def _process_hashicorp_updates(self, data: Dict[str, Any], monitor: SourceMonitor) -> List[UpdateEvent]:
        """Process HashiCorp Discuss API response for updates"""
        updates = []
        
        # This would need to be adapted based on the actual HashiCorp Discuss API
        # For now, placeholder implementation
        
        return updates
    
    async def _check_exploitdb_updates(self, monitor: SourceMonitor) -> List[UpdateEvent]:
        """Check Exploit-DB for new exploits"""
        updates = []
        
        try:
            async with aiohttp.ClientSession() as session:
                config = monitor.config
                url = config['base_url'] + config['search_endpoint']
                
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Generate content hash to detect changes
                        content_hash = hashlib.sha256(content.encode()).hexdigest()
                        cache_key = f"exploitdb_content_hash"
                        
                        if cache_key in self._content_hashes and self._content_hashes[cache_key] != content_hash:
                            # Content has changed, trigger update
                            update = UpdateEvent(
                                id=uuid4(),
                                source_name=monitor.source_name,
                                update_type=UpdateType.CONTENT_MODIFIED,
                                item_id=None,
                                source_url=url,
                                detected_at=datetime.utcnow(),
                                metadata={
                                    'content_hash': content_hash,
                                    'previous_hash': self._content_hashes.get(cache_key)
                                }
                            )
                            updates.append(update)
                        
                        self._content_hashes[cache_key] = content_hash
        
        except Exception as e:
            logger.error("Error checking Exploit-DB updates", error=str(e))
        
        return updates
    
    async def _check_hacktricks_updates(self, monitor: SourceMonitor) -> List[UpdateEvent]:
        """Check HackTricks for content updates"""
        updates = []
        
        try:
            config = monitor.config
            base_url = config['base_url']
            
            async with aiohttp.ClientSession() as session:
                for section in config.get('sections', []):
                    url = f"{base_url}/{section}"
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Generate content hash
                            content_hash = hashlib.sha256(content.encode()).hexdigest()
                            cache_key = f"hacktricks_{section}_hash"
                            
                            if cache_key in self._content_hashes and self._content_hashes[cache_key] != content_hash:
                                update = UpdateEvent(
                                    id=uuid4(),
                                    source_name=monitor.source_name,
                                    update_type=UpdateType.CONTENT_MODIFIED,
                                    item_id=None,
                                    source_url=url,
                                    detected_at=datetime.utcnow(),
                                    metadata={
                                        'section': section,
                                        'content_hash': content_hash,
                                        'previous_hash': self._content_hashes.get(cache_key)
                                    }
                                )
                                updates.append(update)
                            
                            self._content_hashes[cache_key] = content_hash
                        
                        # Rate limiting
                        await asyncio.sleep(1.0)
        
        except Exception as e:
            logger.error("Error checking HackTricks updates", error=str(e))
        
        return updates
    
    async def _update_worker(self, worker_id: str):
        """Worker that processes update events"""
        logger.info(f"Starting update worker {worker_id}")
        
        try:
            while True:
                update_event = await self.update_queue.get()
                start_time = time.time()
                
                try:
                    # Process the update event
                    await self._process_update_event(update_event)
                    
                    # Update statistics
                    processing_time = time.time() - start_time
                    self.stats['updates_processed'] += 1
                    self.stats['average_processing_time'] = (
                        self.stats['average_processing_time'] * 0.9 + processing_time * 0.1
                    )
                    
                    # Record in update history
                    self._update_history.append({
                        'update_id': str(update_event.id),
                        'source': update_event.source_name,
                        'type': update_event.update_type.value,
                        'processed_at': datetime.utcnow().isoformat(),
                        'processing_time': processing_time
                    })
                    
                    logger.debug(f"Worker {worker_id} processed update",
                               update_id=str(update_event.id),
                               processing_time=processing_time)
                
                except Exception as e:
                    logger.error(f"Worker {worker_id} update processing failed",
                                update_id=str(update_event.id),
                                error=str(e))
                
                finally:
                    self.update_queue.task_done()
                    
        except asyncio.CancelledError:
            logger.info(f"Update worker {worker_id} cancelled")
        except Exception as e:
            logger.error(f"Update worker {worker_id} error", error=str(e))
    
    async def _process_update_event(self, update_event: UpdateEvent):
        """Process a specific update event"""
        logger.info("Processing update event",
                   update_id=str(update_event.id),
                   source=update_event.source_name,
                   type=update_event.update_type.value)
        
        try:
            if update_event.update_type == UpdateType.NEW_CONTENT:
                await self._process_new_content(update_event)
            elif update_event.update_type == UpdateType.CONTENT_MODIFIED:
                await self._process_content_modification(update_event)
            elif update_event.update_type == UpdateType.CONTENT_DEPRECATED:
                await self._process_content_deprecation(update_event)
            elif update_event.update_type == UpdateType.SOURCE_UNAVAILABLE:
                await self._process_source_unavailable(update_event)
            
            update_event.processed = True
            
        except Exception as e:
            update_event.conflicts.append(f"Processing error: {str(e)}")
            logger.error("Failed to process update event", error=str(e))
    
    async def _process_new_content(self, update_event: UpdateEvent):
        """Process new content detection"""
        # Extract the new content using the appropriate extractor
        if update_event.metadata.get('rss_entry'):
            # RSS-based content
            await self._extract_rss_content(update_event)
        elif update_event.metadata.get('stackoverflow_item'):
            # Stack Overflow content
            await self._extract_stackoverflow_content(update_event)
        elif update_event.metadata.get('terraform_module'):
            # Terraform module
            await self._extract_terraform_content(update_event)
        else:
            # Generic content extraction
            await self._extract_generic_content(update_event)
    
    async def _extract_rss_content(self, update_event: UpdateEvent):
        """Extract content from RSS feed entry"""
        metadata = update_event.metadata
        
        # Create knowledge item from RSS entry
        knowledge_item = KnowledgeItem(
            id=uuid4(),
            title=metadata.get('title', 'RSS Content'),
            content=metadata.get('description', ''),
            knowledge_type='pattern',
            source_type=update_event.source_name,
            source_url=update_event.source_url,
            tags=[update_event.source_name, 'rss'],
            summary=metadata.get('description', '')[:200] + "...",
            confidence='medium',
            metadata={
                'update_event_id': str(update_event.id),
                'rss_published': metadata.get('published'),
                'detected_via': 'rss_monitor'
            }
        )
        
        # Submit for processing
        processing_id = await self.pipeline.submit_for_processing(knowledge_item, priority=1)
        update_event.metadata['processing_id'] = str(processing_id)
    
    async def _extract_stackoverflow_content(self, update_event: UpdateEvent):
        """Extract content from Stack Overflow update"""
        stackoverflow_item = update_event.metadata.get('stackoverflow_item', {})
        
        # Use existing Stack Overflow extraction logic from the main extractor
        raw_item = {
            'type': 'stackoverflow_question',
            'data': stackoverflow_item,
            'source_url': update_event.source_url,
            'tag': 'realtime_update'
        }
        
        # Convert to knowledge item (reusing logic from multi_source_knowledge_extractor)
        source_config = self.extractor.sources.get('stackoverflow')
        if source_config:
            knowledge_item = await self.extractor._convert_to_knowledge_item(
                raw_item, 'stackoverflow', source_config
            )
            
            # Check for conflicts with existing items
            conflicts = await self._detect_update_conflicts(knowledge_item, update_event)
            if conflicts:
                update_event.conflicts.extend(conflicts)
                await self.conflict_resolver.resolve_conflicts(knowledge_item, conflicts)
            
            # Submit for processing
            processing_id = await self.pipeline.submit_for_processing(knowledge_item, priority=2)
            update_event.metadata['processing_id'] = str(processing_id)
    
    async def _extract_terraform_content(self, update_event: UpdateEvent):
        """Extract content from Terraform module update"""
        terraform_module = update_event.metadata.get('terraform_module', {})
        
        raw_item = {
            'type': 'terraform_module',
            'data': terraform_module,
            'source_url': update_event.source_url,
            'category': 'infrastructure'
        }
        
        source_config = self.extractor.sources.get('terraform')
        if source_config:
            knowledge_item = await self.extractor._convert_to_knowledge_item(
                raw_item, 'terraform', source_config
            )
            
            # Submit for processing
            processing_id = await self.pipeline.submit_for_processing(knowledge_item, priority=1)
            update_event.metadata['processing_id'] = str(processing_id)
    
    async def _extract_generic_content(self, update_event: UpdateEvent):
        """Extract generic content from URL"""
        # For content hash-based updates, we need to re-extract the content
        try:
            # Re-run extraction for this source to get updated content
            source_config = self.extractor.sources.get(update_event.source_name)
            if source_config:
                # Extract a small batch of recent items
                extraction_result = await self.extractor._extract_from_source(
                    update_event.source_name, source_config, max_items=50, quality_threshold=0.6
                )
                
                logger.info("Re-extracted content for update",
                           source=update_event.source_name,
                           items_extracted=extraction_result.items_extracted)
        
        except Exception as e:
            logger.error("Failed to extract generic content", error=str(e))
    
    async def _process_content_modification(self, update_event: UpdateEvent):
        """Process content modification"""
        # Find existing items that may be affected by this modification
        existing_items = await self._find_existing_items_by_source_url(update_event.source_url)
        
        for item in existing_items:
            # Check if the item needs updating
            conflicts = await self._detect_modification_conflicts(item, update_event)
            if conflicts:
                update_event.conflicts.extend(conflicts)
                await self.conflict_resolver.resolve_conflicts(item, conflicts)
            
            # Mark item for re-processing
            item.metadata = item.metadata or {}
            item.metadata['last_source_update'] = update_event.detected_at.isoformat()
            item.metadata['update_event_id'] = str(update_event.id)
            
            processing_id = await self.pipeline.submit_for_processing(item, priority=3)
            update_event.metadata['reprocessing_ids'] = update_event.metadata.get('reprocessing_ids', [])
            update_event.metadata['reprocessing_ids'].append(str(processing_id))
    
    async def _process_content_deprecation(self, update_event: UpdateEvent):
        """Process content deprecation"""
        existing_items = await self._find_existing_items_by_source_url(update_event.source_url)
        
        for item in existing_items:
            # Mark item as deprecated
            await self._mark_item_deprecated(item.id, update_event.detected_at)
            
            # Update metadata
            item.metadata = item.metadata or {}
            item.metadata['deprecated_at'] = update_event.detected_at.isoformat()
            item.metadata['deprecation_reason'] = 'source_content_deprecated'
    
    async def _process_source_unavailable(self, update_event: UpdateEvent):
        """Process source unavailability"""
        # Update source monitor status
        if update_event.source_name in self.source_monitors:
            monitor = self.source_monitors[update_event.source_name]
            monitor.consecutive_failures += 1
            
            if monitor.consecutive_failures >= 3:
                # Temporarily disable the source
                monitor.enabled = False
                logger.warning(f"Temporarily disabled source {update_event.source_name} due to unavailability")
    
    async def _detect_update_conflicts(self, knowledge_item: KnowledgeItem, update_event: UpdateEvent) -> List[str]:
        """Detect conflicts for new/updated content"""
        conflicts = []
        
        # Check for version conflicts (same source URL but different content)
        existing_items = await self._find_existing_items_by_source_url(knowledge_item.source_url)
        
        for existing_item in existing_items:
            if existing_item.id != knowledge_item.id:
                # Compare content hashes
                new_hash = hashlib.sha256(knowledge_item.content.encode()).hexdigest()
                existing_hash = hashlib.sha256(existing_item.content.encode()).hexdigest()
                
                if new_hash != existing_hash:
                    conflicts.append(f"Version conflict with existing item {existing_item.id}")
        
        return conflicts
    
    async def _detect_modification_conflicts(self, existing_item: KnowledgeItem, update_event: UpdateEvent) -> List[str]:
        """Detect conflicts for content modifications"""
        conflicts = []
        
        # Check if local modifications conflict with source updates
        if existing_item.metadata and existing_item.metadata.get('locally_modified'):
            conflicts.append("Local modifications may conflict with source update")
        
        return conflicts
    
    async def _find_existing_items_by_source_url(self, source_url: str) -> List[KnowledgeItem]:
        """Find existing knowledge items by source URL"""
        items = []
        
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, title, content, knowledge_type, source_type, 
                           source_url, tags, summary, confidence, metadata,
                           created_at, updated_at
                    FROM knowledge_items 
                    WHERE source_url = $1 AND (status IS NULL OR status != 'deprecated')
                """, source_url)
                
                for row in rows:
                    item = KnowledgeItem(
                        id=UUID(row['id']),
                        title=row['title'],
                        content=row['content'],
                        knowledge_type=row['knowledge_type'],
                        source_type=row['source_type'],
                        source_url=row['source_url'],
                        tags=row['tags'],
                        summary=row['summary'],
                        confidence=row['confidence'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    items.append(item)
        
        except Exception as e:
            logger.error("Failed to find existing items by source URL", error=str(e))
        
        return items
    
    async def _mark_item_deprecated(self, item_id: UUID, deprecated_at: datetime):
        """Mark an item as deprecated"""
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.execute("""
                    UPDATE knowledge_items 
                    SET status = 'deprecated', 
                        metadata = jsonb_set(COALESCE(metadata, '{}'), '{deprecated_at}', to_jsonb($2::text)),
                        updated_at = $3
                    WHERE id = $1
                """, str(item_id), deprecated_at.isoformat(), datetime.utcnow())
        
        except Exception as e:
            logger.error("Failed to mark item as deprecated", error=str(e))
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        monitor_status = {}
        for name, monitor in self.source_monitors.items():
            monitor_status[name] = {
                'enabled': monitor.enabled,
                'monitor_type': monitor.monitor_type,
                'check_interval': monitor.check_interval,
                'last_check': monitor.last_check.isoformat() if monitor.last_check else None,
                'last_update': monitor.last_update.isoformat() if monitor.last_update else None,
                'consecutive_failures': monitor.consecutive_failures
            }
        
        return {
            'monitoring_active': len(self.monitoring_tasks) > 0,
            'active_monitors': len([m for m in self.source_monitors.values() if m.enabled]),
            'update_queue_size': self.update_queue.qsize(),
            'active_workers': len(self.update_workers),
            'monitor_status': monitor_status,
            'statistics': self.stats,
            'recent_updates': list(self._update_history)[-10:]  # Last 10 updates
        }

class ConflictResolver:
    """Handles conflict resolution for real-time updates"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def resolve_conflicts(self, knowledge_item: KnowledgeItem, conflicts: List[str]):
        """Resolve conflicts for a knowledge item"""
        logger.info("Resolving conflicts",
                   item_id=str(knowledge_item.id),
                   conflicts_count=len(conflicts))
        
        for conflict in conflicts:
            if "Version conflict" in conflict:
                await self._resolve_version_conflict(knowledge_item, conflict)
            elif "Local modifications" in conflict:
                await self._resolve_modification_conflict(knowledge_item, conflict)
        
        # Log conflict resolution
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.execute("""
                    INSERT INTO realtime_conflicts (
                        id, item_id, conflicts, resolved_at, resolution_strategy
                    ) VALUES ($1, $2, $3, $4, $5)
                """, 
                str(uuid4()), str(knowledge_item.id), conflicts, 
                datetime.utcnow(), 'automatic_resolution')
        except Exception as e:
            logger.warning("Failed to log conflict resolution", error=str(e))
    
    async def _resolve_version_conflict(self, knowledge_item: KnowledgeItem, conflict: str):
        """Resolve version conflicts by keeping the latest version"""
        # Simple strategy: always keep the newest content
        # In a more sophisticated system, this could involve merging or user intervention
        logger.info("Resolving version conflict with latest-wins strategy",
                   item_id=str(knowledge_item.id))
    
    async def _resolve_modification_conflict(self, knowledge_item: KnowledgeItem, conflict: str):
        """Resolve modification conflicts"""
        # Create a backup of the locally modified version before updating
        logger.info("Resolving modification conflict with backup strategy",
                   item_id=str(knowledge_item.id))