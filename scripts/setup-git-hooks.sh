#!/bin/bash
# Setup Git Hooks for Security Prevention
# This script installs pre-commit hooks to prevent accidental secret commits

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
HOOKS_SOURCE="$REPO_ROOT/.github/hooks"

echo "Setting up Git hooks..."

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Install pre-commit hook
if [ -f "$HOOKS_SOURCE/pre-commit" ]; then
    cp "$HOOKS_SOURCE/pre-commit" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit"
    echo "✓ Installed pre-commit hook"
else
    echo "⚠ Warning: pre-commit hook source not found at $HOOKS_SOURCE/pre-commit"
    exit 1
fi

# Configure git to run hooks
git config core.hooksPath ".github/hooks" 2>/dev/null || echo "Note: git 2.9+ will use .github/hooks automatically"

echo ""
echo "✓ Git hooks installed successfully!"
echo ""
echo "The following hooks are now active:"
echo "  - pre-commit: Prevents accidental secret commits"
echo ""
echo "To test the pre-commit hook:"
echo "  1. Try creating a test file with a fake API key:"
echo "     echo 'sk_test_0000000' > test.txt"
echo "  2. Stage it: git add test.txt"
echo "  3. Try to commit: git commit -m 'test'"
echo "  4. The hook should block this commit"
echo "  5. Clean up: rm test.txt && git reset HEAD test.txt"
