"""Barra de abas: duas telas de configuracao dentro da mesma janela.

A tela do editor tem duasConfiguracoes, uma para o que se responde sem
pensar e outra para os numeros de ajuste. Trocar de aba redesenha o
formulario inteiro, o mesmo caminho que trocar o detector ja usava, e
nao um place novo: os campos sao os mesmos objetos do modelo, so que
filtrados por nivel.

A aba ativa e um bloco preto com texto branco, e a inativa e um bloco
branco com contorno preto. Sem sublinhado e sem borda arredondada,
porque o resto da tela nao tem nenhum dos dois, e uma aba com
sublinhado pareceria pertencer a outra biblioteca.

O Container guarda as duas abas como filhos de um mesmo Frame, e quem
troca e quem redesenha: aqui so mora a pintura e o clique.
"""

import tkinter as tk

from ..design import tokens, tipografia

_CORES = {
    "ativa": (tokens.PRETO, tokens.BRANCO),
    "inativa": (tokens.BRANCO, tokens.PRETO),
}


class Abas(tk.Frame):
    """Linha de abas. Diga quantas sao e o que cada uma chama."""

    def __init__(self, pai, itens, ao_trocar, ativa=None):
        super().__init__(pai, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0)
        self.ao_trocar = ao_trocar
        self.ativa = ativa
        self._botoes = {}

        for chave, titulo in itens:
            botao = _Aba(self, titulo, lambda c=chave: self._clicou(c))
            botao.pack(side="left", padx=(0, tokens.px(tokens.ESPACO_1)))
            self._botoes[chave] = botao

        if ativa is not None:
            self.definir_ativa(ativa)

    def definir_ativa(self, chave):
        """Marca a aba. Repinta as duas, porque sair de ativa tambem muda."""
        if chave not in self._botoes:
            return
        self.ativa = chave
        for nome, botao in self._botoes.items():
            botao.repintar(nome == chave)

    def _clicou(self, chave):
        if chave == self.ativa:
            return
        # A barra so avisa. Quem pinta a aba e quem redesenha e a janela,
        # porque ela e a dona do nivel. Se a barra se marcase junto, o
        #programa que troca de aba por outro caminho -- recarregar um
        # perfil, um atalho -- deixaria a barra mostrando uma coisa e o
        # formulario mostrando outra.
        self.ao_trocar(chave)


class _Aba(tk.Label):
    """Um bloco da barra. Label porque o texto e tudo que ele mostra."""

    def __init__(self, pai, titulo, comando):
        super().__init__(
            pai,
            text=tipografia.maiuscula(titulo),
            font=tipografia.fonte("h3"),
            padx=tokens.px(tokens.ESPACO_3),
            pady=tokens.px(tokens.ESPACO_2),
            cursor="hand2",
            takefocus=1,
        )
        self._comando = comando
        self.bind("<Button-1>", lambda _e: self._comando())
        self.bind("<Return>", lambda _e: self._comando())
        self.bind("<space>", lambda _e: self._comando())
        self.bind("<FocusIn>", lambda _e: self.configure(highlightcolor=tokens.AMARELO))
        self.bind("<FocusOut>", lambda _e: self.configure(highlightcolor=tokens.PRETO))

    def repintar(self, ativa):
        fundo, tinta = _CORES["ativa" if ativa else "inativa"]
        self.configure(
            bg=fundo,
            fg=tinta,
            highlightthickness=tokens.px(tokens.BORDA_FINA),
            highlightbackground=tokens.PRETO,
        )
