"""Lista de perfis desenhada no Canvas.

O Listbox nativo seria mais simples, mas ele entrega a aparencia do
sistema, e a identidade da tela nao pode depender disso. Entao a lista e
desenhada: cada perfil e um retangulo com um marcador geometrico, e o
selecionado ganha fundo amarelo e uma barra preta a esquerda.

Trocando o widget trocou tambem o teclado, que agora e da nossa conta.
Setas, Home, End, PageUp e PageDown movem a selecao, Enter abre, e a lista
participa do Tab. Sem isso a lista seria um beco sem saida para quem nao
usa o mouse.
"""

import tkinter as tk

from ..design import formas, tokens, tipografia

_ALTURA_LINHA = 44
_PADDING = 12
_MARCADORES = ("circulo", "quadrado", "triangulo", "losango")
_CORES = (tokens.VERMELHO, tokens.AZUL, tokens.AMARELO, tokens.VERMELHO)


class ListaPerfis(tk.Canvas):
    """Lista de seleção única, desenhada e navegável por teclado."""

    def __init__(self, pai, ao_selecionar=None, fundo=tokens.AZUL, tinta=tokens.BRANCO,
                 altura=220):
        super().__init__(
            pai,
            bg=fundo,
            bd=0,
            highlightthickness=0,
            takefocus=1,
            width=tokens.px(240),
            height=tokens.px(altura),
        )
        self.fundo = fundo
        self.tinta = tinta
        self.itens = []
        self.selecionado = -1
        self.ao_selecionar = ao_selecionar
        self._hover = -1

        self.bind("<Configure>", lambda _e: self._redesenhar())
        self.bind("<Button-1>", self._clique)
        self.bind("<Motion>", self._mover)
        self.bind("<Leave>", lambda _e: self._setar_hover(-1))
        self.bind("<Up>", lambda _e: self._mover_selecao(-1))
        self.bind("<Down>", lambda _e: self._mover_selecao(1))
        self.bind("<Home>", lambda _e: self._selecionar(0))
        self.bind("<End>", lambda _e: self._selecionar(len(self.itens) - 1))
        self.bind("<Prior>", lambda _e: self._mover_selecao(-3))
        self.bind("<Next>", lambda _e: self._mover_selecao(3))
        self.bind("<Return>", self._confirmar)
        self.bind("<space>", self._confirmar)
        self.bind("<FocusIn>", lambda _e: self._redesenhar())
        self.bind("<FocusOut>", lambda _e: self._redesenhar())

    # -- dados -----------------------------------------------------------

    def definir_itens(self, caminhos, selecionado=None):
        self.itens = list(caminhos)
        if selecionado is None:
            self.selecionado = -1
        elif selecionado in self.itens:
            self.selecionado = self.itens.index(selecionado)
        else:
            self.selecionado = -1
        self._redesenhar()

    def caminho_selecionado(self):
        if 0 <= self.selecionado < len(self.itens):
            return self.itens[self.selecionado]
        return None

    def definir_selecionado(self, caminho):
        """Move so o destaque, sem tocar na lista de itens.

        Separate de definir_itens porque quem salva ou apaga um perfil
        precisa dos dois: a lista muda e o destaque tambem, mas o caminho
        novo ja vem junto nos dois. Chamar definir_itens de novo com a
        lista inteira daria o mesmo resultado e redesenharia duas vezes.
        """
        if caminho is None or caminho not in self.itens:
            self.selecionado = -1
        else:
            self.selecionado = self.itens.index(caminho)
        self._redesenhar()
        if self.selecionado >= 0:
            self._revelar(self.selecionado)

    def _indice_em(self, y):
        if not self.itens:
            return -1
        return min(len(self.itens) - 1, max(0, int(y // self._altura_linha())))

    def _altura_linha(self):
        return tokens.px(_ALTURA_LINHA)

    # -- eventos ---------------------------------------------------------

    def _selecionar(self, indice):
        """Mova a selecao. So redesenha quando o indice muda de fato,
        senao um arrastinho do mouse viraria um redesenho por pixel."""
        if not self.itens or indice == self.selecionado:
            return
        self.selecionado = indice
        self._redesenhar()
        self._revelar(indice)

    def _revelar(self, indice):
        """Rola o minimo necessario para a linha escolhida aparecer.

        O Canvas nao tem see(), que e de Text e Listbox. A rolagem aqui e
        feita pela fracao, que e o que o yview devolve.
        """
        total = len(self.itens)
        if total <= 1:
            self.yview_moveto(0)
            return
        visiveis = max(1, self.winfo_height() // self._altura_linha())
        primeiro = int(self.yview()[0] * total)
        if indice < primeiro:
            self.yview_moveto(indice / total)
        elif indice >= primeiro + visiveis:
            self.yview_moveto((indice - visiveis + 1) / total)

    def _clique(self, evento):
        indice = self._indice_em(evento.y)
        if indice < 0 or indice >= len(self.itens):
            return "break"
        mudou = indice != self.selecionado
        self._selecionar(indice)
        if mudou:
            self._confirmar(None)
        return "break"

    def _mover(self, evento):
        self._setar_hover(self._indice_em(evento.y))

    def _mover_selecao(self, delta):
        if not self.itens:
            return "break"
        base = self.selecionado if self.selecionado >= 0 else -1
        self._selecionar(max(0, min(len(self.itens) - 1, base + delta)))
        return "break"

    def _confirmar(self, _evento):
        caminho = self.caminho_selecionado()
        if caminho is not None and self.ao_selecionar:
            self.ao_selecionar(caminho)
        return "break"

    def _setar_hover(self, indice):
        if indice != self._hover:
            self._hover = indice
            self._redesenhar()

    # -- pintura ---------------------------------------------------------

    def _redesenhar(self):
        self.delete("tudo")
        largura = self.winfo_width()
        if largura <= 1:
            return
        altura_linha = self._altura_linha()
        padding = tokens.px(_PADDING)
        tem_foco = self.focus_get() is self

        for indice, caminho in enumerate(self.itens):
            topo = indice * altura_linha
            marcado = indice == self.selecionado
            pairado = indice == self._hover and not marcado

            fundo = tokens.AMARELO if marcado else (tokens.CINZA if pairado else self.fundo)
            tinta = tokens.PRETO if (marcado or pairado) else self.tinta

            self.create_rectangle(
                0, topo, largura, topo + altura_linha, fill=fundo, outline=fundo
            )
            if marcado:
                # Barra preta a esquerda: o unico marcador de selecao que
                # nao depende de cor.
                self.create_rectangle(
                    0,
                    topo,
                    tokens.px(tokens.BORDA_GROSSA),
                    topo + altura_linha,
                    fill=tokens.PRETO,
                    outline=tokens.PRETO,
                )
            elif tem_foco and indice == self.selecionado:
                self.create_rectangle(
                    tokens.px(1), topo + 1, largura - 1, topo + altura_linha - 1,
                    outline=tokens.PRETO, width=tokens.px(tokens.BORDA_FINA),
                )

            formas.marcador(
                self,
                padding + tokens.px(7),
                topo + altura_linha / 2,
                _MARCADORES[indice % len(_MARCADORES)],
                _CORES[indice % len(_CORES)],
                lado=tokens.px(12),
                espessura=tokens.px(tokens.BORDA_FINA),
            )

            self.create_text(
                padding + tokens.px(22),
                topo + altura_linha / 2,
                text=caminho.name,
                anchor="w",
                fill=tinta,
                font=tipografia.fonte("label"),
            )

        if not self.itens:
            self.create_text(
                largura / 2,
                altura_linha,
                text="SEM PERFIS AQUI",
                fill=self.tinta,
                font=tipografia.fonte("label"),
            )
