# GreenThumb Architecture

This document explains the system architecture, design decisions, and data flow.

## Table of Contents

- [System Overview](#system-overview)
- [Service Architecture](#service-architecture)
- [Agent/API Split](#agentapi-split)
- [Data Flow](#data-flow)
- [Technology Choices](#technology-choices)
- [Security Model](#security-model)
- [Scaling Considerations](#scaling-considerations)

## System Overview

GreenThumb is a microservices-based application designed for self-hosting on Proxmox. The system consists of six containerized services orchestrated by Docker Compose.

```
┌─────────────────────────────────────────────────────────────┐
│                         Traefik v3                          │
│                    (Reverse Proxy)                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  green.lab   │  │ api.green.lab│  │traefik.green │    │
│  │              │  │              │  │    .lab      │    │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘    │
└─────────┼──────────────────┼──────────────────────────────┘
          │                  │
          │                  │
┌─────────▼─────────┐ ┌─────▼─────────┐
│    Frontend       │ │   Backend API  │
│   (Next.js 14)    │ │   (FastAPI)    │
│                   │ │                │
│  - React UI       │ │  - REST API    │
│  - TypeScript     │ │  - JWT Auth    │
│  - Tailwind CSS   │ │  - Pydantic    │
└───────────────────┘ └────────┬───────┘
                               │
                               │ Async SQLAlchemy
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
    ┌─────▼─────┐      ┌──────▼──────┐     ┌──────▼──────┐
    │ PostgreSQL│      │    Redis    │     │    Agent    │
    │   +PostGIS│      │             │     │  (Worker)   │
    │           │      │  - Caching  │     │             │
    │  - Users  │      │  - Locking  │     │ -APScheduler│
    │  - Gardens│      └─────────────┘     │ - Weather   │
    │  - Plants │                          │ - Seed DB   │
    │  - Weather│                          └─────────────┘
    └───────────┘
```

## Service Architecture

### 1. Traefik (Reverse Proxy)

**Purpose**: Edge router that dynamically routes HTTP traffic to services.

**Key Features**:
- Automatic service discovery via Docker labels
- HTTP to HTTPS redirect (when enabled)
- Let's Encrypt certificate management
- Dashboard for monitoring
- Health checks

**Why Traefik?**:
- Docker-native configuration (no manual config files)
- Automatic SSL certificate renewal
- Built-in dashboard and metrics
- Popular in home lab setups

**Routing Rules**:
```
green.lab          → frontend:3000
api.green.lab      → backend:8000
traefik.green.lab  → traefik:8080 (dashboard)
```

### 2. Frontend (Next.js 14)

**Purpose**: User-facing web interface.

**Tech Stack**:
- Next.js 14+ (App Router)
- TypeScript (strict mode)
- Tailwind CSS + Shadcn/UI
- Axios for API calls

**Key Features**:
- Server-side rendering (SSR) for SEO
- Static generation for performance
- Type-safe API client ([lib/api.ts](../frontend/lib/api.ts))
- Responsive design

**Why Next.js?**:
- Best-in-class React framework
- Excellent DX with App Router
- Built-in optimization (images, fonts, code splitting)
- TypeScript first-class support

### 3. Backend API (FastAPI)

**Purpose**: RESTful API for all business logic.

**Tech Stack**:
- FastAPI (async Python web framework)
- SQLAlchemy 2.0 (async ORM)
- Pydantic v2 (validation and serialization)
- JWT authentication (python-jose)
- Bcrypt password hashing

**Key Features**:
- Auto-generated OpenAPI docs at `/docs`
- Async database operations
- JWT bearer token authentication
- CORS middleware
- Structured JSON logging
- Health check endpoint

**Why FastAPI?**:
- Fastest Python web framework
- Automatic API documentation
- Type hints enable great IDE support
- Async/await for I/O-bound operations
- Pydantic validation prevents bad data

**API Structure**:
```
/api/v1/
  ├── /auth
  │   ├── POST /register
  │   ├── POST /login
  │   └── GET  /me
  ├── /gardens
  │   ├── GET    /          (list)
  │   ├── POST   /          (create)
  │   ├── GET    /{id}      (read)
  │   ├── PATCH  /{id}      (update)
  │   └── DELETE /{id}      (delete)
  ├── /plants
  │   ├── GET    /          (list)
  │   └── POST   /          (create)
  └── /weather
      └── GET    /{garden_id}
```

### 4. Agent (Autonomous Worker)

**Purpose**: Background tasks that run on a schedule.

**Tech Stack**:
- APScheduler (job scheduling)
- Redis (distributed locking)
- httpx (async HTTP client)
- SQLAlchemy (database access)

**Jobs**:
1. **Weather Check** (every 15 minutes):
   - Fetches weather data from Open-Meteo API
   - Stores data for all gardens
   - Uses Redis lock to prevent duplicate runs

2. **Seed Database Sync** (daily at 3 AM):
   - Updates plant data from OpenFoodFacts
   - Enriches seed database

**Why Separate Agent?**:
See [Agent/API Split](#agentapi-split) below.

### 5. PostgreSQL + PostGIS

**Purpose**: Persistent data storage with geospatial support.

**Configuration**:
- PostgreSQL 16
- PostGIS 3.4 for geographic queries
- uuid-ossp for UUID generation
- Automatic updated_at triggers

**Schema**:
```sql
users
  - id (UUID, PK)
  - email (unique, indexed)
  - hashed_password
  - full_name
  - is_active
  - created_at, updated_at

gardens
  - id (UUID, PK)
  - user_id (FK → users.id)
  - name
  - description
  - latitude, longitude
  - location (PostGIS POINT)
  - created_at, updated_at

plants
  - id (UUID, PK)
  - garden_id (FK → gardens.id)
  - name
  - scientific_name
  - variety
  - plant_date, harvest_date
  - notes
  - created_at, updated_at

weather
  - id (UUID, PK)
  - garden_id (FK → gardens.id)
  - temperature, humidity
  - precipitation, wind_speed
  - condition
  - recorded_at
  - created_at
```

**Why PostGIS?**:
- Enables geospatial queries (e.g., "gardens within 10km")
- Native support for latitude/longitude
- Industry standard for geographic data

### 6. Redis

**Purpose**: Caching and distributed locking.

**Use Cases**:
1. **Agent Task Locking**:
   - Prevents multiple agent instances from running same job
   - Lock timeout prevents deadlocks

2. **Future Use**:
   - API response caching
   - Session storage
   - Rate limiting

**Why Redis?**:
- Simple key-value store
- Built-in lock primitives
- Persistent AOF mode preserves data
- Minimal resource usage

## Agent/API Split

**Why is the Agent a separate service from the API?**

This is a key architectural decision. Here's the reasoning:

### 1. Separation of Concerns

The **API** handles:
- User requests (synchronous)
- Authentication
- CRUD operations
- Input validation

The **Agent** handles:
- Scheduled tasks (asynchronous)
- External API calls (weather, plant data)
- Long-running operations
- Data enrichment

Mixing these would make the API codebase harder to maintain.

### 2. Independent Scaling

- **API**: Scales horizontally based on user traffic
  - Can run 3+ replicas behind Traefik
  - Each request is stateless

- **Agent**: Single instance with distributed locking
  - Only needs to scale if jobs take too long
  - Redis lock ensures one worker runs each job

### 3. Fault Isolation

If the agent crashes (e.g., external API down):
- API continues serving users
- No impact on user experience

If API crashes:
- Agent continues collecting weather data
- Data is ready when API restarts

### 4. Different Lifecycles

- **API**: Requests complete in milliseconds
  - FastAPI uses async/await
  - Database queries are fast (<50ms)

- **Agent**: Jobs take seconds to minutes
  - Weather API calls: 1-5 seconds each
  - Multiple gardens: 30+ seconds total
  - Blocking the API would be unacceptable

### 5. Error Handling

**API Errors**: Return HTTP status codes
```python
raise HTTPException(status_code=404, detail="Garden not found")
```

**Agent Errors**: Log and continue
```python
try:
    fetch_weather(garden)
except Exception as e:
    logger.error(f"Weather fetch failed: {e}")
    # Continue with next garden - don't crash the loop
```

The agent **must never crash** because a single garden's weather fails. The try/except blocks prevent crash-loops.

### 6. Resource Usage

- **API**: Many small requests
  - Connection pooling (max 10 connections)
  - Quick release of database connections

- **Agent**: Few large requests
  - Long-lived database connection
  - Holds connections during job execution

## Data Flow

### User Registration Flow

```
1. User enters email/password in frontend
   ├─> POST /api/v1/auth/register
   │
2. Backend validates input (Pydantic schema)
   ├─> Check email not already registered
   ├─> Hash password with bcrypt
   ├─> Insert user into database
   │
3. Return user object (password excluded)
   └─> Frontend redirects to login
```

### Authentication Flow

```
1. User enters credentials
   ├─> POST /api/v1/auth/login (OAuth2 form)
   │
2. Backend verifies password
   ├─> Query user by email
   ├─> bcrypt.verify(password, hashed_password)
   │
3. Generate JWT token
   ├─> Payload: {"sub": user_id, "exp": now + 24h}
   ├─> Sign with SECRET_KEY
   │
4. Frontend stores token in localStorage
   ├─> Sets Authorization header for all requests
   └─> Header: "Bearer eyJ..."
```

### Garden Creation Flow

```
1. User fills garden form
   ├─> Name, description, GPS coordinates
   │
2. POST /api/v1/gardens
   ├─> Authorization: Bearer <token>
   │
3. Backend validates JWT
   ├─> Decode token → get user_id
   ├─> Query user from database
   │
4. Validate garden data
   ├─> Pydantic schema: -90 ≤ lat ≤ 90
   ├─> Pydantic schema: -180 ≤ lng ≤ 180
   │
5. Insert garden into database
   ├─> PostGIS creates location POINT from lat/lng
   ├─> Associate with current user
   │
6. Return created garden
   └─> Frontend adds to garden list
```

### Weather Collection Flow (Automated)

```
Every 15 minutes:

1. APScheduler triggers weather_check_job()
   │
2. Acquire Redis lock (timeout 5 minutes)
   ├─> If lock held, skip (another instance running)
   ├─> Lock key: "agent:weather_check:lock"
   │
3. Query all gardens from database
   │
4. For each garden:
   ├─> Async HTTP call to Open-Meteo API
   │   └─> https://api.open-meteo.com/v1/forecast?lat=X&lon=Y
   │
   ├─> Parse JSON response
   ├─> Extract: temperature, humidity, precipitation, wind
   │
   ├─> Insert weather record
   │   └─> Includes: garden_id, recorded_at, created_at
   │
   └─> Log success (structured JSON)
       └─> {"level":"INFO","service":"agent","garden":"Backyard"}
   │
5. Release Redis lock
   │
6. If error occurs:
   ├─> Log error (don't crash)
   ├─> Release lock in finally block
   └─> Continue with next garden
```

### Weather Retrieval Flow

```
1. User opens garden page
   ├─> GET /api/v1/weather/{garden_id}
   │
2. Backend verifies authorization
   ├─> User owns garden?
   │
3. Query latest weather records
   ├─> SELECT * FROM weather
   │   WHERE garden_id = ? 
   │   ORDER BY recorded_at DESC 
   │   LIMIT 10
   │
4. Return weather data
   └─> Frontend displays chart/graph
```

## Technology Choices

### Why PostgreSQL?

- **Mature**: 30+ years of development
- **PostGIS**: Best geospatial database
- **ACID**: Guarantees data consistency
- **JSON Support**: Can store flexible data if needed
- **Performance**: Excellent for <100k records (home lab scale)

### Why Not MongoDB?

- Overkill for structured data (users, gardens, plants)
- No geospatial queries as powerful as PostGIS
- ACID guarantees matter for user data

### Why FastAPI?

- **Speed**: Async/await for I/O operations
- **Validation**: Pydantic catches errors before database
- **Documentation**: Auto-generated OpenAPI docs
- **Type Safety**: Editor autocomplete and MyPy checking
- **Community**: Large ecosystem of extensions

### Why Not Flask/Django?

- Flask: Older, synchronous (blocks on I/O)
- Django: Great for monoliths, overkill for API-only
- FastAPI: Purpose-built for modern APIs

### Why Next.js?

- **React**: Industry standard UI library
- **SSR/SSG**: Better SEO and performance
- **TypeScript**: Catches bugs at compile time
- **App Router**: Modern React patterns (Server Components)
- **Built-in Optimization**: Images, fonts, code splitting

### Why Not Vue/Svelte?

- React: Larger ecosystem and job market
- Next.js: Best React meta-framework

### Why Docker Compose?

- **Simple**: Single YAML file for orchestration
- **Portable**: Works on any Linux/Mac/Windows
- **Development**: Hot reload with volume mounts
- **Production-Ready**: Same config for dev and prod

### Why Not Kubernetes?

- K8s is overkill for a home lab (6 services)
- Higher resource usage (control plane overhead)
- More complex to manage
- Compose is sufficient until you need multi-host

## Security Model

### Authentication

**JWT (JSON Web Tokens)**:
```
Header:  {"alg":"HS256","typ":"JWT"}
Payload: {"sub":"user-uuid","exp":1234567890}
Signature: HMACSHA256(header + payload, SECRET_KEY)
```

**Why JWT?**:
- Stateless (no session storage needed)
- Contains all user info (no database lookup per request)
- Expires automatically (24-hour default)

**Security Properties**:
- Signature prevents tampering
- Expiration prevents unlimited reuse
- HTTPS prevents interception (enable in production!)

### Password Security

**Bcrypt Hashing**:
```python
# Registration
hashed_password = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))

# Login
is_valid = bcrypt.checkpw(password, hashed_password)
```

**Why Bcrypt?**:
- Designed for passwords (slow by design)
- Salted (prevents rainbow table attacks)
- Adaptive (can increase rounds as CPUs get faster)

**Security Properties**:
- Even with database dump, passwords can't be recovered
- Each password hash is unique (salt)

### Authorization

**Row-Level Security**:
```python
# Gardens endpoint - user can only see their own gardens
gardens = db.query(Garden).filter(Garden.user_id == current_user.id).all()

# Update endpoint - verify ownership
garden = db.query(Garden).filter(Garden.id == garden_id).first()
if garden.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized")
```

**Why This Matters**:
- Prevents user A from accessing user B's data
- Even if user guesses another garden's UUID
- Enforced at database query level

### CORS (Cross-Origin Resource Sharing)

```python
# Only allow requests from frontend domain
allowed_origins = ["http://green.lab", "http://localhost:3000"]
```

**Why CORS?**:
- Prevents malicious websites from calling our API
- Browser enforces same-origin policy
- Explicit allow-list required

### Network Security

Docker Network Isolation:
```yaml
services:
  backend:
    networks:
      - greenthumb  # Internal network only
  
  postgres:
    networks:
      - greenthumb  # NOT exposed to host
```

Only Traefik has ports exposed to host (80, 443). All other services communicate via internal Docker network.

## Scaling Considerations

### Vertical Scaling (Current Architecture)

**Single-Host Deployment** (Proxmox VM):
- API: 1 instance, can handle 100+ req/sec
- Agent: 1 instance (Redis lock prevents duplicates)
- PostgreSQL: 1 instance with connection pooling
- Redis: 1 instance (minimal resource usage)

**Resource Requirements**:
- 2 CPU cores
- 4GB RAM
- 10GB disk (grows with weather data)

### Horizontal Scaling (Future)

If you outgrow a single host:

**API** (easy to scale):
```yaml
backend:
  deploy:
    replicas: 3  # Run 3 API instances
```
Traefik load balances automatically.

**Agent** (requires changes):
- Current: Single instance with Redis locking
- Future: Multiple instances, each locks individual gardens
  ```python
  lock_key = f"agent:weather:{garden_id}"
  ```

**Database** (hardest to scale):
- Current: Single PostgreSQL instance
- Future:
  - Read replicas for reporting queries
  - Connection pooler (PgBouncer)
  - Eventually: PostgreSQL cluster (Patroni + HAProxy)

### Performance Optimization

**Current Bottlenecks**:
1. Weather API calls (1-5 seconds each)
   - Solution: Parallel fetching with asyncio.gather()
   
2. Database queries (N+1 problem)
   - Solution: Eager loading with SQLAlchemy joinedload()

3. Frontend re-renders
   - Solution: React.memo() and useMemo()

**Monitoring**:
- Structured logs enable metrics extraction
- Traefik dashboard shows request latency
- Database slow query log

## Conclusion

This architecture balances:
- **Simplicity**: Single server deployment
- **Maintainability**: Clear separation of concerns
- **Scalability**: Can grow to multiple hosts if needed
- **Security**: JWT auth, bcrypt passwords, CORS
- **Observability**: Structured logging, health checks

The Agent/API split is the key design decision, enabling:
- Independent scaling
- Fault isolation
- Different error handling strategies

---

**Questions?** Open an issue on GitHub.

