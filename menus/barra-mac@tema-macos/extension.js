// Barra Mac: relógio "Sáb 25 de out. 10:30" e ícone da Central de Controle (tema-macos).
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';
import Clutter from 'gi://Clutter';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

export default class BarraMac extends Extension {
    enable() {
        const dateMenu = Main.panel.statusArea.dateMenu;
        this._orig = dateMenu._clockDisplay;
        this._clock = new St.Label({style_class: 'clock', y_align: Clutter.ActorAlign.CENTER});
        this._orig.get_parent().insert_child_above(this._clock, this._orig);
        this._orig.hide();
        this._orig.connectObject('notify::text', () => this._update(), this);
        this._update();

        const qs = Main.panel.statusArea.quickSettings;
        this._cc = new St.Icon({
            gicon: Gio.icon_new_for_string(`${this.path}/control-center-symbolic.svg`),
            style_class: 'system-status-icon barra-mac-control-center',
        });
        qs._indicators.add_child(this._cc);
    }

    _update() {
        const s = GLib.DateTime.new_now_local().format('%a %-d de %b. %H:%M');
        this._clock.text = s.charAt(0).toUpperCase() + s.slice(1);
    }

    disable() {
        this._orig?.disconnectObject(this);
        this._orig?.show();
        this._clock?.destroy();
        this._cc?.destroy();
        this._orig = this._clock = this._cc = null;
    }
}
