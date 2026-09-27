"""Linha de acao: um botao que age sobre os campos do grupo.

Fica separada da LinhaCampo porque um botao nao tem valor. Ele nao grava
nada sozinho: o seletor de regiao, por exemplo, so escreve nos quatro
campos que o grupo da regiao ja tem. Se o botao fosse um Campo, ele
entraria na validacao e acabaria gravado dentro do JSON do perfil.
"""

import tkinter as tk
import tkinter.font as tkfont

from ..design import tokens, tipografia
from .botao import Botao
from .campo import COLUNA_ROTULO


def _largura_da_coluna():
    """O rotulo dos campos reserva COLUNA_ROTULO caracteres, e o botao
    precisa do mesmo espaco a esquerda. Converter com a fonte real da tela
    e melhor do que um pixel chutado: trocar a fonte ou a escala muda os
    dois lados junto."""
    fonte = tkfont.Font(font=tipografia.fonte("label"))
    return fonte.measure("0" * COLUNA_ROTULO)


class LinhaAcao(tk.Frame):
    """Botao e explicacao do que ele faz, alinhados com os campos do grupo."""

    def __init__(self, pai, acao, comando, fundo=tokens.AMARELO_PASTEL):
        super().__init__(pai, bg=fundo, bd=0, highlightthickness=0)
        self.acao = acao
        self.comando = comando

        # O mesmo recuo dos rotulos, para o botao comeca na coluna em que
        # comeca o texto dos campos e nao na borda do cartao.
        tk.Frame(self, bg=fundo, width=_largura_da_coluna(), height=1, bd=0,
                 highlightthickness=0).pack(side="left")

        Botao(self, acao.rotulo, comando, variante="primario").pack(
            side="left", padx=(0, tokens.px(tokens.ESPACO_2)),
            pady=tokens.px(tokens.ESPACO_1),
        )

        tk.Label(
            self,
            text=acao.dica,
            font=tipografia.fonte("corpo"),
            bg=fundo,
            fg=tokens.PRETO,
            anchor="w",
            justify="left",
            wraplength=tokens.px(280),
        ).pack(side="left", fill="x", expand=True, padx=(tokens.px(tokens.ESPACO_3), 0))
