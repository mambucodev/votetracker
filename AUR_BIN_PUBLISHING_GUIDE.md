# Publishing votetracker-bin to AUR

Guide for publishing the pre-built binary version of VoteTracker to AUR.

## What is votetracker-bin?

The `-bin` package provides a pre-built binary version of VoteTracker:

### Advantages of -bin Package
- ✅ **Much faster installation** - No compilation needed (~8 seconds vs ~60 seconds)
- ✅ **No build dependencies** - Doesn't need python-build, python-setuptools, etc.
- ✅ **Smaller download** - Just downloads the binary from GitHub releases
- ✅ **Self-contained** - Binary includes Python and all dependencies
- ✅ **Works alongside source package** - Users can choose which to install

### Comparison

| Package | Size | Install Time | Dependencies | Source |
|---------|------|--------------|--------------|--------|
| `votetracker` | ~211 KB | ~60s | python, pyside6, python-reportlab, python-requests | GitHub source tarball |
| `votetracker-bin` | ~86 MB | ~8s | hicolor-icon-theme | GitHub release binary |

## Status: Ready to Publish ✅

- ✅ PKGBUILD created (`scripts/PKGBUILD.aur-bin`)
- ✅ Checksums generated
- ✅ Package tested and builds successfully
- ✅ Binary available in GitHub releases (v2.7.0+)

## Prerequisites

Same as the source package - you need:
1. AUR account
2. SSH keys configured
3. SSH config for aur.archlinux.org

See `AUR_PUBLISHING_GUIDE.md` for detailed setup instructions.

## Publishing Steps

### Step 1: Clone AUR Repository

```bash
# Clone the empty AUR repo for -bin package
git clone ssh://aur@aur.archlinux.org/votetracker-bin.git aur-votetracker-bin
cd aur-votetracker-bin
```

### Step 2: Add PKGBUILD

```bash
# Copy the AUR-ready PKGBUILD for -bin
cp /path/to/votetracker/scripts/PKGBUILD.aur-bin ./PKGBUILD

# Edit the maintainer line
vim PKGBUILD
# Change: # Maintainer: Your Name <your@email.com>
# To:     # Maintainer: Your Actual Name <your@actual-email.com>
```

### Step 3: Generate .SRCINFO

```bash
# Generate the machine-readable package info
makepkg --printsrcinfo > .SRCINFO
```

### Step 4: Create LICENSE (Optional)

```bash
cat > LICENSE << 'EOF'
SPDX-License-Identifier: 0BSD

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
EOF
```

### Step 5: Test Build

```bash
# Test that the package builds correctly
makepkg -sf

# This will download ~86 MB binary and create package
# Should complete in ~8 seconds
```

### Step 6: Commit and Push to AUR

```bash
# Add files
git add PKGBUILD .SRCINFO LICENSE

# Commit (first commit should be descriptive)
git commit -m "Initial upload: votetracker-bin 2.7.0

Pre-built binary version of VoteTracker school grade management application.

Advantages over source package:
- Faster installation (no compilation)
- No build dependencies required
- Self-contained binary with all dependencies

Features:
- Grade tracking with weighted averages
- Multi-year and multi-term support
- ClasseViva import with smart subject mapping
- PDF report card generation
- Statistics and charts
- Grade simulator"

# Push to AUR
git push origin master
```

### Step 7: Verify Publication

Visit: https://aur.archlinux.org/packages/votetracker-bin

## Updating the -bin Package

When you release a new version with GitHub workflow:

### Step 1: Update PKGBUILD

```bash
cd aur-votetracker-bin

# Edit PKGBUILD
vim PKGBUILD
# Update pkgver=2.7.0 to new version
# Reset pkgrel=1

# Download new binary to get checksum
curl -L -o VoteTracker-Linux "https://github.com/mambucodev/votetracker/releases/download/v2.8.0/VoteTracker-Linux"
sha256sum VoteTracker-Linux
# Update sha256sum in PKGBUILD (first hash)

# Download new desktop file to get checksum
curl -L -o votetracker.desktop "https://raw.githubusercontent.com/mambucodev/votetracker/v2.8.0/scripts/votetracker.desktop"
sha256sum votetracker.desktop
# Update sha256sum in PKGBUILD (second hash)

# OR use makepkg -g to get both
makepkg -g
```

