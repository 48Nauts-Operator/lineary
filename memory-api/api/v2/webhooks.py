# ABOUTME: Webhook system API endpoints for event subscriptions and delivery management
# ABOUTME: Handles webhook registration, event publishing, delivery tracking, and retry logic

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import structlog
import httpx
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from core.database import DatabaseManager
from core.dependencies import get_database_manager
from core.security import get_current_user
from models.webhooks import (
    WebhookConfig, WebhookEvent, WebhookDelivery, WebhookSubscription,
    WebhookTestRequest, WebhookTestResult, WebhookStats,
    WebhookRegistrationRequest, WebhookUpdateRequest, WebhookListResponse,
    WebhookDeliveryListResponse, EventType, DeliveryStatus, WebhookStatus,
    generate_webhook_signature, verify_webhook_signature, calculate_next_retry_time,
    should_retry_delivery
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v2/webhooks", tags=["Webhooks v2"])

# Global webhook service instance
webhook_service: Optional['WebhookService'] = None


class WebhookService:
    """Core webhook service for managing webhooks and deliveries"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.webhook_prefix = "betty:webhook:"
        self.delivery_queue = "betty:webhook:deliveries"
        self.retry_queue = "betty:webhook:retries"
        self.stats_prefix = "betty:webhook:stats:"
        
        # HTTP client for webhook deliveries
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Delivery workers
        self.delivery_workers: List[asyncio.Task] = []
        self.is_running = False
    
    async def start(self):
        """Start webhook service workers"""
        try:
            self.is_running = True
            
            # Start delivery workers
            self.delivery_workers = [
                asyncio.create_task(self._delivery_worker(f"worker-{i}"))
                for i in range(3)  # 3 concurrent delivery workers
            ]
            
            # Start retry processor
            self.delivery_workers.append(
                asyncio.create_task(self._retry_processor())
            )
            
            logger.info("Webhook service started with delivery workers")
            
        except Exception as e:
            logger.error("Failed to start webhook service", error=str(e))
            raise
    
    async def stop(self):
        """Stop webhook service workers"""
        try:
            self.is_running = False
            
            # Cancel all workers
            for worker in self.delivery_workers:
                worker.cancel()
                try:
                    await worker
                except asyncio.CancelledError:
                    pass
            
            # Close HTTP client
            await self.http_client.aclose()
            
            logger.info("Webhook service stopped")
            
        except Exception as e:
            logger.error("Error stopping webhook service", error=str(e))
    
    async def register_webhook(self, webhook_data: WebhookRegistrationRequest, user_id: UUID) -> WebhookConfig:
        """Register a new webhook"""
        try:
            # Generate secret if not provided
            secret = webhook_data.secret or self._generate_secret()
            
            webhook = WebhookConfig(
                name=webhook_data.name,
                url=webhook_data.url,
                events=webhook_data.events,
                secret=secret,
                headers=webhook_data.headers,
                timeout_seconds=webhook_data.timeout_seconds,
                retry_attempts=webhook_data.retry_attempts,
                retry_delay_seconds=webhook_data.retry_delay_seconds,
                filters=webhook_data.filters,
                user_id=user_id,
                project_ids=webhook_data.project_ids,
                description=webhook_data.description,
                tags=webhook_data.tags
            )
            
            # Store in Redis
            webhook_key = f"{self.webhook_prefix}{webhook.id}"
            await self.redis.setex(
                webhook_key,
                86400 * 30,  # 30 days TTL
                json.dumps(webhook.dict(), default=str)
            )
            
            # Index by user
            user_webhooks_key = f"betty:user:{user_id}:webhooks"
            await self.redis.sadd(user_webhooks_key, str(webhook.id))
            
            # Index by events
            for event_type in webhook.events:
                event_key = f"betty:webhooks:events:{event_type.value}"
                await self.redis.sadd(event_key, str(webhook.id))
            
            logger.info("Webhook registered", webhook_id=str(webhook.id), user_id=str(user_id))
            return webhook
            
        except Exception as e:
            logger.error("Failed to register webhook", error=str(e))
            raise
    
    async def get_webhook(self, webhook_id: UUID) -> Optional[WebhookConfig]:
        """Get webhook by ID"""
        try:
            webhook_key = f"{self.webhook_prefix}{webhook_id}"
            data = await self.redis.get(webhook_key)
            
            if data:
                webhook_data = json.loads(data)
                return WebhookConfig(**webhook_data)
            
            return None
            
        except Exception as e:
            logger.error("Failed to get webhook", error=str(e))
            return None
    
    async def update_webhook(
        self, 
        webhook_id: UUID, 
        update_data: WebhookUpdateRequest,
        user_id: UUID
    ) -> Optional[WebhookConfig]:
        """Update webhook configuration"""
        try:
            webhook = await self.get_webhook(webhook_id)
            if not webhook:
                return None
            
            # Check ownership
            if webhook.user_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to update this webhook")
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(webhook, field) and value is not None:
                    setattr(webhook, field, value)
            
            webhook.updated_at = datetime.utcnow()
            
            # Re-store in Redis
            webhook_key = f"{self.webhook_prefix}{webhook_id}"
            await self.redis.setex(
                webhook_key,
                86400 * 30,
                json.dumps(webhook.dict(), default=str)
            )
            
            # Update event indexes if events changed
            if update_data.events is not None:
                # Remove from old event indexes
                for event_type in EventType:
                    event_key = f"betty:webhooks:events:{event_type.value}"
                    await self.redis.srem(event_key, str(webhook_id))
                
                # Add to new event indexes
                for event_type in webhook.events:
                    event_key = f"betty:webhooks:events:{event_type.value}"
                    await self.redis.sadd(event_key, str(webhook_id))
            
            logger.info("Webhook updated", webhook_id=str(webhook_id))
            return webhook
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to update webhook", error=str(e))
            raise
    
    async def delete_webhook(self, webhook_id: UUID, user_id: UUID) -> bool:
        """Delete webhook"""
        try:
            webhook = await self.get_webhook(webhook_id)
            if not webhook:
                return False
            
            # Check ownership
            if webhook.user_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to delete this webhook")
            
            # Remove from Redis
            webhook_key = f"{self.webhook_prefix}{webhook_id}"
            await self.redis.delete(webhook_key)
            
            # Remove from user index
            user_webhooks_key = f"betty:user:{user_id}:webhooks"
            await self.redis.srem(user_webhooks_key, str(webhook_id))
            
            # Remove from event indexes
            for event_type in webhook.events:
                event_key = f"betty:webhooks:events:{event_type.value}"
                await self.redis.srem(event_key, str(webhook_id))
            
            # Clean up delivery history
            delivery_pattern = f"betty:delivery:webhook:{webhook_id}:*"
            delivery_keys = await self.redis.keys(delivery_pattern)
            if delivery_keys:
                await self.redis.delete(*delivery_keys)
            
            logger.info("Webhook deleted", webhook_id=str(webhook_id))
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to delete webhook", error=str(e))
            return False
    
    async def list_user_webhooks(self, user_id: UUID, page: int = 1, page_size: int = 20) -> WebhookListResponse:
        """List webhooks for a user"""
        try:
            user_webhooks_key = f"betty:user:{user_id}:webhooks"
            webhook_ids = await self.redis.smembers(user_webhooks_key)
            
            # Convert to UUID list
            webhook_uuids = [UUID(wid) for wid in webhook_ids]
            
            # Paginate
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_ids = webhook_uuids[start_idx:end_idx]
            
            # Fetch webhook data
            webhooks = []
            for webhook_id in paginated_ids:
                webhook = await self.get_webhook(webhook_id)
                if webhook:
                    webhooks.append(webhook)
            
            return WebhookListResponse(
                webhooks=webhooks,
                total_count=len(webhook_uuids),
                page=page,
                page_size=page_size,
                has_more=end_idx < len(webhook_uuids)
            )
            
        except Exception as e:
            logger.error("Failed to list webhooks", error=str(e))
            return WebhookListResponse(
                webhooks=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False
            )
    
    async def publish_event(self, event: WebhookEvent) -> int:
        """Publish event to matching webhooks"""
        try:
            # Find webhooks subscribed to this event type
            event_key = f"betty:webhooks:events:{event.event_type.value}"
            webhook_ids = await self.redis.smembers(event_key)
            
            if not webhook_ids:
                logger.debug("No webhooks subscribed to event", event_type=event.event_type.value)
                return 0
            
            delivered_count = 0
            
            for webhook_id_str in webhook_ids:
                try:
                    webhook_id = UUID(webhook_id_str)
                    webhook = await self.get_webhook(webhook_id)
                    
                    if not webhook or webhook.status != WebhookStatus.ACTIVE:
                        continue
                    
                    # Apply filters
                    if not self._event_matches_filters(event, webhook.filters):
                        continue
                    
                    # Create delivery
                    delivery = await self._create_delivery(webhook, event)
                    
                    # Queue for delivery
                    await self.redis.lpush(
                        self.delivery_queue,
                        json.dumps(delivery.dict(), default=str)
                    )
                    
                    delivered_count += 1
                    
                except Exception as e:
                    logger.error("Error processing webhook for event", error=str(e), webhook_id=webhook_id_str)
                    continue
            
            logger.info("Event published to webhooks", event_type=event.event_type.value, delivered_to=delivered_count)
            return delivered_count
            
        except Exception as e:
            logger.error("Failed to publish event", error=str(e))
            return 0
    
    async def test_webhook(self, test_request: WebhookTestRequest) -> WebhookTestResult:
        """Test webhook endpoint with sample payload"""
        try:
            start_time = time.time()
            
            # Create test event
            test_event = WebhookEvent(
                event_type=test_request.event_type,
                source="betty-memory-api-test",
                data=test_request.test_data or {"test": True},
                metadata={"test_mode": True}
            )
            
            # Prepare payload
            payload = json.dumps(test_event.dict(), default=str)
            
            # Generate signature if secret provided
            signature = None
            if test_request.secret:
                signature = generate_webhook_signature(payload, test_request.secret)
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "BETTY-Memory-API/1.0 Webhook-Test",
                "X-Webhook-Event": test_event.event_type.value,
                "X-Webhook-Timestamp": str(int(time.time())),
                **test_request.headers
            }
            
            if signature:
                headers["X-Webhook-Signature"] = signature
            
            # Make request
            try:
                response = await self.http_client.post(
                    str(test_request.url),
                    content=payload,
                    headers=headers,
                    timeout=test_request.timeout_seconds
                )
                
                response_time_ms = (time.time() - start_time) * 1000
                
                # Verify signature if echo header present
                signature_valid = None
                if test_request.secret and "X-Echo-Signature" in response.headers:
                    echo_signature = response.headers["X-Echo-Signature"]
                    signature_valid = verify_webhook_signature(payload, test_request.secret, echo_signature)
                
                return WebhookTestResult(
                    success=200 <= response.status_code < 300,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    response_headers=dict(response.headers),
                    response_body=response.text[:1000],  # Truncate large responses
                    signature_valid=signature_valid
                )
                
            except httpx.TimeoutException:
                response_time_ms = (time.time() - start_time) * 1000
                return WebhookTestResult(
                    success=False,
                    response_time_ms=response_time_ms,
                    error_message="Request timeout"
                )
            
            except httpx.RequestError as e:
                response_time_ms = (time.time() - start_time) * 1000
                return WebhookTestResult(
                    success=False,
                    response_time_ms=response_time_ms,
                    error_message=f"Network error: {str(e)}"
                )
                
        except Exception as e:
            logger.error("Webhook test failed", error=str(e))
            return WebhookTestResult(
                success=False,
                response_time_ms=0.0,
                error_message=f"Test failed: {str(e)}"
            )
    
    async def get_webhook_stats(self, webhook_id: UUID) -> WebhookStats:
        """Get webhook statistics"""
        try:
            stats_key = f"{self.stats_prefix}{webhook_id}"
            stats_data = await self.redis.hgetall(stats_key)
            
            if not stats_data:
                # Return empty stats
                return WebhookStats(webhook_id=webhook_id)
            
            # Parse stats
            stats = WebhookStats(
                webhook_id=webhook_id,
                total_events=int(stats_data.get("total_events", 0)),
                successful_deliveries=int(stats_data.get("successful_deliveries", 0)),
                failed_deliveries=int(stats_data.get("failed_deliveries", 0)),
                pending_deliveries=int(stats_data.get("pending_deliveries", 0)),
                average_response_time_ms=float(stats_data.get("average_response_time_ms", 0)) if stats_data.get("average_response_time_ms") else None,
                success_rate_percentage=float(stats_data.get("success_rate_percentage", 0)),
                events_last_24h=int(stats_data.get("events_last_24h", 0)),
                events_last_7d=int(stats_data.get("events_last_7d", 0)),
                events_last_30d=int(stats_data.get("events_last_30d", 0))
            )
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get webhook stats", error=str(e))
            return WebhookStats(webhook_id=webhook_id)
    
    # Private methods
    
    def _generate_secret(self) -> str:
        """Generate random webhook secret"""
        import secrets
        return secrets.token_hex(32)
    
    def _event_matches_filters(self, event: WebhookEvent, filters: Dict[str, Any]) -> bool:
        """Check if event matches webhook filters"""
        try:
            if not filters:
                return True
            
            # User ID filter
            if "user_ids" in filters and event.user_id:
                if str(event.user_id) not in filters["user_ids"]:
                    return False
            
            # Session ID filter
            if "session_ids" in filters and event.session_id:
                if str(event.session_id) not in filters["session_ids"]:
                    return False
            
            # Project ID filter
            if "project_ids" in filters and event.project_id:
                if str(event.project_id) not in filters["project_ids"]:
                    return False
            
            # Custom filters
            for filter_key, filter_value in filters.items():
                if filter_key.startswith("data."):
                    # Filter on event data
                    data_key = filter_key[5:]  # Remove "data." prefix
                    if data_key in event.data:
                        if event.data[data_key] != filter_value:
                            return False
            
            return True
            
        except Exception as e:
            logger.error("Error applying event filters", error=str(e))
            return True  # Default to allow on filter error
    
    async def _create_delivery(self, webhook: WebhookConfig, event: WebhookEvent) -> WebhookDelivery:
        """Create delivery record"""
        payload = json.dumps(event.dict(), default=str)
        signature = generate_webhook_signature(payload, webhook.secret)
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BETTY-Memory-API/2.0 Webhook",
            "X-Webhook-Event": event.event_type.value,
            "X-Webhook-Timestamp": str(int(time.time())),
            "X-Webhook-Signature": signature,
            **webhook.headers
        }
        
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_id=event.id,
            url=str(webhook.url),
            headers=headers,
            payload=payload,
            signature=signature
        )
        
        return delivery
    
    async def _delivery_worker(self, worker_name: str):
        """Webhook delivery worker"""
        logger.info("Webhook delivery worker started", worker=worker_name)
        
        while self.is_running:
            try:
                # Get delivery from queue (blocking with timeout)
                delivery_data = await self.redis.brpop(self.delivery_queue, timeout=5)
                
                if not delivery_data:
                    continue  # Timeout, continue loop
                
                # Parse delivery
                delivery_json = delivery_data[1]
                delivery_dict = json.loads(delivery_json)
                delivery = WebhookDelivery(**delivery_dict)
                
                # Process delivery
                await self._process_delivery(delivery)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in delivery worker", error=str(e), worker=worker_name)
                await asyncio.sleep(1)  # Brief pause on error
        
        logger.info("Webhook delivery worker stopped", worker=worker_name)
    
    async def _process_delivery(self, delivery: WebhookDelivery):
        """Process single webhook delivery"""
        try:
            delivery.attempted_at = datetime.utcnow()
            
            # Make HTTP request
            start_time = time.time()
            
            try:
                response = await self.http_client.post(
                    delivery.url,
                    content=delivery.payload,
                    headers=delivery.headers,
                    timeout=30.0  # Could be configurable per webhook
                )
                
                response_time_ms = (time.time() - start_time) * 1000
                
                # Update delivery record
                delivery.response_status_code = response.status_code
                delivery.response_headers = dict(response.headers)
                delivery.response_body = response.text[:1000]  # Truncate
                delivery.response_time_ms = response_time_ms
                delivery.completed_at = datetime.utcnow()
                
                # Determine success
                if 200 <= response.status_code < 300:
                    delivery.status = DeliveryStatus.SUCCESS
                    await self._update_webhook_stats(delivery.webhook_id, "success", response_time_ms)
                else:
                    delivery.status = DeliveryStatus.FAILED
                    delivery.error_message = f"HTTP {response.status_code}"
                    await self._update_webhook_stats(delivery.webhook_id, "failed")
                    
                    # Schedule retry if appropriate
                    webhook = await self.get_webhook(delivery.webhook_id)
                    if webhook and should_retry_delivery(response.status_code, delivery.retry_count, webhook.retry_attempts):
                        await self._schedule_retry(delivery, webhook)
                
            except httpx.TimeoutException:
                response_time_ms = (time.time() - start_time) * 1000
                delivery.status = DeliveryStatus.FAILED
                delivery.error_message = "Request timeout"
                delivery.response_time_ms = response_time_ms
                delivery.completed_at = datetime.utcnow()
                
                await self._update_webhook_stats(delivery.webhook_id, "failed")
                
                # Schedule retry
                webhook = await self.get_webhook(delivery.webhook_id)
                if webhook and delivery.retry_count < webhook.retry_attempts:
                    await self._schedule_retry(delivery, webhook)
            
            except httpx.RequestError as e:
                response_time_ms = (time.time() - start_time) * 1000
                delivery.status = DeliveryStatus.FAILED
                delivery.error_message = f"Network error: {str(e)}"
                delivery.response_time_ms = response_time_ms
                delivery.completed_at = datetime.utcnow()
                
                await self._update_webhook_stats(delivery.webhook_id, "failed")
                
                # Schedule retry
                webhook = await self.get_webhook(delivery.webhook_id)
                if webhook and delivery.retry_count < webhook.retry_attempts:
                    await self._schedule_retry(delivery, webhook)
            
            # Store delivery record
            await self._store_delivery(delivery)
            
        except Exception as e:
            logger.error("Error processing webhook delivery", error=str(e))
    
    async def _schedule_retry(self, delivery: WebhookDelivery, webhook: WebhookConfig):
        """Schedule delivery retry"""
        try:
            delivery.retry_count += 1
            delivery.status = DeliveryStatus.RETRYING
            delivery.next_retry_at = calculate_next_retry_time(
                delivery.retry_count,
                webhook.retry_delay_seconds,
                webhook.exponential_backoff
            )
            
            # Add to retry queue with delay
            retry_data = {
                "delivery": delivery.dict(),
                "retry_at": delivery.next_retry_at.timestamp()
            }
            
            await self.redis.zadd(
                self.retry_queue,
                {json.dumps(retry_data, default=str): delivery.next_retry_at.timestamp()}
            )
            
            logger.debug("Delivery retry scheduled", delivery_id=str(delivery.id), retry_count=delivery.retry_count)
            
        except Exception as e:
            logger.error("Failed to schedule delivery retry", error=str(e))
    
    async def _retry_processor(self):
        """Process retry queue"""
        logger.info("Webhook retry processor started")
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Get retries that are ready
                retries = await self.redis.zrangebyscore(
                    self.retry_queue,
                    0,
                    current_time,
                    withscores=False
                )
                
                for retry_json in retries:
                    try:
                        retry_data = json.loads(retry_json)
                        delivery_dict = retry_data["delivery"]
                        delivery = WebhookDelivery(**delivery_dict)
                        
                        # Re-queue for delivery
                        await self.redis.lpush(
                            self.delivery_queue,
                            json.dumps(delivery.dict(), default=str)
                        )
                        
                        # Remove from retry queue
                        await self.redis.zrem(self.retry_queue, retry_json)
                        
                    except Exception as e:
                        logger.error("Error processing retry", error=str(e))
                        # Remove problematic retry
                        await self.redis.zrem(self.retry_queue, retry_json)
                
                # Sleep before next check
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in retry processor", error=str(e))
                await asyncio.sleep(5)
        
        logger.info("Webhook retry processor stopped")
    
    async def _store_delivery(self, delivery: WebhookDelivery):
        """Store delivery record"""
        try:
            delivery_key = f"betty:delivery:{delivery.id}"
            await self.redis.setex(
                delivery_key,
                86400 * 7,  # 7 days TTL
                json.dumps(delivery.dict(), default=str)
            )
            
            # Index by webhook
            webhook_deliveries_key = f"betty:webhook:{delivery.webhook_id}:deliveries"
            await self.redis.lpush(webhook_deliveries_key, str(delivery.id))
            
            # Trim to keep last 1000 deliveries per webhook
            await self.redis.ltrim(webhook_deliveries_key, 0, 999)
            
        except Exception as e:
            logger.error("Failed to store delivery record", error=str(e))
    
    async def _update_webhook_stats(self, webhook_id: UUID, result: str, response_time_ms: Optional[float] = None):
        """Update webhook statistics"""
        try:
            stats_key = f"{self.stats_prefix}{webhook_id}"
            
            # Update counters
            await self.redis.hincrby(stats_key, "total_events", 1)
            
            if result == "success":
                await self.redis.hincrby(stats_key, "successful_deliveries", 1)
                await self.redis.hset(stats_key, "last_success", datetime.utcnow().isoformat())
                
                if response_time_ms:
                    # Update average response time
                    current_avg = await self.redis.hget(stats_key, "average_response_time_ms")
                    current_count = await self.redis.hget(stats_key, "successful_deliveries")
                    
                    if current_avg and current_count:
                        current_avg = float(current_avg)
                        current_count = int(current_count)
                        new_avg = ((current_avg * (current_count - 1)) + response_time_ms) / current_count
                        await self.redis.hset(stats_key, "average_response_time_ms", new_avg)
                    else:
                        await self.redis.hset(stats_key, "average_response_time_ms", response_time_ms)
            
            elif result == "failed":
                await self.redis.hincrby(stats_key, "failed_deliveries", 1)
                await self.redis.hset(stats_key, "last_failure", datetime.utcnow().isoformat())
            
            # Update success rate
            successful = int(await self.redis.hget(stats_key, "successful_deliveries") or 0)
            failed = int(await self.redis.hget(stats_key, "failed_deliveries") or 0)
            total = successful + failed
            
            if total > 0:
                success_rate = (successful / total) * 100
                await self.redis.hset(stats_key, "success_rate_percentage", success_rate)
            
            # Set TTL for stats
            await self.redis.expire(stats_key, 86400 * 30)  # 30 days
            
        except Exception as e:
            logger.error("Failed to update webhook stats", error=str(e))


def get_webhook_service() -> WebhookService:
    """Get webhook service instance"""
    global webhook_service
    if not webhook_service:
        raise HTTPException(status_code=503, detail="Webhook service not available")
    return webhook_service


async def init_webhook_service(redis_client: redis.Redis):
    """Initialize webhook service"""
    global webhook_service
    try:
        webhook_service = WebhookService(redis_client)
        await webhook_service.start()
        logger.info("Webhook service initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize webhook service", error=str(e))
        raise


# API Endpoints

@router.post("/register", response_model=WebhookConfig)
async def register_webhook(
    webhook_data: WebhookRegistrationRequest,
    current_user = Depends(get_current_user)
):
    """Register a new webhook"""
    try:
        webhook_svc = get_webhook_service()
        webhook = await webhook_svc.register_webhook(webhook_data, current_user["user_id"])
        
        return webhook
        
    except Exception as e:
        logger.error("Failed to register webhook", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to register webhook")


@router.get("/list", response_model=WebhookListResponse)
async def list_webhooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """List user's webhooks"""
    try:
        webhook_svc = get_webhook_service()
        response = await webhook_svc.list_user_webhooks(current_user["user_id"], page, page_size)
        
        return response
        
    except Exception as e:
        logger.error("Failed to list webhooks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list webhooks")


@router.get("/{webhook_id}", response_model=WebhookConfig)
async def get_webhook(
    webhook_id: UUID,
    current_user = Depends(get_current_user)
):
    """Get webhook details"""
    try:
        webhook_svc = get_webhook_service()
        webhook = await webhook_svc.get_webhook(webhook_id)
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Check ownership
        if webhook.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        return webhook
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get webhook", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get webhook")


