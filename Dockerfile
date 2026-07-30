# syntax=docker/dockerfile:1.4
# Stage 1: Build React Frontend SPA
FROM node:22-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Python dependencies
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-builder /frontend/dist /app/frontend/dist


# Stage 3: Production final runtime image
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000


CMD gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:${PORT:-8000} --timeout 120 --keep-alive 5 app.main:app

