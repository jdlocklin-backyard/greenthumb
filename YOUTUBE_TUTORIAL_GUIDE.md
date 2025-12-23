# GreenThumb YouTube Tutorial Guide: Proxmox Home Lab Deployment

**Target Audience**: Home lab enthusiasts comfortable with Linux and Docker basics, but may lack experience with microservices, Traefik, or PostGIS.

**Video Length**: Plan for 3-4 episodes (60-90 min total)
- **Episode 1**: Prerequisites, Infrastructure Setup (25 min)
- **Episode 2**: Deployment & Service Walkthrough (35 min)
- **Episode 3**: Configuration, Testing & Troubleshooting (20-30 min)

---

## 1. DEPLOYMENT PREREQUISITES

### 1.1 What Viewers MUST Understand Before Starting

#### Proxmox Container Basics
**Concept**: Containers are like lightweight virtual machines that share the host's OS kernel.

**Why This Matters**:
- Unlike VMs, containers don't need their own operating system
- Much faster to start/stop (seconds vs minutes)
- Use less disk space and RAM
- Still isolated from each other (network, filesystem, processes)

**Analogy for Explanation**:
> Think of a container like a shipping container. Each container holds different cargo (software), they stack efficiently, and they all use the same port infrastructure (the host). But each container is sealed—cargo from one doesn't leak into another.

**What Viewers Need**:
- Proxmox host running (the "port authority")
- Ubuntu 22.04 LTS or 24.04 container template available
- Network access from container to external APIs (Open-Meteo for weather)

---

#### Docker & Docker Compose Basics
**Concept**: Docker is the container technology; Docker Compose orchestrates multiple containers.

**The Two-Step Mental Model**:
1. **Docker** = Creates individual containers from instructions (Dockerfiles)
2. **Docker Compose** = Conductor that tells all containers how to work together

**Why This Matters for GreenThumb**:
- We're running 6 containers that must communicate
- Docker Compose handles networking, volumes, environment variables automatically
- Without Compose, we'd manually start each container with complex networking flags

**Analogy for Explanation**:
> Docker is like a recipe that says "use these ingredients and follow these steps to cook chicken." Docker Compose is like a full meal plan that says "make chicken (recipe 1), make rice (recipe 2), put them on the same plate."

**What Viewers Need to Know**:
```
docker ps          # See running containers
docker logs -f     # Watch live logs
docker exec -it    # Get shell inside container
```

**Prerequisites Check**:
```bash
docker --version  # Should be 24.0+
docker compose --version  # Should be 2.20+
```

---

#### Container Networking Fundamentals
**Problem**: 6 separate containers need to talk to each other. How?

**The Solution: Docker Networks**

Docker creates a virtual network bridge. Think of it as a private office building:
- Each container gets an IP address (like office suite numbers)
- Containers can reach each other using container names (like calling an extension)
- Only Traefik has a door to the outside world (ports 80, 443)

**Visual Explanation**:
```
┌─────────────────────────────── Docker Host (Proxmox VM) ──────────────────────┐
│                                                                                 │
│  ┌─────────────────────────── greenthumb network (bridge) ──────────────────┐ │
│  │                                                                           │ │
│  │  Backend (8000)    Redis (6379)     Postgres (5432)   Agent (worker)    │ │
│  │    container         container         container        container        │ │
│  │       │                 │                 │                │             │ │
│  │       └─────────────────┼─────────────────┼────────────────┘             │ │
│  │                         │                                                 │ │
│  │                    greenthumb network (internal DNS)                      │ │
│  │                                                                           │ │
│  │                                                                           │ │
│  │  Frontend (3000)                                                         │ │
│  │    container                                                             │ │
│  │       │                                                                   │ │
│  │       └────────────────────────────────────────────────────────────┐    │ │
│  │                                                                    │    │ │
│  └────────────────────────────────────────────────────────────────────┼────┘ │
│                                                                        │      │
│  ┌──────────────────────── Traefik Container ────────────────────────┼─────┐ │
│  │                                                                    │     │ │
│  │  Listens on :80 → Routes to Frontend (:3000)                      │     │ │
│  │             → Routes to Backend (:8000)                           │     │ │
│  │             → Routes to Traefik Dashboard (:8080)                 │     │ │
│  │                                                                    │     │ │
│  └────────────────────────────────────────────────────────────────────┼─────┘ │
│                                                                        │      │
│    ◄────────────── port 80 (external HTTP traffic) ─────────────────┘       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Key Networking Concepts for Tutorial**:
1. **Container Names = Hostnames**: When backend talks to Postgres, it uses hostname `postgres` (not an IP)
2. **Port Mapping**: Only Traefik maps ports to host. Backend port 8000 is unreachable directly—you must go through Traefik
3. **External APIs**: All containers can reach the internet (Open-Meteo, etc.) via host's network

---

#### DNS Configuration for Home Lab
**Problem**: How do we access `green.lab`, `api.green.lab` from our local computers?

**Two Approaches**:

**Approach 1: Local `/etc/hosts` (Simple, Perfect for Home Lab)**
```bash
# On your client machine (laptop, desktop)
192.168.1.100  green.lab
192.168.1.100  api.green.lab
192.168.1.100  traefik.green.lab
```

**Why This Works**:
- Your browser asks "where is green.lab?" → checks `/etc/hosts` → finds 192.168.1.100
- Sends HTTP request to that IP
- Traefik on that IP sees the hostname in the request, routes accordingly

**Approach 2: Local DNS Server (More Complex, Future-Proof)**
- Set up Pi-hole, dnsmasq, or Bind9 in home lab
- Points all `.green.lab` requests to Proxmox VM
- Any device on network automatically works (no `/etc/hosts` on each machine)

**For Tutorial**: Use Approach 1 (simpler, works immediately)

**Key Point to Explain**:
> DNS is like a phone book. When you type `green.lab` in your browser, it looks up the number (IP address). We're just pre-filling that phone book entry on your computer.

---

### 1.2 Prerequisites Checklist for Viewers

**Physical Requirements**:
- [ ] Proxmox host with 4GB+ RAM available
- [ ] 10GB+ free disk space
- [ ] Network connection (for pulling Docker images, weather API calls)

**Software Requirements**:
- [ ] Ubuntu 22.04 LTS or 24.04 container in Proxmox (or nested VM)
- [ ] Docker 24.0+ installed
- [ ] Docker Compose 2.20+ installed
- [ ] Make utility (for convenient commands)
- [ ] Git (to clone the project)
- [ ] A code editor (VS Code recommended)

**Knowledge Requirements**:
- [ ] Comfortable with Linux command line basics (ls, cd, nano/vim)
- [ ] Understand what Docker containers are
- [ ] Know how to manage services (systemctl, or similar)
- [ ] Basic understanding of networking (IPs, ports, DNS)

**Verification Commands** (show on screen):
```bash
# All of these should return version info without errors
uname -a
docker --version
docker compose version
make --version
git --version
```

---

## 2. COMPLEXITY HOTSPOTS: Where Viewers Will Get Confused

### 2.1 Docker Compose Concepts

**Hotspot**: Understanding `services`, `environment`, and `depends_on`

**What Confuses Beginners**:
```yaml
services:
  backend:
    environment:
      POSTGRES_HOST: postgres  # Why is this "postgres"?
    depends_on:
      postgres:
        condition: service_healthy  # What does "healthy" mean?
