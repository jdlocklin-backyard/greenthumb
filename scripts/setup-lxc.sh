#!/bin/bash
# =============================================================================
# GreenThumb - LXC Container Quick Setup
# =============================================================================
# Run this INSIDE a fresh Ubuntu 22.04 LXC container
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/your-org/greenthumb/main/scripts/setup-lxc.sh | bash
#
# Or:
#   wget -qO- https://raw.githubusercontent.com/your-org/greenthumb/main/scripts/setup-lxc.sh | bash
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check we're running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root (or with sudo)"
    exit 1
fi

# Check we're in an LXC container
if [ ! -f /run/systemd/container ]; then
    log_warn "This doesn't appear to be a systemd container. Continuing anyway..."
fi

echo ""
echo "=========================================="
echo "  GreenThumb LXC Setup"
echo "=========================================="
echo ""

# Step 1: Update system
log_info "Updating system packages..."
apt update && apt upgrade -y

# Step 2: Install Docker
log_info "Installing Docker..."
if command -v docker &> /dev/null; then
    log_info "Docker already installed: $(docker --version)"
else
    curl -fsSL https://get.docker.com | sh
    log_info "Docker installed: $(docker --version)"
fi

# Step 3: Install git
log_info "Installing git..."
apt install -y git

# Step 4: Clone GreenThumb
APP_DIR="/opt/greenthumb"
if [ -d "$APP_DIR" ]; then
    log_warn "Directory $APP_DIR already exists. Updating..."
    cd "$APP_DIR"
    git pull || true
else
    log_info "Cloning GreenThumb to $APP_DIR..."
    git clone https://github.com/your-org/greenthumb.git "$APP_DIR"
    cd "$APP_DIR"
fi

# Step 5: Create .env file
if [ ! -f .env ]; then
    log_info "Creating .env from template..."
    cp .env.example .env

    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/dev-secret-change-in-production-use-openssl-rand-hex-32/$SECRET_KEY/" .env
    log_info "Generated new SECRET_KEY"
else
    log_warn ".env already exists, keeping existing configuration"
fi

# Step 6: Build and start
log_info "Building and starting containers (this takes 3-5 minutes)..."
docker compose up -d --build

# Step 7: Wait for services to be healthy
log_info "Waiting for services to start..."
sleep 10

# Check health
HEALTHY=true
for service in postgres redis backend; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' greenthumb-$service 2>/dev/null || echo "unknown")
    if [ "$STATUS" != "healthy" ]; then
        log_warn "Service $service is $STATUS (may still be starting)"
        HEALTHY=false
    fi
done

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""

if [ "$HEALTHY" = true ]; then
    log_info "All services are healthy!"
else
    log_warn "Some services may still be starting. Check with: docker compose ps"
fi

echo ""
echo "Access GreenThumb at:"
echo ""
echo "  Main App:    http://$IP_ADDR:3000"
echo "  API Docs:    http://$IP_ADDR:3000/api/docs"
echo ""
echo "Useful commands:"
echo ""
echo "  cd $APP_DIR"
echo "  docker compose ps          # Check status"
echo "  docker compose logs -f     # View logs"
echo "  docker compose restart     # Restart services"
echo ""
