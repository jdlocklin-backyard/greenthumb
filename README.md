# GreenThumb

Production-ready, self-hosted gardening platform for Proxmox Home Lab.

Track your gardens, monitor plant growth, and get automated weather updates - all running on your own infrastructure.

---

## Features

- **Multi-Garden Management** - Track unlimited gardens and plants
- **Automated Weather Tracking** - GPS-based weather data collection every 15 minutes
- **RESTful API** - FastAPI backend with auto-generated OpenAPI documentation
- **Modern Web Interface** - Responsive Next.js frontend with TypeScript
- **Self-Hosted** - Complete control over your data
- **Docker-Based** - Easy deployment with Docker Compose
- **Production-Ready** - Structured logging, health checks, and fault isolation
- **No DNS Required** - Works with direct IP access out of the box

---

## Architecture

```
  Browser --> http://<your-ip>:3000
                    |
                    v
            +---------------+
            |   Frontend    |  Next.js (proxies /api/* internally)
            +-------+-------+
                    |
                    v
            +---------------+     +------------+
            |   Backend     |<--->| PostgreSQL |
            |   (FastAPI)   |     | + PostGIS  |
            +-------+-------+     +------------+
                    |
                    v
            +---------------+     +------------+
            |    Agent      |<--->|   Redis    |
            +---------------+     +------------+
```

- **Frontend**: Next.js 14+ with TypeScript and Tailwind CSS
- **Backend API**: Python FastAPI with async SQLAlchemy
- **Agent**: Autonomous worker with APScheduler for weather checks
- **Database**: PostgreSQL 16 with PostGIS for geospatial queries
- **Cache/Queue**: Redis for agent task locking

**No reverse proxy needed** - Next.js handles API routing internally.

---

## Quick Start

### Option 1: One-Line Install (Proxmox LXC)

Inside a fresh Ubuntu 22.04 LXC container:

```bash
curl -fsSL https://raw.githubusercontent.com/your-org/greenthumb/main/scripts/setup-lxc.sh | bash
```

### Option 2: Manual Setup

```bash
# Clone the repository
git clone https://github.com/your-org/greenthumb.git
cd greenthumb

# Create environment file
cp .env.example .env

# Start all services
docker compose up -d --build
```

**Access the platform at:** `http://<your-ip>:3000`

| URL | Purpose |
|-----|---------|
| `http://<your-ip>:3000` | Main application |
| `http://<your-ip>:3000/api/docs` | API documentation (Swagger UI) |
| `http://<your-ip>:3000/api/health` | Health check endpoint |

---

## Documentation

| Document | Description |
|----------|-------------|
| **[Proxmox LXC Deployment](docs/DEPLOY_PROXMOX_LXC.md)** | Step-by-step Proxmox container setup |
| **[Quick Reference](docs/QUICK_REFERENCE.md)** | One-page cheat sheet for commands |
| **[Architecture](docs/ARCHITECTURE.md)** | System design and technology choices |

---

## Prerequisites

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **2GB RAM minimum** (4GB recommended)
- **10GB disk space**

That's it. No DNS configuration, no reverse proxy setup, no hosts file editing.

---

## Environment Variables

Configuration via `.env` file (copied from `.env.example`).

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `greenthumb` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `greenthumb_dev` | Database password |
| `POSTGRES_DB` | `greenthumb` | Database name |
| `SECRET_KEY` | (generate one) | JWT signing key |
| `AGENT_LOG_LEVEL` | `INFO` | Agent logging verbosity |
| `WEATHER_API_PROVIDER` | `open-meteo` | Weather data source (free) |

**For production:** Generate a real secret key with `openssl rand -hex 32`

---

## Common Commands

```bash
# Start all services
docker compose up -d

# View logs (all services)
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f agent

# Restart services
docker compose restart

# Stop all services
docker compose down

# Rebuild after code changes
docker compose up -d --build

# Database shell
docker exec -it greenthumb-postgres psql -U greenthumb greenthumb

# Backup database
docker exec greenthumb-postgres pg_dump -U greenthumb greenthumb > backup.sql

# Restore database
cat backup.sql | docker exec -i greenthumb-postgres psql -U greenthumb greenthumb
```

---

## Project Structure

```
.
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/v1/         # API routes (gardens, plants, weather)
│   │   ├── core/           # Config, database, logging
│   │   ├── models/         # SQLAlchemy models
│   │   └── schemas.py      # Pydantic schemas
│   ├── main.py             # FastAPI entry point
│   └── Dockerfile
│
├── agent/                  # Background worker
│   ├── worker.py           # APScheduler jobs
│   └── Dockerfile
│
├── frontend/               # Next.js application
│   ├── app/                # App router pages
│   ├── next.config.js      # API rewrite configuration
│   └── Dockerfile
│
├── scripts/
│   └── setup-lxc.sh        # One-line installer
│
├── docs/
│   └── DEPLOY_PROXMOX_LXC.md
│
├── docker-compose.yml      # Service orchestration
└── .env.example            # Environment template
```

---

## First Steps After Installation

1. **Open the app**: Navigate to `http://<your-ip>:3000`

2. **Create an account**: Click "Sign In" then "Register"

3. **Create your first garden**:
   - Enter garden name and GPS coordinates
   - Weather data collection starts automatically

4. **Add plants**:
   - Open your garden
   - Add plants with variety and planting date

5. **Monitor weather**:
   - Weather updates every 15 minutes
   - View history in garden dashboard

---

## API Documentation

Interactive docs at `http://<your-ip>:3000/api/docs`

### Quick API Test

```bash
# Health check
curl http://localhost:3000/api/health

# Register user
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123","full_name":"Test User"}'

# Login
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=secure123"
```

---

## Troubleshooting

### Containers won't start

```bash
# Check container status
docker compose ps

# View detailed logs
docker compose logs

# Ensure LXC features enabled (if in Proxmox LXC)
# On Proxmox host:
pct set <CTID> --features keyctl=1,nesting=1
```

### Frontend can't reach backend

This usually means the backend isn't healthy yet. Wait 30-60 seconds after startup.

```bash
# Check backend health
docker compose logs backend | tail -20

# Verify health endpoint works
curl http://localhost:3000/api/health
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test direct connection
docker exec -it greenthumb-postgres psql -U greenthumb greenthumb -c "SELECT 1"
```

---

## Production Recommendations

1. **Change default passwords** in `.env`:
   ```bash
   openssl rand -base64 24  # Generate password
   openssl rand -hex 32     # Generate SECRET_KEY
   ```

2. **Enable firewall**:
   ```bash
   ufw allow 22/tcp    # SSH
   ufw allow 3000/tcp  # GreenThumb
   ufw enable
   ```

3. **Regular backups**:
   ```bash
   # Add to crontab
   0 2 * * * docker exec greenthumb-postgres pg_dump -U greenthumb greenthumb > /backup/greenthumb_$(date +\%Y\%m\%d).sql
   ```

4. **Optional: Add HTTPS** with Cloudflare Tunnel or Caddy reverse proxy for external access.

---

## License

MIT License - See LICENSE file for details.

---

## Roadmap

- [ ] Plant photo uploads
- [ ] Frost and heat alerts
- [ ] Companion planting recommendations
- [ ] Harvest tracking
- [ ] Mobile app
- [ ] Smart sensor integration

---

**Built for home lab enthusiasts who want their gardening data under their own control.**
