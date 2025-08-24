# ABOUTME: Multi-Source Knowledge Extraction Pipeline for Betty's Pattern Intelligence Enhancement
# ABOUTME: Extracts knowledge from Stack Overflow, CommandLineFu, security sources, and infrastructure sources

import asyncio
import aiohttp
import hashlib
import json
import time
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Set
from uuid import UUID, uuid4
from dataclasses import dataclass, field
import structlog
from collections import defaultdict
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

from core.database import DatabaseManager
from models.knowledge import KnowledgeItem
from services.vector_service import VectorService
from services.pattern_quality_service import AdvancedQualityScorer
from services.pattern_intelligence_service import PatternIntelligenceEngine

logger = structlog.get_logger(__name__)

@dataclass
class SourceConfig:
    """Configuration for a knowledge source"""
    name: str
    base_url: str
    api_key: Optional[str] = None
    rate_limit: float = 1.0  # requests per second
    timeout: float = 30.0
    enabled: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    authentication: Optional[Dict[str, str]] = None
    quality_weight: float = 1.0

@dataclass
class ExtractionResult:
    """Result of knowledge extraction from a source"""
    source_name: str
    items_extracted: int
    items_processed: int
    items_stored: int
    errors: List[str]
    processing_time: float
    quality_scores: List[float]

