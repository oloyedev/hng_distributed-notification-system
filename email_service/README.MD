# Email Service

The Email Service is a microservice that consumes email notification requests from RabbitMQ queues, fetches templates from the Template Service, renders them with variables, and sends emails via SMTP or SendGrid.

## 🎯 Purpose

- Consume messages from RabbitMQ email queues
- Fetch and render email templates
- Send emails via SMTP or SendGrid
- Handle delivery confirmations and failures
- Retry failed messages with exponential backoff
- Update notification status in API Gateway

## 🏗️ Architecture

```
RabbitMQ Queues → Email Service → Template Service
                       ↓
                  SMTP/SendGrid
                       ↓
                  API Gateway (status update)
```

## 📦 Project Structure

```
email_service/
├── main.py                           # FastAPI application entry point
├── app/
│   ├── core/
│   │   ├── config.py                 # Configuration management
│   │   ├── rabbitmq.py               # RabbitMQ connection & consumer
│   │   └── redis.py                  # Redis cache manager
│   ├── services/
│   │   ├── email_processor.py        # Main processing pipeline
│   │   ├── template_fetcher.py       # Template fetching & caching
│   │   ├── email_sender.py           # SMTP & SendGrid implementation
│   │   └── status_updater.py         # Status callback to API Gateway
│   ├── api/v1/routes/
│   │   └── health.py                 # Health check endpoints
│   └── utils/
│       └── logger.py                 # Logging utilities
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Container image
├── .env.example                      # Environment template
└── README.md                         # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Redis 7+
- RabbitMQ 3+
- SMTP credentials or SendGrid API key

### Installation

```bash
# Clone repository
cd email-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration
```

### Configuration

Create `.env` file:

```bash
# Application
APP_NAME=Email Service
VERSION=1.0.0
DEBUG=False
HOST=0.0.0.0
PORT=3003

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Queue Configuration
EMAIL_QUEUE=email.queue
EMAIL_PRIORITY_QUEUE=email.priority.queue
FAILED_QUEUE=failed.queue

# SMTP Configuration (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@example.com
SMTP_FROM_NAME=Notification System
SMTP_USE_TLS=True

# SendGrid (Alternative to SMTP)
USE_SENDGRID=False
SENDGRID_API_KEY=your-sendgrid-api-key

# Service URLs
TEMPLATE_SERVICE_URL=http://localhost:3002
API_GATEWAY_URL=http://localhost:3000

# Service Authentication
SERVICE_NAME=email-service
SERVICE_TOKEN=email-service-secret-token-change-in-production

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY_SECONDS=5
EXPONENTIAL_BACKOFF=True

# Performance
PREFETCH_COUNT=10
CONCURRENT_WORKERS=5
```

### Running the Service

#### Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 3003
```

#### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 3003 --workers 4
```

#### Docker
```bash
# Build image
docker build -t email-service:latest .

# Run container
docker run -d \
  -p 3003:3003 \
  --env-file .env \
  --name email-service \
  email-service:latest
```

## 🔄 How It Works

### Message Processing Flow

1. **Consume Message** from RabbitMQ queue
2. **Validate** message structure
3. **Fetch Template** from Template Service (with caching)
4. **Render Template** with user variables
5. **Send Email** via SMTP or SendGrid
6. **Update Status** back to API Gateway
7. **Handle Failures** with retry logic

### Functional Pipeline

```python
process_email_message(message) →
  ├─ fetch_template_step()
  ├─ render_template_step()
  ├─ send_email_step()
  └─ update_status_step()
