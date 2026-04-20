# Multi-stage Dockerfile for Hageglede (Hageplan)
# Production FastAPI with SQLite persistence

# Stage 1: Builder for frontend assets (if needed)
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/ .
# If you have npm build steps, add them here
# RUN npm install && npm run build

# Stage 2: Python builder
FROM python:3.11-slim AS python-builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY app/ ./app/
COPY scripts/ ./scripts/

# Stage 3: Production runtime
FROM python:3.11-slim
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy frontend assets (from frontend-builder or directly)
COPY --from=frontend-builder /app/frontend /app/frontend

# Copy application code
COPY src/ ./src/
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create volume directory for SQLite
RUN mkdir -p /data
VOLUME /data

# Set environment variables
ENV DATABASE_URL="sqlite:////data/hageglede.db"
ENV PYTHONPATH="/app"
ENV PORT=8000
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]