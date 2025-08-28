# ABOUTME: Progress tracking service for long-running operations
# ABOUTME: Provides real-time progress updates using Redis for batch operations

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID
import asyncio
import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)

class ProgressTracker:
    """Service for tracking progress of long-running operations"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.progress_key_prefix = "betty:progress:"
        self.progress_ttl = 3600  # 1 hour TTL for progress data
    
    async def start_progress(self, operation_id: UUID, initial_message: str = "Starting operation"):
        """Start tracking progress for an operation"""
        try:
            progress_data = {
                "operation_id": str(operation_id),
                "status": "running",
                "progress_percentage": 0.0,
                "processed_items": 0,
                "total_items": 0,
                "failed_items": 0,
                "current_phase": "initialization",
                "message": initial_message,
                "started_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "estimated_time_remaining": None,
                "throughput_items_per_second": None,
                "errors": []
            }
            
            await self._store_progress(operation_id, progress_data)
            
            logger.info("Progress tracking started", operation_id=str(operation_id))
            
        except Exception as e:
            logger.error("Failed to start progress tracking", error=str(e))
            raise
    
    async def update_progress(
        self,
        operation_id: UUID,
        processed_items: int,
        total_items: Optional[int] = None,
        current_phase: Optional[str] = None,
        message: Optional[str] = None,
        failed_items: Optional[int] = None,
        errors: Optional[List[str]] = None
    ):
        """Update progress for an operation"""
        try:
            # Get current progress data
            current_progress = await self.get_progress(operation_id)
            if not current_progress:
                await self.start_progress(operation_id, "Operation in progress")
                current_progress = await self.get_progress(operation_id)
            
            # Update progress data
            now = datetime.utcnow()
            
            if total_items is not None:
                current_progress["total_items"] = total_items
            
            current_progress["processed_items"] = processed_items
            
            if failed_items is not None:
                current_progress["failed_items"] = failed_items
            
            # Calculate progress percentage
            if current_progress["total_items"] > 0:
                current_progress["progress_percentage"] = (
                    processed_items / current_progress["total_items"] * 100
                )
            
            # Update phase and message
            if current_phase:
                current_progress["current_phase"] = current_phase
            
            if message:
                current_progress["message"] = message
            
            # Calculate throughput and ETA
            start_time = datetime.fromisoformat(current_progress["started_at"])
            elapsed_seconds = (now - start_time).total_seconds()
            
            if elapsed_seconds > 0 and processed_items > 0:
                current_progress["throughput_items_per_second"] = processed_items / elapsed_seconds
                
                # Estimate time remaining
                if current_progress["total_items"] > processed_items and current_progress["throughput_items_per_second"] > 0:
                    remaining_items = current_progress["total_items"] - processed_items
                    remaining_seconds = remaining_items / current_progress["throughput_items_per_second"]
                    current_progress["estimated_time_remaining"] = int(remaining_seconds)
            
            # Add errors if provided
            if errors:
                current_progress["errors"].extend(errors)
                # Keep only last 100 errors to prevent memory issues
                current_progress["errors"] = current_progress["errors"][-100:]
            
            current_progress["last_updated"] = now.isoformat()
            
            await self._store_progress(operation_id, current_progress)
            
            logger.debug(
                "Progress updated",
                operation_id=str(operation_id),
                progress=current_progress["progress_percentage"],
                phase=current_progress["current_phase"]
            )
            
        except Exception as e:
            logger.error("Failed to update progress", error=str(e))
            # Don't raise exception to avoid breaking the main operation
    
    async def complete_progress(self, operation_id: UUID, final_message: str = "Operation completed"):
        """Mark progress as completed"""
        try:
            current_progress = await self.get_progress(operation_id)
            if current_progress:
                current_progress["status"] = "completed"
                current_progress["progress_percentage"] = 100.0
                current_progress["message"] = final_message
                current_progress["current_phase"] = "completed"
                current_progress["completed_at"] = datetime.utcnow().isoformat()
                current_progress["last_updated"] = datetime.utcnow().isoformat()
                current_progress["estimated_time_remaining"] = 0
                
                await self._store_progress(operation_id, current_progress)
                
                logger.info("Progress completed", operation_id=str(operation_id))
            
        except Exception as e:
            logger.error("Failed to complete progress", error=str(e))
    
    async def fail_progress(self, operation_id: UUID, error_message: str):
        """Mark progress as failed"""
        try:
            current_progress = await self.get_progress(operation_id)
            if current_progress:
                current_progress["status"] = "failed"
                current_progress["message"] = f"Operation failed: {error_message}"
                current_progress["current_phase"] = "failed"
                current_progress["failed_at"] = datetime.utcnow().isoformat()
                current_progress["last_updated"] = datetime.utcnow().isoformat()
                current_progress["errors"].append(error_message)
                
                await self._store_progress(operation_id, current_progress)
                
                logger.error("Progress marked as failed", operation_id=str(operation_id), error=error_message)
            
        except Exception as e:
            logger.error("Failed to mark progress as failed", error=str(e))
    
    async def pause_progress(self, operation_id: UUID, pause_message: str = "Operation paused"):
        """Mark progress as paused"""
        try:
            current_progress = await self.get_progress(operation_id)
            if current_progress:
                current_progress["status"] = "paused"
                current_progress["message"] = pause_message
                current_progress["current_phase"] = "paused"
                current_progress["paused_at"] = datetime.utcnow().isoformat()
                current_progress["last_updated"] = datetime.utcnow().isoformat()
                
                await self._store_progress(operation_id, current_progress)
                
                logger.info("Progress paused", operation_id=str(operation_id))
            
        except Exception as e:
            logger.error("Failed to pause progress", error=str(e))
    
    async def resume_progress(self, operation_id: UUID, resume_message: str = "Operation resumed"):
        """Resume paused progress"""
        try:
            current_progress = await self.get_progress(operation_id)
            if current_progress and current_progress["status"] == "paused":
                current_progress["status"] = "running"
                current_progress["message"] = resume_message
                current_progress["current_phase"] = "running"
                current_progress["resumed_at"] = datetime.utcnow().isoformat()
                current_progress["last_updated"] = datetime.utcnow().isoformat()
                
                await self._store_progress(operation_id, current_progress)
                
                logger.info("Progress resumed", operation_id=str(operation_id))
            
        except Exception as e:
            logger.error("Failed to resume progress", error=str(e))
    
    async def get_progress(self, operation_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current progress for an operation"""
        try:
            key = f"{self.progress_key_prefix}{operation_id}"
            data = await self.redis.get(key)
            
            if data:
                progress_data = json.loads(data)
                return progress_data
            
            return None
            
        except Exception as e:
            logger.error("Failed to get progress", error=str(e))
            return None
    
    async def get_multiple_progress(self, operation_ids: List[UUID]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get progress for multiple operations"""
        try:
            results = {}
            
            for operation_id in operation_ids:
                progress = await self.get_progress(operation_id)
                results[str(operation_id)] = progress
            
            return results
            
        except Exception as e:
            logger.error("Failed to get multiple progress", error=str(e))
            return {}
    
    async def list_active_operations(self) -> List[Dict[str, Any]]:
        """List all active operations being tracked"""
        try:
            pattern = f"{self.progress_key_prefix}*"
            keys = await self.redis.keys(pattern)
            
            active_operations = []
            for key in keys:
                data = await self.redis.get(key)
                if data:
                    progress_data = json.loads(data)
                    if progress_data.get("status") in ["running", "paused"]:
                        active_operations.append(progress_data)
            
            # Sort by start time (most recent first)
            active_operations.sort(
                key=lambda x: x.get("started_at", ""), 
                reverse=True
            )
            
            return active_operations
            
        except Exception as e:
            logger.error("Failed to list active operations", error=str(e))
            return []
    
    async def cleanup_expired_progress(self, max_age_hours: int = 24):
        """Clean up expired progress entries"""
        try:
            pattern = f"{self.progress_key_prefix}*"
            keys = await self.redis.keys(pattern)
            
            cleanup_count = 0
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            for key in keys:
                data = await self.redis.get(key)
                if data:
                    progress_data = json.loads(data)
                    
                    # Check if operation is old and completed/failed
                    last_updated = progress_data.get("last_updated")
                    status = progress_data.get("status", "")
                    
                    if last_updated and status in ["completed", "failed", "cancelled"]:
                        update_time = datetime.fromisoformat(last_updated)
                        if update_time < cutoff_time:
                            await self.redis.delete(key)
                            cleanup_count += 1
            
            logger.info(f"Cleaned up {cleanup_count} expired progress entries")
            return cleanup_count
            
        except Exception as e:
            logger.error("Failed to cleanup expired progress", error=str(e))
            return 0
    
    async def get_progress_statistics(self) -> Dict[str, Any]:
        """Get statistics about progress tracking"""
        try:
            pattern = f"{self.progress_key_prefix}*"
            keys = await self.redis.keys(pattern)
            
            stats = {
                "total_operations": len(keys),
                "status_counts": {
                    "running": 0,
                    "paused": 0,
                    "completed": 0,
                    "failed": 0,
                    "cancelled": 0
                },
                "average_progress": 0.0,
                "operations_with_errors": 0,
                "oldest_operation": None,
                "newest_operation": None
            }
            
            if not keys:
                return stats
            
            total_progress = 0
            operation_times = []
            
            for key in keys:
                data = await self.redis.get(key)
                if data:
                    progress_data = json.loads(data)
                    
                    status = progress_data.get("status", "unknown")
                    if status in stats["status_counts"]:
                        stats["status_counts"][status] += 1
                    
                    progress = progress_data.get("progress_percentage", 0)
                    total_progress += progress
                    
                    if progress_data.get("errors"):
                        stats["operations_with_errors"] += 1
                    
                    if progress_data.get("started_at"):
                        operation_times.append(progress_data["started_at"])
            
            if len(keys) > 0:
                stats["average_progress"] = total_progress / len(keys)
            
            if operation_times:
                operation_times.sort()
                stats["oldest_operation"] = operation_times[0]
                stats["newest_operation"] = operation_times[-1]
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get progress statistics", error=str(e))
            return {}
    
    async def cancel_operation(self, operation_id: UUID, cancel_message: str = "Operation cancelled"):
        """Cancel an operation and update its progress"""
        try:
            current_progress = await self.get_progress(operation_id)
            if current_progress and current_progress["status"] in ["running", "paused"]:
                current_progress["status"] = "cancelled"
                current_progress["message"] = cancel_message
                current_progress["current_phase"] = "cancelled"
                current_progress["cancelled_at"] = datetime.utcnow().isoformat()
                current_progress["last_updated"] = datetime.utcnow().isoformat()
                
                await self._store_progress(operation_id, current_progress)
                
                logger.info("Operation cancelled", operation_id=str(operation_id))
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to cancel operation", error=str(e))
            return False
    
    async def add_progress_note(self, operation_id: UUID, note: str, note_type: str = "info"):
        """Add a note to the progress tracking"""
        try:
            current_progress = await self.get_progress(operation_id)
            if current_progress:
                if "notes" not in current_progress:
                    current_progress["notes"] = []
                
                note_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": note_type,
                    "message": note,
                    "phase": current_progress.get("current_phase", "unknown")
                }
                
                current_progress["notes"].append(note_entry)
                
                # Keep only last 50 notes to prevent memory issues
                current_progress["notes"] = current_progress["notes"][-50:]
                
                current_progress["last_updated"] = datetime.utcnow().isoformat()
                
                await self._store_progress(operation_id, current_progress)
                
                logger.debug("Progress note added", operation_id=str(operation_id), note_type=note_type)
            
        except Exception as e:
            logger.error("Failed to add progress note", error=str(e))
    
    async def _store_progress(self, operation_id: UUID, progress_data: Dict[str, Any]):
        """Store progress data in Redis"""
        try:
            key = f"{self.progress_key_prefix}{operation_id}"
            await self.redis.setex(
                key,
                self.progress_ttl,
                json.dumps(progress_data, default=str)
            )
            
            # Publish progress update for real-time streaming
            await self._publish_progress_update(operation_id, progress_data)
            
        except Exception as e:
            logger.error("Failed to store progress data", error=str(e))
            raise
    
    async def _publish_progress_update(self, operation_id: UUID, progress_data: Dict[str, Any]):
        """Publish progress update to Redis for real-time streaming"""
        try:
            # Publish to Redis pub/sub channel for real-time WebSocket updates
            progress_channel = "betty:realtime:progress"
            
            event_data = {
                "operation_id": str(operation_id),
                "timestamp": datetime.utcnow().isoformat(),
                **progress_data
            }
            
            await self.redis.publish(
                progress_channel,
                json.dumps(event_data, default=str)
            )
            
            logger.debug("Progress update published to real-time channel", operation_id=str(operation_id))
            
        except Exception as e:
            logger.error("Failed to publish progress update", error=str(e))
            # Don't raise exception to avoid breaking progress tracking
    
    async def create_progress_stream(self, operation_id: UUID):
        """Create a real-time progress stream for WebSocket connections"""
        try:
            # Get current progress
            current_progress = await self.get_progress(operation_id)
            
            # If progress exists, publish it immediately for new connections
            if current_progress:
                await self._publish_progress_update(operation_id, current_progress)
            
            return current_progress
            
        except Exception as e:
            logger.error("Failed to create progress stream", error=str(e))
            return None