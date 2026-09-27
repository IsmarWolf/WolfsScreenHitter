"""Linha de acao: um botao que age sobre os campos do grupo.

Fica separada da LinhaCampo porque um botao nao tem valor. Ele nao grava
nada sozinho: o seletor de regiao, por exemplo, so escreve nos quatro
campos que o grupo da regiao ja tem. Se o botao fosse um Campo, ele
entraria na validacao e acabaria gravado dentro do JSON do perfil.
"""

import tkinter as tk

from ..design import tokens, tipografia
from .botao import Botao
from .campo import rotulo_de_coluna


class LinhaAcao(tk.Frame):
    """Botao e explicacao do que ele faz, alinhados com os campos do grupo."""

    def __init__(self, pai, acao, comando, fundo=tokens.AMARELO_PASTEL):
        super().__init__(pai, bg=fundo, bd=0, highlightthickness=0)
        self.acao = acao
        self.comando = comando

        # A coluna vazia e um Rotulo, e nao um Frame de largura calculada. Um
        # Frame com altura fixa vira uma barra de um pixel atravessando a
        # linha, que e lida como defeito e nao como espacamento. E o rotulo
        # vem do mesmo lugar do rotulo de campo, entao o botao comeca
        # exatamente onde comecam as entradas.
        rotulo_de_coluna(self, "", fundo).pack(
            side="left", padx=(0, tokens.px(tokens.ESPACO_2)),
            pady=tokens.px(tokens.ESPACO_1),
        )

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
