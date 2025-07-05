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

# Load deployment configuration
load_env "deploy.env"

# Default values
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_HOST="${REMOTE_HOST:-YOUR_SERVER_IP}"
SSH_KEY="${SSH_KEY_PATH:-~/.ssh/your_ssh_key}"

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Test Docker installation on remote server"
    echo ""
    echo "Options:"
    echo "  -u, --user USER     SSH username (default from deploy.env or 'root')"
    echo "  -h, --host HOST     Server hostname/IP (default from deploy.env or 'YOUR_SERVER_IP')"
    echo "  -k, --key PATH      SSH private key path (default from deploy.env or '~/.ssh/your_ssh_key')"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                               # Test using deploy.env configuration"
    echo "  $0 -h your-server.com -u ubuntu # Test with specific server and user"
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

echo -e "${BLUE}🔍 Testing Docker Installation${NC}"
echo -e "${YELLOW}Target: $REMOTE_USER@$REMOTE_HOST${NC}"
echo -e "${YELLOW}SSH Key: $SSH_KEY${NC}"
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
    echo -e "${RED}Please check your SSH configuration${NC}"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"
echo ""

# Comprehensive Docker testing
echo -e "${BLUE}🐳 Running comprehensive Docker tests...${NC}"

$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    echo '=== System Information ==='
    echo 'OS: ' \$(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')
    echo 'Kernel: ' \$(uname -r)
    echo 'Architecture: ' \$(uname -m)
    echo ''
    
    echo '=== Docker Installation Check ==='
    if command -v docker >/dev/null 2>&1; then
        echo '✅ Docker command is available'
        echo 'Docker version:'
        docker --version
        echo ''
        
        echo 'Docker system info:'
        docker info --format 'Server Version: {{.ServerVersion}}' 2>/dev/null || echo 'Docker daemon may not be running'
        docker info --format 'Storage Driver: {{.Driver}}' 2>/dev/null
        docker info --format 'Operating System: {{.OperatingSystem}}' 2>/dev/null
        docker info --format 'Architecture: {{.Architecture}}' 2>/dev/null
        echo ''
        
        echo 'Docker service status:'
        systemctl is-active docker 2>/dev/null || echo 'systemctl not available or Docker service not found'
        systemctl is-enabled docker 2>/dev/null || echo 'Docker service auto-start status unknown'
        echo ''
        
        echo 'Testing Docker functionality:'
        if docker run --rm hello-world >/dev/null 2>&1; then
            echo '✅ Docker can run containers successfully'
        else
            echo '❌ Docker cannot run containers'
            echo 'Docker daemon logs (last 10 lines):'
            journalctl -u docker --no-pager -n 10 2>/dev/null || echo 'Cannot access Docker logs'
        fi
    else
        echo '❌ Docker is not installed'
    fi
    echo ''
    
    echo '=== docker-compose Installation Check ==='
    if command -v docker-compose >/dev/null 2>&1; then
        echo '✅ docker-compose command is available'
        echo 'docker-compose version:'
        docker-compose --version
        echo ''
        
        echo 'docker-compose executable info:'
        which docker-compose
        ls -la \$(which docker-compose)
        file \$(which docker-compose) 2>/dev/null || echo 'file command not available'
    else
        echo '❌ docker-compose is not installed'
    fi
    echo ''
    
    echo '=== Docker Compose Plugin Check ==='
    if docker compose version >/dev/null 2>&1; then
        echo '✅ Docker Compose plugin is available'
        echo 'Docker Compose plugin version:'
        docker compose version
    else
        echo '❌ Docker Compose plugin is not available'
    fi
    echo ''
    
    echo '=== Network and Connectivity ==='
    echo 'Testing internet connectivity:'
    if curl -s --connect-timeout 5 https://get.docker.com >/dev/null; then
        echo '✅ Can reach Docker installation script'
    else
        echo '❌ Cannot reach Docker installation script'
    fi
    
    if curl -s --connect-timeout 5 https://github.com >/dev/null; then
        echo '✅ Can reach GitHub (for docker-compose downloads)'
    else
        echo '❌ Cannot reach GitHub'
    fi
    echo ''
    
    echo '=== User and Permissions ==='
    echo 'Current user: ' \$(whoami)
    echo 'User groups: ' \$(groups)
    if groups | grep -q docker; then
        echo '✅ User is in docker group'
    else
        echo '⚠️  User is not in docker group (may need sudo for Docker commands)'
    fi
    echo ''
    
    echo '=== Docker Images and Containers ==='
    if command -v docker >/dev/null 2>&1; then
        echo 'Docker images:'
        docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' 2>/dev/null || echo 'Cannot list Docker images'
        echo ''
        
        echo 'Running containers:'
        docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}' 2>/dev/null || echo 'Cannot list Docker containers'
        echo ''
        
        echo 'All containers:'
        docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}' 2>/dev/null || echo 'Cannot list all Docker containers'
    fi
    echo ''
    
    echo '=== PATH and Environment ==='
    echo 'PATH: ' \$PATH
    echo '/usr/local/bin contents:'
    ls -la /usr/local/bin/ 2>/dev/null | grep -E '(docker|compose)' || echo 'No Docker-related files in /usr/local/bin'
    echo ''
    
    echo '=== Final Status ==='
    DOCKER_OK=false
    COMPOSE_OK=false
    
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        DOCKER_OK=true
        echo '✅ Docker is installed and working'
    else
        echo '❌ Docker is not working properly'
    fi
    
    if command -v docker-compose >/dev/null 2>&1 && docker-compose --version >/dev/null 2>&1; then
        COMPOSE_OK=true
        echo '✅ docker-compose is installed and working'
    else
        echo '❌ docker-compose is not working properly'
    fi
    
    if [ \"\$DOCKER_OK\" = true ] && [ \"\$COMPOSE_OK\" = true ]; then
        echo ''
        echo '🎉 Docker environment is ready for deployment!'
        exit 0
    else
        echo ''
        echo '⚠️  Docker environment needs attention before deployment'
        exit 1
    fi
"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 Docker testing completed successfully!${NC}"
    echo -e "${GREEN}Your server is ready for deployment.${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  Docker testing found issues.${NC}"
    echo -e "${YELLOW}Run the deployment script to automatically fix these issues.${NC}"
fi 