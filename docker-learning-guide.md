# Docker Mastery: Beginner to Senior Developer

## Part 1: Docker Fundamentals

### What is Docker?
Docker packages applications and their dependencies into **containers** - lightweight, portable units that run consistently across environments.

### Key Concepts:

#### **Images vs Containers**
- **Image**: Blueprint/template (like a class in programming)
- **Container**: Running instance of an image (like an object)

```bash
# Think of it like:
Class Car {}           # = Docker Image
Car myCar = new Car()  # = Docker Container
```

#### **Dockerfile**: Recipe to build an image
```dockerfile
# Every instruction creates a new layer
FROM python:3.10-slim    # Base layer
RUN apt-get update       # Layer 2
COPY app/ /app/          # Layer 3
CMD ["python", "app.py"] # Layer 4
```

### Docker Architecture:
```
┌─────────────────┐
│   Docker Client │ ← You run commands here
└─────────┬───────┘
          │
┌─────────▼───────┐
│  Docker Daemon  │ ← Does the actual work
│  (dockerd)      │
└─────────┬───────┘
          │
┌─────────▼───────┐
│   Containers    │ ← Your apps run here
│   Images        │
│   Networks      │
│   Volumes       │
└─────────────────┘
```

## Part 2: Essential Docker Commands

### Image Management:
```bash
# Build image from Dockerfile
docker build -t myapp:v1.0 .
docker build -t myapp:latest --no-cache .  # Force rebuild

# List images
docker images
docker image ls

# Remove images
docker rmi myapp:v1.0
docker image prune        # Remove unused images
docker system prune -a    # Remove everything unused
```

### Container Management:
```bash
# Run containers
docker run myapp                    # Run once and exit
docker run -d myapp                 # Run in background (detached)
docker run -p 8000:8000 myapp      # Map ports (host:container)
docker run -v /host:/container myapp # Mount volumes
docker run --name mycontainer myapp  # Give it a name

# List containers
docker ps           # Running containers
docker ps -a        # All containers (including stopped)

# Control containers
docker start mycontainer
docker stop mycontainer
docker restart mycontainer
docker kill mycontainer    # Force stop

# Interact with containers
docker exec -it mycontainer bash    # Enter running container
docker logs mycontainer             # View logs
docker logs -f mycontainer          # Follow logs real-time
```

### Advanced Docker Commands:
```bash
# Inspect containers/images
docker inspect mycontainer
docker stats mycontainer    # Resource usage
docker top mycontainer      # Running processes

# Copy files
docker cp file.txt mycontainer:/app/
docker cp mycontainer:/app/file.txt ./

# Network management
docker network ls
docker network create mynetwork
docker run --network mynetwork myapp
```

## Part 3: Advanced Dockerfile Techniques

### Multi-stage Builds (Senior Level):
```dockerfile
# Stage 1: Build dependencies
FROM node:16 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Stage 2: Runtime image
FROM node:16-alpine AS runtime
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
CMD ["node", "server.js"]
```

