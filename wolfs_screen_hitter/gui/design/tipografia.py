"""Tipografia do design system.

A familia e Outfit, uma geometrica sem serifa, que e o que segura o
carater construtivista do resto da tela. Ela vem junto no pacote e e
registrada so para este processo, por isso o usuario nao precisa instalar
nada e o Windows nao e alterado.

O detalhe que faz isso funcionar: o Tk 8.6 nao tem comando para carregar
fonte em tempo de execucao, ele so enxerga o que o Windows informa. O
caminho e chamar AddFontResourceExW antes de existir a janela, e o Tk
passa a listar a familia. Se qualquer parte disso falhar, a pilha de
fallback assume e a tela continua igual, so com outra fonte.
"""

import sys
from pathlib import Path
from tkinter import font

from . import tokens

DIR_FONTES = Path(__file__).resolve().parent / "fontes"
ARQUIVO_OUTFIT = DIR_FONTES / "Outfit.ttf"

# Candidatas em ordem de preferencia. Outfit primeiro porque e a escolha do
# design system; as outras garantem que a tela tenha cara em uma maquina
# que por algum motivo nao aceitou a fonte embutida.
FAMILIAS = ("Outfit", "Outfit Medium", "Segoe UI", "Helvetica", "Arial")

# A fonte do Outfit e variavel, e o Tk expoe cada instancia nomeada como
# uma familia separada. Da para pedir o Black e o SemiBold de verdade, em
# vez de synthesized bold, que no Tk e so o mesmo desenho engordurado.
INSTANCIAS = {
    "display": ("Outfit Black", "Outfit", "Segoe UI", "Arial"),
    "h2": ("Outfit", "Outfit SemiBold", "Segoe UI", "Arial"),
    "h3": ("Outfit SemiBold", "Outfit", "Segoe UI", "Arial"),
    "corpo": ("Outfit", "Outfit Light", "Segoe UI", "Arial"),
    "label": ("Outfit Medium", "Outfit", "Segoe UI", "Arial"),
}

_TAMANHOS = {
    "display": tokens.TAMANHO_DISPLAY,
    "h2": tokens.TAMANHO_H2,
    "h3": tokens.TAMANHO_H3,
    "corpo": tokens.TAMANHO_CORPO,
    "label": tokens.TAMANHO_LABEL,
}

_PESOS = {
    "display": "bold",
    "h2": "bold",
    "h3": "bold",
    "corpo": "normal",
    "label": "bold",
}

_disponiveis = set()
_fontes = {}


def registrar_fonte_embutida():
    """Registra o Outfit no processo. Chame antes de criar a janela.

    Devolve True se a fonte ficou disponivel. Nunca levanta: uma fonte que
    nao carregou e um problema de aparencia, e nao um motivo para a
    interface nao abrir.
    """
    if not ARQUIVO_OUTFIT.exists():
        return False

    if sys.platform != "win32":
        # Fora do Windows o caminho seria outro (fontconfig, CoreText) e nao
        # vale a pena inventar agora. A pilha de fallback cobre.
        return False

    try:
        import ctypes

        # FR_PRIVATE = 0x10: a fonte vale so neste processo e some quando
        # ele fecha. Nada e instalado, nada e registrado no Windows.
        adicionar = ctypes.windll.gdi32.AddFontResourceExW
        adicionar.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
        return bool(adicionar(str(ARQUIVO_OUTFIT), 0x10, None))
    except (AttributeError, OSError, ImportError):
        return False


def carregar(raiz):
    """Le as familias que o Tk enxerga e monta as fontes do sistema."""
    _disponiveis.clear()
    _fontes.clear()
    _disponiveis.update(font.families(raiz))

    for papel in _TAMANHOS:
        _fontes[papel] = font.Font(
            root=raiz,
            family=familia(papel),
            size=_TAMANHOS[papel],
            weight=_PESOS[papel],
        )

    return _fontes


def disponiveis():
    return sorted(_disponiveis)


def usando_outfit():
    return familia("corpo").startswith("Outfit")


def familia(papel="corpo"):
    """A primeira familia deste papel que o Tk realmente tem."""
    for candidata in INSTANCIAS.get(papel, FAMILIAS):
        if candidata in _disponiveis:
            return candidata

    # Nenhuma da lista existe. A ultima resortada e a fonte do proprio Tk,
    # que sempre existe.
    return font.nametofont("TkDefaultFont").actual("family")


def fonte(papel="corpo"):
    """O objeto de fonte de um papel. Antes de carregar(), cai no padrao."""
    return _fontes.get(papel) or font.nametofont("TkDefaultFont")


def maiuscula(texto):
    """Rotulo, botao e tag sempre em caixa-alta, como manda o sistema."""
    return str(texto).upper()
