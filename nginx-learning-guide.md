# Nginx Mastery: Complete Learning Guide

## Part 1: What is Nginx?

Nginx (pronounced "engine-x") is a high-performance web server, reverse proxy, load balancer, and HTTP cache. Originally created to solve the C10K problem (handling 10,000+ concurrent connections).

### Core Concepts:

#### **Web Server vs Reverse Proxy**
```
Web Server (serving static files):
Client → Nginx → Static Files (HTML, CSS, JS, images)

Reverse Proxy (forwarding to backend):
Client → Nginx → Backend Server (Python, Node.js, etc.)
```

#### **Event-Driven Architecture**
Unlike Apache (process-based), Nginx uses an event-driven model:
- Single master process
- Multiple worker processes
- Each worker handles thousands of connections
- Non-blocking I/O

## Part 2: Nginx Configuration Structure

### Main Configuration File: `/etc/nginx/nginx.conf`
```nginx
# Global context
user nginx;
worker_processes auto;

# Events context
events {
    worker_connections 1024;
}

# HTTP context
http {
    # HTTP-level directives
    
    # Server context
    server {
        listen 80;
        server_name example.com;
        
        # Location context
        location / {
            # Location-specific directives
        }
    }
}
```

### Configuration Hierarchy:
```
Global Context
├── Events Context
└── HTTP Context
    ├── Upstream Context
    └── Server Context
        └── Location Context
```

## Part 3: Core Directives

### Server Block (Virtual Host)
```nginx
server {
    listen 80;                          # Port to listen on
    listen [::]:80;                     # IPv6
    server_name example.com www.example.com;  # Domain names
    root /var/www/html;                 # Document root
    index index.html index.php;        # Default files
}
```

### Location Blocks (URL Routing)
```nginx
# Exact match (highest priority)
location = /favicon.ico {
    log_not_found off;
    access_log off;
}

# Prefix match
location /api/ {
    proxy_pass http://backend/;
}

# Regular expression (case-sensitive)
location ~ \.(jpg|jpeg|png|gif)$ {
    expires 1y;
}

# Regular expression (case-insensitive)
location ~* \.(jpg|jpeg|png|gif)$ {
    expires 1y;
}

# Prefix match (lower priority than regex)
location ^~ /static/ {
    alias /var/www/static/;
}

# Default fallback (lowest priority)
location / {
    try_files $uri $uri/ =404;
}
```

### Location Matching Priority:
1. Exact match (`=`)
2. Prefix match with `^~`
3. Regular expression (`~` and `~*`)
4. Prefix match
5. Default (`/`)

## Part 4: Reverse Proxy Fundamentals

