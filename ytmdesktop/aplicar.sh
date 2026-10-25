#!/usr/bin/env bash
# Aplica o tema macOS escuro no YouTube Music Desktop (Flatpak app.ytmdesktop.ytmdesktop).
# Uso: bash ~/tema-macos/ytmdesktop/aplicar.sh        (aplica / atualiza o CSS)
#      bash ~/tema-macos/ytmdesktop/aplicar.sh --off  (volta ao visual original)
#      bash ~/tema-macos/ytmdesktop/aplicar.sh --sem-ambilight  (tema sem o brilho atrás do player)
set -euo pipefail

APP=app.ytmdesktop.ytmdesktop
DIR="$HOME/.var/app/$APP/config/YouTube Music Desktop App"
CFG="$DIR/config.json"
CSS="$DIR/macos-dark.css"
SRC="$(dirname "$(readlink -f "$0")")/macos-dark.css"

if [[ ! -f "$CFG" ]]; then
  echo "Abra o YouTube Music Desktop uma vez antes (flatpak run $APP)."; exit 1
fi

# O app vigia o arquivo e recarrega o CSS sozinho quando ele muda.
# Escreve no lugar (sem renomear), senão o app desliga o CSS.
[[ "${1:-}" == "--off" ]] || cat "$SRC" > "$CSS"

rodando=0
if flatpak ps --columns=application | grep -qx "$APP"; then rodando=1; flatpak kill "$APP"; sleep 1; fi

tmp=$(mktemp)
if [[ "${1:-}" == "--off" ]]; then
  jq '.appearance.customCSSEnabled=false' "$CFG" > "$tmp"
else
  # Integração MPRIS fica no app por padrão; a notificação de troca de música fica a cargo do widget.
  jq --arg css "$CSS" '.appearance.customCSSEnabled=true | .appearance.customCSSPath=$css' "$CFG" > "$tmp"
fi
cat "$tmp" > "$CFG"; rm -f "$tmp"

# Cópia corrigida do app (fica carregando para sempre com o miniplayer novo do YouTube Music).
FIX="$HOME/.local/share/ytmd-app"
commit=$(flatpak info --user -c "$APP")
AMBI="$(dirname "$SRC")/ambilight.js"
[[ "${1:-}" == "--sem-ambilight" ]] && AMBI=""
assinatura="$commit${AMBI:+ $(sha256sum "$AMBI" | cut -c1-16)}"
if [[ "${1:-}" == "--off" ]]; then
  rm -rf "$FIX"
elif [[ ! -f "$FIX/.patch" || "$(cat "$FIX/.patch")" != "$assinatura" ]]; then
  ORIG="$(flatpak info --user -l "$APP")/files"
  # Monta ao lado e troca no fim, para não quebrar o app se ele estiver aberto.
  rm -rf "$FIX.new" "$FIX.old"; cp -a "$ORIG" "$FIX.new"
  if python3 -I "$(dirname "$SRC")/corrigir-carregamento.py" \
       "$ORIG/lib/youtube-music-desktop-app/resources/app.asar" \
       "$FIX.new/lib/youtube-music-desktop-app/resources/app.asar" ${AMBI:+"$AMBI"}; then
    echo "$commit" > "$FIX.new/.origem"; echo "$assinatura" > "$FIX.new/.patch"
    [[ -d "$FIX" ]] && mv "$FIX" "$FIX.old"
    mv "$FIX.new" "$FIX"
  else
    echo "Esta versão do app não precisa (ou não aceita) a correção; usando a oficial."; rm -rf "$FIX.new" "$FIX"
  fi
fi

# Atalho do menu/dock abre pelo ytm-macos.sh (usa a cópia corrigida quando existir).
if [[ "${1:-}" == "--off" ]]; then
  rm -f "$HOME/.local/share/applications/$APP.desktop" "$HOME/.local/bin/ytm-macos"
else
  mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications"
  ln -sf "$(dirname "$SRC")/ytm-macos.sh" "$HOME/.local/bin/ytm-macos"
  sed -e "s|^Exec=.*|Exec=$HOME/.local/bin/ytm-macos %U|" -e 's|^Name=.*|Name=YouTube Music|' \
    "$HOME/.local/share/flatpak/exports/share/applications/$APP.desktop" \
    > "$HOME/.local/share/applications/$APP.desktop"
fi

if (( rodando )) && [[ "${1:-}" == "--off" ]]; then setsid -f flatpak run "$APP" >/dev/null 2>&1
elif (( rodando )); then setsid -f "$HOME/.local/bin/ytm-macos"; fi
echo "Pronto."
