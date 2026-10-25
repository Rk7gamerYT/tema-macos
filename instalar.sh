#!/usr/bin/env bash
# Visual estilo macOS (WhiteSur Dark) para GNOME 50, com suporte a root/sudo e Flatpak.
# Rode como seu usuário normal (NÃO com sudo):  bash ~/tema-macos/instalar.sh
# A senha do sudo é pedida pelo próprio sudo; nada é salvo.
# Desfazer: bash ~/theme-backup-2026-10-24/restaurar.sh
set -euo pipefail

if [[ $EUID -eq 0 ]]; then echo "Rode sem sudo: bash $0"; exit 1; fi

SRC="$HOME/tema-macos/src"
U="$USER"
mkdir -p "$SRC"

say() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

say "Pacotes do Ubuntu (Kvantum, qt5ct/qt6ct, fontes Inter e JetBrains Mono, User Themes)"
sudo apt-get -o DPkg::Lock::Timeout=600 update
sudo apt-get -o DPkg::Lock::Timeout=600 install -y git sassc libglib2.0-dev-bin \
  qt-style-kvantum qt-style-kvantum-themes qt5ct qt6ct \
  fonts-inter fonts-jetbrains-mono \
  gnome-shell-extension-user-theme gnome-tweaks

say "Baixando WhiteSur (github.com/vinceliuice)"
for r in WhiteSur-gtk-theme WhiteSur-icon-theme WhiteSur-cursors WhiteSur-kde; do
  if [[ -d "$SRC/$r/.git" ]]; then git -C "$SRC/$r" pull -q --ff-only
  else git clone -q --depth=1 "https://github.com/vinceliuice/$r.git" "$SRC/$r"; fi
done

say "Tema GTK WhiteSur Dark no sistema (/usr/share/themes)"
cd "$SRC/WhiteSur-gtk-theme"
sudo ./install.sh -c dark -t default -N glassy
say "libadwaita/GTK4 do seu usuário (~/.config/gtk-4.0)"
./install.sh -c dark -t default -N glassy -l

say "Ícones WhiteSur e cursor WhiteSur (/usr/share/icons)"
cd "$SRC/WhiteSur-icon-theme" && sudo ./install.sh -t default -b
cd "$SRC/WhiteSur-cursors"   && sudo ./install.sh

say "Kvantum WhiteSur (/usr/share/Kvantum)"
sudo mkdir -p /usr/share/Kvantum
sudo cp -r "$SRC/WhiteSur-kde/Kvantum/"* /usr/share/Kvantum/
if find /usr/share/Kvantum -name 'WhiteSurDark.kvconfig' | grep -q .; then KV=WhiteSurDark; else KV=WhiteSur; fi
mkdir -p ~/.config/Kvantum
printf '[General]\ntheme=%s\n' "$KV" > ~/.config/Kvantum/kvantum.kvconfig

say "Aplicando no seu usuário"
I=org.gnome.desktop.interface
gsettings set $I gtk-theme 'WhiteSur-Dark'
gsettings set $I icon-theme 'WhiteSur-dark'
gsettings set $I cursor-theme 'WhiteSur-cursors'
gsettings set $I color-scheme 'prefer-dark'
gsettings set $I font-name 'Inter 11'
gsettings set $I document-font-name 'Inter 11'
gsettings set $I monospace-font-name 'JetBrains Mono 11'
gsettings set org.gnome.desktop.wm.preferences titlebar-font 'Inter Bold 11'
gsettings set org.gnome.desktop.wm.preferences button-layout 'close,minimize,maximize:'
gsettings set $I font-antialiasing 'rgba'
gsettings set $I font-hinting 'slight'

mkdir -p ~/.config/gtk-3.0
cat > ~/.config/gtk-3.0/settings.ini <<'EOF'
[Settings]
gtk-theme-name = WhiteSur-Dark
gtk-icon-theme-name = WhiteSur-dark
gtk-cursor-theme-name = WhiteSur-cursors
gtk-font-name = Inter 11
gtk-application-prefer-dark-theme = true
EOF

