"""Botao Bauhaus.

O botao e um Frame com dois filhos: a face, colorida e contornada de preto,
e a sombra, preta, offset. Nao ha imagem de fundo nem estilo de ttk,
porque no tema vista do Windows a cor e a borda sao ignoradas.

A sensacao e mecanica, nao animada: ao pressionar a face anda 2px na
diagonal e a sombra encolhe 2px, como um botao de maquina de impressora.
Solto, volta. Sem transicao e sem curva.

Um detalhe do Tk que moldou o codigo: place() nao contribui para o tamanho
pedido do pai. Se a sombra fosse posicionada so por place, o container
encolheria para 1px e a sombra sairia cortada. Por isso o container recebe
a largura e a altura somadas, medidas na face.
"""

import tkinter as tk

from ..design import tokens, tipografia

_VARIANTES = {
    # nome: (fundo, texto, tem borda)
    "primario": (tokens.VERMELHO, tokens.BRANCO, True),
    "secundario": (tokens.AZUL, tokens.BRANCO, True),
    "amarelo": (tokens.AMARELO, tokens.PRETO, True),
    "contorno": (tokens.BRANCO, tokens.PRETO, True),
    "fantasma": (None, tokens.PRETO, False),
}

# Ao passar o mouse, o que muda em cada variante.
_HOVER = {
    "primario": tokens.VERMELHO,
    "secundario": tokens.AZUL,
    "amarelo": tokens.AMARELO,
    "contorno": tokens.CINZA,
    "fantasma": tokens.CINZA,
}

_PASSO = 2
_ANEL = tokens.AMARELO


def fundo_do_pai(pai):
    """O bg do pai, ou o da janela quando o pai nao tem bg proprio."""
    try:
        if "bg" in pai.keys():
            return pai.cget("bg")
    except Exception:  # noqa: BLE001
        pass
    return tokens.BG_CANVAS


class Botao(tk.Frame):
    """Botao com borda preta, sombra rigida e afundamento ao pressionar."""

    def __init__(self, pai, texto, comando, variante="primario", largura=None, **kwargs):
        fundo, tinta, bordada = _VARIANTES[variante]
        self._texto = texto
        self.variante = variante
        self.tinta = tinta
        self.bordada = bordada
        self.comando = comando
        self._pressionado = False
        self.fonte = kwargs.pop("fonte", None) or tipografia.fonte("h3")

        self.fundo = fundo_do_pai(pai) if variante == "fantasma" else fundo
        self.borda = tokens.px(tokens.BORDA_FINA) if bordada else 0
        self.sombra_x, self.sombra_y = tokens.sombra()
        if variante == "fantasma":
            self.sombra_x = self.sombra_y = 0

        medir = self._criar_face(pai)
        medir.update_idletasks()
        largura_face = medir.winfo_reqwidth() + tokens.px(tokens.ESPACO_2)
        altura_face = medir.winfo_reqheight()
        medir.destroy()

        super().__init__(
            pai,
            bg=self.fundo,
            width=largura or largura_face,
            height=altura_face + self.sombra_y,
            **kwargs,
        )

        if self.sombra_x:
            self._sombra = tk.Frame(self, bg=tokens.PRETO)
        else:
            self._sombra = None

        self.face = self._criar_face(self)
        self.face.place(x=0, y=0)
        self._descansa()
        self._ligar()

    def _criar_face(self, pai):
        return tk.Label(
            pai,
            text=tipografia.maiuscula(self._texto),
            font=self.fonte,
            bg=self.fundo,
            fg=self.tinta,
            padx=tokens.px(tokens.ESPACO_3),
            pady=tokens.px(tokens.ESPACO_1),
            cursor="hand2",
            takefocus=1,
            highlightthickness=self.borda if self.bordada else 0,
            highlightbackground=tokens.PRETO if self.bordada else self.fundo,
            highlightcolor=_ANEL,
        )

    # -- eventos ---------------------------------------------------------

    def _ligar(self):
        for alvo in (self.face, self):
            alvo.bind("<ButtonPress-1>", self._pressiona)
            alvo.bind("<ButtonRelease-1>", self._solta)
            alvo.bind("<Enter>", self._entra)
            alvo.bind("<Leave>", self._sai)
        self.face.bind("<Return>", lambda _e: self._executa())
        self.face.bind("<space>", lambda _e: self._executa())
        self.face.bind("<FocusIn>", lambda _e: self.face.configure(highlightcolor=_ANEL))
        self.face.bind("<FocusOut>", lambda _e: self.face.configure(highlightcolor=tokens.PRETO))

    def _pressiona(self, _evento):
        self._pressionado = True
        self.face.place(x=_PASSO, y=_PASSO)
        if self._sombra is not None:
            self._sombra.place(
                x=max(0, self.sombra_x - _PASSO),
                y=max(0, self.sombra_y - _PASSO),
            )

    def _solta(self, evento):
        if not self._pressionado:
            return
        self._pressionado = False
        self._descansa()
        dentro = (
            0 <= evento.x < self.face.winfo_width()
            and 0 <= evento.y < self.face.winfo_height()
        )
        if dentro:
            self._executa()

    def _descansa(self):
        self.face.place(x=0, y=0)
        if self._sombra is not None:
            self._sombra.place(x=self.sombra_x, y=self.sombra_y)

    def _entra(self, _evento):
        self.face.configure(bg=_HOVER[self.variante])

    def _sai(self, _evento):
        if self._pressionado:
            return
        self.face.configure(bg=self.fundo)
        self.face.configure(highlightcolor=tokens.PRETO)

    def _executa(self):
        self.focus_set()
        if self.comando:
            self.comando()

    # -- estado ----------------------------------------------------------

    @property
    def pressionado(self):
        return self._pressionado

    def definir_texto(self, texto):
        self._texto = texto
        self.face.configure(text=tipografia.maiuscula(texto))

    def ligar(self, comando):
        self.comando = comando
