# GreenThumb YouTube Tutorial - Visual Explanation Guide

This document provides ASCII diagrams and visual descriptions for on-screen demonstrations and graphics.

---

## 1. CONTAINER NETWORKING VISUAL

### What to Show on Screen

**Diagram 1: Without Traefik (Chaos)**
```
Your Computer                    Proxmox VM
┌─────────────────┐              ┌──────────────────────────┐
│                 │              │                          │
│ Browser         │              │  Frontend (port 3000)    │
│  ❌ Can't reach │──────────X──→│  Backend (port 8000)     │
│  :3000 or :8000 │              │  Postgres (port 5432)    │
│  (confusing!)   │              │  Redis (port 6379)       │
│                 │              │  Agent (no port)         │
└─────────────────┘              └──────────────────────────┘

Problem: Hard to remember which port is which
         Hard to expose multiple services
         Port conflicts
```

**Diagram 2: With Traefik (Order)**
```
Your Computer                              Proxmox VM
┌──────────────────────────┐              ┌────────────────────────────────────┐
│                          │              │  ┌──────────────────────────────┐  │
│  http://green.lab  ───────────port 80──→│  │      Traefik (Port 80)      │  │
│  http://api.green.lab ───────port 80──→│  │                              │  │
│  http://traefik.green.lab ─port 80──→│  │  Routes based on hostname:  │  │
│                          │              │  │ green.lab → frontend:3000   │  │
└──────────────────────────┘              │  │ api.green.lab → backend:8000│  │
                                          │  │ traefik.green.lab → api:8080│  │
                                          │  └──────────────────────────────┘  │
                                          │                                      │
                                          │  ┌──────────────────────────────┐  │
                                          │  │  greenthumb Docker Network   │  │
                                          │  │  (172.18.0.0/16)            │  │
                                          │  │                              │  │
                                          │  │  Frontend:3000     ──────┐   │  │
                                          │  │  Backend:8000      ───┐  │   │  │
                                          │  │  Postgres:5432     ─┐ │  │   │  │
                                          │  │  Redis:6379        │ │  │   │  │
                                          │  │  Agent:worker      │ │  │   │  │
                                          │  │  (all connected via │ │  │   │  │
                                          │  │   internal DNS)    │ │  │   │  │
                                          │  │                    │ │  │   │  │
                                          │  └────────────────────┼─┼──┼───┘  │
                                          │                       └─┴──┘       │
                                          └────────────────────────────────────┘

Solution: One port (80), multiple hostnames
         Easy to remember
         No port conflicts
         Professional setup
```

### Animation Idea
Show a request flowing through Traefik:
1. Browser sends request to port 80 with `Host: api.green.lab`
2. Traefik checks routing rules
3. Rule matches: Host = api.green.lab
4. Forward to backend:8000
5. Response flows back

---

## 2. DATABASE COMMUNICATION FLOW

### Visual: How Data Gets Stored

