#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load deployment configuration
if [ -f "deploy.env" ]; then
    source deploy.env
else
    echo -e "${YELLOW}⚠️  deploy.env not found, using defaults${NC}"
fi

# Default values
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}
REMOTE_USER=${REMOTE_USER:-root}
REMOTE_HOST=${REMOTE_HOST:-64.227.69.138}
REMOTE_DEPLOY_DIR=${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}

# Prepare SSH command
SSH_CMD="ssh"
if [ -n "$SSH_KEY_PATH" ] && [ "$SSH_KEY_PATH" != "" ]; then
    SSH_KEY_EXPANDED=$(eval echo $SSH_KEY_PATH)
    if [ -f "$SSH_KEY_EXPANDED" ]; then
        SSH_CMD="ssh -i $SSH_KEY_EXPANDED"
    else
        SSH_CMD="ssh"
    fi
fi

echo -e "${BLUE}🔍 Docker Debug Tool${NC}"
echo -e "${YELLOW}Target: $REMOTE_USER@$REMOTE_HOST${NC}"
echo ""

echo -e "${BLUE}Checking Docker installation...${NC}"

$SSH_CMD $REMOTE_USER@$REMOTE_HOST '
    echo "=== Docker Version ==="
    docker --version
    echo ""
    
    echo "=== Docker Service Status ==="
    systemctl status docker --no-pager -l
    echo ""
    
    echo "=== Checking docker-compose executable ==="
    if [ -f "/usr/local/bin/docker-compose" ]; then
        echo "File exists: /usr/local/bin/docker-compose"
        echo "File size: $(stat -c%s /usr/local/bin/docker-compose) bytes"
        echo "File permissions: $(stat -c%A /usr/local/bin/docker-compose)"
        echo ""
        echo "First 200 characters of the file:"
        head -c 200 /usr/local/bin/docker-compose
        echo ""
        echo ""
        echo "File type:"
        file /usr/local/bin/docker-compose
        echo ""
    else
        echo "❌ /usr/local/bin/docker-compose does not exist"
    fi
    
    echo "=== Checking docker compose plugin ==="
    if docker compose version >/dev/null 2>&1; then
        echo "✅ Docker Compose plugin is available"
        docker compose version
    else
        echo "❌ Docker Compose plugin not available"
    fi
    
    echo ""
    echo "=== Available docker compose commands ==="
    which docker-compose 2>/dev/null || echo "docker-compose not found in PATH"
    command -v docker-compose 2>/dev/null || echo "docker-compose command not found"
    
    echo ""
    echo "=== Docker plugins directory ==="
    ls -la /usr/libexec/docker/cli-plugins/ 2>/dev/null || echo "Plugin directory not found"
    
    echo ""
    echo "=== PATH ==="
    echo $PATH
' 