@router.put("/{webhook_id}", response_model=WebhookConfig)
async def update_webhook(
    webhook_id: UUID,
    update_data: WebhookUpdateRequest,
    current_user = Depends(get_current_user)
):
    """Update webhook configuration"""
    try:
        webhook_svc = get_webhook_service()
        webhook = await webhook_svc.update_webhook(webhook_id, update_data, current_user["user_id"])
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        return webhook
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update webhook", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update webhook")


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    current_user = Depends(get_current_user)
):
    """Delete webhook"""
    try:
        webhook_svc = get_webhook_service()
        success = await webhook_svc.delete_webhook(webhook_id, current_user["user_id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        return JSONResponse(content={
            "success": True,
            "message": "Webhook deleted successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete webhook", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete webhook")


@router.post("/test", response_model=WebhookTestResult)
async def test_webhook_endpoint(
    test_request: WebhookTestRequest,
    current_user = Depends(get_current_user)
):
    """Test webhook endpoint"""
    try:
        webhook_svc = get_webhook_service()
        result = await webhook_svc.test_webhook(test_request)
        
        return result
        
    except Exception as e:
        logger.error("Failed to test webhook", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to test webhook")


@router.get("/{webhook_id}/stats", response_model=WebhookStats)
async def get_webhook_statistics(
    webhook_id: UUID,
    current_user = Depends(get_current_user)
):
    """Get webhook statistics"""
    try:
        webhook_svc = get_webhook_service()
        
        # Check webhook ownership
        webhook = await webhook_svc.get_webhook(webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        if webhook.user_id != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        stats = await webhook_svc.get_webhook_stats(webhook_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get webhook stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get webhook statistics")


@router.post("/publish")
async def publish_webhook_event(
    event_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Publish event to webhooks (admin/system use)"""
    try:
        # This endpoint could be restricted to admin users or system services
        event_type = EventType(event_data.get("event_type"))
        
        event = WebhookEvent(
            event_type=event_type,
            source="betty-memory-api",
            data=event_data.get("data", {}),
            metadata=event_data.get("metadata", {}),
            user_id=current_user["user_id"]
        )
        
        webhook_svc = get_webhook_service()
        
        # Publish in background
        background_tasks.add_task(webhook_svc.publish_event, event)
        
        return JSONResponse(content={
            "success": True,
            "message": "Event published to webhooks",
            "event_id": str(event.id)
        })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {str(e)}")
    except Exception as e:
        logger.error("Failed to publish webhook event", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to publish event")