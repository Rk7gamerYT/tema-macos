#!/usr/bin/env bash
# Padronização final estilo macOS: menus (shell/GTK3/GTK4/Qt), atalhos, notificações, Nautilus, fontes.
# Rode como seu usuário (sem sudo):   bash ~/tema-macos/padronizar.sh
# Apps rodando como root (pede sudo): bash ~/tema-macos/padronizar.sh --root
# Desfazer:                           bash ~/tema-macos/padronizar.sh --desfazer
set -euo pipefail
[[ $EUID -eq 0 ]] && { echo "Rode sem sudo: bash $0"; exit 1; }

M="$HOME/tema-macos/menus"
B="$HOME/theme-backup-2026-10-24/padronizar"
SHELL_THEME="$HOME/.local/share/themes/WhiteSur-Dark-Mac"
KV_USER="$HOME/.config/Kvantum/WhiteSurDark"
MARK_START='/* >>> tema-macos'
GM="$HOME/.local/share/gnome-shell/extensions/globalmenu@ShiroOSL.github.io"
BARRA_EXT="$HOME/.local/share/gnome-shell/extensions/barra-mac@tema-macos"
BARRA_DCONF=(/org/gnome/shell/extensions/blur-my-shell/panel/ /org/gnome/shell/extensions/appindicator/
  /org/gnome/shell/extensions/globalmenu/ /org/gnome/shell/extensions/just-perfection/
  /org/gnome/shell/extensions/blur-my-shell/dash-to-dock/ /org/gnome/shell/extensions/dash-to-dock/)
strip_gtk4() { [[ -f "$1" ]] && sed -i "\|^${MARK_START//\*/\\*}|,\|^/\* <<< tema-macos \*/|d" "$1"; true; }

if [[ "${1:-}" == "--root" ]]; then
  echo "==> Mesmos menus e fontes para apps abertos como root"
  sudo mkdir -p /root/.config/gtk-3.0 /root/.config/gtk-4.0 /root/.config/Kvantum /root/.config/qt5ct /root/.config/qt6ct
  sudo cp ~/.config/gtk-3.0/gtk.css /root/.config/gtk-3.0/gtk.css
  sudo cp ~/.config/gtk-4.0/gtk.css /root/.config/gtk-4.0/gtk.css
  sudo cp -r "$KV_USER" /root/.config/Kvantum/
  sudo cp ~/.config/Kvantum/kvantum.kvconfig /root/.config/Kvantum/
  sudo cp ~/.config/qt5ct/qt5ct.conf /root/.config/qt5ct/
  sudo cp ~/.config/qt6ct/qt6ct.conf /root/.config/qt6ct/
  echo "Pronto."
  exit 0
fi