```

**How to Explain It**:

**Container Names vs Network Names**:
> When you say "depends_on: postgres", you're not talking about a file or a computer. You're talking about another service defined in this same compose file. Docker will create a container named "postgres" and put it on the greenthumb network where the backend can reach it by name.

**Host vs Localhost vs Service Name**:
```
POSTGRES_HOST: postgres
  ├─ NOT your Proxmox host (192.168.1.100)
  ├─ NOT localhost (127.0.0.1) — that won't work!
  └─ IS the service name in docker-compose.yml
```

**What `service_healthy` Means**:
```yaml
healthcheck:
  test: ["CMD", "pg_isready", "-U", "${POSTGRES_USER}"]
  interval: 10s
  timeout: 5s
  retries: 5
```

> Docker continuously pings Postgres asking "are you ready?" Every 10 seconds, it runs `pg_isready`. If it passes 5 times in a row without timing out, Docker marks the service as "healthy." The backend doesn't start until this happens.

**Explanation Approach**:
1. Show the `docker-compose.yml` file
2. Highlight each service box with different colors on screen
3. Show actual running commands:
   ```bash
   docker ps -a  # Show all containers running from this compose file
   docker network ls  # Show greenthumb network
   docker network inspect greenthumb  # Show which containers are on it
   ```

---

### 2.2 Traefik Reverse Proxy (The Big One)

**Hotspot**: Why do we need Traefik? How does it know which request goes where?

**The Problem It Solves**:
Without Traefik:
- Frontend would be on port 3000, not port 80
- Backend on 8000, not 80
- You'd visit `green.lab:3000` instead of just `green.lab`
- Having 6 services means 6 different ports to remember

**The Solution Traefik Provides**:
Single entry point (port 80/443) that routes based on the hostname in the HTTP request.

**Visual Analogy for Explanation** (use screen recording):
> Think of Traefik like a receptionist at a hotel. When you arrive at the hotel, you go to the front desk (port 80). You tell the receptionist "I'm checking in as John" (you send a request with `Host: green.lab`). The receptionist knows that John's room is 3000 (the frontend container), so they hand you a key to that room. If someone else comes and says "I'm here for meetings" (Host: api.green.lab), the receptionist sends them to room 8000 (the backend).

**How Docker Labels Work**:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.frontend.rule=Host(`${TRAEFIK_DOMAIN:-green.lab}`)"
  - "traefik.http.routers.frontend.entrypoints=web"
  - "traefik.http.services.frontend.loadbalancer.server.port=3000"
```

**Breaking This Down Line by Line**:
1. `traefik.enable=true` — "Tell Traefik about this service"
2. `traefik.http.routers.frontend.rule=Host(...)` — "Route requests where Host header matches"
3. `traefik.http.routers.frontend.entrypoints=web` — "Watch port 80 (the 'web' entrypoint)"
4. `traefik.http.services.frontend.loadbalancer.server.port=3000` — "Forward requests to container port 3000"

**On-Screen Demonstration**:
1. Show the docker-compose.yml with labels highlighted
2. Show Traefik dashboard at `traefik.green.lab` (admin/admin)
   - Show the "Routers" section — lists: frontend, backend, traefik
   - Show the "Services" section — shows what each router points to
   - Explain: "These labels are automatically read from docker-compose.yml"
3. Show a network trace:
   ```bash
   # Terminal 1: Watch Traefik logs
   docker logs -f greenthumb-traefik

   # Terminal 2: Make a request from browser/curl
   curl -H "Host: green.lab" http://localhost/

   # Terminal 1 shows: "Request for green.lab → forward to frontend:3000"
   ```

**Common Beginner Mistake**:
> "Why can't I access the backend on `http://localhost:8000`?"

**Answer**: "In Docker, localhost means 'inside the container'. Port 8000 isn't exposed to your computer. Only Traefik has a door to the outside (port 80). You must go through Traefik by visiting `http://api.green.lab` (which routes to port 8000 internally)."

---

### 2.3 Environment Variables & .env File

**Hotspot**: How `.env` file values flow into services

**The Flow**:
```
.env (disk file)
  ↓
docker-compose.yml reads via env_file: .env
  ↓
Each service gets environment variables
  ↓
Services use them (DATABASE_URL, SECRET_KEY, etc.)
```

**Critical Variables to Explain**:

