# Maintainer: Your Name <your@email.com>
pkgname=votetracker
pkgver=2.2.0
pkgrel=1
pkgdesc="School grade management application"
arch=('any')
license=('MIT')
depends=('python' 'pyside6' 'python-reportlab')

# No source - we use local files
source=()
sha256sums=()

package() {
    cd "$startdir"
    
    # Find Python version
    _pyver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    
    # Install Python package
    install -dm755 "$pkgdir/usr/lib/python$_pyver/site-packages/votetracker"
    install -dm755 "$pkgdir/usr/lib/python$_pyver/site-packages/votetracker/pages"
    
    install -Dm644 votetracker/*.py -t "$pkgdir/usr/lib/python$_pyver/site-packages/votetracker/"
    install -Dm644 votetracker/pages/*.py -t "$pkgdir/usr/lib/python$_pyver/site-packages/votetracker/pages/"
    
    # Install launcher script
    install -dm755 "$pkgdir/usr/bin"
    cat > "$pkgdir/usr/bin/votetracker" << 'EOF'
#!/usr/bin/env python3
from votetracker.__main__ import main
main()
EOF
    chmod +x "$pkgdir/usr/bin/votetracker"
    
    # Install .desktop file
    install -Dm644 votetracker.desktop "$pkgdir/usr/share/applications/votetracker.desktop"
}
