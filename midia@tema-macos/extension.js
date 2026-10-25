// Tocando agora: widget de mídia na área de trabalho, no estilo dos widgets do macOS (tema-macos).
// Controla qualquer player MPRIS (Spotify, Firefox/YouTube, Rhythmbox...).
// As posições vêm de ~/.config/tema-macos/midia.json, gravado pelo ~/tema-macos/widgets.py.
import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Soup from 'gi://Soup';
import St from 'gi://St';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const CONFIG = GLib.build_filenamev([GLib.get_user_config_dir(), 'tema-macos', 'midia.json']);
const CACHE = GLib.build_filenamev([GLib.get_user_cache_dir(), 'tema-macos-midia']);
const MPRIS = 'org.mpris.MediaPlayer2.';
const PLAYER_IFACE = 'org.mpris.MediaPlayer2.Player';
const PATH = '/org/mpris/MediaPlayer2';

Gio._promisify(Soup.Session.prototype, 'send_and_read_async');

function unpack(v) {
    return v?.recursiveUnpack ? v.recursiveUnpack() : v;
}

function fmt(us) {
    const s = Math.max(0, Math.floor(us / 1e6));
    const h = Math.floor(s / 3600), m = Math.floor(s / 60) % 60, sec = String(s % 60).padStart(2, '0');
    return h ? `${h}:${String(m).padStart(2, '0')}:${sec}` : `${m}:${sec}`;
}

// Um player MPRIS (um nome org.mpris.MediaPlayer2.* no barramento)
class Player {
    constructor(busName, onChange) {
        this.busName = busName;
        this.identity = busName.slice(MPRIS.length).split('.')[0];
        this.identity = this.identity.charAt(0).toUpperCase() + this.identity.slice(1);
        this.position = 0;
        this.lastPlaying = 0;
        this._onChange = onChange;
        this._cancellable = new Gio.Cancellable();
        Gio.DBusProxy.new_for_bus(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, null,
            busName, PATH, PLAYER_IFACE, this._cancellable, (_o, res) => {
                try {
                    this._proxy = Gio.DBusProxy.new_for_bus_finish(res);
                } catch {
                    return;
                }
                this._proxy.connectObject('g-properties-changed', (_p, changed) => {
                    if ('Position' in changed.deepUnpack())
                        this.position = this._get('Position') ?? 0;
                    this._touch();
                    this._onChange();
                }, 'g-signal', (_p, _sender, signal, params) => {
                    if (signal === 'Seeked') {
                        this.position = params.deepUnpack()[0];
                        this._onChange();
                    }
                }, this);
                this._touch();
                this.refreshPosition();
            });
        Gio.DBus.session.call(busName, PATH, 'org.freedesktop.DBus.Properties', 'Get',
            new GLib.Variant('(ss)', ['org.mpris.MediaPlayer2', 'Identity']), null,
            Gio.DBusCallFlags.NONE, -1, this._cancellable, (conn, res) => {
                try {
                    this.identity = unpack(conn.call_finish(res).deepUnpack()[0]) || this.identity;
                    this._onChange();
                } catch {}
            });
    }

    _get(name) {
        return unpack(this._proxy?.get_cached_property(name));
    }

    _touch() {
        if (this.playing)
            this.lastPlaying = GLib.get_monotonic_time();
    }

    get ready() {
        return !!this._proxy;
    }

    get playing() {
        return this._get('PlaybackStatus') === 'Playing';
    }

    get meta() {
        return this._get('Metadata') ?? {};
    }

    get length() {
        return Number(this.meta['mpris:length'] ?? 0);
    }

    can(what) {
        return this._get(what) !== false;
    }

    // Position não avisa quando muda: lê de novo a cada segundo enquanto toca
    refreshPosition() {
        this._proxy?.call('org.freedesktop.DBus.Properties.Get',
            new GLib.Variant('(ss)', [PLAYER_IFACE, 'Position']), Gio.DBusCallFlags.NONE, 1000,
            this._cancellable, (p, res) => {
                try {
                    this.position = Number(unpack(p.call_finish(res).deepUnpack()[0]));
                    this._onChange();
                } catch {}
            });
    }

    call(method, params = null) {
        this._proxy?.call(method, params, Gio.DBusCallFlags.NONE, -1, null, null);
    }

    seek(fraction) {
        const id = this.meta['mpris:trackid'];
        if (id && this.length)
            this.call('SetPosition', new GLib.Variant('(ox)', [id, Math.round(fraction * this.length)]));
    }

    destroy() {
        this._cancellable.cancel();
        this._proxy?.disconnectObject(this);
        this._proxy = null;
    }
}

