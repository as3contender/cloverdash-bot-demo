#!/bin/bash

# Remote deployment script for backend
# Run this script directly on the server to avoid SSH timeouts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/opt/cloverdash-bot/backend"
LOG_FILE="/tmp/backend_deploy.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to log and display
log_display() {
    echo -e "${2:-}$1${NC}"
    log "$1"
}

# Start deployment
log_display "🚀 Starting backend deployment..." "$BLUE"
log_display "📁 Working directory: $DEPLOY_DIR" "$YELLOW"
log_display "📋 Log file: $LOG_FILE" "$YELLOW"

# Create deploy directory if it doesn't exist
if [ ! -d "$DEPLOY_DIR" ]; then
    log_display "❌ Deploy directory not found: $DEPLOY_DIR" "$RED"
    exit 1
fi

cd "$DEPLOY_DIR"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    log_display "❌ docker-compose.yml not found in $DEPLOY_DIR" "$RED"
    exit 1
fi

# Stop existing containers
log_display "🛑 Stopping existing containers..." "$YELLOW"
docker-compose down --remove-orphans 2>&1 | tee -a "$LOG_FILE"

# Build image with detailed logging
log_display "🏗️  Building backend Docker image..." "$BLUE"
log_display "📊 This process may take 5-10 minutes..." "$YELLOW"

# Try building with cache first
log_display "🔄 Attempting build with cache..." "$YELLOW"
if timeout 600 docker-compose build 2>&1 | tee -a "$LOG_FILE"; then
    log_display "✅ Build with cache successful!" "$GREEN"
    BUILD_SUCCESS=true
else
    log_display "⚠️  Build with cache failed, trying without cache..." "$YELLOW"
    if timeout 900 docker-compose build --no-cache 2>&1 | tee -a "$LOG_FILE"; then
        log_display "✅ Build without cache successful!" "$GREEN"
        BUILD_SUCCESS=true
    else
        log_display "❌ Build failed completely" "$RED"
        BUILD_SUCCESS=false
    fi
fi

if [ "$BUILD_SUCCESS" = false ]; then
    log_display "❌ Docker build failed. Check logs at $LOG_FILE" "$RED"
    exit 1
fi

# Start containers
log_display "🚀 Starting backend containers..." "$BLUE"
if docker-compose up -d 2>&1 | tee -a "$LOG_FILE"; then
    log_display "✅ Containers started successfully!" "$GREEN"
else
    log_display "❌ Failed to start containers" "$RED"
    exit 1
fi

# Wait for backend to be ready
log_display "⏳ Waiting for backend to be ready..." "$YELLOW"
READY=false
for i in {1..30}; do
    if curl -s http://localhost:8000/health/ >/dev/null 2>&1; then
        log_display "✅ Backend is ready!" "$GREEN"
        READY=true
        break
    fi
    log "Health check attempt $i/30..."
    sleep 2
done

if [ "$READY" = false ]; then
    log_display "❌ Backend failed to start properly" "$RED"
    log_display "📋 Container status:" "$YELLOW"
    docker-compose ps | tee -a "$LOG_FILE"
    log_display "📋 Recent logs:" "$YELLOW"
    docker-compose logs --tail=20 | tee -a "$LOG_FILE"
    exit 1
fi

# Final health check
log_display "🏥 Running final health check..." "$BLUE"
HEALTH_RESULT=$(curl -s http://localhost:8000/health/ 2>/dev/null)
if [ $? -eq 0 ]; then
    log_display "✅ Health check passed!" "$GREEN"
    log "Health check result: $HEALTH_RESULT"
else
    log_display "⚠️  Health check failed, but container is running" "$YELLOW"
fi

# Display final status
log_display "🎉 Backend deployment completed successfully!" "$GREEN"
log_display "📊 Container status:" "$BLUE"
docker-compose ps | tee -a "$LOG_FILE"

log_display "📋 Useful commands:" "$BLUE"
log_display "  View logs: docker-compose logs -f" "$YELLOW"
log_display "  Check status: docker-compose ps" "$YELLOW"
log_display "  Restart: docker-compose restart" "$YELLOW"
log_display "  Health check: curl http://localhost:8000/health/" "$YELLOW"

log_display "📁 Full deployment log saved to: $LOG_FILE" "$YELLOW"
log_display "🎯 Backend is ready for use!" "$GREEN" 