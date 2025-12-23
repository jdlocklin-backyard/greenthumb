# GreenThumb Quick Reference

**One-page cheat sheet for GreenThumb platform operations**

---

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://green.lab | User account |
| **API Docs** | http://api.green.lab/docs | JWT token required |
| **Traefik Dashboard** | http://traefik.green.lab | admin / admin |

---

## Essential Make Commands

| Command | Description |
|---------|-------------|
| `make setup` | Initial setup (copy .env, create dirs) |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make logs` | View all logs (Ctrl+C to exit) |
| `make logs-backend` | Backend API logs only |
| `make logs-agent` | Agent worker logs only |
| `make logs-frontend` | Frontend logs only |
| `make clean` | Stop and remove all containers + data |
| `make rebuild` | Rebuild all containers from scratch |

---

## Docker Commands

| Command | Description |
|---------|-------------|
| `docker ps` | List running containers |
| `docker ps -a` | List all containers (including stopped) |
| `docker logs greenthumb-backend` | View specific container logs |
| `docker restart greenthumb-backend` | Restart specific container |
| `docker exec -it greenthumb-backend bash` | Shell into container |
| `docker stats` | Real-time resource usage |
| `docker system prune -a` | Clean up unused images/containers |

---

## Shell Access

| Command | Description |
|---------|-------------|
| `make backend-shell` | Open shell in backend container |
| `make agent-shell` | Open shell in agent container |
| `make db-shell` | Open PostgreSQL shell |
| `docker exec -it greenthumb-redis redis-cli` | Open Redis CLI |

---

## Database Operations

| Command | Description |
|---------|-------------|
| `make db-shell` | Access PostgreSQL shell |
| `docker exec greenthumb-postgres pg_dump -U greenthumb greenthumb > backup.sql` | Backup database |
| `cat backup.sql | docker exec -i greenthumb-postgres psql -U greenthumb greenthumb` | Restore database |
| `docker exec greenthumb-postgres pg_isready -U greenthumb` | Check database health |

**Inside psql shell:**
```sql
\dt                           -- List tables
\d users                      -- Describe table
SELECT * FROM gardens;        -- Query data
SELECT COUNT(*) FROM plants;  -- Count records
\q                            -- Quit
```

---

## Environment Variables

**Location:** `.env` file in project root

| Variable | Default | Notes |
|----------|---------|-------|
| `POSTGRES_PASSWORD` | `changeme_secure_password` | CHANGE THIS |
| `REDIS_PASSWORD` | `changeme_redis_password` | CHANGE THIS |
| `SECRET_KEY` | `changeme_generate...` | Generate with `openssl rand -hex 32` |
| `NEXT_PUBLIC_API_URL` | `http://api.green.lab` | Frontend → Backend URL |
| `TRAEFIK_DOMAIN` | `green.lab` | Main frontend domain |
| `TRAEFIK_API_DOMAIN` | `api.green.lab` | Backend API domain |
| `AGENT_CHECK_INTERVAL` | `3600` | Weather check interval (seconds) |
| `TRAEFIK_ENABLE_HTTPS` | `false` | Enable Let's Encrypt SSL |

**After changing .env:**
```bash
make restart
```

---

## Port Mappings

| Service | Internal Port | External Access |
|---------|---------------|-----------------|
| Traefik | 80, 443 | http://green.lab |
| Backend | 8000 | Via Traefik (api.green.lab) |
| Frontend | 3000 | Via Traefik (green.lab) |
| PostgreSQL | 5432 | Internal only |
| Redis | 6379 | Internal only |

---

## Health Checks

| Check | Command |
|-------|---------|
| **All containers** | `docker ps` |
| **Backend health** | `curl http://api.green.lab/health` |
| **Database** | `docker exec greenthumb-postgres pg_isready -U greenthumb` |
| **Redis** | `docker exec greenthumb-redis redis-cli ping` |
| **Disk space** | `df -h` |
| **Memory usage** | `docker stats --no-stream` |

---

## Common Troubleshooting

### Services Won't Start

```bash
# Check what failed
docker ps -a

# View logs
make logs

# Rebuild from scratch
make clean
make setup
make up
```

### Can't Access Web Interface

```bash
# Test DNS
ping green.lab

# Check Traefik
docker logs greenthumb-traefik

# Verify ports
netstat -tulpn | grep :80
```

### Database Connection Errors

```bash
# Check database is running
docker ps | grep postgres

# Test connection
make db-shell

# View backend logs
make logs-backend
```

### Agent Not Collecting Weather

```bash
# Check agent logs
make logs-agent

# Verify Redis
docker exec greenthumb-redis redis-cli ping

# Restart agent
docker restart greenthumb-agent
```

### Out of Disk Space

```bash
# Check usage
df -h

# Clean Docker
docker system prune -a --volumes

# Remove old logs
rm -rf logs/*
make restart
```

---

## API Authentication

> **Copy/Paste Tip:** When copying multi-line commands, ensure no leading spaces are accidentally included. The backslash (`\`) at the end of a line continues the command.

### Register New User (curl)

```bash
curl -X POST http://api.green.lab/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure123",
    "full_name": "Test User"
  }'
