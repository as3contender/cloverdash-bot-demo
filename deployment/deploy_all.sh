#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to load environment variables from file
load_env() {
    if [ -f "$1" ]; then
        echo -e "${BLUE}📄 Loading configuration from $1...${NC}"
        export $(grep -v '^#' "$1" | grep -v '^$' | xargs)
        echo -e "${GREEN}✅ Configuration loaded${NC}"
    fi
}

# Function to check and install Docker
install_docker() {
    local ssh_cmd="$1"
    local remote_user="$2"
    local remote_host="$3"
    
    echo -e "${BLUE}🐳 Checking Docker installation...${NC}"
    
    $ssh_cmd $remote_user@$remote_host "
        if command -v docker >/dev/null 2>&1; then
            echo '✅ Docker is already installed'
            docker --version
        else
            echo '📦 Installing Docker...'
            
            # Update package index
            apt-get update -y >/dev/null 2>&1 || yum update -y >/dev/null 2>&1 || true
            
            # Install Docker using official script
            curl -fsSL https://get.docker.com -o get-docker.sh
            if [ -f get-docker.sh ]; then
                sh get-docker.sh
                rm get-docker.sh
                
                # Enable and start Docker service
                systemctl enable docker >/dev/null 2>&1 || true
                systemctl start docker >/dev/null 2>&1 || true
                
                # Add current user to docker group (if not root)
                if [ \"\$USER\" != \"root\" ]; then
                    usermod -aG docker \$USER >/dev/null 2>&1 || true
                fi
                
                # Verify installation
                if command -v docker >/dev/null 2>&1; then
                    echo '✅ Docker installed successfully'
                    docker --version
                else
                    echo '❌ Docker installation failed'
                    exit 1
                fi
            else
                echo '❌ Failed to download Docker installation script'
                exit 1
            fi
        fi
    "
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Docker installation failed${NC}"
        exit 1
    fi
}

# Function to check and install docker-compose
install_docker_compose() {
    local ssh_cmd="$1"
    local remote_user="$2"
    local remote_host="$3"
    
    echo -e "${BLUE}🔧 Checking docker-compose installation...${NC}"
    
    $ssh_cmd $remote_user@$remote_host "
        # Check if docker-compose is already available
        if docker-compose --version >/dev/null 2>&1; then
            echo '✅ docker-compose is already installed'
            docker-compose --version
            exit 0
        fi
        
        # Check if docker compose plugin is available
        if docker compose version >/dev/null 2>&1; then
            echo '✅ Docker Compose plugin is available'
            docker compose version
            
            # Create compatibility symlink
            echo '🔗 Creating docker-compose compatibility link...'
            cat > /usr/local/bin/docker-compose << 'EOF'
#!/bin/bash
exec docker compose \"\$@\"
EOF
            chmod +x /usr/local/bin/docker-compose
            
            # Verify the symlink works
            if docker-compose --version >/dev/null 2>&1; then
                echo '✅ docker-compose compatibility link created successfully'
                docker-compose --version
            else
                echo '❌ Failed to create docker-compose compatibility link'
                exit 1
            fi
            exit 0
        fi
        
        # Neither docker-compose nor docker compose plugin available, install standalone version
        echo '📦 Installing docker-compose standalone...'
        
        # Get the latest stable version
        COMPOSE_VERSION=\"2.24.6\"
        ARCH=\$(uname -m)
        OS=\$(uname -s)
        
        # Download docker-compose
        echo \"📥 Downloading docker-compose v\$COMPOSE_VERSION for \$OS-\$ARCH...\"
        curl -L \"https://github.com/docker/compose/releases/download/v\$COMPOSE_VERSION/docker-compose-\$OS-\$ARCH\" -o /usr/local/bin/docker-compose
        
        if [ ! -f /usr/local/bin/docker-compose ]; then
            echo '❌ Failed to download docker-compose'
            exit 1
        fi
        
        # Make it executable
        chmod +x /usr/local/bin/docker-compose
        
        # Create symlink in /usr/bin for better PATH compatibility
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose 2>/dev/null || true
        
        # Verify installation
        if docker-compose --version >/dev/null 2>&1; then
            echo '✅ docker-compose installed successfully'
            docker-compose --version
        else
            echo '❌ docker-compose installation failed'
            echo 'Attempting to fix permissions and PATH...'
            
            # Try fixing permissions
            chmod 755 /usr/local/bin/docker-compose
            
            # Test again
            if /usr/local/bin/docker-compose --version >/dev/null 2>&1; then
                echo '✅ docker-compose fixed and working'
                /usr/local/bin/docker-compose --version
                
                # Add to PATH if needed
                if ! echo \$PATH | grep -q '/usr/local/bin'; then
                    echo 'export PATH=\"/usr/local/bin:\$PATH\"' >> /etc/environment
                    echo '📝 Added /usr/local/bin to PATH'
                fi
            else
                echo '❌ docker-compose still not working after fixes'
                ls -la /usr/local/bin/docker-compose
                file /usr/local/bin/docker-compose
                exit 1
            fi
        fi
    "
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ docker-compose installation failed${NC}"
        exit 1
    fi
}

# Function to verify Docker environment
verify_docker_environment() {
    local ssh_cmd="$1"
    local remote_user="$2"
    local remote_host="$3"
    
    echo -e "${BLUE}🔍 Verifying Docker environment...${NC}"
    
    $ssh_cmd $remote_user@$remote_host "
        echo '🐳 Docker version:'
        docker --version
        
        echo '📊 Docker system info:'
        docker info --format 'Version: {{.ServerVersion}}' 2>/dev/null || echo 'Docker daemon may not be running'
        
        echo '🔧 docker-compose version:'
        docker-compose --version
        
        echo '✅ Docker environment verification completed'
    "
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Docker environment is ready${NC}"
    else
        echo -e "${RED}❌ Docker environment verification failed${NC}"
        exit 1
    fi
}

# Load deployment configuration
load_env "deploy.env"

# Default values (can be overridden by deploy.env or command line)
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_HOST="${REMOTE_HOST:-64.227.69.138}"
SSH_KEY="${SSH_KEY_PATH:-~/.ssh/id_ed25519_do_cloverdash-bot}"
DEPLOY_BACKEND="${DEPLOY_BACKEND:-true}"
DEPLOY_BOT="${DEPLOY_BOT:-true}"
REMOTE_DEPLOY_DIR="${REMOTE_DEPLOY_DIR:-/opt/cloverdash-bot}"

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Configuration:"
    echo "  Create deploy.env file with your settings (see deploy.env.example)"
    echo "  Or use command line options to override defaults"
    echo ""
    echo "Options:"
    echo "  -u, --user USER     SSH username (default from deploy.env or 'root')"
    echo "  -h, --host HOST     Server hostname/IP (default from deploy.env or '64.227.69.138')"
    echo "  -k, --key PATH      SSH private key path (default from deploy.env or '~/.ssh/id_ed25519_do_cloverdash-bot')"
    echo "  --backend-only      Deploy only backend API"
    echo "  --bot-only          Deploy only Telegram bot"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                               # Deploy using deploy.env configuration"
    echo "  $0 --backend-only                # Deploy only backend API"
    echo "  $0 --bot-only                    # Deploy only bot"
    echo "  $0 -h your-server.com -u ubuntu # Override server and user"
    echo ""
    echo "Configuration file (deploy.env):"
    echo "  REMOTE_HOST=your-server.com"
    echo "  REMOTE_USER=ubuntu"
    echo "  SSH_KEY_PATH=~/.ssh/your-key"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--user)
            REMOTE_USER="$2"
            shift 2
            ;;
        -h|--host)
            REMOTE_HOST="$2"
            shift 2
            ;;
        -k|--key)
            SSH_KEY="$2"
            shift 2
            ;;
        --backend-only)
            DEPLOY_BACKEND=true
            DEPLOY_BOT=false
            shift
            ;;
        --bot-only)
            DEPLOY_BACKEND=false
            DEPLOY_BOT=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required configuration
