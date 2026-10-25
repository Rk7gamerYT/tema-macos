#!/usr/bin/env bash
# Tela de login (GDM) no mesmo estilo macOS escuro: tema WhiteSur, fundo degradê, Inter, ícones e cursor WhiteSur.
# Rode como seu usuário (sem sudo na frente):  bash ~/tema-macos/login.sh
# Desfazer:                                    bash ~/tema-macos/login.sh --desfazer
# A tela de boot (Plymouth) não é alterada: a do Ubuntu já é escura e limpa (logo + spinner).
set -euo pipefail
[[ $EUID -eq 0 ]] && { echo "Rode sem sudo: bash $0"; exit 1; }

WS="$HOME/tema-macos/src/WhiteSur-gtk-theme"
B="$HOME/theme-backup-2026-10-24/gdm"
IMG=/usr/share/backgrounds/tema-macos-login.png
CONF=/usr/share/gdm/dconf/95-tema-macos

if [[ "${1:-}" == "--desfazer" ]]; then
  cd "$WS" && sudo ./tweaks.sh -g -r
  sudo rm -f "$CONF" "$IMG"
  [[ -f "$B/99-wpe-gui" ]] && sudo cp "$B/99-wpe-gui" /usr/share/gdm/dconf/99-wpe-gui
  sudo /usr/share/gdm/generate-config
  echo "Tela de login restaurada. Vale no próximo login/reinício."
  exit 0
fi

echo "==> Backup da configuração atual do GDM em $B"
mkdir -p "$B"
cp -a /usr/share/gdm/dconf/. "$B/" 2>/dev/null || true
cp -L /usr/share/gnome-shell/gdm-theme.gresource "$B/gdm-theme.gresource.antes"
update-alternatives --query gdm-theme.gresource > "$B/alternatives.txt" 2>/dev/null || true

echo "==> Fundo da tela de login (degradê azul/roxo)"
sudo install -m 0644 "$HOME/.local/share/backgrounds/macos-gradiente.png" "$IMG"

echo "==> Tema WhiteSur no GDM"
cd "$WS"
sudo ./tweaks.sh -g -b "$IMG" -nd

echo "==> Ícones, cursor, fontes e modo escuro no GDM"
sudo tee "$CONF" >/dev/null <<'EOF'
# Tema estilo macOS (tema-macos). Desfazer: bash ~/tema-macos/login.sh --desfazer
[org/gnome/desktop/interface]
color-scheme='prefer-dark'
accent-color='blue'
icon-theme='WhiteSur-dark'
cursor-theme='WhiteSur-cursors'
cursor-size=24
font-name='Inter 11'
clock-format='24h'
clock-show-weekday=true

[com/ubuntu/login-screen]
background-picture-uri='file:///usr/share/backgrounds/tema-macos-login.png'
background-size='cover'
background-repeat='no-repeat'
EOF
# O fundo do wpe-gui (99-wpe-gui) é lido depois do 95 e ganharia; desativa enquanto o tema estiver ativo
# (a cópia ficou no backup acima e volta com --desfazer)
sudo rm -f /usr/share/gdm/dconf/99-wpe-gui
sudo /usr/share/gdm/generate-config

echo
echo "Pronto! A tela de login nova aparece no próximo login (ou reinício)."
echo "Desfazer: bash ~/tema-macos/login.sh --desfazer"
