#!/bin/bash
# Anna Kitney Wellness Chatbot - GitHub Backup Script
# Repository: https://github.com/sam9s/racen-annakitney.git
#
# Usage: ./backup_to_github.sh "Your commit message"
# Or just: ./backup_to_github.sh (uses auto-generated message with timestamp)

set -e

REPO_URL="https://github.com/sam9s/racen-annakitney.git"
BRANCH="main"

# Check if origin remote exists, if not add it
if ! git remote | grep -q "^origin$"; then
    echo "Adding origin remote..."
    git remote add origin "$REPO_URL"
fi

# Verify origin URL is correct
CURRENT_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ "$CURRENT_URL" != "$REPO_URL" ]; then
    echo "Updating origin URL to $REPO_URL..."
    git remote set-url origin "$REPO_URL"
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

# Push to GitHub
echo "Pushing to GitHub..."
echo "Note: You may be prompted for credentials."
echo "  Username: sam9s"
echo "  Password: Use your GITHUB_PERSONAL_ACCESS_TOKEN value"
echo ""

git push -u origin "$BRANCH"

echo ""
echo "Backup complete! Changes pushed to: $REPO_URL"