// Card na área de trabalho, no mesmo vidro escuro dos widgets do Desktop Widgets
class Card {
    constructor(place, controller) {
        this._place = place;
        this._controller = controller;
        this.actor = new St.BoxLayout({
            style_class: 'midia-card', orientation: Clutter.Orientation.VERTICAL, reactive: true, visible: false,
        });

        const top = new St.BoxLayout({style_class: 'midia-top'});
        this._art = new St.Bin({style_class: 'midia-art', y_align: Clutter.ActorAlign.CENTER});
        this._artIcon = new St.Icon({icon_name: 'audio-x-generic-symbolic', style_class: 'midia-art-icon'});
        this._art.set_child(this._artIcon);
        const info = new St.BoxLayout({
            orientation: Clutter.Orientation.VERTICAL, x_expand: true, y_align: Clutter.ActorAlign.CENTER,
            style_class: 'midia-info',
        });
        this._app = new St.Label({style_class: 'midia-app'});
        this._title = new St.Label({style_class: 'midia-title'});
        this._artist = new St.Label({style_class: 'midia-artist'});
        for (const l of [this._app, this._title, this._artist]) {
            l.clutter_text.ellipsize = 3; // Pango.EllipsizeMode.END
            info.add_child(l);
        }
        top.add_child(this._art);
        top.add_child(info);
        this.actor.add_child(top);

        this._progress = new St.BoxLayout({style_class: 'midia-progress'});
        this._elapsed = new St.Label({style_class: 'midia-time', y_align: Clutter.ActorAlign.CENTER});
        this._remaining = new St.Label({style_class: 'midia-time', y_align: Clutter.ActorAlign.CENTER});
        this._track = new St.Widget({
            style_class: 'midia-track', x_expand: true, y_align: Clutter.ActorAlign.CENTER, reactive: true,
        });
        this._fill = new St.Widget({style_class: 'midia-fill'});
        this._track.add_child(this._fill);
        this._track.connect('button-release-event', (actor, event) => {
            const [x] = event.get_coords();
            const [, tx] = actor.transform_stage_point(x, 0);
            this._controller.current?.seek(Math.min(1, Math.max(0, tx / actor.width)));
            return Clutter.EVENT_STOP;
        });
        this._track.connect('notify::width', () => this._drawFill());
        this._progress.add_child(this._elapsed);
        this._progress.add_child(this._track);
        this._progress.add_child(this._remaining);
        this.actor.add_child(this._progress);

        const controls = new St.BoxLayout({style_class: 'midia-controls', x_align: Clutter.ActorAlign.CENTER});
        this._prev = this._button('media-skip-backward-symbolic', 'Previous');
        this._play = this._button('media-playback-start-symbolic', 'PlayPause');
        this._play.add_style_class_name('midia-play');
        this._next = this._button('media-skip-forward-symbolic', 'Next');
        for (const b of [this._prev, this._play, this._next])
            controls.add_child(b);
        this.actor.add_child(controls);

        Main.layoutManager._backgroundGroup.add_child(this.actor);
        this.actor.connect('notify::size', () => this._position());
        Main.layoutManager.connectObject('monitors-changed', () => this._position(), this);
        this._artUrl = null;
    }

    _button(icon, method) {
        const b = new St.Button({
            style_class: 'midia-button', can_focus: false,
            child: new St.Icon({icon_name: icon, style_class: 'midia-button-icon'}),
        });
        b.connect('clicked', () => this._controller.current?.call(method));
        return b;
    }

    _position() {
        const p = this._place;
        const mon = Main.layoutManager.monitors[p.monitorIndex] ?? Main.layoutManager.primaryMonitor;
        if (!mon)
            return;
        let x = mon.x + p.relativeX * mon.width, y = mon.y + p.relativeY * mon.height;
        const [w, h] = this.actor.get_size();
        const a = p.anchor ?? 'Top_Right';
        if (a.includes('Right'))
            x -= w;
        else if (a.startsWith('Center'))
            x -= w / 2;
        if (a.includes('Bottom'))
            y -= h;
        else if (a === 'Center')
            y -= h / 2;
        this.actor.set_position(Math.round(x), Math.round(y));
    }

    _drawFill() {
        const p = this._controller.current;
        const frac = p && p.length ? Math.min(1, p.position / p.length) : 0;
        this._fill.set_size(Math.round(frac * this._track.width), this._track.height);
    }

    update() {
        const p = this._controller.current;
        if (!p) {
            this.actor.hide();
            return;
        }
        const m = p.meta;
        const artist = [].concat(m['xesam:artist'] ?? []).join(', ') || m['xesam:album'] || '';
        this._app.text = p.identity.toUpperCase();
        this._title.text = m['xesam:title'] || 'Sem título';
        this._artist.text = artist;
        this._artist.visible = !!artist;
        this._play.child.icon_name = p.playing ? 'media-playback-pause-symbolic' : 'media-playback-start-symbolic';
        this._prev.reactive = p.can('CanGoPrevious');
        this._next.reactive = p.can('CanGoNext');
        this._prev.opacity = this._prev.reactive ? 255 : 90;
        this._next.opacity = this._next.reactive ? 255 : 90;
        this._progress.visible = p.length > 0;
        if (p.length) {
            this._elapsed.text = fmt(p.position);
            this._remaining.text = `-${fmt(p.length - p.position)}`;
            this._drawFill();
        }
        this._setArt(this._controller.artFor(p));
        this.actor.show();
        this._position();
    }

