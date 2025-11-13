# Deployment Guide - Distributed Notification System

This guide covers deploying the notification system to production environments including VPS servers, cloud platforms, and Kubernetes.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Deployment Options](#deployment-options)
4. [VPS Deployment (DigitalOcean, Linode, etc.)](#vps-deployment)
5. [AWS Deployment](#aws-deployment)
6. [Google Cloud Platform Deployment](#gcp-deployment)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [Domain & SSL Setup](#domain--ssl-setup)
9. [Monitoring Setup](#monitoring-setup)
10. [Backup & Recovery](#backup--recovery)
11. [Scaling Guide](#scaling-guide)

## Prerequisites

### Required
- Domain name (e.g., api.yourcompany.com)
- Server with minimum 4GB RAM, 2 CPU cores
- Ubuntu 22.04 LTS (recommended)
- Docker & Docker Compose installed
- SSH access to server
- SSL certificate (Let's Encrypt recommended)

### Recommended
- CI/CD pipeline (GitHub Actions)
- Monitoring tools (Prometheus, Grafana)
- Log aggregation (ELK Stack or Loki)
- Backup solution

## Environment Setup

### 1. Server Initial Setup

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y curl git wget vim

# Create deployment user
useradd -m -s /bin/bash deploy
usermod -aG sudo deploy
su - deploy
```

### 2. Install Docker & Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 3. Setup Firewall

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow application ports (optional, if not behind reverse proxy)
sudo ufw allow 3000/tcp  # API Gateway
sudo ufw allow 3001/tcp  # User Service
sudo ufw allow 3002/tcp  # Template Service
sudo ufw allow 3003/tcp  # Email Service
sudo ufw allow 3004/tcp  # Push Service

# Check status
sudo ufw status
```

## Deployment Options

### Option 1: Docker Compose (Recommended for Single Server)
Best for: Small to medium applications, development, staging

### Option 2: Kubernetes
Best for: Large scale applications, high availability, auto-scaling

### Option 3: Cloud Services (AWS ECS, GCP Cloud Run)
Best for: Managed infrastructure, auto-scaling

## VPS Deployment

Deploy to any VPS provider (DigitalOcean, Linode, Vultr, Hetzner, etc.)

### 1. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/notification-system
sudo chown -R deploy:deploy /opt/notification-system
cd /opt/notification-system

# Clone repository
git clone https://github.com/your-username/notification-system.git .
```

### 2. Configure Environment Variables

```bash
# Create production environment file
cp .env.example .env.production

# Edit environment variables
nano .env.production
```

**Production .env.production**:
```bash
# Application
NODE_ENV=production
DEBUG=False

# Database
DATABASE_URL=postgresql+asyncpg://postgres:STRONG_PASSWORD@postgres:5432/template_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=STRONG_REDIS_PASSWORD

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=STRONG_RABBITMQ_PASSWORD

# SMTP (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourcompany.com
SMTP_USE_TLS=True

# Or SendGrid
USE_SENDGRID=True
SENDGRID_API_KEY=SG.your_sendgrid_api_key

# Firebase Cloud Messaging (for Push Service)
FCM_SERVER_KEY=your_fcm_server_key

# Security
JWT_SECRET=generate-strong-random-secret-here
API_GATEWAY_SECRET=generate-another-strong-secret
SERVICE_TOKEN_EMAIL=email-service:generate-strong-token
SERVICE_TOKEN_PUSH=push-service:generate-strong-token

# Domain
DOMAIN=api.yourcompany.com
ALLOWED_ORIGINS=https://yourcompany.com,https://www.yourcompany.com
```

### 3. Create Production Docker Compose

Create `docker-compose.production.yml`:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx-cache:/var/cache/nginx
    depends_on:
      - api-gateway
    networks:
      - notification-network
    restart: always

  api-gateway:
    build: ./api-gateway
    container_name: api-gateway
    env_file: .env.production
    environment:
      - PORT=3000
    depends_on:
      - redis
      - rabbitmq
    networks:
      - notification-network
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  user-service:
    build: ./user-service
    container_name: user-service
    env_file: .env.production
    environment:
      - PORT=3001
    depends_on:
      - postgres
      - redis
    networks:
      - notification-network
    restart: always

  template-service:
    build: ./template-service
    container_name: template-service
    env_file: .env.production
    environment:
      - PORT=3002
    depends_on:
      - postgres
      - redis
    networks:
      - notification-network
    restart: always

  email-service:
    build: ./email-service
    container_name: email-service
    env_file: .env.production
    environment:
      - PORT=3003
    depends_on:
      - redis
      - rabbitmq
      - template-service
    networks:
      - notification-network
    restart: always
    deploy:
      replicas: 2  # Scale email workers

  push-service:
    build: ./push-service
    container_name: push-service
    env_file: .env.production
    environment:
      - PORT=3004
    depends_on:
      - redis
      - rabbitmq
      - template-service
    networks:
      - notification-network
    restart: always
    deploy:
      replicas: 2  # Scale push workers

  postgres:
    image: postgres:15-alpine
    container_name: postgres
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=notification_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - notification-network
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - notification-network
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: rabbitmq
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_USER}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    networks:
      - notification-network
    restart: always
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

networks:
  notification-network:
    driver: bridge

volumes:
  postgres-data:
  redis-data:
  rabbitmq-data:
  nginx-cache:
```

### 4. Setup Nginx Reverse Proxy

Create `nginx/nginx.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req_status 429;

    # Upstream servers
    upstream api_gateway {
        least_conn;
        server api-gateway:3000 max_fails=3 fail_timeout=30s;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name api.yourcompany.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name api.yourcompany.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # API Gateway
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://api_gateway;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check endpoint (no rate limit)
        location /api/v1/health {
            proxy_pass http://api_gateway;
            proxy_set_header Host $host;
            access_log off;
        }
    }
}
```

### 5. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot

# Stop nginx temporarily
sudo docker-compose -f docker-compose.production.yml stop nginx

# Obtain certificate
sudo certbot certonly --standalone -d api.yourcompany.com

# Copy certificates
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/api.yourcompany.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/api.yourcompany.com/privkey.pem nginx/ssl/

# Set permissions
sudo chown -R deploy:deploy nginx/ssl

# Start nginx
sudo docker-compose -f docker-compose.production.yml up -d nginx
```

### 6. Deploy Application

```bash
# Build and start services
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Check all services are running
docker-compose -f docker-compose.production.yml ps
```

### 7. Create Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Pull latest code
echo "📦 Pulling latest code..."
git pull origin main

# Build images
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.production.yml build --no-cache

# Stop old containers
echo "🛑 Stopping old containers..."
docker-compose -f docker-compose.production.yml down

# Start new containers
echo "✅ Starting new containers..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check health
echo "🏥 Checking service health..."
curl -f http://localhost:3000/api/v1/health || exit 1
curl -f http://localhost:3001/api/v1/health || exit 1
curl -f http://localhost:3002/api/v1/health || exit 1
curl -f http://localhost:3003/api/v1/health || exit 1
curl -f http://localhost:3004/api/v1/health || exit 1

# Clean up
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✨ Deployment completed successfully!"
```

Make it executable:
```bash
chmod +x deploy.sh
```

## AWS Deployment

### Using AWS ECS (Elastic Container Service)

#### 1. Push Images to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag and push images
docker tag api-gateway:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/api-gateway:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/api-gateway:latest

# Repeat for all services
```

#### 2. Create ECS Task Definitions

Create `aws/task-definition.json`:

```json
{
  "family": "notification-system",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api-gateway",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/api-gateway:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NODE_ENV", "value": "production"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:database-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/notification-system",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "api-gateway"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:3000/api/v1/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### 3. Deploy to ECS

```bash
# Create cluster
aws ecs create-cluster --cluster-name notification-system

# Register task definition
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json

# Create service
aws ecs create-service \
  --cluster notification-system \
  --service-name api-gateway \
  --task-definition notification-system \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

### Using AWS RDS, ElastiCache, and Amazon MQ

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier notification-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username postgres \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20

# Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id notification-cache \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1

# Create Amazon MQ (RabbitMQ)
aws mq create-broker \
  --broker-name notification-queue \
  --engine-type RABBITMQ \
  --engine-version 3.11 \
  --host-instance-type mq.t3.micro \
  --users Username=admin,Password=YOUR_PASSWORD
```

## Google Cloud Platform Deployment

### Using Cloud Run

```bash
# Build and push images
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/api-gateway

# Deploy to Cloud Run
gcloud run deploy api-gateway \
  --image gcr.io/YOUR_PROJECT_ID/api-gateway \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="NODE_ENV=production" \
  --set-secrets="DATABASE_URL=database-url:latest"

# Repeat for all services
```

### Using GKE (Google Kubernetes Engine)

```bash
# Create GKE cluster
gcloud container clusters create notification-system \
  --num-nodes=3 \
  --machine-type=n1-standard-2 \
  --zone=us-central1-a

# Get credentials
gcloud container clusters get-credentials notification-system

# Deploy using kubectl (see Kubernetes section)
```

## Kubernetes Deployment

### 1. Create Kubernetes Manifests

Create `k8s/api-gateway-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  labels:
    app: api-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: your-registry/api-gateway:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health/live
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  selector:
    app: api-gateway
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
```

### 2. Create ConfigMaps and Secrets

```bash
# Create secrets
kubectl create secret generic app-secrets \
  --from-literal=database-url='postgresql://...' \
  --from-literal=redis-password='...' \
  --from-literal=jwt-secret='...'

# Create ConfigMap
kubectl create configmap app-config \
  --from-literal=redis-host='redis' \
  --from-literal=rabbitmq-host='rabbitmq'
```

### 3. Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/api-gateway
```

## Domain & SSL Setup

### Using Certbot (Manual)

```bash
# Install Certbot
sudo apt install certbot

# Obtain certificate
sudo certbot certonly --standalone -d api.yourcompany.com

# Auto-renewal
sudo crontab -e
# Add: 0 3 * * * certbot renew --quiet
```

### Using Cloudflare

1. Add your domain to Cloudflare
2. Point DNS to your server IP
3. Enable Cloudflare SSL (Full/Strict mode)
4. Enable HTTP/3 and Brotli compression

### Using AWS Certificate Manager

```bash
# Request certificate
aws acm request-certificate \
  --domain-name api.yourcompany.com \
  --validation-method DNS

# Attach to Load Balancer
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:...
```

## Monitoring Setup

### Prometheus & Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - notification-network

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    networks:
      - notification-network

volumes:
  prometheus-data:
  grafana-data:
```

## Backup & Recovery

### Automated Backups

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker exec postgres pg_dumpall -U postgres > $BACKUP_DIR/postgres_$DATE.sql

# Backup Redis
docker exec redis redis-cli --rdb /data/dump.rdb
docker cp redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR s3://your-backup-bucket/ --recursive

# Keep only last 7 days
find $BACKUP_DIR -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /opt/notification-system/backup.sh
```

## Scaling Guide

### Horizontal Scaling

```bash
# Scale services in Docker Compose
docker-compose -f docker-compose.production.yml up -d --scale email-service=5 --scale push-service=5

# Scale in Kubernetes
kubectl scale deployment api-gateway --replicas=5
```

### Vertical Scaling

Update resource limits in docker-compose or Kubernetes manifests.

## CI/CD with GitHub Actions

See `.github/workflows/deploy.yml` in the main repository.

## Troubleshooting

### Check Service Logs
```bash
docker-compose logs -f service-name
```

### Check Resource Usage
```bash
docker stats
```

### Test Connectivity
```bash
curl https://api.yourcompany.com/api/v1/health
```

---

**Deployment completed! Your notification system is now live! 🎉**
