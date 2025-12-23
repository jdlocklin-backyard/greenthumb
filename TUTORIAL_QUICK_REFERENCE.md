# GreenThumb YouTube Tutorial - Quick Reference

## Episode Structure at a Glance

```
EPISODE 1: ARCHITECTURE & PREREQUISITES (25 min)
├─ [2 min] Welcome & what you'll learn
├─ [8 min] System architecture diagram (build live)
├─ [10 min] Prerequisites deep dive
│           - Proxmox containers
│           - Docker & Compose basics
│           - Networking concepts
│           - DNS setup
└─ [5 min] Project file walkthrough

EPISODE 2: DEPLOYMENT & TESTING (35 min)
├─ [5 min] Environment setup (.env file)
├─ [5 min] Starting services (docker compose up)
├─ [5 min] Traefik dashboard walkthrough
├─ [8 min] Testing frontend (create account & garden)
├─ [7 min] Testing API (Swagger UI, endpoints)
└─ [5 min] Database exploration (PostGIS queries)

EPISODE 3: MONITORING & TROUBLESHOOTING (25-30 min)
├─ [5 min] Agent & Redis locking
├─ [5 min] Logs & monitoring
├─ [8 min] Common mistakes & diagnostics
├─ [7 min] Live troubleshooting scenarios
└─ [5 min] Next steps (HTTPS, scaling, backups)
```

---

## Top 5 Concepts to Explain Simply

### 1. Containers as Lightweight VMs
**Script**: "Containers are like shipping containers on a ship. Each has its own cargo (software), they stack efficiently, and they're all using the same port infrastructure (the ship). But each is sealed—cargo doesn't leak."

**Demo**: Show `docker ps` and explain what each row means.

---

### 2. Traefik as a Receptionist
**Script**: "Traefik sits at the front desk (port 80). When your request arrives asking for 'green.lab', Traefik checks the routing rules and sends you to the right room (frontend:3000). For 'api.green.lab', it sends you to a different room (backend:8000)."

**Demo**: Traefik dashboard showing routers → services → ports.

---

### 3. Docker Network = Private Office Building
**Script**: "All containers live in a private office building (the greenthumb Docker network). They talk to each other by name, like dialing an extension. But only Traefik has a door to the outside world (port 80)."

**Demo**: `docker network inspect greenthumb` showing all containers' IPs.

---

### 4. Redis Lock = Bathroom Key
**Script**: "When the agent wants to collect weather, it grabs the Redis lock (like a bathroom key). A backup agent sees the lock is taken and waits. When the first agent finishes, it puts the key back."

**Demo**: Watch Redis keys during weather collection with `redis-cli KEYS "*lock*"`.

---

### 5. PostGIS = Geographic Superpowers
**Script**: "PostgreSQL stores data. PostGIS makes it understand Earth coordinates. Instead of 'find gardens with latitude between 40-41', we can say 'find gardens within 10km of here'."

**Demo**: Run a geospatial query and explain the output.

---

## Critical Terminal Commands to Show

```bash
# Verification
docker --version
docker compose version
docker ps
docker ps -a

# Starting & Stopping
docker compose up
docker compose down
docker compose restart backend

# Viewing Logs
docker logs greenthumb-backend
docker logs -f greenthumb-agent
docker compose logs | grep "error"

# Accessing Services
docker exec greenthumb-postgres psql -U greenthumb -d greenthumb
docker exec greenthumb-backend env | grep POSTGRES_HOST
docker exec greenthumb-redis redis-cli KEYS "*"

# Validating Config
docker compose config
docker compose config --services

# Troubleshooting
docker ps | grep postgres  # Check if running
sudo lsof -i :80           # Check port usage
curl -v http://api.green.lab/health  # Test connectivity
```

---

## Browser Checkpoints

### Checkpoint URLs (in order)
1. `http://green.lab` — Frontend loads?
2. `http://traefik.green.lab` (admin/admin) — Dashboard shows services?
3. `http://api.green.lab/docs` — Swagger UI shows endpoints?
4. Create account, garden, plant
5. Check browser DevTools (F12) → Network tab → No errors?

---

## Common Mistakes & Quick Fixes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| `/etc/hosts` missing | "green.lab not found" | Add to `/etc/hosts` with correct IP |
| Wrong `POSTGRES_HOST` | Backend can't connect | Should be `postgres` (service name), not IP |
| Wrong `NEXT_PUBLIC_API_URL` | Frontend can't reach API | Should be `http://api.green.lab` |
| Port 80 in use | "Address already in use" | `sudo lsof -i :80` then stop conflicting service |
| `.env` not updated | Services using defaults | Rebuild: `docker compose build` then `up` |
| Database corrupted | Backend hangs on startup | `rm -rf data/db` to delete volume, restart |
| Redis lock stuck | Agent not running | `docker exec greenthumb-redis redis-cli DEL agent:weather_check:lock` |

---

## What Each Container Does (One Sentence Each)

| Container | Role |
|-----------|------|
| **Traefik** | Listens on port 80, routes requests to right service based on hostname |
| **PostgreSQL** | Stores all data (users, gardens, plants, weather) with PostGIS for coordinates |
| **Redis** | Provides locking mechanism so multiple agents don't collect weather simultaneously |
| **Backend** | FastAPI REST API that validates requests, queries database, returns JSON |
| **Agent** | Python worker that runs scheduled tasks (weather collection every 15 min) |
| **Frontend** | Next.js web app that users interact with, calls backend API |

