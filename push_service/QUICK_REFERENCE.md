# Quick Reference - Push Service

## 🚀 Essential Commands

### Setup
```bash
# Clone repo
git clone <repo-url>
cd <repo-name>

# Create branch
git checkout -b feature/push-service

# Setup Python
python -m venv venv
source venv/bin/activate
pip install -r push-service/requirements.txt

# Setup environment
cd push-service
cp .env.example .env
# Edit .env with team values
```

### Development
```bash
# Start dependencies
docker-compose up rabbitmq redis -d

# Run service
python -m uvicorn app.main:app --reload --port 8003

# Run tests
pytest tests/ -v

# Format code
black app/
isort app/

# Lint
flake8 app/
```

### Docker
```bash
# Build
docker build -t push-service .

# Run
docker-compose up --build

# Stop
docker-compose down

# Logs
docker-compose logs -f push-service

# Restart
docker-compose restart push-service
```

### Git Workflow
```bash
# Status check
git status

# Add files
git add .

# Commit
git commit -m "feat: your message"

# Push
git push origin feature/push-service

# Pull latest
git pull origin main

# Merge main
git checkout main
git pull
git checkout feature/push-service
git merge main
```

### Testing Endpoints
```bash
# Health check
curl http://localhost:8003/api/v1/health

# Metrics
curl http://localhost:8003/api/v1/metrics

# Pretty print
curl -s http://localhost:8003/api/v1/health | python -m json.tool
```

### RabbitMQ Management
```bash
# Access management UI
open http://localhost:15672
# Login: guest/guest

# List queues (in container)
docker exec rabbitmq rabbitmqctl list_queues

# Purge queue
docker exec rabbitmq rabbitmqctl purge_queue push.queue
```

### Redis Commands
```bash
# Access Redis CLI
docker exec -it redis redis-cli

# Check keys
KEYS idempotency:push:*

# Get value
GET idempotency:push:req-123

# Delete key
DEL idempotency:push:req-123

# Clear all
FLUSHALL
```

### Debugging
```bash
# Check running containers
docker ps

# Service logs
docker logs push-service --tail 100 -f

# RabbitMQ logs
docker logs rabbitmq --tail 50

# Redis logs
docker logs redis --tail 50

# Check ports
netstat -an | grep 8003
lsof -i :8003

# Check processes
ps aux | grep python
```

### Firebase Testing
```bash
# Test FCM directly (in Python shell)
python
>>> from app.services.fcm_service import fcm_service
>>> fcm_service.health_check()
True
```

### Environment Variables Quick Check
```bash
# View current env
cat .env

# Check if loaded
python -c "from app.config import settings; print(settings.rabbitmq_host)"
```

## 📋 File Checklist

```
✅ requirements.txt
✅ Dockerfile
✅ docker-compose.yml
✅ .env.example
✅ .env (don't commit!)
✅ .gitignore
✅ README.md
✅ firebase-credentials.json (don't commit!)
✅ app/main.py
✅ app/config.py
✅ app/models/schemas.py
✅ app/services/fcm_service.py
✅ app/services/rabbitmq_consumer.py
✅ app/services/circuit_breaker.py
✅ app/services/retry_handler.py
✅ app/utils/logger.py
✅ app/utils/idempotency.py
✅ app/api/routes.py
✅ tests/test_push_service.py
✅ .github/workflows/ci-cd.yml
```

## 🔧 Common Issues - Quick Fixes

### Service won't start
```bash
# Check logs
docker-compose logs push-service

# Restart everything
docker-compose down
docker-compose up --build
```

### RabbitMQ connection error
```bash
# Check if RabbitMQ is running
docker ps | grep rabbitmq

# Restart RabbitMQ
docker-compose restart rabbitmq

# Check RabbitMQ logs
docker logs rabbitmq
```

### Redis connection error
```bash
# Check Redis
docker ps | grep redis

# Test connection
docker exec -it redis redis-cli ping
# Should respond: PONG
```

