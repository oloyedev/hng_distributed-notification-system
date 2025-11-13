# API Gateway

This folder contains the API Gateway service for the Distributed Notification System.

Files created:
- `Dockerfile` — container image build instructions
- `docker-compose.yaml` — compose file to run the gateway with supporting infra (RabbitMQ, Redis)
- `.env.example` — example environment variables (copy to `.env` and edit)

Requirements
- Docker and Docker Compose (v2 recommended)
- Optionally Python 3.11 and a virtual environment to run locally

Quick start (PowerShell)

1. Copy example env and edit values where needed:

```powershell
cd 'c:\Users\DELL\Desktop\Dev\hng_distributed-notification-system\api_gateway'
copy .env.example .env
# Edit .env to adjust settings (JWT secret, service URLs, etc.)
```

2. Build and start the stack (compose):

```powershell
docker compose up --build -d
docker compose logs -f
```

3. Stop and remove resources:

```powershell
docker compose down -v
```

Notes
- The compose file uses the service names `rabbitmq` and `redis` so the `RABBITMQ_HOST` and `REDIS_HOST` default values in `.env.example` point to those hostnames. When running compose from the `api_gateway` directory this resolves correctly.
- If you prefer to run locally without Docker, create a virtualenv and install `requirements.txt`, then run `uvicorn app.core.main:app --reload --host 0.0.0.0 --port 3000`.

Healthchecks and ports
- The gateway listens on port `3000` by default (mapped to the host in `docker-compose.yaml`).
- RabbitMQ management UI is exposed on `15672` by the compose file.

Troubleshooting
- If imports (e.g., `httpx`) cannot be resolved in the container, ensure `requirements.txt` lists them and rebuild the image:

```powershell
docker compose build --no-cache
```

- If you need the service to wait for other services to be ready before starting, consider adding an init/wait script or using an entrypoint that polls dependencies.

If you want, I can:
- Add a top-level full-stack `docker-compose.yaml` that launches all microservices and infra, or
- Add a small `entrypoint.sh` that runs DB migrations or init steps before starting the app.
