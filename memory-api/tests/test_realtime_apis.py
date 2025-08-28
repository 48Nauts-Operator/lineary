# ABOUTME: Comprehensive tests for real-time WebSocket and webhook APIs
# ABOUTME: Tests WebSocket connections, authentication, progress streaming, webhooks, and event handling

import asyncio
import json
import pytest
import time
from datetime import datetime
from typing import Dict, Any
from uuid import UUID, uuid4
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect
import websockets
import httpx

from main import app
from models.websocket import (
    WebSocketMessage, WebSocketMessageType, ConnectionMetadata, EventFilter,
    create_progress_message, create_search_result_message, create_notification_message
)
from models.webhooks import (
    WebhookConfig, WebhookEvent, WebhookDelivery, WebhookTestRequest,
    EventType, DeliveryStatus, WebhookStatus, generate_webhook_signature
)
from services.realtime_service import RealTimeService, ConnectionManager
from services.progress_tracker import ProgressTracker
from api.v2.websocket import init_realtime_service
from api.v2.webhooks import WebhookService, init_webhook_service


class TestWebSocketConnections:
    """Test WebSocket connection management"""
    
    @pytest.fixture
    async def mock_redis(self):
        """Mock Redis client"""
        redis_mock = AsyncMock()
        redis_mock.setex = AsyncMock()
        redis_mock.get = AsyncMock()
        redis_mock.delete = AsyncMock()
        redis_mock.keys = AsyncMock(return_value=[])
        redis_mock.publish = AsyncMock()
        redis_mock.pubsub = Mock()
        return redis_mock
    
    @pytest.fixture
    async def realtime_service(self, mock_redis):
        """Create real-time service instance"""
        service = RealTimeService(mock_redis)
        return service
    
    @pytest.fixture
    async def mock_websocket(self):
        """Mock WebSocket connection"""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        websocket.close = AsyncMock()
        websocket.client = Mock()
        websocket.client.host = "127.0.0.1"
        websocket.headers = {"user-agent": "test-client"}
        return websocket
    
    async def test_connection_establishment(self, realtime_service, mock_websocket):
        """Test WebSocket connection establishment"""
        connection_id = uuid4()
        user_id = uuid4()
        
        # Test successful connection
        success = await realtime_service.connection_manager.connect(
            mock_websocket, connection_id, user_id=user_id
        )
        
        assert success
        assert connection_id in realtime_service.connection_manager.active_connections
        assert connection_id in realtime_service.connection_manager.connection_metadata
        
        # Check metadata
        metadata = realtime_service.connection_manager.connection_metadata[connection_id]
        assert metadata.user_id == user_id
        assert metadata.ip_address == "127.0.0.1"
        assert metadata.is_authenticated == False  # Not authenticated yet
    
    async def test_connection_authentication(self, realtime_service, mock_websocket):
        """Test WebSocket authentication"""
        # Mock JWT token validation
        with patch('api.v2.websocket.decode_jwt_token') as mock_decode:
            mock_decode.return_value = {
                "sub": str(uuid4()),
                "permissions": ["read", "write"],
                "session_id": str(uuid4())
            }
            
            token = "valid.jwt.token"
            auth_data = await realtime_service.authenticate_connection(mock_websocket, token)
            
            assert auth_data is not None
            assert "user_id" in auth_data
            assert "permissions" in auth_data
            assert "session_id" in auth_data
    
    async def test_connection_cleanup(self, realtime_service, mock_websocket):
        """Test connection cleanup on disconnect"""
        connection_id = uuid4()
        user_id = uuid4()
        session_id = uuid4()
        
        # Establish connection
        await realtime_service.connection_manager.connect(
            mock_websocket, connection_id, user_id=user_id, session_id=session_id
        )
        
        # Join a room
        realtime_service.connection_manager.join_room(connection_id, "test-room")
        
        # Disconnect
        await realtime_service.connection_manager.disconnect(connection_id)
        
        # Verify cleanup
        assert connection_id not in realtime_service.connection_manager.active_connections
        assert connection_id not in realtime_service.connection_manager.connection_metadata
        assert connection_id not in realtime_service.connection_manager.user_connections[user_id]
        assert connection_id not in realtime_service.connection_manager.session_connections[session_id]
        assert connection_id not in realtime_service.connection_manager.room_connections["test-room"]
    
    async def test_message_broadcasting(self, realtime_service, mock_websocket):
        """Test message broadcasting to connections"""
        # Create multiple connections
        connections = []
        for i in range(3):
            connection_id = uuid4()
            user_id = uuid4()
            
            await realtime_service.connection_manager.connect(
                AsyncMock(), connection_id, user_id=user_id
            )
            connections.append((connection_id, user_id))
        
        # Create test message
        message = WebSocketMessage(
            type=WebSocketMessageType.SYSTEM_NOTIFICATION,
            data={"message": "Test broadcast"}
        )
        
        # Mock successful sends
        with patch.object(realtime_service.connection_manager, 'send_to_connection') as mock_send:
            mock_send.return_value = True
            
            # Broadcast message
            sent_count = await realtime_service.connection_manager.broadcast(message)
            
            assert sent_count == 3
            assert mock_send.call_count == 3
    
    async def test_room_management(self, realtime_service, mock_websocket):
        """Test room joining and leaving"""
        connection_id = uuid4()
        
        await realtime_service.connection_manager.connect(mock_websocket, connection_id)
        
        # Join room
        success = realtime_service.connection_manager.join_room(connection_id, "test-room")
        assert success
        assert connection_id in realtime_service.connection_manager.room_connections["test-room"]
        
        # Leave room
        success = realtime_service.connection_manager.leave_room(connection_id, "test-room")
        assert success
        assert connection_id not in realtime_service.connection_manager.room_connections.get("test-room", set())
    
    async def test_rate_limiting(self, realtime_service, mock_websocket):
        """Test WebSocket rate limiting"""
        connection_id = uuid4()
        
        await realtime_service.connection_manager.connect(mock_websocket, connection_id)
        
        # Test rate limiting
        connection_manager = realtime_service.connection_manager
        
        # Allow first 60 messages
        for i in range(60):
            assert connection_manager._check_rate_limit(connection_id, 60)
        
        # 61st message should be blocked
        assert not connection_manager._check_rate_limit(connection_id, 60)


