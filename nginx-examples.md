# Nginx Practical Examples for Your CSV Tool

## Example 1: Basic Reverse Proxy for CSV API

### Simple Configuration
```nginx
# /etc/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name _;
        
        # Proxy all requests to FastAPI
        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Test this configuration:
```bash
# Start your FastAPI app
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Start nginx with this config
nginx -c /path/to/nginx.conf

# Test
curl http://localhost/health
curl http://localhost/admin/stats
```

## Example 2: Production Configuration for CSV Tool

### Full Production Setup
```nginx
# nginx/nginx.conf
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
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time';
    
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;

    # CSV upload optimization
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        application/json
        application/javascript
        text/css
        text/plain
        text/xml;

    # Rate limiting for CSV API
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

    # Upstream backend
    upstream csv_api {
        server api:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    server {
        listen 80;
        server_name _;

        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Health check (no rate limiting, no logging)
        location = /health {
            proxy_pass http://csv_api/health;
            access_log off;
            proxy_set_header Host $host;
        }

        # CSV upload endpoint (special handling)
        location = /admin/import-csv {
            limit_req zone=upload burst=5 nodelay;
            
            # Extended timeouts for large file processing
            proxy_read_timeout 300s;
            proxy_send_timeout 300s;
            proxy_connect_timeout 60s;
            
            # Don't buffer request body (stream large files)
            proxy_request_buffering off;
            
            proxy_pass http://csv_api/admin/import-csv;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Admin endpoints (moderate rate limiting)
        location /admin/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Admin-specific security
            # Uncomment to restrict admin access to specific IPs
            # allow 192.168.1.0/24;
            # deny all;
        }

        # All other endpoints
        location / {
            limit_req zone=api burst=50 nodelay;
            
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Connection reuse
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }

        # Block common exploit attempts
        location ~* \.(php|asp|aspx|jsp)$ {
            return 444;  # Close connection without response
        }
        
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }

        # Custom error pages
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
            internal;
        }
        
        error_page 429 /429.html;
        location = /429.html {
            root /usr/share/nginx/html;
            internal;
        }
    }
}
```

## Example 3: SSL/HTTPS Configuration

### HTTPS Setup for Production
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates (Let's Encrypt example)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Your CSV API configuration (same as above)
    location / {
        proxy_pass http://csv_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## Example 4: Load Balancing Multiple API Instances

### Multiple FastAPI Instances
```nginx
# Define multiple backend servers
upstream csv_api_cluster {
    least_conn;  # Use least connections load balancing
    
    server api1:8000 weight=3 max_fails=3 fail_timeout=30s;
    server api2:8000 weight=3 max_fails=3 fail_timeout=30s;
    server api3:8000 weight=1 max_fails=3 fail_timeout=30s backup;
    
    # Connection pooling
    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://csv_api_cluster;
        
        # Headers for load balancing
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Connection reuse
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        
        # Failover settings
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_next_upstream_tries 3;
        proxy_next_upstream_timeout 30s;
    }
}
```

## Example 5: Monitoring and Debugging Configuration

### Configuration with Enhanced Logging
```nginx
http {
    # Detailed log format for debugging
    log_format debug '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time" '
                    'upstream="$upstream_addr" '
                    'cache="$upstream_cache_status"';

    # Normal access log
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    server {
        listen 80;
        
        # Use debug logging for troubleshooting
        access_log /var/log/nginx/debug.log debug;
        error_log /var/log/nginx/error.log debug;
        
        # Nginx status endpoint
        location = /nginx_status {
            stub_status on;
            allow 127.0.0.1;
            allow 172.16.0.0/12;  # Docker networks
            deny all;
            access_log off;
        }
        
        # Your API endpoints
        location / {
            proxy_pass http://csv_api;
            proxy_set_header Host $host;
        }
    }
}
```

### Monitoring Endpoints
```nginx
# Add this location block for monitoring
location = /nginx_status {
    stub_status on;
    allow 127.0.0.1;
    deny all;
    access_log off;
}

# Custom health check that tests backend
location = /nginx_health {
    access_log off;
    return 200 "nginx healthy\n";
    add_header Content-Type text/plain;
}
```

## Example 6: Development vs Production Configurations

### Development Configuration (nginx/dev.conf)
```nginx
events {
    worker_connections 1024;
}

http {
    # Simple logging for development
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log debug;
    
    # Allow large uploads
    client_max_body_size 100M;
    
    upstream dev_api {
        server api:8000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # Disable caching in development
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
        
        # CORS for development (if needed)
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range";
        
        location / {
            proxy_pass http://dev_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### Production Configuration (nginx/prod.conf)
```nginx
# Use the full production config from Example 2
# Key differences from dev:
# - Rate limiting enabled
# - Security headers
# - Optimized logging
# - No CORS headers
# - Caching enabled
# - Connection pooling
```

## Example 7: Docker-Specific Configuration

### Nginx Configuration for Docker Compose
```nginx
# nginx/docker.conf
events {
    worker_connections 1024;
}

http {
    # Docker-specific upstream
    upstream docker_api {
        # Use Docker service name
        server toolm8-api:8000;
    }
    
    server {
        listen 80;
        server_name _;
        
        # Docker health check
        location = /docker-health {
            access_log off;
            return 200 "nginx in docker\n";
            add_header Content-Type text/plain;
        }
        
        location / {
            proxy_pass http://docker_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## Example 8: Testing Configurations

### Test Script for Your Configurations
```bash
#!/bin/bash
# test-nginx-config.sh

echo "Testing Nginx configurations for CSV tool..."

# Test 1: Basic syntax
echo "1. Testing syntax..."
nginx -t -c nginx/nginx.conf

# Test 2: Check if upstream is reachable
echo "2. Testing backend connectivity..."
curl -f http://localhost:8000/health || echo "Backend not running"

# Test 3: Test through nginx
echo "3. Testing through nginx..."
curl -f http://localhost/health || echo "Nginx proxy failed"

# Test 4: Test CSV upload endpoint
echo "4. Testing CSV upload endpoint..."
curl -X POST -F "file=@test.csv" -F "source=taaft" http://localhost/admin/import-csv

# Test 5: Test rate limiting
echo "5. Testing rate limiting..."
for i in {1..15}; do
    curl -w "%{http_code}\n" -o /dev/null -s http://localhost/admin/stats
done

# Test 6: Test large file upload
echo "6. Testing large file handling..."
dd if=/dev/zero of=large.csv bs=1M count=50
curl -X POST -F "file=@large.csv" -F "source=taaft" http://localhost/admin/import-csv
rm large.csv

echo "Testing complete!"
```

## Example 9: Performance Tuning for CSV Processing

### High-Performance Configuration
```nginx
# Optimized for large CSV file uploads
events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
    worker_rlimit_nofile 65535;
}

http {
    # Optimize for large file uploads
    client_max_body_size 500M;
    client_body_buffer_size 1M;
    client_body_timeout 300s;
    client_header_timeout 300s;
    
    # Proxy buffering optimization
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
    proxy_busy_buffers_size 8k;
    
    # For very large files, consider disabling buffering
    # proxy_request_buffering off;
    # proxy_buffering off;
    
    # Extended timeouts for CSV processing
    proxy_connect_timeout 60s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    
    # Your upstream and server blocks...
}
```

These examples provide real-world nginx configurations specifically tailored for your CSV import tool!