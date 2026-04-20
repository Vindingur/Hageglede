# Multi-stage Dockerfile for FastAPI application
FROM python:3.11-alpine AS builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev linux-headers

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY src/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Second stage: runtime
FROM python:3.11-alpine

# Install runtime dependencies
RUN apk add --no-cache sqlite libstdc++

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ .

# Create data directory and set permissions
RUN mkdir -p /data && chown -R appuser:appgroup /data

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "hageglede.main:app", "--host", "0.0.0.0", "--port", "8000"]