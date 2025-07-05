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
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/your_ssh_key}
REMOTE_USER=${REMOTE_USER:-root}
REMOTE_HOST=${REMOTE_HOST:-YOUR_SERVER_IP}
REMOTE_DEPLOY_DIR=${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}

# Prepare SSH command
SSH_CMD="ssh"
if [ -n "$SSH_KEY_PATH" ] && [ "$SSH_KEY_PATH" != "" ]; then
    SSH_KEY_EXPANDED=$(eval echo $SSH_KEY_PATH)
    if [ -f "$SSH_KEY_EXPANDED" ]; then
        SSH_CMD="ssh -i $SSH_KEY_EXPANDED"
    else
        echo -e "${YELLOW}⚠️  SSH key not found: $SSH_KEY_PATH, using default SSH configuration${NC}"
        SSH_CMD="ssh"
    fi
fi

echo -e "${BLUE}🔧 Docker Compose Fix Tool${NC}"
echo -e "${YELLOW}Target: $REMOTE_USER@$REMOTE_HOST${NC}"
echo ""

echo -e "${BLUE}🧹 Cleaning up broken docker-compose installation...${NC}"

$SSH_CMD $REMOTE_USER@$REMOTE_HOST '
    # Remove broken docker-compose
    rm -f /usr/local/bin/docker-compose
    
    echo "Checking Docker installation..."
    docker --version
    
    echo "Checking for Docker Compose plugin..."
    if docker compose version >/dev/null 2>&1; then
        echo "✅ Docker Compose plugin is available"
        
        # Create wrapper script for docker-compose command
        cat > /usr/local/bin/docker-compose << '\''EOF'\''
#!/bin/bash
exec docker compose "$@"
EOF
        chmod +x /usr/local/bin/docker-compose
        
        echo "✅ Created docker-compose wrapper"
        
    else
        echo "Installing standalone Docker Compose..."
        
        # Download latest stable version
        curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        
        # Verify installation
        if /usr/local/bin/docker-compose version >/dev/null 2>&1; then
            echo "✅ Standalone Docker Compose installed successfully"
        else
            echo "❌ Failed to install standalone Docker Compose"
            echo "File contents (first 100 chars):"
            head -c 100 /usr/local/bin/docker-compose
            exit 1
        fi
    fi
    
    echo "Final verification:"
    docker-compose version
    
    echo "✅ Docker Compose is ready"
'

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker Compose fixed successfully!${NC}"
    echo ""
    echo -e "${BLUE}🚀 You can now retry deployment:${NC}"
    echo "./deploy_all.sh"
else
    echo -e "${RED}❌ Failed to fix Docker Compose${NC}"
    echo ""
    echo -e "${BLUE}🔍 Debug commands:${NC}"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'docker --version'"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'docker compose version'"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'ls -la /usr/local/bin/docker-compose'"
fi 