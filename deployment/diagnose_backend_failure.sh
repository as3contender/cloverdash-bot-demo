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
        echo -e "${YELLOW}⚠️  SSH key not found: $SSH_KEY_PATH, using default SSH configuration${NC}"
        SSH_CMD="ssh"
    fi
fi

echo -e "${BLUE}🔍 Backend Failure Diagnostic Tool${NC}"
echo -e "${YELLOW}Target: $REMOTE_USER@$REMOTE_HOST${NC}"
echo ""

echo -e "${BLUE}📊 Step 1: Check Docker Container Status${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DEPLOY_DIR/backend 2>/dev/null || {
        echo '❌ Backend directory not found: $REMOTE_DEPLOY_DIR/backend'
        exit 1
    }
    
    echo '=== Docker Compose Status ==='
    docker-compose ps
    echo ''
    
    echo '=== Container Health ==='
    docker-compose top 2>/dev/null || echo 'No running containers'
    echo ''
"

echo ""
echo -e "${BLUE}📋 Step 2: Check Backend Logs${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DEPLOY_DIR/backend
    echo '=== Last 30 lines of backend logs ==='
    docker-compose logs --tail=30
    echo ''
"

echo ""
echo -e "${BLUE}🌐 Step 3: Test Network Connectivity${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    echo '=== Docker Networks ==='
    docker network ls
    echo ''
    
    echo '=== Port 8000 Status ==='
    ss -tlnp | grep ':8000' || echo 'Port 8000 not listening'
    echo ''
    
    echo '=== Test internal connectivity ==='
    curl -v http://localhost:8000/ 2>&1 | head -10 || echo 'Failed to connect to localhost:8000'
    echo ''
"

echo ""
echo -e "${BLUE}🗄️ Step 4: Check Database Connectivity${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DEPLOY_DIR/backend
    
    echo '=== Environment Variables ==='
    docker-compose exec -T backend env | grep -E '(DATABASE|OPENAI)' 2>/dev/null || echo 'Backend container not running'
    echo ''
    
    echo '=== Test PostgreSQL connectivity ==='
    # Try to connect to both databases
    timeout 10 nc -zv localhost 5432 && echo '✅ PostgreSQL port 5432 is reachable' || echo '❌ PostgreSQL port 5432 not reachable'
    echo ''
"

echo ""
echo -e "${BLUE}🔧 Step 5: Check Backend Configuration${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DEPLOY_DIR/backend
    
    echo '=== .env file contents (sensitive data hidden) ==='
    if [ -f .env ]; then
        sed 's/=.*/=***/' .env
    else
        echo '❌ .env file not found'
    fi
    echo ''
    
    echo '=== docker-compose.yml ==='
    cat docker-compose.yml 2>/dev/null || echo 'docker-compose.yml not found'
    echo ''
"

echo ""
echo -e "${BLUE}🎯 Step 6: Manual Health Check${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    echo '=== Try direct health check ==='
    curl -v http://localhost:8000/health/ 2>&1 || echo 'Health check failed'
    echo ''
    
    echo '=== Try root endpoint ==='
    curl -v http://localhost:8000/ 2>&1 || echo 'Root endpoint failed'
    echo ''
"

echo ""
echo -e "${BLUE}💡 Step 7: Suggested Fixes${NC}"
echo -e "${YELLOW}Based on common issues:${NC}"
echo ""
echo -e "${GREEN}1. Database Connection Issues:${NC}"
echo "   # Check if PostgreSQL is running:"
echo "   $SSH_CMD $REMOTE_USER@$REMOTE_HOST 'systemctl status postgresql'"
echo ""
echo "   # Check database users and permissions:"
echo "   $SSH_CMD $REMOTE_USER@$REMOTE_HOST 'sudo -u postgres psql -c \"\\du\"'"
echo ""
echo -e "${GREEN}2. Environment Variables:${NC}"
echo "   # Recreate .env with correct database hosts:"
echo "   $SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/backend && sed -i \"s/DATABASE_HOST=.*/DATABASE_HOST=localhost/\" .env'"
echo ""
echo -e "${GREEN}3. Container Issues:${NC}"
echo "   # Restart backend containers:"
echo "   $SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/backend && docker-compose down && docker-compose up -d'"
echo ""
echo -e "${GREEN}4. Build Issues:${NC}"
echo "   # Rebuild from scratch:"
echo "   $SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/backend && docker-compose down && docker-compose build --no-cache && docker-compose up -d'"
echo ""
echo -e "${GREEN}5. OpenAI API Issues:${NC}"
echo "   # Test OpenAI API key:"
echo "   $SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/backend && docker-compose exec backend python -c \"import openai; print(\\\"OpenAI configured\\\")\"'"

echo ""
echo -e "${BLUE}🚀 Quick Fix Command:${NC}"
echo "# To restart and check logs:"
echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/backend && docker-compose restart && sleep 10 && docker-compose logs --tail=20'" 