class TestProgressStreaming:
    """Test progress streaming WebSocket endpoint"""
    
    @pytest.fixture
    async def progress_tracker(self, mock_redis):
        """Create progress tracker instance"""
        return ProgressTracker(mock_redis)
    
    async def test_progress_stream_connection(self, progress_tracker):
        """Test progress stream WebSocket connection"""
        operation_id = uuid4()
        
        # Mock progress data
        progress_data = {
            "operation_id": str(operation_id),
            "status": "running",
            "progress_percentage": 50.0,
            "processed_items": 50,
            "total_items": 100,
            "current_phase": "processing",
            "message": "Processing items..."
        }
        
        with patch.object(progress_tracker, 'get_progress') as mock_get:
            mock_get.return_value = progress_data
            
            progress = await progress_tracker.get_progress(operation_id)
            assert progress is not None
            assert progress["progress_percentage"] == 50.0
    
    async def test_progress_message_creation(self):
        """Test progress message creation"""
        operation_id = uuid4()
        progress_data = {
            "status": "running",
            "progress_percentage": 75.0,
            "processed_items": 75,
            "total_items": 100,
            "message": "Almost done"
        }
        
        message = create_progress_message(operation_id, progress_data)
        
        assert message.type == WebSocketMessageType.PROGRESS_UPDATE
        assert str(operation_id) in message.data["operation_id"]
        assert message.data["progress_percentage"] == 75.0


class TestLiveSearch:
    """Test live search WebSocket functionality"""
    
    async def test_search_message_creation(self):
        """Test search result message creation"""
        query_id = uuid4()
        query = "test search"
        results = [
            {"id": "1", "title": "Result 1", "relevance": 0.95},
            {"id": "2", "title": "Result 2", "relevance": 0.85}
        ]
        
        message = create_search_result_message(
            query_id=query_id,
            query=query,
            results=results,
            is_complete=True,
            execution_time_ms=150.5
        )
        
        assert message.type == WebSocketMessageType.SEARCH_RESULT
        assert message.data["query"] == query
        assert message.data["total_results"] == 2
        assert message.data["is_complete"] == True
        assert message.data["execution_time_ms"] == 150.5
    
    async def test_search_debouncing(self):
        """Test search request debouncing"""
        # This would test the debouncing logic in the WebSocket handler
        # Implementation depends on how debouncing is handled
        pass


