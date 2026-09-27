"""Acordeao: o grupo de campos que abre e fecha.

Fechado, o cabecalho e branco com borda preta. Aberto, o cabecalho fica
vermelho, o conteudo passa a amarelo pastel, e uma barra preta de 4px
separa os dois. O indicador alterna entre + e -.

A altura abre em passos de 12ms, porque a sensacao pedida e de mecanismo e
nao de transicao suave. Se o usuario clicar no meio do caminho, o clique
manda: a animacao pendente e cancelada, senao as duas lutariam pela mesma
altura.

Detalhe do Tk que moldou o codigo: para animar a altura, o corpo tem que
ter altura fixa e pack_propagate desligado, senao o pai recalcula o
tamanho a cada passo e a animacao nao sai do lugar. E para o conteudo
nao vazar durante a abertura, ele e cortado pela moldura.
"""

import tkinter as tk

from ..design import tokens, tipografia
from .painel import Divisor

_PASSO_MS = 12
_SALTO_PX = 12

# O cabecalho tem altura fixa porque ele e placeado dentro da moldura, e o
# place nao contribui para o tamanho pedido do pai. Sem esta constante o
# acordeao inteiro nasceria com 1px de altura.
_ALTURA_CABECALHO = 36


class Acordeao(tk.Frame):
    """Um grupo de campos, com cabecalho que abre e fecha o conteudo."""

    def __init__(self, pai, identificador, titulo, ao_mudar=None):
        super().__init__(pai, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0)
        self.identificador = identificador
        self.titulo = titulo
        self.ao_mudar = ao_mudar

        self.aberto = False
        self._altura = 0
        self._alvo = 0
        self._agendado = None

        self.borda = tokens.px(tokens.BORDA_FINA)
        self.sombra_x, self.sombra_y = tokens.sombra()
        self.margem = self.sombra_x
        self.altura_cabecalho = tokens.px(_ALTURA_CABECALHO)

        self._sombra = tk.Frame(self, bg=tokens.PRETO)
        self._sombra.place(relwidth=1, relheight=1, x=self.sombra_x, y=self.sombra_y)

        # A moldura e empacotada, e a borda e a folga preta que sobra em
        # volta dos filhos. Posicionar a moldura em vez de empacotar faria
        # o acordeao valer 1px, porque o place nao devolve nada para o
        # tamanho pedido do pai.
        self._moldura = tk.Frame(self, bg=tokens.PRETO, bd=0, highlightthickness=0)
        self._moldura.pack(fill="both", expand=True)

        self.cabecalho = tk.Frame(
            self._moldura,
            bg=tokens.BRANCO,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            height=self.altura_cabecalho,
        )
        self.cabecalho.pack(
            fill="x", padx=self.borda, pady=(self.borda, 0)
        )
        self.cabecalho.pack_propagate(False)

        self.texto = tk.Label(
            self.cabecalho,
            text=tipografia.maiuscula(titulo),
            font=tipografia.fonte("h3"),
            bg=tokens.BRANCO,
            fg=tokens.PRETO,
            anchor="w",
            takefocus=1,
        )
        self.texto.pack(side="left", padx=tokens.px(tokens.ESPACO_3),
                        pady=tokens.px(tokens.ESPACO_2))

        self.indicador = tk.Canvas(
            self.cabecalho,
            width=tokens.px(24),
            height=tokens.px(24),
            bg=tokens.BRANCO,
            bd=0,
            highlightthickness=0,
        )
        self.indicador.pack(side="right", padx=tokens.px(tokens.ESPACO_3))

        # Corpo: divisor preto em cima, conteudo embaixo. Os dois vivem
        # dentro do mesmo frame para que uma unica altura controle a
        # animacao inteira.
        self.corpo = tk.Frame(
            self._moldura, bg=tokens.AMARELO_PASTEL, bd=0, highlightthickness=0
        )
        Divisor(self.corpo).pack(fill="x", side="top")
        self.conteudo = tk.Frame(
            self.corpo, bg=tokens.AMARELO_PASTEL, bd=0, highlightthickness=0
        )
        self.conteudo.pack(fill="both", expand=True)

        self._pintar()
        self._aplicar()
        for alvo in (self.cabecalho, self.texto, self.indicador):
            alvo.bind("<Button-1>", self._alternar)
        for alvo in (self.texto,):
            alvo.bind("<Return>", self._alternar)
            alvo.bind("<space>", self._alternar)

    # -- estado ----------------------------------------------------------

    def esta_aberto(self):
        return self.aberto

    def abrir(self, animado=True):
        if self.aberto:
            return self
        self.aberto = True
        self._pintar()
        self._animar(animado)
        self._notificar()
        return self

    def fechar(self, animado=True):
        if not self.aberto:
            return self
        self.aberto = False
        self._pintar()
        self._animar(animado)
        self._notificar()
        return self

    def alternar(self):
        if self._agendado is not None:
            # Um clique no meio da animacao manda na animacao.
            self.after_cancel(self._agendado)
            self._agendado = None
        (self.fechar if self.aberto else self.abrir)()
        return self

    def _alternar(self, _evento):
        self.alternar()
        return "break"

    def _notificar(self):
        """Todo estado novo e avisado, inclusive por quem chamou abrir.

        Se a notificacao morasse so no clique, o invariante de um grupo so
        aberto valeria unicamente para o mouse, e abrir um grupo por
        codigo deixaria dois abertos sem ninguem reclamando.
        """
        if self.ao_mudar:
            self.ao_mudar(self)

    # -- pintura ---------------------------------------------------------

    def _pintar(self):
        if self.aberto:
            fundo, tinta = tokens.VERMELHO, tokens.BRANCO
        else:
            fundo, tinta = tokens.BRANCO, tokens.PRETO

        for alvo in (self.cabecalho, self.texto, self.indicador):
            alvo.configure(bg=fundo)
        self.texto.configure(fg=tinta)
        self._desenhar_indicador(fundo, tinta)

    def _desenhar_indicador(self, fundo, tinta):
        self.indicador.delete("tudo")
        centro = tokens.px(12)
        bruto = tokens.px(6)
        espessura = tokens.px(3)
        traco = dict(fill=tinta, width=espessura, capstyle="projecting")

        # Horizontal: sempre. Vertical: so quando esta fechado.
        self.indicador.create_line(centro - bruto, centro, centro + bruto, centro, **traco)
        if not self.aberto:
            self.indicador.create_line(centro, centro - bruto, centro, centro + bruto, **traco)

    # -- altura ----------------------------------------------------------

    def _animar(self, animado):
        if self.aberto:
            self._medir()
            self._alvo = self.corpo.winfo_reqheight()
        else:
            self._alvo = 0

        if not animado:
            self._altura = self._alvo
            self._aplicar()
            return

        passo = _SALTO_PX if self._alvo > self._altura else -_SALTO_PX
        self._passo(passo)

    def _passo(self, passo):
        if self._altura == self._alvo:
            self._agendado = None
            self._aplicar()
            return

        self._altura += passo
        if (passo > 0 and self._altura > self._alvo) or (passo < 0 and self._altura < self._alvo):
            self._altura = self._alvo

        self._aplicar()
        self._agendado = self.after(_PASSO_MS, lambda: self._passo(passo))

    def _medir(self):
        """Descobre a altura do corpo sem deixa-lo aparecer."""
        self.conteudo.update_idletasks()

    def _aplicar(self):
        """Altura do corpo e do acordeao inteiro, sempre em pixels inteiros.

        O acordeao tambem tem altura fixa, porque a moldura e placeada e o
        place nao devolve nada para o tamanho pedido. Sem isso ele valeria
        1px e o cabecalho sumiria.
        """
        if self._altura <= 0:
            self.corpo.pack_forget()
        else:
            if not self.corpo.winfo_ismapped():
                self.corpo.pack(
                    fill="x", padx=self.borda, pady=(0, self.borda)
                )
            self.corpo.pack_propagate(False)
            self.corpo.configure(height=self._altura)

        self.configure(height=self.altura_cabecalho + self._altura)
        self.pack_propagate(False)

    def parar(self):
        """Cancela a animacao, para o componente poder ser destruido."""
        if self._agendado is not None:
            self.after_cancel(self._agendado)
            self._agendado = None

    def destroy(self):
        self.parar()
        super().destroy()

    # -- layout ----------------------------------------------------------

    def pack(self, **kwargs):
        """Soma a margem da sombra ao espacamento pedido."""
        kwargs["pady"] = _com_sombra(kwargs.get("pady", 0), self.margem)
        if "padx" not in kwargs:
            kwargs["padx"] = (0, self.margem)
        return super().pack(**kwargs)

    def grid(self, **kwargs):
        kwargs["pady"] = _com_sombra(kwargs.get("pady", 0), self.margem)
        if "padx" not in kwargs:
            kwargs["padx"] = (0, self.margem)
        return super().grid(**kwargs)


def _com_sombra(pady, margem):
    """A sombra cai para fora do widget, entao a folga inferior cresce."""
    if isinstance(pady, (tuple, list)):
        return (pady[0], pady[1] + margem)
    return (pady, pady + margem)