if [[ "${1:-}" == "--desfazer" ]]; then
  [[ -d "$B/dconf" ]] || { echo "Sem backup em $B"; exit 1; }
  if [[ -d "$B/barra" ]]; then  # barra superior estilo macOS
    gnome-extensions disable barra-mac@tema-macos 2>/dev/null; rm -rf "$BARRA_EXT"
    cp "$B/barra/globalmenu"/*.js "$GM/" 2>/dev/null
    for f in "$B/barra/dconf"/*.ini; do p=$(basename "$f" .ini | tr _ /); dconf reset -f "$p"; dconf load "$p" < "$f"; done
    rm -rf "$B/barra"
  fi
  dconf write /org/gnome/shell/extensions/user-theme/name "'WhiteSur-Dark'"
  rm -rf "$SHELL_THEME" "$KV_USER"
  rm -f ~/.config/gtk-3.0/gtk.css
  [[ -f "$B/gtk-3.0-gtk.css" ]] && cp "$B/gtk-3.0-gtk.css" ~/.config/gtk-3.0/gtk.css
  for f in gtk.css gtk-dark.css; do strip_gtk4 ~/.config/gtk-4.0/$f; done
  cp "$B/qt5ct.conf" ~/.config/qt5ct/qt5ct.conf; cp "$B/qt6ct.conf" ~/.config/qt6ct/qt6ct.conf
  for f in "$B"/dconf/*.ini; do
    p=$(basename "$f" .ini | tr _ /); dconf reset -f "$p"; dconf load "$p" < "$f"
  done
  echo "Se usou --root: sudo rm -f /root/.config/gtk-3.0/gtk.css /root/.config/gtk-4.0/gtk.css; sudo rm -rf /root/.config/Kvantum/WhiteSurDark"
  echo "Desfeito."
  exit 0
fi

echo "==> Backup em $B"
mkdir -p "$B"
DCONF_PATHS=(/org/gnome/shell/keybindings/ /org/gnome/desktop/wm/keybindings/ /org/gnome/shell/extensions/just-perfection/
  /org/gnome/shell/extensions/user-theme/ /org/gnome/nautilus/preferences/ /org/gnome/nautilus/icon-view/
  /org/gtk/gtk4/settings/file-chooser/ /org/gnome/desktop/wm/preferences/)
if [[ ! -d "$B/dconf" ]]; then
  mkdir -p "$B/dconf"
  for p in "${DCONF_PATHS[@]}"; do dconf dump "$p" > "$B/dconf/$(echo "$p" | tr / _).ini"; done
  [[ -f ~/.config/gtk-3.0/gtk.css ]] && cp ~/.config/gtk-3.0/gtk.css "$B/gtk-3.0-gtk.css"
  cp ~/.config/gtk-4.0/gtk.css "$B/gtk-4.0-gtk.css"
  cp ~/.config/qt5ct/qt5ct.conf ~/.config/qt6ct/qt6ct.conf "$B/"
fi

echo "==> Botões de janela tipo semáforo à esquerda"
gsettings set org.gnome.desktop.wm.preferences button-layout 'close,minimize,maximize:'
gsettings set org.gnome.desktop.wm.preferences action-double-click-titlebar 'toggle-maximize'

echo "==> Atalhos estilo macOS"
# Super+Espaço = busca (Spotlight); troca de teclado vai para Ctrl+Super+Espaço
gsettings set org.gnome.desktop.wm.keybindings switch-input-source "['<Control><Super>space', 'XF86Keyboard']"
gsettings set org.gnome.shell.keybindings toggle-overview "['<Super>space']"
# Shift+Super+3 tela inteira, 4 seleção de área, 5 barra de captura (com gravação)
gsettings set org.gnome.shell.keybindings screenshot "['<Shift><Super>3', '<Shift>Print']"
gsettings set org.gnome.shell.keybindings show-screenshot-ui "['<Shift><Super>4', 'Print']"
gsettings set org.gnome.shell.keybindings show-screen-recording-ui "['<Shift><Super>5', '<Ctrl><Shift><Alt>R']"
gsettings set org.gnome.shell.keybindings screenshot-window "['<Alt>Print']"

echo "==> Notificações no canto superior direito"
dconf write /org/gnome/shell/extensions/just-perfection/notification-banner-position 2

echo "==> Nautilus parecido com o Finder"
N=org.gnome.nautilus.preferences
gsettings set $N default-folder-viewer 'icon-view'
gsettings set $N click-policy 'double'
gsettings set $N show-delete-permanently false
gsettings set $N show-create-link false
gsettings set org.gnome.nautilus.icon-view default-zoom-level 'medium' 2>/dev/null || true
gsettings set org.gtk.gtk4.Settings.FileChooser sort-directories-first true
gsettings set org.gtk.gtk4.Settings.FileChooser show-hidden false

echo "==> Menus do shell (barra, logo, dock, Central de controle): tema WhiteSur-Dark-Mac"
mkdir -p "$SHELL_THEME/gnome-shell"
# Arquivo único (WhiteSur-Dark + ajustes no fim): com @import o shell dava prioridade às regras do WhiteSur
WS="$HOME/.themes/WhiteSur-Dark/gnome-shell"
{ head -1 "$M/gnome-shell.css"
  sed "s|url(\"assets/|url(\"file://$WS/assets/|g" "$WS/gnome-shell.css"
  tail -n +2 "$M/gnome-shell.css" | grep -v '^@import'; } > "$SHELL_THEME/gnome-shell/gnome-shell.css"
printf '[Desktop Entry]\nType=X-GNOME-Metatheme\nName=WhiteSur-Dark-Mac\n' > "$SHELL_THEME/index.theme"
dconf write /org/gnome/shell/extensions/user-theme/name "'WhiteSur-Dark-Mac'"

echo "==> Menus GTK3 e GTK4"
cp "$M/gtk3.css" ~/.config/gtk-3.0/gtk.css
for f in gtk.css gtk-dark.css; do
  [[ -f ~/.config/gtk-4.0/$f ]] || continue
  strip_gtk4 ~/.config/gtk-4.0/$f; cat "$M/gtk4.css" >> ~/.config/gtk-4.0/$f
done

echo "==> Qt (Kvantum): destaque azul e fontes Inter / JetBrains Mono"
rm -rf "$KV_USER"; mkdir -p "$KV_USER"
cp /usr/share/Kvantum/WhiteSur/WhiteSurDark.kvconfig /usr/share/Kvantum/WhiteSur/WhiteSurDark.svg "$KV_USER/"
sed -i -e 's/^highlight.color=.*/highlight.color=#0860f2/' -e 's/^inactive.highlight.color=.*/inactive.highlight.color=#0860f2/' \
       -e 's/^reduce_menu_opacity=.*/reduce_menu_opacity=12/' "$KV_USER/WhiteSurDark.kvconfig"
