#!/bin/bash
# Anna Kitney Wellness Chatbot - GitHub Backup Script
# Repository: https://github.com/sam9s/racen-annakitney.git
#
# Usage: ./backup_to_github.sh "Your commit message"
# Or just: ./backup_to_github.sh (uses auto-generated message with timestamp)
#
# Requires: GITHUB_PERSONAL_ACCESS_TOKEN environment variable

set -e

REPO_NAME="sam9s/racen-annakitney.git"
BRANCH="main"

# Check for token
if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
    echo "ERROR: GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set."
    echo "Please ensure the token is configured in Replit Secrets."
    exit 1
fi

# Build authenticated URL (token is read from env, never displayed)
AUTH_URL="https://${GITHUB_PERSONAL_ACCESS_TOKEN}@github.com/${REPO_NAME}"

# Configure remote with authenticated URL
if git remote | grep -q "^origin$"; then
    git remote set-url origin "$AUTH_URL"
else
    git remote add origin "$AUTH_URL"
fi

# Stage all changes
echo "Staging changes..."
git add .

# Get commit message (use argument or auto-generate)
if [ -n "$1" ]; then
    COMMIT_MSG="$1"
else
    COMMIT_MSG="Backup: $(date '+%Y-%m-%d %H:%M:%S')"
fi

# Commit if there are changes
if git diff --cached --quiet; then
    echo "No changes to commit."
else
    echo "Committing: $COMMIT_MSG"
    git commit -m "$COMMIT_MSG"
fi

# Push to GitHub (force to ensure Replit is source of truth)
echo "Pushing to GitHub..."
git push -u origin "$BRANCH" --force

# Reset remote URL to non-authenticated version (security: don't leave token in git config)
git remote set-url origin "https://github.com/${REPO_NAME}"

echo ""
echo "Backup complete! Changes pushed to: https://github.com/${REPO_NAME}"