---

## Success Metrics (How to Know Everything Works)

- [ ] All 6 containers show "Up" in `docker ps`
- [ ] Postgres and Backend show "healthy" status
- [ ] Can visit `http://green.lab` and see login page
- [ ] Can register a new account
- [ ] Can create a garden
- [ ] Can add a plant
- [ ] After 15+ minutes, weather data appears
- [ ] `docker logs greenthumb-agent` shows successful weather checks
- [ ] No red errors in browser DevTools console
- [ ] Traefik dashboard at `http://traefik.green.lab` shows all services active

---

## Key Files to Reference

| File | Purpose | Key Content |
|------|---------|-------------|
| `docker-compose.yml` | Service orchestration | 6 services, volumes, networks, labels |
| `.env` | Environment variables | Database credentials, API URLs, secrets |
| `backend/Dockerfile` | Backend image | Python 3.11, FastAPI, PostGIS libs |
| `frontend/Dockerfile` | Frontend image | Node 20, Next.js build, multi-stage |
| `agent/Dockerfile` | Agent image | Python 3.11, APScheduler, Redis |
| `docs/ARCHITECTURE.md` | Deep technical docs | Detailed system design |
| `README.md` | User guide | Quick start, CLI commands |

---

## Pre-Recording Checklist

Before you hit record:
- [ ] GreenThumb fully deployed locally (or on test Proxmox)
- [ ] All 6 services running and healthy
- [ ] DNS entries in `/etc/hosts` verified
- [ ] Traefik dashboard accessible
- [ ] Frontend loads without errors
- [ ] Created test account, garden, plant
- [ ] Waited 15+ min to see weather data
- [ ] All terminal commands tested ahead of time
- [ ] Backup `.env` file (for reset if needed)
- [ ] Clean up test data before final recording

---

## Ad-Lib Script Helpers

### When something breaks during recording:
> "Even if things break during deployment—and they might—we'll learn how to diagnose it using logs and curl commands. Breaking things and fixing them is how you really learn your infrastructure."

### When explaining Traefik for the third time:
> "Think of Traefik like a DNS server for your network. Instead of translating domain names to IPs, it translates domain names to containers. It's the thing that lets you visit 'green.lab' instead of remembering 'port 3000'."

### When explaining why services are separate:
> "Why split the agent from the API? Because weather collection takes 30+ seconds, but API requests should return in milliseconds. We don't want a slow background job blocking user requests."

### When explaining Docker networking:
> "In Docker, 'localhost' means inside the container. From your computer, you can't access container:8000 directly. Only Traefik has a 'door' (port 80) that opens to the outside. That's why you can't visit localhost:8000."

---

## Thumbnail & Title Ideas

### Episode 1
- **Title**: "Deploy GreenThumb on Proxmox #1: Architecture & Setup"
- **Thumbnail**: Proxmox logo + Docker logo + "Microservices" text

### Episode 2
- **Title**: "Deploy GreenThumb on Proxmox #2: Full Deployment & Testing"
- **Thumbnail**: Terminal screenshot + checkmarks + "6 containers running" text

### Episode 3
- **Title**: "Deploy GreenThumb on Proxmox #3: Monitoring & Troubleshooting"
- **Thumbnail**: Traefik dashboard screenshot + "Debug" text

---

## Description Template

```
Learn to deploy GreenThumb, a production-ready gardening platform on your Proxmox home lab!

In this [PART N] episode, we:
- [List 3-4 key learnings]
- Deploy [N] services using Docker Compose
- Test everything with curl and browser

What is GreenThumb?
A self-hosted app that tracks your gardens, monitors plants, and collects weather data automatically. Built with FastAPI, Next.js, PostgreSQL, Redis, and Traefik.

Repository: https://github.com/...

Prerequisites:
- Proxmox with Ubuntu container
- Docker 24.0+
- Basic Linux/Docker knowledge

Timestamps:
[00:00] Intro
[02:45] Explain [concept]
[15:20] Deploy [component]
[25:30] Test [feature]

Questions? Drop them in the comments!
```

---

## Resource Links for Description

- Repository: [GitHub link]
- Architecture Docs: [GitHub link to ARCHITECTURE.md]
- Docker Docs: https://docs.docker.com/
- Traefik Docs: https://doc.traefik.io/
- PostgreSQL PostGIS: https://postgis.net/
- FastAPI: https://fastapi.tiangolo.com/
- Proxmox Docs: https://pve.proxmox.com/wiki/

---

## Post-Video Engagement Ideas

1. **Create a companion guide**: Write a blog post with the same content as the video
2. **Code snippets**: Share troubleshooting commands in a GitHub gist
3. **Live stream Q&A**: Answer questions about deployment
4. **Follow-up videos**:
   - "Enable HTTPS with Let's Encrypt"
   - "Scale GreenThumb to multiple servers"
   - "Backup and restore your garden data"
5. **Discord community**: Help viewers with their deployments

---

**Total Production Time Estimate**:
- Script writing: 2-3 hours (already done!)
- Recording: 3-4 hours
- Editing: 4-5 hours
- **Total: 9-12 hours for high-quality 3-episode series**

**Ready to record!**
