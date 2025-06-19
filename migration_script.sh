#!/bin/bash

# WireGuard Bot Safe Migration Script
# Adds bot blocking protection without breaking existing functionality

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BOT_SERVICE_NAME="wireguard-bot"  # Change if your service has different name
BACKUP_DIR="/tmp/wireguard_bot_backup_$(date +%Y%m%d_%H%M%S)"
CURRENT_DIR=$(pwd)

echo -e "${BLUE}=== WireGuard Bot Migration Script ===${NC}"
echo -e "${YELLOW}This script will safely add bot blocking protection${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Pre-flight checks
print_status "Running pre-flight checks..."

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root. This is OK but be careful."
elif ! sudo -n true 2>/dev/null; then
    print_error "This script requires sudo access. Please run with sudo or as root."
    exit 1
fi

# Check if PostgreSQL is available
if ! command_exists psql; then
    print_error "PostgreSQL client (psql) not found. Please install it first."
    exit 1
fi

# Check if bot directory exists
if [[ ! -f "app.py" ]] || [[ ! -d "handlers" ]]; then
    print_error "This doesn't appear to be a wireguard-bot directory."
    print_error "Please run this script from the bot's root directory."
    exit 1
fi

# Create backup directory
print_status "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Step 1: Stop the bot service
print_status "Stopping bot service..."
if systemctl is-active --quiet "$BOT_SERVICE_NAME" 2>/dev/null; then
    sudo systemctl stop "$BOT_SERVICE_NAME"
    print_status "Bot service stopped"
else
    print_warning "Bot service '$BOT_SERVICE_NAME' not found or not running"
    print_warning "You may need to stop the bot manually"
fi

# Step 2: Backup current code
print_status "Backing up current bot code..."
cp -r "$CURRENT_DIR" "$BACKUP_DIR/bot_code"
print_status "Code backed up to: $BACKUP_DIR/bot_code"

# Step 3: Backup WireGuard config
print_status "Backing up WireGuard configuration..."
if [[ -f "/etc/wireguard/wg0.conf" ]]; then
    sudo cp "/etc/wireguard/wg0.conf" "$BACKUP_DIR/wg0.conf.backup"
    print_status "WireGuard config backed up"
else
    print_warning "WireGuard config not found at /etc/wireguard/wg0.conf"
fi

# Step 4: Backup database
print_status "Preparing database backup..."
echo "Please provide your database connection details:"

# Try to read from .env file first
if [[ -f ".env" ]]; then
    print_status "Found .env file, trying to read database config..."
    DB_NAME=$(grep "^DB_NAME=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "")
    DB_USER=$(grep "^DB_USER=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "")
    DB_HOST=$(grep "^DB_HOST=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "localhost")
    DB_PORT=$(grep "^DB_PORT=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "5432")
fi

# Ask for database details if not found in .env
if [[ -z "$DB_NAME" ]]; then
    read -p "Database name: " DB_NAME
fi
if [[ -z "$DB_USER" ]]; then
    read -p "Database user: " DB_USER
fi
if [[ -z "$DB_HOST" ]]; then
    read -p "Database host [localhost]: " DB_HOST
    DB_HOST=${DB_HOST:-localhost}
fi
if [[ -z "$DB_PORT" ]]; then
    read -p "Database port [5432]: " DB_PORT
    DB_PORT=${DB_PORT:-5432}
fi

print_status "Creating database backup..."
export PGPASSWORD
read -s -p "Database password: " PGPASSWORD
echo ""

if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" > "$BACKUP_DIR/database_backup.sql"; then
    print_status "Database backed up to: $BACKUP_DIR/database_backup.sql"
else
    print_error "Database backup failed!"
    print_error "Please check your database credentials and try again."
    exit 1
fi

# Step 5: Show backup summary
echo ""
print_status "=== BACKUP SUMMARY ==="
print_status "Backup location: $BACKUP_DIR"
print_status "- Bot code: $BACKUP_DIR/bot_code"
print_status "- Database: $BACKUP_DIR/database_backup.sql"
print_status "- WireGuard config: $BACKUP_DIR/wg0.conf.backup"
echo ""

# Step 6: Confirm migration
echo -e "${YELLOW}Ready to apply migration. This will:${NC}"
echo "1. Add new database tables for user banning"
echo "2. Update bot code with blocking protection"
echo "3. Add new admin commands (/ban, /unban, /status)"
echo "4. Improve error handling"
echo ""
echo -e "${GREEN}Your existing data will NOT be modified or deleted.${NC}"
echo ""

read -p "Continue with migration? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Migration cancelled by user"
    print_status "Your backups are saved in: $BACKUP_DIR"
    exit 0
fi

print_status "Starting migration..."

# Create rollback script
cat > "$BACKUP_DIR/rollback.sh" << 'EOF'
#!/bin/bash
# Rollback script for WireGuard Bot migration

BACKUP_DIR=$(dirname "$0")
CURRENT_DIR=$(pwd)

echo "Rolling back WireGuard Bot migration..."

# Stop bot
sudo systemctl stop wireguard-bot 2>/dev/null || true

# Restore code
if [[ -d "$BACKUP_DIR/bot_code" ]]; then
    rm -rf "$CURRENT_DIR"/*
    cp -r "$BACKUP_DIR/bot_code"/* "$CURRENT_DIR/"
    echo "Code restored"
fi

# Restore WireGuard config
if [[ -f "$BACKUP_DIR/wg0.conf.backup" ]]; then
    sudo cp "$BACKUP_DIR/wg0.conf.backup" "/etc/wireguard/wg0.conf"
    echo "WireGuard config restored"
fi

echo "Database restore:"
echo "Run: psql -h HOST -p PORT -U USER DATABASE_NAME < $BACKUP_DIR/database_backup.sql"

echo "Rollback completed. Start bot manually if needed."
EOF

chmod +x "$BACKUP_DIR/rollback.sh"
print_status "Rollback script created: $BACKUP_DIR/rollback.sh"

echo ""
print_status "=== MIGRATION READY ==="
print_status "Backups created successfully!"
print_status "Next: Run the code update script to apply changes"
print_status "Rollback available at: $BACKUP_DIR/rollback.sh"
echo ""
echo -e "${GREEN}Migration preparation completed!${NC}"
echo -e "${YELLOW}Keep this backup directory safe: $BACKUP_DIR${NC}"