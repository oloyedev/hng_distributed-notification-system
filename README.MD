# Distributed Notification System

A production-ready microservices-based notification system built with functional programming principles. Supports email and push notifications with queue-based processing, template management, user preferences, and automatic retries.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Applications                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   API Gateway (3000)   │
                    │  - Authentication      │
                    │  - Rate Limiting       │
                    │  - Request Routing     │
                    └───────────┬───────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ User Service │ │Template Svc  │ │  RabbitMQ    │
        │   (3001)     │ │   (3002)     │ │   Queues     │
        │              │ │              │ └──────┬───────┘
        │ - User CRUD  │ │ - Templates  │        │
        │ - Preferences│ │ - i18n       │        │
        │ - Auth       │ │ - Versioning │        │
        └──────────────┘ └──────────────┘        │
                                        ┌─────────┴──────────┐
                                        │                    │
                                        ▼                    ▼
                                ┌──────────────┐    ┌──────────────┐
                                │Email Service │    │Push Service  │
                                │   (3003)     │    │   (3004)     │
                                │              │    │              │
                                │ - SMTP       │    │ - FCM        │
                                │ - SendGrid   │    │ - OneSignal  │
                                │ - Retries    │    │ - Web Push   │
                                └──────────────┘    └──────────────┘
```

## 📦 Services Overview

### 1. API Gateway (Port 3000) - Entry Point
**Purpose**: Single entry point for all notification requests

**Key Features**:
- Request validation and authentication (JWT/API Key)
- User preference checking (REST call to User Service)
- Message routing to appropriate queues
- Status tracking and retrieval
- Rate limiting (100 req/min per user)
- Circuit breaker for downstream services
- Idempotency support

**Endpoints**:
```
POST   /api/v1/notifications          # Create notification
GET    /api/v1/notifications/:id      # Get notification status
GET    /api/v1/notifications           # List user notifications
POST   /api/v1/email/status            # Email service callback
POST   /api/v1/push/status             # Push service callback
GET    /api/v1/health                  # Health check
GET    /api/v1/metrics                 # Metrics
```

### 2. User Service (Port 3001) - User Management
**Purpose**: Manages user data, contact information, and notification preferences

**Key Features**:
- User CRUD operations
- Email and push token storage
- Notification preferences management
- Authentication and authorization
- User lookup for API Gateway

**Endpoints**:
```
POST   /api/v1/users                   # Create user
GET    /api/v1/users/:id               # Get user
PUT    /api/v1/users/:id               # Update user
DELETE /api/v1/users/:id               # Delete user
GET    /api/v1/users/:id/preferences   # Get preferences
PUT    /api/v1/users/:id/preferences   # Update preferences
POST   /api/v1/auth/login              # Login
POST   /api/v1/auth/register           # Register
GET    /api/v1/health                  # Health check
```

**Database Schema**:
```sql
users:
  - id (UUID)
  - name (string)
  - email (string, unique)
  - push_token (string, nullable)
  - email_notifications (boolean)
  - push_notifications (boolean)
  - created_at (timestamp)
  - updated_at (timestamp)
```

### 3. Template Service (Port 3002) - Template Management
**Purpose**: Manages notification templates with versioning and multi-language support

**Key Features**:
- Template CRUD operations
- Variable substitution ({{variable}} syntax)
- Multi-language support (i18n)
- Version management (automatic versioning)
- Template caching with Redis
- Support for nested variables and default values

**Endpoints**:
```
POST   /api/v1/templates               # Create template
GET    /api/v1/templates/:code         # Get template
PUT    /api/v1/templates/:code         # Update template (creates new version)
DELETE /api/v1/templates/:code         # Soft delete template
GET    /api/v1/templates                # List templates
POST   /api/v1/templates/render        # Render template with variables
GET    /api/v1/templates/:code/versions # Get all versions
GET    /api/v1/health                  # Health check
GET    /api/v1/metrics                 # Metrics
```

**Template Syntax**:
- Simple: `{{name}}`
- Nested: `{{user.name}}`
- Default: `{{name|default:"Guest"}}`
- Filters: `{{name|upper}}`

### 4. Email Service (Port 3003) - Email Processing
**Purpose**: Consumes email notification requests and sends emails

**Key Features**:
- RabbitMQ queue consumer (email.queue, email.priority.queue)
- Template fetching and rendering
- Email sending via SMTP or SendGrid
- Automatic retries with exponential backoff
- Bounce and delivery tracking
- Status updates to API Gateway

**Endpoints**:
```
GET    /api/v1/health                  # Health check
GET    /api/v1/health/ready            # Readiness check
GET    /api/v1/health/live             # Liveness check
```

**Queue Message Format**:
```json
{
  "notification_id": "notif_xyz789",
  "notification_type": "email",
  "user_id": "uuid",
  "recipient": "user@example.com",
  "template_code": "welcome_email",
  "variables": {"name": "John", "link": "https://..."},
  "request_id": "req_unique_123",
  "priority": 5,
  "retry_count": 0,
  "max_retries": 3
}
```

### 5. Push Service (Port 3004) - Push Notifications
**Purpose**: Consumes push notification requests and sends to mobile/web devices

**Key Features**:
- RabbitMQ queue consumer (push.queue, push.priority.queue)
- Firebase Cloud Messaging (FCM) integration
- OneSignal support
- Web Push with VAPID
- Device token validation
- Rich notifications (title, text, image, link)
- Status updates to API Gateway

**Endpoints**:
```
GET    /api/v1/health                  # Health check
GET    /api/v1/health/ready            # Readiness check
GET    /api/v1/health/live             # Liveness check
```

**Push Notification Format**:
```json
{
  "notification_id": "notif_abc123",
  "notification_type": "push",
  "user_id": "uuid",
  "recipient": "device_token_here",
  "template_code": "order_update",
  "variables": {"order_id": "123", "status": "Delivered"},
  "priority": 8
}
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- RabbitMQ 3+

