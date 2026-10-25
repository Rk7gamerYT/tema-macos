#!/usr/bin/env python3
"""Widgets: app GTK4/libadwaita para escolher os widgets da área de trabalho de cada monitor.

Toda a lógica (monitores, widgets.json, gravação no Desktop Widgets) vem de ~/tema-macos/widgets.py.
"""
import copy
import math
import os
import sys
import threading

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

sys.path.insert(0, os.path.expanduser('~/tema-macos'))
import widgets as W  # noqa: E402

APP_ID = 'io.github.temamacos.Widgets'
NAMES = {'relogio': 'Relógio', 'relogio-analogico': 'Relógio analógico', 'tempo': 'Tempo', 'sistema': 'Sistema',
         'midia': 'Tocando agora'}
ICONS = {'relogio': 'preferences-system-time-symbolic', 'relogio-analogico': 'alarm-symbolic',
         'tempo': 'weather-few-clouds-symbolic', 'sistema': 'utilities-system-monitor-symbolic',
         'midia': 'audio-x-generic-symbolic'}
POS_LABELS = {'top-left': 'Superior esquerdo', 'top-center': 'Superior centro', 'top-right': 'Superior direito',
              'center': 'Centro', 'bottom-left': 'Inferior esquerdo', 'bottom-center': 'Inferior centro',
              'bottom-right': 'Inferior direito'}
POS_KEYS = list(POS_LABELS)


class MonitorMap(Gtk.DrawingArea):
    """Desenho dos monitores na posição real, com um ponto para cada widget."""

    def __init__(self, window):
        super().__init__(content_height=190, hexpand=True)
        self._win = window
        self._rects = []
        self.set_draw_func(self._draw)
        click = Gtk.GestureClick()
        click.connect('released', self._clicked)
        self.add_controller(click)

    def _draw(self, _area, cr, width, height):
        mons = self._win.mons
        if not mons:
            return
        x0, y0 = min(m['x'] for m in mons), min(m['y'] for m in mons)
        tw = max(m['x'] + m['width'] for m in mons) - x0
        th = max(m['y'] + m['height'] for m in mons) - y0
        scale = min((width - 24) / tw, (height - 24) / th)
        ox, oy = (width - tw * scale) / 2, (height - th * scale) / 2
        fg = self.get_color()
        self._rects = []
        for m in mons:
            x, y = ox + (m['x'] - x0) * scale + 3, oy + (m['y'] - y0) * scale + 3
            w, h = m['width'] * scale - 6, m['height'] * scale - 6
            self._rects.append((m['connector'], x, y, w, h))
            selected = m['connector'] == self._win.selected
            rounded(cr, x, y, w, h, 10)
            if selected:
                cr.set_source_rgba(0.21, 0.52, 0.89, 0.35)
            else:
                cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.08)
            cr.fill_preserve()
            cr.set_line_width(2 if selected else 1)
            if selected:
                cr.set_source_rgba(0.21, 0.52, 0.89, 1)
            else:
                cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.3)
            cr.stroke()
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.9)
            cr.select_font_face('Inter', 0, 1)
            cr.set_font_size(13)
            label = m['connector'] + (' ★' if m['primary'] else '')
            ext = cr.text_extents(label)
            cr.move_to(x + (w - ext.width) / 2, y + h / 2 + 4)
            cr.show_text(label)
            # Um ponto por widget, no canto escolhido
            items = self._win.items_for(m['connector'])
            stacks = {}
            for item in items:
                pos = item.get('pos', 'top-right')
                _a, fx, fy = W.POSITIONS[pos]
                n = stacks.get(pos, 0)
                stacks[pos] = n + 1
                px = x + 12 + fx * (w - 24)
                py = y + 12 + fy * (h - 24) + (n * 12 if fy < 1 else -n * 12)
                cr.arc(px, py, 4.5, 0, 2 * math.pi)
                cr.set_source_rgba(1, 1, 1, 0.95)
                cr.fill()

    def _clicked(self, _gesture, _n, x, y):
        for connector, rx, ry, rw, rh in self._rects:
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self._win.select(connector)
                return


DING = 'ding@rastersoft.com'


def icons_enabled():
    return DING in os.popen('gnome-extensions list --enabled').read().split()


def set_icons(on):
    GLib.spawn_async(['gnome-extensions', 'enable' if on else 'disable', DING],
                     flags=GLib.SpawnFlags.SEARCH_PATH)


