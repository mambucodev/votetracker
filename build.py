#!/usr/bin/env python3
"""
Build script for creating standalone executables.

Usage:
    python build.py              # Build for current platform
    python build.py --onefile    # Single file (slower startup)
    python build.py --appimage   # Create AppImage (Linux only)

Requirements:
    pip install pyinstaller
    
For AppImage (Linux):
    sudo pacman -S appimagetool  # Arch
    # or download from https://appimage.github.io/appimagetool/
"""

import subprocess
import sys
import platform
import shutil
from pathlib import Path


def build_pyinstaller(onefile: bool = False):
    """Build with PyInstaller."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "VoteTracker",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui", 
        "--hidden-import", "PySide6.QtWidgets",
    ]
    
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    # Platform-specific
    if platform.system() == "Windows":
        icon_path = Path("assets/icon.ico")
        if icon_path.exists():
            cmd.extend(["--icon", str(icon_path)])
    elif platform.system() == "Darwin":
        icon_path = Path("assets/icon.icns")
        if icon_path.exists():
            cmd.extend(["--icon", str(icon_path)])
        cmd.extend(["--osx-bundle-identifier", "com.votetracker.app"])
    
    cmd.append("votetracker/__main__.py")
    
    print(f"Building for {platform.system()}...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        output = "dist/VoteTracker" + (".exe" if onefile and platform.system() == "Windows" else "")
        print()
        print("=" * 50)
        print("Build successful!")
        print(f"Output: {output}")
        print("=" * 50)
        return True
    else:
        print("Build failed!")
        return False


def build_appimage():
    """Build AppImage for Linux."""
    if platform.system() != "Linux":
        print("AppImage is only supported on Linux")
        return False
    
    # Check for appimagetool
    if not shutil.which("appimagetool"):
        print("ERROR: appimagetool not found")
        print("Install with: sudo pacman -S appimagetool")
        return False
    
    # First build with PyInstaller (onedir)
    if not build_pyinstaller(onefile=False):
        return False
    
    # Create AppDir structure
    appdir = Path("dist/VoteTracker.AppDir")
    appdir.mkdir(exist_ok=True)
    
    # Move PyInstaller output
    shutil.copytree("dist/VoteTracker", appdir / "usr/bin", dirs_exist_ok=True)
    
    # Create AppRun
    apprun = appdir / "AppRun"
    apprun.write_text("""#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
exec "$HERE/usr/bin/VoteTracker" "$@"
""")
    apprun.chmod(0o755)
    
    # Copy .desktop file
    shutil.copy("votetracker.desktop", appdir / "votetracker.desktop")
    
    # Create simple icon (or copy if exists)
    icon_path = appdir / "votetracker.png"
    if not icon_path.exists():
        # Create placeholder
        icon_path.write_text("")  # AppImage will use default
    
    # Build AppImage
    print("\nCreating AppImage...")
    result = subprocess.run([
        "appimagetool", str(appdir), "dist/VoteTracker-x86_64.AppImage"
    ])
    
    if result.returncode == 0:
        print()
        print("=" * 50)
        print("AppImage created: dist/VoteTracker-x86_64.AppImage")
        print("=" * 50)
        return True
    
    return False


def main():
    if "--appimage" in sys.argv:
        build_appimage()
    elif "--onefile" in sys.argv:
        build_pyinstaller(onefile=True)
    else:
        build_pyinstaller(onefile=False)


if __name__ == "__main__":
    main()

