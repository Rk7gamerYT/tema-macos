#!/usr/bin/env python3
"""Corrige o YouTube Music Desktop 2.0.12 que fica carregando para sempre.

O YouTube Music trocou a barra do player (ytmusic-player-bar) por um miniplayer novo
e o app não acha mais a API do player. Aplica a mesma ideia do PR upstream
ytmdesktop/ytmdesktop#1837: usa ytmusic-app-layout como ponto de entrada.

Uso: corrigir-carregamento.py <app.asar original> <app.asar corrigido> [script.js extra]
O script extra (ex.: ambilight.js) roda na página quando o YouTube Music termina de carregar.
"""
import hashlib, json, re, struct, sys

QS = 'document.querySelector("ytmusic-app-layout>ytmusic-player-bar")'
REPLACES = [
    # Gancho: ytmPlayerBar passa a ser o ytmusic-app-layout (tem o mesmo playerApi)
    (r'this\.hostElement\.nodeName === "YTMUSIC-PLAYER-BAR"\) \{\s*window\.__YTMD_HOOK__\.ytmPlayerBar = this\s*\}',
     'this.hostElement.nodeName === "YTMUSIC-APP-LAYOUT") { window.__YTMD_HOOK__.ytmPlayerBar = this } '
     'if (this.hostElement && this.hostElement.nodeName === "YTMUSIC-PLAYER-PAGE") { window.__YTMD_HOOK__.ytmPlayerPage = this }', 1),
    # Botões extras na barra antiga: sem a barra antiga, não adiciona (antes travava o carregamento)
    (r'let ytmdControlButtons = \{\};', 'if (!' + QS.replace('\\', '') + ') return; let ytmdControlButtons = {};', 1),
    (re.escape(QS + '.querySelector("ytmusic-like-button-renderer").data'),
     'document.querySelector("ytmusic-app-layout>ytmusic-player-bar ytmusic-like-button-renderer")?.data', None),
    (re.escape(QS + '.currentItem'), 'window.__YTMD_HOOK__.ytmPlayerPage?.currentItem', 1),
    (re.escape(QS + '.getMenuRenderer()'), 'window.__YTMD_HOOK__.ytmPlayerPage?.getMenuRenderer()', 1),
    (re.escape(QS + '.playing'), 'window.__YTMD_HOOK__.ytmStore.getState().player.isPlaying', 2),
    (re.escape(QS + '.queue.shuffle()'), QS + '?.queue.shuffle()', 1),
    (re.escape(QS + '.addEventListener'), QS + '?.addEventListener', 1),
    (re.escape(QS + '.removeEventListener'), QS + '?.removeEventListener', 1),
    (re.escape('document.querySelector("ytmusic-app-layout>ytmusic-player-bar #volume-slider").classList'),
     'document.querySelector("ytmusic-app-layout>ytmusic-player-bar #volume-slider")?.classList', 1),
    # Lista de playlists: dispara a ação no app-layout
    (re.escape(QS) + r'(?=\s*,\s*\{\s*addToPlaylistEndpoint)', 'window.__YTMD_HOOK__.ytmPlayerBar.hostElement', 1),
    (re.escape(QS + '.dispatchEvent'), 'window.__YTMD_HOOK__.ytmPlayerBar.hostElement.dispatchEvent', 1),
]


def patch(text, extra=None):
    reps = list(REPLACES)
    if extra:
        js = json.dumps(extra)
        reps.append((re.escape('e.ipcRenderer.send("ytmView:loaded")});'),
                     'e.webFrame.executeJavaScript(' + js + ').catch(()=>{}),e.ipcRenderer.send("ytmView:loaded")});', 1))
    for pat, rep, want in reps:
        text, n = re.subn(pat, lambda _m: rep, text)
        if want is not None and n != want:
            raise SystemExit(f"padrão encontrado {n}x (esperado {want}): {pat[:70]}")
    return text


def integrity(data, block=4 * 1024 * 1024):
    return {"algorithm": "SHA256", "hash": hashlib.sha256(data).hexdigest(), "blockSize": block,
            "blocks": [hashlib.sha256(data[i:i + block]).hexdigest() for i in range(0, max(len(data), 1), block)]}


def main(src, dst, extra_path=None):
    extra = open(extra_path, encoding="utf-8").read() if extra_path else None
    raw = open(src, 'rb').read()
    pickle_size = struct.unpack_from('<I', raw, 4)[0]
    json_len = struct.unpack_from('<I', raw, 12)[0]
    header = json.loads(raw[16:16 + json_len])
    base = 8 + pickle_size

    files = []  # (node, bytes) na ordem do arquivo original
    def walk(node):
        for name, child in node.get('files', {}).items():
            if 'files' in child:
                walk(child)
            elif 'offset' in child and not child.get('unpacked'):
                files.append(child)
    walk(header)
    files.sort(key=lambda n: int(n['offset']))

    changed = 0
    out, pos = [], 0
    for node in files:
        data = raw[base + int(node['offset']): base + int(node['offset']) + node['size']]
        if b'ytmusic-player-bar' in data or b'YTMUSIC-PLAYER-BAR' in data:
            new = patch(data.decode('utf-8'), extra).encode('utf-8')
            if new != data:
                data, changed = new, changed + 1
                node['size'] = len(data)
                if 'integrity' in node:
                    node['integrity'] = integrity(data)
        node['offset'] = str(pos)
        out.append(data)
        pos += len(data)
    if not changed:
        raise SystemExit("nada para corrigir (versão diferente?)")

    hj = json.dumps(header, separators=(',', ':')).encode()
    pad = (4 - len(hj) % 4) % 4
    payload = struct.pack('<I', len(hj)) + hj + b'\0' * pad
    head = struct.pack('<III', 4, len(payload) + 4, len(payload)) + payload
    with open(dst, 'wb') as f:
        f.write(head)
        for d in out:
            f.write(d)
    print(f"ok: {changed} arquivo(s) corrigido(s)")


if __name__ == '__main__':
    main(*sys.argv[1:4])
