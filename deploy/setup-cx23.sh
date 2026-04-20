#!/bin/bash
# hageglede CX23 deployment bootstrap script
# Install Docker, Traefik, and deploy initial stack

set -e

echo "=== hageglede CX23 Bootstrap ==="

# Update system and install prerequisites
echo "Updating system packages..."
apt-get update
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Create Docker network for Traefik
if ! docker network inspect traefik > /dev/null 2>&1; then
    echo "Creating traefik Docker network..."
    docker network create traefik
    echo "Created traefik network"
else
    echo "traefik network already exists"
fi

# Create directories for Traefik
echo "Creating Traefik configuration directories..."
mkdir -p /opt/hageglede/deploy/traefik
mkdir -p /var/traefik/certs
mkdir -p /var/traefik/acme
chmod 600 /var/traefik/acme

# Copy Traefik configuration files (assuming they're in current directory)
if [ -f "./deploy/traefik/traefik.yml" ]; then
    cp ./deploy/traefik/traefik.yml /opt/hageglede/deploy/traefik/
    cp ./deploy/traefik/dynamic.yml /opt/hageglede/deploy/traefik/
    echo "Copied Traefik config files"
else
    echo "Warning: Traefik config files not found in current directory"
fi

# Pull Traefik image
echo "Pulling Traefik Docker image..."
docker pull traefik:v3.0

# Deploy Traefik stack
if [ -f "./docker-compose.yml" ]; then
    echo "Starting initial deployment..."
    docker compose -f ./docker-compose.yml up -d traefik
    
    echo "Waiting for Traefik to start..."
    sleep 10
    
    # Check if Traefik is running
    if docker ps | grep -q traefik; then
        echo "Traefik started successfully"
        echo "Check logs: docker logs traefik"
    else
        echo "Warning: Traefik may not have started properly"
    fi
else
    echo "docker-compose.yml not found in current directory"
    echo "You can deploy Traefik manually with:"
    echo "  docker run -d \\"
    echo "    -p 80:80 -p 443:443 \\"
    echo "    -v /var/run/docker.sock:/var/run/docker.sock:ro \\"
    echo "    -v /opt/hageglede/deploy/traefik/traefik.yml:/etc/traefik/traefik.yml \\"
    echo "    -v /opt/hageglede/deploy/traefik/dynamic.yml:/etc/traefik/dynamic.yml \\"
    echo "    -v /var/traefik/certs:/certs \\"
    echo "    -v /var/traefik/acme:/acme \\"
    echo "    --network traefik \\"
    echo "    --name traefik \\"
    echo "    traefik:v3.0"
fi

# Create SQLite data directory
echo "Creating SQLite data directory..."
mkdir -p /opt/hageglede/data
chmod 755 /opt/hageglede/data

echo "=== Bootstrap Complete ==="
echo ""
echo "Next steps:"
echo "1. Set up DNS: hageglede.no CNAME to projects.vindingur.no"
echo "2. Deploy hageglede app: docker compose up -d"
echo "3. Check Traefik dashboard: https://projects.vindingur.no/hageglede (once deployed)"
echo ""
echo "Monitor logs:"
echo "  docker logs traefik"
echo "  docker compose logs -f"
echo ""
echo "To update deployment:"
echo "  docker compose pull"
echo "  docker compose up -d"