### Start All Services

```bash
# Clone repository
git clone <repository-url>
cd notification-system

# Copy environment files
cp .env.example .env
# Edit .env with your configuration

# Start all services with Docker Compose
docker-compose -f docker-compose.full-system.yml up -d

# View logs
docker-compose -f docker-compose.full-system.yml logs -f

# Check all services are running
docker-compose -f docker-compose.full-system.yml ps
```

### Verify Services

```bash
# Check API Gateway
curl http://localhost:3000/api/v1/health

# Check User Service
curl http://localhost:3001/api/v1/health

# Check Template Service
curl http://localhost:3002/api/v1/health

# Check Email Service
curl http://localhost:3003/api/v1/health

# Check Push Service
curl http://localhost:3004/api/v1/health
```

## 📝 Complete Usage Example

### 1. Register a User
```bash
curl -X POST http://localhost:3001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "preferences": {
      "email": true,
      "push": true
    }
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "john@example.com",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "User registered successfully"
}
```

### 2. Create a Template
```bash
curl -X POST http://localhost:3002/api/v1/templates \
  -H "Content-Type: application/json" \
  -d '{
    "template_code": "welcome_email",
    "name": "Welcome Email",
    "description": "Welcome new users",
    "subject": "Welcome to {{company_name}}, {{name}}!",
    "body": "<html><body><h1>Hello {{name}}</h1><p>Welcome to {{company_name}}! Click <a href=\"{{verification_link}}\">here</a> to verify your email.</p><p>Thanks,<br>The {{company_name}} Team</p></body></html>",
    "language": "en"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "template_code": "welcome_email",
    "name": "Welcome Email",
    "version": 1,
    "is_active": true
  },
  "message": "Template created successfully"
}
```

### 3. Send a Notification
```bash
curl -X POST http://localhost:3000/api/v1/notifications \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "template_code": "welcome_email",
    "variables": {
      "name": "John Doe",
      "company_name": "Acme Inc",
      "verification_link": "https://example.com/verify/abc123"
    },
    "request_id": "req_unique_12345",
    "priority": 5,
    "metadata": {
      "campaign_id": "welcome_campaign_2025"
    }
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "notification_id": "notif_xyz789abc",
    "status": "pending",
    "created_at": "2025-11-13T10:30:00Z"
  },
  "message": "Notification queued successfully",
  "error": null,
  "meta": null
}
```

### 4. Check Notification Status
```bash
curl -X GET http://localhost:3000/api/v1/notifications/notif_xyz789abc \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "success": true,
  "data": {
    "notification_id": "notif_xyz789abc",
    "status": "delivered",
    "notification_type": "email",
    "created_at": "2025-11-13T10:30:00Z",
    "updated_at": "2025-11-13T10:30:15Z"
  },
  "message": "Notification found"
}
```

### 5. Get User's Notifications
```bash
curl -X GET "http://localhost:3000/api/v1/notifications?page=1&limit=20" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 🔐 Authentication

### API Key Authentication
```bash
curl -X POST http://localhost:3000/api/v1/notifications \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### JWT Token Authentication
```bash
# 1. Login to get token
curl -X POST http://localhost:3001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'

# 2. Use token in requests
curl -X POST http://localhost:3000/api/v1/notifications \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Service-to-Service Authentication
```bash
# Email/Push services calling API Gateway
curl -X POST http://localhost:3000/api/v1/email/status \
  -H "X-Service-Token: email-service:secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_id": "notif_xyz789",
    "status": "delivered"
  }'
```

## 🔄 Message Queue Structure

```
Exchange: notifications.direct (Direct Exchange)
│
├── email.queue
│   └── Consumers: Email Service (prefetch: 10)
│
├── email.priority.queue
│   └── Consumers: Email Service (high priority)
│
├── push.queue
│   └── Consumers: Push Service (prefetch: 10)
│
├── push.priority.queue
│   └── Consumers: Push Service (high priority)
│
└── failed.queue (Dead Letter Queue)
    └── Manual intervention required
```

**Priority Routing**:
- Priority 0-4: Regular queue
- Priority 5-10: Priority queue

## 📊 Database Architecture

### User Service Database (PostgreSQL)
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    push_token TEXT,
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

### Template Service Database (PostgreSQL)
```sql
-- Templates table
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    template_code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX idx_template_code_language_version 
    ON templates(template_code, language, version);
