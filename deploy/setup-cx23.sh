#!/bin/bash
set -e

echo "=== hageglede CX23 Deployment Bootstrap ==="
echo "This script prepares a CX23 server for hageplan deployment."
echo "Run this once on a fresh CX23 server before first deployment."
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root. Use: sudo bash $0"
   exit 1
fi

echo "1. Updating system packages..."
apt-get update
apt-get upgrade -y

echo "2. Installing Docker and Docker Compose..."
# Install Docker
apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose Plugin
apt-get install -y docker-compose-plugin

echo "3. Creating deployment directory structure..."
mkdir -p /opt/hageglede/deploy/traefik
mkdir -p /opt/hageglede/data/sqlite
mkdir -p /opt/hageglede/logs
chmod -R 755 /opt/hageglede

echo "4. Creating Traefik configuration files..."
# Create traefik.yml
cat > /opt/hageglede/deploy/traefik/traefik.yml << 'EOF'
api:
  dashboard: true
  debug: true

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: dev@vindingur.no
      storage: /etc/traefik/acme.json
      httpChallenge:
        entryPoint: web

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: traefik-network
  file:
    directory: /etc/traefik/dynamic
    watch: true

log:
  level: INFO
  filePath: /var/log/traefik/traefik.log

accessLog:
  filePath: /var/log/traefik/access.log
EOF

# Create dynamic.yml
cat > /opt/hageglede/deploy/traefik/dynamic.yml << 'EOF'
http:
  middlewares:
    strip-hageplan-prefix:
      stripPrefix:
        prefixes:
          - "/projects/hageplan"

  routers:
    hageplan-router:
      rule: "PathPrefix(`/projects/hageplan`)"
      entryPoints:
        - websecure
      middlewares:
        - strip-hageplan-prefix
      service: hageplan-service
      tls:
        certResolver: letsencrypt

  services:
    hageplan-service:
      loadBalancer:
        servers:
          - url: "http://hageplan:8000"
EOF

echo "5. Creating docker-compose.yml for Traefik..."
cat > /opt/hageglede/docker-compose.yml << 'EOF'
version: '3.8'

networks:
  traefik-network:
    external: true

services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    networks:
      - traefik-network
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./deploy/traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - ./deploy/traefik/dynamic.yml:/etc/traefik/dynamic/dynamic.yml:ro
      - ./deploy/traefik/acme.json:/etc/traefik/acme.json
      - ./deploy/traefik/logs:/var/log/traefik
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.localhost`)"
      - "traefik.http.routers.traefik.service=api@internal"
      - "traefik.http.routers.traefik.entrypoints=websecure"
      - "traefik.http.routers.traefik.tls.certresolver=letsencrypt"

  hageplan:
    image: vindingur/hageglede:latest
    container_name: hageplan
    restart: unless-stopped
    networks:
      - traefik-network
    volumes:
      - ./data/sqlite:/app/data
    environment:
      - SQLITE_PATH=/app/data/hageglede.db
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=traefik-network"
EOF

echo "6. Setting permissions for Traefik ACME storage..."
touch /opt/hageglede/deploy/traefik/acme.json
chmod 600 /opt/hageglede/deploy/traefik/acme.json

echo "7. Creating Traefik Docker network..."
docker network create traefik-network 2>/dev/null || true

echo "8. Creating systemd service for automatic startup..."
cat > /etc/systemd/system/hageglede.service << 'EOF'
[Unit]
Description=hageglede Deployment Stack
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/hageglede
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

echo "9. Enabling and starting the service..."
systemctl daemon-reload
systemctl enable hageglede.service

echo "10. Creating deploy script for GitHub Actions..."
cat > /opt/hageglede/deploy.sh << 'EOF'
#!/bin/bash
set -e

cd /opt/hageglede
docker-compose pull
docker-compose up -d --remove-orphans
docker system prune -af --volumes
EOF
chmod +x /opt/hageglede/deploy.sh

echo ""
echo "=== Bootstrap Complete ==="
echo "Server is ready for hageglede deployments."
echo ""
echo "Next steps from GitHub Actions:"
echo "1. SSH to this server: ssh root@your-server-ip"
echo "2. Verify Traefik is running: docker ps"
echo "3. First deployment will pull the hageplan image"
echo ""
echo "To start Traefik immediately:"
echo "  cd /opt/hageglede && docker-compose up -d traefik"
echo ""
echo "To monitor logs:"
echo "  docker logs -f traefik"
echo ""
echo "Traefik dashboard will be available at: https://traefik.localhost"
echo "(Requires local hosts file entry or direct server IP access)"
EOF