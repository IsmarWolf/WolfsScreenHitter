"""Componentes do design system.

Tudo que a tela repete esta aqui: botao, card, acordeao, lista de perfis,
seletor de perfil, dialogo e linha de campo. Nenhum deles decide o que e um
perfil valido; isso continua sendo do modelo. Eles so desenham e avisam
quando algo muda.
"""

from .acordeao import Acordeao
from .botao import Botao
from .campo import LinhaCampo
from .dialogo import pedir_texto
from .linha_acao import LinhaAcao
from .lista import ListaPerfis
from .painel import Divisor, Painel
from .seletor import SeletorPerfil
from .seletor_regiao import escolher_regiao

__all__ = [
    "Acordeao",
    "Botao",
    "Divisor",
    "LinhaAcao",
    "LinhaCampo",
    "ListaPerfis",
    "Painel",
    "SeletorPerfil",
    "escolher_regiao",
    "pedir_texto",
]
