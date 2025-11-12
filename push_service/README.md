# Push Notification Service

Microservice for sending push notifications via Firebase Cloud Messaging (FCM) as part of a distributed notification system.

## 🚀 Features

- **Asynchronous Message Processing**: Consumes messages from RabbitMQ push queue
- **Firebase FCM Integration**: Sends push notifications to iOS, Android, and Web
- **Circuit Breaker Pattern**: Prevents cascading failures when FCM is down
- **Retry Mechanism**: Exponential backoff with configurable retry attempts
- **Idempotency**: Prevents duplicate notifications using Redis
- **Health Checks**: Monitoring endpoints for service health
- **Dead Letter Queue**: Failed messages are routed to DLQ for manual review
- **Horizontal Scaling**: Supports multiple instances with RabbitMQ load balancing

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- RabbitMQ
- Redis
- Firebase Project with FCM enabled
- Firebase service account credentials JSON

## 🛠️ Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd push-service
```

### 2. Get Firebase Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to Project Settings → Service Accounts
4. Click "Generate New Private Key"
5. Save the JSON file as `firebase-credentials.json` in the project root

### 3. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Update RabbitMQ connection details
- Update Redis connection details
- Set Firebase credentials path
- Configure API Gateway URL

### 4. Install Dependencies

**Using virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Using Docker:**
```bash
docker-compose up --build
```

## 🏃 Running the Service

### Local Development

```bash
# Start dependencies
docker-compose up rabbitmq redis -d

# Run the service
python -m uvicorn app.main:app --reload --port 8003
```

### Using Docker Compose

```bash
docker-compose up --build
```

The service will start on `http://localhost:8003`

## 📡 API Endpoints

### Health Check
```bash
GET /api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "service": "push-service",
  "version": "1.0.0",
  "timestamp": "2025-11-11T12:00:00",
  "checks": {
    "rabbitmq": "connected",
    "firebase_fcm": "initialized",
    "redis": "connected",
    "circuit_breaker": {
      "name": "FCM",
      "state": "closed",
      "failure_count": 0,
      "threshold": 5
    }
  }
}
```

### Metrics
```bash
GET /api/v1/metrics
```

## 📨 Message Format

The service consumes messages from RabbitMQ with this format:

```json
{
  "notification_type": "push",
  "user_id": "uuid-here",
  "template_code": "Welcome {{name}}!",
  "variables": {
    "name": "John Doe",
    "link": "https://example.com",
    "meta": {}
  },
  "request_id": "unique-request-id",
  "priority": 2,
  "metadata": {
    "campaign_id": "123"
  }
}
```

## 🔄 Message Flow

1. API Gateway publishes message to `push.queue`
2. Push Service consumes message
3. Checks idempotency (skip if already processed)
4. Fetches user's device token from User Service
5. Builds push notification with template
6. Sends via FCM with circuit breaker protection
7. Retries on failure (exponential backoff)
8. Sends status update to API Gateway
9. Moves permanently failed messages to `failed.queue`

## 🛡️ Failure Handling

### Circuit Breaker
- Opens after 5 consecutive failures
- Rejects requests for 30 seconds
- Tests recovery in half-open state

### Retry Logic
- Max 3 attempts
- Exponential backoff: 1s, 2s, 4s
- Max delay: 60 seconds

### Error Types
- **Retryable**: FCM service errors, network issues
- **Non-Retryable**: Invalid token, malformed message

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 🐳 Docker Commands

```bash
# Build image
docker build -t push-service .

# Run container
docker run -p 8003:8003 --env-file .env push-service

# View logs
docker-compose logs -f push-service

# Stop services
docker-compose down
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8003/api/v1/health
```

### Logs
Structured JSON logs with correlation IDs for tracking:
```json
{
  "timestamp": "2025-11-11 12:00:00",
  "level": "INFO",
  "message": "Push notification delivered successfully",
  "correlation_id": "req-123"
}
```

### Metrics
- Message processing rate
- FCM success/failure rate
- Circuit breaker state
- Queue lengths
- Response times

## 🔧 Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `RABBITMQ_HOST` | RabbitMQ hostname | localhost |
| `RABBITMQ_PUSH_QUEUE` | Queue name | push.queue |
| `REDIS_HOST` | Redis hostname | localhost |
| `FIREBASE_CREDENTIALS_PATH` | FCM credentials | firebase-credentials.json |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | Failures before opening | 5 |
| `MAX_RETRY_ATTEMPTS` | Max retry count | 3 |
| `MESSAGE_PREFETCH_COUNT` | RabbitMQ prefetch | 10 |

## 🚀 Deployment

### CI/CD Pipeline

The service uses GitHub Actions for automated deployment:

1. **Lint**: Code quality checks
2. **Test**: Unit and integration tests
3. **Build**: Docker image creation
4. **Deploy**: Push to server

### Manual Deployment

```bash
# SSH to server
ssh user@server

# Pull latest code
cd /app/push-service
git pull origin main

# Restart service
docker-compose down
docker-compose up -d --build
```

## 🔐 Security

- Service runs as non-root user in Docker
- Firebase credentials mounted as read-only
- Secrets managed via environment variables
- No credentials in code or logs

## 📝 Architecture

```
┌─────────────┐
│ API Gateway │
└──────┬──────┘
       │ publishes
       ▼
┌─────────────┐     ┌──────────────┐
│ RabbitMQ    │────▶│ Push Service │
│ push.queue  │     └──────┬───────┘
└─────────────┘            │
                           ▼
                    ┌──────────────┐
                    │ Firebase FCM │
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ User Devices │
                    └──────────────┘
```

## 🤝 Integration with Other Services

- **User Service**: Fetches device tokens
- **API Gateway**: Receives status updates
- **Template Service**: (Optional) Can fetch templates

## 📚 Resources

- [Firebase FCM Documentation](https://firebase.google.com/docs/cloud-messaging)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/tutorials)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 👥 Team

Stage 4 Backend Task - Distributed Notification System

## 📄 License

MIT License