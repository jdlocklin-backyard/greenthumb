# GreenThumb: Proxmox LXC Deployment Guide

Deploy GreenThumb on Proxmox VE using an LXC container. This guide gets you running in under 15 minutes.

## Prerequisites

- Proxmox VE 7.x or 8.x
- At least 2GB RAM available for the container
- 10GB disk space
- Network access (DHCP or static IP)

## Step 1: Create the LXC Container

### Via Proxmox Web UI

1. **Download Ubuntu Template**
   - Datacenter > your-node > local (storage) > CT Templates
   - Click "Templates" button
   - Download: `ubuntu-22.04-standard`

2. **Create Container**
   - Click "Create CT" in top right

   | Setting | Value | Notes |
   |---------|-------|-------|
   | Node | Your node | - |
   | CT ID | 200 | Or any unused ID |
   | Hostname | greenthumb | - |
   | Password | (set a password) | For root user |
   | Template | ubuntu-22.04-standard | From step 1 |
   | Root Disk | 10GB minimum | 20GB recommended |
   | CPU | 2 cores | 1 works but slower builds |
   | Memory | 2048 MB | 4096 MB recommended |
   | Swap | 512 MB | - |
   | Network | DHCP or Static | Note the IP for later |

3. **Enable Features for Docker**
   - Select the container > Options > Features
   - Enable: `keyctl`, `nesting`

   Or via CLI:
   ```bash
   pct set 200 --features keyctl=1,nesting=1
   ```

4. **Start the Container**
   - Select container > Start

### Via Proxmox CLI (Alternative)

```bash
# Download template if not present
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst

# Create container
pct create 200 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname greenthumb \
  --memory 2048 \
  --swap 512 \
  --cores 2 \
  --rootfs local-lvm:10 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --features keyctl=1,nesting=1 \
  --start 1
```

## Step 2: Install Docker in the Container

Connect to the container:
```bash
# From Proxmox host
pct enter 200

# Or via SSH once you know the IP
ssh root@<container-ip>
```

Run the Docker installation script:
```bash
# Update system
apt update && apt upgrade -y

# Install Docker using official convenience script
curl -fsSL https://get.docker.com | sh

# Verify Docker works
docker run --rm hello-world

# Install Docker Compose plugin (already included in Docker 24+)
docker compose version
```

**Expected output:** Docker version 24.x+ and Compose version 2.x+

## Step 3: Deploy GreenThumb

```bash
# Create app directory
mkdir -p /opt/greenthumb && cd /opt/greenthumb

# Clone repository
apt install -y git
git clone https://github.com/your-org/greenthumb.git .

# Create environment file from template
cp .env.example .env

# (Optional) Edit .env to change passwords
# nano .env

# Build and start all containers
docker compose up -d --build
```

**First build takes 3-5 minutes** (downloading images + building).

### Verify Deployment

```bash
# Check all containers are running
docker compose ps

# Expected output:
# NAME                   STATUS
# greenthumb-postgres    Up (healthy)
# greenthumb-redis       Up (healthy)
# greenthumb-backend     Up (healthy)
# greenthumb-agent       Up
# greenthumb-frontend    Up
```

## Step 4: Access GreenThumb

Find your container's IP:
```bash
hostname -I
# Example output: 192.168.1.50
```

Open in your browser:

| URL | Purpose |
|-----|---------|
| `http://192.168.1.50:3000` | Main application |
| `http://192.168.1.50:3000/api/docs` | API documentation (Swagger) |
| `http://192.168.1.50:3000/api/health` | Health check endpoint |

**That's it!** No DNS configuration, no reverse proxy setup, no CORS debugging.

## Common Operations

### View Logs

```bash
cd /opt/greenthumb

# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

### Restart Services

```bash
# Restart everything
docker compose restart

# Restart specific service
docker compose restart backend
```

### Update GreenThumb

```bash
cd /opt/greenthumb

# Pull latest code
git pull

