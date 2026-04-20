#!/bin/bash
set -e

# Idempotent server bootstrap script for CX23 deployment
# This script sets up Docker, Traefik network, directory structure, and firewall rules

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

# Update package list
log_info "Updating package list..."
apt-get update -qq

# Install required packages
log_info "Installing required packages..."
apt-get install -y -qq \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    ufw \
    git

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    log_info "Installing Docker..."
    
    # Add Docker's official GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up the repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update -qq
    apt-get install -y -qq \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-compose-plugin
    
    log_info "Docker installed successfully"
else
    log_info "Docker is already installed"
fi

# Install Docker Compose (standalone) if not present
if ! command -v docker-compose &> /dev/null; then
    log_info "Installing Docker Compose standalone..."
    curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log_info "Docker Compose installed successfully"
else
    log_info "Docker Compose is already installed"
fi

# Create deployment directory structure
log_info "Creating directory structure..."
mkdir -p /opt/hageglede/deploy
mkdir -p /opt/hageglede/deploy/traefik
mkdir -p /opt/hageglede/data
mkdir -p /opt/hageglede/logs
mkdir -p /opt/hageglede/ssl
mkdir -p /opt/hageglede/backups

# Set ownership for deployment directories
chown -R $SUDO_USER:$SUDO_USER /opt/hageglede

# Create Traefik directories
mkdir -p /opt/traefik/config
mkdir -p /opt/traefik/certificates
chmod 600 /opt/traefik/certificates

# Create docker-compose.yml in /opt/hageglede if it doesn't exist
if [ ! -f "/opt/hageglede/docker-compose.yml" ]; then
    log_info "Creating docker-compose.yml..."
    cat > /opt/hageglede/docker-compose.yml << 'EOF'
# Copy from the repository: hageglede/docker-compose.yml
# This file should be copied from the git repository
echo "Please copy docker-compose.yml from the repository to /opt/hageglede/"
EOF
    log_warn "docker-compose.yml not found. Please copy it from the repository"
fi

# Configure firewall (UFW)
log_info "Configuring firewall..."
ufw --force disable  # Disable first to avoid locking ourselves out

# Set default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH
ufw allow ssh

# Allow HTTP/HTTPS for Traefik
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw --force enable

log_info "Firewall configured: SSH (22), HTTP (80), HTTPS (443) allowed"

# Create Traefik network if it doesn't exist
log_info "Creating Docker network for Traefik..."
if ! docker network inspect traefik-public >/dev/null 2>&1; then
    docker network create traefik-public
    log_info "Created Docker network 'traefik-public'"
else
    log_info "Docker network 'traefik-public' already exists"
fi

# Create systemd service for auto-start (optional)
log_info "Creating systemd service file for reference..."
cat > /etc/systemd/system/hageglede.service << 'EOF'
[Unit]
Description=hageglede deployment
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/hageglede
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=$SUDO_USER
Group=$SUDO_USER

[Install]
WantedBy=multi-user.target
EOF

log_info "Systemd service file created at /etc/systemd/system/hageglede.service"
log_info "To enable auto-start: systemctl enable hageglede.service"

# Create backup script
log_info "Creating backup script..."
cat > /opt/hageglede/backup.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/opt/hageglede/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hageglede_backup_$DATE.tar.gz"

echo "Starting backup of hageglede data..."
docker exec hageglede sqlite3 /app/data/hageglede.db ".backup /tmp/hageglede_backup.db" 2>/dev/null || echo "Database backup skipped (container may not be running)"

cd /opt/hageglede
tar czf $BACKUP_FILE data/ logs/ 2>/dev/null

if [ -f "/tmp/hageglede_backup.db" ]; then
    tar rzf $BACKUP_FILE /tmp/hageglede_backup.db
    rm /tmp/hageglede_backup.db
fi

echo "Backup created: $BACKUP_FILE"

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "hageglede_backup_*.tar.gz" -mtime +30 -delete
EOF

chmod +x /opt/hageglede/backup.sh
chown $SUDO_USER:$SUDO_USER /opt/hageglede/backup.sh

# Create restore script
cat > /opt/hageglede/restore.sh << 'EOF'
#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "WARNING: This will overwrite existing data!"
read -p "Are you sure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

echo "Stopping hageglede..."
cd /opt/hageglede
docker-compose down || true

echo "Extracting backup..."
tar xzf "$BACKUP_FILE" -C /

echo "Starting hageglede..."
docker-compose up -d

echo "Restore completed"
EOF

chmod +x /opt/hageglede/restore.sh
chown $SUDO_USER:$SUDO_USER /opt/hageglede/restore.sh

# Create update script
cat > /opt/hageglede/update.sh << 'EOF'
#!/bin/bash
set -e

echo "Updating hageglede deployment..."

cd /opt/hageglede

# Pull latest images
docker-compose pull

# Recreate containers with new images
docker-compose up -d --force-recreate

# Clean up old images
docker image prune -f

echo "Update completed"
EOF

chmod +x /opt/hageglede/update.sh
chown $SUDO_USER:$SUDO_USER /opt/hageglede/update.sh

# Summary
log_info "=== Server bootstrap complete ==="
log_info "Directory structure created in /opt/hageglede/"
log_info "Firewall configured (SSH, HTTP, HTTPS)"
log_info "Docker network 'traefik-public' ready"
log_info ""
log_info "Next steps:"
log_info "1. Copy files from repository to /opt/hageglede/:"
log_info "   - docker-compose.yml"
log_info "   - deploy/traefik/traefik.yml → /opt/traefik/config/"
log_info "   - deploy/traefik/dynamic.yml → /opt/traefik/config/"
log_info "2. Update secrets in docker-compose.yml (if needed)"
log_info "3. Start the deployment:"
log_info "   cd /opt/hageglede && docker-compose up -d"
log_info ""
log_info "Backup scripts created:"
log_info "  /opt/hageglede/backup.sh    - Create backup"
log_info "  /opt/hageglede/restore.sh   - Restore from backup"
log_info "  /opt/hageglede/update.sh    - Update containers"
log_info ""
log_info "For auto-start: systemctl enable hageglede.service"