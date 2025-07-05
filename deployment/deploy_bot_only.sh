#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load configuration
if [ -f "deploy.env" ]; then
    echo -e "${BLUE}📄 Loading configuration from deploy.env...${NC}"
    export $(grep -v '^#' "deploy.env" | grep -v '^$' | xargs)
    echo -e "${GREEN}✅ Configuration loaded${NC}"
fi

# Default values
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_HOST="${REMOTE_HOST:-64.227.69.138}"
SSH_KEY="${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}"
REMOTE_DEPLOY_DIR="${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}"

echo -e "${BLUE}🤖 CloverdashBot Telegram Bot Deployment${NC}"
echo -e "${YELLOW}Target: $REMOTE_USER@$REMOTE_HOST${NC}"
echo -e "${YELLOW}SSH Key: $SSH_KEY${NC}"
echo -e "${YELLOW}Deploy Dir: $REMOTE_DEPLOY_DIR${NC}"
echo ""

# Prepare SSH command
SSH_CMD="ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=20 -o ConnectTimeout=60 -o TCPKeepAlive=yes"
if [ -n "$SSH_KEY" ] && [ -f "$(eval echo $SSH_KEY)" ]; then
    SSH_CMD="$SSH_CMD -i $(eval echo $SSH_KEY)"
fi

# Test SSH connection
echo -e "${BLUE}🔐 Testing SSH connection...${NC}"
if ! $SSH_CMD -o ConnectTimeout=10 $REMOTE_USER@$REMOTE_HOST 'exit 0' 2>/dev/null; then
    echo -e "${RED}❌ SSH connection failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

# Check if bot .env file exists
if [ ! -f "../telegram-bot/.env" ]; then
    echo -e "${RED}❌ Telegram bot .env file not found${NC}"
    echo -e "${RED}Create telegram-bot/.env file with required configuration${NC}"
    exit 1
fi

# Copy telegram-bot files
echo -e "${BLUE}📁 Copying telegram-bot files...${NC}"
rsync -avz --exclude-from=../.deployignore -e "$SSH_CMD" ../telegram-bot/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR/telegram-bot/

# Configure and start bot
echo -e "${BLUE}⚙️  Configuring and starting bot...${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    # Create shared network if it doesn't exist
    docker network create cloverdash-network 2>/dev/null || echo 'Network already exists'
    
    cd $REMOTE_DEPLOY_DIR/telegram-bot
    
    # Set backend URL to container name for inter-container communication
    sed -i 's|BACKEND_URL=.*|BACKEND_URL=http://cloverdash_backend:8000|' .env 2>/dev/null || true
    
    # Stop any existing bot
    docker-compose down --remove-orphans 2>/dev/null || true
    
    echo 'Building telegram bot Docker image...'
    if ! timeout 180 docker-compose build; then
        echo 'Build failed with cache, trying without cache...'
        timeout 300 docker-compose build --no-cache
    fi
    
    echo 'Starting telegram bot services...'
    docker-compose up -d
    
    # Wait for bot to start
    echo 'Waiting for telegram bot to start...'
    sleep 10
"

# Check if bot deployed successfully
if $SSH_CMD $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose ps | grep -q 'Up'"; then
    echo -e "${GREEN}✅ Telegram Bot deployed successfully${NC}"
    echo ""
    echo -e "${BLUE}🎉 Bot is now running!${NC}"
    echo -e "${YELLOW}Test your bot by sending /start in Telegram${NC}"
    echo ""
    echo -e "${BLUE}📊 Useful commands:${NC}"
    echo -e "${YELLOW}# Check bot status:${NC}"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose ps'"
    echo ""
    echo -e "${YELLOW}# View bot logs:${NC}"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose logs -f'"
else
    echo -e "${RED}❌ Telegram Bot deployment failed${NC}"
    echo -e "${YELLOW}Checking bot logs:${NC}"
    $SSH_CMD $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose logs --tail=20"
    exit 1
fi 