```

### Login and Get Token (curl)

```bash
curl -X POST http://api.green.lab/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=secure123"
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Use Token for Requests

```bash
curl -X GET http://api.green.lab/api/v1/gardens \
  -H "Authorization: Bearer eyJ..."
```

---

## Backup and Restore

### Backup Everything

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"

mkdir -p "$BACKUP_DIR"

# Database
docker exec greenthumb-postgres pg_dump -U greenthumb greenthumb | \
  gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Config
cp /opt/greenthumb/.env "$BACKUP_DIR/env_$DATE.env"

# Data directories
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" /opt/greenthumb/data

echo "Backup completed: $DATE"
```

### Restore Database

```bash
# Stop services
make down

# Restore
gunzip < backup.sql.gz | \
  docker exec -i greenthumb-postgres psql -U greenthumb greenthumb

# Start services
make up
```

---

## Security Checklist

- [ ] Changed `POSTGRES_PASSWORD` from default
- [ ] Changed `REDIS_PASSWORD` from default
- [ ] Generated unique `SECRET_KEY` with `openssl rand -hex 32`
- [ ] Changed Traefik dashboard password (admin/admin)
- [ ] Enabled firewall: `ufw allow 80/tcp && ufw allow 443/tcp`
- [ ] Configured automatic backups
- [ ] Enabled HTTPS if public-facing
- [ ] Reviewed `.env` file for sensitive data

---

## Performance Monitoring

### Check Resource Usage

```bash
# Container stats
docker stats

# System resources
htop

# Disk I/O
iotop
```

### Log Analysis

```bash
# Count errors in backend
make logs-backend | grep ERROR | wc -l

# Find slow requests
make logs-backend | jq 'select(.duration > 1000)'

# Agent weather checks
make logs-agent | grep "weather check"
```

---

## Updating GreenThumb

### Pull Latest Changes

```bash
cd /opt/greenthumb

# Pull new code
git pull

# Rebuild containers
make rebuild

# Check logs
make logs
```

### Update Docker Images

```bash
cd /opt/greenthumb

# Pull latest images
docker compose pull

# Restart with new images
make restart
```

---

## File Locations

| Item | Path |
|------|------|
| Application code | `/opt/greenthumb/` |
| Environment config | `/opt/greenthumb/.env` |
| Database data | `/opt/greenthumb/data/db/` |
| Redis data | `/opt/greenthumb/data/redis/` |
| Application logs | `/opt/greenthumb/logs/` |
| Docker Compose | `/opt/greenthumb/docker-compose.yml` |
| Makefile | `/opt/greenthumb/Makefile` |

---

## Container Names

| Service | Container Name |
|---------|----------------|
| Frontend | `greenthumb-frontend` |
| Backend | `greenthumb-backend` |
| Agent | `greenthumb-agent` |
| Traefik | `greenthumb-traefik` |
| PostgreSQL | `greenthumb-postgres` |
| Redis | `greenthumb-redis` |

---

## Useful One-Liners

```bash
# Restart only backend
docker restart greenthumb-backend

# Follow backend logs
docker logs -f greenthumb-backend

# Check agent's last weather check
docker logs greenthumb-agent --tail 50 | grep "weather"

# Count gardens in database
docker exec greenthumb-postgres psql -U greenthumb -d greenthumb \
  -c "SELECT COUNT(*) FROM gardens;"

# Check database size
docker exec greenthumb-postgres psql -U greenthumb -d greenthumb \
  -c "SELECT pg_size_pretty(pg_database_size('greenthumb'));"

# Vacuum database (optimize)
docker exec greenthumb-postgres psql -U greenthumb -d greenthumb \
  -c "VACUUM ANALYZE;"

# Test Redis connection
docker exec greenthumb-redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d '=' -f2) ping

# Get Redis info
docker exec greenthumb-redis redis-cli info

# View Traefik routes
docker exec greenthumb-traefik traefik healthcheck

# Check open ports
netstat -tulpn | grep LISTEN
```

---

## Emergency Recovery

### Complete Reset (Nuclear Option)

**WARNING: This deletes ALL data**

```bash
cd /opt/greenthumb

# Stop and remove everything
make clean

# Fresh start
make setup
make up
```

### Recover from Backup

```bash
# Stop services
make down

# Restore database
gunzip < /root/backups/db_latest.sql.gz | \
  docker exec -i greenthumb-postgres psql -U greenthumb greenthumb

# Restore config
cp /root/backups/env_latest.env /opt/greenthumb/.env

# Start services
make up
```

---

## Getting Help

1. **Check logs first**: `make logs`
2. **Review deployment guide**: `docs/DEPLOYMENT_GUIDE.md`
3. **Check architecture docs**: `docs/ARCHITECTURE.md`
4. **Search GitHub issues**: Look for similar problems
5. **Open new issue**: Provide logs and error messages

---

**Print this page and keep it handy for quick reference**

**Last Updated:** 2024-01-09