```

### Queue Message Format

```json
{
  "notification_id": "notif_xyz789",
  "notification_type": "email",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "recipient": "user@example.com",
  "template_code": "welcome_email",
  "variables": {
    "name": "John Doe",
    "link": "https://example.com/verify"
  },
  "request_id": "req_unique_123",
  "priority": 5,
  "timestamp": "2025-11-12T20:30:00Z",
  "retry_count": 0,
  "max_retries": 3,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 📧 Email Sending

### SMTP Configuration

For Gmail:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Not regular password!
SMTP_USE_TLS=True
```

**Note**: For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use App Password instead of regular password

### SendGrid Configuration

```bash
USE_SENDGRID=True
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
```

## 🔄 Retry Logic

### Exponential Backoff

- **Attempt 1**: Immediate retry after 5 seconds
- **Attempt 2**: Retry after 10 seconds (5 * 2^1)
- **Attempt 3**: Retry after 20 seconds (5 * 2^2)
- **Failed**: Move to Dead Letter Queue

### Retry Configuration

```bash
MAX_RETRIES=3
RETRY_DELAY_SECONDS=5
EXPONENTIAL_BACKOFF=True
```

## 🏥 Health Checks

### Endpoints

```bash
# Overall health
GET http://localhost:3003/api/v1/health

# Readiness check (for K8s)
GET http://localhost:3003/api/v1/health/ready

# Liveness check (for K8s)
GET http://localhost:3003/api/v1/health/live
```

### Response Example

```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T20:30:00Z",
  "service": "Email Service",
  "version": "1.0.0",
  "redis": "connected"
}
```

## 📊 Monitoring

### Logs

The service provides structured logging with:
- Correlation IDs for request tracking
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Contextual information (notification_id, correlation_id)

### Log Format

```
2025-11-12 20:30:00 - email_processor - INFO - [email_processor.py:45] - Processing email message: notif_xyz789 (correlation: 550e8400-e29b-41d4-a716-446655440000)
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_email_processor.py -v
```

### Manual Testing

```bash
# Test email sending directly (requires running service)
python scripts/test_email.py
```

## 🔧 Troubleshooting

### Issue: Emails not sending

**Check:**
1. SMTP credentials are correct
2. Redis is connected: `redis-cli ping`
3. RabbitMQ has messages: Check management UI at http://localhost:15672
4. Template Service is responding: `curl http://localhost:3002/api/v1/health`
5. View logs: `docker logs email-service`

### Issue: Messages stuck in queue

**Check:**
1. Email Service is running: `docker ps | grep email-service`
2. Check RabbitMQ consumers: Management UI → Queues → Consumers
3. Check for errors in logs

### Issue: Template not found

**Check:**
1. Template exists in Template Service: `curl http://localhost:3002/api/v1/templates/your_template_code`
2. Template Service is accessible from Email Service
3. Check network connectivity between services

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 3003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3003/api/v1/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3003"]
```

### Docker Compose

See `docker-compose.full-system.yml` in root directory.

## 🔐 Security

- Service-to-service authentication with tokens
- SMTP credentials encrypted at rest
- No sensitive data in logs
- Environment variables for secrets
- TLS for SMTP connections

## 📈 Performance

### Metrics

- **Throughput**: Processes 100+ emails/second
- **Latency**: < 2 seconds per email (SMTP)
- **Prefetch**: 10 messages at a time
- **Concurrent workers**: 5 (configurable)

### Optimization

- Template caching with Redis (1 hour TTL)
- Connection pooling for SMTP
- Async I/O for all operations
- Batch processing support

## 🤝 Integration

### With Template Service

```python
# Fetch template
GET http://template-service:3002/api/v1/templates/render
Body: {
  "template_code": "welcome_email",
  "variables": {...},
  "language": "en"
}
```

### With API Gateway

```python
# Update notification status
POST http://api-gateway:3000/api/v1/email/status
Headers: {
  "X-Service-Token": "email-service:secret"
}
Body: {
  "notification_id": "notif_xyz789",
  "status": "delivered",
  "timestamp": "2025-11-12T20:30:00Z"
}
```

## 📝 API Documentation

Once running, access interactive API docs:
- **Swagger UI**: http://localhost:3003/api/docs
- **ReDoc**: http://localhost:3003/api/redoc

## 🛠️ Development

### Code Style

```bash
# Format code
black .

# Lint code
flake8 .
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install
```

## 📄 License

MIT License

## 🙋 Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Email: support@example.com

## 📚 Related Services

- [API Gateway](../api-gateway/README.md)
- [Template Service](../template-service/README.md)
- [User Service](../user-service/README.md)