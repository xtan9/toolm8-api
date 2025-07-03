# Nginx Hands-On Exercises

Complete these exercises to master Nginx configuration and deployment:

## Exercise 1: Basic Reverse Proxy (15 minutes)

### Setup
```bash
# Create nginx directory
mkdir -p nginx

# Start your FastAPI app
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
```

### Task 1.1: Simple Proxy Configuration
```bash
# Create basic nginx config
cat > nginx/basic.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    server {
        listen 8080;
        server_name localhost;
        
        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
        }
    }
}
EOF

# Test the configuration
nginx -t -c $(pwd)/nginx/basic.conf

# Start nginx with this config
nginx -c $(pwd)/nginx/basic.conf

# Test it works
curl http://localhost:8080/health
curl http://localhost:8080/admin/stats

# Stop nginx
nginx -s stop
```

### Task 1.2: Add Request Headers
```bash
# Update config to pass more headers
cat > nginx/headers.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    server {
        listen 8080;
        server_name localhost;
        
        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Restart nginx with new config
nginx -c $(pwd)/nginx/headers.conf
```

### Expected Results:
- ✅ FastAPI app accessible through nginx on port 8080
- ✅ Headers properly forwarded to backend
- ✅ All endpoints work through proxy

## Exercise 2: Location Blocks and Routing (20 minutes)

### Task 2.1: Different Handling for Different Endpoints
```bash
cat > nginx/routing.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    server {
        listen 8080;
        server_name localhost;
        
        # Health check - no logging
        location = /health {
            proxy_pass http://127.0.0.1:8000/health;
            access_log off;
        }
        
        # Admin endpoints - log everything
        location /admin/ {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            access_log /tmp/admin.log;
        }
        
        # API endpoints
        location /api/ {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
        }
        
        # Default location
        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
        }
    }
}
EOF

nginx -s stop
nginx -c $(pwd)/nginx/routing.conf
```

### Task 2.2: Test Location Matching
```bash
# Test different endpoints
curl http://localhost:8080/health
curl http://localhost:8080/admin/stats
curl http://localhost:8080/docs

# Check admin log was created
ls -la /tmp/admin.log

# View admin requests
tail /tmp/admin.log
```

### Challenge: Add Static File Serving
```nginx
# Add this location block to your config
location /static/ {
    alias /var/www/static/;
    expires 1y;
}
```

## Exercise 3: File Upload Optimization (25 minutes)

### Task 3.1: Configure for Large CSV Uploads
```bash
cat > nginx/uploads.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    # Allow large file uploads
    client_max_body_size 100M;
    client_body_timeout 300s;
    
    server {
        listen 8080;
        server_name localhost;
        
        # CSV upload endpoint - special handling
        location = /admin/import-csv {
            proxy_pass http://127.0.0.1:8000/admin/import-csv;
            proxy_set_header Host $host;
            
            # Extended timeouts for processing
            proxy_read_timeout 300s;
            proxy_send_timeout 300s;
            
            # Don't buffer large files
            proxy_request_buffering off;
        }
        
        # Other endpoints
        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
        }
    }
}
EOF

nginx -s stop
nginx -c $(pwd)/nginx/uploads.conf
```

### Task 3.2: Test Large File Upload
```bash
# Create a test CSV file
cat > test.csv << 'EOF'
ai_link,task_label,external_ai_link href
ChatGPT,Writing,https://openai.com/chatgpt
Midjourney,Image Generation,https://midjourney.com
EOF

# Test upload through nginx
curl -X POST \
  -F "file=@test.csv" \
  -F "source=taaft" \
  -F "replace_existing=false" \
  http://localhost:8080/admin/import-csv

# Create larger test file
head -c 10M /dev/urandom > large.csv
curl -X POST \
  -F "file=@large.csv" \
  -F "source=taaft" \
  http://localhost:8080/admin/import-csv

rm large.csv test.csv
```

## Exercise 4: Rate Limiting (20 minutes)

