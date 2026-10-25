#!/usr/bin/env python3
"""Uma imagem de fundo diferente em cada monitor (GNOME só aceita uma: monto uma imagem 'spanned').

Uso:
  python3 ~/tema-macos/fundo-por-monitor.py --list
  python3 ~/tema-macos/fundo-por-monitor.py DP-5=~/Imagens/a.jpg HDMI-3=~/Imagens/b.png
  python3 ~/tema-macos/fundo-por-monitor.py principal=a.jpg secundario=b.jpg
Monitores não citados mantêm a imagem da última vez (ficam em ~/tema-macos/fundos.json).
Obs.: com o wpe-gui rodando, os wallpapers animados ficam por cima; ao fechar o app, ele pode
trocar o fundo pela captura dele (opção "Fundo estático" nas configurações do wpe-gui).
"""
import json
import os
import subprocess
import sys
import time

from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from widgets import monitors, resolve  # noqa: E402

CONFIG = os.path.expanduser('~/tema-macos/fundos.json')
OUT_DIR = os.path.expanduser('~/.local/share/backgrounds')


def main():
    mons = monitors()
    cfg = json.load(open(CONFIG, encoding='utf-8')) if os.path.exists(CONFIG) else {}
    args = sys.argv[1:]
    if args == ['--list']:
        for m in mons:
            tag = ' (principal)' if m['primary'] else ''
            print(f"{m['connector']:8} {m['label']} {m['width']}x{m['height']}{tag}: {cfg.get(m['connector'], '-')}")
        return
    for arg in args:
        name, _, path = arg.partition('=')
        mon = resolve(name, mons)
        path = os.path.abspath(os.path.expanduser(path))
        if not mon or not os.path.isfile(path):
            raise SystemExit(f'Não entendi "{arg}" (monitor desconhecido ou arquivo inexistente). Veja --list.')
        cfg[mon['connector']] = path

    x0, y0 = min(m['x'] for m in mons), min(m['y'] for m in mons)
    w = max(m['x'] + m['width'] for m in mons) - x0
    h = max(m['y'] + m['height'] for m in mons) - y0
    canvas = Image.new('RGB', (w, h), (11, 16, 48))
    for m in mons:
        src = cfg.get(m['connector'])
        if not src or not os.path.isfile(src):
            print(f"Aviso: {m['connector']} sem imagem definida; fica com fundo liso.")
            continue
        img = ImageOps.fit(Image.open(src).convert('RGB'), (m['width'], m['height']), Image.LANCZOS)
        canvas.paste(img, (m['x'] - x0, m['y'] - y0))
    # Nome novo a cada vez: o GNOME guarda a imagem em cache pelo caminho
    for old in os.listdir(OUT_DIR):
        if old.startswith('fundo-por-monitor-'):
            os.remove(os.path.join(OUT_DIR, old))
    out = os.path.join(OUT_DIR, f'fundo-por-monitor-{int(time.time())}.png')
    canvas.save(out)
    with open(CONFIG, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    uri = 'file://' + out
    for key in ('picture-uri', 'picture-uri-dark'):
        subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', key, uri], check=True)
    subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-options', 'spanned'], check=True)
    print(f'Fundo aplicado ({w}x{h}): ' + ', '.join(f"{k}={os.path.basename(v)}" for k, v in cfg.items()))


if __name__ == '__main__':
    main()
