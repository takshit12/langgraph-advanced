# Dockerfile — containerise the LangGraph agent as a portable HTTP service.
#
# Build:  docker build -t langgraph-agent .
# Run:    docker run -p 8000:8000 --env-file .env langgraph-agent
# Test:   curl -s localhost:8000/health
#
# This image has ZERO dependency on LangSmith / LangGraph Platform. It is a plain
# Python web service you can push to any registry and run on any VPS, ECS, Cloud
# Run, Fly.io, or Kubernetes cluster.

FROM python:3.11-slim

# Don't buffer stdout (so logs show up live) and don't write .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install deps first (this layer is cached unless requirements change → fast rebuilds).
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy the app code (agent.py, app.py, etc.). See .dockerignore for exclusions.
COPY . .

EXPOSE 8000

# 1 uvicorn worker is plenty for a classroom demo. For real load, put this behind
# gunicorn with uvicorn workers, or run multiple replicas behind a load balancer.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
