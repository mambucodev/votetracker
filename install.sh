#!/bin/bash
# install.sh - Install VoteTracker on Linux without pip
# Works on Arch, Debian, Fedora, etc.

set -e

PREFIX="${PREFIX:-$HOME/.local}"
LIB_DIR="$PREFIX/lib/votetracker"
BIN_DIR="$PREFIX/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "VoteTracker Installer"
echo "====================="
echo "Install directory: $LIB_DIR"
echo "Binary directory:  $BIN_DIR"
echo ""

# Check dependencies
echo "Checking dependencies..."
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "ERROR: PySide6 not found!"
    echo ""
    echo "Install it with your package manager:"
    echo "  Arch:   sudo pacman -S pyside6"
    echo "  Debian: sudo apt install python3-pyside6"
    echo "  Fedora: sudo dnf install python3-pyside6"
    exit 1
fi
echo "✓ PySide6 found"

# Create directories
mkdir -p "$LIB_DIR/votetracker/pages"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# Copy files
echo "Installing files..."
cp votetracker/*.py "$LIB_DIR/votetracker/"
cp votetracker/pages/*.py "$LIB_DIR/votetracker/pages/"

# Create launcher
cat > "$BIN_DIR/votetracker" << EOF
#!/usr/bin/env python3
import sys
sys.path.insert(0, "$LIB_DIR")
from votetracker.__main__ import main
main()
EOF
chmod +x "$BIN_DIR/votetracker"

# Install .desktop file
sed "s|Exec=votetracker|Exec=$BIN_DIR/votetracker|" votetracker.desktop > "$DESKTOP_DIR/votetracker.desktop"

echo ""
echo "✓ Installation complete!"
echo ""
echo "Run with: votetracker"
echo "(Make sure $BIN_DIR is in your PATH)"
echo ""
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "Add to PATH with:"
    echo "  echo 'export PATH=\"\$PATH:$BIN_DIR\"' >> ~/.bashrc"
fi
