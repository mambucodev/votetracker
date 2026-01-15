#!/bin/bash
# uninstall.sh - Remove VoteTracker

PREFIX="${PREFIX:-$HOME/.local}"
LIB_DIR="$PREFIX/lib/votetracker"
BIN_DIR="$PREFIX/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Removing VoteTracker..."

rm -rf "$LIB_DIR"
rm -f "$BIN_DIR/votetracker"
rm -f "$DESKTOP_DIR/votetracker.desktop"

echo "✓ VoteTracker removed"
echo ""
echo "Note: Your data is preserved at:"
echo "  ~/.local/share/votetracker/votes.db"
echo ""
echo "To remove data too: rm -rf ~/.local/share/votetracker"
