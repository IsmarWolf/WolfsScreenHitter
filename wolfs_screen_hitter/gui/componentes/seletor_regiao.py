"""Seletor de regiao: arrastar sobre a tela para escolher a area.

Quatro numeros de largura, altura, esquerda e topo nao dizem nada sobre a
tela. "Esquerda 0, topo 0, 1920 x 1080" e o monitor inteiro; a unica forma de
saber se e a janela do jogo e olhar. Por isso o campo e um seletor, e nao
quatro entradas: a pessoa arrasta o retangulo em volta daquilo que ela quer,
e a tela escreve os numeros.

A camada e um retangulo escuro sobre a area escolhida, com a selecao
contornada em amarelo e uma faixa que mostra o tamanho enquanto se arrasta.
Quem fecha e quem decide e sempre a pessoa: Esc cancela e o perfil fica
como estava.

O espaco de coordenadas e o ponto que costuma dar errado. O programa inteiro
mede a tela com GetSystemMetrics, e e em pixel fisico que o perfil guarda.
O overlay usa a mesma funcao, screens(), que o modo de regiao "screen" usa
para a mesma pergunta -- entao o retangao arrastado e o retangulo que o
perfil vai procurar, sem chance de os dois discordarem da definicao de "tela
principal".

Entre o Tk e o Win32 ha um fator, medido em vez de assumido: um pixel de
canvas pode valer mais de um pixel fisico se o processo algum dia se
declarar ciente de DPI. Hoje o fator e 1 e a conversao e a identidade, mas
ela esta escrita para continuar valendo.
"""

import tkinter as tk

from ... import windows
from ..design import tokens, tipografia

# Abaixo disso nao e um retangulo, e um clique. Nao vale gravar "largura 2"
# e descobrir o erro so quando a detecao nunca achar nada.
_MINIMO = 8
_TRANSLUCIDO = 0.35


def fator_do_tk(raiz):
    """Quantos pixels o Tk conta por pixel que o Windows mede.

    Deve ser 1: enquanto o processo nao se declara ciente de DPI, os dois
    falam em pixel fisico. A funcao existe para o seletor nao assumir isso
    em silencio.
    """
    largura_win32 = max(1, windows.virtual_screen()[2])
    return max(1, raiz.winfo_screenwidth()) / largura_win32


def escolher_regiao(pai):
    """Cobre a tela principal e espera o retangulo.

    Devolve (esquerda, topo, largura, altura) no sistema de coordenadas que
    resolve_region entende, ou None se a pessoa desistiu.
    """
    seletor = SeletorRegiao(pai)
    return seletor.esperar()