```

### Shared Redis Cache
```
Keys:
- user:{user_id}                    # User cache (5 min TTL)
- template:{code}:{lang}:{version}  # Template cache (1 hour TTL)
- notification:{notification_id}     # Notification status (24 hours TTL)
- request:{request_id}              # Idempotency (24 hours TTL)
- ratelimit:{identifier}            # Rate limit counter (1 min TTL)
```

## 🎯 Key Features

### ✅ Functional Programming
- Pure functions for business logic
- Immutable data structures
- Function composition and pipelines
- Higher-order functions
- Side effects isolation

### ✅ Reliability
- Automatic retries with exponential backoff
- Dead Letter Queue for failed messages
- Circuit breaker pattern
- Idempotency support
- Health checks for all services

### ✅ Scalability
- Horizontal scaling support
- Queue-based async processing
- Connection pooling
- Caching with Redis
- Load balancing ready

### ✅ Observability
- Correlation IDs for request tracking
- Structured logging
- Health endpoints (liveness/readiness)
- Metrics endpoints
- Service monitoring

### ✅ Security
- JWT and API Key authentication
- Service-to-service tokens
- Rate limiting (100 req/min per user)
- Input validation with Pydantic
- SQL injection protection

## 📈 Performance Targets

- **Throughput**: 1,000+ notifications per minute
- **API Gateway**: < 100ms response time
- **Template Service**: < 50ms (cached), < 100ms (DB)
- **Email Processing**: < 2 seconds per email
- **Success Rate**: 99.5% delivery success rate
- **Cache Hit Rate**: ~80%

## 🔧 Configuration

### Environment Variables

Each service has its own `.env` file. See individual service READMEs for details.

**Common Variables**:
```bash
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Service URLs
USER_SERVICE_URL=http://localhost:3001
TEMPLATE_SERVICE_URL=http://localhost:3002
API_GATEWAY_URL=http://localhost:3000
```

## 🐳 Docker Services

Access the management UIs:

- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **PostgreSQL**: localhost:5432 (postgres/password)
- **Redis**: localhost:6379

## 🧪 Testing

### Integration Test
```bash
# 1. Create a template
./scripts/create_template.sh

# 2. Register a user
./scripts/register_user.sh

# 3. Send notification
./scripts/send_notification.sh

# 4. Check status
./scripts/check_status.sh
```

### Load Testing
```bash
# Install k6
brew install k6  # macOS
# or download from https://k6.io/

# Run load test
k6 run scripts/load_test.js
```

## 📚 Documentation

- [API Gateway Documentation](./api-gateway/README.md)
- [User Service Documentation](./user-service/README.md)
- [Template Service Documentation](./template-service/README.md)
- [Email Service Documentation](./email-service/README.md)
- [Push Service Documentation](./push-service/README.md)
- [Deployment Guide](./DEPLOYMENT.md)

## 🔍 Monitoring & Logs

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f email-service
docker-compose logs -f api-gateway

# With timestamps
docker-compose logs -f --timestamps
```

### RabbitMQ Monitoring
```bash
# View queue statistics
curl -u guest:guest http://localhost:15672/api/queues

# View connections
curl -u guest:guest http://localhost:15672/api/connections
```

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check Docker logs
docker-compose logs

# Check if ports are available
netstat -an | grep LISTEN | grep -E '3000|3001|3002|3003|3004|5432|6379|5672'

# Restart services
docker-compose down
docker-compose up -d
```

### Notifications Not Sending
```bash
# 1. Check RabbitMQ has messages
curl -u guest:guest http://localhost:15672/api/queues/%2F/email.queue

# 2. Check Email Service is consuming
docker-compose logs email-service | grep "Processing"

# 3. Check Template Service is accessible
curl http://localhost:3002/api/v1/health

# 4. Verify SMTP credentials in .env
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
docker exec -it postgres psql -U postgres -d template_db -c "SELECT 1;"

# Check Redis connection
docker exec -it redis redis-cli ping
```

## 🎓 Learning Outcomes

This project demonstrates:
- ✅ Microservices architecture design
- ✅ Functional programming in Python
- ✅ Asynchronous message queuing
- ✅ RESTful API design
- ✅ Database design and optimization
- ✅ Caching strategies
- ✅ Docker containerization
- ✅ Service-to-service communication
- ✅ Error handling and retry mechanisms
- ✅ Authentication and authorization
- ✅ Monitoring and observability

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Follow functional programming principles
4. Write tests
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

## 📄 License

MIT License - See LICENSE file for details

## 👥 Team

**HNG12 Internship - Stage 4 Backend Task**

## 🙏 Acknowledgments

- HNG Internship Program
- FastAPI Framework
- RabbitMQ
- PostgreSQL
- Redis
- All open-source contributors

## 📞 Support

- **GitHub Issues**: [repository-url]/issues
- **Email**: support@example.com
- **Documentation**: [docs-url]

---

**Built with ❤️ using Functional Programming Principles**
