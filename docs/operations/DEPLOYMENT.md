# Operations and Deployment Guide

## Production Architecture
- **API Backend**: FastAPI application deployed as containerized service (Google Cloud Run or Kubernetes).
- **Web Frontend**: Vue 3 + TypeScript single-page application served via static CDN or Cloud Storage.
- **Search & Retrieval**: Managed Elasticsearch 8 (Elastic Cloud or self-hosted cluster).
- **Relational Metadata**: Managed PostgreSQL or Cloud SQL (SQLite used for local single-node mode).

## Environment Configuration
```env
PORT=8000
DATABASE_URL=sqlite+aiosqlite:///./narrative_copilot.db
ELASTICSEARCH_URL=http://localhost:9200
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
VERTEX_MODEL_NAME=gemini-2.0-flash
```

## Docker Compose Quickstart
```bash
# Start Elasticsearch, API backend, and Web frontend
docker compose up -d

# Verify readiness
curl http://localhost:8000/ready
```
