# Git Integration Guide for Push Service

## 📋 Before You Start

Make sure you have:
1. Git installed on your machine
2. Access to the team's GitHub repository
3. Your GitHub account added as a collaborator
4. Firebase credentials JSON file (ask team lead if needed)

---

## 🚀 Step-by-Step Integration Process

### Step 1: Initial Setup

```bash
# Navigate to where you want to work
cd ~/projects  # or your preferred directory

# Clone the team repository
git clone <repository-url>
cd <repository-name>

# Check what branch you're on
git branch

# Create your feature branch
git checkout -b feature/push-service
```

### Step 2: Check Repository Structure

```bash
# See what's already in the repo
ls -la

# Understand the existing structure
tree -L 2  # or just ls -R
```

**Expected structure might be:**
```
notification-system/
├── api-gateway/
├── user-service/
├── email-service/
└── push-service/        # This is where your code goes
```

### Step 3: Add Your Push Service

**Option A: If push-service folder doesn't exist**
```bash
# Create the directory
mkdir push-service
cd push-service

# Copy all your files here
# (I'll show you the file structure below)
```

**Option B: If push-service folder exists with some files**
```bash
cd push-service

# Check what's already there
ls -la

# Pull latest changes first
git pull origin main
```

### Step 4: Copy Your Files

Create this exact structure in the `push-service/` folder:

```
push-service/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rabbitmq_consumer.py
│   │   ├── fcm_service.py
│   │   ├── circuit_breaker.py
│   │   └── retry_handler.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── idempotency.py
│   └── api/
│       ├── __init__.py
│       └── routes.py
├── tests/
│   ├── __init__.py
│   └── test_push_service.py
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── GIT_INTEGRATION_GUIDE.md
```

### Step 5: Configure Team-Specific Settings

Before committing, update these files with team's actual values:

**1. Edit `app/config.py`:**
```python
# Update these URLs based on your team's setup
rabbitmq_host: str = "your-team-rabbitmq-host"
api_gateway_url: str = "http://your-gateway:8000"
```

**2. Edit `app/services/rabbitmq_consumer.py`:**
```python
# Line 26 - Update user service URL
self.user_service_url = "http://user-service:8001"  # Ask team lead for correct URL
```

**3. Create `.env` file** (copy from .env.example):
```bash
cp .env.example .env
# Edit with your team's actual values
nano .env  # or vim .env, or use VS Code
```

### Step 6: Get Firebase Credentials

**Ask your team lead for:**
1. The Firebase project name
2. The service account JSON file

**Once you have it:**
```bash
# Place it in push-service root
mv ~/Downloads/firebase-credentials.json .

# Verify it's there
ls -la firebase-credentials.json

# Make sure it's in .gitignore (already added)
cat .gitignore | grep firebase
```

### Step 7: Test Locally First

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start dependencies with Docker
docker-compose up rabbitmq redis -d

# Run the service
python -m uvicorn app.main:app --reload --port 8003

# In another terminal, test health endpoint
curl http://localhost:8003/api/v1/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "push-service",
  ...
}
```

### Step 8: Commit Your Code

```bash
# Check what files will be committed
git status

# Add all files
git add .

# Review what you're about to commit
git diff --staged

# Commit with a clear message
git commit -m "feat: add push notification service with FCM integration

- Implemented RabbitMQ consumer for push queue
- Integrated Firebase Cloud Messaging
- Added circuit breaker and retry logic
- Implemented idempotency with Redis
- Added health check and metrics endpoints
- Configured CI/CD pipeline
- Added comprehensive documentation"

# Push to your branch
git push origin feature/push-service
```

### Step 9: Create Pull Request

1. Go to your GitHub repository
2. Click "Compare & pull request"
3. Fill in the PR template:

```markdown
## Description
Implemented Push Notification Service for the distributed notification system.

## Changes
- ✅ RabbitMQ consumer for push.queue
- ✅ Firebase FCM integration
- ✅ Circuit breaker pattern
- ✅ Retry mechanism with exponential backoff
- ✅ Idempotency checks
- ✅ Health checks and monitoring
- ✅ Docker containerization
- ✅ CI/CD pipeline

## Testing
- [x] Health endpoint responds correctly
- [x] Unit tests pass
- [x] Docker build succeeds
- [x] Integrates with RabbitMQ
- [x] Integrates with Redis

## Screenshots
(Add screenshots of health check response, metrics, etc.)

## Checklist
- [x] Code follows project conventions (snake_case)
- [x] Added comprehensive documentation
- [x] Added unit tests
- [x] Dockerfile and docker-compose configured
- [x] CI/CD pipeline configured
- [x] No secrets committed
```

4. Request review from team members
5. Tag your team lead

---

## 🔄 Syncing with Team's Changes

### If Team Members Push Changes

```bash
# Switch to main branch
git checkout main

# Pull latest changes
git pull origin main

# Switch back to your branch
git checkout feature/push-service