```
┌─────────────────┐
│  User fills     │
│  garden form    │
│  green.lab      │
└────────┬────────┘
         │
         │ POST /api/v1/gardens
         │ { name: "Backyard", lat: 40.7, lon: -74.0 }
         ↓
┌─────────────────────────────────────────────┐
│          Traefik (Port 80)                   │
│                                              │
│  Sees: Host: green.lab                       │
│  Routes to: backend:8000                     │
└────────┬────────────────────────────────────┘
         │
         │ (internal Docker network)
         ↓
┌─────────────────────────────────────────────┐
│     FastAPI Backend (Container)              │
│                                              │
│  1. Validate input (Pydantic)                │
│  2. Check user owns this garden              │
│  3. Generate UUID for garden                 │
│  4. Create INSERT statement                  │
│  5. Open connection to postgres:5432         │
└────────┬────────────────────────────────────┘
         │
         │ INSERT INTO gardens (...) VALUES (...)
         │ Hostname: postgres (Docker DNS)
         │ Port: 5432
         ↓
┌─────────────────────────────────────────────┐
│   PostgreSQL Container                       │
│                                              │
│  1. Receive INSERT from backend              │
│  2. Convert lat/lon to POINT(40.7, -74.0)    │
│  3. Generate updated_at timestamp            │
│  4. Write to disk (in data/db volume)        │
│  5. Return: "INSERT OK, 1 row affected"      │
└────────┬────────────────────────────────────┘
         │
         │ Response: { id, name, coordinates, created_at }
         ↓
┌─────────────────────────────────────────────┐
│    FastAPI Backend                           │
│                                              │
│  Convert database row to JSON                │
│  Return to frontend                          │
└────────┬────────────────────────────────────┘
         │
         │ 200 OK
         │ Content-Type: application/json
         │ { garden object }
         ↓
┌─────────────────────────────────────────────┐
│   Browser (green.lab)                        │
│                                              │
│  Receive JSON response                       │
│  Update UI: "Backyard garden added!"         │
│  Show new garden in list                     │
└─────────────────────────────────────────────┘
```

### Timing Annotation
Add text overlay:
- Browser to Traefik: ~1ms
- Traefik routing: ~0.5ms
- Backend processing: ~5-10ms
- Database write: ~2-5ms
- **Total: ~10-20ms** (feels instant to user)

---

## 3. AGENT & REDIS LOCKING SEQUENCE

### Visual: Automatic Weather Collection

```
                          EVERY 15 MINUTES
                                │
                                ↓
                    ┌───────────────────────┐
                    │   APScheduler Triggers │
                    │   weather_check_job() │
                    └───────────┬───────────┘
                                │
                    ┌───────────↓───────────┐
                    │  Try to get Redis Lock│
                    └───────────┬───────────┘
                                │
                    ┌───────────↓───────────┐
                    │  Lock exists? (Check) │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
              │ YES                               │ NO
              ↓                                   ↓
      ┌───────────────┐                 ┌─────────────────────┐
      │ Another agent │                 │ GET the lock        │
      │ is working    │                 │ (set timeout: 5 min)│
      │               │                 └──────────┬──────────┘
      │ Skip this     │                           │
      │ cycle         │                           ↓
      └───────────────┘        ┌──────────────────────────────┐
              │                 │ Query all gardens from DB    │
              │                 │ SELECT * FROM gardens;       │
              │                 └──────────────┬───────────────┘
              │                                │
              │                    ┌───────────↓───────────┐
              │                    │ For each garden:      │
              │                    │ GET weather from      │
              │                    │ Open-Meteo API        │
              │                    │ ~2-5 seconds per call │
              │                    └───────────┬───────────┘
              │                                │
              │                    ┌───────────↓───────────┐
              │                    │ INSERT weather record │
              │                    │ into database         │
              │                    └───────────┬───────────┘
              │                                │
              │                    ┌───────────↓───────────┐
              │                    │ Log success (JSON)    │
              │                    │ {                     │
              │                    │   "garden": "Backyard"│
              │                    │   "temp": 25,         │
              │                    │   "humidity": 65      │
              │                    │ }                     │
              │                    └───────────┬───────────┘
              │                                │
              │                    ┌───────────↓───────────┐
              │                    │ DELETE Redis lock     │
              │                    │ (job complete)        │
              │                    └───────────┬───────────┘
              │                                │
              └────────────────────────────────┘
                                 │
                                 ↓
                        (Job complete)
                        Next cycle in 15 min
```

### Key Annotations
- **Lock acquisition**: "Prevents duplicate runs if multiple agents exist"
- **Each garden**: "Shown so viewers understand it fetches weather for ALL gardens"
- **Timeout 5 min**: "If agent crashes, lock automatically releases (prevents deadlock)"
- **Log format**: "These are structured JSON logs—easy to parse and monitor"

---

## 4. POSTGIS COORDINATES EXPLANATION

