with import <nixpkgs> {};
mkShell {
    buildInputs = [
        (python38.withPackages(ps: with ps; [
            flake8
            matplotlib
            pandas
        ]))
        jq
        shellcheck
    ];
    shellHook = ''
        . .shellhook
    '';
}
