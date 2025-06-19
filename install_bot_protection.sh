#!/bin/bash

# WireGuard Bot Protection Installer
# Complete automated installation of bot blocking protection

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                WireGuard Bot Protection Installer            ║"
    echo "║                                                              ║"
    echo "║  This installer will safely add bot blocking protection     ║"
    echo "║  to your existing WireGuard bot without breaking anything    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -f "app.py" ]] || [[ ! -d "handlers" ]]; then
        print_error "This doesn't appear to be a wireguard-bot directory."
        print_error "Please run this script from the bot's root directory."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is required but not installed."
        exit 1
    fi
    
    # Check if bot is running
    if pgrep -f "python.*app.py" > /dev/null; then
        print_warning "Bot appears to be running. We'll stop it during installation."
        BOT_WAS_RUNNING=true
    else
        BOT_WAS_RUNNING=false
    fi
    
    print_status "Prerequisites check passed"
}

# Create backup
create_backup() {
    print_step "Creating backup..."
    
    BACKUP_DIR="/tmp/wireguard_bot_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup code
    cp -r . "$BACKUP_DIR/bot_code"
    
    # Backup WireGuard config if exists
    if [[ -f "/etc/wireguard/wg0.conf" ]]; then
        sudo cp "/etc/wireguard/wg0.conf" "$BACKUP_DIR/wg0.conf.backup"
    fi
    
    # Create rollback script
    cat > "$BACKUP_DIR/ROLLBACK.sh" << EOF
#!/bin/bash
echo "Rolling back WireGuard Bot..."

# Stop bot
sudo systemctl stop wireguard-bot 2>/dev/null || pkill -f "python.*app.py" || true

# Restore code
ORIGINAL_DIR=\$(pwd)
cd "\$(dirname "\$0")"
rm -rf "\$ORIGINAL_DIR"/*
cp -r bot_code/* "\$ORIGINAL_DIR/"

# Restore WireGuard config
if [[ -f "wg0.conf.backup" ]]; then
    sudo cp "wg0.conf.backup" "/etc/wireguard/wg0.conf"
    sudo systemctl restart wg-quick@wg0
fi

echo "Rollback completed!"
echo "Restore database manually: psql database_name < database_backup.sql"
EOF
    
    chmod +x "$BACKUP_DIR/ROLLBACK.sh"
    
    print_status "Backup created: $BACKUP_DIR"
    echo "         Rollback script: $BACKUP_DIR/ROLLBACK.sh"
}

# Stop bot
stop_bot() {
    print_step "Stopping bot..."
    
    # Try systemctl first
    if sudo systemctl stop wireguard-bot 2>/dev/null; then
        print_status "Bot service stopped"
    # Try pkill
    elif pkill -f "python.*app.py" 2>/dev/null; then
        print_status "Bot process stopped"
        sleep 2
    else
        print_warning "Could not stop bot automatically"
        print_warning "Please stop the bot manually and press Enter to continue"
        read -p ""
    fi
}

# Install dependencies
install_dependencies() {
    print_step "Installing dependencies..."
    
    # Check if we're in virtual environment
    if [[ -n "$VIRTUAL_ENV" ]]; then
        PIP_CMD="pip"
        print_status "Using virtual environment: $VIRTUAL_ENV"
    else
        PIP_CMD="pip3"
        print_warning "No virtual environment detected"
    fi
    
    # Install required packages
    $PIP_CMD install psycopg2-binary aiofiles --quiet
    
    print_status "Dependencies installed"
}

# Apply database migration
apply_database_migration() {
    print_step "Applying database migration..."
    
    # Create migration SQL
    cat > migration.sql << 'EOF'
-- Add bot blocking protection tables
CREATE TABLE IF NOT EXISTS banned_users (
    user_id BIGINT PRIMARY KEY,
    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT DEFAULT 'Bot blocked by user'
);

CREATE INDEX IF NOT EXISTS idx_banned_users_user_id ON banned_users(user_id);

COMMENT ON TABLE banned_users IS 'Users who are permanently banned from the bot';
EOF
    
    # Apply migration
    if python3 -c "
import sys
sys.path.append('.')
try:
    from data.config import Config
    import psycopg2
    
    config = Config()
    conn = psycopg2.connect(**config.db_connection_parameters)
    cursor = conn.cursor()
    
    with open('migration.sql', 'r') as f:
        cursor.execute(f.read())
    
    conn.commit()
    cursor.close()
    conn.close()
    print('Database migration successful')
except Exception as e:
    print(f'Database migration failed: {e}')
    sys.exit(1)
"; then
        print_status "Database migration applied"
    else
        print_error "Database migration failed"
        exit 1
    fi
    
    rm migration.sql
}

# Apply code updates
apply_code_updates() {
    print_step "Applying code updates..."
    
    if python3 update_bot.py; then
        print_status "Code updates applied successfully"
    else
        print_error "Code updates failed"
        exit 1
    fi
}

# Start bot
start_bot() {
    print_step "Starting bot..."
    
    if [[ "$BOT_WAS_RUNNING" == "true" ]]; then
        # Try to start with systemctl
        if sudo systemctl start wireguard-bot 2>/dev/null; then
            print_status "Bot service started"
        else
            print_warning "Could not start bot service automatically"
            print_warning "Please start the bot manually"
        fi
    else
        print_status "Bot was not running before, not starting automatically"
    fi
}

# Test installation
test_installation() {
    print_step "Testing installation..."
    
    # Test database connection
    if python3 -c "
import sys
sys.path.append('.')
try:
    import database.selector
    import database.update
    from utils.bot_error_handler import safe_send_message
    print('✓ All modules imported successfully')
except Exception as e:
    print(f'✗ Import test failed: {e}')
    sys.exit(1)
"; then
        print_status "Installation test passed"
    else
        print_error "Installation test failed"
        return 1
    fi
}

# Main installation
main() {
    print_header
    
    echo "This installer will:"
    echo "• Create a complete backup of your current setup"
    echo "• Add bot blocking protection features"
    echo "• Update database schema safely"
    echo "• Add new admin commands (/ban, /unban, /status)"
    echo "• Preserve all existing functionality"
    echo ""
    
    read -p "Continue with installation? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    echo ""
    print_step "Starting installation..."
    
    # Run installation steps
    check_prerequisites
    create_backup
    stop_bot
    install_dependencies
    apply_database_migration
    apply_code_updates
    
    # Test before starting
    if test_installation; then
        start_bot
        
        echo ""
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗"
        echo -e "║                    INSTALLATION SUCCESSFUL!                 ║"
        echo -e "╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${GREEN}✅ Bot blocking protection installed successfully!${NC}"
        echo ""
        echo "📋 New features added:"
        echo "  • Automatic detection when users block the bot"
        echo "  • Automatic removal of configs for blocked users"
        echo "  • New admin commands:"
        echo "    - /ban <user_id>    - Ban user permanently"
        echo "    - /unban <user_id>  - Unban user"
        echo "    - /status <user_id> - Check user status"
        echo ""
        echo "💾 Backup location: $BACKUP_DIR"
        echo "🔄 Rollback script: $BACKUP_DIR/ROLLBACK.sh"
        echo ""
        echo "🎉 Your bot is now protected against blocking abuse!"
        
    else
        print_error "Installation test failed. Rolling back..."
        
        # Automatic rollback
        if [[ -f "$BACKUP_DIR/ROLLBACK.sh" ]]; then
            bash "$BACKUP_DIR/ROLLBACK.sh"
            print_status "Rollback completed"
        fi
        
        exit 1
    fi
}

# Run main function
main "$@"