### Visual: How Coordinates Become Data

```
Real-World Example: Central Park, New York

┌──────────────────┐     ┌──────────────────┐
│  User Input      │     │  Database Storage│
│                  │     │                  │
│  Latitude:  40.7 │────→│  POINT(40.7 -74) │
│  Longitude: -74  │     │                  │
└──────────────────┘     └────────┬─────────┘
                                  │
                        ┌─────────↓─────────┐
                        │  PostGIS converts │
                        │  to geography     │
                        │  (Earth coords)   │
                        └─────────┬─────────┘
                                  │
                    ┌─────────────↓─────────────┐
                    │  Can now answer questions:│
                    │                           │
                    │  Q: Gardens near me?      │
                    │  SELECT * FROM gardens    │
                    │  WHERE ST_Distance(       │
                    │    location,              │
                    │    ST_Point(40.7,-74)     │
                    │  ) < 10000;               │
                    │                           │
                    │  (Find within 10km)       │
                    └───────────────────────────┘
```

### Animation for Video
1. Show a map of Central Park
2. Mark the coordinates (40.7, -74.0)
3. Draw a circle: "10km radius"
4. Show SQL query finding gardens in that circle
5. Explain: "This would be impossible without PostGIS"

---

## 5. DOCKER COMPOSE STARTUP SEQUENCE

### Visual: What Happens When You Run `docker compose up`

```
$ docker compose up

[1] Reading docker-compose.yml
    ├─ Found 6 services
    ├─ Found volumes: db, redis
    ├─ Found network: greenthumb
    └─ Validating syntax... ✓

[2] Building images (first time only)
    ├─ Building backend from Dockerfile
    │  ├─ FROM python:3.11-slim
    │  ├─ RUN apt-get install ... (GIS libraries)
    │  ├─ COPY requirements.txt
    │  ├─ RUN pip install -r requirements.txt
    │  └─ Layer size: 850MB
    │
    ├─ Building frontend from Dockerfile
    │  ├─ Stage 1: deps (npm ci)
    │  ├─ Stage 2: builder (npm run build)
    │  ├─ Stage 3: runner (cleanup)
    │  └─ Layer size: 290MB
    │
    └─ Building agent from Dockerfile
       ├─ FROM python:3.11-slim
       ├─ RUN pip install -r requirements.txt
       └─ Layer size: 450MB

[3] Creating Docker network
    └─ greenthumb (bridge driver)

[4] Creating volumes
    ├─ data/db (PostgreSQL data)
    └─ data/redis (Redis data)

[5] Starting containers (in dependency order)
    ├─ greenthumb-traefik
    │  ├─ Status: starting...
    │  ├─ Waiting for port 80 to bind
    │  └─ Status: running
    │
    ├─ greenthumb-postgres
    │  ├─ Status: starting...
    │  ├─ Running init-db.sql (create tables, PostGIS)
    │  ├─ Status: running
    │  ├─ Healthcheck: pg_isready
    │  └─ Status: healthy ✓
    │
    ├─ greenthumb-redis
    │  ├─ Status: starting...
    │  ├─ Redis listening on 6379
    │  ├─ Healthcheck: redis-cli PING
    │  └─ Status: healthy ✓
    │
    ├─ greenthumb-backend
    │  ├─ Status: starting... (waiting for postgres healthy)
    │  ├─ Uvicorn server on 8000
    │  ├─ Healthcheck: GET /health
    │  ├─ Status: running
    │  ├─ Status: healthy ✓
    │  │
    │  └─ Traefik reads labels:
    │     ├─ "traefik.enable=true"
    │     ├─ "traefik.http.routers.backend.rule=Host(`api.green.lab`)"
    │     ├─ "traefik.http.services.backend.loadbalancer.server.port=8000"
    │     └─ Traefik updates routing ✓
    │
    ├─ greenthumb-agent
    │  ├─ Status: starting... (waiting for postgres healthy)
    │  ├─ APScheduler initialized
    │  ├─ First job runs in 15 minutes
    │  └─ Status: running
    │
    └─ greenthumb-frontend
       ├─ Status: starting...
       ├─ Next.js server on 3000
       ├─ Status: running
       │
       └─ Traefik reads labels:
          ├─ "traefik.enable=true"
          ├─ "traefik.http.routers.frontend.rule=Host(`green.lab`)"
          ├─ "traefik.http.services.frontend.loadbalancer.server.port=3000"
          └─ Traefik updates routing ✓

[6] Final Status
    ┌──────────────────────────────────────┐
    │  Name                   Status       │
    ├──────────────────────────────────────┤
    │  greenthumb-traefik      Up (healthy) │
    │  greenthumb-postgres     Up (healthy) │
    │  greenthumb-redis        Up (healthy) │
    │  greenthumb-backend      Up (healthy) │
    │  greenthumb-agent        Up           │
    │  greenthumb-frontend     Up           │
    └──────────────────────────────────────┘

    All services ready! ✓

[7] Traefik Summary
    ✓ green.lab → frontend:3000
    ✓ api.green.lab → backend:8000
    ✓ traefik.green.lab → api@internal:8080
```