| Variable | Value in .env | Used By | Purpose |
|----------|--------------|---------|---------|
| `POSTGRES_PASSWORD` | `secure_password_here` | Postgres container init | Initial password for `greenthumb` user |
| `POSTGRES_HOST` | `postgres` | Backend, Agent | Hostname to reach Postgres (service name) |
| `DATABASE_URL` | `postgresql://greenthumb:...` | Backend, Agent | Full connection string (auto-generated) |
| `REDIS_PASSWORD` | `redis_secure_pass` | Agent, Redis | Password for Redis auth |
| `REDIS_HOST` | `redis` | Backend, Agent | Hostname to reach Redis (service name) |
| `SECRET_KEY` | Random string | Backend | Signing key for JWT tokens |
| `NEXT_PUBLIC_API_URL` | `http://api.green.lab` | Frontend | Where frontend browser requests go |
| `TRAEFIK_DOMAIN` | `green.lab` | Traefik labels | Domain for frontend |
| `TRAEFIK_API_DOMAIN` | `api.green.lab` | Traefik labels | Domain for backend |

**The Dangerous Ones** (stress this in video):
```env
POSTGRES_PASSWORD=secure_password_here      # ⚠️ CHANGE THIS!
REDIS_PASSWORD=redis_secure_pass            # ⚠️ CHANGE THIS!
SECRET_KEY=random_string_123                # ⚠️ CHANGE THIS!
```

**How to Explain**:
> These are passwords. If someone gains access to your `.env` file, they can log into your database and Redis. In a home lab, it's less critical, but in production, treat `.env` like a house key—don't leave it lying around, and don't commit it to git.

**On-Screen Demonstration**:
1. Show the `.env` file
2. Show how it's referenced in `docker-compose.yml`:
   ```yaml
   env_file:
     - .env
   ```
3. Show environment variables inside a running container:
   ```bash
   docker exec greenthumb-backend env | grep POSTGRES
   # Output:
   # POSTGRES_USER=greenthumb
   # POSTGRES_PASSWORD=secure_password_here
   # POSTGRES_HOST=postgres
   ```

**Common Mistake**:
> "I changed `.env` but the change didn't take effect!"

**Answer**: "Docker only reads `.env` when you start the container. You need to restart: `docker compose down && docker compose up`"

---

### 2.4 Database Initialization & PostGIS

**Hotspot**: Understanding PostGIS and why the database initialization script is necessary

**What is PostGIS?**

**Simple Explanation**:
> PostgreSQL is a regular database. PostGIS is an extension that adds geographic superpowers—it understands latitude/longitude coordinates and can answer questions like "find all gardens within 10km of my current location."

**Why GreenThumb Uses It**:
- Stores garden coordinates (latitude, longitude)
- Can query gardens by geographic proximity
- Uses `POINT` data type: a single location on Earth

**How It Gets Initialized**:
```yaml
# In docker-compose.yml
postgres:
  volumes:
    - ./backend/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql:ro
```

**What This Does**:
1. When Postgres container first starts, it checks `/docker-entrypoint-initdb.d/` directory
2. Runs any `.sql` files in alphabetical order
3. Our `init-db.sql` creates PostGIS extension, tables, indexes

**Analogy for Explanation**:
> Think of it like moving into a new house. The moving truck (container) comes with a checklist (init-db.sql). As soon as the container "moves in," it checks off the list: "Install gas hookup (PostGIS extension), build bookshelves (create tables), add locks (indexes)."

**On-Screen Demonstration**:
```bash
# Check PostGIS is enabled
docker exec greenthumb-postgres psql -U greenthumb -d greenthumb -c "SELECT extension FROM pg_extension WHERE extname = 'postgis';"

# Show a garden record with POINT data
docker exec greenthumb-postgres psql -U greenthumb -d greenthumb -c "SELECT name, ST_AsText(location) FROM gardens LIMIT 1;"
# Output: Backyard Garden | POINT(-118.2437 34.0522)
```

**What Can Go Wrong**:
1. **init-db.sql doesn't run** (database already has old data)
   - Solution: `make clean` to remove volumes, then restart
2. **PostGIS functions not found**
   - Solution: Check that `postgis/postgis:16-3.4` image is actually used
   - Run: `docker exec greenthumb-postgres psql -U greenthumb -c "\dx" | grep postgis`

---

### 2.5 Agent & Redis Locking

**Hotspot**: Why do we need Redis? Why is "locking" important?

**The Problem the Agent Solves**:
- Every 15 minutes, weather data should be collected
- If we had multiple agents (for redundancy), they'd all fetch weather simultaneously
- That wastes API calls and causes duplicate database records

**Redis Lock Solution**:
```python
# Agent pseudo-code
lock = redis_client.get("agent:weather_check:lock")
if lock_exists:
    exit()  # Another instance is running, skip

redis_client.setex("agent:weather_check:lock", 300, "locked")  # Lock for 5 min
try:
    fetch_weather_for_all_gardens()
finally:
    redis_client.delete("agent:weather_check:lock")  # Release lock
```

**Analogy for Explanation**:
> Redis lock is like a bathroom key. When Agent #1 goes into the bathroom, it takes the key. Agent #2 tries to use the bathroom, sees the key is gone, and waits. When Agent #1 finishes, it returns the key. Only one person uses the bathroom at a time.

**Why Redis and Not Just Files?**
- Files are slow
- Multiple containers can't reliably check the same file
- Redis is designed for distributed locking
- It's already in our architecture (bonus: can use for caching later)

**On-Screen Demonstration**:
```bash
# Check Redis is running
docker exec greenthumb-redis redis-cli ping
# Output: PONG

# During a weather check, watch the lock
docker exec greenthumb-redis redis-cli KEYS "*lock*"
# Output: agent:weather_check:lock

# See when it disappears (after job finishes)
watch -n 1 'docker exec greenthumb-redis redis-cli KEYS "*lock*"'
```

---

## 3. VISUAL DEMONSTRATION OPPORTUNITIES

### What MUST Be Shown On Screen

#### 3.1 System Architecture Diagram
**When**: Episode 1 intro
**Duration**: 5 minutes
**What**: Build the diagram live, explaining each component

```
Live demo flow:
1. Draw Proxmox container running Ubuntu
2. Draw Docker Host inside it
3. Add Traefik box (highlight port 80 mapping)
4. Add Frontend, Backend, Agent boxes (no port mappings)
5. Add PostgreSQL, Redis boxes (internal only)
6. Draw arrows showing data flow
7. Show the greenthumb bridge network connecting everything
```

