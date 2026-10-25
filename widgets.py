#!/usr/bin/env python3
"""Widgets estilo macOS para a extensão Desktop Widgets (azclock), configuráveis por monitor.

A configuração fica em ~/tema-macos/widgets.json. Exemplos:
  python3 ~/tema-macos/widgets.py --list
  python3 ~/tema-macos/widgets.py --monitor DP-5 --add relogio --pos top-right
  python3 ~/tema-macos/widgets.py --monitor HDMI-3 --remove sistema
  python3 ~/tema-macos/widgets.py --monitor HDMI-3 --clear
  python3 ~/tema-macos/widgets.py --cidade "Campinas"
  python3 ~/tema-macos/widgets.py            (só reaplica o widgets.json)

Monitores: nome do conector (DP-5, HDMI-3...), ou "principal" / "secundario".
Widgets: relogio, tempo, sistema, relogio-analogico, midia (Tocando agora: extensão midia@tema-macos).
Posições: top-left, top-right, bottom-left, bottom-right, top-center, bottom-center, center.
Desfazer: dconf reset -f /org/gnome/shell/extensions/azclock/
          (midia: gnome-extensions disable midia@tema-macos)
"""
import argparse
import json
import shutil
import os
import subprocess
import sys
import unicodedata
import uuid

import gi
gi.require_version('GWeather', '4.0')
from gi.repository import Gio, GLib, GWeather  # noqa: E402

ROOT = '/org/gnome/shell/extensions/azclock/'
CONFIG = os.path.expanduser('~/tema-macos/widgets.json')
# O widget "midia" não é do Desktop Widgets (que não tem botões clicáveis): é a extensão midia@tema-macos,
# que lê as posições deste arquivo e se atualiza sozinha quando ele muda.
MIDIA_UUID = 'midia@tema-macos'
MIDIA_SRC = os.path.expanduser('~/tema-macos/' + MIDIA_UUID)
MIDIA_EXT = os.path.expanduser('~/.local/share/gnome-shell/extensions/' + MIDIA_UUID)
MIDIA_CONFIG = os.path.expanduser('~/.config/tema-macos/midia.json')
CARD = 'rgba(28, 28, 36, 0.55)'
FONT = "(true, 'Inter')"
SHADOW = "(true, 'rgba(0, 0, 0, 0.35)', 0, 2, 0, 6)"
MARGIN = 40   # px da borda da tela
GAP = 20      # px entre widgets empilhados no mesmo canto
# Altura aproximada de cada widget, para empilhar vários no mesmo canto
HEIGHT = {'relogio': 150, 'tempo': 250, 'sistema': 150, 'relogio-analogico': 230, 'midia': 170}
POSITIONS = {
    'top-left': ('Top_Left', 0, 0), 'top-right': ('Top_Right', 1, 0),
    'bottom-left': ('Bottom_Left', 0, 1), 'bottom-right': ('Bottom_Right', 1, 1),
    'top-center': ('Center_Top', 0.5, 0), 'bottom-center': ('Center_Bottom', 0.5, 1),
    'center': ('Center', 0.5, 0.5),
}
DEFAULT = {
    'cidade': 'São Paulo',
    'monitores': {
        'principal': [{'widget': 'relogio', 'pos': 'top-right'}, {'widget': 'tempo', 'pos': 'top-right'},
                      {'widget': 'midia', 'pos': 'top-right'}],
        'secundario': [{'widget': 'sistema', 'pos': 'top-right'}],
    },
}


def write(path, key, value):
    subprocess.run(['dconf', 'write', path + key, value], check=True)


def q(s):
    return GLib.Variant('s', s).print_(False)