### Task 4.1: Implement Rate Limiting
```bash
cat > nginx/ratelimit.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    # Define rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;
    
    server {
        listen 8080;
        server_name localhost;
        
        # Health check - no rate limiting
        location = /health {
            proxy_pass http://127.0.0.1:8000/health;
            access_log off;
        }
        
        # Upload endpoint - strict rate limiting
        location = /admin/import-csv {
            limit_req zone=upload burst=5 nodelay;
            proxy_pass http://127.0.0.1:8000/admin/import-csv;
            proxy_set_header Host $host;
        }
        
        # Admin endpoints - moderate rate limiting
        location /admin/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
        }
        
        # Default - normal rate limiting
        location / {
            limit_req zone=api burst=50 nodelay;
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
        }
    }
}
EOF

nginx -s stop
nginx -c $(pwd)/nginx/ratelimit.conf
```

### Task 4.2: Test Rate Limiting
```bash
# Test normal requests (should work)
curl http://localhost:8080/health

# Test rate limiting (some should fail with 429)
for i in {1..15}; do
    echo "Request $i:"
    curl -w "%{http_code}\n" -o /dev/null -s http://localhost:8080/admin/stats
    sleep 0.1
done

# Test upload rate limiting
for i in {1..5}; do
    echo "Upload $i:"
    curl -w "%{http_code}\n" -o /dev/null -s -X POST \
      -F "source=taaft" \
      http://localhost:8080/admin/import-csv
done
```

### Expected Results:
- ✅ Health checks work without rate limiting
- ✅ Rapid requests to /admin/ endpoints get 429 errors
- ✅ Upload endpoint has stricter limits

## Exercise 5: Load Balancing (30 minutes)

### Task 5.1: Start Multiple API Instances
```bash
# Stop existing FastAPI
pkill uvicorn

# Start multiple instances
uvicorn app.main:app --host 127.0.0.1 --port 8001 &
uvicorn app.main:app --host 127.0.0.1 --port 8002 &
uvicorn app.main:app --host 127.0.0.1 --port 8003 &

# Wait for them to start
sleep 5
```

### Task 5.2: Configure Load Balancing
```bash
cat > nginx/loadbalance.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    # Define upstream servers
    upstream csv_api {
        least_conn;  # Load balancing method
        server 127.0.0.1:8001 weight=3;
        server 127.0.0.1:8002 weight=2;
        server 127.0.0.1:8003 backup;
    }
    
    server {
        listen 8080;
        server_name localhost;
        
        location / {
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            
            # Add upstream info to response header
            add_header X-Upstream $upstream_addr;
        }
    }
}
EOF

nginx -s stop
nginx -c $(pwd)/nginx/loadbalance.conf
```

### Task 5.3: Test Load Balancing
```bash
# Make multiple requests and see which server responds
for i in {1..10}; do
    echo "Request $i:"
    curl -I http://localhost:8080/health | grep X-Upstream
done

# Test failover by stopping one server
pkill -f "port 8001"

# Test requests still work
curl http://localhost:8080/health
```

## Exercise 6: SSL/HTTPS Setup (25 minutes)

### Task 6.1: Create Self-Signed Certificate
```bash
# Create SSL directory
mkdir -p nginx/ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/nginx.key \
  -out nginx/ssl/nginx.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### Task 6.2: Configure HTTPS
```bash
cat > nginx/ssl.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream csv_api {
        server 127.0.0.1:8001;
        server 127.0.0.1:8002;
    }
    
    # HTTPS server
    server {
        listen 8443 ssl;
        server_name localhost;
        
        ssl_certificate ssl/nginx.crt;
        ssl_certificate_key ssl/nginx.key;
        
        # Modern SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;
        
        location / {
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    
    # HTTP to HTTPS redirect
    server {
        listen 8080;
        server_name localhost;
        return 301 https://$server_name:8443$request_uri;
    }
}
EOF

nginx -s stop
nginx -c $(pwd)/nginx/ssl.conf
```

### Task 6.3: Test HTTPS
```bash
# Test HTTPS (ignore certificate warnings)
curl -k https://localhost:8443/health

# Test HTTP redirect
curl -I http://localhost:8080/health

# Check certificate details
openssl s_client -connect localhost:8443 -servername localhost < /dev/null
```

## Exercise 7: Monitoring and Logging (20 minutes)

### Task 7.1: Advanced Logging Configuration
```bash
cat > nginx/logging.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    # Custom log formats
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
                    
    log_format detailed '$remote_addr - $remote_user [$time_local] '
                       '"$request" $status $body_bytes_sent '
                       '"$http_referer" "$http_user_agent" '
                       'rt=$request_time uct="$upstream_connect_time" '
                       'uht="$upstream_header_time" urt="$upstream_response_time"';
    
    # Access log
    access_log /tmp/nginx_access.log detailed;
    error_log /tmp/nginx_error.log warn;
    
    upstream csv_api {
        server 127.0.0.1:8001;
        server 127.0.0.1:8002;
    }
    
    server {
        listen 8080;
        server_name localhost;
        
        # Status endpoint for monitoring
        location = /nginx_status {
            stub_status on;
            allow 127.0.0.1;
            deny all;
            access_log off;
        }
        
        # Health endpoint - no logging
        location = /health {
            proxy_pass http://csv_api/health;
            access_log off;
        }
        
        # Admin endpoints - detailed logging
        location /admin/ {
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
            access_log /tmp/nginx_admin.log detailed;
        }
        
        location / {
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
        }
    }
}
EOF

