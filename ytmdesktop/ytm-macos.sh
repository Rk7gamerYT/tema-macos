#!/usr/bin/env bash
# Abre o YouTube Music Desktop. Enquanto o Flatpak instalado for o mesmo de quando a
# correção foi feita (aplicar.sh), roda a cópia corrigida em ~/.local/share/ytmd-app;
# se o Flatpak atualizar, volta sozinho para a versão oficial.
APP=app.ytmdesktop.ytmdesktop
FIX="$HOME/.local/share/ytmd-app"

flatpak ps --columns=application 2>/dev/null | grep -qx "$APP" || rm -rf "$FIX.old"
atual=$(flatpak info --user -c "$APP" 2>/dev/null)
args=()
if [[ -n "$atual" && -f "$FIX/.origem" && "$(cat "$FIX/.origem")" == "$atual" ]]; then
  args=(--app-path="$FIX")
fi

exec setsid -f flatpak run --branch=stable --arch=x86_64 "${args[@]}" --command=start-ytmdesktop "$APP" "$@" >/dev/null 2>&1
