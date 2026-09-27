"""Tokens do design system.

Tudo que a tela mede, pinta ou espaca sai deste modulo. Nenhum outro
arquivo escreve uma cor ou uma espessura na mao, senao o sistema visual
se perde no primeiro componente novo.

Duas medidas convivem aqui, e a distincao importa. Fonte e em ponto, e o
Tk ja aplica o DPI nela. Borda, sombra e espacamento sao em pixel, e o Tk
nao aplica nada: num monitor 4K uma borda de 2px vira um fio de cabelo
enquanto o texto dobra de tamanho. Por isso os tokens ficam em pixel de
projeto e passam por px(), que multiplica pela escala real da tela.
"""

from tkinter import TclError

# --- cores -----------------------------------------------------------------

BG_CANVAS = "#F0F0F0"
PRETO = "#121212"
VERMELHO = "#D02020"
AZUL = "#1040C0"
AMARELO = "#F0C020"
BRANCO = "#FFFFFF"
CINZA = "#E0E0E0"
AMARELO_PASTEL = "#FFF9C4"

# --- bordas e sombras -------------------------------------------------------

BORDA_FINA = 2
BORDA_GROSSA = 4
SOMBRA_PEQUENA = (3, 3)
SOMBRA_GRANDE = (8, 8)

# --- espacamento: multiplos estritos de 4 ----------------------------------

ESPACO_1 = 4
ESPACO_2 = 8
ESPACO_3 = 12
ESPACO_4 = 16
ESPACO_6 = 24
ESPACO_8 = 32

# --- escala de fonte, em ponto ---------------------------------------------

TAMANHO_DISPLAY = 32
TAMANHO_H2 = 20
TAMANHO_H3 = 14
TAMANHO_CORPO = 11
TAMANHO_LABEL = 9


# O Tk scaling e pixel por ponto. 1.3333 corresponde a 100% no Windows
# (96 dpi / 72). Qualquer valor diferente e a tela estar mais densa.
_LINHA_DE_BASE = 96 / 72

_escala = 1.0


def configurar_escala(raiz):
    """Le o DPI da tela e guarda o fator para px(). Chame apos criar a raiz."""
    global _escala
    try:
        _escala = float(raiz.tk.call("tk", "scaling")) / _LINHA_DE_BASE
    except (TclError, TypeError, ValueError):
        _escala = 1.0
    return _escala


def escala():
    return _escala


def px(valor):
    """Converte um token de pixel de projeto para pixel da tela real."""
    return max(1, int(round(valor * _escala)))


def sombra(offset=SOMBRA_PEQUENA):
    dx, dy = offset
    return px(dx), px(dy)
