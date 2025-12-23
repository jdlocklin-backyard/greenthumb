# Contributing to GreenThumb

Thank you for your interest in contributing to GreenThumb! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

This project follows a simple code of conduct:

- **Be respectful** - Treat all contributors with respect
- **Be constructive** - Provide helpful feedback
- **Be patient** - Remember that everyone was a beginner once
- **Be collaborative** - We're building this together

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Git installed
- Docker and Docker Compose
- Make
- A GitHub account
- Basic familiarity with Python (backend) or TypeScript (frontend)

### Fork and Clone

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/greenthumb.git
   cd greenthumb
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL-OWNER/greenthumb.git
   ```

4. **Set up environment**:
   ```bash
   make setup
   make up
   ```

5. **Verify everything works**:
   - Visit http://green.lab
   - Check `make logs` for errors

---

## Development Workflow

### 1. Create a Branch

Always create a feature branch from `main`:

```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features (e.g., `feature/plant-photos`)
- `bugfix/` - Bug fixes (e.g., `bugfix/weather-timeout`)
- `docs/` - Documentation updates (e.g., `docs/deployment-improvements`)
- `refactor/` - Code refactoring (e.g., `refactor/api-error-handling`)

### 2. Make Your Changes

**Backend (Python):**
```bash
# Install dev dependencies
cd backend
pip install -r requirements.txt

# Make changes in backend/app/

# Format code
make format-backend

# Lint code
make lint-backend

# Run tests
make test-backend
```

**Frontend (TypeScript):**
```bash
# Install dependencies
cd frontend
npm install

# Make changes in frontend/app/ or frontend/lib/

# Format code
make format-frontend

# Lint code
make lint-frontend

# Run dev server
npm run dev
```

**Agent (Python):**
```bash
# Make changes in agent/

# Follow same process as backend
make format-backend
```

### 3. Test Your Changes

**Manual Testing:**
```bash
# Rebuild affected services
docker compose build backend
docker compose up -d backend

# Check logs
make logs-backend

# Test in browser
# Visit http://green.lab and http://api.green.lab/docs
```

**Automated Testing:**
```bash
# Backend tests
make test-backend

# Frontend tests (if available)
cd frontend && npm test
```

### 4. Commit Your Changes

**Use conventional commit messages:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting (no code change)
- `refactor:` - Code restructuring
- `perf:` - Performance improvement
- `test:` - Adding tests
- `chore:` - Maintenance

**Examples:**

```bash
# Good commit messages
git commit -m "feat(backend): add plant photo upload endpoint"
git commit -m "fix(frontend): prevent duplicate garden creation

- Add form submission loading state
- Disable submit button during API call
- Clear form after success

Fixes #42"

# Bad commit messages
git commit -m "updates"
git commit -m "fix stuff"
git commit -m "WIP"
```

### 5. Keep Your Branch Updated

```bash
# Fetch latest changes
git fetch upstream

# Rebase on main
git rebase upstream/main

# Resolve conflicts if any
# Then continue: git rebase --continue

# Force push to your fork (only for feature branches!)
git push origin feature/your-feature-name --force
```

---

## Coding Standards

### Python (Backend/Agent)

**Style Guide:**
- Follow PEP 8
- Use Black for formatting (line length: 88)
- Use isort for import sorting
- Use type hints for all functions
- Write docstrings for public functions

**Example:**

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.garden import Garden
from app.schemas import GardenCreate

async def create_garden(
    db: Session,
    garden: GardenCreate,
    user_id: str
) -> Garden:
    """Create a new garden for the specified user.

    Args:
        db: Database session
        garden: Garden creation data
        user_id: Owner's user ID

    Returns:
        Created garden object

    Raises:
        ValueError: If coordinates are invalid
    """
    db_garden = Garden(
        name=garden.name,
        user_id=user_id,
        latitude=garden.latitude,
        longitude=garden.longitude
    )
    db.add(db_garden)
    await db.commit()
    await db.refresh(db_garden)
    return db_garden
```

**Tools:**
```bash
# Format (automatically fixes)
black .
isort .

# Lint (reports issues)
flake8 .

# Type check (static analysis)
mypy .
```

### TypeScript (Frontend)

**Style Guide:**
- Use functional components with hooks
- Enable strict mode in TypeScript
- Use Prettier for formatting
- Use ESLint for linting
- Prefer arrow functions
- Use meaningful variable names

**Example:**

```typescript
import { useState, useEffect } from 'react';
import { Garden } from '@/lib/types';
import { api } from '@/lib/api';

interface GardenListProps {
  userId: string;
}