### Step 2: Update .SRCINFO and Push

```bash
# Regenerate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Test build
makepkg -sf

# Commit and push
git add PKGBUILD .SRCINFO
git commit -m "Update to version X.Y.Z"
git push origin master
```

## Important Notes

### provides and conflicts
- `provides=('votetracker')` - This package satisfies dependencies for `votetracker`
- `conflicts=('votetracker')` - Can't install both source and -bin at the same time
- Users can switch between them: `pacman -S votetracker-bin` (replaces votetracker)

### Architecture
- `arch=('x86_64')` - Binary is x86_64 only (unlike source which is `any`)
- The GitHub workflow builds for x86_64 Linux

### Dependencies
- Only needs `hicolor-icon-theme` for icon system
- No Python dependencies needed (bundled in binary)
- Much simpler than source package

### Binary Size
- ~86 MB compressed package
- PyInstaller bundles Python + PySide6 + all dependencies
- This is normal and expected for a self-contained binary

## Automation Tip

You can create a script to update both packages at once:

```bash
#!/bin/bash
# update-aur-packages.sh

VERSION="$1"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "Updating votetracker to $VERSION..."
cd ~/aur-votetracker
vim PKGBUILD  # Update version
makepkg -g
makepkg --printsrcinfo > .SRCINFO
makepkg -sf
git add PKGBUILD .SRCINFO
git commit -m "Update to version $VERSION"
git push

echo "Updating votetracker-bin to $VERSION..."
cd ~/aur-votetracker-bin
vim PKGBUILD  # Update version
makepkg -g
makepkg --printsrcinfo > .SRCINFO
makepkg -sf
git add PKGBUILD .SRCINFO
git commit -m "Update to version $VERSION"
git push

echo "Done! Both packages updated."
```

## Users Can Install

Once published, users can choose:

```bash
# Install pre-built binary (faster, larger)
yay -S votetracker-bin

# OR install from source (slower, smaller)
yay -S votetracker

# Switch from one to the other
yay -S votetracker-bin  # Replaces votetracker if installed
```

## Current PKGBUILD Details

**Package Name:** votetracker-bin
**Current Version:** 2.7.0
**Architecture:** x86_64
**License:** MIT
**Dependencies:** hicolor-icon-theme
**Provides:** votetracker
**Conflicts:** votetracker
**Source:** GitHub release binary (VoteTracker-Linux)
**Package Size:** ~86 MB compressed

## Troubleshooting

### Binary not found in release
- Make sure the GitHub workflow ran successfully for the tag
- Check: https://github.com/mambucodev/votetracker/releases/tag/v2.7.0
- Verify `VoteTracker-Linux` is attached to the release

### Wrong checksum
- Re-download the binary and regenerate: `makepkg -g`
- Make sure you're using the correct version tag in URLs

### Binary doesn't execute
- Check if binary has execute permissions: `chmod +x VoteTracker-Linux`
- The PKGBUILD uses `install -Dm755` which sets execute permission

### Package conflicts with votetracker
- This is expected! Only one can be installed at a time
- Use `pacman -S votetracker-bin` to replace `votetracker`

## Resources

- [Binary packages in AUR](https://wiki.archlinux.org/title/AUR_submission_guidelines#Rules_of_submission)
- [AUR Package Naming](https://wiki.archlinux.org/title/AUR_submission_guidelines#Package_naming)
- [PKGBUILD provides/conflicts](https://wiki.archlinux.org/title/PKGBUILD#provides)

---

**Ready to publish votetracker-bin!** Follow the steps above. 🚀

Users will appreciate having the choice between fast installation (bin) and smaller package (source)!
