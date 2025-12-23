# GitHub Setup Guide

**Preparing GreenThumb for GitHub publication and collaboration**

---

## Table of Contents

1. [What to Commit](#what-to-commit)
2. [What NOT to Commit](#what-not-to-commit)
3. [Initial Repository Setup](#initial-repository-setup)
4. [Forking and Customization](#forking-and-customization)
5. [Contributing Guidelines](#contributing-guidelines)
6. [Version Control Workflow](#version-control-workflow)
7. [Release Management](#release-management)

---

## What to Commit

These files SHOULD be in your Git repository:

### Application Code
- ✅ `backend/` - All Python backend code
- ✅ `agent/` - Agent worker code
- ✅ `frontend/` - Next.js frontend code
- ✅ `docs/` - Documentation files

### Configuration Templates
- ✅ `.env.example` - Environment template (no secrets)
- ✅ `docker-compose.yml` - Service orchestration
- ✅ `Makefile` - Convenience commands

### Development Files
- ✅ `.gitignore` - Ignore rules
- ✅ `README.md` - Project overview
- ✅ `LICENSE` - Open source license
- ✅ `.github/` - GitHub Actions, templates

### Database
- ✅ `backend/init-db.sql` - Database schema
- ✅ `backend/alembic/` - Database migrations (if using Alembic)

---

## What NOT to Commit

These files MUST be in `.gitignore`:

### Secrets and Credentials
- ❌ `.env` - Contains passwords and API keys
- ❌ `*.pem`, `*.key` - Private keys
- ❌ `acme.json` - SSL certificates

### Data and State
- ❌ `data/` - Database and Redis data
- ❌ `logs/` - Application logs
- ❌ `*.log` - Log files

### Build Artifacts
- ❌ `frontend/node_modules/` - NPM dependencies
- ❌ `frontend/.next/` - Next.js build output
- ❌ `backend/__pycache__/` - Python bytecode
- ❌ `backend/*.pyc` - Compiled Python
- ❌ `backend/.pytest_cache/` - Test cache

### IDE and OS Files
- ❌ `.vscode/` - VS Code settings (or keep with `!.vscode/settings.json`)
- ❌ `.idea/` - PyCharm settings
- ❌ `.DS_Store` - macOS metadata
- ❌ `Thumbs.db` - Windows metadata

---

## Initial Repository Setup

### Step 1: Create .gitignore

Ensure your `.gitignore` contains:

```gitignore
# Environment and secrets
.env
*.pem
*.key
acme.json

# Data directories
data/
logs/
*.log

# Backend Python
backend/__pycache__/
backend/*.pyc
backend/.pytest_cache/
backend/venv/
backend/.venv/
backend/*.egg-info/

# Frontend Node
frontend/node_modules/
frontend/.next/
frontend/out/
frontend/.cache/
frontend/dist/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

---

### Step 2: Create README.md

Your README should include:

```markdown
# GreenThumb 🌱

Production-ready, self-hosted gardening platform for Proxmox Home Lab.

## Quick Start

See [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for full setup.

```bash
make setup && make up
```

## Documentation

- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Step-by-step setup
- [Quick Reference](docs/QUICK_REFERENCE.md) - Commands cheat sheet
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Contributing](docs/GITHUB_SETUP.md) - How to contribute

## Features

- Track multiple gardens and plants
- Automated weather data collection
- REST API with OpenAPI docs
- Responsive web interface
- Self-hosted on Proxmox/Docker

## License

MIT License - see LICENSE file
```

---

### Step 3: Create LICENSE

Choose an open-source license:

**MIT License (Recommended - most permissive):**
```
MIT License

Copyright (c) 2024 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

### Step 4: Initialize Git Repository

```bash
# Navigate to project
cd /opt/greenthumb

# Initialize repository
git init

# Add all files (respecting .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: GreenThumb platform v1.0

- FastAPI backend with async SQLAlchemy
- Next.js frontend with TypeScript
- Agent worker for weather collection
- PostgreSQL + PostGIS database
- Redis caching
- Traefik reverse proxy
- Docker Compose orchestration
- Comprehensive documentation"

# Add remote (replace with your GitHub URL)
git remote add origin https://github.com/yourusername/greenthumb.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

### Step 5: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `greenthumb`
3. Description: `Self-hosted gardening platform for Proxmox home labs`
4. Visibility: Public (or Private)
5. **DON'T initialize with README, .gitignore, or license** (we already have these)
6. Click **Create repository**
7. Follow the "push an existing repository" instructions

---

### Step 6: Add Topics and Description

On GitHub repository page:

1. Click **⚙️ Settings** → **General**
2. **Topics**: Add relevant tags
   - `gardening`
   - `self-hosted`
   - `proxmox`
   - `docker`
   - `fastapi`
   - `nextjs`
   - `home-lab`
   - `plant-tracking`

3. Update **About** section with description and website

---

## Forking and Customization

### For Users: How to Fork

**If you want to customize GreenThumb for your own use:**

1. **Fork the repository**
   - Click **Fork** button on GitHub
   - Creates a copy under your account

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/greenthumb.git
   cd greenthumb
   ```

3. **Customize as needed**
   - Modify `.env.example` defaults
   - Change domains in `docker-compose.yml`
   - Add custom features

4. **Keep your fork updated**
   ```bash
   # Add upstream remote
   git remote add upstream https://github.com/ORIGINAL-OWNER/greenthumb.git

   # Fetch upstream changes
   git fetch upstream

   # Merge into your fork
   git merge upstream/main

   # Push to your fork
   git push origin main
   ```

---

### Customization Ideas

**Common customizations:**

- **Change domains**: Edit `.env` → `TRAEFIK_DOMAIN`
- **Adjust weather interval**: Edit `.env` → `AGENT_CHECK_INTERVAL`
- **Add new plant fields**: Modify `backend/app/models/plant.py`
- **Custom UI theme**: Edit `frontend/app/globals.css`
- **Additional API endpoints**: Add to `backend/app/api/v1/endpoints/`

**Example: Add plant photo uploads**

1. Update database model: `backend/app/models/plant.py`
2. Add storage volume in `docker-compose.yml`
3. Create upload endpoint in backend
4. Add upload component in frontend

---

## Contributing Guidelines

### How to Contribute

We welcome contributions! Here's how:

1. **Fork the repository** (see above)

2. **Create a feature branch**
   ```bash
   git checkout -b feature/add-frost-alerts
   ```

3. **Make your changes**
   - Write clear, commented code
   - Follow existing code style
   - Add tests if applicable

4. **Test your changes**
   ```bash
   # Backend tests
   make test-backend

   # Frontend lint
   make lint-frontend
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "Add frost alert notifications

   - New endpoint: GET /api/v1/weather/frost-risk
   - Email notification when temperature drops below 32°F
   - Frontend banner for at-risk gardens"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/add-frost-alerts
   ```

7. **Create Pull Request**
   - Go to original repository on GitHub
   - Click **Pull requests** → **New pull request**
   - Select **compare across forks**
   - Choose your fork and branch
   - Fill in PR template (see below)

---

### Pull Request Template

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Changes Made

- Change 1
- Change 2
- Change 3

## Testing

How did you test this?

- [ ] Manual testing
- [ ] Unit tests added
- [ ] Integration tests added

## Screenshots (if applicable)

## Checklist

- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests pass locally
```

---

### Code Style Guidelines

**Python (Backend/Agent):**
- Use **Black** for formatting: `make format-backend`
- Use **flake8** for linting: `make lint-backend`
- Use **MyPy** for type checking: `make type-check`
- Follow PEP 8 conventions
- Add type hints to all functions
- Write docstrings for public functions

**TypeScript (Frontend):**
- Use **Prettier** for formatting: `make format-frontend`
- Use **ESLint** for linting: `make lint-frontend`
- Enable strict TypeScript mode
- Use functional components with hooks
- Prefer arrow functions
- Use meaningful variable names

**General:**
- Write clear commit messages
- Keep commits atomic (one logical change)
- Update documentation with code changes
- Add tests for new features

---

## Version Control Workflow

### Branching Strategy

**Main branches:**

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Individual features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Emergency fixes for production

**Workflow:**

```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/plant-photos

# Work on feature
git add .
git commit -m "Add plant photo model"

# Keep updated with develop
git fetch origin
git rebase origin/develop

# When done, merge to develop
git checkout develop
git merge feature/plant-photos
git push origin develop

# For release, merge develop → main
git checkout main
git merge develop
git tag -a v1.1.0 -m "Release v1.1.0: Plant photos"
git push origin main --tags
```

---

### Commit Message Format

**Use conventional commits:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation change
- `style:` Code style (formatting, no logic change)
- `refactor:` Code restructuring
- `perf:` Performance improvement
- `test:` Adding tests
- `chore:` Maintenance (dependencies, build)

**Examples:**

```
feat(backend): add frost alert notifications

- New GET /api/v1/weather/frost-risk endpoint
- Email service integration
- Scheduled daily check at 6 PM

Closes #42
```

```
fix(frontend): prevent duplicate garden creation

- Add form submission loading state
- Disable submit button during API call
- Clear form after successful submission

Fixes #38
```

```
docs: update deployment guide for ARM architecture

- Add specific instructions for Raspberry Pi
- Document memory requirements
- Include alternative image sources
```

---

## Release Management

### Versioning

Use **Semantic Versioning** (SemVer):

```
MAJOR.MINOR.PATCH

1.2.3
│ │ └─ Patch: Bug fixes
│ └─── Minor: New features (backward compatible)
└───── Major: Breaking changes
```

**Examples:**
- `1.0.0` → `1.0.1`: Bug fix (weather API timeout)
- `1.0.1` → `1.1.0`: New feature (plant photos)
- `1.1.0` → `2.0.0`: Breaking change (new API authentication)

---

### Creating a Release

1. **Update version numbers**
   - `.env.example` → `APP_VERSION=1.1.0`
   - `backend/app/core/config.py`
   - `frontend/package.json`

2. **Update CHANGELOG.md**
   ```markdown
   # Changelog

   ## [1.1.0] - 2024-01-15

   ### Added
   - Plant photo uploads
   - Frost risk alerts

   ### Changed
   - Improved weather API error handling

   ### Fixed
   - Garden deletion bug (#38)
   ```

3. **Commit and tag**
   ```bash
   git add .
   git commit -m "chore: bump version to 1.1.0"
   git tag -a v1.1.0 -m "Release v1.1.0

   New Features:
   - Plant photo uploads
   - Frost risk alerts

   Improvements:
   - Better weather error handling

   Bug Fixes:
   - Fixed garden deletion
   "
   git push origin main --tags
   ```

4. **Create GitHub Release**
   - Go to repository → **Releases** → **Draft new release**
   - Tag: `v1.1.0`
   - Title: `v1.1.0 - Plant Photos and Frost Alerts`
   - Description: Copy from CHANGELOG.md
   - Attach build artifacts if applicable
   - Click **Publish release**

---

### Release Checklist

Before releasing:

- [ ] All tests pass: `make test-backend`
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers bumped
- [ ] No security vulnerabilities
- [ ] Database migrations tested
- [ ] Deployment guide accurate
- [ ] Breaking changes documented
- [ ] GitHub release created
- [ ] Docker images published (if applicable)

---

## GitHub Features

### Issue Templates

Create `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug Report
about: Report a bug or unexpected behavior
title: '[BUG] '
labels: bug
assignees: ''
---

## Description

Clear description of the bug

## Steps to Reproduce

1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior

What should happen

## Actual Behavior

What actually happens

## Environment

- OS: [e.g., Ubuntu 22.04]
- Docker version:
- GreenThumb version:

## Logs

```
Paste relevant logs here
```

## Screenshots

If applicable
```

---

### GitHub Actions (CI/CD)

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd backend
          pytest

      - name: Lint
        run: |
          cd backend
          flake8 .
          black --check .

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Lint
        run: |
          cd frontend
          npm run lint

      - name: Type check
        run: |
          cd frontend
          npm run type-check
```

---

## Best Practices

### For Repository Maintainers

1. **Review PRs promptly** - Aim for 48-hour response time
2. **Be kind and constructive** - We're all learning
3. **Document decisions** - Use GitHub discussions for major changes
4. **Keep dependencies updated** - Regular Dependabot PRs
5. **Tag releases consistently** - Follow SemVer
6. **Maintain CHANGELOG** - Keep users informed

---

### For Contributors

1. **Search existing issues** before opening new ones
2. **One feature per PR** - Easier to review
3. **Update documentation** with code changes
4. **Add tests** for new features
5. **Be patient** - Reviews take time
6. **Follow code style** - Use provided formatters

---

## Security

### Reporting Vulnerabilities

**DO NOT open public issues for security vulnerabilities**

Instead:
1. Email: security@yourdomain.com (or create SECURITY.md)
2. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

3. Wait for response before public disclosure

---

### Keeping Dependencies Secure

```bash
# Backend: Check for vulnerabilities
pip install safety
safety check -r backend/requirements.txt

# Frontend: Check for vulnerabilities
cd frontend
npm audit

# Fix automatically
npm audit fix
```

Enable Dependabot on GitHub:
- Settings → Security → Dependabot
- Enable security updates
- Enable version updates

---

## Resources

**Git Guides:**
- [Git Handbook](https://guides.github.com/introduction/git-handbook/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)

**Open Source:**
- [Open Source Guide](https://opensource.guide/)
- [Choose a License](https://choosealicense.com/)
- [Contributor Covenant](https://www.contributor-covenant.org/)

**Tools:**
- [GitHub CLI](https://cli.github.com/)
- [Git Graph (VS Code)](https://marketplace.visualstudio.com/items?itemName=mhutchie.git-graph)
- [Semantic Release](https://semantic-release.gitbook.io/)

---

**Happy contributing! 🌱**