### On-Screen Timing
Narrate this while the output scrolls:
- **Seconds 0-5**: "Building images..."
- **Seconds 5-15**: "Docker is downloading base images and installing dependencies"
- **Seconds 15-30**: "Creating containers and starting them in order"
- **Seconds 30-45**: "Each service is running its healthcheck to confirm it's ready"
- **Seconds 45-60**: "All services up! Traefik has discovered all of them"

---

## 6. AUTHENTICATION FLOW DIAGRAM

### Visual: Registration → Login → Protected Request

```
STEP 1: Registration
┌──────────────┐
│ User enters  │
│ email & pwd  │
└──────┬───────┘
       │
       │ POST /api/v1/auth/register
       │ Content-Type: application/json
       │ {
       │   "email": "user@example.com",
       │   "password": "secure123",
       │   "full_name": "John Doe"
       │ }
       ↓
┌──────────────────────────────────┐
│  FastAPI Backend                 │
│                                  │
│  1. Validate with Pydantic       │
│  2. Check email not taken        │
│  3. Hash password with bcrypt    │
│  4. INSERT user into database    │
│  5. Return 201 Created           │
└──────┬───────────────────────────┘
       │
       │ Response:
       │ {
       │   "id": "uuid...",
       │   "email": "user@example.com",
       │   "full_name": "John Doe",
       │   "is_active": true
       │ }
       ↓
┌──────────────────────────────────┐
│ Browser                          │
│ Show: "Account created! Login"   │
└──────┬───────────────────────────┘


STEP 2: Login
┌──────────────┐
│ User enters  │
│ email & pwd  │
└──────┬───────┘
       │
       │ POST /api/v1/auth/login
       │ Content-Type: application/x-www-form-urlencoded
       │ username=user@example.com&password=secure123
       ↓
┌──────────────────────────────────┐
│  FastAPI Backend                 │
│                                  │
│  1. Query user by email          │
│  2. bcrypt.verify(password, hash)│
│  3. Generate JWT token           │
│     Payload:                     │
│     {                            │
│       "sub": "uuid...",          │
│       "exp": now + 24h           │
│     }                            │
│  4. Sign with SECRET_KEY         │
│     using HS256                  │
└──────┬───────────────────────────┘
       │
       │ Response:
       │ {
       │   "access_token": "eyJhbGc...",
       │   "token_type": "bearer"
       │ }
       ↓
┌──────────────────────────────────┐
│ Browser                          │
│                                  │
│ 1. Store token in localStorage   │
│ 2. Redirect to dashboard         │
│ 3. Ready for authenticated calls │
└──────┬───────────────────────────┘


STEP 3: Protected Request
┌──────────────────────────────────┐
│ User clicks "My Gardens"         │
│ Frontend needs to fetch gardens  │
└──────┬───────────────────────────┘
       │
       │ GET /api/v1/gardens
       │ Header: Authorization: Bearer eyJhbGc...
       ↓
┌──────────────────────────────────┐
│  FastAPI Backend                 │
│                                  │
│  1. Middleware reads JWT header  │
│  2. Verify signature with SECRET │
│  3. Check expiration             │
│  4. Extract user_id from payload │
│  5. Query only THIS user's data  │
│                                  │
│  SELECT * FROM gardens           │
│  WHERE user_id = 'uuid...'       │
└──────┬───────────────────────────┘
       │
       │ Database returns:
       │ [
       │   {
       │     "id": "garden-uuid",
       │     "name": "Backyard",
       │     "location": "POINT(...)",
       │     "created_at": "2024-01-15T..."
       │   }
       │ ]
       ↓
┌──────────────────────────────────┐
│ Browser                          │
│ Display: "Backyard Garden"       │
└──────────────────────────────────┘
```