if [ -z "$REMOTE_HOST" ]; then
    echo -e "${RED}❌ Error: REMOTE_HOST is required${NC}"
    echo -e "${RED}Set it in deploy.env file or use -h option${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 CloverdashBot Full Stack Deployment${NC}"
echo -e "${YELLOW}Target: $REMOTE_USER@$REMOTE_HOST${NC}"
echo -e "${YELLOW}SSH Key: $SSH_KEY${NC}"
echo -e "${YELLOW}Deploy Dir: $REMOTE_DEPLOY_DIR${NC}"
echo -e "${YELLOW}Backend API: $([ "$DEPLOY_BACKEND" = true ] && echo "✅ Will deploy" || echo "⏭️  Skipped")${NC}"
echo -e "${YELLOW}Telegram Bot: $([ "$DEPLOY_BOT" = true ] && echo "✅ Will deploy" || echo "⏭️  Skipped")${NC}"
echo ""

# Prepare SSH command
SSH_CMD="ssh"
if [ -n "$SSH_KEY" ] && [ "$SSH_KEY" != "" ]; then
    # Expand tilde in SSH key path and check if file exists
    SSH_KEY_EXPANDED=$(eval echo $SSH_KEY)
    if [ -f "$SSH_KEY_EXPANDED" ]; then
        SSH_CMD="ssh -i $SSH_KEY_EXPANDED"
        echo -e "${YELLOW}Using SSH key: $SSH_KEY${NC}"
    else
        echo -e "${YELLOW}⚠️  SSH key not found: $SSH_KEY, using default SSH configuration${NC}"
        SSH_CMD="ssh"
    fi
