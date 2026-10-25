#!/usr/bin/env bash
# Tema WhiteSur no Firefox (abas e barra no estilo do Safari). Feche o Firefox antes.
# Uso: bash ~/tema-macos/firefox.sh             aplica
#      bash ~/tema-macos/firefox.sh --desfazer  remove (o tweaks.sh do WhiteSur desfaz)
# Funciona com o Firefox snap, deb ou Flatpak: o tweaks.sh encontra o perfil sozinho.
set -euo pipefail
[[ $EUID -eq 0 ]] && { echo "Rode sem sudo: bash $0"; exit 1; }
WS="$HOME/tema-macos/src/WhiteSur-gtk-theme"
[[ -d "$WS" ]] || { echo "Rode antes o instalar.sh (ele baixa o WhiteSur)."; exit 1; }
cd "$WS"
if [[ "${1:-}" == "--desfazer" ]]; then ./tweaks.sh -f -r; else ./tweaks.sh -f; fi