### Key Teaching Points
- **Bcrypt**: "Password is hashed, never stored in plain text"
- **JWT**: "Token is signed, can't be forged. Contains user info, expires after 24h"
- **Authorization**: "Backend checks user owns the garden before returning data"

---

## 7. ERROR SCENARIOS & SOLUTIONS (Visual Flowchart)

### Decision Tree: "Services Won't Start?"

```
         Services won't start
                 │
         ┌───────┴───────┐
         │               │
      Check logs     Check syntax
         │               │
         ↓               ↓
    What error?    docker compose config
         │
    ┌────┼────┬─────────┬────────────┬──────────────┐
    │    │    │         │            │              │
  Port  Conn  DB      Image      Syntax            Perm
  Used  Refused Init  Pull       Error             Issue
    │    │    │         │            │              │
    ↓    ↓    ↓         ↓            ↓              ↓
   lsof pg_ready rm -rf docker logs fix yaml  chmod -R
   kill  logs    data pull  rebuild   syntax    1000
                                               ownership
```

### DNS Not Working? (Flowchart)

```
         "green.lab not found"
                 │
        ┌────────┴────────┐
        │                 │
    Check /etc/hosts   Check DNS
        │                 │
    Entry exist?      Resolver ok?
        │                 │
    ┌───┴──┐          ┌───┴──┐
    │      │          │      │
   NO     YES        NO     YES
    │      │          │      │
    │      ├─→ IP ok? └─→ nslookup
    │      │     │          │
    │      │   NO→ Fix IP   Check firewall
    │      │     │
    Add entry   YES
              OK!
```

---

## 8. COLOR-CODED TERMINAL OUTPUT

### How to Highlight in Editing

**Backend Startup Logs** (color code):
```
[INFO]     green text      - Service started successfully
[ERROR]    red text        - Something failed
[WARNING]  yellow text     - Might be an issue
[DEBUG]    cyan text       - Detailed info
```

**Show in terminal with overlays**:
- `2024-01-15 10:45:23` [BLUE] — Timestamp
- `greenthumb-backend` [GREEN] — Container name
- `GET /api/v1/health` [CYAN] — Request
- `200` [GREEN] — Success code
- `4.2ms` [YELLOW] — Response time

---

## 9. TRAEFIK DASHBOARD ANNOTATIONS

### What to Point to on Screen

