#!/usr/bin/env python3
# Global Menu em português (como o macOS pt-BR) + classe para o nome do app em negrito.
# Uso: python3 globalmenu-ptbr.py <pasta-da-extensao> <pasta-de-backup>   (idempotente)
import re, shutil, sys
from pathlib import Path

ext, bak = Path(sys.argv[1]), Path(sys.argv[2])
bak.mkdir(parents=True, exist_ok=True)

MENUS = {
    'Open Windows': 'Janelas Abertas', 'New Window': 'Nova Janela', 'App Details': 'Detalhes do App',
    'Quit ${appName}': 'Encerrar ${appName}', 'About ${desktopAppName}': 'Sobre o ${desktopAppName}',
    'Open ${desktopAppName}': 'Abrir ${desktopAppName}', 'Settings': 'Configurações', 'Empty Bin...': 'Esvaziar Lixo…',
    'File': 'Arquivo', 'New ${desktopAppName} Window': 'Nova Janela do ${desktopAppName}', 'New Folder': 'Nova Pasta',
    'New Tab': 'Nova Aba', 'Open': 'Abrir', 'Open With': 'Abrir Com', 'Print': 'Imprimir', 'Get Info': 'Obter Informações',
    'Compress': 'Comprimir', 'Duplicate': 'Duplicar', 'Move to Trash': 'Mover para o Lixo', 'Close Window': 'Fechar Janela',
    'Edit': 'Editar', 'Undo': 'Desfazer', 'Redo': 'Refazer', 'Cut': 'Recortar', 'Copy': 'Copiar', 'Paste': 'Colar',
    'Delete': 'Apagar', 'Select All': 'Selecionar Tudo', 'Emoji & Symbols': 'Emoji e Símbolos',
    'View': 'Visualizar', 'as Icons': 'como Ícones', 'as List': 'como Lista', 'Enter Full Screen': 'Entrar em Tela Cheia',
    'Go': 'Ir', 'Back': 'Voltar', 'Forward': 'Avançar', 'Recents': 'Recentes', 'Documents': 'Documentos',
    'Desktop': 'Mesa', 'Home': 'Pasta Pessoal', 'Window': 'Janela', 'Minimize': 'Minimizar', 'Maximize': 'Zoom',
    'Close': 'Fechar', 'Help': 'Ajuda', 'GNOME Help': 'Ajuda do GNOME', 'No items configured': 'Nenhum item',
}
LOGO = {
    'About This System': 'Sobre Este Computador', 'Activities': 'Atividades', 'App Grid': 'Aplicativos',
    'Software Center': 'Central de Apps…', 'System Monitor': 'Monitor do Sistema', 'Terminal': 'Terminal',
    'Extensions': 'Extensões', 'Force Quit App': 'Forçar Encerrar…', 'Sleep': 'Repouso', 'Restart...': 'Reiniciar…',
    'Shut Down...': 'Desligar…', 'Lock Screen': 'Bloquear Tela', 'Log Out...': 'Encerrar Sessão…',
}

def patch(name, fn):
    p = ext / name
    orig = bak / name
    if not orig.exists():
        shutil.copy2(p, orig)
    src = orig.read_text()          # sempre parte do original: idempotente
    p.write_text(fn(src))

def menus(s):
    s = re.sub(r'label: (["`])(.*?)\1', lambda m: f'label: {m[1]}{MENUS.get(m[2], m[2])}{m[1]}', s)
    hook = "            Main.panel.addToStatusArea(`${this.uuid}-${index}`, btn, index + 1, 'left');\n"
    assert hook in s, 'globalmenu mudou; patch do nome do app não aplicado'
    # Se o GNOME ligar a extensão duas vezes seguidas (corrida ao trocar extensões), sobra um botão órfão
    # com o mesmo papel e todo foco de janela dava "Extension point conflict": remove o órfão antes
    stale = "            Main.panel.statusArea[`${this.uuid}-${index}`]?.destroy();\n"
    return s.replace(hook, stale + hook + "            btn.add_style_class_name(index === 0 && this._settings.get_boolean('menu-app-enabled')"
                                  " ? 'globalmenu-app-name' : 'globalmenu-menu-name');\n")

def guard(s):
    hook = "        console.log(`[globalmenu@ShiroOSL.github.io] Enabling extension.`);\n"
    assert hook in s, 'globalmenu mudou; proteção contra enable duplo não aplicada'
    return s.replace(hook, hook + "        if (this._settings)  // enable() de novo sem disable(): limpa o anterior\n            this.disable();\n")

def logo(s):
    return re.sub(r"_addItem\('(.*?)'", lambda m: f"_addItem('{LOGO.get(m[1], m[1])}'", s)

patch('menuManager.js', menus)
patch('systemMenu.js', logo)
patch('extension.js', guard)
print('globalmenu: pt-BR + nome do app em negrito aplicados (vale após sair e entrar na sessão)')
