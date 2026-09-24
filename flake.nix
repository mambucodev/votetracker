{
  description = "VoteTracker - School grade management application";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      nixpkgsFor = forAllSystems (system: import nixpkgs { inherit system; });
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgsFor.${system};
          python = pkgs.python3;
        in
        rec {
          default = votetracker;
          votetracker = python.pkgs.buildPythonApplication {
            pname = "votetracker";
            version = "2.9.0";
            pyproject = true;

            src = ./.;

            nativeBuildInputs = [
              python.pkgs.setuptools
              python.pkgs.wheel
              pkgs.qt6.wrapQtAppsHook
            ];

            buildInputs = [
              pkgs.qt6.qtbase
              pkgs.qt6.qtsvg
            ];

            propagatedBuildInputs = with python.pkgs; [
              pyside6
              reportlab
              requests
              lxml
            ];

            checkPhase = ''
              runHook preCheck
              export QT_QPA_PLATFORM=offscreen
              ${python.interpreter} -m unittest discover -s tests -p "test_*.py"
              runHook postCheck
            '';

            postInstall = ''
              install -Dm644 scripts/votetracker.desktop $out/share/applications/votetracker.desktop
              for size in 16 24 32 48 64 128 256 512; do
                if [ -f "icons/icon-''${size}.png" ]; then
                  install -Dm644 "icons/icon-''${size}.png" \
                    "$out/share/icons/hicolor/''${size}x''${size}/apps/votetracker.png"
                fi
              done
            '';

            preFixup = ''
              makeWrapperArgs+=("''${qtWrapperArgs[@]}")
            '';

            meta = with pkgs.lib; {
              description = "School grade management application";
              homepage = "https://github.com/mambucodev/votetracker";
              license = licenses.mit;
              mainProgram = "votetracker";
              platforms = platforms.linux;
            };
          };
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/votetracker";
        };
      });

      devShells = forAllSystems (system:
        let
          pkgs = nixpkgsFor.${system};
        in
        {
          default = pkgs.mkShell {
            inputsFrom = [ self.packages.${system}.default ];
            packages = [
              pkgs.ruff
              pkgs.python3Packages.pyinstaller
            ];
            shellHook = ''
              export QT_QPA_PLATFORM=''${QT_QPA_PLATFORM:-offscreen}
            '';
          };
        }
      );
    };
}
