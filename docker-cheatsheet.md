# Docker Commands Cheat Sheet

## Essential Docker Commands

### Images
```bash
# Build
docker build -t myapp:tag .
docker build --no-cache -t myapp .

# List & Remove
docker images
docker rmi image_name
docker image prune -a

# Push/Pull
docker push myapp:tag
docker pull myapp:tag
```

### Containers
```bash
# Run
docker run -d --name myapp -p 8000:8000 myapp
docker run -it --rm myapp bash          # Interactive, auto-remove
docker run -v /host:/container myapp     # Volume mount

# Control
docker start/stop/restart container_name
docker kill container_name
docker rm container_name

# Inspect
docker ps                               # Running containers
docker ps -a                           # All containers
docker logs -f container_name           # Follow logs
docker exec -it container_name bash     # Enter container
docker inspect container_name           # Detailed info
docker stats container_name             # Resource usage
```

### System
```bash
# Clean up
docker system prune -a --volumes        # Remove everything unused
docker container prune                  # Remove stopped containers
docker image prune -a                   # Remove unused images
docker volume prune                     # Remove unused volumes

# Info
docker system df                        # Disk usage
docker info                            # System info
```

## Docker Compose Commands

### Basic Operations
```bash
# Start/Stop
docker-compose up -d                    # Start in background
docker-compose down                     # Stop and remove
docker-compose down -v                  # Also remove volumes

# Individual services
docker-compose start/stop/restart web
docker-compose up -d --scale web=3      # Scale service

# Build
docker-compose build                    # Build all services
docker-compose build --no-cache web     # Force rebuild service
```

### Debugging
```bash
# Logs
docker-compose logs -f                  # All services
docker-compose logs -f web              # Specific service

# Execute commands
docker-compose exec web bash            # Enter container
docker-compose run --rm web pytest      # Run one-off command

# Status
docker-compose ps                       # List services
docker-compose top                      # Running processes
```

## Nginx Commands

### Configuration
```bash
# Test configuration
nginx -t

# Reload configuration
nginx -s reload

# Stop nginx
nginx -s stop
nginx -s quit                          # Graceful shutdown
```

### Inside Docker
```bash
# Test config in container
docker exec nginx nginx -t

# Reload config
docker exec nginx nginx -s reload

# View logs
docker logs -f nginx
```

## Troubleshooting

### Common Issues
```bash
# Port already in use
docker ps                              # Check what's using the port
sudo lsof -i :8000                     # Find process using port
docker-compose down                     # Stop services

# Permission denied
sudo chown -R $USER:$USER .            # Fix file ownership
docker run --user $(id -u):$(id -g)    # Run as current user

# Out of disk space
docker system df                       # Check usage
docker system prune -a --volumes       # Clean up

# Container won't start
docker logs container_name             # Check logs
docker run -it --entrypoint bash image # Debug interactively
```

### Debug Network Issues
```bash
# List networks
docker network ls

# Inspect network
docker network inspect network_name

# Test connectivity
docker exec container1 ping container2
docker exec container1 curl http://container2:8000/health
```

### Debug Volume Issues
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect volume_name

# Check mounted files
docker exec container ls -la /mount/path
```

## Performance Tips

### Dockerfile Optimization
```dockerfile
# Use multi-stage builds
FROM node:16 AS builder
# ... build steps
FROM node:16-alpine AS runtime
COPY --from=builder /app/dist ./dist

# Order instructions by change frequency
COPY requirements.txt .    # Changes rarely
RUN pip install -r requirements.txt
COPY . .                  # Changes often

# Use .dockerignore
# Add to .dockerignore: node_modules, .git, tests/
```

### Resource Management
```yaml
# docker-compose.yml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    restart: unless-stopped
```

### Health Checks
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

## Security Best Practices

```dockerfile
# Use non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Use specific versions
FROM python:3.10.12-slim

# Scan for vulnerabilities
docker scout cves myapp:latest
```

## Quick Reference

### Most Used Commands
```bash
# Development workflow
docker-compose up -d --build           # Build and start
docker-compose logs -f api              # Watch logs
docker-compose exec api bash            # Debug
docker-compose down                     # Stop

# Production deployment
docker build -t myapp:v1.0 .
docker run -d --name myapp -p 80:8000 myapp:v1.0
docker logs -f myapp

# Emergency commands
docker kill $(docker ps -q)            # Kill all containers
docker system prune -a --volumes --force # Nuclear cleanup
```

### Environment Variables
```bash
# .env file
POSTGRES_DB=myapp
POSTGRES_USER=user
POSTGRES_PASSWORD=secret

# Use in docker-compose.yml
environment:
  - POSTGRES_DB=${POSTGRES_DB}
```

This cheat sheet covers 90% of what you'll need for daily Docker/Nginx operations!