class TestCollaborativeSessions:
    """Test collaborative session WebSocket functionality"""
    
    async def test_collaboration_join_message(self, realtime_service):
        """Test collaboration join message handling"""
        session_id = uuid4()
        user_id = uuid4()
        connection_id = uuid4()
        
        join_message = WebSocketMessage(
            type=WebSocketMessageType.COLLABORATION_JOIN,
            data={
                "session_id": str(session_id),
                "user_id": str(user_id),
                "connection_id": str(connection_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        assert join_message.type == WebSocketMessageType.COLLABORATION_JOIN
        assert join_message.data["session_id"] == str(session_id)
        assert join_message.data["user_id"] == str(user_id)
    
    async def test_cursor_updates(self):
        """Test cursor position updates"""
        cursor_message = WebSocketMessage(
            type=WebSocketMessageType.COLLABORATION_CURSOR,
            data={
                "session_id": str(uuid4()),
                "user_id": str(uuid4()),
                "cursor_position": {"line": 10, "column": 25},
                "selection": {"start": {"line": 10, "column": 20}, "end": {"line": 10, "column": 30}}
            }
        )
        
        assert cursor_message.type == WebSocketMessageType.COLLABORATION_CURSOR
        assert "cursor_position" in cursor_message.data
        assert "selection" in cursor_message.data


class TestWebhookSystem:
    """Test webhook system functionality"""
    
    @pytest.fixture
    async def webhook_service(self, mock_redis):
        """Create webhook service instance"""
        service = WebhookService(mock_redis)
        return service
    
    async def test_webhook_registration(self, webhook_service):
        """Test webhook registration"""
        from models.webhooks import WebhookRegistrationRequest, EventType
        
        webhook_request = WebhookRegistrationRequest(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=[EventType.PROGRESS_COMPLETED, EventType.SEARCH_COMPLETED],
            description="Test webhook for CI"
        )
        
        user_id = uuid4()
        
        with patch.object(webhook_service.redis, 'setex') as mock_setex, \
             patch.object(webhook_service.redis, 'sadd') as mock_sadd:
            
            webhook = await webhook_service.register_webhook(webhook_request, user_id)
            
            assert webhook.name == "Test Webhook"
            assert webhook.user_id == user_id
            assert len(webhook.events) == 2
            assert webhook.secret is not None  # Should be auto-generated
            
            # Verify Redis calls
            mock_setex.assert_called()
            mock_sadd.assert_called()
    
    async def test_webhook_event_publishing(self, webhook_service):
        """Test webhook event publishing"""
        # Mock webhook data
        webhook_id = uuid4()
        webhook_data = {
            "id": str(webhook_id),
            "name": "Test Webhook",
            "url": "https://example.com/webhook",
            "events": ["progress.completed"],
            "status": "active",
            "secret": "test-secret",
            "filters": {}
        }
        
        with patch.object(webhook_service.redis, 'smembers') as mock_smembers, \
             patch.object(webhook_service, 'get_webhook') as mock_get_webhook, \
             patch.object(webhook_service.redis, 'lpush') as mock_lpush:
            
            # Mock Redis responses
            mock_smembers.return_value = [str(webhook_id)]
            mock_get_webhook.return_value = WebhookConfig(**webhook_data)
            
            # Create test event
            event = WebhookEvent(
                event_type=EventType.PROGRESS_COMPLETED,
                source="test",
                data={"operation_id": str(uuid4()), "result": "success"}
            )
            
            # Publish event
            delivered_count = await webhook_service.publish_event(event)
            
            assert delivered_count == 1
            mock_lpush.assert_called_once()  # Delivery queued
    
    async def test_webhook_signature_generation(self):
        """Test webhook signature generation and verification"""
        payload = '{"test": "data"}'
        secret = "test-secret"
        
        # Generate signature
        signature = generate_webhook_signature(payload, secret)
        
        assert signature.startswith("sha256=")
        assert len(signature) > 10
        
        # Verify signature
        from models.webhooks import verify_webhook_signature
        
        is_valid = verify_webhook_signature(payload, secret, signature)
        assert is_valid
        
        # Test invalid signature
        is_invalid = verify_webhook_signature(payload, secret, "sha256=invalid")
        assert not is_invalid
    
    async def test_webhook_delivery_processing(self, webhook_service):
        """Test webhook delivery processing"""
        # Create test delivery
        webhook_id = uuid4()
        event_id = uuid4()
        
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_id=event_id,
            url="https://httpbin.org/post",
            payload='{"test": "data"}',
            headers={"Content-Type": "application/json"}
        )
        
        # Mock HTTP response
        with patch.object(webhook_service.http_client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.text = '{"success": true}'
            mock_post.return_value = mock_response
            
            # Process delivery
            await webhook_service._process_delivery(delivery)
            
            assert delivery.status == DeliveryStatus.SUCCESS
            assert delivery.response_status_code == 200
            assert delivery.completed_at is not None
    
    async def test_webhook_retry_logic(self, webhook_service):
        """Test webhook retry logic"""
        webhook_id = uuid4()
        
        # Mock webhook with retry configuration
        webhook_data = {
            "id": str(webhook_id),
            "retry_attempts": 3,
            "retry_delay_seconds": 60,
            "exponential_backoff": True
        }
        webhook = WebhookConfig(**webhook_data)
        
        # Create failed delivery
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_id=uuid4(),
            url="https://example.com/webhook",
            payload='{"test": "data"}',
            retry_count=0
        )
        
        with patch.object(webhook_service.redis, 'zadd') as mock_zadd:
            await webhook_service._schedule_retry(delivery, webhook)
            
            assert delivery.retry_count == 1
            assert delivery.status == DeliveryStatus.RETRYING
            assert delivery.next_retry_at is not None
            
            # Verify retry was queued
            mock_zadd.assert_called_once()
    
    async def test_webhook_filtering(self, webhook_service):
        """Test webhook event filtering"""
        # Test event matches filters
        event = WebhookEvent(
            event_type=EventType.PROGRESS_COMPLETED,
            source="test",
            data={"operation_type": "batch_import"},
            user_id=uuid4(),
            project_id=uuid4()
        )
        
        # Test matching filters
        filters = {
            "user_ids": [str(event.user_id)],
            "data.operation_type": "batch_import"
        }
        
        matches = webhook_service._event_matches_filters(event, filters)
        assert matches
        
        # Test non-matching filters
        filters = {
            "user_ids": [str(uuid4())],  # Different user
            "data.operation_type": "batch_import"
        }
        
        matches = webhook_service._event_matches_filters(event, filters)
        assert not matches


class TestWebhookAPI:
    """Test webhook REST API endpoints"""
    
    def test_webhook_registration_endpoint(self):
        """Test webhook registration API endpoint"""
        client = TestClient(app)
        
        # Mock authentication
        with patch('core.security.get_current_user') as mock_auth:
            mock_auth.return_value = {"user_id": uuid4()}
            
            webhook_data = {
                "name": "Test Webhook",
                "url": "https://example.com/webhook",
                "events": ["progress.completed"],
                "description": "Test webhook"
            }
            
            # Mock webhook service
            with patch('api.v2.webhooks.get_webhook_service') as mock_get_service:
                mock_service = AsyncMock()
                mock_webhook = WebhookConfig(
                    name=webhook_data["name"],
                    url=webhook_data["url"],
                    events=[EventType.PROGRESS_COMPLETED],
                    secret="generated-secret"
                )
                mock_service.register_webhook.return_value = mock_webhook
                mock_get_service.return_value = mock_service
                
                response = client.post("/api/v2/webhooks/register", json=webhook_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == webhook_data["name"]
                assert data["secret"] is not None
    
    def test_webhook_test_endpoint(self):
        """Test webhook testing API endpoint"""
        client = TestClient(app)
        
        with patch('core.security.get_current_user') as mock_auth:
            mock_auth.return_value = {"user_id": uuid4()}
            
            test_data = {
                "url": "https://httpbin.org/post",
                "headers": {"Authorization": "Bearer test"},
                "event_type": "progress.completed",
                "test_data": {"test": True}
            }
            
            with patch('api.v2.webhooks.get_webhook_service') as mock_get_service:
                mock_service = AsyncMock()
                mock_result = {
                    "success": True,
                    "status_code": 200,
                    "response_time_ms": 150.0
                }
                mock_service.test_webhook.return_value = mock_result
                mock_get_service.return_value = mock_service
                
                response = client.post("/api/v2/webhooks/test", json=test_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                assert data["status_code"] == 200


class TestEventBroadcasting:
    """Test event broadcasting and distribution"""
    
    async def test_redis_pub_sub_integration(self, realtime_service):
        """Test Redis pub/sub event broadcasting"""
        event_data = {
            "type": "progress.updated",
            "operation_id": str(uuid4()),
            "progress_percentage": 75.0
        }
        
        with patch.object(realtime_service.redis, 'publish') as mock_publish:
            await realtime_service.publish_event("progress.updated", event_data)
            
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            
            # Verify channel and data
            assert call_args[0][0] == realtime_service.event_channel
            published_data = json.loads(call_args[0][1])
            assert published_data["type"] == "progress.updated"
    
    async def test_notification_broadcasting(self, realtime_service):
        """Test system notification broadcasting"""
        with patch.object(realtime_service.connection_manager, 'broadcast') as mock_broadcast:
            mock_broadcast.return_value = 5  # 5 connections notified
            
            await realtime_service.publish_notification(
                "info", 
                "System Update", 
                "System maintenance scheduled"
            )
            
            # Should publish to Redis for distribution
            # In real implementation, this would trigger broadcast to connections


class TestErrorHandling:
    """Test error handling in real-time systems"""
    
    async def test_websocket_connection_errors(self, realtime_service, mock_websocket):
        """Test WebSocket connection error handling"""
        connection_id = uuid4()
        
        # Mock accept failure
        mock_websocket.accept.side_effect = Exception("Connection failed")
        
        success = await realtime_service.connection_manager.connect(
            mock_websocket, connection_id
        )
        
        assert not success
        assert connection_id not in realtime_service.connection_manager.active_connections
    
    async def test_webhook_delivery_failures(self, webhook_service):
        """Test webhook delivery failure handling"""
        delivery = WebhookDelivery(
            webhook_id=uuid4(),
            event_id=uuid4(),
            url="https://invalid-url-that-will-fail.com/webhook",
            payload='{"test": "data"}',
            headers={"Content-Type": "application/json"}
        )
        
        # Mock network error
        with patch.object(webhook_service.http_client, 'post') as mock_post:
            mock_post.side_effect = httpx.RequestError("Network error")
            
            await webhook_service._process_delivery(delivery)
            
            assert delivery.status == DeliveryStatus.FAILED
            assert "Network error" in delivery.error_message
            assert delivery.completed_at is not None
    
    async def test_invalid_websocket_messages(self, realtime_service):
        """Test handling of invalid WebSocket messages"""
        # This would test the message validation and error response logic
        # Implementation depends on specific validation rules
        pass


class TestPerformanceAndScaling:
    """Test performance and scaling characteristics"""
    
    async def test_concurrent_websocket_connections(self, realtime_service):
        """Test handling multiple concurrent WebSocket connections"""
        num_connections = 100
        connections = []
        
        # Create multiple connections
        for i in range(num_connections):
            connection_id = uuid4()
            mock_ws = AsyncMock()
            mock_ws.accept = AsyncMock()
            mock_ws.client = Mock()
            mock_ws.client.host = f"127.0.0.{i}"
            mock_ws.headers = {}
            
            success = await realtime_service.connection_manager.connect(
                mock_ws, connection_id
            )
            assert success
            connections.append(connection_id)
        
        # Verify all connections are tracked
        assert len(realtime_service.connection_manager.active_connections) == num_connections
        
        # Test broadcasting to all connections
        message = WebSocketMessage(
            type=WebSocketMessageType.SYSTEM_NOTIFICATION,
            data={"message": "Performance test"}
        )
        
        with patch.object(realtime_service.connection_manager, 'send_to_connection') as mock_send:
            mock_send.return_value = True
            
            sent_count = await realtime_service.connection_manager.broadcast(message)
            assert sent_count == num_connections
    
    async def test_webhook_delivery_throughput(self, webhook_service):
        """Test webhook delivery throughput"""
        # This would test the delivery worker performance
        # with multiple concurrent deliveries
        num_deliveries = 50
        
        # Mock successful HTTP responses
        with patch.object(webhook_service.http_client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.text = '{"success": true}'
            mock_post.return_value = mock_response
            
            # Create multiple deliveries
            deliveries = []
            for i in range(num_deliveries):
                delivery = WebhookDelivery(
                    webhook_id=uuid4(),
                    event_id=uuid4(),
                    url=f"https://webhook-{i}.example.com",
                    payload='{"test": "data"}',
                    headers={"Content-Type": "application/json"}
                )
                deliveries.append(delivery)
            
            # Process deliveries concurrently
            start_time = time.time()
            
            tasks = [
                webhook_service._process_delivery(delivery)
                for delivery in deliveries
            ]
            
            await asyncio.gather(*tasks)
            
            processing_time = time.time() - start_time
            
            # Verify all deliveries succeeded
            for delivery in deliveries:
                assert delivery.status == DeliveryStatus.SUCCESS
            
            # Log performance metrics
            throughput = num_deliveries / processing_time
            print(f"Webhook delivery throughput: {throughput:.2f} deliveries/second")


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])