say "Extensões: User Themes (tema do painel) e Blur my Shell"
enable_ext() {  # adiciona à lista mesmo se o shell ainda não carregou a extensão
  gnome-extensions enable "$1" 2>/dev/null || python3 - "$1" <<'PY'
import sys, subprocess, ast
cur = ast.literal_eval(subprocess.check_output(["gsettings","get","org.gnome.shell","enabled-extensions"]).decode().replace("@as ",""))
if sys.argv[1] not in cur:
    subprocess.check_call(["gsettings","set","org.gnome.shell","enabled-extensions",str(cur+[sys.argv[1]])])
PY
}
enable_ext user-theme@gnome-shell-extensions.gcampax.github.com
dconf write /org/gnome/shell/extensions/user-theme/name "'WhiteSur-Dark'"
if ! gnome-extensions list | grep -q blur-my-shell@aunetx; then
  echo "Vai abrir uma janela do GNOME pedindo para instalar o Blur my Shell: clique em Instalar."
  gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell \
    --method org.gnome.Shell.Extensions.InstallRemoteExtension blur-my-shell@aunetx || true
fi
enable_ext blur-my-shell@aunetx || true
# Dock: Ubuntu Dock com desfoque do Blur my Shell (ver padronizar.sh). A Dash2Dock derrubava o shell: nunca ligar
dconf write /org/gnome/shell/extensions/blur-my-shell/dash-to-dock/blur true 2>/dev/null || true
gnome-extensions disable dash2dock-lite@icedman.github.com 2>/dev/null || true
dconf write /org/gnome/shell/extensions/blur-my-shell/panel/blur true 2>/dev/null || true
dconf write /org/gnome/shell/extensions/blur-my-shell/overview/blur true 2>/dev/null || true
dconf write /org/gnome/shell/extensions/blur-my-shell/appfolder/blur true 2>/dev/null || true

say "Root/sudo: mesmas configs GTK/Qt em /root"
sudo mkdir -p /root/.config/gtk-3.0 /root/.config/gtk-4.0 /root/.config/Kvantum /root/.config/qt5ct /root/.config/qt6ct
sudo cp ~/.config/gtk-3.0/settings.ini /root/.config/gtk-3.0/settings.ini
sudo cp -r ~/.config/gtk-4.0/. /root/.config/gtk-4.0/
sudo cp ~/.config/Kvantum/kvantum.kvconfig /root/.config/Kvantum/
sudo cp ~/.config/qt5ct/qt5ct.conf /root/.config/qt5ct/
sudo cp ~/.config/qt6ct/qt6ct.conf /root/.config/qt6ct/
# sudo mantém as variáveis de tema (não é regra de senha, só ambiente)
TMP=$(mktemp)
cat > "$TMP" <<'EOF'
# Tema estilo macOS: apps gráficos rodando com sudo usam o mesmo visual
Defaults env_keep += "GTK_THEME QT_QPA_PLATFORMTHEME QT_STYLE_OVERRIDE XCURSOR_THEME XCURSOR_SIZE"
EOF
sudo visudo -cf "$TMP" && sudo install -m 0440 "$TMP" /etc/sudoers.d/90-tema
rm -f "$TMP"
# Variáveis para todas as sessões (inclui pkexec, que limpa o ambiente do usuário)
sudo mkdir -p /etc/environment.d
sudo tee /etc/environment.d/90-tema.conf >/dev/null <<'EOF'
QT_QPA_PLATFORMTHEME=qt6ct
QT_STYLE_OVERRIDE=kvantum
XCURSOR_THEME=WhiteSur-cursors
XCURSOR_SIZE=24
EOF

say "Flatpak: acesso aos temas do sistema também"
sudo flatpak override --filesystem=/usr/share/themes:ro --filesystem=/usr/share/icons:ro \
  --env=GTK_THEME=WhiteSur-Dark --env=XCURSOR_THEME=WhiteSur-cursors || true

say "Pronto! Saia da sessão e entre de novo para tudo valer."
echo "Para desfazer: bash ~/theme-backup-2026-10-24/restaurar.sh"

# Dock do Ubuntu: translúcida como a do Mac (o resto está no padronizar.sh)
D=org.gnome.shell.extensions.dash-to-dock
gsettings set $D transparency-mode 'FIXED'
gsettings set $D background-opacity 0.4
gsettings set $D custom-background-color true
gsettings set $D background-color '#1c1c1e'