### Best Practices Dockerfile:
```dockerfile
FROM python:3.10-slim

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use exec form for proper signal handling
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Layer Optimization:
```dockerfile
# ❌ Bad: Creates many layers
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y git
RUN rm -rf /var/lib/apt/lists/*

# ✅ Good: Single layer
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*
```

## Part 4: Docker Compose Mastery

### What is Docker Compose?
Tool for defining and running multi-container applications using YAML files.

### Basic docker-compose.yml:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
    volumes:
      - .:/app
    depends_on:
      - db
      
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Advanced Docker Compose Features:

#### **Environment Files:**
```yaml
# docker-compose.yml
services:
  web:
    env_file:
      - .env
      - .env.local
```

#### **Profiles (Different Environments):**
```yaml
services:
  web:
    build: .
    
  nginx:
    image: nginx
    profiles: ["production"]
    
  debug:
    image: myapp:debug
    profiles: ["development"]
```

```bash
# Run specific profiles
docker-compose --profile production up
docker-compose --profile development up
```

#### **Override Files:**
```yaml
# docker-compose.override.yml (automatically loaded)
services:
  web:
    volumes:
      - .:/app  # Mount source for development
    environment:
      - DEBUG=true
```

#### **Networks and Service Discovery:**
```yaml
services:
  web:
    networks:
      - frontend
      - backend
      
  api:
    networks:
      - backend
      
  db:
    networks:
      - backend

networks:
  frontend:
  backend:
    internal: true  # No external access
```

### Docker Compose Commands:
```bash
# Basic operations
docker-compose up                    # Start all services
docker-compose up -d                 # Start in background
docker-compose down                  # Stop and remove containers
docker-compose down -v               # Also remove volumes

# Service management
docker-compose start web             # Start specific service
docker-compose stop web              # Stop specific service
docker-compose restart web           # Restart specific service

# Scaling
docker-compose up -d --scale web=3   # Run 3 instances of web service

# Logs and debugging
docker-compose logs                  # All service logs
docker-compose logs -f web           # Follow web service logs
docker-compose exec web bash         # Enter web container

# Building and updating
docker-compose build                 # Build all services
docker-compose build --no-cache web  # Force rebuild web service
docker-compose pull                  # Pull latest images
```

## Part 5: Nginx Mastery

### What is Nginx?
High-performance web server, reverse proxy, load balancer, and HTTP cache.

### Key Nginx Concepts:

#### **Server Blocks (Virtual Hosts):**
```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    
    location / {
        proxy_pass http://backend;
    }
}
```

#### **Location Blocks (URL Routing):**
```nginx
server {
    listen 80;
    
    # Exact match
    location = /health {
        return 200 "OK";
    }
    
    # Prefix match
    location /api/ {
        proxy_pass http://api-backend/;
    }
    
    # Regex match
    location ~* \.(jpg|jpeg|png|gif)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Default fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Production Nginx Configuration:
```nginx
# nginx.conf
user nginx;
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

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/xml+rss 
               application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    # Upstream servers
    upstream api_backend {
        server api:8000;
        # server api2:8000 backup;  # Backup server
    }

    server {
        listen 80;
        server_name _;

        # File upload size
        client_max_body_size 100M;
        client_body_timeout 60s;

        # Rate limiting for API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check (no logging)
        location /health {
            proxy_pass http://api_backend/health;
            access_log off;
        }

        # Static files with caching
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Default location
        location / {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### SSL/HTTPS Configuration:
```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/ssl/certs/example.com.pem;
    ssl_certificate_key /etc/ssl/private/example.com.key;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    location / {
        proxy_pass http://backend;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}
```

## Part 6: Advanced Patterns

### Load Balancing:
```nginx
upstream backend {
    least_conn;  # Load balancing method
    server api1:8000 weight=3;
    server api2:8000 weight=1;
    server api3:8000 backup;
}
```

### Blue-Green Deployment:
```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      
  app-blue:
    image: myapp:blue
    
  app-green:
    image: myapp:green
```

```nginx
# Switch traffic by changing upstream
upstream backend {
    server app-blue:8000;  # Change to app-green:8000 for deployment
}
```

### Health Checks and Circuit Breakers:
```nginx
upstream backend {
    server api1:8000 max_fails=3 fail_timeout=30s;
    server api2:8000 max_fails=3 fail_timeout=30s;
}
```

## Part 7: Production Best Practices

### Security:
```dockerfile
# Use specific versions
FROM python:3.10.12-slim

# Run as non-root user
USER 1000:1000

# Read-only root filesystem
COPY --chown=1000:1000 app/ /app/
```

### Monitoring and Logging:
```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Resource Limits:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

## Part 8: Troubleshooting Commands

```bash
# Debug containers
docker logs --tail 50 -f container_name
docker exec -it container_name bash
docker inspect container_name

# Check resource usage
docker stats
docker system df

# Network debugging
docker network ls
docker network inspect network_name

# Clean up
docker system prune -a --volumes
docker container prune
docker image prune -a
```

This guide covers everything a senior developer needs to know about Docker, Docker Compose, and Nginx. Practice with your CSV tool project to solidify these concepts!