else
    echo -e "${YELLOW}Using default SSH configuration (no key specified)${NC}"
fi

# Test SSH connection first
echo -e "${BLUE}🔐 Testing SSH connection...${NC}"
if ! $SSH_CMD -o ConnectTimeout=10 $REMOTE_USER@$REMOTE_HOST 'exit 0' 2>/dev/null; then
    echo -e "${RED}❌ SSH connection failed${NC}"
    echo -e "${RED}Please check:${NC}"
    echo -e "${RED}  - Server is accessible: $REMOTE_HOST${NC}"
    echo -e "${RED}  - User has access: $REMOTE_USER${NC}"
    if [ -n "$SSH_KEY" ]; then
        echo -e "${RED}  - SSH key exists: $SSH_KEY${NC}"
    else
        echo -e "${RED}  - SSH configuration and keys${NC}"
    fi
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

# Install and verify Docker environment
echo ""
install_docker "$SSH_CMD" "$REMOTE_USER" "$REMOTE_HOST"
install_docker_compose "$SSH_CMD" "$REMOTE_USER" "$REMOTE_HOST"
verify_docker_environment "$SSH_CMD" "$REMOTE_USER" "$REMOTE_HOST"
echo ""

# Check if .env files exist
if [ "$DEPLOY_BACKEND" = true ] && [ ! -f "backend/.env" ]; then
    echo -e "${RED}❌ Backend .env file not found${NC}"
    echo -e "${RED}Create backend/.env file with required configuration${NC}"
    echo -e "${RED}See backend/env_example.txt for reference${NC}"
    exit 1
fi

if [ "$DEPLOY_BOT" = true ] && [ ! -f "telegram-bot/.env" ]; then
    echo -e "${RED}❌ Telegram bot .env file not found${NC}"
    echo -e "${RED}Create telegram-bot/.env file with required configuration${NC}"
    echo -e "${RED}Example: TELEGRAM_TOKEN=your_bot_token${NC}"
    echo -e "${RED}         BACKEND_URL=http://localhost:8000${NC}"
    exit 1
fi

# Clean existing deployments
echo -e "${BLUE}🧹 Cleaning existing deployments...${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DEPLOY_DIR 2>/dev/null || true
    find . -name \"docker-compose*.yml\" -exec docker-compose -f {} down --remove-orphans \\; 2>/dev/null || true
    docker system prune -af --volumes 2>/dev/null || true
    rm -rf $REMOTE_DEPLOY_DIR 2>/dev/null || true
    mkdir -p $REMOTE_DEPLOY_DIR
" 2>/dev/null || true
echo -e "${GREEN}✅ Cleanup completed${NC}"
echo ""