**Script**:
> "Here's our Proxmox container. Inside, Docker creates an isolated network called 'greenthumb.' Traefik is our gate keeper—it sits at port 80 (the only door to the outside). When a request comes in for green.lab, Traefik checks its routing rules and sends it to the Frontend. For api.green.lab, it routes to the Backend. PostgreSQL and Redis live internally—they never talk to the outside world."

---

#### 3.2 Docker Compose File Walkthrough
**When**: Episode 1, 10 minutes
**What**: Show the YAML file, highlight sections with colors

```
Highlights:
- services: (all 6 containers listed)
- environment variables section for each
- volumes (data/db, data/redis)
- healthcheck blocks
- networks section at bottom
- labels on Traefik, Backend, Frontend
```

**Live Commands**:
```bash
# Show the file structure
tree -I 'node_modules|.env' -a

# Validate syntax
docker compose config

# Show which services will be created
docker compose config | grep "services:" -A 50
```

---

#### 3.3 Container Startup Sequence
**When**: Episode 2, deployment
**Duration**: 2-3 minutes
**What**: Run `docker compose up` and narrate what's happening

```bash
docker compose up

# Narration:
# 1. "Building backend image from Dockerfile..." (shows layer downloads)
# 2. "Starting Traefik container..."
# 3. "Starting PostgreSQL..." (shows init-db.sql running)
# 4. "PostgreSQL not ready yet, other services waiting..."
# 5. "PostgreSQL healthy! Starting backend..."
# 6. "Backend starting, healthcheck running..."
# 7. "All services up! Traefik routing configured!"
```

**Split Screen**:
- Left: Terminal showing docker compose logs
- Right: Browser with Traefik dashboard reloading every second
  - Watch services go from "down" → "down" → "up"

---

#### 3.4 Traefik Dashboard Live Walkthrough
**When**: Episode 2, after services are running
**Duration**: 5 minutes
**What**: Click through the dashboard, explain what you see

```
Navigate to http://traefik.green.lab
Login: admin/admin

Show:
1. HTTP Routers section
   - frontend: green.lab → frontend:3000
   - backend: api.green.lab → backend:8000
   - traefik: traefik.green.lab → api@internal

2. Services section
   - Each router's target service and port

3. Middleware section
   - CORS headers for API
   - Compression for frontend

4. Make a request while watching
   - curl http://green.lab/
   - Watch request appear in Traefik logs
   - Explain "incoming request Host: green.lab → router matches → forward to frontend:3000"
```

---

#### 3.5 API Documentation Live Demo
**When**: Episode 2, testing
**Duration**: 3 minutes
**What**: Show FastAPI's auto-generated Swagger UI

```
Navigate to http://api.green.lab/docs

Show:
1. Registration endpoint
   - Explain request/response schema
   - Click "Try it out"
   - Create a test user

2. Login endpoint
   - Mention OAuth2 form format
   - Log in with test user
   - Copy the access_token

3. Gardens endpoint
   - Show it requires authorization header
   - Paste token in "Authorize" button
   - List gardens (empty on first run)

4. Explain: "This is auto-generated from our Python code. Every endpoint here is type-safe."
```

---

#### 3.6 Database Structure & PostGIS Queries
**When**: Episode 2, after deployment
**Duration**: 4 minutes
**What**: Connect to database and show tables/data

```bash
docker exec -it greenthumb-postgres psql -U greenthumb -d greenthumb

\dt  # Show tables

# Show PostGIS location column
SELECT
  name,
  ST_AsText(location) AS coordinates,
  created_at
FROM gardens
LIMIT 5;

# Show geospatial query example
SELECT
  name,
  ST_Distance(location, ST_Point(-118.2437, 34.0522)::geography) / 1000 AS km_away
FROM gardens
WHERE ST_Distance(location, ST_Point(-118.2437, 34.0522)::geography) < 50000
ORDER BY ST_Distance(location, ST_Point(-118.2437, 34.0522)::geography);

# Explain: "This finds gardens within 50km of a coordinate using PostGIS."
```

---

#### 3.7 Agent Logs & Weather Collection
**When**: Episode 2-3, monitoring
**Duration**: 5 minutes
**What**: Watch agent collect weather in real-time

```bash
docker logs -f greenthumb-agent

# Wait for scheduled job to run (or create garden then wait 15 min)
# Show JSON logs with structure:
# {"level":"INFO","message":"Weather collected","service":"agent","garden":"Backyard Garden","temperature":"25C"}

# Parse with jq
docker logs greenthumb-agent | jq 'select(.message | contains("weather"))'

# Show how Redis lock works during weather check
docker exec greenthumb-redis redis-cli MONITOR  # In background
# During weather check, see: "SET agent:weather_check:lock"
```

---

### What Should Be Explained Verbally (Not Shown)

1. **Async/Await in FastAPI** — too much code, but explain concept
2. **JWT token structure** — show example, explain three parts
3. **Bcrypt password hashing** — why it's intentionally slow
4. **CORS headers** — what problem they solve
5. **Database migrations with Alembic** — mention, but don't dive deep

---

## 4. COMMON PITFALLS & How to Troubleshoot

### 4.1 DNS Resolution Failures

**Symptom**: "I can access frontend but not api.green.lab" or vice versa

**Root Causes**:
1. `/etc/hosts` entry missing or wrong IP
2. DNS hasn't propagated yet (if using real domain + Let's Encrypt)
3. Frontend can't reach API at the URL specified

**How to Diagnose On-Screen**:
```bash
# Test DNS
ping green.lab
ping api.green.lab

# If ping works but browser fails:
curl -v http://api.green.lab/docs  # -v shows headers

# Check what the frontend thinks the API URL is
docker exec greenthumb-frontend env | grep NEXT_PUBLIC_API_URL

# If wrong, rebuild frontend:
docker compose build frontend
docker compose up frontend
```