# Merge main into your branch
git merge main

# Resolve any conflicts if they occur
# (Git will tell you which files have conflicts)

# Push updated branch
git push origin feature/push-service
```

### If You Need to Update Your Branch

```bash
# Fetch all remote changes
git fetch origin

# See what branches exist
git branch -a

# Pull specific branch
git pull origin feature/push-service
```

---

## 🐛 Common Issues & Solutions

### Issue 1: Firebase credentials not found
**Solution:**
```bash
# Check if file exists
ls -la firebase-credentials.json

# If missing, ask team lead for it
# Make sure it's in the right location (push-service root)
```

### Issue 2: Port already in use
**Solution:**
```bash
# Check what's using port 8003
lsof -i :8003  # On Mac/Linux
netstat -ano | findstr :8003  # On Windows

# Kill the process or use different port
# Update .env: API_PORT=8004
```

### Issue 3: RabbitMQ connection failed
**Solution:**
```bash
# Start RabbitMQ with Docker
docker-compose up rabbitmq -d

# Check if it's running
docker ps | grep rabbitmq

# Check logs
docker logs rabbitmq
```

### Issue 4: Git merge conflicts
**Solution:**
```bash
# See which files have conflicts
git status

# Open conflicted files and look for:
<<<<<<< HEAD
your code
=======
their code
>>>>>>> main

# Manually resolve, then:
git add <resolved-files>
git commit -m "fix: resolve merge conflicts"
```

### Issue 5: Push rejected (non-fast-forward)
**Solution:**
```bash
# Pull first, then push
git pull origin feature/push-service --rebase
git push origin feature/push-service
```

---

## 📝 Git Best Practices for This Project

### 1. Commit Message Format
```bash
# Format: <type>: <description>

git commit -m "feat: add FCM push notification support"
git commit -m "fix: handle invalid device tokens properly"
git commit -m "docs: update README with setup instructions"
git commit -m "test: add circuit breaker unit tests"
git commit -m "refactor: improve error handling in consumer"
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

### 2. Branch Naming
```bash
feature/push-service          # Your main branch
feature/push-service-retry    # Sub-feature
bugfix/fcm-connection         # Bug fixes
hotfix/critical-token-issue   # Urgent fixes
```

### 3. Commit Frequency
- Commit after completing each feature
- Don't commit broken code
- Test before committing

### 4. Before Pushing
```bash
# Always run these before pushing:
python -m pytest tests/ -v     # Run tests
python -m black app/           # Format code
python -m flake8 app/          # Lint
git status                     # Review changes
```

---

## 🤝 Team Collaboration Tips

### 1. Communication
Before starting, in your team channel:
```
"Starting work on Push Service. Will be working on:
- RabbitMQ consumer
- FCM integration
- Circuit breaker implementation
ETA: 2 days. Let me know if anyone needs to coordinate."
```

### 2. Daily Updates
```
"Push Service Update:
✅ Completed: RabbitMQ consumer, FCM setup
🏗️ In Progress: Circuit breaker testing
🚧 Blocked: Need User Service endpoint for device tokens
📅 Next: Retry logic implementation"
```

### 3. Code Review
- Respond to review comments promptly
- Don't take feedback personally
- Ask questions if unclear
- Update your PR based on feedback

### 4. Merge Conflicts Prevention
- Pull main branch frequently
- Communicate when working on shared files
- Keep PRs small and focused

---

## 🎯 Final Checklist Before Submission

```bash
# ✅ Code Complete
[ ] All features implemented
[ ] Tests pass locally
[ ] Documentation updated
[ ] No TODO comments left

# ✅ Git Ready
[ ] Latest changes pulled
[ ] No merge conflicts
[ ] Commit messages clear
[ ] Branch pushed to remote

# ✅ Integration Ready
[ ] Tested with RabbitMQ
[ ] Tested with Redis
[ ] Health checks working
[ ] Env vars documented

# ✅ Team Ready
[ ] PR created
[ ] Team notified
[ ] Demo prepared
[ ] Ready for questions
```

---

## 📞 Need Help?

**Ask your team lead about:**
- Repository URL
- Firebase credentials
- RabbitMQ connection details
- User Service endpoint
- API Gateway URL
- Deployment server details

**In team chat, use:**
```
@teamlead I need help with [specific issue]

Example:
@teamlead I need the User Service endpoint URL for fetching device tokens.
Currently using: http://user-service:8001
Is this correct?
```

---

## 🎉 Next Steps After Merge

1. **Celebrate!** 🎊 You've built a production-ready microservice!

2. **Monitor deployment:**
```bash
# Check logs after deployment
ssh user@server
docker logs push-service -f
```

3. **Prepare for presentation:**
   - Demo health check
   - Show circuit breaker in action
   - Explain retry logic
   - Walk through code

4. **Document learnings:**
   - What worked well
   - What challenges you faced
   - What you'd improve

Good luck! 🚀