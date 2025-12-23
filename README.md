# GreenThumb 🌱

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

---

## Architecture

- **Frontend**: Next.js 14+ with TypeScript and Tailwind CSS
- **Backend API**: Python FastAPI with async SQLAlchemy
- **Agent**: Autonomous worker with APScheduler for weather checks
- **Database**: PostgreSQL 16 with PostGIS for geospatial queries
- **Cache/Queue**: Redis for agent task locking
- **Reverse Proxy**: Traefik v3 with automatic service discovery

**See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design**

---

## Quick Start

Get GreenThumb running in under 5 minutes:

```bash
make setup && make up
```

That's it! The platform will be available at:

- **Frontend**: http://green.lab
- **API Docs**: http://api.green.lab/docs
- **Traefik Dashboard**: http://traefik.green.lab (admin/admin)

**For complete deployment instructions, see [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)**

---

## Documentation

| Document | Description |
|----------|-------------|
| **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** | Complete step-by-step deployment on Proxmox Ubuntu container |
| **[Quick Reference](docs/QUICK_REFERENCE.md)** | One-page cheat sheet for commands and troubleshooting |
| **[Architecture](docs/ARCHITECTURE.md)** | System design, technology choices, and data flow |
| **[GitHub Setup](docs/GITHUB_SETUP.md)** | Contributing guidelines and version control workflow |

---

## Prerequisites

Before starting, ensure you have:

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Make** (for convenient commands)
- **At least 4GB RAM** and **10GB disk space**
- **DNS setup** pointing `*.green.lab` to your server IP (or edit `/etc/hosts`)

### DNS Configuration

Add to your `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows):

```
192.168.1.100  green.lab
192.168.1.100  api.green.lab
192.168.1.100  traefik.green.lab
```

Replace `192.168.1.100` with your Proxmox host IP.

---

## Environment Variables Reference

All configuration is done via `.env` file (copied from `.env.example` during setup).

| Variable | Default | Description |
|----------|---------|-------------|
| **Database** |||
| `POSTGRES_USER` | `greenthumb` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `secure_password_here` | PostgreSQL password (⚠️ CHANGE THIS) |
| `POSTGRES_DB` | `greenthumb` | Database name |
| `POSTGRES_HOST` | `postgres` | Database hostname (Docker service name) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `DATABASE_URL` | Auto-generated | Full PostgreSQL connection string |
| **Redis** |||
| `REDIS_HOST` | `redis` | Redis hostname (Docker service name) |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | `redis_secure_pass` | Redis password (⚠️ CHANGE THIS) |
| `REDIS_URL` | Auto-generated | Full Redis connection string |
| **Backend API** |||
| `SECRET_KEY` | Random | JWT signing key (⚠️ CHANGE THIS) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token expiry (24 hours) |
| `ALLOWED_ORIGINS` | `http://green.lab` | CORS allowed origins |
| **Frontend** |||
| `NEXT_PUBLIC_API_URL` | `http://api.green.lab` | Backend API URL for browser |
| **Agent** |||
| `AGENT_CHECK_INTERVAL` | `15` | Weather check interval (minutes) |
| `WEATHER_API_PROVIDER` | `open-meteo` | Weather data source |
| **Traefik** |||
| `DOMAIN_FRONTEND` | `green.lab` | Frontend domain |
| `DOMAIN_API` | `api.green.lab` | API domain |
| `DOMAIN_TRAEFIK` | `traefik.green.lab` | Traefik dashboard domain |
| `ENABLE_HTTPS` | `false` | Enable Let's Encrypt HTTPS |
| `ACME_EMAIL` | `admin@example.com` | Email for Let's Encrypt |

## Common Commands

All commands use Make for convenience:

```bash
# Setup and start
make setup          # Copy .env.example, create directories
make up             # Start all services
make logs           # View all logs
make down           # Stop all services

# Service-specific
make logs-backend   # Backend API logs only
make logs-agent     # Agent worker logs only
make logs-frontend  # Frontend logs only

# Development
make backend-shell  # Open shell in backend container
make agent-shell    # Open shell in agent container
make db-shell       # Open psql in database

# Database
make migrate        # Run Alembic migrations
make migrate-create # Create new migration

# Maintenance
make restart        # Restart all services
make rebuild        # Rebuild all containers from scratch
make clean          # Stop and remove all containers/volumes

# Testing and Quality
make test-backend   # Run backend tests
make format-backend # Format Python code with Black
make lint-backend   # Lint Python code
make type-check     # MyPy type checking
```

## Project Structure

```
.
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API routes
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py      # Authentication
│   │   │   │   │   ├── gardens.py   # Garden CRUD
│   │   │   │   │   ├── plants.py    # Plant CRUD
│   │   │   │   │   └── weather.py   # Weather data
│   │   │   │   └── router.py        # Route aggregation
│   │   │   └── deps.py               # Dependencies (auth)
│   │   ├── core/           # Core configuration
│   │   │   ├── config.py             # Settings
│   │   │   ├── database.py           # SQLAlchemy setup
│   │   │   └── logging_config.py     # JSON logging
│   │   ├── models/         # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── garden.py
│   │   │   ├── plant.py
│   │   │   └── weather.py
│   │   └── schemas.py      # Pydantic schemas
│   ├── main.py             # FastAPI app entry point
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile
│   └── init-db.sql         # Database initialization
│
├── agent/                  # Autonomous worker
│   ├── worker.py           # Scheduler and jobs
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/               # Next.js application
│   ├── app/
│   │   ├── page.tsx        # Dashboard
│   │   ├── layout.tsx      # Root layout
│   │   └── globals.css     # Tailwind styles
│   ├── lib/
│   │   └── api.ts          # Typed API client
│   ├── package.json
│   ├── tsconfig.json       # TypeScript config (strict mode)
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── Dockerfile
│
├── docs/
│   └── ARCHITECTURE.md     # System architecture docs
│
├── docker-compose.yml      # Service orchestration
├── .env.example            # Environment template
├── .gitignore
├── Makefile                # Convenience commands
└── README.md               # This file
```

## First Steps After Installation

1. **Create an account**:
   - Visit http://green.lab
   - Click "Sign In" → "Register"
   - Enter email and password

2. **Create your first garden**:
   - Click "Create Your First Garden"
   - Enter garden name and description
   - Add GPS coordinates (latitude/longitude)
   - Submit

3. **Add plants**:
   - Open your garden
   - Click "Add Plant"
   - Enter plant details (name, variety, planting date)
   - Save

4. **Check weather**:
   - Weather data is automatically collected every 15 minutes
   - View weather history in your garden dashboard
   - Agent logs available: `make logs-agent`

## API Documentation

Interactive API docs are auto-generated by FastAPI:

- **Swagger UI**: http://api.green.lab/docs
- **ReDoc**: http://api.green.lab/redoc

All endpoints require JWT authentication (except `/auth/register` and `/auth/login`).

### Authentication Flow

```bash
# 1. Register
curl -X POST http://api.green.lab/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123","full_name":"Test User"}'

# 2. Login
curl -X POST http://api.green.lab/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=secure123"

# Response: {"access_token":"eyJ...","token_type":"bearer"}

# 3. Use token
curl -X GET http://api.green.lab/api/v1/gardens \
  -H "Authorization: Bearer eyJ..."
```

## Monitoring and Logs

### Structured JSON Logs

All services output structured JSON logs:

```bash
# View real-time logs
make logs

# Filter specific service
make logs-backend | jq 'select(.level=="ERROR")'

# Find slow queries
make logs-backend | jq 'select(.duration > 1000)'

# Agent weather check logs
make logs-agent | jq 'select(.message | contains("weather"))'
```

### Health Checks

Each service has a health endpoint:

- **Backend**: http://api.green.lab/health
- **Database**: `docker exec greenthumb-postgres pg_isready`
- **Redis**: `docker exec greenthumb-redis redis-cli ping`

