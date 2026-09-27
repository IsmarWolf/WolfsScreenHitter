"""Seletor de perfil da barra superior.

Trocar a lista da lateral por um dropdown no topo e o que o pedido de
tela minimalista pede, e tambem faz sentido com a regra nova de que todo
perfil ja nasce gravado: quando todo perfil tem nome e existe em disco,
a pergunta "qual deles" e uma pergunta de agora, e a lista inteira nao
precisa ocupar uma coluna da tela para isso.

O popup e uma Toplevel sem borda, apoiada embaixo do seletor e do tamanho
da propria lista, e dentro dele quem sabe desenhar os perfis e a
ListaPerfis de sempre. A lista nao foi reescrita: ela ja sabe do teclado,
do marcador por perfil e do retangulo amarelo, e duplicar isso aqui seria
ter duas listas para consertar.
"""

import tkinter as tk

from ..design import tokens, tipografia
from .lista import ListaPerfis


class SeletorPerfil(tk.Frame):
    """Campo que mostra o perfil aberto e abre a lista ao clicar."""

    def __init__(self, pai, ao_escolher, largura=260):
        super().__init__(pai, bg=tokens.PRETO, bd=0, highlightthickness=0)
        self.ao_escolher = ao_escolher
        self.caminho = None
        self.largura = largura
        self._pendentes = []
        self._popup = None

        self.moldura = tk.Frame(self, bg=tokens.PRETO, bd=0, highlightthickness=0)
        self.moldura.pack(fill="both", expand=True)

        self.rotulo = tk.Label(
            self.moldura,
            text="PERFIL",
            font=tipografia.fonte("label"),
            bg=tokens.BRANCO,
            fg=tokens.PRETO,
            anchor="w",
        )
        self.rotulo.pack(side="left", padx=tokens.px(tokens.ESPACO_3),
                         pady=tokens.px(tokens.ESPACO_1))

        self.nome = tk.Label(
            self.moldura,
            text="NENHUM",
            font=tipografia.fonte("h3"),
            bg=tokens.BRANCO,
            fg=tokens.AZUL,
            anchor="e",
        )
        self.nome.pack(side="left", fill="x", expand=True, padx=tokens.px(tokens.ESPACO_2))

        self.seta = tk.Canvas(
            self.moldura,
            width=tokens.px(26),
            height=tokens.px(26),
            bg=tokens.BRANCO,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.seta.pack(side="right", padx=tokens.px(tokens.ESPACO_2),
                       pady=tokens.px(tokens.ESPACO_1))
        self._desenhar_seta()

        self.configure(width=tokens.px(largura))
        self.pack_propagate(False)
        self._ligar()

    def _ligar(self):
        for alvo in (self, self.moldura, self.rotulo, self.nome, self.seta):
            alvo.bind("<Button-1>", lambda _e: self.alternar())
        self.nome.configure(takefocus=1)
        self.nome.bind("<Return>", lambda _e: self.alternar())
        self.nome.bind("<space>", lambda _e: self.alternar())

    def _desenhar_seta(self, para_cima=False):
        self.seta.delete("tudo")
        centro = tokens.px(13)
        direcao = -1 if para_cima else 1
        self.seta.create_polygon(
            centro - tokens.px(6),
            centro - direcao * tokens.px(3),
            centro + tokens.px(6),
            centro - direcao * tokens.px(3),
            centro,
            centro + direcao * tokens.px(4),
            fill=tokens.PRETO,
            outline=tokens.PRETO,
        )

    # -- estado ----------------------------------------------------------

    def definir_perfil(self, caminho, sujo=False):
        self.caminho = caminho
        if caminho is None:
            self.nome.configure(text="NENHUM", fg=tokens.PRETO)
        else:
            self.nome.configure(text=caminho.stem + (" *" if sujo else ""), fg=tokens.AZUL)

    # -- popup -----------------------------------------------------------

    def alternar(self):
        self.fechar() if self._popup else self.abrir()

    def abrir(self):
        if self._popup:
            return
        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.configure(bg=tokens.PRETO)
        self._popup.transient(self.winfo_toplevel())

        # O trace segue o seletor: se a janela fechar com o popup aberto, o
        # popup tem de ir junto, senao ele fica flutuando sem dono.
        self.winfo_toplevel().bind("<Destroy>", self._se_dono_morreu, add="+")

        moldura = tk.Frame(self._popup, bg=tokens.PRETO, bd=0, highlightthickness=0)
        moldura.pack(fill="both", expand=True, padx=tokens.px(tokens.BORDA_FINA),
                     pady=tokens.px(tokens.BORDA_FINA))

        altura = tokens.px(60) + tokens.px(24)
        lista = ListaPerfis(
            moldura,
            ao_selecionar=self._escolheu,
            fundo=tokens.BRANCO,
            tinta=tokens.PRETO,
            altura=altura,
        )
        lista.pack(fill="both", expand=True)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        largura = self.winfo_width()
        self._popup.geometry(f"{largura}x{altura}+{x}+{y}")
        self._popup.bind("<Escape>", lambda _e: self.fechar())
        self._popup.bind("<FocusOut>", lambda _e: self.fechar())
        self._popup.update_idletasks()
        lista.definir_itens(self._pendentes, self.caminho)
        lista.focus_set()
        self._desenhar_seta(para_cima=True)
        self._lista = lista

    def _itens(self):
        return self._pendentes

    def definir_itens(self, caminhos):
        self._pendentes = list(caminhos)
        if self._popup:
            self._lista.definir_itens(self._pendentes, self.caminho)

    def _escolheu(self, caminho):
        self.fechar()
        if caminho != self.caminho:
            self.ao_escolher(caminho)

    def fechar(self):
        if not self._popup:
            return
        self._popup.destroy()
        self._popup = None
        self._desenhar_seta(para_cima=False)

    def _se_dono_morreu(self, _evento):
        self.fechar()

    def destroy(self):
        self.fechar()
        super().destroy()