nginx -s stop
nginx -c $(pwd)/nginx/logging.conf
```

### Task 7.2: Generate and Analyze Logs
```bash
# Make some requests
curl http://localhost:8080/health
curl http://localhost:8080/admin/stats
curl http://localhost:8080/docs

# Check nginx status
curl http://localhost:8080/nginx_status

# Analyze logs
echo "=== Main Access Log ==="
tail -5 /tmp/nginx_access.log

echo "=== Admin Access Log ==="
tail -5 /tmp/nginx_admin.log

echo "=== Error Log ==="
tail -5 /tmp/nginx_error.log

# Real-time log monitoring
tail -f /tmp/nginx_access.log &
LOG_PID=$!

# Generate some traffic
for i in {1..5}; do
    curl http://localhost:8080/admin/stats > /dev/null 2>&1
    sleep 1
done

kill $LOG_PID
```

## Exercise 8: Performance Optimization (25 minutes)

### Task 8.1: Configure Caching and Compression
```bash
cat > nginx/performance.conf << 'EOF'
events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/json
        application/xml+rss
        image/svg+xml;
    
    # Proxy caching
    proxy_cache_path /tmp/nginx_cache levels=1:2 keys_zone=api_cache:10m 
                     max_size=100m inactive=60m use_temp_path=off;
    
    upstream csv_api {
        server 127.0.0.1:8001;
        server 127.0.0.1:8002;
        keepalive 32;
    }
    
    server {
        listen 8080;
        server_name localhost;
        
        # No caching for admin endpoints
        location /admin/ {
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
            proxy_cache off;
        }
        
        # Cache other endpoints
        location / {
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
            
            # Enable caching
            proxy_cache api_cache;
            proxy_cache_valid 200 302 10m;
            proxy_cache_valid 404 1m;
            proxy_cache_use_stale error timeout invalid_header updating;
            
            # Add cache status header
            add_header X-Cache-Status $upstream_cache_status;
        }
    }
}
EOF

nginx -s stop
nginx -c $(pwd)/nginx/performance.conf
```

### Task 8.2: Test Performance Features
```bash
# Test compression
curl -H "Accept-Encoding: gzip" -I http://localhost:8080/docs | grep -i content-encoding

# Test caching
curl -I http://localhost:8080/health | grep X-Cache-Status
curl -I http://localhost:8080/health | grep X-Cache-Status  # Should show HIT

# Test cache directory
ls -la /tmp/nginx_cache/

# Performance test with multiple requests
time for i in {1..100}; do
    curl -s http://localhost:8080/health > /dev/null