sed -i 's/#315bef/#0860f2/gI' "$KV_USER/WhiteSurDark.svg"
set_qt_fonts() {  # $1 arquivo, $2 sufixo de peso do Qt (5: ",50,0,0,0,0,0"; 6: ",400,0,0,0,0,0,0,0,0,0,1")
  python3 - "$1" "$2" <<'PY'
import sys, configparser
p, tail = sys.argv[1], sys.argv[2]
c = configparser.RawConfigParser(); c.optionxform = str; c.read(p)
if not c.has_section('Fonts'): c.add_section('Fonts')
c.set('Fonts', 'general', '"Inter,11,-1,5' + tail + '"')
c.set('Fonts', 'fixed', '"JetBrains Mono,11,-1,5' + tail + '"')
with open(p, 'w') as f: c.write(f, space_around_delimiters=False)
PY
}
set_qt_fonts ~/.config/qt5ct/qt5ct.conf ',50,0,0,0,0,0'
set_qt_fonts ~/.config/qt6ct/qt6ct.conf ',400,0,0,0,0,0,0,0,0,0,1'

echo "==> Barra superior estilo macOS (24px, vidro escuro, menus em português, relógio do Mac)"
if [[ ! -d "$B/barra/dconf" ]]; then
  mkdir -p "$B/barra/dconf"
  for p in "${BARRA_DCONF[@]}"; do dconf dump "$p" > "$B/barra/dconf/$(echo "$p" | tr / _).ini"; done
fi
# Menus globais em pt-BR e nome do app em negrito (o original fica em $B/barra/globalmenu)
python3 "$M/globalmenu-ptbr.py" "$GM" "$B/barra/globalmenu"
# Relógio "Sáb 25 de out. 10:30" e ícone da Central de Controle
rm -rf "$BARRA_EXT"; cp -r "$M/barra-mac@tema-macos" "$BARRA_EXT"
gnome-extensions enable barra-mac@tema-macos 2>/dev/null || \
  gsettings get org.gnome.shell enabled-extensions | grep -q "'barra-mac@tema-macos'" || \
  gsettings set org.gnome.shell enabled-extensions "$(gsettings get org.gnome.shell enabled-extensions | sed "s/]$/, 'barra-mac@tema-macos']/")"
