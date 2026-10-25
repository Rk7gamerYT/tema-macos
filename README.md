# tema-macos

Visual estilo macOS escuro para Ubuntu com GNOME (testado no GNOME 50), baseado nos temas
[WhiteSur](https://github.com/vinceliuice) do vinceliuice. Vai além do tema GTK: deixa no mesmo
estilo os apps Qt, os apps rodando como root/sudo, o Flatpak, a tela de login, o boot, o Firefox,
o YouTube Music Desktop e adiciona widgets na área de trabalho.

> Os scripts esperam a pasta em `~/tema-macos`. Rode tudo como seu usuário normal, **sem sudo**:
> quando precisar, o próprio script pede a senha.

```bash
git clone https://github.com/Rk7gamerYT/tema-macos.git ~/tema-macos
cd ~/tema-macos
bash instalar.sh
```

## O que tem aqui

| Arquivo | O que faz | Desfazer |
|---|---|---|
| `instalar.sh` | Instala pacotes (Kvantum, qt5ct/qt6ct, fontes Inter e JetBrains Mono), baixa o WhiteSur, aplica GTK3/GTK4/libadwaita, ícones, cursor, Kvantum, User Themes, Blur my Shell, dock translúcida, e copia o visual para root/sudo e Flatpak | backup feito pelo script em `~/theme-backup-*/` |
| `padronizar.sh` | Acabamento: menus do shell, GTK3, GTK4 e Qt no estilo Mac, barra superior (`menus/barra-mac@tema-macos`), menu global em português, atalhos, notificações, Nautilus e fontes. `--root` aplica também nos apps rodando como root | `padronizar.sh --desfazer` |
| `login.sh` | Tela de login (GDM) com WhiteSur, fundo degradê, Inter, ícones e cursor | `login.sh --desfazer` |
| `boot.sh` | Plymouth preto com o logo do Ubuntu e barra fina, e menu do GRUB escuro com Inter (`--esconder-menu`, `--plymouth`) | `boot.sh --desfazer` |
| `firefox.sh` | Tema WhiteSur no Firefox (snap, deb ou Flatpak) | `firefox.sh --desfazer` |
| `ytmdesktop/aplicar.sh` | Tema escuro estilo Apple Music no YouTube Music Desktop (Flatpak), com brilho ambiente atrás do player (`--sem-ambilight` para desligar) | `aplicar.sh --off` |
| `widgets.py` | Widgets da área de trabalho por monitor (relógio, tempo, sistema, relógio analógico, tocando agora) usando a extensão Desktop Widgets | `dconf reset -f /org/gnome/shell/extensions/azclock/` |
| `app/widgets_app.py` | App GTK4/libadwaita para escolher os widgets de cada monitor com o mouse | |
| `midia@tema-macos/` | Extensão do GNOME Shell com o widget "Tocando agora" (capa, música, progresso e controles para qualquer player MPRIS) | |
| `fundo-por-monitor.py` | Uma imagem de fundo diferente em cada monitor | |
| `icones-toggle.sh` | Liga/desliga os ícones da área de trabalho (atalho Super+Shift+D) | |
| `boot/`, `menus/` | Arquivos usados pelos scripts acima | |

## Widgets

```bash
python3 ~/tema-macos/widgets.py --list
python3 ~/tema-macos/widgets.py --monitor principal --add relogio --pos top-right
python3 ~/tema-macos/widgets.py --monitor secundario --add sistema --pos top-right
python3 ~/tema-macos/widgets.py --cidade "Campinas"
python3 ~/tema-macos/app/widgets_app.py      # versão com janela
```

A configuração fica em `~/tema-macos/widgets.json`, criada na primeira execução com os nomes reais
dos seus monitores. Posições: `top-left`, `top-right`, `bottom-left`, `bottom-right`, `top-center`,
`bottom-center`, `center`.

## Fundo por monitor

```bash
python3 ~/tema-macos/fundo-por-monitor.py --list
python3 ~/tema-macos/fundo-por-monitor.py DP-1=~/Imagens/a.jpg HDMI-1=~/Imagens/b.png
```

Para wallpapers animados do Wallpaper Engine, veja o [wpe-gui](https://github.com/Rk7gamerYT/wpe-gui).

## Ordem sugerida

1. `bash instalar.sh`, depois saia da sessão e entre de novo
2. `bash padronizar.sh`
3. `bash login.sh` e `bash boot.sh` (opcionais, mexem no sistema)
4. `bash firefox.sh`, `bash ytmdesktop/aplicar.sh` e `python3 widgets.py` conforme os apps que você usa

## Observações

- A pasta `src/` (temas WhiteSur) não vai para o repositório: o `instalar.sh` baixa do GitHub.
- `widgets.json` e `fundos.json` são configurações pessoais e também ficam fora.
- A Dash2Dock Lite derrubava o GNOME Shell nos testes: o tema usa a dock do Ubuntu com desfoque do Blur my Shell.

## Créditos

Temas, ícones e cursores [WhiteSur](https://github.com/vinceliuice) por vinceliuice (GPL-3.0).
Widgets sobre a extensão [Desktop Widgets (azclock)](https://gitlab.com/AndrewZaech/azclock).