def rounded(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


class Window(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='Widgets', default_width=560, default_height=720)
        self.mons = W.monitors()
        self.cfg = W.load()
        self._saved = copy.deepcopy(self.cfg)
        primary = next((m for m in self.mons if m['primary']), self.mons[0])
        self.selected = primary['connector']

        self.toasts = Adw.ToastOverlay()
        view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.apply_button = Gtk.Button(label='Aplicar', css_classes=['suggested-action'])
        self.apply_button.connect('clicked', self._apply)
        header.pack_end(self.apply_button)
        view.add_top_bar(header)

        page = Adw.PreferencesPage()
        desktop = Adw.PreferencesGroup()
        self.icons = Adw.SwitchRow(title='Ícones da área de trabalho',
                                   subtitle='Atalho fora do app: Super+Shift+D', active=icons_enabled())
        self.icons.connect('notify::active', lambda row, _p: set_icons(row.get_active()))
        desktop.add(self.icons)
        page.add(desktop)

        intro = Adw.PreferencesGroup(description='Clique em um monitor para escolher os widgets dele.')
        self.map = MonitorMap(self)
        intro.add(self.map)
        page.add(intro)

        self.group = Adw.PreferencesGroup()
        self.add_button = Gtk.MenuButton(icon_name='list-add-symbolic', tooltip_text='Adicionar widget',
                                         css_classes=['flat'], valign=Gtk.Align.CENTER)
        menu = Gio.Menu()
        for key, name in NAMES.items():
            menu.append(name, f'win.add::{key}')
        self.add_button.set_menu_model(menu)
        self.group.set_header_suffix(self.add_button)
        page.add(self.group)
        self._rows = []

        weather = Adw.PreferencesGroup(title='Tempo', description='Cidade usada pelos widgets de tempo.')
        self.city = Adw.EntryRow(title='Cidade', text=self.cfg.get('cidade', 'São Paulo'))
        self.city.connect('changed', lambda e: self.cfg.__setitem__('cidade', e.get_text().strip()))
        weather.add(self.city)
        page.add(weather)

        view.set_content(page)
        self.toasts.set_child(view)
        self.set_content(self.toasts)

        action = Gio.SimpleAction.new('add', GLib.VariantType.new('s'))
        action.connect('activate', lambda _a, v: self._add(v.get_string()))
        self.add_action(action)
        self._refresh()

    # Entradas do widgets.json podem ser "DP-5" ou "principal"/"secundario"
    def _key_for(self, connector):
        mon = W.resolve(connector, self.mons)
        for key in self.cfg['monitores']:
            if W.resolve(key, self.mons) == mon:
                return key
        return connector

    def items_for(self, connector):
        return self.cfg['monitores'].get(self._key_for(connector), [])

    def select(self, connector):
        self.selected = connector
        self._refresh()

    def _refresh(self):
        mon = W.resolve(self.selected, self.mons)
        orient = 'em pé' if mon['height'] > mon['width'] else 'deitado'
        tag = ' · principal' if mon['primary'] else ''
        self.group.set_title(f"{mon['connector']} — {mon['label']}")
        self.group.set_description(f"{mon['width']}×{mon['height']} · {orient}{tag}")
        for row in self._rows:
            self.group.remove(row)
        self._rows = []
        items = self.items_for(self.selected)
        if not items:
            row = Adw.ActionRow(title='Nenhum widget neste monitor', subtitle='Use o botão + para adicionar.')
            self.group.add(row)
            self._rows.append(row)
        for item in items:
            row = Adw.ComboRow(title=NAMES.get(item['widget'], item['widget']),
                               model=Gtk.StringList.new(list(POS_LABELS.values())))
            row.add_prefix(Gtk.Image(icon_name=ICONS.get(item['widget'], 'image-missing-symbolic')))
            row.set_selected(POS_KEYS.index(item.get('pos', 'top-right')))
            row.connect('notify::selected', self._moved, item)
            remove = Gtk.Button(icon_name='user-trash-symbolic', tooltip_text='Remover',
                                css_classes=['flat'], valign=Gtk.Align.CENTER)
            remove.connect('clicked', self._remove, item)
            row.add_suffix(remove)
            self.group.add(row)
            self._rows.append(row)
        self.map.queue_draw()

    def _add(self, kind):
        key = self._key_for(self.selected)
        self.cfg['monitores'].setdefault(key, []).append({'widget': kind, 'pos': 'top-right'})
        self._refresh()

    def _moved(self, row, _pspec, item):
        item['pos'] = POS_KEYS[row.get_selected()]
        self.map.queue_draw()

    def _remove(self, _button, item):
        self.items_for(self.selected).remove(item)
        self._refresh()

    def _apply(self, _button):
        self.apply_button.set_sensitive(False)
        cfg = copy.deepcopy(self.cfg)

        def work():
            try:
                W.save(cfg)
                W.apply(cfg, self.mons)
                msg = 'Widgets aplicados'
            except (Exception, SystemExit) as error:  # noqa: BLE001 - mostrar qualquer erro ao usuário
                msg = f'Erro: {error}'
            GLib.idle_add(self._applied, msg)

        threading.Thread(target=work, daemon=True).start()

    def _applied(self, msg):
        self.apply_button.set_sensitive(True)
        self.toasts.add_toast(Adw.Toast(title=msg, timeout=3))
        return GLib.SOURCE_REMOVE


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

    def do_activate(self):
        win = self.props.active_window or Window(self)
        win.present()


if __name__ == '__main__':
    sys.exit(App().run(sys.argv))
