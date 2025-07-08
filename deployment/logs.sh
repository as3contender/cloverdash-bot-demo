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
    # Expand tilde in SSH key path and check if file exists
    SSH_KEY_EXPANDED=$(eval echo $SSH_KEY_PATH)
    if [ -f "$SSH_KEY_EXPANDED" ]; then
        SSH_CMD="ssh -i $SSH_KEY_EXPANDED"
    else
        echo -e "${YELLOW}⚠️  SSH key not found: $SSH_KEY_PATH, using default SSH configuration${NC}"
        SSH_CMD="ssh"
    fi
fi

usage() {
    echo "Usage: $0 [OPTIONS] [SERVICE]"
    echo ""
    echo "Services:"
    echo "  backend    Show backend API logs"
    echo "  bot        Show telegram bot logs"
    echo "  all        Show all services status"
    echo ""
    echo "Options:"
    echo "  -f, --follow    Follow log output (tail -f)"
    echo "  -n NUM          Show last NUM lines (default: 50)"
    echo "  --status        Show services status"
    echo "  --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 backend              # Show last 50 lines of backend logs"
    echo "  $0 bot -f               # Follow bot logs in real time"
    echo "  $0 backend -n 100       # Show last 100 lines of backend logs"
    echo "  $0 --status             # Show all services status"
}

# Parse command line arguments
FOLLOW=false
LINES=50
SERVICE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n)
            LINES="$2"
            shift 2
            ;;
        --status)
            SERVICE="status"
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        backend|bot|all)
            SERVICE="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

if [ -z "$SERVICE" ]; then
    echo -e "${RED}❌ Please specify a service${NC}"
    usage
    exit 1
fi

echo -e "${BLUE}🔍 CloverdashBot Logs Viewer${NC}"
echo -e "${YELLOW}Target: $REMOTE_USER@$REMOTE_HOST${NC}"
echo -e "${YELLOW}Deploy Dir: $REMOTE_DEPLOY_DIR${NC}"
echo ""

case $SERVICE in
    backend)
        echo -e "${BLUE}📊 Backend API Logs${NC}"
        if [ "$FOLLOW" = true ]; then
            echo -e "${YELLOW}Following logs (Ctrl+C to stop)...${NC}"
            $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" \
                "cd $REMOTE_DEPLOY_DIR/backend && docker-compose logs -f"
        else
            echo -e "${YELLOW}Showing last $LINES lines...${NC}"
            $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" \
                "cd $REMOTE_DEPLOY_DIR/backend && docker-compose logs --tail=$LINES"
        fi
        ;;
    
    bot)
        echo -e "${BLUE}🤖 Telegram Bot Logs${NC}"
        if [ "$FOLLOW" = true ]; then
            echo -e "${YELLOW}Following logs (Ctrl+C to stop)...${NC}"
            $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" \
                "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose logs -f"
        else
            echo -e "${YELLOW}Showing last $LINES lines...${NC}"
            $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" \
                "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose logs --tail=$LINES"
        fi
        ;;
    
    status)
        echo -e "${BLUE}📊 Services Status${NC}"
        $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" \
            "cd $REMOTE_DEPLOY_DIR && find . -name 'docker-compose*.yml' -exec echo 'Checking: {}' \\; -exec docker-compose -f {} ps \\;"
        ;;
    
    all)
        echo -e "${BLUE}📊 All Services Overview${NC}"
        echo ""
        echo -e "${YELLOW}=== Backend Status ===${NC}"
        $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" \
            "cd $REMOTE_DEPLOY_DIR/backend && docker-compose ps"
        
        echo ""
        echo -e "${YELLOW}=== Bot Status ===${NC}"
        $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" \
            "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose ps"
        
        echo ""
        echo -e "${YELLOW}=== Recent Backend Logs ===${NC}"
        $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" \
            "cd $REMOTE_DEPLOY_DIR/backend && docker-compose logs --tail=10"
        
        echo ""
        echo -e "${YELLOW}=== Recent Bot Logs ===${NC}"
        $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" \
            "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose logs --tail=10"
        ;;
esac 