    _setArt(path) {
        if (path === this._artUrl)
            return;
        this._artUrl = path;
        if (path) {
            this._art.style = `background-image: url("${path.replace(/"/g, '\\"')}");`;
            this._artIcon.hide();
        } else {
            this._art.style = null;
            this._artIcon.show();
        }
    }

    destroy() {
        Main.layoutManager.disconnectObject(this);
        this.actor.destroy();
    }
}

export default class Midia extends Extension {
    enable() {
        this._players = new Map();
        this._cards = [];
        this._art = new Map(); // URL da capa -> arquivo local
        this._session = new Soup.Session({timeout: 20});
        this.current = null;

        this._watch = Gio.DBus.session.signal_subscribe('org.freedesktop.DBus', 'org.freedesktop.DBus',
            'NameOwnerChanged', '/org/freedesktop/DBus', null, Gio.DBusSignalFlags.NONE,
            (_c, _s, _p, _i, _sig, params) => {
                const [name, oldOwner, newOwner] = params.deepUnpack();
                if (!name.startsWith(MPRIS))
                    return;
                if (oldOwner)
                    this._removePlayer(name);
                if (newOwner)
                    this._addPlayer(name);
            });
        Gio.DBus.session.call('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
            'ListNames', null, null, Gio.DBusCallFlags.NONE, -1, null, (conn, res) => {
                try {
                    for (const name of conn.call_finish(res).deepUnpack()[0]) {
                        if (name.startsWith(MPRIS))
                            this._addPlayer(name);
                    }
                } catch {}
            });

        this._configFile = Gio.File.new_for_path(CONFIG);
        this._monitor = this._configFile.monitor_file(Gio.FileMonitorFlags.NONE, null);
        this._monitor.connect('changed', () => this._loadConfig());
        this._loadConfig();

        this._tick = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 1, () => {
            if (this.current?.playing && this._cards.length)
                this.current.refreshPosition();
            return GLib.SOURCE_CONTINUE;
        });
    }

    disable() {
        if (!this._players)  // o GNOME às vezes chama disable() duas vezes seguidas
            return;
        GLib.source_remove(this._tick);
        Gio.DBus.session.signal_unsubscribe(this._watch);
        this._monitor.cancel();
        this._cards.forEach(c => c.destroy());
        this._players.forEach(p => p.destroy());
        this._session.abort();
        this._cards = this._players = this._art = this._session = this._monitor = this.current = null;
    }

    _loadConfig() {
        let places = [];
        try {
            const [, bytes] = this._configFile.load_contents(null);
            places = JSON.parse(new TextDecoder().decode(bytes)).cards ?? [];
        } catch {}
        this._cards.forEach(c => c.destroy());
        this._cards = places.map(p => new Card(p, this));
        this._changed();
    }

    _addPlayer(name) {
        if (!this._players.has(name))
            this._players.set(name, new Player(name, () => this._changed()));
    }

    _removePlayer(name) {
        this._players.get(name)?.destroy();
        this._players.delete(name);
        this._changed();
    }

    // Mostra o player que está tocando; senão, o último que tocou
    _changed() {
        const list = [...this._players.values()].filter(p => p.ready && (p.meta['xesam:title'] || p.playing));
        this.current = list.find(p => p.playing) ??
            list.sort((a, b) => b.lastPlaying - a.lastPlaying)[0] ?? null;
        this._cards?.forEach(c => c.update());
    }

    // Capa local na hora; capa da internet (Spotify) é baixada para o cache uma vez
    artFor(player) {
        const url = player.meta['mpris:artUrl'];
        if (!url)
            return null;
        // Apps em Flatpak/Snap mandam capas do /tmp delas, que não existe fora do sandbox
        if (url.startsWith('file://'))
            return Gio.File.new_for_uri(url).query_exists(null) ? url : null;
        if (!/^https?:\/\//.test(url))
            return null;
        if (this._art.has(url))
            return this._art.get(url);
        this._art.set(url, null);
        const file = Gio.File.new_for_path(GLib.build_filenamev([CACHE,
            GLib.compute_checksum_for_string(GLib.ChecksumType.SHA1, url, -1)]));
        if (file.query_exists(null)) {
            this._art.set(url, file.get_uri());
            return file.get_uri();
        }
        this._session.send_and_read_async(Soup.Message.new('GET', url), GLib.PRIORITY_DEFAULT, null)
            .then(bytes => {
                GLib.mkdir_with_parents(CACHE, 0o755);
                file.replace_contents(bytes.toArray(), null, false, Gio.FileCreateFlags.NONE, null);
                this._art?.set(url, file.get_uri());
                this._changed();
            }).catch(() => {});
        return null;
    }
}