def norm(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def monitors():
    """Monitores na ordem do GNOME (a mesma que a extensão usa como monitorIndex)."""
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    _serial, physical, logical, _props = bus.call_sync(
        'org.gnome.Mutter.DisplayConfig', '/org/gnome/Mutter/DisplayConfig', 'org.gnome.Mutter.DisplayConfig',
        'GetCurrentState', None, None, Gio.DBusCallFlags.NONE, -1, None).unpack()
    modes = {}
    for (connector, _vendor, model, _serial2), mode_list, props in physical:
        cur = next((m for m in mode_list if m[6].get('is-current')), mode_list[0])
        modes[connector] = (cur[1], cur[2], model, props.get('display-name', model))
    result = []
    for index, (x, y, scale, transform, primary, mons, _p) in enumerate(logical):
        connector = mons[0][0]
        w, h, model, label = modes[connector]
        if transform % 2:  # girado 90/270 graus
            w, h = h, w
        result.append({'index': index, 'connector': connector, 'model': model, 'label': label,
                       'primary': primary, 'x': x, 'y': y, 'width': round(w / scale), 'height': round(h / scale)})
    return result


def resolve(name, mons):
    n = name.lower()
    if n in ('principal', 'primary'):
        return next((m for m in mons if m['primary']), None)
    if n in ('secundario', 'secundário', 'secondary'):
        return next((m for m in mons if not m['primary']), None)
    return next((m for m in mons if m['connector'].lower() == n or m['model'].lower() == n), None)


def find_city(name):
    want = norm(name)
    stack = [GWeather.Location.get_world()]
    found = None
    while stack:
        loc = stack.pop()
        if loc.get_level() == GWeather.LocationLevel.CITY and norm(loc.get_name()) == want:
            if loc.get_country() == 'BR' or found is None:
                found = loc
        child = loc.next_child(None)
        while child:
            stack.append(child)
            child = loc.next_child(child)
    return found


def text(name, kind, size, weight, **extra):
    keys = {'name': q(name), 'element-type': q(kind), 'font-size': str(size), 'font-weight': str(weight),
            'font-family-override': FONT, 'foreground-color': q('white'), 'shadow': SHADOW}
    keys.update(extra)
    return keys


def elements_for(kind, align, city):
    if kind == 'relogio':
        return 'Relógio', [
            text('Hora', 'Digital_Clock', 84, 200, **{'date-format': q('%H:%M'), 'text-align-x': q(align)}),
            text('Data', 'Digital_Clock', 17, 500, **{'date-format': q('%A, %-d de %B'),
                                                     'foreground-color': q('rgba(255, 255, 255, 0.75)'),
                                                     'text-align-x': q(align)}),
        ], 4
    if kind == 'relogio-analogico':
        return 'Relógio analógico', [{'name': q('Analógico'), 'element-type': q('Analog_Clock'),
                                      'clock-size': '200', 'second-hand-visible': 'true'}], 4
    if kind == 'tempo':
        keys = text('Tempo', 'Weather_Element', 12, 400, **{
            'polling-interval': '900', 'temperature-unit': q('Celsius'), 'icon-color': q('white'),
            'current-weather-icon-type': q('Full_Color'), 'show-hourly-forecast': 'false',
            'show-daily-forecast': 'true', 'max-daily-forecasts': '5', 'current-temp-font-size': '34',
            'show-daily-forecast-thermometer-scale': 'true'})
        loc = find_city(city)
        if loc:
            keys['locations'] = '[<%s>]' % loc.serialize().print_(True)
        else:
            print(f'Aviso: cidade "{city}" não encontrada; o widget de tempo fica sem local.')
        return 'Tempo', [keys], 4
    if kind == 'sistema':
        return 'Sistema', [
            text('Título', 'Text_Label', 11, 700, **{'text': q('SISTEMA'), 'text-align-x': q('Start'),
                                                    'foreground-color': q('rgba(255, 255, 255, 0.55)')}),
            {**text('Stats', 'Command_Label', 12, 400, **{
                'command': q(os.path.expanduser('~/.local/bin/widget-sistema')),
                'polling-enabled': 'true', 'polling-interval': '2000', 'text-align-x': q('Start'),
                'line-alignment': q('Start')}),
             'font-family-override': "(true, 'JetBrains Mono')"},
        ], 8
    raise SystemExit(f'Widget desconhecido: {kind}. Use: {", ".join(HEIGHT)}')


def write_widget(name, anchor, location, elements, spacing):
    wid = str(uuid.uuid4())
    path = f'{ROOT}widget-data/{wid}/'
    write(path, 'name', q(name))
    write(path, 'anchor-point', q(anchor))
    write(path, 'location-data', q(json.dumps(location)))
    write(path, 'convert-old-location-done', 'true')
    write(path, 'show-background', 'true')
    write(path, 'background-color', q(CARD))
    write(path, 'border-radius', '22')
    write(path, 'show-border', 'true')
    write(path, 'border-width', '1')
    write(path, 'border-color', q('rgba(255, 255, 255, 0.08)'))
    write(path, 'padding', '(18, 26, 18, 26)')
    write(path, 'spacing', str(spacing))
    ids = []
    for keys in elements:
        eid = str(uuid.uuid4())
        for k, v in keys.items():
            write(f'{path}element-data/{eid}/', k, v)
        ids.append(eid)
    write(path, 'elements', '[' + ', '.join("{%s: <{'enabled': <true>}>}" % q(e) for e in ids) + ']')
    return wid


def install_midia(enable):
    """Copia a extensão Tocando agora do ~/tema-macos e liga/desliga."""
    if enable and os.path.isdir(MIDIA_SRC):
        os.makedirs(MIDIA_EXT, exist_ok=True)
        for f in os.listdir(MIDIA_SRC):
            shutil.copy2(os.path.join(MIDIA_SRC, f), MIDIA_EXT)
    enabled = GLib.Variant.parse(None, subprocess.check_output(
        ['gsettings', 'get', 'org.gnome.shell', 'enabled-extensions'], text=True), None, None).unpack()
    if enable == (MIDIA_UUID in enabled):
        return
    # gnome-extensions só funciona se o shell já carregou a extensão; senão vale no próximo login
    if subprocess.run(['gnome-extensions', 'enable' if enable else 'disable', MIDIA_UUID],
                      capture_output=True).returncode != 0:
        enabled = [e for e in enabled if e != MIDIA_UUID] + ([MIDIA_UUID] if enable else [])
        subprocess.run(['gsettings', 'set', 'org.gnome.shell', 'enabled-extensions',
                        GLib.Variant('as', enabled).print_(False)], check=True)
        if enable:
            print('Tocando agora: a extensão aparece depois de sair e entrar de novo na sessão.')


def apply(cfg, mons):
    subprocess.run(['dconf', 'reset', '-f', ROOT], check=True)
    ids = []
    midia = []
    for mon_name, items in cfg['monitores'].items():
        mon = resolve(mon_name, mons)
        if not mon:
            print(f'Aviso: monitor "{mon_name}" não está conectado; pulei os widgets dele.')
            continue
        stacked = {}  # px já ocupados em cada canto
        for item in items:
            kind, pos = item['widget'], item.get('pos', 'top-right')
            if pos not in POSITIONS:
                raise SystemExit(f'Posição desconhecida: {pos}. Use: {", ".join(POSITIONS)}')
            anchor, fx, fy = POSITIONS[pos]
            offset = stacked.get(pos, 0)
            stacked[pos] = offset + HEIGHT[kind] + GAP
            px = MARGIN + (0 if fx == 0.5 else 0)
            x = fx if fx == 0.5 else (px / mon['width'] if fx == 0 else 1 - px / mon['width'])
            if fy == 0.5:
                y = 0.5
            elif fy == 0:
                y = (MARGIN + offset) / mon['height']
            else:
                y = 1 - (MARGIN + offset) / mon['height']
            x, y = item.get('x', x), item.get('y', y)
            if kind == 'midia':
                midia.append({'monitorIndex': mon['index'], 'relativeX': round(x, 4), 'relativeY': round(y, 4),
                              'anchor': anchor})
                continue
            align = 'End' if fx == 1 else 'Start' if fx == 0 else 'Center'
            name, elements, spacing = elements_for(kind, align, item.get('cidade', cfg.get('cidade', 'São Paulo')))
            location = {'monitorIndex': mon['index'], 'relativeX': round(x, 4), 'relativeY': round(y, 4)}
            ids.append(write_widget(f'{name} ({mon["connector"]})', anchor, location, elements, spacing))
    write(ROOT, 'widgets', '[' + ', '.join("{%s: <{'enabled': <true>}>}" % q(w) for w in ids) + ']')
    write(ROOT, 'create-initial-widget', 'false')
    write(ROOT, 'update-notifier-enabled', 'false')
    os.makedirs(os.path.dirname(MIDIA_CONFIG), exist_ok=True)
    with open(MIDIA_CONFIG, 'w', encoding='utf-8') as f:
        json.dump({'cards': midia}, f, indent=2)
        f.write('\n')
    install_midia(bool(midia))
    print(f'{len(ids) + len(midia)} widget(s) aplicados.')


def load():
    if os.path.exists(CONFIG):
        with open(CONFIG, encoding='utf-8') as f:
            return json.load(f)
    return json.loads(json.dumps(DEFAULT))


def save(cfg):
    with open(CONFIG, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    ap = argparse.ArgumentParser(description='Widgets da área de trabalho por monitor')
    ap.add_argument('--list', action='store_true', help='mostra monitores e widgets configurados')
    ap.add_argument('--monitor', help='DP-5, HDMI-3..., principal ou secundario')
    ap.add_argument('--add', metavar='WIDGET', help=', '.join(HEIGHT))
    ap.add_argument('--remove', metavar='WIDGET')
    ap.add_argument('--clear', action='store_true', help='tira todos os widgets do monitor')
    ap.add_argument('--pos', default='top-right', help=', '.join(POSITIONS))
    ap.add_argument('--cidade', help='cidade do widget de tempo (com --monitor/--add: só daquele widget)')
    args = ap.parse_args()

    mons = monitors()
    first_run = not os.path.exists(CONFIG)
    cfg = load()
    if first_run:  # grava o padrão com os nomes reais dos monitores
        cfg['monitores'] = {(resolve(k, mons) or {'connector': k})['connector']: v for k, v in cfg['monitores'].items()}

    if args.list:
        print('Monitores:')
        for m in mons:
            tag = ' (principal)' if m['primary'] else ''
            print(f"  {m['connector']:8} {m['label']} {m['width']}x{m['height']}{tag}")
        print(f"\nCidade do tempo: {cfg.get('cidade')}\nWidgets ({CONFIG}):")
        for mon_name, items in cfg['monitores'].items():
            mon = resolve(mon_name, mons)
            where = f" -> {mon['connector']}" if mon and mon['connector'] != mon_name else '' if mon else ' (desconectado)'
            print(f'  {mon_name}{where}: ' + (', '.join(f"{i['widget']} @ {i.get('pos', 'top-right')}" for i in items) or 'nenhum'))
        return

    if args.add or args.remove or args.clear:
        if not args.monitor:
            raise SystemExit('Use --monitor junto com --add/--remove/--clear')
        mon = resolve(args.monitor, mons)
        # Guarda pelo nome do conector, mas aceita a entrada antiga "principal"/"secundario"
        key = next((k for k in cfg['monitores'] if resolve(k, mons) == mon and mon), None) if mon else None
        key = key or (mon['connector'] if mon else args.monitor)
        items = cfg['monitores'].setdefault(key, [])
        if args.clear:
            items.clear()
        if args.remove:
            items[:] = [i for i in items if i['widget'] != args.remove]
        if args.add:
            if args.add not in HEIGHT:
                raise SystemExit(f'Widget desconhecido: {args.add}. Use: {", ".join(HEIGHT)}')
            if args.pos not in POSITIONS:
                raise SystemExit(f'Posição desconhecida: {args.pos}. Use: {", ".join(POSITIONS)}')
            item = {'widget': args.add, 'pos': args.pos}
            if args.cidade:
                item['cidade'] = args.cidade
            items.append(item)
    elif args.cidade:
        cfg['cidade'] = args.cidade

    save(cfg)
    apply(cfg, mons)


if __name__ == '__main__':
    sys.exit(main())
