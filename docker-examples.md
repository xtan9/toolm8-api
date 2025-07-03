# Hands-On Docker Examples for Your CSV Tool

## Example 1: Basic Development Setup

### Step 1: Build and Run Locally
```bash
# Build your image
docker build -t toolm8-api .

# Run with environment variables
docker run -d \
  --name toolm8-dev \
  -p 8000:8000 \
  -e SUPABASE_URL="your_url" \
  -e SUPABASE_ANON_KEY="your_key" \
  toolm8-api

# Test it
curl http://localhost:8000/health
```

### Step 2: Development with Live Reload
```bash
# Mount source code for live development
docker run -d \
  --name toolm8-dev \
  -p 8000:8000 \
  -v $(pwd)/app:/app/app \
  -e SUPABASE_URL="your_url" \
  toolm8-api

# Now changes to app/ will reflect immediately
```

## Example 2: Docker Compose Development

### docker-compose.dev.yml
```yaml
version: '3.8'

services:
  api:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: toolm8-api-dev
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app:ro  # Read-only mount
      - ./tests:/app/tests:ro
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET}
      - DEBUG=true
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    restart: unless-stopped

  # Optional: Redis for caching (future enhancement)
  redis:
    image: redis:7-alpine
    container_name: toolm8-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:

networks:
  default:
    name: toolm8-network
```

### Usage:
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f api

# Run tests inside container
docker-compose -f docker-compose.dev.yml exec api pytest

# Stop everything
docker-compose -f docker-compose.dev.yml down
```

## Example 3: Production Setup with Nginx

### Production docker-compose.yml
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:1.24-alpine
    container_name: toolm8-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - frontend
      - backend

  api:
    build: .
    container_name: toolm8-api
    expose:
      - "8000"  # Only expose to other containers, not host
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET}
    volumes:
      - api_logs:/app/logs
    restart: unless-stopped
    networks:
      - backend
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  # Log aggregation
  fluentd:
    image: fluent/fluentd:v1.16-1
    container_name: toolm8-logs
    volumes:
      - nginx_logs:/var/log/nginx:ro
      - api_logs:/var/log/api:ro
      - ./fluentd/conf:/fluentd/etc
    networks:
      - backend
    restart: unless-stopped

volumes:
  nginx_logs:
  api_logs:

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # Backend network isolated from internet
```

## Example 4: Advanced Nginx Configuration

### nginx/nginx.conf
```nginx
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Log formats
    log_format detailed '$remote_addr - $remote_user [$time_local] '
                       '"$request" $status $body_bytes_sent '
                       '"$http_referer" "$http_user_agent" '
                       'rt=$request_time uct="$upstream_connect_time" '
                       'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log detailed;

    # Performance tuning
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 100M;  # For CSV uploads
    client_body_timeout 60s;
    client_header_timeout 60s;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

    # Upstream backend
    upstream api_backend {
        least_conn;
        server api:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    server {
        listen 80;
        server_name _;

        # Health check endpoint (no rate limiting)
        location = /health {
            proxy_pass http://api_backend/health;
            proxy_set_header Host $host;
            access_log off;
        }

        # CSV upload endpoint (special rate limiting)
        location = /admin/import-csv {
            limit_req zone=upload burst=5 nodelay;
            
            proxy_pass http://api_backend/admin/import-csv;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Upload-specific timeouts
            proxy_read_timeout 300s;
            proxy_send_timeout 300s;
            proxy_request_buffering off;
        }

        # Admin endpoints (stricter rate limiting)
        location /admin/ {
            limit_req zone=api burst=10 nodelay;
            
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # All other endpoints
        location / {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Connection reuse
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }

        # Custom error pages
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }

        # Block common exploit attempts
        location ~* \.(php|asp|aspx|jsp)$ {
            return 444;
        }
    }
}
```

## Example 5: Multi-Environment Setup

### docker-compose.override.yml (Development)
```yaml
# Automatically loaded in development
version: '3.8'

services:
  api:
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./app:/app/app:rw
      - ./tests:/app/tests:rw
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    ports:
      - "8000:8000"  # Expose directly for development
```

### docker-compose.prod.yml (Production)
```yaml
version: '3.8'

services:
  api:
    image: toolm8-api:latest
    environment:
      - DEBUG=false
      - LOG_LEVEL=info
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### Usage:
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

## Example 6: Monitoring and Debugging

### Add monitoring to docker-compose.yml
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: toolm8-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    networks:
      - backend

  grafana:
    image: grafana/grafana:latest
    container_name: toolm8-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - backend

volumes:
  grafana_data:
```

### Debugging Commands:
```bash
# Check container health
docker-compose ps
docker-compose top

# View logs with timestamps
docker-compose logs -t -f api

# Monitor resource usage
docker stats $(docker-compose ps -q)

# Enter container for debugging
docker-compose exec api bash

# Check network connectivity
docker-compose exec api ping nginx
docker-compose exec nginx ping api

# Inspect volumes
docker volume ls
docker volume inspect toolm8_api_logs

# Debug nginx configuration
docker-compose exec nginx nginx -t
docker-compose exec nginx nginx -s reload
```

## Example 7: CI/CD Pipeline Integration

### .github/workflows/docker.yml
```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t toolm8-api:${{ github.sha }} .
      
      - name: Run tests
        run: |
          docker run --rm \
            -e SUPABASE_URL=${{ secrets.SUPABASE_URL }} \
            toolm8-api:${{ github.sha }} \
            pytest
      
      - name: Deploy to production
        if: github.ref == 'refs/heads/main'
        run: |
          # Your deployment commands here
          echo "Deploying to production..."
```

This comprehensive guide gives you everything needed to master Docker, Docker Compose, and Nginx for production-grade applications!