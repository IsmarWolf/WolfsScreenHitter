"""Widgets do formulario, gerados a partir dos campos do modelo.

Cada Campo vira uma linha: rotulo, entrada e a dica. Nada aqui decide o
que e valido; isso e do modelo. A janela so pede uma linha por Campo e
depois le o texto de volta.
"""

import tkinter as tk
from tkinter import ttk

from . import model


class Linha:
    """Uma linha do formulario: o widget, e o texto que ele representa."""

    def __init__(self, campo, widget, dica):
        self.campo = campo
        self.widget = widget
        self.dica = dica
        self.erro = None

    @property
    def caminho(self):
        return self.campo.caminho

    def texto(self):
        if isinstance(self.widget, ttk.Combobox):
            return self.widget.get()
        if isinstance(self.widget, tk.BooleanVar):
            return model.para_texto(self.widget.get())
        return self.widget.get()

    def definir(self, texto):
        """Coloca um valor na linha sem contar como edicao do usuario."""
        if isinstance(self.widget, ttk.Combobox):
            self.widget.set(texto)
        elif isinstance(self.widget, tk.BooleanVar):
            self.widget.set(model.de_texto(texto, "bool", self.caminho))
        else:
            self.widget.delete(0, tk.END)
            self.widget.insert(0, texto)

    def marcar_erro(self, mensagem):
        self.erro = mensagem
        if isinstance(self.widget, ttk.Entry):
            self.widget.configure(style="Erro.TEntry")
        self.dica.configure(text=mensagem, foreground="#b00020")

    def limpar_erro(self):
        self.erro = None
        if isinstance(self.widget, ttk.Entry):
            self.widget.configure(style="TEntry")
        self.dica.configure(text=self.campo.dica, foreground="#666666")


def criar_linha(quadro, campo, valor):
    """Cria a linha de um campo dentro de quadro e devolve a Linha."""
    caixa = tk.Frame(quadro)
    caixa.pack(fill="x", pady=3)

    tk.Label(caixa, text=campo.rotulo, width=22, anchor="w").pack(side="left")

    if campo.tipo == "escolha":
        widget = ttk.Combobox(caixa, values=list(campo.opcoes), state="readonly", width=18)
    elif campo.tipo == "bool":
        widget = tk.BooleanVar(value=model.de_texto(valor, "bool", campo.caminho))
        ttk.Checkbutton(caixa, variable=widget).pack(side="left")
    else:
        widget = ttk.Entry(caixa, width=20)
        widget.insert(0, valor)

    if not isinstance(widget, tk.BooleanVar):
        widget.pack(side="left", padx=(6, 0))

    dica = tk.Label(caixa, text=campo.dica, foreground="#666666", anchor="w", wraplength=300)
    dica.pack(side="left", fill="x", expand=True, padx=(10, 0))

    return Linha(campo, widget, dica)


def montar_formulario(quadro, campos, ao_mudar):
    """Desenha os grupos visiveis e devolve as linhas por caminho.

    Recebe o dicionario achatado que a janela mantem, e nao o perfil
    aninhado: assim a tela mostra exatamente o que esta em edicao, sem
    passar por uma conversao que poderia esconder um valor.
    """
    contexto = model.contexto_dos_campos(campos)
    linhas = {}

    for _identificador, titulo, condicao, grupo in model.GRUPOS:
        if condicao and not model.PERFILADO[condicao](contexto):
            continue

        moldura = ttk.LabelFrame(quadro, text=titulo, padding=8)
        moldura.pack(fill="x", padx=6, pady=6)

        for campo in grupo:
            if not campo.visivel(contexto):
                continue
            linha = criar_linha(moldura, campo, campos.get(campo.caminho, ""))
            _ligar(linha, ao_mudar)
            linhas[campo.caminho] = linha

    return linhas


def _ligar(linha, ao_mudar):
    """Avisa a cada mudanca da linha, e nao so quando o foco sai da caixa."""
    widget = linha.widget

    def avisar(*_args):
        if linha.erro:
            linha.limpar_erro()
        ao_mudar(linha.caminho, linha.texto())

    if isinstance(widget, ttk.Combobox):
        widget.bind("<<ComboboxSelected>>", avisar)
    elif isinstance(widget, tk.BooleanVar):
        widget.trace_add("write", avisar)
    else:
        widget.bind("<KeyRelease>", avisar)
        widget.bind("<FocusOut>", avisar)