class MultiSourceKnowledgeExtractor:
    """
    Advanced Multi-Source Knowledge Extraction Pipeline
    Supports Stack Overflow, CommandLineFu, security sources, and infrastructure sources
    """
    
    def __init__(
        self, 
        db_manager: DatabaseManager,
        vector_service: VectorService,
        quality_scorer: AdvancedQualityScorer,
        pattern_intelligence: PatternIntelligenceEngine
    ):
        self.db_manager = db_manager
        self.vector_service = vector_service
        self.quality_scorer = quality_scorer
        self.pattern_intelligence = pattern_intelligence
        
        # Initialize source configurations
        self.sources = self._initialize_sources()
        
        # Rate limiting and request management
        self._request_trackers = defaultdict(list)
        self._session_pool = {}
        
        # Processing statistics
        self.stats = {
            'total_extracted': 0,
            'total_processed': 0,
            'total_stored': 0,
            'sources_active': 0,
            'last_extraction': None
        }
        
    def _initialize_sources(self) -> Dict[str, SourceConfig]:
        """Initialize all knowledge source configurations"""
        sources = {
            # Stack Overflow API
            'stackoverflow': SourceConfig(
                name='Stack Overflow',
                base_url='https://api.stackexchange.com/2.3',
                rate_limit=0.33,  # 30 requests per minute limit
                headers={'Accept-Encoding': 'gzip'},
                quality_weight=0.9,
                enabled=True
            ),
            
            # CommandLineFu (scraping)
            'commandlinefu': SourceConfig(
                name='CommandLineFu',
                base_url='https://www.commandlinefu.com',
                rate_limit=0.5,  # Be respectful
                quality_weight=0.8,
                enabled=True
            ),
            
            # Exploit-DB (security patterns)
            'exploitdb': SourceConfig(
                name='Exploit Database',
                base_url='https://www.exploit-db.com',
                rate_limit=0.2,  # Very conservative
                quality_weight=0.95,
                enabled=True
            ),
            
            # HackTricks (security knowledge)
            'hacktricks': SourceConfig(
                name='HackTricks',
                base_url='https://book.hacktricks.xyz',
                rate_limit=0.3,
                quality_weight=0.85,
                enabled=True
            ),
            
            # OWASP Knowledge Base
            'owasp': SourceConfig(
                name='OWASP',
                base_url='https://owasp.org',
                rate_limit=0.5,
                quality_weight=0.95,
                enabled=True
            ),
            
            # Kubernetes Documentation
            'kubernetes': SourceConfig(
                name='Kubernetes Documentation',
                base_url='https://kubernetes.io/docs',
                rate_limit=1.0,
                quality_weight=0.9,
                enabled=True
            ),
            
            # Terraform Registry
            'terraform': SourceConfig(
                name='Terraform Registry',
                base_url='https://registry.terraform.io',
                rate_limit=0.5,
                quality_weight=0.85,
                enabled=True
            ),
            
            # HashiCorp Discuss
            'hashicorp': SourceConfig(
                name='HashiCorp Discuss',
                base_url='https://discuss.hashicorp.com',
                rate_limit=0.5,
                quality_weight=0.8,
                enabled=True
            )
        }
        
        return sources
    
    async def extract_all_sources(
        self,
        max_items_per_source: int = 1000,
        quality_threshold: float = 0.6
    ) -> Dict[str, ExtractionResult]:
        """Extract knowledge from all enabled sources"""
        logger.info("Starting multi-source knowledge extraction",
                   sources_count=len([s for s in self.sources.values() if s.enabled]),
                   max_items_per_source=max_items_per_source)
        
        results = {}
        extraction_tasks = []
        
        # Create extraction tasks for all enabled sources
        for source_name, config in self.sources.items():
            if config.enabled:
                task = asyncio.create_task(
                    self._extract_from_source(
                        source_name, config, max_items_per_source, quality_threshold
                    )
                )
                extraction_tasks.append((source_name, task))
        
        # Execute all extractions concurrently
        for source_name, task in extraction_tasks:
            try:
                result = await task
                results[source_name] = result
                logger.info(f"Completed extraction from {source_name}",
                           items_extracted=result.items_extracted,
                           items_stored=result.items_stored)
            except Exception as e:
                logger.error(f"Failed extraction from {source_name}", error=str(e))
                results[source_name] = ExtractionResult(
                    source_name=source_name,
                    items_extracted=0,
                    items_processed=0,
                    items_stored=0,
                    errors=[str(e)],
                    processing_time=0.0,
                    quality_scores=[]
                )
        
        # Update statistics
        await self._update_extraction_statistics(results)
        
        logger.info("Multi-source knowledge extraction completed",
                   total_sources=len(results),
                   total_items_stored=sum(r.items_stored for r in results.values()))
        
        return results
    
    async def _extract_from_source(
        self,
        source_name: str,
        config: SourceConfig,
        max_items: int,
        quality_threshold: float
    ) -> ExtractionResult:
        """Extract knowledge from a specific source"""
        start_time = time.time()
        items_extracted = 0
        items_processed = 0
        items_stored = 0
        errors = []
        quality_scores = []
        
        try:
            # Get or create session for this source
            session = await self._get_session(source_name, config)
            
            # Source-specific extraction logic
            if source_name == 'stackoverflow':
                raw_items = await self._extract_stackoverflow(session, config, max_items)
            elif source_name == 'commandlinefu':
                raw_items = await self._extract_commandlinefu(session, config, max_items)
            elif source_name == 'exploitdb':
                raw_items = await self._extract_exploitdb(session, config, max_items)
            elif source_name == 'hacktricks':
                raw_items = await self._extract_hacktricks(session, config, max_items)
            elif source_name == 'owasp':
                raw_items = await self._extract_owasp(session, config, max_items)
            elif source_name == 'kubernetes':
                raw_items = await self._extract_kubernetes(session, config, max_items)
            elif source_name == 'terraform':
                raw_items = await self._extract_terraform(session, config, max_items)
            elif source_name == 'hashicorp':
                raw_items = await self._extract_hashicorp(session, config, max_items)
            else:
                raise ValueError(f"Unknown source: {source_name}")
            
            items_extracted = len(raw_items)
            
            # Process each extracted item
            for raw_item in raw_items:
                try:
                    # Convert to KnowledgeItem
                    knowledge_item = await self._convert_to_knowledge_item(
                        raw_item, source_name, config
                    )
                    
                    # Quality scoring
                    from models.pattern_quality import PatternContext
                    context = PatternContext(
                        domain=self._determine_domain(knowledge_item),
                        team_experience="medium",
                        business_criticality="medium",
                        technology_stack=[source_name],
                        compliance_requirements=[]
                    )
                    
                    quality_score = await self.quality_scorer.score_pattern_quality(
                        knowledge_item, context
                    )
                    quality_scores.append(quality_score.overall_score)
                    
                    items_processed += 1
                    
                    # Store if quality meets threshold
                    if quality_score.overall_score >= quality_threshold:
                        await self._store_knowledge_item(knowledge_item, quality_score)
                        items_stored += 1
                        
                        # Check for pattern relationships
                        await self._detect_cross_source_relationships(knowledge_item)
                    
                    # Rate limiting
                    await self._respect_rate_limit(source_name, config)
                    
                except Exception as e:
                    errors.append(f"Error processing item: {str(e)}")
                    logger.warning(f"Failed to process item from {source_name}", error=str(e))
            
        except Exception as e:
            errors.append(f"Source extraction error: {str(e)}")
            logger.error(f"Failed to extract from {source_name}", error=str(e))
        
        processing_time = time.time() - start_time
        
        return ExtractionResult(
            source_name=source_name,
            items_extracted=items_extracted,
            items_processed=items_processed,
            items_stored=items_stored,
            errors=errors,
            processing_time=processing_time,
            quality_scores=quality_scores
        )
    
    async def _extract_stackoverflow(
        self,
        session: aiohttp.ClientSession,
        config: SourceConfig,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Extract knowledge from Stack Overflow API"""
        items = []
        page_size = min(100, max_items)
        pages_needed = (max_items + page_size - 1) // page_size
        
        # Popular programming tags for better quality
        tags = ['python', 'javascript', 'java', 'docker', 'kubernetes', 'aws', 'react', 'node.js']
        
        for tag in tags[:3]:  # Limit to prevent rate limiting
            for page in range(1, min(pages_needed + 1, 4)):  # Max 3 pages per tag
                try:
                    url = f"{config.base_url}/questions"
                    params = {
                        'site': 'stackoverflow',
                        'tagged': tag,
                        'sort': 'votes',
                        'order': 'desc',
                        'pagesize': page_size,
                        'page': page,
                        'filter': 'withbody'
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            questions = data.get('items', [])
                            
                            for question in questions:
                                if len(items) >= max_items:
                                    return items
                                
                                # Get answers for high-score questions
                                if question.get('score', 0) > 5:
                                    answers = await self._get_stackoverflow_answers(
                                        session, question['question_id'], config
                                    )
                                    question['answers'] = answers
                                
                                items.append({
                                    'type': 'stackoverflow_question',
                                    'data': question,
                                    'source_url': question.get('link', ''),
                                    'tag': tag
                                })
                        
                        await self._respect_rate_limit('stackoverflow', config)
                        
                except Exception as e:
                    logger.warning(f"Error extracting Stack Overflow page {page}", error=str(e))
        
        return items
    
    async def _get_stackoverflow_answers(
        self,
        session: aiohttp.ClientSession,
        question_id: int,
        config: SourceConfig
    ) -> List[Dict[str, Any]]:
        """Get answers for a Stack Overflow question"""
        try:
            url = f"{config.base_url}/questions/{question_id}/answers"
            params = {
                'site': 'stackoverflow',
                'sort': 'votes',
                'order': 'desc',
                'filter': 'withbody',
                'pagesize': 3  # Top 3 answers only
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', [])
        except Exception as e:
            logger.warning(f"Error getting Stack Overflow answers for {question_id}", error=str(e))
        
        return []
    
    async def _extract_commandlinefu(
        self,
        session: aiohttp.ClientSession,
        config: SourceConfig,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Extract commands from CommandLineFu"""
        items = []
        
        # Categories to extract from
        categories = ['networking', 'system-administration', 'security', 'monitoring']
        
        for category in categories:
            if len(items) >= max_items:
                break
                
            try:
                # Get commands from category
                url = f"{config.base_url}/commands/browse/sort-by-votes/{category}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract command elements
                        command_divs = soup.find_all('div', class_='command')
                        
                        for div in command_divs[:max_items // len(categories)]:
                            try:
                                command_text = div.find('code').get_text().strip()
                                description = div.find('p').get_text().strip() if div.find('p') else ""
                                votes = self._extract_votes(div)
                                
                                items.append({
                                    'type': 'commandlinefu_command',
                                    'data': {
                                        'command': command_text,
                                        'description': description,
                                        'votes': votes,
                                        'category': category
                                    },
                                    'source_url': url,
                                    'category': category
                                })
                            except Exception as e:
                                logger.debug(f"Error parsing command div", error=str(e))
                
                await self._respect_rate_limit('commandlinefu', config)
                
            except Exception as e:
                logger.warning(f"Error extracting CommandLineFu category {category}", error=str(e))
        
        return items
    
    async def _extract_exploitdb(
        self,
        session: aiohttp.ClientSession,
        config: SourceConfig,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Extract security patterns from Exploit-DB"""
        items = []
        
        try:
            # Focus on web application exploits (most relevant for patterns)
            url = f"{config.base_url}/search"
            params = {
                'type': 'webapps',
                'platform': 'multiple'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract exploit entries
                    exploit_rows = soup.find_all('tr')[1:max_items + 1]  # Skip header
                    
                    for row in exploit_rows:
                        try:
                            cells = row.find_all('td')
                            if len(cells) >= 4:
                                title = cells[1].get_text().strip()
                                author = cells[2].get_text().strip()
                                exploit_type = cells[3].get_text().strip()
                                
                                # Get exploit ID from link
                                link = cells[1].find('a')
                                exploit_id = None
                                if link and 'href' in link.attrs:
                                    href = link['href']
                                    exploit_id = href.split('/')[-1] if '/' in href else None
                                
                                items.append({
                                    'type': 'exploitdb_entry',
                                    'data': {
                                        'title': title,
                                        'author': author,
                                        'exploit_type': exploit_type,
                                        'exploit_id': exploit_id
                                    },
                                    'source_url': f"{config.base_url}{link['href']}" if link else "",
                                    'category': 'security'
                                })
                        except Exception as e:
                            logger.debug(f"Error parsing exploit row", error=str(e))
            
            await self._respect_rate_limit('exploitdb', config)
            
        except Exception as e:
            logger.warning(f"Error extracting Exploit-DB", error=str(e))
        
        return items
    
    async def _extract_hacktricks(
        self,
        session: aiohttp.ClientSession,
        config: SourceConfig,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Extract security knowledge from HackTricks"""
        items = []
        
        # Key security topics
        topics = [
            'pentesting-web',
            'linux-hardening',
            'windows-hardening', 
            'network-attacks',
            'privilege-escalation'
        ]
        
        for topic in topics:
            if len(items) >= max_items:
                break
                
            try:
                url = f"{config.base_url}/{topic}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract main content sections
                        content_sections = soup.find_all(['h2', 'h3', 'h4'])
                        
                        for section in content_sections[:max_items // len(topics)]:
                            try:
                                title = section.get_text().strip()
                                
                                # Get following content until next header
                                content = ""
                                for sibling in section.next_siblings:
                                    if sibling.name in ['h2', 'h3', 'h4']:
                                        break
                                    if hasattr(sibling, 'get_text'):
                                        content += sibling.get_text().strip() + "\n"
                                
                                if len(content.strip()) > 100:  # Meaningful content
                                    items.append({
                                        'type': 'hacktricks_section',
                                        'data': {
                                            'title': title,
                                            'content': content.strip()[:2000],  # Limit length
                                            'topic': topic
                                        },
                                        'source_url': url,
                                        'category': 'security'
                                    })
                            except Exception as e:
                                logger.debug(f"Error parsing HackTricks section", error=str(e))
                
                await self._respect_rate_limit('hacktricks', config)
                
            except Exception as e:
                logger.warning(f"Error extracting HackTricks topic {topic}", error=str(e))
        
        return items
    
    async def _extract_owasp(
        self,
        session: aiohttp.ClientSession,
        config: SourceConfig,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Extract security knowledge from OWASP"""
        items = []
        
        # OWASP key resources
        resources = [
            'www-project-top-ten',
            'www-project-web-security-testing-guide',
            'www-project-application-security-verification-standard'
        ]
        
        for resource in resources:
            if len(items) >= max_items:
                break
                
            try:
                url = f"{config.base_url}/{resource}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract main content
                        main_content = soup.find('main') or soup.find('div', class_='content')
                        
                        if main_content:
                            sections = main_content.find_all(['h2', 'h3'])
                            
                            for section in sections[:max_items // len(resources)]:
                                try:
                                    title = section.get_text().strip()
                                    
                                    # Get content after this section
                                    content_parts = []
                                    for sibling in section.next_siblings:
                                        if sibling.name in ['h2', 'h3']:
                                            break
                                        if hasattr(sibling, 'get_text'):
                                            text = sibling.get_text().strip()
                                            if text:
                                                content_parts.append(text)
                                    
                                    content = "\n".join(content_parts)
                                    
                                    if len(content.strip()) > 50:
                                        items.append({
                                            'type': 'owasp_section',
                                            'data': {
                                                'title': title,
                                                'content': content[:1500],  # Limit length
                                                'resource': resource
                                            },
                                            'source_url': url,
                                            'category': 'security'
                                        })
                                except Exception as e:
                                    logger.debug(f"Error parsing OWASP section", error=str(e))
                
                await self._respect_rate_limit('owasp', config)
                
            except Exception as e:
                logger.warning(f"Error extracting OWASP resource {resource}", error=str(e))
        
        return items
    
    async def _extract_kubernetes(
        self,
        session: aiohttp.ClientSession,
        config: SourceConfig,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Extract patterns from Kubernetes documentation"""
        # For this implementation, we'll use Context7 MCP for structured doc access
        items = []
        
        try:
            # Use Context7 to get Kubernetes documentation
            from mcp__context7__resolve_library_id import resolve_library_id
            from mcp__context7__get_library_docs import get_library_docs
            
            # This would be implemented with Context7 MCP integration
            # For now, placeholder implementation
            logger.info("Kubernetes extraction would use Context7 MCP integration")
            
        except ImportError:
            logger.warning("Context7 MCP not available for Kubernetes extraction")
        
        return items
    
    async def _extract_terraform(
        self,
        session: aiohttp.ClientSession,
        config: SourceConfig,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Extract patterns from Terraform Registry"""
        items = []
        
        try:
            # Get popular providers
            url = f"{config.base_url}/v1/providers"
            params = {'limit': 20}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    providers = data.get('providers', [])
                    
                    for provider in providers[:5]:  # Top 5 providers
                        provider_name = provider.get('name', '')
                        namespace = provider.get('namespace', '')
                        
                        # Get modules for this provider
                        modules_url = f"{config.base_url}/v1/modules"
                        module_params = {
                            'provider': provider_name,
                            'limit': max_items // 5
                        }
                        
                        async with session.get(modules_url, params=module_params) as mod_response:
                            if mod_response.status == 200:
                                mod_data = await mod_response.json()
                                modules = mod_data.get('modules', [])
                                
                                for module in modules:
                                    items.append({
                                        'type': 'terraform_module',
                                        'data': {
                                            'name': module.get('name', ''),
                                            'namespace': module.get('namespace', ''),
                                            'provider': module.get('provider', ''),
                                            'description': module.get('description', ''),
                                            'version': module.get('version', ''),
                                            'downloads': module.get('downloads', 0)
                                        },
                                        'source_url': f"https://registry.terraform.io/modules/{module.get('namespace')}/{module.get('name')}/{module.get('provider')}",
                                        'category': 'infrastructure'
                                    })
                        
                        await self._respect_rate_limit('terraform', config)
            
        except Exception as e:
            logger.warning(f"Error extracting Terraform Registry", error=str(e))
        
        return items
    
    async def _extract_hashicorp(
        self,
        session: aiohttp.ClientSession,
        config: SourceConfig,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Extract knowledge from HashiCorp Discuss"""
        items = []
        
        # Popular categories
        categories = ['terraform', 'vault', 'consul', 'nomad', 'packer']
        
        for category in categories:
            if len(items) >= max_items:
                break
                
            try:
                url = f"{config.base_url}/c/{category}/latest.json"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        topics = data.get('topic_list', {}).get('topics', [])
                        
                        for topic in topics[:max_items // len(categories)]:
                            try:
                                items.append({
                                    'type': 'hashicorp_discussion',
                                    'data': {
                                        'title': topic.get('title', ''),
                                        'excerpt': topic.get('excerpt', ''),
                                        'posts_count': topic.get('posts_count', 0),
                                        'like_count': topic.get('like_count', 0),
                                        'views': topic.get('views', 0),
                                        'category': category
                                    },
                                    'source_url': f"{config.base_url}/t/{topic.get('slug', '')}/{topic.get('id', '')}",
                                    'category': 'infrastructure'
                                })
                            except Exception as e:
                                logger.debug(f"Error parsing HashiCorp topic", error=str(e))
                
                await self._respect_rate_limit('hashicorp', config)
                
            except Exception as e:
                logger.warning(f"Error extracting HashiCorp category {category}", error=str(e))
        
        return items
    
    # Helper methods
    async def _get_session(self, source_name: str, config: SourceConfig) -> aiohttp.ClientSession:
        """Get or create HTTP session for source"""
        if source_name not in self._session_pool:
            timeout = aiohttp.ClientTimeout(total=config.timeout)
            self._session_pool[source_name] = aiohttp.ClientSession(
                headers=config.headers,
                timeout=timeout
            )
        
        return self._session_pool[source_name]
    
    async def _respect_rate_limit(self, source_name: str, config: SourceConfig):
        """Implement rate limiting for source"""
        now = time.time()
        tracker = self._request_trackers[source_name]
        
        # Remove old requests (older than 1 second)
        tracker[:] = [t for t in tracker if now - t < 1.0]
        
        # Check if we need to wait
        if len(tracker) >= config.rate_limit:
            wait_time = 1.0 / config.rate_limit
            await asyncio.sleep(wait_time)
        
        # Record this request
        tracker.append(now)
    
    def _extract_votes(self, element) -> int:
        """Extract vote count from HTML element"""
        try:
            vote_element = element.find(class_='vote')
            if vote_element:
                return int(vote_element.get_text().strip())
        except (ValueError, AttributeError):
            pass
        return 0
    
    def _determine_domain(self, knowledge_item: KnowledgeItem) -> str:
        """Determine domain from knowledge item"""
        source = knowledge_item.source_type
        tags = knowledge_item.tags
        
        if source in ['exploitdb', 'hacktricks', 'owasp']:
            return 'security'
        elif source in ['kubernetes', 'terraform', 'hashicorp']:
            return 'infrastructure'
        elif source == 'commandlinefu':
            return 'system-administration'
        elif source == 'stackoverflow':
            # Determine from tags
            if any(tag in tags for tag in ['docker', 'kubernetes', 'aws', 'terraform']):
                return 'infrastructure'
            elif any(tag in tags for tag in ['security', 'authentication', 'encryption']):
                return 'security'
            else:
                return 'development'
        else:
            return 'general'
    
    async def _convert_to_knowledge_item(
        self,
        raw_item: Dict[str, Any],
        source_name: str,
        config: SourceConfig
    ) -> KnowledgeItem:
        """Convert raw extracted item to KnowledgeItem"""
        item_type = raw_item.get('type', '')
        data = raw_item.get('data', {})
        
        # Generate title and content based on item type
        if item_type == 'stackoverflow_question':
            title = data.get('title', 'Stack Overflow Question')
            content = self._format_stackoverflow_content(data)
            tags = data.get('tags', [])
            
        elif item_type == 'commandlinefu_command':
            title = f"Command: {data.get('command', '')[:50]}..."
            content = self._format_commandlinefu_content(data)
            tags = ['command-line', data.get('category', '')]
            
        elif item_type in ['exploitdb_entry', 'hacktricks_section', 'owasp_section']:
            title = data.get('title', 'Security Knowledge')
            content = self._format_security_content(data, item_type)
            tags = ['security', data.get('category', ''), data.get('topic', '')]
            
        elif item_type in ['terraform_module', 'hashicorp_discussion']:
            title = data.get('name') or data.get('title', 'Infrastructure Pattern')
            content = self._format_infrastructure_content(data, item_type)
            tags = ['infrastructure', data.get('provider', ''), data.get('category', '')]
            
        else:
            title = 'Extracted Knowledge'
            content = json.dumps(data, indent=2)
            tags = [source_name]
        
        # Clean tags
        tags = [tag for tag in tags if tag and tag.strip()]
        
        return KnowledgeItem(
            id=uuid4(),
            title=title[:200],  # Limit title length
            content=content,
            knowledge_type='pattern',
            source_type=source_name,
            source_url=raw_item.get('source_url', ''),
            tags=tags,
            summary=self._generate_summary(content),
            confidence='medium',
            metadata={
                'extraction_timestamp': datetime.utcnow().isoformat(),
                'source_config': config.name,
                'original_type': item_type,
                'quality_weight': config.quality_weight
            }
        )
    
    def _format_stackoverflow_content(self, data: Dict[str, Any]) -> str:
        """Format Stack Overflow question and answers"""
        content = f"## Question\n\n{data.get('body', '')}\n\n"
        
        answers = data.get('answers', [])
        if answers:
            content += "## Top Answers\n\n"
            for i, answer in enumerate(answers[:3], 1):
                content += f"### Answer {i} (Score: {answer.get('score', 0)})\n\n"
                content += f"{answer.get('body', '')}\n\n"
        
        return content
    
    def _format_commandlinefu_content(self, data: Dict[str, Any]) -> str:
        """Format CommandLineFu command"""
        content = f"## Command\n\n```bash\n{data.get('command', '')}\n```\n\n"
        
        if data.get('description'):
            content += f"## Description\n\n{data.get('description')}\n\n"
        
        content += f"**Votes:** {data.get('votes', 0)}\n"
        content += f"**Category:** {data.get('category', 'Unknown')}\n"
        
        return content
    
    def _format_security_content(self, data: Dict[str, Any], item_type: str) -> str:
        """Format security-related content"""
        content = ""
        
        if item_type == 'exploitdb_entry':
            content = f"**Exploit Type:** {data.get('exploit_type', '')}\n"
            content += f"**Author:** {data.get('author', '')}\n\n"
            if data.get('description'):
                content += f"## Description\n\n{data.get('description')}\n\n"
                
        else:  # hacktricks_section, owasp_section
            content = data.get('content', '')
        
        return content
    
    def _format_infrastructure_content(self, data: Dict[str, Any], item_type: str) -> str:
        """Format infrastructure-related content"""
        content = ""
        
        if item_type == 'terraform_module':
            content = f"**Provider:** {data.get('provider', '')}\n"
            content += f"**Version:** {data.get('version', '')}\n"
            content += f"**Downloads:** {data.get('downloads', 0)}\n\n"
            if data.get('description'):
                content += f"## Description\n\n{data.get('description')}\n\n"
                
        elif item_type == 'hashicorp_discussion':
            content = f"**Posts:** {data.get('posts_count', 0)}\n"
            content += f"**Views:** {data.get('views', 0)}\n"
            content += f"**Likes:** {data.get('like_count', 0)}\n\n"
            if data.get('excerpt'):
                content += f"## Excerpt\n\n{data.get('excerpt')}\n\n"
        
        return content
    
    def _generate_summary(self, content: str) -> str:
        """Generate summary from content"""
        # Simple extraction of first meaningful sentence
        sentences = re.split(r'[.!?]+', content.replace('\n', ' '))
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                return sentence
        
        return content[:150] + "..." if len(content) > 150 else content
    
    async def _store_knowledge_item(self, item: KnowledgeItem, quality_score) -> None:
        """Store knowledge item in database"""
        try:
            # Store in PostgreSQL
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.execute("""
                    INSERT INTO knowledge_items (
                        id, title, content, knowledge_type, source_type, 
                        source_url, tags, summary, confidence, metadata, 
                        created_at, quality_score
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                    ) ON CONFLICT (id) DO NOTHING
                """, 
                str(item.id), item.title, item.content, item.knowledge_type, 
                item.source_type, item.source_url, item.tags, item.summary, 
                item.confidence, json.dumps(item.metadata), 
                datetime.utcnow(), quality_score.overall_score)
            
            # Store vector embedding
            embedding_text = f"{item.title} {item.summary} {' '.join(item.tags)}"
            embedding = await self.vector_service.generate_embedding(embedding_text)
            await self.vector_service.store_embedding(
                str(item.id), embedding, {'source': item.source_type}
            )
            
            # Store in Neo4j for relationships
            async with self.db_manager.get_neo4j_session() as session:
                await session.run("""
                    MERGE (k:Knowledge {id: $id})
                    SET k.title = $title,
                        k.source_type = $source_type,
                        k.created_at = $created_at,
                        k.quality_score = $quality_score
                """, {
                    'id': str(item.id),
                    'title': item.title,
                    'source_type': item.source_type,
                    'created_at': datetime.utcnow().isoformat(),
                    'quality_score': quality_score.overall_score
                })
            
        except Exception as e:
            logger.error("Failed to store knowledge item", 
                        item_id=str(item.id), error=str(e))
            raise
    
    async def _detect_cross_source_relationships(self, new_item: KnowledgeItem) -> None:
        """Detect relationships between new item and existing knowledge"""
        try:
            # Find similar items using vector search
            embedding_text = f"{new_item.title} {new_item.summary} {' '.join(new_item.tags)}"
            embedding = await self.vector_service.generate_embedding(embedding_text)
            
            similar_items = await self.vector_service.search_similar(
                embedding, limit=10, threshold=0.7
            )
            
            # Create relationships for highly similar items
            for similar_item in similar_items:
                if similar_item.id != new_item.id:
                    await self._create_cross_source_relationship(new_item, similar_item)
                    
        except Exception as e:
            logger.warning("Failed to detect cross-source relationships", error=str(e))
    
    async def _create_cross_source_relationship(
        self, 
        item1: KnowledgeItem, 
        item2: KnowledgeItem
    ) -> None:
        """Create relationship between items from different sources"""
        try:
            async with self.db_manager.get_neo4j_session() as session:
                await session.run("""
                    MATCH (a:Knowledge {id: $id1}), (b:Knowledge {id: $id2})
                    MERGE (a)-[r:CROSS_SOURCE_SIMILAR]->(b)
                    SET r.created_at = $created_at,
                        r.confidence = $confidence
                """, {
                    'id1': str(item1.id),
                    'id2': str(item2.id),
                    'created_at': datetime.utcnow().isoformat(),
                    'confidence': 0.8
                })
        except Exception as e:
            logger.warning("Failed to create cross-source relationship", error=str(e))
    
    async def _update_extraction_statistics(
        self, 
        results: Dict[str, ExtractionResult]
    ) -> None:
        """Update extraction statistics"""
        total_extracted = sum(r.items_extracted for r in results.values())
        total_processed = sum(r.items_processed for r in results.values())
        total_stored = sum(r.items_stored for r in results.values())
        
        self.stats.update({
            'total_extracted': self.stats['total_extracted'] + total_extracted,
            'total_processed': self.stats['total_processed'] + total_processed,
            'total_stored': self.stats['total_stored'] + total_stored,
            'sources_active': len([r for r in results.values() if r.items_stored > 0]),
            'last_extraction': datetime.utcnow().isoformat()
        })
        
        # Store stats in database
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.execute("""
                    INSERT INTO extraction_stats (
                        timestamp, total_extracted, total_processed, 
                        total_stored, sources_active, extraction_results
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                datetime.utcnow(), total_extracted, total_processed, 
                total_stored, len(results), json.dumps({
                    name: {
                        'items_extracted': r.items_extracted,
                        'items_stored': r.items_stored,
                        'processing_time': r.processing_time,
                        'avg_quality': sum(r.quality_scores) / len(r.quality_scores) if r.quality_scores else 0.0
                    } for name, r in results.items()
                }))
        except Exception as e:
            logger.warning("Failed to store extraction statistics", error=str(e))
    
    async def get_extraction_statistics(self) -> Dict[str, Any]:
        """Get current extraction statistics"""
        return {
            **self.stats,
            'sources_configured': len(self.sources),
            'sources_enabled': len([s for s in self.sources.values() if s.enabled]),
            'average_quality_threshold': 0.6,
            'supported_sources': list(self.sources.keys())
        }
    
    async def close(self):
        """Clean up sessions and resources"""
        for session in self._session_pool.values():
            await session.close()
        self._session_pool.clear()