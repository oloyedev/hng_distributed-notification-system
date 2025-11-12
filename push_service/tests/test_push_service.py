import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.circuit_breaker import CircuitBreaker, CircuitState
from app.services.retry_handler import RetryHandler, RetryableError


client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_returns_200(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
    
    def test_health_check_structure(self):
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        assert "checks" in data
        
        checks = data["checks"]
        assert "rabbitmq" in checks
        assert "firebase_fcm" in checks
        assert "redis" in checks
        assert "circuit_breaker" in checks


class TestMetricsEndpoint:
    """Test metrics endpoint"""
    
    def test_metrics_returns_200(self):
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
    
    def test_metrics_structure(self):
        response = client.get("/api/v1/metrics")
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "message" in data


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_returns_200(self):
        response = client.get("/api/v1/")
        assert response.status_code == 200
    
    def test_root_structure(self):
        response = client.get("/api/v1/")
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["service"] == "push-service"


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    def test_circuit_starts_closed(self):
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, name="test")
        
        def failing_func():
            raise Exception("Test failure")
        
        # Trigger failures
        for _ in range(3):
            try:
                cb.call(failing_func)
            except Exception:
                pass
        
        assert cb.state == CircuitState.OPEN
    
    def test_circuit_resets_on_success(self):
        cb = CircuitBreaker(failure_threshold=3, name="test")
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.failure_count == 0


class TestRetryHandler:
    """Test retry handler functionality"""
    
    def test_retry_handler_retries_on_retryable_error(self):
        handler = RetryHandler()
        attempts = []
        
        def failing_func():
            attempts.append(1)
            if len(attempts) < 3:
                raise RetryableError("Temporary failure")
            return "success"
        
        result = handler.with_retry(failing_func)
        assert result == "success"
        assert len(attempts) == 3
    
    def test_retry_handler_calculates_backoff(self):
        handler = RetryHandler()
        
        backoff_0 = handler.calculate_backoff(0)
        backoff_1 = handler.calculate_backoff(1)
        backoff_2 = handler.calculate_backoff(2)
        
        assert backoff_1 > backoff_0
        assert backoff_2 > backoff_1


class TestPushMessageSchema:
    """Test push message schema validation"""
    
    def test_valid_push_message(self):
        from app.models.schemas import PushMessage
        
        message = PushMessage(
            title="Test Title",
            body="Test Body",
            image_url="https://example.com/image.jpg",
            click_action="https://example.com",
            data={"key": "value"}
        )
        
        assert message.title == "Test Title"
        assert message.body == "Test Body"
    
    def test_push_message_optional_fields(self):
        from app.models.schemas import PushMessage
        
        message = PushMessage(
            title="Test",
            body="Body"
        )
        
        assert message.image_url is None
        assert message.click_action is None


class TestNotificationSchemas:
    """Test notification request schemas"""
    
    def test_valid_notification_request(self):
        from app.models.schemas import PushNotificationRequest, UserData, NotificationType
        
        request = PushNotificationRequest(
            notification_type=NotificationType.push,
            user_id="user-123",
            template_code="template-1",
            variables=UserData(
                name="John Doe",
                link="https://example.com"
            ),
            request_id="req-123",
            priority=2
        )
        
        assert request.notification_type == NotificationType.push
        assert request.user_id == "user-123"
        assert request.priority == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])