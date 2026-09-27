"""Componentes do design system.

Tudo que a tela repete esta aqui: botao, card, acordeao, lista de perfis e
linha de campo. Nenhum deles decide o que e um perfil valido; isso continua
sendo do modelo. Eles so desenham e avisam quando algo muda.
"""

from .acordeao import Acordeao
from .botao import Botao
from .campo import LinhaCampo
from .lista import ListaPerfis
from .painel import Divisor, Painel

__all__ = ["Acordeao", "Botao", "Divisor", "LinhaCampo", "ListaPerfis", "Painel"]
