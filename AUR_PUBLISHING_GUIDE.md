# Publishing VoteTracker to AUR

This guide walks you through publishing VoteTracker to the Arch User Repository (AUR).

## Status: Ready to Publish ✅

All preparation work is complete:
- ✅ MIT LICENSE file added to repository
- ✅ AUR-ready PKGBUILD created (`scripts/PKGBUILD.aur`)
- ✅ pyproject.toml updated with SPDX license format
- ✅ Package tested and builds successfully
- ✅ All files committed and pushed to GitHub

## Prerequisites

Before you start, you need:

### 1. AUR Account
- Register at https://aur.archlinux.org/register
- Verify your email

### 2. SSH Key Setup
Generate a dedicated SSH key for AUR:

```bash
# Generate key
ssh-keygen -f ~/.ssh/aur
# Press Enter for no passphrase or set one

# Copy public key
cat ~/.ssh/aur.pub
```

Go to https://aur.archlinux.org/account/ and paste your public key in "My Account" settings.

### 3. SSH Config
Add to `~/.ssh/config`:

```
Host aur.archlinux.org
  IdentityFile ~/.ssh/aur
  User aur
```

Test the connection:
```bash
ssh -T aur@aur.archlinux.org
# Should say: "Hi <username>! You've successfully authenticated..."
```

### 4. Install Required Tools
```bash
sudo pacman -S base-devel git
```

## Publishing Steps

### Step 1: Check Package Name Availability

```bash
# Search if votetracker already exists
yay -Ss votetracker
# Or visit: https://aur.archlinux.org/packages/?K=votetracker
```

If the package doesn't exist, you're good to go!

### Step 2: Clone AUR Repository

```bash
# Clone the empty AUR repo (will be created on first push)
git clone ssh://aur@aur.archlinux.org/votetracker.git aur-votetracker
cd aur-votetracker
```

### Step 3: Add PKGBUILD

```bash
# Copy the AUR-ready PKGBUILD
cp /path/to/votetracker/scripts/PKGBUILD.aur ./PKGBUILD

# Edit the maintainer line
vim PKGBUILD
# Change: # Maintainer: Your Name <your@email.com>
# To:     # Maintainer: Your Actual Name <your@actual-email.com>
```

### Step 4: Generate .SRCINFO

```bash
# Generate the machine-readable package info
makepkg --printsrcinfo > .SRCINFO
```

### Step 5: Create LICENSE for AUR Submission

The AUR recommends adding a license file for the package submission itself (separate from your software license):

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

### Step 6: Test Build (Important!)

```bash
# Test that the package builds correctly
makepkg -sf

# If successful, you'll have: votetracker-2.7.0-1-any.pkg.tar.zst

# Optional: Test install
sudo pacman -U votetracker-2.7.0-1-any.pkg.tar.zst
```

### Step 7: Commit and Push to AUR

```bash
# Add files
git add PKGBUILD .SRCINFO LICENSE

# Commit (first commit should be descriptive)
git commit -m "Initial upload: votetracker 2.7.0

School grade management application with ClasseViva integration.

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

### Step 8: Verify Publication

1. Visit: https://aur.archlinux.org/packages/votetracker
2. You should see your package listed!

## Updating the Package

When you release a new version of VoteTracker:

### Step 1: Update Version in PKGBUILD

```bash
cd aur-votetracker

# Edit PKGBUILD
vim PKGBUILD
# Update pkgver=2.7.0 to new version
# Reset pkgrel=1

# Generate new checksum
makepkg -g
# Copy the sha256sum and update it in PKGBUILD
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

## Users Can Now Install

Once published, users can install with:

```bash
# Using yay
yay -S votetracker

# Using paru
paru -S votetracker

# Manual with makepkg
git clone https://aur.archlinux.org/votetracker.git
cd votetracker
makepkg -si
```

## Maintenance Tips

### Handling Out-of-Date Flags
- Users can flag your package as "out-of-date" when a new version is released
- Check your AUR account regularly for notifications
- Update promptly to keep users happy

### Orphaning/Disowning
- If you no longer want to maintain the package, you can "disown" it
- Go to: https://aur.archlinux.org/packages/votetracker
- Click "Disown Package" (only visible to maintainer)

### Co-maintainers
- You can add co-maintainers who can also update the package
- Add their usernames in the package settings

## Troubleshooting

### "Repository not found" error
- Make sure you've set up SSH keys correctly
- Test: `ssh -T aur@aur.archlinux.org`

### "Package already exists"
- The package name is taken
- Consider: votetracker-git, votetracker-bin, or a different name

### Build fails
- Test locally first with `makepkg -sf`
- Check dependencies are correct
- Verify the source URL is accessible

### Permission denied
- Check SSH config is correct
- Verify you're the package maintainer

## Resources

- [AUR Submission Guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines)
- [PKGBUILD Documentation](https://wiki.archlinux.org/title/PKGBUILD)
- [Python Package Guidelines](https://wiki.archlinux.org/title/Python_package_guidelines)
- [AUR User Guidelines](https://wiki.archlinux.org/title/AUR_User_Guidelines)

## Current PKGBUILD Details

**Package Name:** votetracker
**Current Version:** 2.7.0
**Architecture:** any (pure Python)
**License:** MIT
**Dependencies:** python, pyside6, python-reportlab, python-requests, python-installer
**Build Dependencies:** python-build, python-setuptools, python-wheel
**Source:** GitHub release tarball (v2.7.0)
**Package Size:** ~211 KB compressed

---

**Ready to publish!** Follow the steps above to make VoteTracker available on the AUR. 🚀
