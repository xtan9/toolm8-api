# Docker Learning Exercises

Complete these exercises in order to master Docker, Docker Compose, and Nginx:

## Exercise 1: Basic Docker (15 minutes)

### Task: Build and run your CSV tool
```bash
# 1. Build your image
docker build -t toolm8-api:v1 .

# 2. Run it with environment variables
docker run -d \
  --name csv-tool \
  -p 8000:8000 \
  -e SUPABASE_URL="your_url" \
  -e SUPABASE_ANON_KEY="your_key" \
  toolm8-api:v1

# 3. Test it works
curl http://localhost:8000/health

# 4. View logs
docker logs csv-tool

# 5. Enter the container
docker exec -it csv-tool bash

# 6. Clean up
docker stop csv-tool
docker rm csv-tool
```

### Expected Output:
- Container runs successfully
- Health endpoint returns 200
- You can see FastAPI logs
- You can execute commands inside container

## Exercise 2: Volume Mounting (10 minutes)

### Task: Mount your source code for development
```bash
# Run with source code mounted
docker run -d \
  --name csv-dev \
  -p 8000:8000 \
  -v $(pwd)/app:/app/app \
  -e SUPABASE_URL="your_url" \
  toolm8-api:v1

# Make a change to app/main.py (add a comment)
echo "# Development mode" >> app/main.py

# Check if change appears in container
docker exec csv-dev cat /app/app/main.py

# Clean up
docker stop csv-dev && docker rm csv-dev
```

### Learn: Volume vs Bind Mounts
```bash
# Bind mount (what you just did)
-v /host/path:/container/path

# Named volume
-v volume_name:/container/path

# Anonymous volume
-v /container/path
```

## Exercise 3: Docker Compose Basics (20 minutes)

### Task: Create development environment
```bash
# 1. Create docker-compose.dev.yml
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
    environment:
      - DEBUG=true
    restart: unless-stopped
EOF

# 2. Start with compose
docker-compose -f docker-compose.dev.yml up -d

# 3. Check status
docker-compose -f docker-compose.dev.yml ps

# 4. View logs
docker-compose -f docker-compose.dev.yml logs -f api

# 5. Scale the service
docker-compose -f docker-compose.dev.yml up -d --scale api=2

# 6. Stop everything
docker-compose -f docker-compose.dev.yml down
```

### Challenge: Add Redis
```yaml
# Add this to your docker-compose.dev.yml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Exercise 4: Multi-Container App (25 minutes)

### Task: Add Nginx reverse proxy
```bash
# 1. Create nginx configuration
mkdir -p nginx
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        
        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
        }
        
        location /health {
            proxy_pass http://api/health;
            access_log off;
        }
    }
}
EOF

# 2. Update docker-compose.dev.yml
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
      
  api:
    build: .
    expose:
      - "8000"
    environment:
      - DEBUG=true
    volumes:
      - ./app:/app/app
EOF

# 3. Start the stack
docker-compose -f docker-compose.dev.yml up -d

# 4. Test through nginx
curl http://localhost/health

# 5. Check nginx logs
docker-compose -f docker-compose.dev.yml logs nginx
```

## Exercise 5: Environment Management (15 minutes)

### Task: Create production configuration
```bash
# 1. Create .env file
cat > .env << 'EOF'
SUPABASE_URL=your_production_url
SUPABASE_ANON_KEY=your_production_key
DEBUG=false
EOF

# 2. Create docker-compose.prod.yml
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
    restart: unless-stopped
      
  api:
    image: toolm8-api:latest
    expose:
      - "8000"
    env_file: .env
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
EOF

# 3. Build production image
docker build -t toolm8-api:latest .

# 4. Start production stack
docker-compose -f docker-compose.prod.yml up -d

# 5. Test it
curl http://localhost/health
```

## Exercise 6: Debugging and Troubleshooting (20 minutes)

### Task: Practice debugging techniques
```bash
# 1. Intentionally break something
# Edit nginx/nginx.conf and add invalid syntax
echo "invalid syntax;" >> nginx/nginx.conf

# 2. Try to start
docker-compose up nginx

# 3. Debug the issue
docker-compose logs nginx
docker-compose exec nginx nginx -t

# 4. Fix the config
# Remove the invalid line

# 5. Practice container debugging
docker-compose exec api bash
# Inside container:
ps aux
netstat -tulpn
curl localhost:8000/health
exit

# 6. Monitor resources
docker stats
```

## Exercise 7: Advanced Nginx (30 minutes)

### Task: Add advanced features
```nginx
# Update nginx/nginx.conf with advanced features
events {
    worker_connections 1024;
}

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # Upstream with load balancing
    upstream api {
        least_conn;
        server api:8000 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 80;
        
        # File upload size for CSV
        client_max_body_size 100M;
        
        # Health check (no rate limiting)
        location = /health {
            proxy_pass http://api/health;
            access_log off;
        }
        
        # API endpoints with rate limiting
        location /admin/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # Default location
        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
        }
    }
}
```

### Test rate limiting:
```bash
# Restart nginx
docker-compose restart nginx

# Test rate limiting (run multiple times quickly)
for i in {1..15}; do curl -w "%{http_code}\n" http://localhost/admin/stats; done
```

## Exercise 8: Production Deployment Simulation (25 minutes)

### Task: Simulate production deployment
```bash
# 1. Create deployment script
cat > deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "Building new image..."
docker build -t toolm8-api:latest .

echo "Running tests..."
docker run --rm toolm8-api:latest pytest

echo "Backing up current deployment..."
docker-compose -f docker-compose.prod.yml down

echo "Starting new deployment..."
docker-compose -f docker-compose.prod.yml up -d

echo "Waiting for health check..."
sleep 10
curl -f http://localhost/health || exit 1

echo "Deployment successful!"
EOF

chmod +x deploy.sh

# 2. Run deployment
./deploy.sh

# 3. Verify deployment
docker-compose -f docker-compose.prod.yml ps
curl http://localhost/health
```

## Exercise 9: Monitoring Setup (20 minutes)

### Task: Add monitoring
```yaml
# Add to docker-compose.prod.yml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
```

```yaml
# Create monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
```

## Exercise 10: Cleanup and Best Practices (10 minutes)

### Task: Clean up and optimize
```bash
# 1. Stop all containers
docker-compose down
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.prod.yml down

# 2. Remove unused resources
docker system prune -a --volumes

# 3. Optimize Dockerfile (add to your Dockerfile)
# Use .dockerignore
cat > .dockerignore << 'EOF'
.git
.github
tests/
*.md
.env*
docker-compose*.yml
EOF

# 4. Check image size
docker images toolm8-api

# 5. Security scan (if available)
docker scout cves toolm8-api:latest || echo "Docker Scout not available"
```

## Success Criteria

After completing these exercises, you should be able to:

✅ Build and run Docker containers  
✅ Use volumes for development  
✅ Write docker-compose files  
✅ Configure Nginx as reverse proxy  
✅ Manage different environments  
✅ Debug container issues  
✅ Implement production best practices  
✅ Monitor applications  
✅ Deploy applications safely  

## Next Steps

1. **Practice with your real app**: Use these skills with your CSV tool
2. **Learn Kubernetes**: Next level container orchestration
3. **CI/CD**: Integrate with GitHub Actions
4. **Security**: Learn container security scanning
5. **Monitoring**: Add Grafana, ELK stack

Congratulations! You now have senior-level Docker knowledge! 🎉