### Basic Reverse Proxy
```nginx
server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Advanced Proxy Settings
```nginx
location /api/ {
    proxy_pass http://backend/;
    
    # Headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Timeouts
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
    
    # Buffering
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
    
    # Connection reuse
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

## Part 5: Load Balancing

### Upstream Blocks
```nginx
# Define backend servers
upstream backend {
    server 192.168.1.10:8000 weight=3;
    server 192.168.1.11:8000 weight=1;
    server 192.168.1.12:8000 backup;
}

server {
    location / {
        proxy_pass http://backend;
    }
}
```

### Load Balancing Methods
```nginx
# Round Robin (default)
upstream backend {
    server srv1.example.com;
    server srv2.example.com;
}

# Least Connections
upstream backend {
    least_conn;
    server srv1.example.com;
    server srv2.example.com;
}

# IP Hash (session persistence)
upstream backend {
    ip_hash;
    server srv1.example.com;
    server srv2.example.com;
}

# Weighted Round Robin
upstream backend {
    server srv1.example.com weight=3;
    server srv2.example.com weight=1;
}
```

### Health Checks
```nginx
upstream backend {
    server srv1.example.com max_fails=3 fail_timeout=30s;
    server srv2.example.com max_fails=3 fail_timeout=30s;
    server srv3.example.com backup;
}
```

## Part 6: SSL/TLS Configuration

### Basic SSL Setup
```nginx
server {
    listen 443 ssl http2;
    server_name example.com;
    
    ssl_certificate /etc/ssl/certs/example.com.pem;
    ssl_certificate_key /etc/ssl/private/example.com.key;
    
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

### Modern SSL Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name example.com;
    
    # Certificates
    ssl_certificate /etc/ssl/certs/example.com.pem;
    ssl_certificate_key /etc/ssl/private/example.com.key;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # SSL session cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
}
```

## Part 7: Security Features

### Rate Limiting
```nginx
# Define rate limiting zones
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
}

server {
    # Apply rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend;
    }
    
    location /login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://backend;
    }
}
```

### Access Control
```nginx
# IP-based access control
location /admin/ {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
    proxy_pass http://backend;
}

# Geo-based blocking
geo $blocked_country {
    default 0;
    include /etc/nginx/blocked_countries.conf;
}

server {
    if ($blocked_country) {
        return 403;
    }
}
```

### Security Headers
```nginx
# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'" always;

# Hide nginx version
server_tokens off;

# Prevent access to hidden files
location ~ /\. {
    deny all;
    access_log off;
    log_not_found off;
}
```

## Part 8: Performance Optimization

### Caching
```nginx
# Proxy caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g 
                 inactive=60m use_temp_path=off;

server {
    location / {
        proxy_cache my_cache;
        proxy_cache_valid 200 302 10m;
        proxy_cache_valid 404 1m;
        proxy_cache_use_stale error timeout invalid_header updating;
        
        proxy_pass http://backend;
    }
}

# Static file caching
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### Compression
```nginx
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
    application/xml+rss
    application/json
    image/svg+xml;
```

### Connection Optimization
```nginx
# HTTP/2 support
listen 443 ssl http2;

# Keepalive connections
keepalive_timeout 65;
keepalive_requests 100;

# Client optimizations
client_max_body_size 100M;
client_body_timeout 60s;
client_header_timeout 60s;

# Sendfile and TCP optimizations
sendfile on;
tcp_nopush on;
tcp_nodelay on;
```

## Part 9: Logging and Monitoring

### Custom Log Formats
```nginx
# Custom log format
log_format detailed '$remote_addr - $remote_user [$time_local] '
                   '"$request" $status $body_bytes_sent '
                   '"$http_referer" "$http_user_agent" '
                   'rt=$request_time uct="$upstream_connect_time" '
                   'uht="$upstream_header_time" urt="$upstream_response_time"';

# Apply to server
server {
    access_log /var/log/nginx/access.log detailed;
    error_log /var/log/nginx/error.log warn;
}
```

### Conditional Logging
```nginx
# Don't log health checks
location /health {
    access_log off;
    proxy_pass http://backend;
}

# Log only errors for static files
location ~* \.(jpg|jpeg|png|gif|css|js)$ {
    log_not_found off;
    expires 1y;
}
```

### Status and Metrics
```nginx
# Nginx status module
location /nginx_status {
    stub_status on;
    allow 127.0.0.1;
    deny all;
}
```

## Part 10: Advanced Features

### Dynamic Configuration
```nginx
# Include files for modularity
include /etc/nginx/conf.d/*.conf;
include /etc/nginx/sites-enabled/*;

# Variables
set $maintenance 0;
if (-f /var/www/maintenance.html) {
    set $maintenance 1;
}

if ($maintenance) {
    return 503;
}
```

### Error Pages
```nginx
# Custom error pages
error_page 404 /404.html;
error_page 500 502 503 504 /50x.html;

location = /404.html {
    root /var/www/error;
    internal;
}

location = /50x.html {
    root /var/www/error;
    internal;
}
```

### Websocket Proxying
```nginx
location /ws/ {
    proxy_pass http://websocket_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

## Part 11: Testing and Debugging

### Configuration Testing
```bash
# Test configuration syntax
nginx -t

# Test and print configuration
nginx -T

# Reload configuration
nginx -s reload

# Check which config file is being used
nginx -V 2>&1 | grep -o '\-\-conf-path=\S*'
```

### Debugging Tools
```bash
# Check listening ports
netstat -tulpn | grep nginx

# Monitor real-time logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Check worker processes
ps aux | grep nginx

# Test specific location blocks
curl -H "Host: example.com" http://localhost/api/test
```

### Common Issues and Solutions
```nginx
# Issue: 502 Bad Gateway
# Solution: Check upstream servers
upstream backend {
    server 127.0.0.1:8000;  # Make sure this is reachable
}

# Issue: Large file uploads fail
# Solution: Increase limits
client_max_body_size 100M;
proxy_read_timeout 300s;

# Issue: Slow responses
# Solution: Optimize buffering
proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;
```

This comprehensive guide covers everything you need to know about Nginx as a senior developer!