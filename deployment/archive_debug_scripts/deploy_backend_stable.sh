#!/bin/bash

# Stable backend deployment using screen session
# This script is resilient to SSH disconnections

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load configuration
if [ -f "deploy.env" ]; then
    source deploy.env
fi

# Configuration with defaults
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_HOST="${REMOTE_HOST:-64.227.69.138}"
SSH_KEY="${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}"
REMOTE_DEPLOY_DIR="${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}"
SESSION_NAME="backend-deploy"

# Prepare SSH command
SSH_CMD="ssh -i $SSH_KEY -o ServerAliveInterval=30 -o ServerAliveCountMax=3"

echo -e "${BLUE}🚀 Stable Backend Deployment${NC}"
echo -e "${YELLOW}Target: $REMOTE_USER@$REMOTE_HOST${NC}"
echo -e "${YELLOW}Session: $SESSION_NAME${NC}"
echo ""

# Function to check if screen session exists
check_session() {
    $SSH_CMD $REMOTE_USER@$REMOTE_HOST "screen -list | grep -q $SESSION_NAME"
}

# Function to copy files
copy_files() {
    echo -e "${BLUE}📁 Copying backend files...${NC}"
    
    # Copy backend files
    RSYNC_CMD="rsync -e 'ssh -i $SSH_KEY' -av --exclude-from=../.deployignore"
    $RSYNC_CMD ../backend/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR/backend/
    
    # Copy remote deployment script
    scp -i $SSH_KEY deploy_backend_remote.sh $REMOTE_USER@$REMOTE_HOST:/tmp/
    $SSH_CMD $REMOTE_USER@$REMOTE_HOST "chmod +x /tmp/deploy_backend_remote.sh"
    
    echo -e "${GREEN}✅ Files copied successfully${NC}"
}

# Function to start deployment in screen
start_deployment() {
    echo -e "${BLUE}🏗️  Starting deployment in screen session...${NC}"
    
    $SSH_CMD $REMOTE_USER@$REMOTE_HOST "
        # Kill existing session if it exists
        screen -S $SESSION_NAME -X quit 2>/dev/null || true
        
        # Start new screen session with deployment
        screen -dmS $SESSION_NAME bash -c '
            echo \"[$(date)] Starting backend deployment in screen session...\"
            /tmp/deploy_backend_remote.sh
            echo \"[$(date)] Deployment completed. Session will remain active.\"
            echo \"Press Ctrl+C to exit or Ctrl+A D to detach.\"
            bash  # Keep session alive
        '
    "
    
    echo -e "${GREEN}✅ Deployment started in screen session: $SESSION_NAME${NC}"
}

# Function to monitor deployment
monitor_deployment() {
    echo -e "${BLUE}📊 Monitoring deployment...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to detach from monitoring (deployment will continue)${NC}"
    echo -e "${YELLOW}Use: $0 --attach to reattach later${NC}"
    echo ""
    
    # Monitor log file
    $SSH_CMD $REMOTE_USER@$REMOTE_HOST "
        echo 'Waiting for log file to appear...'
        while [ ! -f /tmp/backend_deploy.log ]; do
            sleep 1
        done
        
        echo 'Following deployment log (Ctrl+C to detach):'
        tail -f /tmp/backend_deploy.log
    "
}

# Function to attach to existing session
attach_session() {
    echo -e "${BLUE}🔗 Attaching to existing deployment session...${NC}"
    $SSH_CMD $REMOTE_USER@$REMOTE_HOST -t "screen -r $SESSION_NAME"
}

# Function to check deployment status
check_status() {
    echo -e "${BLUE}📊 Checking deployment status...${NC}"
    
    if check_session; then
        echo -e "${YELLOW}📺 Screen session '$SESSION_NAME' is active${NC}"
        
        # Check if log file exists
        if $SSH_CMD $REMOTE_USER@$REMOTE_HOST "[ -f /tmp/backend_deploy.log ]"; then
            echo -e "${BLUE}📋 Recent deployment log:${NC}"
            $SSH_CMD $REMOTE_USER@$REMOTE_HOST "tail -20 /tmp/backend_deploy.log"
        else
            echo -e "${YELLOW}⏳ Deployment log not found yet...${NC}"
        fi
    else
        echo -e "${GREEN}✅ No active deployment session${NC}"
    fi
    
    # Check if backend is running
    echo -e "${BLUE}🏥 Backend health check:${NC}"
    if $SSH_CMD $REMOTE_USER@$REMOTE_HOST "curl -s http://localhost:8000/health/ >/dev/null 2>&1"; then
        echo -e "${GREEN}✅ Backend is running and healthy${NC}"
        $SSH_CMD $REMOTE_USER@$REMOTE_HOST "curl -s http://localhost:8000/health/ | jq . 2>/dev/null || curl -s http://localhost:8000/health/"
    else
        echo -e "${RED}❌ Backend is not responding${NC}"
    fi
}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --start         Start new deployment (default)"
    echo "  --monitor       Monitor active deployment"
    echo "  --attach        Attach to existing screen session"
    echo "  --status        Check deployment status"
    echo "  --logs          View deployment logs"
    echo "  --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0              # Start deployment"
    echo "  $0 --monitor    # Monitor deployment progress"
    echo "  $0 --attach     # Attach to deployment session"
    echo "  $0 --status     # Check current status"
}

# Parse command line arguments
case "${1:-}" in
    --attach)
        attach_session
        exit 0
        ;;
    --status)
        check_status
        exit 0
        ;;
    --monitor)
        monitor_deployment
        exit 0
        ;;
    --logs)
        echo -e "${BLUE}📋 Viewing deployment logs...${NC}"
        $SSH_CMD $REMOTE_USER@$REMOTE_HOST "tail -f /tmp/backend_deploy.log" 2>/dev/null || echo "No logs found"
        exit 0
        ;;
    --help)
        usage
        exit 0
        ;;
    --start|"")
        # Continue with deployment
        ;;
    *)
        echo "Unknown option: $1"
        usage
        exit 1
        ;;
esac

# Main deployment flow
echo -e "${BLUE}🚀 Starting stable backend deployment...${NC}"

# Check if deployment is already running
if check_session; then
    echo -e "${YELLOW}⚠️  Deployment session already running${NC}"
    echo -e "${YELLOW}Use: $0 --attach to connect to it${NC}"
    echo -e "${YELLOW}Use: $0 --status to check status${NC}"
    exit 1
fi

# Copy files and start deployment
copy_files
start_deployment

echo ""
echo -e "${GREEN}🎉 Deployment started successfully!${NC}"
echo ""
echo -e "${BLUE}📋 What's next:${NC}"
echo -e "${YELLOW}  Monitor progress: $0 --monitor${NC}"
echo -e "${YELLOW}  Attach to session: $0 --attach${NC}"
echo -e "${YELLOW}  Check status: $0 --status${NC}"
echo -e "${YELLOW}  View logs: $0 --logs${NC}"
echo ""
echo -e "${GREEN}💡 The deployment will continue even if you disconnect!${NC}"

# Offer to start monitoring
echo ""
read -p "Start monitoring now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    monitor_deployment
fi 