```
Traefik Dashboard: http://traefik.green.lab

Top Bar:
┌──────────────────────────────────────────────┐
│ HTTP   | TCP  | UDP |   Features Button     │
│ 3 →    │ --   | --  │ (less important)      │
│ routers│      │     │                       │
└──────────────────────────────────────────────┘

Left Side: Routers
┌──────────────────────────────────────┐
│ frontend                             │ ← Points to frontend:3000
│ ├─ Rule: Host(`green.lab`)           │   Serves web UI
│ ├─ Entry Point: web (port 80)        │
│ ├─ Status: UP ✓                      │
│                                      │
│ backend                              │ ← Points to backend:8000
│ ├─ Rule: Host(`api.green.lab`)       │   Serves REST API
│ ├─ Entry Point: web (port 80)        │
│ ├─ Status: UP ✓                      │
│                                      │
│ traefik                              │ ← Points to traefik:8080
│ ├─ Rule: Host(`traefik.green.lab`)   │   Serves this dashboard
│ ├─ Entry Point: web (port 80)        │
│ ├─ Status: UP ✓                      │
└──────────────────────────────────────┘

Right Side: Services
┌──────────────────────────────────────┐
│ frontend:3000                        │ ← Where requests go
│ ├─ Server: 172.18.0.5:3000           │   (internal Docker IP)
│ ├─ Status: UP ✓                      │
│ ├─ Avg Response Time: 12ms           │
│                                      │
│ backend:8000                         │ ← Where API requests go
│ ├─ Server: 172.18.0.4:8000           │
│ ├─ Status: UP ✓                      │
│ ├─ Avg Response Time: 8ms            │
│                                      │
│ api@internal (Traefik API)           │ ← Internal to Traefik
│ ├─ Server: 127.0.0.1:8080            │
│ ├─ Status: UP ✓                      │
└──────────────────────────────────────┘
```

---

## 10. COMMAND-LINE SCREENSHOTS

### Key Commands to Show (with Output)

**Show what successful `docker ps` looks like:**
```
$ docker ps

CONTAINER ID  IMAGE                      STATUS              PORTS
a1b2c3d4e5f6  traefik:v3.0              Up 2 minutes        0.0.0.0:80->80/tcp
b2c3d4e5f6a7  postgis/postgis:16-3.4    Up 2 minutes        (healthy)
c3d4e5f6a7b8  redis:7-alpine            Up 2 minutes        (healthy)
d4e5f6a7b8c9  greenthumb-backend        Up 2 minutes        (healthy)
e5f6a7b8c9d0  greenthumb-agent          Up 2 minutes
f6a7b8c9d0e1  greenthumb-frontend       Up 2 minutes
```

**Show a successful curl test:**
```
$ curl -v http://api.green.lab/health

> GET /health HTTP/1.1
> Host: api.green.lab
> User-Agent: curl/7.64.1

< HTTP/1.1 200 OK
< Content-Type: application/json
< Content-Length: 16

{"status":"ok"}
```

**Show database connection:**
```
$ docker exec -it greenthumb-postgres psql -U greenthumb -d greenthumb

greenthumb=# \dt
              List of relations
 Schema |       Name        | Type  |  Owner
--------+-------------------+-------+----------
 public | users             | table | greenthumb
 public | gardens           | table | greenthumb
 public | plants            | table | greenthumb
 public | weather           | table | greenthumb
(4 rows)

greenthumb=# SELECT name, ST_AsText(location) FROM gardens LIMIT 1;
      name       |        st_astext
-----------------+-------------------------
 Backyard Garden | POINT(-118.2437 34.0522)
(1 row)
```

---

## Screen Recording Tips

### Recording Setup
- **Terminal**: Use large font (18pt minimum)
- **Background**: Dark theme (Dracula or Nord)
- **Width**: 120 columns, 40 rows (for readability)
- **Cursor**: Make it visible (white, larger)

### Visual Pacing
- **Slow**: Type commands and explain
- **Fast**: Scroll through log output
- **Pause**: 2-3 seconds when something important appears
- **Repeat**: Show same command twice if critical

### Add Visual Effects
- **Arrow overlays**: Point to important lines
- **Highlight boxes**: Circle key values
- **Text callouts**: Annotate what you're seeing
- **Timer**: Show how long operations take

---

**These visuals should be implemented in editing software (Adobe Premiere, Final Cut Pro, DaVinci Resolve) or simpler tools (ScreenFlow, OBS).**