# Rebuild and restart
docker compose up -d --build
```

### Backup Database

```bash
# Create backup
docker exec greenthumb-postgres pg_dump -U greenthumb greenthumb > backup_$(date +%Y%m%d).sql

# Restore backup
cat backup_20240101.sql | docker exec -i greenthumb-postgres psql -U greenthumb greenthumb
```

## Troubleshooting

### Container Won't Start

**Symptom:** `docker compose up` fails with permission errors

**Fix:** Ensure LXC features are enabled:
```bash
# On Proxmox host (not inside container)
pct set 200 --features keyctl=1,nesting=1
pct reboot 200
```

### Port Already in Use

**Symptom:** `bind: address already in use`

**Fix:** Check what's using port 3000:
```bash
ss -tlnp | grep 3000
# Kill the process or change the port in docker-compose.yml
```

### Database Connection Failed

**Symptom:** Backend logs show "connection refused"

**Fix:** Wait for PostgreSQL to be healthy:
```bash
# Check PostgreSQL status
docker compose ps postgres

# If not healthy, check logs
docker compose logs postgres
```

### Out of Memory

**Symptom:** Containers randomly restart, OOM errors in `dmesg`

**Fix:** Increase container memory in Proxmox:
```bash
# On Proxmox host
pct set 200 --memory 4096
pct reboot 200
```

## Resource Usage

Expected steady-state resource usage:

| Container | Memory | CPU | Notes |
|-----------|--------|-----|-------|
| PostgreSQL | ~150MB | Low | Scales with data |
| Redis | ~20MB | Low | Minimal |
| Backend | ~200MB | Low | Python/FastAPI |
| Agent | ~100MB | Low | Scheduled tasks |
| Frontend | ~150MB | Low | Next.js SSR |
| **Total** | **~620MB** | - | Fits in 1GB+ container |

## Security Recommendations

For production use:

1. **Change default passwords** in `.env`:
   ```bash
   # Generate secure password
   openssl rand -base64 24
   ```

2. **Generate real SECRET_KEY**:
   ```bash
   openssl rand -hex 32
   ```

3. **Firewall** - Only expose port 3000:
   ```bash
   ufw allow 22/tcp    # SSH
   ufw allow 3000/tcp  # GreenThumb
   ufw enable
   ```

4. **Regular updates**:
   ```bash
   apt update && apt upgrade -y
   docker compose pull
   docker compose up -d
   ```

## Optional: Access from Internet

If you want external access (not recommended without proper security):

1. **Port forward** 3000 on your router to the container IP
2. **Use Cloudflare Tunnel** (free, more secure than port forwarding)
3. **Set up a proper reverse proxy** (Nginx, Caddy) with SSL

For a home lab internal-only deployment, none of this is needed.

---

## Architecture Reference

```
+------------------------------------------------------------------+
|  Proxmox LXC Container (Ubuntu 22.04)                            |
|                                                                  |
|  Port 3000 (exposed)                                             |
|       |                                                          |
|       v                                                          |
|  +------------------+                                            |
|  | Frontend         |  Next.js                                   |
|  | (greenthumb-     |  Handles all user requests                 |
|  |  frontend)       |  Proxies /api/* to backend                 |
|  +--------+---------+                                            |
|           |                                                      |
|           | Internal network (greenthumb-internal)               |
|           v                                                      |
|  +------------------+     +------------------+                   |
|  | Backend          |<--->| PostgreSQL       |                   |
|  | (greenthumb-     |     | + PostGIS        |                   |
|  |  backend)        |     +------------------+                   |
|  +--------+---------+                                            |
|           |               +------------------+                   |
|           +-------------->| Redis            |                   |
|           |               +------------------+                   |
|           v                                                      |
|  +------------------+                                            |
|  | Agent            |  Background worker                         |
|  | (greenthumb-     |  Weather updates, scheduled tasks          |
|  |  agent)          |                                            |
|  +------------------+                                            |
+------------------------------------------------------------------+
```

**Key Insight:** Only port 3000 is exposed. The frontend acts as the reverse proxy, eliminating the need for Traefik or Nginx.
