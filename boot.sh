#!/usr/bin/env bash
# Boot estilo macOS: tela de carregamento (Plymouth) preta com o logo branco do Ubuntu no centro e barra fina,
# e menu do GRUB escuro com fonte Inter. Não mexe na linha do kernel nem nas entradas do menu.
#
# Rode como seu usuário (sem sudo na frente):
#   bash ~/tema-macos/boot.sh                  aplica (com Windows no PC, o menu do GRUB aparece por 5 s em todo boot)
#   bash ~/tema-macos/boot.sh --esconder-menu  aplica com o menu escondido (aperte Esc no boot para vê-lo)
#   bash ~/tema-macos/boot.sh --plymouth       só troca a tela de carregamento (não mexe no GRUB)
#   bash ~/tema-macos/boot.sh --desfazer       volta tudo como era
# O logo da placa-mãe ainda pode piscar antes, por ~1 s: é o firmware (UEFI), antes do Linux carregar.
set -euo pipefail
[[ $EUID -eq 0 ]] && { echo "Rode sem sudo: bash $0"; exit 1; }

SRC="$HOME/tema-macos/boot"
B="$HOME/theme-backup-2026-10-24/boot"
GRUB_CFG_D=/etc/default/grub.d/90-tema-macos.cfg
THEME_DIR=/boot/grub/themes/tema-macos
PLY_DIR=/usr/share/plymouth/themes/tema-macos

check_and_update_grub() {
  echo "==> Gerando o menu do GRUB num arquivo de teste e validando antes de instalar"
  local tmp; tmp=$(sudo mktemp /boot/grub/grub.cfg.teste.XXXXXX)
  sudo grub-mkconfig -o "$tmp"
  sudo grub-script-check "$tmp"
  local before after
  before=$(sudo grep -cE '^\s*menuentry ' /boot/grub/grub.cfg || true)
  after=$(sudo grep -cE '^\s*menuentry ' "$tmp" || true)
  echo "    entradas no menu: antes $before, depois $after"
  if (( after < 1 || after < before )); then
    sudo rm -f "$tmp"
    echo "ERRO: o menu novo tem menos entradas que o atual; nada foi instalado." >&2
    return 1
  fi
  sudo rm -f "$tmp"
  sudo update-grub
}

if [[ "${1:-}" == "--desfazer" ]]; then
  sudo rm -f "$GRUB_CFG_D"
  sudo rm -rf "$THEME_DIR"
  check_and_update_grub
  sudo update-alternatives --set default.plymouth /usr/share/plymouth/themes/bgrt/bgrt.plymouth
  sudo update-alternatives --remove default.plymouth "$PLY_DIR/tema-macos.plymouth" 2>/dev/null || true
  sudo rm -rf "$PLY_DIR"
  sudo update-initramfs -u
  echo "Boot restaurado (GRUB e Plymouth originais)."
  exit 0
fi

install_plymouth() {
  echo "==> Tela de carregamento (Plymouth): logo do Ubuntu + barra fina, sem o logo da placa-mãe"
  [[ -f "$SRC/plymouth/tema-macos/watermark.png" ]] || { echo "ERRO: falta $SRC/plymouth/tema-macos/watermark.png" >&2; exit 1; }
  sudo rm -rf "$PLY_DIR"
  sudo cp -r "$SRC/plymouth/tema-macos" "$PLY_DIR"
  sudo update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth \
    "$PLY_DIR/tema-macos.plymouth" 150
  sudo update-alternatives --set default.plymouth "$PLY_DIR/tema-macos.plymouth"
  sudo update-initramfs -u
  grep -q 'splash' /proc/cmdline || echo "Aviso: o kernel não está com 'splash' na linha de boot; a tela pode não aparecer."
}

if [[ "${1:-}" == "--plymouth" ]]; then
  install_plymouth
  echo; echo "Pronto! Reinicie para ver. Desfazer: bash ~/tema-macos/boot.sh --desfazer"
  exit 0
fi

if [[ -f "$B/grub.cfg" ]]; then
  echo "==> Backup já existe em $B (mantido o original)"
else
  echo "==> Backup em $B"
  mkdir -p "$B"
  cp /etc/default/grub "$B/grub"
  cp -a /etc/default/grub.d "$B/grub.d"
  update-alternatives --query default.plymouth > "$B/plymouth-alternatives.txt"
  sudo cp /boot/grub/grub.cfg "$B/grub.cfg"; sudo chown "$USER:" "$B/grub.cfg"
  [[ -d /boot/grub/themes ]] && sudo cp -a /boot/grub/themes "$B/grub-themes" || true
fi

echo "==> Tema do GRUB"
sudo mkdir -p /boot/grub/themes
sudo rm -rf "$THEME_DIR"
sudo cp -r "$SRC/grub-theme/tema-macos" "$THEME_DIR"
{
  echo "# Tema estilo macOS (tema-macos). Desfazer: bash ~/tema-macos/boot.sh --desfazer"
  echo "GRUB_THEME=\"$THEME_DIR/theme.txt\""
  echo 'GRUB_GFXMODE="1920x1080,auto"'
  # Com dois sistemas (Windows), o menu precisa aparecer para dar para escolher
  if [[ "${1:-}" != "--esconder-menu" ]] && sudo os-prober 2>/dev/null | grep -qi windows; then
    echo 'GRUB_TIMEOUT_STYLE=menu'
    echo 'GRUB_TIMEOUT=5'
  fi
} | sudo tee "$GRUB_CFG_D" >/dev/null
check_and_update_grub

install_plymouth
echo
echo "Pronto! Reinicie para ver. Desfazer: bash ~/tema-macos/boot.sh --desfazer"
