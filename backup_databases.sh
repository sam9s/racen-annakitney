#!/bin/bash
# Anna Kitney Wellness Chatbot - Database Backup Script
# Creates backups of both PostgreSQL and ChromaDB (vector) databases
#
# Usage: ./backup_databases.sh
# Backups are stored in: ./database_backups/

set -e

BACKUP_DIR="./database_backups"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "=== Anna Kitney Database Backup ==="
echo "Timestamp: $TIMESTAMP"
echo ""

# PostgreSQL Backup
echo "1. Backing up PostgreSQL database..."
if [ -n "$DATABASE_URL" ]; then
    PG_BACKUP_FILE="$BACKUP_DIR/postgresql_backup_$TIMESTAMP.sql"
    pg_dump "$DATABASE_URL" > "$PG_BACKUP_FILE"
    echo "   PostgreSQL backup saved to: $PG_BACKUP_FILE"
    echo "   Size: $(du -h "$PG_BACKUP_FILE" | cut -f1)"
else
    echo "   WARNING: DATABASE_URL not set. Skipping PostgreSQL backup."
fi

echo ""

# ChromaDB (Vector Database) Backup
echo "2. Backing up ChromaDB (vector database)..."
CHROMA_DIR="./chroma_db"
if [ -d "$CHROMA_DIR" ]; then
    CHROMA_BACKUP_DIR="$BACKUP_DIR/chroma_backup_$TIMESTAMP"
    cp -r "$CHROMA_DIR" "$CHROMA_BACKUP_DIR"
    echo "   ChromaDB backup saved to: $CHROMA_BACKUP_DIR"
    echo "   Size: $(du -sh "$CHROMA_BACKUP_DIR" | cut -f1)"
else
    echo "   WARNING: ChromaDB directory not found at $CHROMA_DIR. Skipping."
fi

echo ""
echo "=== Backup Complete ==="
echo ""

# Show recent backups
echo "Recent backups in $BACKUP_DIR:"
ls -lht "$BACKUP_DIR" | head -10

echo ""
echo "Tip: Run ./backup_to_github.sh to push database backups to GitHub"
