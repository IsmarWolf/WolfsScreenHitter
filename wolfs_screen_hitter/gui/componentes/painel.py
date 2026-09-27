"""Card e divisor: as superficies do design system.

Um painel e fundo branco, borda preta de 4px, sombra dura de 8px, e um
marcador geometrico no canto. Sem desfoque, sem gradiente.

A sombra nao e efeito: e um Frame preto posicionado 8px atras e abaixo da
face, do mesmo jeito que no botao.

A borda tambem nao e efeito. No ttk do Windows ela seria ignorada, entao
aqui ela e um Frame preto com o conteudo desenhado por dentro. Duas
decisoes de layout sustenta-lo, e as duas vieram de erro:

O conteudo e empacotado, nunca posicionado. O place nao contribui para o
tamanho pedido do pai, entao um card montado so com place nasce com 1px de
largura e 1px de altura, mesmo tendo o conteudo inteiro dentro.

E o lado de dentro da moldura e espacamento, nao posicao. Tentar encurtar
a face com width=-borda tambem nao funciona: o place nao subtrai do pai,
o resultado e 1x1 de novo. Entao a moldura e preta e o conteudo e
empacotado com 4px de folga nos quatro lados; o que sobra de preto e a
borda, e o que sobrar de preto e a borda mesmo quando o card e redimensionado.
"""

import tkinter as tk

from ..design import formas, tokens, tipografia


class Painel(tk.Frame):
    """Card branco com borda grossa, sombra dura e marcador de canto."""

    def __init__(
        self,
        pai,
        titulo=None,
        marcador=None,
        cor=tokens.BRANCO,
        sombra=True,
        borda=tokens.BORDA_GROSSA,
        **kwargs,
    ):
        self.sombra = sombra
        self.sombra_x, self.sombra_y = (
            tokens.sombra(tokens.SOMBRA_GRANDE) if sombra else (0, 0)
        )
        self.margem = self.sombra_x if sombra else 0
        self.borda = tokens.px(borda) if borda else 0

        super().__init__(pai, bg=tokens.BG_CANVAS, **kwargs)

        if sombra:
            self._sombra = tk.Frame(self, bg=tokens.PRETO)
            self._sombra.place(relwidth=1, relheight=1, x=self.sombra_x, y=self.sombra_y)

        self._moldura = tk.Frame(self, bg=tokens.PRETO, bd=0, highlightthickness=0)
        self._moldura.pack(fill="both", expand=True)

        self.face = tk.Frame(self._moldura, bg=cor, bd=0, highlightthickness=0)
        self.face.pack(
            fill="both",
            expand=True,
            padx=self.borda,
            pady=self.borda,
        )

        self.corpo = tk.Frame(self.face, bg=cor, bd=0, highlightthickness=0)
        self.corpo.pack(
            fill="both",
            expand=True,
            padx=tokens.px(tokens.ESPACO_4),
            pady=tokens.px(tokens.ESPACO_3),
        )

        if titulo:
            tk.Label(
                self.corpo,
                text=tipografia.maiuscula(titulo),
                font=tipografia.fonte("h3"),
                bg=cor,
                fg=tokens.PRETO,
                anchor="w",
            ).pack(fill="x", pady=(0, tokens.px(tokens.ESPACO_2)))

        if marcador:
            canvas = tk.Canvas(
                self.face,
                width=tokens.px(20),
                height=tokens.px(20),
                bg=cor,
                bd=0,
                highlightthickness=0,
            )
            formas.marcador(
                canvas,
                tokens.px(10),
                tokens.px(10),
                marcador,
                tokens.VERMELHO,
                lado=tokens.px(10),
                espessura=tokens.px(tokens.BORDA_FINA),
            )
            canvas.place(
                relx=1.0,
                x=-tokens.px(tokens.ESPACO_3),
                y=tokens.px(tokens.ESPACO_2),
                anchor="ne",
            )

    def pack(self, **kwargs):
        """Soma a margem da sombra, para o pai nao cortar a face."""
        if "padx" not in kwargs:
            kwargs["padx"] = (0, self.margem)
        kwargs["pady"] = _com_sombra(kwargs.get("pady", 0), self.margem)
        return super().pack(**kwargs)

    def grid(self, **kwargs):
        if "padx" not in kwargs:
            kwargs["padx"] = (0, self.margem)
        kwargs["pady"] = _com_sombra(kwargs.get("pady", 0), self.margem)
        return super().grid(**kwargs)


class Divisor(tk.Frame):
    """Barra preta de 4px que separa duas superficies."""

    def __init__(self, pai, horizontal=True, **kwargs):
        if horizontal:
            kwargs.setdefault("height", tokens.px(tokens.BORDA_GROSSA))
        else:
            kwargs.setdefault("width", tokens.px(tokens.BORDA_GROSSA))
        super().__init__(pai, bg=tokens.PRETO, bd=0, highlightthickness=0, **kwargs)


def _com_sombra(pady, margem):
    """A sombra cai para fora do widget, entao a folga inferior cresce."""
    if isinstance(pady, (tuple, list)):
        return (pady[0], pady[1] + margem)
    return (pady, pady + margem)