# Minimizar com o Magic Lamp: a dock (Ubuntu Dock) informa onde fica cada ícone. O Magic Lamp chamava
# Main.overview.dash._redisplay(), que quebra o dash.js no GNOME 50; essa linha fica desligada.
ML="$HOME/.local/share/gnome-shell/extensions/compiz-alike-magic-lamp-effect@hermes83.github.com/extension.js"
[[ -f "$ML" ]] && sed -i 's|^\(\s*\)Main.overview.dash._redisplay();.*$|\1// Main.overview.dash._redisplay(); // tema-macos: quebra o dash.js no GNOME 50|' "$ML"
gsettings set org.gnome.desktop.wm.keybindings minimize "['<Super>h']"
# Vidro: desfoque do que está atrás (não só do papel de parede), cor vem do tema
BMS=/org/gnome/shell/extensions/blur-my-shell/panel
dconf write $BMS/static-blur false; dconf write $BMS/sigma 30
dconf write $BMS/override-background false; dconf write $BMS/brightness 0.9
# Ícones de apps na bandeja monocromáticos e do mesmo tamanho dos de status
AI=/org/gnome/shell/extensions/appindicator
dconf write $AI/icon-saturation 1.0; dconf write $AI/icon-size 16; dconf write $AI/icon-opacity 230
# Só o que o Mac mostra: sem Atividades, botão de desligar, layout de teclado e clima na barra
JP=/org/gnome/shell/extensions/just-perfection
dconf write $JP/activities-button false; dconf write $JP/power-icon false; dconf write $JP/keyboard-layout false
dconf write $JP/panel-size 24; dconf write $JP/panel-icon-size 15
dconf write $JP/panel-button-padding-size 6; dconf write $JP/panel-indicator-padding-size 3
dconf write $JP/weather false; dconf write $JP/world-clock false
dconf write $JP/clock-menu-position 1; dconf write $JP/clock-menu-position-offset 0
gsettings set org.gnome.desktop.interface clock-show-weekday true
gsettings set org.gnome.desktop.interface clock-show-date true
gsettings set org.gnome.desktop.interface clock-show-seconds false
dconf write /org/gnome/shell/extensions/user-theme/name "'Adwaita'"; sleep 2
dconf write /org/gnome/shell/extensions/user-theme/name "'WhiteSur-Dark-Mac'"

echo "==> Dock estilo Mac (Ubuntu Dock): embaixo, centralizada, vidro escuro com desfoque, pontinhos"
# A Dash2Dock Animated derrubava o GNOME Shell (assert do Clutter no dash.js): fica sempre desligada
gnome-extensions disable dash2dock-lite@icedman.github.com 2>/dev/null || true
D=org.gnome.shell.extensions.dash-to-dock
gsettings set $D dock-position BOTTOM; gsettings set $D extend-height false; gsettings set $D custom-theme-shrink true
gsettings set $D dock-fixed false; gsettings set $D autohide true; gsettings set $D intellihide true
gsettings set $D intellihide-mode ALL_WINDOWS
gsettings set $D transparency-mode FIXED; gsettings set $D background-opacity 0.4
gsettings set $D custom-background-color true; gsettings set $D background-color '#1c1c1e'
gsettings set $D running-indicator-style DOT; gsettings set $D click-action minimize
gsettings set $D show-trash false; gsettings set $D show-mounts false; gsettings set $D show-apps-at-top false
gsettings set $D apply-custom-theme false; gsettings set $D dash-max-icon-size 48
BD=/org/gnome/shell/extensions/blur-my-shell/dash-to-dock
dconf write $BD/blur true; dconf write $BD/static-blur false; dconf write $BD/override-background true
dconf write $BD/style-dash-to-dock 2; dconf write $BD/sigma 30; dconf write $BD/brightness 0.8
gnome-extensions enable ubuntu-dock@ubuntu.com 2>/dev/null || true

echo
echo "Menus em português e relógio novo aparecem depois de sair e entrar na sessão."
echo
echo "Pronto! Menus do shell já mudaram; apps abertos precisam ser reabertos."
echo "Para apps abertos como root: bash ~/tema-macos/padronizar.sh --root"
echo "Desfazer: bash ~/tema-macos/padronizar.sh --desfazer"