### Firebase not initialized
```bash
# Check credentials exist
ls -la firebase-credentials.json

# Verify path in .env
grep FIREBASE .env

# Test in Python
python -c "import firebase_admin; print('OK')"
```

### Port already in use
```bash
# Find process
lsof -i :8003

# Kill it
kill -9 <PID>

# Or use different port
# Update API_PORT in .env
```

### Git push rejected
```bash
# Pull first
git pull origin feature/push-service --rebase

# Then push
git push origin feature/push-service
```

## 📊 Monitoring Commands

### Check Service Health
```bash
# Quick health check
curl -s http://localhost:8003/api/v1/health | jq '.status'

# Full health report
curl -s http://localhost:8003/api/v1/health | jq '.'
```

### Monitor Logs in Real-time
```bash
# Service logs
docker-compose logs -f push-service

# All services
docker-compose logs -f

# With timestamps
docker-compose logs -f -t push-service
```

### Check Resource Usage
```bash
# Container stats
docker stats push-service

# All containers
docker stats
```

## 🎯 Pre-Commit Checklist

```bash
# 1. Format code
black app/
isort app/

# 2. Lint
flake8 app/

# 3. Run tests
pytest tests/ -v

# 4. Check health
curl http://localhost:8003/api/v1/health

# 5. Review changes
git diff

# 6. Commit
git add .
git commit -m "feat: your message"

# 7. Push
git push origin feature/push-service
```

## 🚢 Deployment Commands

```bash
# SSH to server
ssh user@server

# Navigate to app
cd /app/push-service

# Pull latest
git pull origin main

# Rebuild
docker-compose down
docker-compose pull
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f push-service

# Health check
curl http://localhost:8003/api/v1/health
```

## 📞 Team Communication Templates

### Starting Work
```
🚀 Starting work on Push Service
📋 Task: Implement FCM push notifications
⏱️ ETA: 2 days
📍 Branch: feature/push-service
```

### Daily Update
```
Push Service Update - Day 1
✅ Completed: RabbitMQ consumer, FCM setup
🏗️ In Progress: Testing circuit breaker
🚧 Blocked: Need User Service endpoint
📅 Tomorrow: Retry logic + tests
```

### Ready for Review
```
✅ Push Service Ready for Review
📝 PR: #123
🔗 Link: [PR URL]
📊 Tests: All passing
🐳 Docker: Build successful
📚 Docs: Updated

Please review when you get a chance! @teamlead
```

### Asking for Help
```
🆘 Need help with Push Service
❓ Issue: [Specific issue]
🔍 What I tried: [Your attempts]
📍 File: app/services/fcm_service.py:45
💭 Context: [Relevant context]

@teamlead when you have a moment?
```

## 🎓 Key Concepts to Explain (for presentation)

1. **Circuit Breaker**: Prevents cascade failures
2. **Retry Logic**: Exponential backoff for resilience
3. **Idempotency**: Prevents duplicate notifications
4. **Dead Letter Queue**: Handles permanent failures
5. **Horizontal Scaling**: Multiple instances can run
6. **Health Checks**: Monitoring and alerting
7. **Async Processing**: Non-blocking message handling

## 📚 Important URLs (Update with your team's)

- **GitHub Repo**: `https://github.com/team/repo`
- **RabbitMQ UI**: `http://localhost:15672`
- **Push Service**: `http://localhost:8003`
- **API Gateway**: `http://localhost:8000`
- **User Service**: `http://localhost:8001`
- **Firebase Console**: `https://console.firebase.google.com`

## 🔐 Secrets Needed (Ask Team Lead)

- [ ] GitHub repository URL
- [ ] Firebase credentials JSON
- [ ] RabbitMQ connection details
- [ ] Redis connection details
- [ ] User Service endpoint
- [ ] API Gateway endpoint
- [ ] Deployment server SSH key

---

**Pro Tip**: Bookmark this file! You'll reference it often. 📌