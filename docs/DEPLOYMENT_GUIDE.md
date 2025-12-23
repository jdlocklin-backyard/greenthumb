# GreenThumb Deployment Guide

Complete step-by-step guide for deploying GreenThumb on a Proxmox Ubuntu container.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Proxmox Container Setup](#proxmox-container-setup)
4. [Installing Dependencies](#installing-dependencies)
5. [DNS and Networking](#dns-and-networking)
6. [Deploying GreenThumb](#deploying-greenthumb)
7. [Verification and Testing](#verification-and-testing)
8. [Troubleshooting](#troubleshooting)
9. [Production Hardening](#production-hardening)

---

## Overview

GreenThumb is a self-hosted gardening platform that runs on Docker. This guide will walk you through deploying it on a Proxmox LXC container running Ubuntu.

**What You'll Deploy:**
- Frontend (Next.js) at `http://green.lab`
- Backend API (FastAPI) at `http://api.green.lab`
- PostgreSQL database with PostGIS
- Redis cache
- Agent worker for automated weather updates
- Traefik reverse proxy

**Total Time:** 30-45 minutes for first-time setup

**System Requirements:**
- 2 CPU cores
- 4GB RAM minimum (8GB recommended)
- 20GB disk space
- Internet connection for Docker images

---

## Prerequisites

Before you begin, ensure you have:

- [ ] **Proxmox VE** installed and accessible
- [ ] Basic familiarity with Linux command line
- [ ] SSH client (PuTTY, Terminal, or similar)
- [ ] Text editor knowledge (nano, vim, or similar)
- [ ] Network access to Proxmox host

---

## Proxmox Container Setup

### Step 1: Create Ubuntu LXC Container

**ACTION: In Proxmox Web UI**

1. Click **Create CT** (top right)
2. Fill in the General tab:
   - **Node**: Select your Proxmox node
   - **CT ID**: `100` (or next available)
   - **Hostname**: `greenthumb`
   - **Password**: Set a strong root password
   - [ ] Unprivileged container: **UNCHECKED** (Docker needs privileged)

3. Template tab:
   - **Storage**: local
   - **Template**: `ubuntu-22.04-standard` (download if needed)

4. Disks tab:
   - **Disk size**: `20 GB`
   - **Storage**: local-lvm or other storage

5. CPU tab:
   - **Cores**: `2`

6. Memory tab:
   - **Memory (MiB)**: `4096`
   - **Swap (MiB)**: `2048`

7. Network tab:
   - **Bridge**: `vmbr0`
   - **IPv4**: `DHCP` or static (note the IP address)
   - **IPv6**: DHCP (or leave blank)

8. DNS tab:
   - Use host settings (default)

9. Click **Finish**

**CHECKPOINT:** Container created successfully

---

### Step 2: Configure Container for Docker

**ACTION: In Proxmox Shell (Node)**

Docker requires specific container features. Edit the container config:

```bash
nano /etc/pve/lxc/100.conf
```

Add these lines at the end:

```
# Docker support
lxc.apparmor.profile: unconfined
lxc.cgroup2.devices.allow: a
lxc.cap.drop:
lxc.mount.auto: proc:rw sys:rw cgroup:rw
```

**Save and exit** (Ctrl+O, Enter, Ctrl+X in nano)

**CHECKPOINT:** Container configured for Docker

---

### Step 3: Start and Access Container

**ACTION: In Proxmox Web UI**

1. Select the container (`greenthumb`)
2. Click **Start**
3. Wait for it to boot (10-20 seconds)
4. Click **Console** or SSH to the container

**Via SSH:**
```bash
ssh root@<container-ip>
```

**CHECKPOINT:** You're now inside the Ubuntu container

---

## Installing Dependencies

### Step 4: Update System

**ACTION: In Container Shell**

```bash
apt update && apt upgrade -y
```

This updates package lists and installs security patches.

**CHECKPOINT:** System updated

---

### Step 5: Install Docker

**ACTION: In Container Shell**

Install Docker using the official convenience script:

> **Pro Tip:** If you're copying from this documentation, ensure no leading spaces are accidentally included. The backslash (`\`) at the end of a line means the command continues on the next line - copy the entire multi-line command as one block.

```bash
# Install prerequisites
apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**Verify Docker installation:**

```bash
docker --version
docker compose version
```

Expected output:
```
Docker version 24.x.x
Docker Compose version v2.x.x
```

**CHECKPOINT:** Docker installed successfully

---

### Step 6: Install Additional Tools

**ACTION: In Container Shell**

Install helpful utilities:

```bash
apt install -y \
  git \
  make \
  nano \
  curl \
  htop \
  net-tools
```

**CHECKPOINT:** Tools installed

---

## DNS and Networking

### Step 7: Configure Container Network

**ACTION: Find Container IP Address**

In the container shell:

```bash
ip addr show eth0 | grep inet
```

Note the IP address (e.g., `192.168.1.150`)

**CHECKPOINT:** Container IP address identified: `_____________`

---

### Step 8: Configure DNS on Your Computer

You need to tell your computer where `green.lab` points.

**IMPORTANT:** Replace `192.168.1.150` with your actual container IP

#### Option A: Edit Hosts File (Recommended for Testing)

**ACTION: On Your Local Computer**

**Linux/Mac:**
```bash
sudo nano /etc/hosts
```

**Windows:**
```
# Run Notepad as Administrator
C:\Windows\System32\drivers\etc\hosts
```

Add these lines:

```
192.168.1.150  green.lab
192.168.1.150  api.green.lab
192.168.1.150  traefik.green.lab
```

**Save the file**

**CHECKPOINT:** DNS configured via hosts file

---

#### Option B: Configure Local DNS Server (Better for Network-Wide Access)

If you run Pi-hole, AdGuard Home, or pfSense:

**ACTION: In Your DNS Server**

Add DNS records:
```
green.lab          → 192.168.1.150
api.green.lab      → 192.168.1.150
traefik.green.lab  → 192.168.1.150
```

**CHECKPOINT:** DNS configured via DNS server

---

### Step 9: Test DNS Resolution

**ACTION: On Your Local Computer**

```bash
ping green.lab
```

Expected output:
```
PING green.lab (192.168.1.150): 56 data bytes
64 bytes from 192.168.1.150: icmp_seq=0 ttl=64 time=0.5 ms
```

**CHECKPOINT:** DNS resolution working

---

## Deploying GreenThumb

### Step 10: Clone the Repository

**ACTION: In Container Shell**

```bash
# Create app directory
mkdir -p /opt/greenthumb
cd /opt/greenthumb

# Clone repository (replace with your repo URL)
git clone <your-repo-url> .
```

**If you don't have a Git repo yet:**
```bash
# Download and extract manually
# Or copy files via SCP/SFTP
```

**CHECKPOINT:** Code downloaded to `/opt/greenthumb`

---

### Step 11: Configure Environment Variables

**ACTION: In Container Shell**

```bash
cd /opt/greenthumb

# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

**IMPORTANT CHANGES REQUIRED:**

```bash
# Database - CHANGE THESE PASSWORDS
POSTGRES_PASSWORD=your_secure_db_password_here

# Redis - CHANGE THIS PASSWORD
REDIS_PASSWORD=your_secure_redis_password_here

# Backend - GENERATE A SECRET KEY
# Run this command to generate: openssl rand -hex 32
SECRET_KEY=paste_generated_key_here

# Frontend - Use your domain
NEXT_PUBLIC_API_URL=http://api.green.lab

# Traefik - Your domains
TRAEFIK_DOMAIN=green.lab
TRAEFIK_API_DOMAIN=api.green.lab
TRAEFIK_DASHBOARD_DOMAIN=traefik.green.lab
```

**Generate SECRET_KEY:**
```bash
openssl rand -hex 32
```
Copy the output and paste it into `.env` for `SECRET_KEY`

**Save the file** (Ctrl+O, Enter, Ctrl+X)

**CHECKPOINT:** Environment variables configured

---

### Step 12: Create Required Directories

**ACTION: In Container Shell**

```bash
cd /opt/greenthumb

# Run setup command
make setup
```

This creates:
- `data/db/` - PostgreSQL data
- `data/redis/` - Redis data
- `logs/` - Application logs
- `acme.json` - SSL certificates (for HTTPS later)

**CHECKPOINT:** Directories created

---

### Step 13: Start the Platform

**ACTION: In Container Shell**

```bash
cd /opt/greenthumb

# Pull Docker images and start services
make up
```

**What's happening:**
1. Downloading Docker images (2-5 minutes first time)
2. Starting PostgreSQL database
3. Starting Redis cache
4. Building and starting Backend API
5. Building and starting Agent worker
6. Building and starting Frontend
7. Starting Traefik reverse proxy

**Wait for completion.** You'll see output like:

```
✓ Platform is running!
  Frontend: http://green.lab
  API: http://api.green.lab
  API Docs: http://api.green.lab/docs
  Traefik Dashboard: http://traefik.green.lab
```

**CHECKPOINT:** All services started

---

## Verification and Testing

### Step 14: Check Service Health

**ACTION: In Container Shell**

```bash
# Check all containers are running
docker ps
```

Expected output (6 containers):
```
CONTAINER ID   IMAGE                    STATUS         PORTS
...            greenthumb-frontend      Up 2 minutes
...            greenthumb-backend       Up 2 minutes
...            greenthumb-agent         Up 2 minutes
...            greenthumb-traefik       Up 2 minutes   0.0.0.0:80->80/tcp
...            greenthumb-postgres      Up 2 minutes
...            greenthumb-redis         Up 2 minutes
```

**Check logs for errors:**
```bash
make logs
```

Press `Ctrl+C` to exit logs.

**CHECKPOINT:** All containers running

---

### Step 15: Test Web Access

**ACTION: On Your Local Computer's Browser**

Visit each URL and verify:

1. **Frontend** - http://green.lab
   - Should show GreenThumb dashboard
   - "Sign In" button visible

2. **API Documentation** - http://api.green.lab/docs
   - Should show Swagger UI
   - List of API endpoints visible

3. **Traefik Dashboard** - http://traefik.green.lab
   - Prompt for credentials
   - Username: `admin`
   - Password: `admin` (CHANGE THIS LATER)

**CHECKPOINT:** All web interfaces accessible

---

### Step 16: Create Your First Account

**ACTION: In Browser at http://green.lab**

1. Click **Sign In**
2. Click **Register** (or sign-up link)
3. Enter:
   - Email: `your@email.com`
   - Password: (strong password)
   - Full Name: Your name
4. Click **Register**
5. You'll be redirected to login
6. Log in with your credentials

**CHECKPOINT:** User account created and logged in

---

### Step 17: Create Your First Garden

**ACTION: In Browser (logged in)**

1. Click **Create Your First Garden** or **+ New Garden**
2. Fill in:
   - **Name**: `My Backyard Garden`
   - **Description**: `Vegetables and herbs`
   - **Latitude**: Your GPS coordinate (e.g., `37.7749`)
   - **Longitude**: Your GPS coordinate (e.g., `-122.4194`)

   **Tip:** Get coordinates from Google Maps - right-click on your location

3. Click **Create Garden**

**CHECKPOINT:** Garden created successfully

---

### Step 18: Verify Agent is Running

The agent automatically collects weather data every 15 minutes.

**ACTION: In Container Shell**

```bash
# Check agent logs
make logs-agent
```

Look for entries like:
```json
{"level":"INFO","service":"agent","message":"Starting weather check job"}
{"level":"INFO","service":"agent","garden":"My Backyard Garden","message":"Weather data collected"}
```

**Wait up to 15 minutes** for first weather check, or trigger manually:

```bash
docker restart greenthumb-agent
```

**CHECKPOINT:** Agent collecting weather data

---

## Troubleshooting

### Container Won't Start

**Problem:** Container fails to start or gets stuck

**ACTION:**
```bash
# In Proxmox shell
pct stop 100
pct start 100

# Check container logs
pct logs 100
```

---

### Docker Services Won't Start

**Problem:** `make up` fails or containers crash

**ACTION: In Container Shell**

```bash
# Check what's failing
docker ps -a

# View logs of failed service
docker logs greenthumb-backend
docker logs greenthumb-postgres

# Check port conflicts
netstat -tulpn | grep -E ':(80|443|5432|6379)'

# Restart from scratch
make down
make clean
make setup
make up
```

---

### Can't Access Web Interface

**Problem:** Browser shows "Can't connect" for green.lab

**Checklist:**

1. **DNS Resolution**
   ```bash
   # On your computer
   ping green.lab
   ```
   If fails: Recheck Step 8 (DNS configuration)

2. **Traefik Running**
   ```bash
   # In container
   docker ps | grep traefik
   ```
   If not running: Check logs with `docker logs greenthumb-traefik`

3. **Firewall on Container**
   ```bash
   # In container - check if ufw is blocking
   ufw status

   # If active, allow ports
   ufw allow 80/tcp
   ufw allow 443/tcp
   ```

4. **Proxmox Firewall**
   - Check Proxmox datacenter firewall isn't blocking port 80

---

### Database Connection Errors

**Problem:** Backend logs show "connection refused" or "authentication failed"

**ACTION: In Container Shell**

```bash
# Verify Postgres is running
docker exec greenthumb-postgres pg_isready -U greenthumb

# Test database connection
docker exec -it greenthumb-postgres psql -U greenthumb -d greenthumb

# If connection works, check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Restart backend
docker restart greenthumb-backend
```

---

### Agent Not Collecting Weather

**Problem:** No weather data appears after 15+ minutes

**ACTION: In Container Shell**

```bash
# Check agent logs for errors
docker logs greenthumb-agent --tail 100

# Verify Redis connection
docker exec -it greenthumb-redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d '=' -f2) ping
# Should respond: PONG

# Manually restart agent
docker restart greenthumb-agent

# Check gardens exist in database
docker exec -it greenthumb-postgres psql -U greenthumb -d greenthumb -c "SELECT id, name FROM gardens;"
```

---

### Forgot Traefik Dashboard Password

**Problem:** Can't log into http://traefik.green.lab

**ACTION: In Container Shell**

The default is `admin/admin`. To change it:

```bash
# Generate new password hash
htpasswd -nb admin your-new-password

# Copy the output (looks like: admin:$apr1$...)

# Edit docker-compose.yml
nano docker-compose.yml

# Find this line under traefik service labels:
# traefik.http.middlewares.auth.basicauth.users=admin:$$apr1$$...

# Replace with your new hash (escape $ with $$)

# Restart Traefik
docker restart greenthumb-traefik
```

---

### Out of Disk Space

**Problem:** Container shows "no space left on device"

**ACTION:**

```bash
# Check disk usage
df -h

# Clean Docker system
docker system prune -a --volumes

# If still full, increase container disk in Proxmox:
# Datacenter → Container → Resources → Hard Disk → Resize
```

---

## Production Hardening

Once your system is working, follow these steps to secure it.

### Step 19: Change Default Passwords

**WARNING:** Do this BEFORE exposing to the internet

**ACTION: In Container Shell**

1. **Traefik Dashboard** (see "Forgot Traefik Dashboard Password" above)

2. **Database and Redis** (already done in Step 11)

3. **Verify SECRET_KEY** is random:
   ```bash
   grep SECRET_KEY .env
   ```
   Should be 64-character hex string, not the default

**CHECKPOINT:** All default passwords changed

---

### Step 20: Enable HTTPS (Optional but Recommended)

**Prerequisites:**
- You own a domain name
- Domain DNS points to your public IP
- Port 80 and 443 forwarded to container

**ACTION: In Container Shell**

```bash
nano .env
```

Change:
```bash
# Enable HTTPS
TRAEFIK_ENABLE_HTTPS=true

# Your real domain
TRAEFIK_DOMAIN=green.yourdomain.com
TRAEFIK_API_DOMAIN=api.green.yourdomain.com
TRAEFIK_DASHBOARD_DOMAIN=traefik.green.yourdomain.com

# Your email for Let's Encrypt
ACME_EMAIL=you@yourdomain.com

# Update frontend
NEXT_PUBLIC_API_URL=https://api.green.yourdomain.com
```

**Save and restart:**
```bash
make restart
```

Traefik will automatically obtain SSL certificates from Let's Encrypt.

**CHECKPOINT:** HTTPS enabled with valid certificates

---

### Step 21: Configure Firewall

**ACTION: In Container Shell**

```bash
# Install UFW if not present
apt install -y ufw

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (IMPORTANT - don't lock yourself out)
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable

# Verify
ufw status
```

**CHECKPOINT:** Firewall configured

---

### Step 22: Set Up Automatic Backups

**ACTION: In Container Shell**

Create backup script:

```bash
nano /root/backup-greenthumb.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database
docker exec greenthumb-postgres pg_dump -U greenthumb greenthumb | \
  gzip > "$BACKUP_DIR/greenthumb_db_$DATE.sql.gz"

# Backup .env file
cp /opt/greenthumb/.env "$BACKUP_DIR/greenthumb_env_$DATE.env"

# Keep only last 7 days
find "$BACKUP_DIR" -name "greenthumb_*" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable:
```bash
chmod +x /root/backup-greenthumb.sh
```

Schedule with cron:
```bash
crontab -e
```

Add line (daily at 2 AM):
```
0 2 * * * /root/backup-greenthumb.sh >> /var/log/greenthumb-backup.log 2>&1
```

**Test backup:**
```bash
/root/backup-greenthumb.sh
ls -lh /root/backups/
```

**CHECKPOINT:** Automated backups configured

---

### Step 23: Enable Automatic Updates (Optional)

**ACTION: In Container Shell**

```bash
# Install unattended-upgrades
apt install -y unattended-upgrades

# Enable automatic security updates
dpkg-reconfigure -plow unattended-upgrades
# Select "Yes"
```

**Note:** This only updates Ubuntu packages, not Docker containers.

To update Docker containers:
```bash
cd /opt/greenthumb
docker compose pull
make restart
```

**CHECKPOINT:** Security updates automated

---

## Maintenance Commands

### Daily Operations

```bash
# View live logs
make logs

# View specific service
make logs-backend
make logs-agent
make logs-frontend

# Restart all services
make restart

# Check resource usage
docker stats
```

---

### Updates

```bash
# Pull latest code (if using Git)
cd /opt/greenthumb
git pull

# Rebuild containers
make rebuild

# Or update specific service
docker compose build backend
docker compose up -d backend
```

---

### Database Maintenance

```bash
# Backup database
docker exec greenthumb-postgres pg_dump -U greenthumb greenthumb > backup.sql

# Restore database
cat backup.sql | docker exec -i greenthumb-postgres psql -U greenthumb greenthumb

# Access database shell
make db-shell

# Vacuum database (reclaim space)
docker exec greenthumb-postgres psql -U greenthumb -d greenthumb -c "VACUUM ANALYZE;"
```

---

### Complete Reset (Nuclear Option)

**WARNING:** This deletes ALL data

```bash
cd /opt/greenthumb
make clean
make setup
make up
```

---

## Next Steps

Congratulations! GreenThumb is now running. Here's what to do next:

1. **Explore the Interface**
   - Create gardens
   - Add plants
   - View weather data

2. **Customize**
   - Adjust agent interval (`.env` → `AGENT_CHECK_INTERVAL`)
   - Configure weather provider

3. **Monitor**
   - Check logs regularly: `make logs`
   - Watch Traefik dashboard: http://traefik.green.lab

4. **Share with Others**
   - Add more users via registration
   - Consider HTTPS for security

5. **Backup Strategy**
   - Test backup restore process
   - Consider off-site backup storage

---

## Support

**Documentation:**
- [Architecture Overview](ARCHITECTURE.md)
- [Quick Reference](QUICK_REFERENCE.md)
- [GitHub Setup](GITHUB_SETUP.md)

**Troubleshooting:**
- Check logs: `make logs`
- Restart services: `make restart`
- Review this guide's troubleshooting section

**Community:**
- Open issues on GitHub
- Check existing issues for solutions

---

**Built for home lab enthusiasts by home lab enthusiasts**