export const GardenList: React.FC<GardenListProps> = ({ userId }) => {
  const [gardens, setGardens] = useState<Garden[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGardens = async () => {
      try {
        const data = await api.gardens.list();
        setGardens(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchGardens();
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {gardens.map((garden) => (
        <GardenCard key={garden.id} garden={garden} />
      ))}
    </div>
  );
};
```

**Tools:**
```bash
# Format
npm run format

# Lint
npm run lint

# Type check
npm run type-check
```

### SQL/Database

**Migrations:**
- Use Alembic for schema changes
- Never modify existing migrations
- Test migrations both up and down

**Example:**
```bash
# Create migration
cd backend
alembic revision -m "add plant photos table"

# Edit the generated file in alembic/versions/
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1
```

### Documentation

**Markdown:**
- Use clear headings
- Include code examples
- Add tables for reference data
- Keep line length reasonable (80-100 chars)

**Comments:**
- Explain WHY, not WHAT
- Update comments when code changes
- Remove commented-out code

---

## Submitting Changes

### Pull Request Process

1. **Ensure all tests pass**:
   ```bash
   make test-backend
   make lint-backend
   make lint-frontend
   ```

2. **Update documentation** if needed:
   - Update README.md for new features
   - Update API docs if endpoints changed
   - Add or update architecture docs

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request** on GitHub:
   - Go to original repository
   - Click "Pull requests" → "New pull request"
   - Click "compare across forks"
   - Select your fork and branch
   - Fill in the PR template
   - Submit

5. **Respond to feedback**:
   - Check for review comments
   - Make requested changes
   - Push updates to same branch
   - Reply to comments when addressed

6. **Wait for merge**:
   - Maintainer will merge when approved
   - PR will be automatically closed
   - Your contribution will be in the next release!

### Pull Request Checklist

Before submitting, verify:

- [ ] Code follows project style
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] No merge conflicts with main
- [ ] PR description is clear
- [ ] Related issue linked (if applicable)

---

## Reporting Issues

### Before Opening an Issue

1. **Search existing issues** - Someone may have already reported it
2. **Check documentation** - Answer might be in guides
3. **Update to latest** - Bug might be fixed already
4. **Gather information** - Logs, versions, steps to reproduce

### Opening an Issue

Use the appropriate template:

- **Bug Report** - For bugs and unexpected behavior
- **Feature Request** - For new functionality suggestions

**Include:**
- Clear description
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Environment details
- Relevant logs
- Screenshots if helpful

**Example of a good bug report:**

```
Title: [BUG] Weather agent crashes when garden has no coordinates

Description:
The agent worker crashes with a NoneType error when a garden
in the database has NULL latitude/longitude values.

Steps to Reproduce:
1. Create garden via API without coordinates
2. Wait for agent weather check (15 min)
3. Check agent logs

Expected: Agent should skip gardens without coordinates
Actual: Agent crashes with KeyError

Environment:
- Ubuntu 22.04 LXC on Proxmox
- Docker 24.0.5
- GreenThumb commit: abc123

Logs:
```
[Paste logs here]
```

Possible Fix:
Add validation in garden creation endpoint to require coordinates,
or add null check in agent before processing.
```

---

## Development Tips

### Hot Reload

For faster development:

**Backend:**
```bash
# Backend auto-reloads on code changes
# Just edit files in backend/app/
# Check logs: make logs-backend
```

**Frontend:**
```bash
# Frontend auto-reloads
# Edit files in frontend/app/
# Browser will refresh automatically
```

**Agent:**
```bash
# Agent requires restart
docker restart greenthumb-agent
```

### Debugging

**Backend:**
```bash
# Shell into container
make backend-shell

# Run Python interactively
python

# Import and test
from app.models.garden import Garden
```

**Database:**
```bash
# Access PostgreSQL
make db-shell

# Run queries
SELECT * FROM gardens;
\d gardens
\q
```

**Logs:**
```bash
# All services
make logs

# Specific service
make logs-backend
make logs-agent
make logs-frontend

# Filter for errors
make logs | grep ERROR

# Follow specific container
docker logs -f greenthumb-backend
```

### Performance Testing

```bash
# API load testing with Apache Bench
ab -n 1000 -c 10 http://api.green.lab/api/v1/gardens

# Database query analysis
make db-shell
EXPLAIN ANALYZE SELECT * FROM gardens WHERE user_id = 'xxx';
```

---

## Questions?

- **Documentation**: Check [docs/](docs/)
- **Architecture**: Read [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Setup**: See [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- **GitHub Issues**: Open a question issue
- **Discussions**: Use GitHub Discussions for general questions

---

**Thank you for contributing to GreenThumb! 🌱**

Every contribution, no matter how small, helps make this project better for the home lab community.
