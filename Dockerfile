
# EnergySense - Multi-Stage Production Dockerfile

# Stage 1: Build React Frontend
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend and datasets
COPY backend/ ./backend/
COPY datasets/ ./datasets/

# Copy compiled React frontend
COPY --from=frontend-builder /app/frontend/dist ./backend/frontend_dist

# Create non-root user
RUN useradd -m -u 1000 user && \
    chown -R user:user /app

USER user

WORKDIR /app/backend

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
