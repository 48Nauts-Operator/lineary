#!/usr/bin/env python3
"""
BETTY Memory System - Qdrant Collections Initialization
Database: Qdrant Vector Database for Semantic Embeddings
Purpose: Create collections for knowledge embeddings, conversation search, and pattern matching

Integration with BETTY Architecture:
- knowledge_embeddings: Core knowledge items with 768-dimensional vectors
- conversation_embeddings: Chat messages and context for semantic search  
- pattern_embeddings: Code patterns and architectural solutions
- cross_project_embeddings: Cross-project knowledge relationships

Qdrant Configuration:
- HTTP API on port 6333
- Collections optimized for similarity search
- Metadata filtering for project boundaries
- Performance tuned for <200ms search queries
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    CollectionInfo,
    VectorParams,
    PayloadSchemaType,
    Distance,
    OptimizersConfig,
    WalConfig,
    HnswConfig,
    QuantizationConfig,
    ScalarQuantization,
    ScalarType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QdrantInitializer:
    """Initialize Qdrant collections for BETTY Memory System."""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        """
        Initialize Qdrant client.
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
        """
        self.host = host
        self.port = port
        self.client = None
        self.base_url = f"http://{host}:{port}"
        
    async def connect(self) -> bool:
        """
        Establish connection to Qdrant server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            
            # Test connection
            await self._wait_for_server()
            collections = self.client.get_collections()
            logger.info(f"Connected to Qdrant at {self.base_url}")
            logger.info(f"Current collections: {len(collections.collections)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            return False
    
    async def _wait_for_server(self, max_retries: int = 30, delay: float = 2.0):
        """
        Wait for Qdrant server to be ready.
        
        Args:
            max_retries: Maximum number of connection attempts
            delay: Delay between attempts in seconds
        """
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/health")
                    if response.status_code == 200:
                        logger.info("Qdrant server is ready")
                        return
            except Exception:
                if attempt < max_retries - 1:
                    logger.info(f"Waiting for Qdrant server... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    raise Exception("Qdrant server not available after maximum retries")
    
    def create_knowledge_embeddings_collection(self) -> bool:
        """
        Create collection for knowledge item embeddings.
        
        Optimized for:
        - 768-dimensional vectors (standard embedding size)
        - Fast similarity search across all knowledge items
        - Project-scoped filtering
        - Quality and reusability scoring
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection_name = "knowledge_embeddings"
            
            # Check if collection already exists
            try:
                collection_info = self.client.get_collection(collection_name)
                logger.info(f"Collection '{collection_name}' already exists with {collection_info.points_count} points")
                return True
            except Exception:
                pass  # Collection doesn't exist, create it
            
            # Create collection with optimized configuration
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=768,  # Standard embedding dimension
                    distance=Distance.COSINE,  # Cosine similarity for semantic search
                    hnsw_config=HnswConfig(
                        m=16,  # Number of bi-directional links for every new element
                        ef_construct=200,  # Size of the dynamic candidate list
                        full_scan_threshold=10000,  # Threshold for switching to full scan
                        on_disk=True  # Store vectors on disk for large collections
                    )
                ),
                optimizers_config=OptimizersConfig(
                    deleted_threshold=0.2,  # Trigger optimization when 20% deleted
                    vacuum_min_vector_number=1000,  # Minimum vectors for vacuum
                    default_segment_number=2,  # Number of segments per shard
                    max_segment_size_kb=200000,  # Maximum segment size (200MB)
                    memmap_threshold_kb=100000,  # Memory mapping threshold (100MB)
                    indexing_threshold_kb=20000,  # Indexing threshold (20MB)
                    flush_interval_sec=5,  # Flush to disk interval
                    max_optimization_threads=2  # Optimization threads
                ),
                wal_config=WalConfig(
                    wal_capacity_mb=32,  # WAL capacity
                    wal_segments_ahead=0  # WAL segments ahead
                ),
                quantization_config=ScalarQuantization(
                    scalar=ScalarQuantization(
                        type=ScalarType.INT8,  # 8-bit quantization for memory efficiency
                        quantile=0.99,  # Quantile for clipping
                        always_ram=True  # Keep quantized vectors in RAM
                    )
                ),
                on_disk_payload=True,  # Store payload on disk
                timeout=60  # Operation timeout
            )
            
            # Create payload indexes for efficient filtering
            payload_indexes = [
                ("project_id", PayloadSchemaType.KEYWORD),
                ("knowledge_type", PayloadSchemaType.KEYWORD),
                ("domain", PayloadSchemaType.KEYWORD),
                ("subdomain", PayloadSchemaType.KEYWORD),
                ("technologies", PayloadSchemaType.KEYWORD),
                ("patterns", PayloadSchemaType.KEYWORD),
                ("quality_score", PayloadSchemaType.FLOAT),
                ("reusability_score", PayloadSchemaType.FLOAT),
                ("usage_count", PayloadSchemaType.INTEGER),
                ("complexity_level", PayloadSchemaType.KEYWORD),
                ("created_at", PayloadSchemaType.DATETIME),
                ("valid_from", PayloadSchemaType.DATETIME),
                ("valid_until", PayloadSchemaType.DATETIME)
            ]
            
            for field_name, field_type in payload_indexes:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
            
            logger.info(f"Created collection '{collection_name}' with {len(payload_indexes)} payload indexes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create knowledge embeddings collection: {e}")
            return False
    
    def create_conversation_embeddings_collection(self) -> bool:
        """
        Create collection for conversation message embeddings.
        
        Optimized for:
        - Chat message semantic search
        - Session context retrieval
        - Cross-session conversation patterns
        - Tool usage correlation
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection_name = "conversation_embeddings"
            
            # Check if collection already exists
            try:
                collection_info = self.client.get_collection(collection_name)
                logger.info(f"Collection '{collection_name}' already exists with {collection_info.points_count} points")
                return True
            except Exception:
                pass
            
            # Create collection optimized for conversation search
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE,
                    hnsw_config=HnswConfig(
                        m=16,
                        ef_construct=100,  # Lower for frequent updates
                        full_scan_threshold=5000,
                        on_disk=False  # Keep in memory for fast access
                    )
                ),
                optimizers_config=OptimizersConfig(
                    deleted_threshold=0.3,
                    vacuum_min_vector_number=500,
                    default_segment_number=1,
                    max_segment_size_kb=50000,  # Smaller segments for conversation data
                    memmap_threshold_kb=20000,
                    indexing_threshold_kb=5000,
                    flush_interval_sec=3,
                    max_optimization_threads=1
                ),
                on_disk_payload=False,  # Keep payload in memory for speed
                timeout=60
            )
            
            # Create payload indexes for conversation filtering
            payload_indexes = [
                ("session_id", PayloadSchemaType.KEYWORD),
                ("project_id", PayloadSchemaType.KEYWORD),
                ("user_id", PayloadSchemaType.KEYWORD),
                ("role", PayloadSchemaType.KEYWORD),
                ("message_index", PayloadSchemaType.INTEGER),
                ("intent", PayloadSchemaType.KEYWORD),
                ("complexity_score", PayloadSchemaType.FLOAT),
                ("knowledge_density", PayloadSchemaType.FLOAT),
                ("tools_used", PayloadSchemaType.KEYWORD),
                ("timestamp", PayloadSchemaType.DATETIME),
                ("has_tool_calls", PayloadSchemaType.BOOL),
                ("has_errors", PayloadSchemaType.BOOL)
            ]
            
            for field_name, field_type in payload_indexes:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
            
            logger.info(f"Created collection '{collection_name}' with {len(payload_indexes)} payload indexes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create conversation embeddings collection: {e}")
            return False
    
    def create_pattern_embeddings_collection(self) -> bool:
        """
        Create collection for code pattern and architectural solution embeddings.
        
        Optimized for:
        - Code pattern matching
        - Architectural solution similarity
        - Cross-project pattern reuse
        - Implementation approach clustering
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection_name = "pattern_embeddings"
            
            # Check if collection already exists
            try:
                collection_info = self.client.get_collection(collection_name)
                logger.info(f"Collection '{collection_name}' already exists with {collection_info.points_count} points")
                return True
            except Exception:
                pass
            
            # Create collection optimized for pattern matching
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE,
                    hnsw_config=HnswConfig(
                        m=32,  # Higher connectivity for pattern clustering
                        ef_construct=400,  # Higher for better pattern grouping
                        full_scan_threshold=20000,
                        on_disk=True
                    )
                ),
                optimizers_config=OptimizersConfig(
                    deleted_threshold=0.1,  # Less frequent optimization
                    vacuum_min_vector_number=2000,
                    default_segment_number=3,
                    max_segment_size_kb=300000,
                    memmap_threshold_kb=150000,
                    indexing_threshold_kb=30000,
                    flush_interval_sec=10,
                    max_optimization_threads=2
                ),
                on_disk_payload=True,
                timeout=60
            )
            
            # Create payload indexes for pattern filtering
            payload_indexes = [
                ("pattern_type", PayloadSchemaType.KEYWORD),
                ("pattern_name", PayloadSchemaType.KEYWORD),
                ("technologies", PayloadSchemaType.KEYWORD),
                ("domains", PayloadSchemaType.KEYWORD),
                ("complexity_level", PayloadSchemaType.KEYWORD),
                ("success_rate", PayloadSchemaType.FLOAT),
                ("reuse_count", PayloadSchemaType.INTEGER),
                ("implementation_effort", PayloadSchemaType.KEYWORD),
                ("prerequisites", PayloadSchemaType.KEYWORD),
                ("business_domains", PayloadSchemaType.KEYWORD),
                ("created_at", PayloadSchemaType.DATETIME),
                ("last_used_at", PayloadSchemaType.DATETIME)
            ]
            
            for field_name, field_type in payload_indexes:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
            
            logger.info(f"Created collection '{collection_name}' with {len(payload_indexes)} payload indexes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create pattern embeddings collection: {e}")
            return False
    
    def create_cross_project_embeddings_collection(self) -> bool:
        """
        Create collection for cross-project knowledge relationship embeddings.
        
        Optimized for:
        - Cross-project pattern detection
        - Knowledge transfer opportunities
        - Similar problem identification
        - Solution applicability scoring
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection_name = "cross_project_embeddings"
            
            # Check if collection already exists
            try:
                collection_info = self.client.get_collection(collection_name)
                logger.info(f"Collection '{collection_name}' already exists with {collection_info.points_count} points")
                return True
            except Exception:
                pass
            
            # Create collection optimized for cross-project analysis
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=768,
                    distance=Distance.COSINE,
                    hnsw_config=HnswConfig(
                        m=24,
                        ef_construct=300,
                        full_scan_threshold=15000,
                        on_disk=True
                    )
                ),
                optimizers_config=OptimizersConfig(
                    deleted_threshold=0.15,
                    vacuum_min_vector_number=1500,
                    default_segment_number=2,
                    max_segment_size_kb=250000,
                    memmap_threshold_kb=100000,
                    indexing_threshold_kb=25000,
                    flush_interval_sec=8,
                    max_optimization_threads=2
                ),
                on_disk_payload=True,
                timeout=60
            )
            
            # Create payload indexes for cross-project analysis
            payload_indexes = [
                ("source_project_id", PayloadSchemaType.KEYWORD),
                ("target_project_id", PayloadSchemaType.KEYWORD),
                ("relationship_type", PayloadSchemaType.KEYWORD),
                ("similarity_score", PayloadSchemaType.FLOAT),
                ("confidence_score", PayloadSchemaType.FLOAT),
                ("applicability_score", PayloadSchemaType.FLOAT),
                ("shared_technologies", PayloadSchemaType.KEYWORD),
                ("shared_patterns", PayloadSchemaType.KEYWORD),
                ("shared_domains", PayloadSchemaType.KEYWORD),
                ("transfer_complexity", PayloadSchemaType.KEYWORD),
                ("success_likelihood", PayloadSchemaType.FLOAT),
                ("created_at", PayloadSchemaType.DATETIME),
                ("validated_at", PayloadSchemaType.DATETIME)
            ]
            
            for field_name, field_type in payload_indexes:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
            
            logger.info(f"Created collection '{collection_name}' with {len(payload_indexes)} payload indexes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create cross-project embeddings collection: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all collections.
        
        Returns:
            Dict containing collection statistics
        """
        try:
            collections = self.client.get_collections()
            stats = {
                "total_collections": len(collections.collections),
                "collections": {}
            }
            
            for collection in collections.collections:
                try:
                    info = self.client.get_collection(collection.name)
                    stats["collections"][collection.name] = {
                        "points_count": info.points_count,
                        "indexed_vectors_count": info.indexed_vectors_count,
                        "vectors_config": {
                            "size": info.config.params.vectors.size,
                            "distance": info.config.params.vectors.distance.value
                        },
                        "status": info.status.value,
                        "optimizer_status": info.optimizer_status
                    }
                except Exception as e:
                    stats["collections"][collection.name] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    async def initialize_all_collections(self) -> bool:
        """
        Initialize all BETTY Memory System collections.
        
        Returns:
            bool: True if all collections created successfully
        """
        logger.info("Starting Qdrant collections initialization for BETTY Memory System")
        
        collections_to_create = [
            ("knowledge_embeddings", self.create_knowledge_embeddings_collection),
            ("conversation_embeddings", self.create_conversation_embeddings_collection),
            ("pattern_embeddings", self.create_pattern_embeddings_collection),
            ("cross_project_embeddings", self.create_cross_project_embeddings_collection)
        ]
        
        success_count = 0
        for collection_name, create_func in collections_to_create:
            logger.info(f"Creating collection: {collection_name}")
            if create_func():
                success_count += 1
                logger.info(f"✓ Successfully created {collection_name}")
            else:
                logger.error(f"✗ Failed to create {collection_name}")
        
        # Get final statistics
        stats = self.get_collection_stats()
        logger.info(f"Initialization complete: {success_count}/{len(collections_to_create)} collections created")
        logger.info(f"Collection statistics: {stats}")
        
        return success_count == len(collections_to_create)

async def main():
    """Main initialization function."""
    logger.info("BETTY Memory System - Qdrant Collections Initialization")
    logger.info("=" * 60)
    
    # Initialize Qdrant collections
    initializer = QdrantInitializer(host="localhost", port=6333)
    
    # Connect to Qdrant
    if not await initializer.connect():
        logger.error("Failed to connect to Qdrant server")
        sys.exit(1)
    
    # Initialize all collections
    success = await initializer.initialize_all_collections()
    
    if success:
        logger.info("=" * 60)
        logger.info("✓ BETTY Memory System Qdrant initialization completed successfully")
        logger.info("All collections created with optimized configurations")
        logger.info("Ready for semantic search and embedding operations")
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("✗ BETTY Memory System Qdrant initialization failed")
        logger.error("Some collections could not be created")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())