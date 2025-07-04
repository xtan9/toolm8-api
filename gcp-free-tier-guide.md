# Google Cloud Free Tier Guide 2024

## Current Free Tier Offerings

### Always Free Compute (2024)
Google Cloud's Always Free tier includes:

#### **Compute Engine:**
- **1 e2-micro instance** per month in eligible regions
- **0.25 vCPU, 1GB RAM**
- **30GB standard persistent disk**
- **1GB network egress per month** (excluding egress to China and Australia)

#### **Eligible Regions (Always Free):**
- `us-west1` (Oregon)
- `us-central1` (Iowa) 
- `us-east1` (South Carolina)

#### **Machine Type Comparison:**

| Type | vCPU | Memory | Notes |
|------|------|--------|-------|
| `e2-micro` | 0.25-2 | 1GB | **Always Free** (burstable CPU) |
| `e2-small` | 0.5-2 | 2GB | Paid (~$13/month) |
| `e2-medium` | 1-2 | 4GB | Paid (~$27/month) |

### **e2-micro Details:**
- **Burstable performance**: Can burst up to 2 vCPUs when needed
- **Shared-core**: Shares physical CPU with other VMs
- **Perfect for**: Low-traffic web apps, development, small APIs
- **Limitations**: CPU throttling under sustained load

## Updated VM Creation Commands

### Using gcloud CLI:
```bash
# Create e2-micro instance (always free)
gcloud compute instances create toolm8-api-vm \
    --machine-type=e2-micro \
    --zone=us-central1-a \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=30GB \
    --boot-disk-type=pd-standard \
    --tags=http-server,https-server \
    --metadata=startup-script='#!/bin/bash
        apt-get update
        apt-get install -y docker.io docker-compose
        usermod -aG docker $USER'

# Create firewall rule for your API
gcloud compute firewall-rules create allow-toolm8-api \
    --allow tcp:8000,tcp:80,tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow access to ToolM8 API"
```

### Using Web Console:
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. **Compute Engine → VM Instances → Create Instance**
3. **Configuration:**
   ```
   Name: toolm8-api-vm
   Region: us-central1 (Iowa)
   Zone: us-central1-a
   
   Machine Configuration:
   - Series: E2
   - Machine type: e2-micro (0.25-2 vCPU, 1 GB memory)
   
   Boot disk:
   - Operating system: Ubuntu
   - Version: Ubuntu 20.04 LTS
   - Boot disk type: Standard persistent disk
   - Size: 30 GB
   
   Firewall:
   ✅ Allow HTTP traffic
   ✅ Allow HTTPS traffic
   ```

## Performance Expectations for Your CSV Tool

### **e2-micro Capabilities:**
```bash
# What it can handle:
✅ FastAPI application (lightweight)
✅ CSV files up to 50-100MB
✅ Docker containers (2-3 containers max)
✅ Nginx reverse proxy
✅ Light database operations (via Supabase API)
✅ Occasional admin tasks

# Limitations:
⚠️  Sustained CPU-intensive tasks
⚠️  Memory-intensive operations >800MB
⚠️  High concurrent users (>10 simultaneous)
⚠️  Large file processing (>100MB CSVs)
```

### **Optimization for e2-micro:**
```dockerfile
# Dockerfile optimizations for limited resources
FROM python:3.10-slim

# Use multi-stage build to reduce image size
FROM python:3.10-slim as builder
COPY requirements-prod.txt .
RUN pip install --user -r requirements-prod.txt

FROM python:3.10-slim
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/

# Set memory limits
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Use lightweight command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

## Alternative Free Options if e2-micro Isn't Enough

### **Oracle Cloud (More Generous Free Tier):**
```bash
# Oracle offers:
- 2x AMD-based VMs (1GB RAM each)
- 4x Arm-based VMs (24GB RAM total)
- Always free forever
```

### **AWS Free Tier:**
```bash
# AWS offers:
- t2.micro (1 vCPU, 1GB RAM)
- 12 months free (not forever)
- 750 hours/month
```

### **Azure Free Tier:**
```bash
# Azure offers:
- B1S VM (1 vCPU, 1GB RAM)
- 12 months free
- $200 credit for first 30 days
```

## Monitoring Resource Usage

### **Check VM Performance:**
```bash
# SSH into your VM and monitor resources
ssh your-vm

# Check CPU usage
htop
top

# Check memory usage
free -h

# Check disk usage
df -h

# Monitor Docker containers
docker stats

# Check if CPU is being throttled
dmesg | grep -i "cpu"
```

### **Optimize for Low Resources:**
```yaml
# docker-compose.yml with resource limits
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'
        reservations:
          memory: 256M
          cpus: '0.1'
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.1'
    depends_on:
      - api
    restart: unless-stopped
```

## Free Tier Monitoring Script

```bash
#!/bin/bash
# monitor-free-tier.sh

echo "=== Google Cloud Free Tier Usage Monitor ==="

# Check if we're on e2-micro
MACHINE_TYPE=$(curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/machine-type | \
  awk -F/ '{print $NF}')

echo "Machine Type: $MACHINE_TYPE"

if [ "$MACHINE_TYPE" != "e2-micro" ]; then
    echo "⚠️  WARNING: Not using e2-micro! This will incur charges."
fi

# Check disk usage (should stay under 30GB)
echo ""
echo "=== Disk Usage ==="
df -h / | tail -1 | awk '{print "Used: " $3 " (" $5 ") of " $2}'

DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️  WARNING: Disk usage high ($DISK_USAGE%)"
fi

# Check memory usage
echo ""
echo "=== Memory Usage ==="
free -h | grep Mem | awk '{print "Used: " $3 " of " $2 " (" int($3/$2*100) "%)"}'

# Check CPU load
echo ""
echo "=== CPU Load ==="
uptime | awk -F'load average:' '{print "Load Average:" $2}'

# Check network usage (rough estimate)
echo ""
echo "=== Network Usage (since boot) ==="
cat /proc/net/dev | grep eth0 | awk '{print "TX: " int($10/1024/1024) "MB, RX: " int($2/1024/1024) "MB"}'

echo ""
echo "✅ Monitoring complete. Stay within free tier limits!"
```

## Updated Deployment Strategy

Given the e2-micro limitations, here's the optimal deployment approach:

### **Option 1: Minimal Docker Setup (Recommended)**
```yaml
# Lightweight docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 800M
          cpus: '0.25'
```

### **Option 2: Native Python (Maximum Performance)**
```bash
# Skip Docker for maximum performance on e2-micro
git clone your-repo
cd toolm8_api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt

# Run directly
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The e2-micro is perfect for your CSV admin tool since it's low-traffic and the burstable CPU handles occasional uploads well!