**Tutorial Explanation**:
> "When you visit green.lab in your browser, three things must be true:
> 1. Your computer knows green.lab = 192.168.1.100 (check /etc/hosts)
> 2. Your firewall lets port 80 through (usually yes)
> 3. Traefik is running and sees the request (check docker ps)"

---

### 4.2 Port Conflicts

**Symptom**: "Address already in use" error for port 80 or 443

**Root Causes**:
1. Another service on host listening on same port
2. Proxmox host firewall blocking
3. Another Docker Compose project already running Traefik

**How to Diagnose**:
```bash
# Check what's listening on port 80
sudo lsof -i :80
# or
sudo netstat -tulpn | grep :80

# If it's Traefik from another project, stop it first
docker compose -f /other/project/docker-compose.yml down

# If it's something else, decide:
# - Stop it: sudo systemctl stop apache2
# - Use different port: Modify docker-compose.yml port mapping
```

**Tutorial Explanation**:
> "Ports are like numbered doors on a building. If port 80 is already in use by another service, Traefik can't open that door. We need to find what's using it and either stop it or use a different port."

---

### 4.3 Database Connection Errors

**Symptom**: "Backend can't connect to PostgreSQL" — backend crashes with connection timeout

**Root Causes**:
1. `POSTGRES_HOST` is wrong (should be `postgres`, not an IP)
2. Postgres not fully initialized yet (hasn't reached healthy state)
3. Wrong password in `DATABASE_URL`
4. Postgres volume has old corrupted data

**How to Diagnose**:
```bash
# Check Postgres is running
docker ps | grep postgres

# Check Postgres is healthy
docker ps | grep postgres  # Status should show "healthy"

# Try connecting manually
docker exec greenthumb-postgres psql -U greenthumb -d greenthumb -c "SELECT 1;"

# Check DATABASE_URL is correct
docker exec greenthumb-backend env | grep DATABASE_URL

# If all else fails, nuke the volume
docker compose down
rm -rf data/db  # ⚠️ This deletes all data!
docker compose up
```

**Tutorial Explanation**:
> "When the backend starts, it needs to immediately connect to Postgres. But Postgres might not be ready yet—it's still initializing. That's why we use `depends_on: condition: service_healthy`. Docker waits until Postgres says 'I'm ready,' then starts the backend."

---

### 4.4 Redis Connection & Locking Issues

**Symptom**: "Agent logs show Redis connection error" OR "Agent weather checks stop running"

**Root Causes**:
1. `REDIS_HOST` wrong in .env
2. `REDIS_PASSWORD` wrong in .env
3. Redis container not running
4. Agent stuck with held lock (shouldn't happen but can)

**How to Diagnose**:
```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
docker exec greenthumb-redis redis-cli ping  # Should say PONG

# If password-protected:
docker exec greenthumb-redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d '=' -f2) ping

# Check what keys are in Redis
docker exec greenthumb-redis redis-cli KEYS "*"

# Check if weather lock exists (shouldn't, but if stuck)
docker exec greenthumb-redis redis-cli GET "agent:weather_check:lock"

# Clear stuck lock
docker exec greenthumb-redis redis-cli DEL "agent:weather_check:lock"

# Restart agent
docker compose restart agent
```

**Tutorial Explanation**:
> "Redis is like a mailbox. The agent puts a 'weather-collection-in-progress' note in the mailbox, does the job, then removes the note. If the note is stuck (because the agent crashed), the backup agent sees it and waits. We can manually remove stuck notes with redis-cli DEL."

---

### 4.5 Frontend Can't Reach Backend API

**Symptom**: "Frontend loads but buttons don't work" or network errors in browser console

**Root Causes**:
1. `NEXT_PUBLIC_API_URL` is wrong
2. CORS not configured correctly
3. Backend not running/responding
4. Traefik routing wrong for API domain

**How to Diagnose On-Screen**:
```bash
# 1. Check API URL
docker exec greenthumb-frontend env | grep NEXT_PUBLIC_API_URL

# 2. Check API responds
curl -v http://api.green.lab/health

# 3. Watch browser network tab
# Open DevTools (F12) → Network → Reload page
# Look for failed requests to /api/v1/*
# Check response headers for CORS errors

# 4. Check Traefik is routing API correctly
docker logs greenthumb-traefik | grep api.green.lab

# 5. Test with curl and auth header
curl -H "Host: api.green.lab" http://localhost/api/v1/health
```

**Tutorial Explanation**:
> "The frontend (running in your browser) tries to fetch data from the API. The browser blocks this request if:
> 1. The URL is wrong (NEXT_PUBLIC_API_URL)
> 2. The API doesn't allow the request (CORS headers)
> Check the browser console—it tells you exactly what went wrong."

---

### 4.6 Environment Variable Mistakes

**Symptom**: Services start but behave unexpectedly

**Common Mistakes**:
1. Quotes in `.env` included in value
   ```env
   # Wrong:
   POSTGRES_PASSWORD="password123"
   # Right:
   POSTGRES_PASSWORD=password123
   ```

2. Special characters not escaped
   ```env
   # Wrong:
   SECRET_KEY=my$ecure&key
   # Right:
   SECRET_KEY=my\$ecure\&key
   ```

3. Whitespace in values
   ```env
   # Wrong:
   POSTGRES_HOST = postgres  # (spaces around =)
   # Right:
   POSTGRES_HOST=postgres
   ```

**How to Diagnose**:
```bash
# See actual values
docker exec greenthumb-backend env | grep SECRET_KEY

# Validate syntax
docker compose config  # Shows parsed values
```

**Tutorial Demonstration**:
```bash
# Show .env file editing
nano .env

# Show how docker reads it
docker compose config | grep -A 20 "services:"

# Demonstrate the difference
# Wrong: value includes quotes
# Right: value is just the string
```

---

### 4.7 Volume & File Permissions Issues

**Symptom**: "Permission denied" errors in logs

**Root Causes**:
1. Container user (1000) doesn't own mount directories
2. Directory doesn't exist yet

**How to Fix**:
```bash
# Create directories if they don't exist
mkdir -p data/db data/redis logs/backend logs/agent

# Set correct ownership
sudo chown -R 1000:1000 data/ logs/

# Or use Docker to create them properly
docker compose run backend mkdir -p /app/logs
```

**Tutorial Explanation**:
> "Docker containers run as non-root users for security. The backend runs as user 1000. If we mount a directory owned by root, the container can't write to it. We need to give ownership to user 1000 first."

---

## 5. CONCEPTUAL EXPLANATIONS BROKEN DOWN

### 5.1 How Traefik Reverse Proxy Works

**The Simple Version** (for non-technical viewers):
> A reverse proxy is a traffic director. Imagine Traefik is a hotel receptionist. When you call the hotel's main number (port 80), the receptionist doesn't answer your call—they transfer you to the right room. You don't know (or care) which room, you just call the main number.

**The Detailed Version** (with visuals):

**Step 1: Request comes in**
```
Browser: GET / (with Host: green.lab)
         ↓
Traefik (listening on port 80): "Aha, this is for green.lab"
         ↓
Checks routing rules (from docker-compose.yml labels)
```

**Step 2: Traefik matches the rule**
```
Rule: "Host(`green.lab`)"
Request Host: green.lab
Result: ✓ MATCH
```

**Step 3: Traefik routes to the right service**
```
"green.lab matches frontend rule"
"frontend rule points to frontend:3000"
Forward request to 172.18.0.3:3000 (frontend's IP on docker network)
```

**Step 4: Response comes back**
```
Frontend: <html>...</html>
    ↓
Traefik: Receives response, sends back to browser
    ↓
Browser: Displays page
```

**Visual Diagram** (draw this on screen):
```
┌─────────────────────────────────────────────────┐
│                   Traefik                        │
│                                                  │
│  Listening on port 80:                          │
│                                                  │
│  Request → Host: green.lab? ──→ frontend:3000  │
│         ↓                                        │
│         Host: api.green.lab? ──→ backend:8000  │
│         ↓                                        │
│         Host: traefik.green.lab? ──→ api@internal│
│                                                  │
└─────────────────────────────────────────────────┘
```

**Why Not Just Use Backend's Port Directly?**

**Without Traefik**:
```
Browser → http://192.168.1.100:8000  (hard to remember)
Browser → http://192.168.1.100:3000  (hard to remember)
Browser → http://192.168.1.100:5432  (don't expose this!)
```

**With Traefik**:
```
Browser → http://api.green.lab  (easy, memorable)
Browser → http://green.lab  (easy, memorable)
```

---

### 5.2 Why Redis is Needed for the Agent

**The Problem**: Without Redis

Imagine two agents running (for redundancy). Both check the weather at the same time:
```
Agent 1: "I'll check weather for all gardens"
Agent 2: "I'll also check weather for all gardens"
         ↓
Both hit Open-Meteo API simultaneously (inefficient, may rate-limit)
Both write to database simultaneously (duplicate records)
```

**The Solution**: Redis Locking

```
Agent 1: "Let me get the weather-check lock..."
         Gets it. Sets: "LOCK_EXISTS"
Agent 2: "Let me get the weather-check lock..."
         Sees lock exists, exits (skips this cycle)
         ↓
Agent 1: Checks weather for all gardens
         Writes to database
         Deletes lock
Agent 2: Next cycle: "Let me get the weather-check lock..."
         Gets it now. Repeats.
```

**Analogy**:
> Imagine you and your friend both need to water your shared garden. You'd be chaotic if you both grabbed the watering can at the same time. Instead, you use a sign: "Someone is watering." When your friend sees the sign, they wait. When you finish, you remove the sign. Only one person waters at a time.

---

### 5.3 How Microservices Communicate

**The Backend ↔ PostgreSQL Communication**

**What Happens When You Create a Garden**:
```
1. Browser sends: POST /api/v1/gardens
                  { "name": "Backyard", "lat": 40.7, "lon": -74.0 }
                  ↓
2. Traefik routes to backend:8000
                  ↓
3. FastAPI backend receives request
   - Validates input (Pydantic schema)
   - Generates UUID for garden
   - Creates SQLAlchemy model object
                  ↓
4. Backend opens connection to PostgreSQL
   "INSERT INTO gardens (id, name, user_id, latitude, longitude, location, created_at)
    VALUES ('uuid', 'Backyard', 'user-uuid', 40.7, -74.0, POINT(40.7, -74.0), NOW())"
                  ↓
5. PostgreSQL processes:
   - PostGIS converts lat/lon to POINT geometry
   - Inserts record
   - Fires trigger to set updated_at timestamp
   - Returns success
                  ↓
6. Backend receives confirmation
   - Returns garden object to frontend
                  ↓
7. Browser receives JSON response
   - Displays new garden in UI
```

**The Backend ↔ Agent Communication (via Database)**

Agents don't call the backend directly. They both access the same database:

```
Agent gets list of all gardens:
  "SELECT * FROM gardens"
  ↓
For each garden, fetch weather:
  "INSERT INTO weather (garden_id, temperature, humidity, ...)"
  ↓
Frontend can now query latest weather:
  "SELECT * FROM weather WHERE garden_id = 'X' ORDER BY recorded_at DESC LIMIT 10"
```

**Async vs Blocking**:
```
❌ Blocking (slow):
   Backend waits for Postgres response before continuing
   Browser has to wait

✅ Async/Await (fast):
   Backend starts query, does other work while waiting
   Handles multiple requests simultaneously
   Browser gets response immediately
```

---

### 5.4 PostgreSQL + PostGIS for Geolocation

**What is PostGIS?**

PostgreSQL alone is good at storing data. PostGIS is an extension that adds geographic data types and functions.

**Without PostGIS** (storing coordinates as separate columns):
```sql
CREATE TABLE gardens (
  id UUID,
  name VARCHAR,
  latitude FLOAT,
  longitude FLOAT
);

-- Find gardens near me (DIFFICULT)
SELECT * FROM gardens
WHERE latitude > 40.7 AND latitude < 40.8
  AND longitude > -74.0 AND longitude < -73.9;
-- This is approximate and slow
```

**With PostGIS** (storing as geometry):
```sql
CREATE TABLE gardens (
  id UUID,
  name VARCHAR,
  location POINT  -- This is a PostGIS geometry type
);

-- Find gardens within 10km of me (EASY)
SELECT * FROM gardens
WHERE ST_Distance(location, ST_Point(40.7, -74.0)::geography) < 10000;
-- Fast and accurate
```

**On-Screen Demo**:
```bash
docker exec greenthumb-postgres psql -U greenthumb -d greenthumb

-- Show how coordinates are stored
SELECT name, ST_AsText(location) FROM gardens;
-- Output: Backyard Garden | POINT(40.7 -74.0)

-- Show geospatial query
SELECT
  name,
  ST_Distance(location, ST_Point(40.7, -74.0)::geography) / 1000 AS km_away
FROM gardens
ORDER BY ST_Distance(location, ST_Point(40.7, -74.0)::geography);
```

**Why This Matters for GreenThumb**:
> Future feature: "Find gardens with similar weather conditions nearby." PostGIS makes this efficient. Without it, you'd have to fetch all gardens, calculate distances in Python (slow), then filter.

---

## 6. RECOMMENDED TUTORIAL STRUCTURE

### Episode 1: Prerequisites & Architecture (25 minutes)

**Segment 1: Welcome & Agenda (2 min)**
- What you'll learn
- What you'll build
- Prerequisites

**Segment 2: System Architecture (8 min)**
- Draw the diagram (build it live)
- Introduce each component
- Explain why Traefik is needed
- Explain Agent/API split
- Explain Docker networking

**Segment 3: Prerequisites Deep Dive (10 min)**
- Proxmox container basics
- Docker & Docker Compose basics
- DNS configuration
- Required knowledge
- Verification commands (show live)

**Segment 4: Project Walkthrough (5 min)**
- Show directory structure
- Show docker-compose.yml
- Preview what will run where

---

### Episode 2: Deployment & Service Walkthrough (35 minutes)

**Segment 1: Environment Setup (5 min)**
- Clone repository
- Copy .env.example → .env
- Explain each variable
- Show what NOT to commit to git

**Segment 2: Starting Services (5 min)**
- Run `docker compose up`
- Narrate startup sequence
- Explain healthchecks
- Show all services running: `docker ps`

**Segment 3: Traefik Dashboard (5 min)**
- Navigate to traefik.green.lab
- Explain Routers section
- Explain Services section
- Live request trace

**Segment 4: Testing Frontend (8 min)**
- Navigate to green.lab
- Create account
- Create garden
- Add plants
- Show frontend working

**Segment 5: Testing Backend API (7 min)**
- Navigate to api.green.lab/docs (Swagger UI)
- Show endpoints
- Test registration/login
- Copy JWT token
- Test a protected endpoint

**Segment 6: Database & PostGIS (5 min)**
- Access database: `docker exec -it greenthumb-postgres psql`
- Show tables
- Show garden with PostGIS location
- Explain POINT data type

---

### Episode 3: Configuration, Monitoring & Troubleshooting (25-30 minutes)

**Segment 1: Agent & Redis (5 min)**
- Explain how agent works
- Show Redis lock mechanism
- Watch weather collection live
- Show agent logs: `docker logs -f greenthumb-agent`

**Segment 2: Structured Logging & Monitoring (5 min)**
- Show JSON logs
- Filter logs with jq
- Explain metrics available
- Show Traefik request latency

**Segment 3: Common Mistakes (8 min)**
- DNS resolution issues
- Port conflicts
- Environment variable mistakes
- How to diagnose with curl/docker commands

**Segment 4: Troubleshooting Scenarios (7 min)**
- Simulate service failure
- Show how to find root cause
- Show recovery steps
- Explain how to read error messages

**Segment 5: Next Steps (Optional, 5 min)**
- Enable HTTPS with Let's Encrypt
- Scaling horizontally (multiple API instances)
- Backup/restore procedure
- Future enhancements

---

## 7. SUCCESS CHECKPOINTS: Verification Steps

After each major milestone, viewers should verify everything works:

### Checkpoint 1: Docker & Docker Compose Working
**What to verify**:
```bash
docker --version        # ✓ Shows 24.0+
docker compose version  # ✓ Shows 2.20+
docker ps -a           # ✓ Empty (no containers yet)
```

**Explanation**: "If any of these fail, Docker isn't installed correctly. Don't proceed."

---

### Checkpoint 2: Project Cloned & .env Ready
**What to verify**:
```bash
ls -la | grep docker-compose.yml  # ✓ File exists
ls -la | grep .env                # ✓ File exists
grep "POSTGRES_HOST=postgres" .env # ✓ Correct host
```

**Explanation**: "Before we start containers, we need the compose file and environment variables."

---

### Checkpoint 3: Services Starting
**What to verify**:
```bash
docker ps  # ✓ All 6 containers shown with status "Up"
# traefik, postgres, redis, backend, agent, frontend

docker ps --filter "status=exited"  # ✓ Should be empty (no failed containers)
```

**Explanation**: "All services must be running. If any show 'Exited', we have an issue to fix."

---

### Checkpoint 4: Services Healthy
**What to verify**:
```bash
docker ps  # ✓ Status column shows "(healthy)" for postgres, backend

docker compose ps  # ✓ All services show "running"
```

**Explanation**: "Healthy means the service passed its healthcheck. Database and API must be healthy before moving on."

---

### Checkpoint 5: Frontend Loads
**What to verify**:
```bash
# Add to /etc/hosts:
192.168.1.100 green.lab

# Then visit in browser:
http://green.lab  # ✓ Should show login page
```

**Browser Console**:
- [ ] No red errors in JavaScript console
- [ ] Network tab shows successful requests to /api/v1/*
- [ ] No CORS errors

**Explanation**: "The frontend is served. If you see CORS errors, the API domain might be wrong."

---

### Checkpoint 6: API Documentation Works
**What to verify**:
```bash
# Also add to /etc/hosts:
192.168.1.100 api.green.lab

# Visit:
http://api.green.lab/docs  # ✓ Should show Swagger UI
```

**In Swagger UI**:
- [ ] All endpoints listed
- [ ] Can expand endpoints to see schema
- [ ] No error responses

**Explanation**: "If Swagger doesn't load, Traefik routing to the backend isn't working."

---

### Checkpoint 7: Can Register & Login
**What to verify**:
```bash
# In Swagger UI:
1. Click "POST /auth/register"
2. Click "Try it out"
3. Enter: {"email":"test@example.com","password":"test123","full_name":"Test User"}
4. Click "Execute"
5. Status 201 Created ✓
```

**Explanation**: "Registration tests the entire stack: frontend → Traefik → backend → database."

---

### Checkpoint 8: Agent is Running
**What to verify**:
```bash
docker logs greenthumb-agent | tail -20  # ✓ Shows recent activity

# Wait for next scheduled weather check (every 15 minutes)
# Or check logs for "weather_check_job started"
docker logs -f greenthumb-agent | grep "weather_check"  # ✓ Shows weather collection
```

**Explanation**: "Agent runs silently in the background. Check logs to verify it's working."

---

### Checkpoint 9: Can Create Garden & See Weather
**What to verify**:
```bash
# In browser (green.lab):
1. Log in
2. Click "Create Your First Garden"
3. Enter: name="Test Garden", lat=40.7128, lon=-74.0060
4. Submit ✓

# Wait 15+ minutes or check Redis:
docker exec greenthumb-redis redis-cli KEYS "*weather*"  # ✓ Weather data present

# Check weather in UI ✓
```

**Explanation**: "This tests the entire flow: user input → API → database → agent → database → API → UI."

---

## 8. TROUBLESHOOTING WALKTHROUGH: Live Demonstrations

### Scenario 1: "Services Won't Start"

**Setup**: Intentionally corrupt docker-compose.yml (change syntax)

**On-Screen Demo**:
```bash
# Try to start
docker compose up

# Error: "yaml: line 25: mapping values are not allowed in this context"

# Root cause: Syntax error in docker-compose.yml
nano docker-compose.yml  # Fix the line

# Try again
docker compose up  # ✓ Works

# Lesson: "Always validate YAML syntax first"
docker compose config  # Validates without starting
```

---

### Scenario 2: "Port 80 Already in Use"

**Setup**: Start another service on port 80 first

**On-Screen Demo**:
```bash
# Simulate another service
docker run -d -p 80:80 nginx:latest

# Try to start GreenThumb
docker compose up

# Error: "Address already in use"

# Diagnose
sudo lsof -i :80  # Shows nginx is using it

# Fix option 1: Stop the other service
docker stop <container-id>

# Try again ✓
```

---

### Scenario 3: "Backend Can't Connect to Database"

**Setup**: Backend service starts before Postgres is ready

**On-Screen Demo**:
```bash
# Look at logs
docker logs greenthumb-backend

# Error: "could not connect to server: Connection refused"

# Why? The depends_on isn't working?
# Or Postgres is up but not healthy?

# Check Postgres status
docker ps | grep postgres

# If status doesn't show "healthy", Postgres still initializing

# Check Postgres logs
docker logs greenthumb-postgres

# Wait for "database system is ready to accept connections"

# Then backend reconnects automatically (or restart it)
docker compose restart backend

# ✓ Now connected
```

---

### Scenario 4: "Frontend Can't Reach API"

**Setup**: Wrong `NEXT_PUBLIC_API_URL` in .env

**On-Screen Demo**:
```bash
# User reports: "Buttons don't work, I see network errors"

# Step 1: Check browser console (F12 → Network)
# See: POST http://localhost:8000/api/v1/gardens → FAILED (CORS error)

# Step 2: This tells us the API URL is wrong

# Step 3: Check .env
grep NEXT_PUBLIC_API_URL .env
# Output: NEXT_PUBLIC_API_URL=http://localhost:8000

# Wrong! Should be:
# NEXT_PUBLIC_API_URL=http://api.green.lab

# Step 4: Fix and rebuild
nano .env
docker compose build frontend
docker compose up frontend

# ✓ Now API calls work
```

---

### Scenario 5: "Agent Not Collecting Weather"

**Setup**: Stop Redis or set wrong Redis password

**On-Screen Demo**:
```bash
# Check agent logs
docker logs greenthumb-agent

# Error: "Could not connect to Redis at redis:6379: Connection refused"

# Step 1: Is Redis running?
docker ps | grep redis  # Not running!

# Step 2: Why?
docker logs greenthumb-redis  # Check error logs

# Step 3: Restart Redis
docker compose up redis

# Step 4: Restart agent
docker compose restart agent

# ✓ Agent can now use Redis lock

# Or if password wrong:
docker logs greenthumb-agent | grep "password"

# Fix in .env
nano .env  # Correct REDIS_PASSWORD
docker compose up  # Restart with new password
```

---

## Final Notes for Video Production

### Pacing
- **Go slow on complex concepts** (Traefik, Redis locking, PostGIS)
- **Quick through repetitive steps** (docker commands, scrolling)
- **Pause for Q&A** at checkpoints

### Visual Aids
- **Use different terminal colors** for output
- **Highlight important lines** with text overlays
- **Draw diagrams** with screen drawing tool
- **Browser DevTools** open for API/frontend debugging

### Voice & Tone
- **Enthusiastic** — You believe GreenThumb is cool
- **Patient** — This is complex, viewers might be lost
- **Practical** — Always show what to do if things break
- **Curious** — "Let's check the logs to see what's happening"

### Resources to Link
- Docker docs: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- Traefik docs: https://doc.traefik.io/
- PostgreSQL PostGIS: https://postgis.net/
- FastAPI: https://fastapi.tiangolo.com/
- Proxmox: https://www.proxmox.com/

---

**Total Estimated Watch Time**: 60-90 minutes (3 episodes)

**Total Estimated Learning Time**: 2-3 hours (viewers will pause, re-watch, and test locally)

**Success Metric**: Viewers can deploy GreenThumb on their Proxmox lab, create a garden, and see weather data collected automatically.