done
```

## Exercise 9: Security Configuration (30 minutes)

### Task 9.1: Implement Security Headers and Access Control
```bash
cat > nginx/security.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=admin:10m rate=5r/s;
    
    upstream csv_api {
        server 127.0.0.1:8001;
        server 127.0.0.1:8002;
    }
    
    server {
        listen 8080;
        server_name localhost;
        
        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        
        # Hide nginx version
        server_tokens off;
        
        # Block common exploit attempts
        location ~* \.(php|asp|aspx|jsp)$ {
            return 444;
        }
        
        # Block access to hidden files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }
        
        # Admin endpoints - restricted access and rate limiting
        location /admin/ {
            # Uncomment to restrict by IP
            # allow 127.0.0.1;
            # allow 192.168.1.0/24;
            # deny all;
            
            limit_req zone=admin burst=10 nodelay;
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
        }
        
        # Public endpoints
        location / {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
        }
        
        # Custom error pages
        error_page 429 /429.html;
        location = /429.html {
            internal;
            return 429 "Rate limit exceeded";
        }
    }
}
EOF

nginx -s stop
nginx -c $(pwd)/nginx/security.conf
```

### Task 9.2: Test Security Features
```bash
# Test security headers
curl -I http://localhost:8080/health | grep -E "X-Frame-Options|X-Content-Type-Options"

# Test blocked file types
curl -I http://localhost:8080/test.php

# Test hidden files
curl -I http://localhost:8080/.env

# Test rate limiting
for i in {1..15}; do
    curl -w "%{http_code} " -o /dev/null -s http://localhost:8080/admin/stats
done
echo ""
```

## Exercise 10: Production Deployment (35 minutes)

### Task 10.1: Create Production-Ready Configuration
```bash
cat > nginx/production.conf << 'EOF'
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
    client_max_body_size 100M;

    # Security
    server_tokens off;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types application/json text/css text/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

    # Upstream
    upstream csv_api {
        least_conn;
        server api1:8000 max_fails=3 fail_timeout=30s;
        server api2:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    server {
        listen 80;
        server_name _;

        location = /health {
            proxy_pass http://csv_api/health;
            access_log off;
        }

        location = /admin/import-csv {
            limit_req zone=upload burst=5 nodelay;
            proxy_pass http://csv_api/admin/import-csv;
            proxy_set_header Host $host;
            proxy_read_timeout 300s;
            proxy_request_buffering off;
        }

        location /admin/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
        }

        location / {
            limit_req zone=api burst=50 nodelay;
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
        }
    }
}
EOF
```

### Task 10.2: Deployment Script
```bash
cat > deploy-nginx.sh << 'EOF'
#!/bin/bash
set -e

echo "Deploying Nginx configuration..."

# Backup current config
if [ -f /etc/nginx/nginx.conf ]; then
    sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)
fi

# Test new configuration
nginx -t -c $(pwd)/nginx/production.conf

# Copy new configuration
sudo cp nginx/production.conf /etc/nginx/nginx.conf

# Reload nginx
sudo nginx -s reload

echo "Nginx deployed successfully!"
EOF

chmod +x deploy-nginx.sh
```

### Task 10.3: Health Check Script
```bash
cat > health-check.sh << 'EOF'
#!/bin/bash

echo "Performing health checks..."

# Test nginx syntax
nginx -t

# Test backend connectivity
curl -f http://localhost:8001/health || echo "Backend 1 down"
curl -f http://localhost:8002/health || echo "Backend 2 down"

# Test through nginx
curl -f http://localhost:8080/health || echo "Nginx proxy failed"

# Test performance
echo "Performance test:"
time curl -s http://localhost:8080/health > /dev/null

echo "Health check complete!"
EOF

chmod +x health-check.sh
./health-check.sh
```

## Cleanup
```bash
# Stop nginx
nginx -s stop

# Stop FastAPI instances
pkill uvicorn

# Clean up files
rm -f /tmp/nginx_*.log
rm -rf /tmp/nginx_cache
rm -f large.csv test.csv

echo "Cleanup complete!"
```

## Success Criteria

After completing all exercises, you should be able to:

✅ Configure nginx as a reverse proxy  
✅ Implement load balancing  
✅ Set up SSL/HTTPS  
✅ Configure rate limiting  
✅ Optimize for file uploads  
✅ Implement security measures  
✅ Set up monitoring and logging  
✅ Deploy production configurations  
✅ Debug nginx issues  
✅ Performance tune configurations  

Congratulations! You now have senior-level Nginx expertise! 🎉