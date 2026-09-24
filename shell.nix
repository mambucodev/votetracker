{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: [
      ps.pyside6
      ps.reportlab
      ps.requests
      ps.lxml
    ]))
    pkgs.ruff
    pkgs.python3Packages.pyinstaller
    pkgs.rustc
    pkgs.cargo
    pkgs.rustfmt
    pkgs.clippy
    pkgs.pkg-config
    pkgs.gtk4
    pkgs.libadwaita
    pkgs.glib
  ];

  shellHook = ''
    export PYTHONPATH="$PWD/src:$PYTHONPATH"
    export QT_QPA_PLATFORM=''${QT_QPA_PLATFORM:-offscreen}
  '';
}
