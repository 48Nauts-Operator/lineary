# ABOUTME: Vector operations service for BETTY Memory System
# ABOUTME: Handles Qdrant vector database operations for semantic search and embeddings

import asyncio
from typing import List, Dict, Any, Optional
from uuid import uuid4
import structlog
import numpy as np
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

from services.base_service import BaseService

logger = structlog.get_logger(__name__)

class VectorService(BaseService):
    """Service for vector operations using Qdrant"""
    
    def __init__(self, databases):
        super().__init__(databases)
        # Initialize sentence transformer model for semantic embeddings
        # Using OpenAI-compatible dimensions (1536) with appropriate model
        try:
            # Try to use a model that matches our Qdrant collection dimensions
            self.embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')  # 768-dimensional
            self.embedding_dimension = 768
            logger.info("Sentence transformer model loaded", model="all-mpnet-base-v2", dimensions=768)
        except Exception as e:
            # Fallback to smaller model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dimensional
            self.embedding_dimension = 384
            logger.info("Using fallback model", model="all-MiniLM-L6-v2", dimensions=384)
    
    async def get_embedding(self, text: str) -> List[float]:
        """Generate semantic embedding for text using sentence transformers"""
        try:
            # Sanitize input text
            if not text or not text.strip():
                text = "empty content"
            
            # Generate embedding using sentence transformer
            embedding = await asyncio.to_thread(
                self.embedding_model.encode,
                text.strip(),
                normalize_embeddings=True
            )
            
            # Pad embedding to 1536 dimensions to match Qdrant collection
            embedding_list = embedding.tolist()
            if len(embedding_list) < 1536:
                # Pad with zeros to reach 1536 dimensions
                embedding_list.extend([0.0] * (1536 - len(embedding_list)))
            
            return embedding_list
            
        except Exception as e:
            logger.error(
                "Failed to generate embedding",
                text_preview=text[:100],
                error=str(e)
            )
            # Fallback to zero vector with correct dimensions
            return np.zeros(1536).tolist()
    
    def _create_simple_embedding(self, text: str) -> List[float]:
        """Create semantic embedding using sentence transformers (synchronous wrapper)"""
        # This method now delegates to the async version for consistency
        # but provides synchronous interface where needed
        try:
            # Use the sentence transformer directly for sync calls
            if not text or not text.strip():
                text = "empty content"
                
            embedding = self.embedding_model.encode(
                text.strip(),
                normalize_embeddings=True
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(
                "Failed to generate embedding (sync)",
                text_preview=text[:100] if text else "None",
                error=str(e)
            )
            # Fallback to zero vector with correct dimensions
            return np.zeros(1536).tolist()
    
    async def create_embedding(
        self,
        item_id: str,
        content: str,
        metadata: Dict[str, Any] = None,
        collection_name: str = "knowledge_items"
    ) -> str:
        """Create vector embedding for content"""
        try:
            # Generate embedding using semantic model
            embedding = await self.get_embedding(content)
            
            # Generate unique point ID
            point_id = str(uuid4())
            
            # Prepare metadata
            payload = {
                "item_id": item_id,
                "content_preview": content[:200],  # First 200 chars for preview
                "created_at": str(asyncio.get_event_loop().time()),
                **(metadata or {})
            }
            
            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            
            # Insert into Qdrant
            await asyncio.to_thread(
                self.qdrant.upsert,
                collection_name=collection_name,
                points=[point]
            )
            
            logger.info(
                "Vector embedding created",
                point_id=point_id,
                item_id=item_id,
                collection=collection_name,
                embedding_dim=len(embedding)
            )
            
            return point_id
            
        except Exception as e:
            logger.error(
                "Failed to create vector embedding",
                item_id=item_id,
                error=str(e)
            )
            raise
    
    async def update_embedding(
        self,
        point_id: str,
        content: str,
        metadata: Dict[str, Any] = None,
        collection_name: str = "knowledge_items"
    ) -> None:
        """Update existing vector embedding"""
        try:
            # Generate new embedding using semantic model
            embedding = await self.get_embedding(content)
            
            # Prepare updated payload
            payload = {
                "content_preview": content[:200],
                "updated_at": str(asyncio.get_event_loop().time()),
                **(metadata or {})
            }
            
            # Update point
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            
            await asyncio.to_thread(
                self.qdrant.upsert,
                collection_name=collection_name,
                points=[point]
            )
            
            logger.info(
                "Vector embedding updated",
                point_id=point_id,
                collection=collection_name
            )
            
        except Exception as e:
            logger.error(
                "Failed to update vector embedding",
                point_id=point_id,
                error=str(e)
            )
            raise
    
    async def delete_embedding(
        self,
        point_id: str,
        collection_name: str = "knowledge_items"
    ) -> None:
        """Delete vector embedding"""
        try:
            await asyncio.to_thread(
                self.qdrant.delete,
                collection_name=collection_name,
                points_selector=[point_id]
            )
            
            logger.info(
                "Vector embedding deleted",
                point_id=point_id,
                collection=collection_name
            )
            
        except Exception as e:
            logger.error(
                "Failed to delete vector embedding",
                point_id=point_id,
                error=str(e)
            )
            raise
    
    async def search_similar(
        self,
        query: str,
        collection_name: str = "knowledge_items",
        limit: int = 20,
        similarity_threshold: float = 0.7,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        try:
            # Generate query embedding using semantic model
            query_embedding = await self.get_embedding(query)
            
            # Build filter if provided
            search_filter = None
            if filters:
                conditions = []
                
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Handle list values (e.g., tags)
                        for item in value:
                            conditions.append(
                                FieldCondition(key=key, match=MatchValue(value=item))
                            )
                    else:
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                
                if conditions:
                    search_filter = Filter(must=conditions)
            
            # Search
            search_results = await asyncio.to_thread(
                self.qdrant.search,
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=similarity_threshold,
                query_filter=search_filter,
                with_payload=True
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            logger.info(
                "Vector similarity search completed",
                collection=collection_name,
                query_preview=query[:50],
                results_count=len(results),
                threshold=similarity_threshold
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Vector similarity search failed",
                query=query[:50],
                collection=collection_name,
                error=str(e)
            )
            raise
    
    async def get_embedding_stats(
        self,
        collection_name: str = "knowledge_items"
    ) -> Dict[str, Any]:
        """Get embedding collection statistics"""
        try:
            collection_info = await asyncio.to_thread(
                self.qdrant.get_collection,
                collection_name=collection_name
            )
            
            return {
                "collection_name": collection_name,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "config": {
                    "vector_size": collection_info.config.params.vectors.size,
                    "distance": collection_info.config.params.vectors.distance.value
                }
            }
            
        except Exception as e:
            logger.error(
                "Failed to get embedding stats",
                collection=collection_name,
                error=str(e)
            )
            raise
    
    async def create_collection_if_not_exists(
        self,
        collection_name: str,
        vector_size: int = None,
        distance: str = "Cosine"
    ) -> None:
        """Create collection if it doesn't exist"""
        try:
            from qdrant_client.models import VectorParams, Distance
            
            # Check if collection exists
            try:
                await asyncio.to_thread(
                    self.qdrant.get_collection,
                    collection_name=collection_name
                )
                logger.info(f"Collection {collection_name} already exists")
                return
            except:
                # Collection doesn't exist, create it
                pass
            
            # Determine vector size
            if vector_size is None:
                vector_size = self.settings.vector_dimension
            
            # Map distance string to enum
            distance_map = {
                "Cosine": Distance.COSINE,
                "Dot": Distance.DOT,
                "Euclid": Distance.EUCLID
            }
            
            distance_enum = distance_map.get(distance, Distance.COSINE)
            
            # Create collection
            await asyncio.to_thread(
                self.qdrant.create_collection,
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_enum
                )
            )
            
            logger.info(
                "Vector collection created",
                collection=collection_name,
                vector_size=vector_size,
                distance=distance
            )
            
        except Exception as e:
            logger.error(
                "Failed to create vector collection",
                collection=collection_name,
                error=str(e)
            )
            raise
    
    async def batch_create_embeddings(
        self,
        items: List[Dict[str, Any]],
        collection_name: str = "knowledge_items",
        batch_size: int = 100
    ) -> List[str]:
        """Create embeddings for multiple items in batches"""
        try:
            point_ids = []
            
            # Process in batches
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_points = []
                
                # Generate embeddings for batch using semantic model
                contents = [item["content"] for item in batch]
                embeddings = []
                
                for content in contents:
                    embedding = await self.get_embedding(content)
                    embeddings.append(embedding)
                
                # Create points
                for j, (item, embedding) in enumerate(zip(batch, embeddings)):
                    point_id = str(uuid4())
                    point_ids.append(point_id)
                    
                    payload = {
                        "item_id": item["item_id"],
                        "content_preview": item["content"][:200],
                        "created_at": str(asyncio.get_event_loop().time()),
                        **item.get("metadata", {})
                    }
                    
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                    batch_points.append(point)
                
                # Insert batch
                await asyncio.to_thread(
                    self.qdrant.upsert,
                    collection_name=collection_name,
                    points=batch_points
                )
                
                logger.info(
                    "Batch embeddings created",
                    batch_start=i,
                    batch_size=len(batch_points),
                    collection=collection_name
                )
            
            logger.info(
                "Batch embedding creation completed",
                total_items=len(items),
                total_points=len(point_ids),
                collection=collection_name
            )
            
            return point_ids
            
        except Exception as e:
            logger.error(
                "Batch embedding creation failed",
                total_items=len(items),
                collection=collection_name,
                error=str(e)
            )
            raise