# Deploy backend API
if [ "$DEPLOY_BACKEND" = true ]; then
    echo -e "${BLUE}📊 Step 1: Deploying Backend API...${NC}"
    
    # Create backend deployment package
    echo -e "${YELLOW}📦 Creating backend deployment package...${NC}"
    
    # Copy backend files
    echo -e "${YELLOW}📁 Copying backend files...${NC}"
    SCP_CMD=$(echo $SSH_CMD | sed 's/ssh/scp/')
    $SCP_CMD -r backend/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR/
    
    # Modify .env for production
    echo -e "${YELLOW}⚙️  Configuring backend for production...${NC}"
    $SSH_CMD $REMOTE_USER@$REMOTE_HOST "
        cd $REMOTE_DEPLOY_DIR/backend
        
        # Set localhost for database connections
        sed -i "s/APP_DATABASE_HOST=.*/APP_DATABASE_HOST=localhost/" .env 2>/dev/null || true
        sed -i "s/DATA_DATABASE_HOST=.*/DATA_DATABASE_HOST=localhost/" .env 2>/dev/null || true
        
        # Set API host for production
        sed -i "s/API_HOST=.*/API_HOST=0.0.0.0/" .env 2>/dev/null || true
        sed -i "s/API_PORT=.*/API_PORT=8000/" .env 2>/dev/null || true
        
        # Generate new secret key for production
        if command -v python3 >/dev/null 2>&1; then
            NEW_SECRET=$(python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")
            sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env 2>/dev/null || true
        fi
        
        echo "Docker and docker-compose are ready for deployment..."
        
        # Build and start backend
        docker-compose down --remove-orphans 2>/dev/null || true
        docker-compose build --no-cache
        docker-compose up -d
        
        # Wait for backend to be ready
        echo "Waiting for backend to start..."
        for i in {1..30}; do
            if curl -s http://localhost:8000/api/v1/health >/dev/null 2>&1; then
                echo "Backend is ready!"
                break
            fi
            sleep 2
        done
    "
    
    # Check if backend deployed successfully
    if $SSH_CMD $REMOTE_USER@$REMOTE_HOST 'curl -s http://localhost:8000/api/v1/health >/dev/null 2>&1'; then
        echo -e "${GREEN}✅ Backend API deployed successfully${NC}"
    else
        echo -e "${RED}❌ Backend API deployment failed${NC}"
        echo -e "${YELLOW}Checking backend logs:${NC}"
        $SSH_CMD $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DEPLOY_DIR/backend && docker-compose logs --tail=20"
        exit 1
    fi
    
    echo ""
else
    echo -e "${YELLOW}⏭️  Skipping Backend API deployment${NC}"
fi

# Deploy Telegram bot
if [ "$DEPLOY_BOT" = true ]; then
    echo -e "${BLUE}🤖 Step 2: Deploying Telegram Bot...${NC}"
    
    # Copy telegram-bot files
    echo -e "${YELLOW}📁 Copying telegram-bot files...${NC}"
    $SCP_CMD -r telegram-bot/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR/
    
    # Configure bot for production
    echo -e "${YELLOW}⚙️  Configuring bot for production...${NC}"
    $SSH_CMD $REMOTE_USER@$REMOTE_HOST "
        cd $REMOTE_DEPLOY_DIR/telegram-bot
        
        # Set backend URL to localhost
        sed -i "s|BACKEND_URL=.*|BACKEND_URL=http://localhost:8000|" .env 2>/dev/null || true
        
        # Build and start bot
        docker-compose down --remove-orphans 2>/dev/null || true
        docker-compose build --no-cache
        docker-compose up -d
        
        # Wait for bot to start
        echo "Waiting for telegram bot to start..."
        sleep 10
    "
    
    # Check if bot deployed successfully
    if $SSH_CMD $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose ps | grep -q \"Up\""; then
        echo -e "${GREEN}✅ Telegram Bot deployed successfully${NC}"
    else
        echo -e "${RED}❌ Telegram Bot deployment failed${NC}"
        echo -e "${YELLOW}Checking bot logs:${NC}"
        $SSH_CMD $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose logs --tail=20"
        exit 1
    fi
    
    echo ""
else
    echo -e "${YELLOW}⏭️  Skipping Telegram Bot deployment${NC}"
fi

# Final summary
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Your services are now running:${NC}"

if [ "$DEPLOY_BACKEND" = true ]; then
    echo -e "${YELLOW}🔗 Backend API:${NC}"
    echo -e "   • API: http://$REMOTE_HOST:8000"
    echo -e "   • Docs: http://$REMOTE_HOST:8000/docs"
    echo -e "   • Health: http://$REMOTE_HOST:8000/api/v1/health"
fi

if [ "$DEPLOY_BOT" = true ]; then
    echo -e "${YELLOW}🤖 Telegram Bot:${NC}"
    echo -e "   • Status: Running and ready for messages"
    echo -e "   • Test: Send /start to your bot in Telegram"
fi

echo ""
echo -e "${BLUE}📊 Useful commands:${NC}"
echo -e "${YELLOW}# Check all services status:${NC}"
echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && find . -name \"docker-compose*.yml\" -exec docker-compose -f {} ps \\;'"

echo ""
echo -e "${YELLOW}# View logs:${NC}"
if [ "$DEPLOY_BACKEND" = true ] && [ "$DEPLOY_BOT" = true ]; then
    echo "# Backend logs:"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/backend && docker-compose logs -f'"
    echo ""
    echo "# Bot logs:"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose logs -f'"
elif [ "$DEPLOY_BACKEND" = true ]; then
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/backend && docker-compose logs -f'"
elif [ "$DEPLOY_BOT" = true ]; then
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose logs -f'"
fi

echo ""
echo -e "${YELLOW}# Restart services:${NC}"
if [ "$DEPLOY_BACKEND" = true ]; then
    echo "# Restart backend:"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/backend && docker-compose restart'"
fi
if [ "$DEPLOY_BOT" = true ]; then
    echo "# Restart bot:"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR/telegram-bot && docker-compose restart'"
fi

echo -e "${GREEN}🎯 Ready for production use!${NC}" 