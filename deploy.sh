#!/bin/bash
# OPNsense IaC Deployment Script
# This script helps deploy the OPNsense IaC tool on a VM

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    echo -e "${GREEN}[+] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_error() {
    echo -e "${RED}[!] $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    print_error "Cannot detect OS"
    exit 1
fi

print_message "Detected OS: $OS $VER"

# Check for required software
check_commands() {
    print_message "Checking required commands..."
    
    # Check for Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found. Installing..."
        
        # Install Docker based on OS
        if [[ "$OS" == *"Ubuntu"* ]]; then
            apt-get update
            apt-get install -y apt-transport-https ca-certificates curl software-properties-common
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
            add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io
        elif [[ "$OS" == *"Debian"* ]]; then
            apt-get update
            apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io
        else
            print_error "Unsupported OS for automatic Docker installation"
            print_error "Please install Docker manually and run this script again"
            exit 1
        fi
    else
        print_message "Docker is already installed"
    fi
    
    # Check for Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose not found. Installing..."
        
        curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    else
        print_message "Docker Compose is already installed"
    fi
    
    # Check for Bun
    if ! command -v bun &> /dev/null; then
        print_warning "Bun not found. Installing..."
        
        curl -fsSL https://bun.sh/install | bash
        
        # Source profile to get bun in path
        if [ -f "$HOME/.bashrc" ]; then
            source "$HOME/.bashrc"
        fi
    else
        print_message "Bun is already installed"
    fi
    
    # Check for git
    if ! command -v git &> /dev/null; then
        print_warning "Git not found. Installing..."
        
        apt-get update
        apt-get install -y git
    else
        print_message "Git is already installed"
    fi
}

# Get OPNsense information
collect_info() {
    print_message "Collecting required information..."
    
    # VM IP address
    read -p "Enter this VM's IP address: " VM_IP
    
    # OPNsense info
    read -p "Enter OPNsense hostname or IP address: " OPNSENSE_HOST
    read -p "Enter OPNsense API key: " OPNSENSE_KEY
    read -p "Enter OPNsense API secret: " OPNSENSE_SECRET
    
    # Test connectivity
    if ping -c 1 $OPNSENSE_HOST &> /dev/null; then
        print_message "OPNsense host is reachable"
    else
        print_warning "OPNsense host is not responding to ping. This might be normal if ICMP is blocked."
    fi
}

# Deploy the application
deploy_app() {
    print_message "Deploying OPNsense IaC..."
    
    # Clone the repository if not already present
    if [ ! -d "./OPN_IaC" ]; then
        print_message "Cloning repository..."
        git clone https://github.com/yourusername/OPN_IaC.git
    else
        print_message "Repository already exists. Pulling latest changes..."
        cd OPN_IaC
        git pull
        cd ..
    fi
    
    # Enter the directory
    cd OPN_IaC
    
    # Create .env file
    print_message "Creating environment configuration..."
    cat > .env << EOL
DEBUG=False
DJANGO_ALLOWED_HOSTS=$VM_IP,localhost,127.0.0.1
SECRET_KEY=$(openssl rand -base64 32)
POSTGRES_DB=opn_django
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(openssl rand -base64 12)
POSTGRES_HOST=db
POSTGRES_PORT=5432
OPNSENSE_API_URL=https://$OPNSENSE_HOST/api
OPNSENSE_API_KEY=$OPNSENSE_KEY
OPNSENSE_API_SECRET=$OPNSENSE_SECRET
OPNSENSE_API_VERIFY_SSL=False
EOL
    
    # Build and start the services
    print_message "Building and starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_message "Waiting for services to be ready..."
    sleep 10
    
    # Create superuser
    print_message "Creating Django admin superuser..."
    read -p "Enter admin username: " ADMIN_USER
    read -p "Enter admin email: " ADMIN_EMAIL
    read -s -p "Enter admin password: " ADMIN_PASS
    echo
    
    # Create superuser using Docker exec
    docker-compose exec -T web python OPN_Django/manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='$ADMIN_USER').exists():
    User.objects.create_superuser('$ADMIN_USER', '$ADMIN_EMAIL', '$ADMIN_PASS')
    print("Superuser created successfully")
else:
    print("Superuser already exists")
EOF
    
    # Set up CLI
    print_message "Setting up CLI..."
    cp cli-package.json package.json
    bun install
    
    # Create symbolic link for CLI
    if [ ! -f "/usr/local/bin/opn-cli" ]; then
        print_message "Creating symbolic link for CLI..."
        ln -sf "$(pwd)/cli.js" /usr/local/bin/opn-cli
        chmod +x /usr/local/bin/opn-cli
    fi
    
    # Display success message
    print_message "Deployment completed successfully!"
    print_message "You can access the admin interface at: http://$VM_IP:8000/admin"
    print_message "API documentation is available at: http://$VM_IP:8000/api/docs"
    
    # Onboard OPNsense host
    print_message "Onboarding OPNsense host..."
    opn-cli onboard -n "Primary OPNsense" -h "$OPNSENSE_HOST" -k "$OPNSENSE_KEY" -s "$OPNSENSE_SECRET"
}

# Main execution
main() {
    print_message "Starting OPNsense IaC deployment..."
    
    check_commands
    collect_info
    deploy_app
    
    print_message "Setup complete! Your OPNsense IaC system is ready to use."
}

# Run the script
main
