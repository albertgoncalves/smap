with import <nixpkgs> {};
mkShell {
    buildInputs = [
        (python3.withPackages (ps: with ps; [
            flake8
            matplotlib
            pandas
        ]))
        feh
        jq
        shellcheck
    ];
    shellHook = ''
        . .shellhook
    '';
}
