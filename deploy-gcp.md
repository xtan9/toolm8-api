# Deploy to Google Cloud with Docker

## Step 1: Create Google Cloud VM

### Create VM Instance:
```bash
# Using gcloud CLI (recommended)
gcloud compute instances create toolm8-api-vm \
    --machine-type=f1-micro \
    --zone=us-central1-a \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=30GB \
    --boot-disk-type=pd-standard \
    --tags=http-server,https-server

# Create firewall rules
gcloud compute firewall-rules create allow-toolm8-api \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow access to ToolM8 API"
```

### Or use Web Console:
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Compute Engine → VM Instances → Create Instance
3. Settings:
   - Name: `toolm8-api-vm`
   - Machine type: `f1-micro` (always free)
   - Region: `us-central1` (or us-west1/us-east1)
   - Boot disk: Ubuntu 20.04 LTS, 30GB
   - Firewall: Allow HTTP and HTTPS traffic

## Step 2: Connect to VM

```bash
# SSH via web console or:
gcloud compute ssh toolm8-api-vm --zone=us-central1-a
```

## Step 3: Setup VM Environment

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt install -y git

# Logout and login again for docker group to take effect
exit
# SSH back in
```

## Step 4: Deploy Your Application

```bash
# Clone your repository
git clone https://github.com/yourusername/toolm8_api.git
cd toolm8_api

# Create environment file
cat > .env << EOF
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_JWT_SECRET=your_jwt_secret_here
EOF

# Build and start with Docker Compose
docker-compose up -d

# Check if it's running
docker-compose ps
docker-compose logs api

# Test the API
curl http://localhost:8000/health
```

## Step 5: Access Your API

```bash
# Get external IP
gcloud compute instances describe toolm8-api-vm --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# Your API will be available at:
# http://EXTERNAL_IP:8000
```

## Step 6: Production Setup (Optional)

```bash
# Add nginx reverse proxy
docker-compose --profile production up -d

# Your API now available at:
# http://EXTERNAL_IP (port 80)
```

## Docker Commands You'll Learn:

```bash
# View running containers
docker ps

# View logs
docker logs toolm8-api
docker-compose logs -f api

# Restart application
docker-compose restart api

# Update application
git pull
docker-compose build
docker-compose up -d

# Clean up
docker system prune -f

# Enter container for debugging
docker exec -it toolm8-api bash
```

## Monitoring & Maintenance:

```bash
# Check disk usage (stay under 30GB)
df -h

# Check memory usage
free -h

# Monitor docker containers
docker stats

# View application logs
docker-compose logs -f --tail=100
```

## Cost Monitoring:
- f1-micro is free forever in us-central1, us-west1, us-east1
- 30GB disk is within free tier
- 1GB egress per month (you'll use <1MB)
- Total cost: $0.00/month

## Backup Strategy:
```bash
# Create VM snapshot
gcloud compute disks snapshot toolm8-api-vm --zone=us-central1-a --snapshot-names=toolm8-backup-$(date +%Y%m%d)
```

## Security Best Practices:
```bash
# Update regularly
sudo apt update && sudo apt upgrade -y

# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 8000
sudo ufw allow 80
sudo ufw --force enable
```