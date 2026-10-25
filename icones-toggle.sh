#!/usr/bin/env bash
# Liga/desliga os ícones da área de trabalho (extensão DING do Ubuntu). Atalho: Super+Shift+D
E=ding@rastersoft.com
if gnome-extensions list --enabled | grep -qx "$E"; then
  gnome-extensions disable "$E"; notify-send -i user-desktop "Ícones da área de trabalho" "Desligados" 2>/dev/null
else
  gnome-extensions enable "$E"; notify-send -i user-desktop "Ícones da área de trabalho" "Ligados" 2>/dev/null
fi
true
