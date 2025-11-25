#!/bin/bash

# HomeGuard Backup Script

echo "💾 Creating HomeGuard backup..."

# Navigate to project directory
cd "$(dirname "$0")/.."

# Create backup directory
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup MongoDB
echo "📦 Backing up MongoDB..."
docker-compose exec -T mongodb mongodump --archive > "$BACKUP_DIR/mongodb_backup.archive"

# Backup ML models
echo "🤖 Backing up ML models..."
if [ -d "backend/ml_models" ]; then
    cp -r backend/ml_models "$BACKUP_DIR/"
fi

# Backup configuration
echo "⚙️  Backing up configuration..."
cp backend/.env "$BACKUP_DIR/.env.backup"

echo "✅ Backup completed: $BACKUP_DIR"

