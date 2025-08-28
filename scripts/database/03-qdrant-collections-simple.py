#!/usr/bin/env python3
"""
BETTY Memory System - Qdrant Collections Initialization (Simplified)
Database: Qdrant Vector Database for Semantic Embeddings
Purpose: Create collections for knowledge embeddings, conversation search, and pattern matching

Simplified version compatible with latest Qdrant client API.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams,
    Distance,
    PayloadSchemaType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QdrantInitializer:
    """Initialize Qdrant collections for BETTY Memory System."""
    
    def __init__(self, host: str = "betty_qdrant", port: int = 6333):
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
    
    def create_collection_simple(self, collection_name: str, description: str) -> bool:
        """
        Create a collection with basic configuration.
        
        Args:
            collection_name: Name of the collection
            description: Description of the collection purpose
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if collection already exists
            try:
                collection_info = self.client.get_collection(collection_name)
                logger.info(f"Collection '{collection_name}' already exists with {collection_info.points_count} points")
                return True
            except Exception:
                pass  # Collection doesn't exist, create it
            
            # Create collection with basic configuration
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=768,  # Standard embedding dimension
                    distance=Distance.COSINE  # Cosine similarity for semantic search
                )
            )
            
            # Create basic payload indexes
            payload_fields = []
            
            if collection_name == "knowledge_embeddings":
                payload_fields = [
                    "project_id", "knowledge_type", "domain", "subdomain", 
                    "technologies", "patterns", "quality_score", "reusability_score",
                    "usage_count", "complexity_level", "created_at"
                ]
            elif collection_name == "conversation_embeddings":
                payload_fields = [
                    "session_id", "project_id", "user_id", "role", "message_index",
                    "intent", "complexity_score", "knowledge_density", "tools_used", "timestamp"
                ]
            elif collection_name == "pattern_embeddings":
                payload_fields = [
                    "pattern_type", "pattern_name", "technologies", "domains",
                    "complexity_level", "success_rate", "reuse_count", "created_at"
                ]
            elif collection_name == "cross_project_embeddings":
                payload_fields = [
                    "source_project_id", "target_project_id", "relationship_type",
                    "similarity_score", "confidence_score", "applicability_score",
                    "shared_technologies", "created_at"
                ]
            
            # Create payload indexes for efficient filtering
            for field_name in payload_fields:
                try:
                    # Determine field type
                    if field_name.endswith('_score') or field_name.endswith('_count'):
                        field_type = PayloadSchemaType.FLOAT
                    elif field_name in ['message_index', 'usage_count', 'reuse_count']:
                        field_type = PayloadSchemaType.INTEGER  
                    elif field_name in ['created_at', 'timestamp']:
                        field_type = PayloadSchemaType.DATETIME
                    elif field_name in ['technologies', 'patterns', 'tools_used', 'domains', 'shared_technologies']:
                        field_type = PayloadSchemaType.KEYWORD  # For arrays
                    else:
                        field_type = PayloadSchemaType.KEYWORD
                    
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=field_type
                    )
                except Exception as e:
                    logger.warning(f"Could not create index for {field_name}: {e}")
            
            logger.info(f"Created collection '{collection_name}' with {len(payload_fields)} payload indexes")
            logger.info(f"Description: {description}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
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
                        "indexed_vectors_count": info.indexed_vectors_count if hasattr(info, 'indexed_vectors_count') else 0,
                        "status": info.status.value if hasattr(info, 'status') else "unknown"
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
            ("knowledge_embeddings", "Core knowledge items with 768-dimensional vectors for semantic search"),
            ("conversation_embeddings", "Chat messages and context for semantic conversation search"),
            ("pattern_embeddings", "Code patterns and architectural solutions for pattern matching"),
            ("cross_project_embeddings", "Cross-project knowledge relationships for intelligence transfer")
        ]
        
        success_count = 0
        for collection_name, description in collections_to_create:
            logger.info(f"Creating collection: {collection_name}")
            if self.create_collection_simple(collection_name, description):
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
    initializer = QdrantInitializer(host="betty_qdrant", port=6333)
    
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