class SeletorRegiao:
    """A camada de arraste sobre a tela principal."""

    def __init__(self, pai):
        self.pai = pai
        self.regiao = None
        # A mesma fonte de verdade do resto do programa, e nao o screenwidth
        # do Tk: se as duas discordassem, o perfil gravaria uma regiao e o
        # detector recortaria outra.
        self.principal = windows.screen()
        self.fator = fator_do_tk(pai)
        self.inicio = None
        self.atual = None
        self.retangulo = None

    # -- a janela ---------------------------------------------------------

    def esperar(self):
        # A janela principal sai de cena. Sem isso a pessoa arrasta por cima
        # do proprio formulario e escolhe a area sem ver o que tem embaixo.
        estava_visivel = self.pai.state() == "normal"
        if estava_visivel:
            self.pai.withdraw()

        self.camada = None
        try:
            self._montar()
            self._ligar()
            self.camada.grab_set()
            self.pai.wait_window(self.camada)
        finally:
            if estava_visivel:
                self.pai.deiconify()
                self.pai.lift()
        return self.regiao

    def _montar(self):
        self.camada = tk.Toplevel(self.pai)
        esquerda, topo, largura, altura = self.principal
        self.camada.overrideredirect(True)
        self.camada.attributes("-topmost", True)
        self.camada.attributes("-alpha", _TRANSLUCIDO)
        self.camada.configure(bg=tokens.PRETO)
        self.camada.geometry(
            f"{round(largura * self.fator)}x{round(altura * self.fator)}"
            f"+{round(esquerda * self.fator)}+{round(topo * self.fator)}"
        )

        self.quadro = tk.Canvas(
            self.camada,
            width=round(largura * self.fator),
            height=round(altura * self.fator),
            bg=tokens.PRETO,
            bd=0,
            highlightthickness=0,
            cursor="crosshair",
            takefocus=1,
        )
        self.quadro.pack(fill="both", expand=True)

        self.forma = {
            "instrucao": self.quadro.create_text(
                self.quadro.winfo_reqwidth() // 2,
                32,
                text="ARRASTE EM VOLTA DA AREA  /  ESC SAI",
                fill=tokens.BRANCO,
                font=tipografia.fonte("h3"),
            ),
            "medida": self.quadro.create_text(
                self.quadro.winfo_reqwidth() // 2,
                64,
                text="",
                fill=tokens.AMARELO,
                font=tipografia.fonte("display"),
            ),
        }


    # -- geometria --------------------------------------------------------

    def para_win32(self, x, y):
        """Ponto do canvas em pixel de GetSystemMetrics.

        O canvas cobre a tela principal, entao a origem dele e o canto
        esquerdo de cima da tela principal -- que ja vem em coordenada da
        area virtual. O canvas e maior em pixel de tela do que em pixel de
        medida, entao a divisao pelo fator fecha a conta.
        """
        esquerda, topo = self.principal[0], self.principal[1]
        return (
            round(esquerda + x / self.fator),
            round(topo + y / self.fator),
        )

    def _atualizar(self):
        if self.inicio is None or self.atual is None:
            return
        x0, y0 = self.inicio
        x1, y1 = self.atual
        esquerda, topo = min(x0, x1), min(y0, y1)
        largura, altura = abs(x1 - x0), abs(y1 - y0)

        self.quadro.delete("alvo")
        if largura < _MINIMO or altura < _MINIMO:
            self.retangulo = None
            self._dizer("")
            return

        self.retangulo = (esquerda, topo, largura, altura)
        self._dizer(f"{round(largura / self.fator)} x {round(altura / self.fator)}")

        # O que esta em volta da selecao ganha um pano escuro. A area
        # escolhida fica sem pano, e e por isso que ela continua visivel
        # atraves da camada.
        limite_x, limite_y = self.quadro.winfo_width(), self.quadro.winfo_height()
        for xa, ya, xb, yb in (
            (0, 0, esquerda, limite_y),
            (esquerda + largura, 0, limite_x, limite_y),
            (esquerda, 0, esquerda + largura, topo),
            (esquerda, topo + altura, esquerda + largura, limite_y),
        ):
            self.quadro.create_rectangle(
                xa, ya, xb, yb, fill=tokens.PRETO, stipple="gray50", outline="", tags="alvo"
            )
        self.quadro.create_rectangle(
            esquerda, topo, esquerda + largura, topo + altura,
            outline=tokens.AMARELO, width=tokens.px(3), tags="alvo",
        )
        # As alcas nos cantos: e o que comunica "da para arrastar por aqui".
        for xa, ya in (
            (esquerda, topo),
            (esquerda + largura, topo + altura),
        ):
            self.quadro.create_rectangle(
                xa - tokens.px(3), ya - tokens.px(3), xa + tokens.px(3), ya + tokens.px(3),
                fill=tokens.AMARELO, outline=tokens.PRETO, tags="alvo",
            )

    def _dizer(self, texto):
        self.quadro.itemconfigure(self.forma["medida"], text=texto)

    # -- interacao --------------------------------------------------------

    def _ligar(self):
        self.quadro.bind("<ButtonPress-1>", self._comecar)
        self.quadro.bind("<B1-Motion>", self._mover)
        self.quadro.bind("<ButtonRelease-1>", self._soltar)
        self.quadro.bind("<Return>", lambda _e: self._aceitar())
        self.quadro.bind("<Escape>", lambda _e: self.camada.destroy())
        self.camada.bind("<Escape>", lambda _e: self.camada.destroy())
        # focus_set so pega se a janela ja estiver visivel e em foco, e uma
        # camada sem barra de titulo nao toma foco sozinha. Sem isto o Esc --
        # a saida de emergencia de quem esta com a tela coberta -- so
        # funciona depois do primeiro clique, o que e tarde demais.
        self.quadro.focus_force()

    def _comecar(self, evento):
        self.inicio = (evento.x, evento.y)
        self.atual = self.inicio
        self._atualizar()

    def _mover(self, evento):
        self.atual = (evento.x, evento.y)
        self._atualizar()

    def _soltar(self, evento):
        self.atual = (evento.x, evento.y)
        self._atualizar()
        if self.retangulo is None:
            # Clique sem arrastar: nao e erro, so nao escolheu nada ainda.
            self.inicio = self.atual = None
            return
        self._aceitar()

    def _aceitar(self):
        if self.retangulo is None:
            return
        esquerda, topo, largura, altura = self.retangulo
        x, y = self.para_win32(esquerda, topo)
        self.regiao = (
            x,
            y,
            max(1, round(largura / self.fator)),
            max(1, round(altura / self.fator)),
        )
        self.camada.destroy()