### Traefik Dashboard

Monitor all services at http://traefik.green.lab:

- HTTP routers and services
- TLS certificates (if HTTPS enabled)
- Request metrics

## Production Deployment

### Enable HTTPS

1. Get a domain (e.g., `gardening.yourdomain.com`)
2. Point DNS to your Proxmox host
3. Update `.env`:
   ```
   ENABLE_HTTPS=true
   DOMAIN_FRONTEND=gardening.yourdomain.com
   DOMAIN_API=api.gardening.yourdomain.com
   ACME_EMAIL=your@email.com
   ```
4. Restart: `make restart`

Traefik will automatically obtain Let's Encrypt certificates.

### Security Hardening

1. **Change default passwords** in `.env`:
   - `POSTGRES_PASSWORD`
   - `REDIS_PASSWORD`
   - `SECRET_KEY` (generate with `openssl rand -hex 32`)

2. **Firewall rules**:
   ```bash
   # Allow only HTTP/HTTPS
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw deny 8080/tcp  # Block Traefik dashboard externally
   ```

3. **Backups**:
   ```bash
   # Database backup
   docker exec greenthumb-postgres pg_dump -U greenthumb greenthumb > backup.sql
   
   # Restore
   docker exec -i greenthumb-postgres psql -U greenthumb greenthumb < backup.sql
   ```

## Troubleshooting

### Services won't start

```bash
# Check logs
make logs

# Verify ports aren't in use
netstat -tulpn | grep -E ':(80|443|5432|6379|8000|3000)'

# Rebuild from scratch
make clean
make rebuild
make up
```

### Database connection errors

```bash
# Check database is running
docker ps | grep postgres

# Test connection
docker exec -it greenthumb-postgres psql -U greenthumb -d greenthumb

# Verify DATABASE_URL in .env
```

### Agent not collecting weather

```bash
# Check agent logs
make logs-agent

# Verify Redis connection
docker exec -it greenthumb-redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d '=' -f2) ping

# Manually trigger weather check (requires Python in container)
docker exec -it greenthumb-agent python -c "from worker import weather_check_job; weather_check_job()"
```

### Frontend can't reach API

```bash
# Check NEXT_PUBLIC_API_URL in .env matches api domain
# Verify Traefik routing
curl -H "Host: api.green.lab" http://localhost/health

# Check CORS settings in backend/app/core/config.py
```

## Contributing

Contributions are welcome! Please see our [GitHub Setup Guide](docs/GITHUB_SETUP.md) for:

- How to fork and customize
- Contributing guidelines
- Code style standards
- Pull request process
- Version control workflow

**Quick Contributing Steps:**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes with tests
4. Follow code style: `make format-backend` and `make lint-frontend`
5. Submit a pull request

---

## License

MIT License - See LICENSE file for details.

---

## Support and Resources

**Getting Help:**
- Check the [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) for setup issues
- Review the [Quick Reference](docs/QUICK_REFERENCE.md) for common commands
- Search [existing issues](https://github.com/yourusername/greenthumb/issues)
- Open a [new issue](https://github.com/yourusername/greenthumb/issues/new) with logs and details

**Useful Links:**
- [Architecture Documentation](docs/ARCHITECTURE.md) - Understand system design
- [API Documentation](http://api.green.lab/docs) - Interactive API docs (when running)
- [Traefik Dashboard](http://traefik.green.lab) - Monitor services (when running)

---

## Roadmap

Future enhancements planned:

- [ ] Plant photo uploads with image storage
- [ ] Frost and heat alerts via email/push notifications
- [ ] Companion planting recommendations
- [ ] Harvest tracking and yield analytics
- [ ] Mobile app (React Native)
- [ ] Integration with smart sensors (soil moisture, etc.)
- [ ] Multi-user support with shared gardens
- [ ] Export data to CSV/JSON

**Want to contribute?** Pick an item and open a PR!

---

**Built with ❤️ for home lab enthusiasts**

*If you find GreenThumb useful, please consider starring the repository!*

