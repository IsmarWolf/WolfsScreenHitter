"""Caixa de dialogo do design system.

O dialogo do proprio Tk e o certo para confirmar algo: ele ja vem no
idioma do sistema, e recusar um "salvar sem salvar" usando um popup
estranho seria uma pior experiencia do que o padrao.

O que o dialogo do sistema nao faz e ter a cara da tela. Por isso o
nome do perfil, que e a unica coisa que o usuario precisa escrever na
primeira vez que abre o programa, tem a sua propria janela: mesma
paleta, mesma borda, mesma fonte, e o mesmo botao de fechar que o resto
da tela usa.

A janela e modal de verdade, com grab_set e wait_window, e nao um
"desenho por cima". Isso importa porque o teclado tem de ir para ela:
sem grab, o Tab continuaria andando pelo formulario que esta atras, e o
Enter criaria um perfil com o nome do campo que estivesse em foco.
"""

import tkinter as tk

from ..design import tokens, tipografia
from .botao import Botao
from .painel import Divisor, Painel


def pedir_texto(pai, titulo, valor="", instrucao="", confirmar="Confirmar"):
    """Abre uma janela pedindo um texto. Devolve o texto, ou None se cancelou.

    Bloqueia ate a janela fechar, entao quem chama continua logo abaixo
    com a resposta na mao.
    """
    janela = tk.Toplevel(pai)
    janela.title(titulo)
    janela.configure(bg=tokens.BG_CANVAS)
    janela.transient(pai)
    janela.resizable(False, False)

    resposta = {"texto": None}

    cabecalho = tk.Frame(janela, bg=tokens.AZUL, bd=0, highlightthickness=0)
    cabecalho.pack(fill="x")
    tk.Label(
        cabecalho,
        text=tipografia.maiuscula(titulo),
        font=tipografia.fonte("h3"),
        bg=tokens.AZUL,
        fg=tokens.BRANCO,
    ).pack(side="left", padx=tokens.px(tokens.ESPACO_4), pady=tokens.px(tokens.ESPACO_3))
    tk.Frame(cabecalho, bg=tokens.PRETO, height=tokens.px(tokens.BORDA_GROSSA)).pack(
        fill="x", side="bottom"
    )

    corpo = tk.Frame(janela, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0)
    corpo.pack(fill="both", expand=True, padx=tokens.px(tokens.ESPACO_4),
               pady=tokens.px(tokens.ESPACO_4))

    if instrucao:
        tk.Label(
            corpo,
            text=instrucao,
            font=tipografia.fonte("corpo"),
            bg=tokens.BG_CANVAS,
            fg=tokens.PRETO,
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=(0, tokens.px(tokens.ESPACO_2)))

    cartao = Painel(corpo, borda=tokens.BORDA_FINA)
    cartao.pack(fill="x")

    moldura = tk.Frame(cartao.corpo, bg=tokens.PRETO, bd=0, highlightthickness=0)
    moldura.pack(fill="x")
    entrada = tk.Entry(
        moldura,
        font=tipografia.fonte("h2"),
        bg=tokens.BRANCO,
        fg=tokens.PRETO,
        insertbackground=tokens.PRETO,
        selectbackground=tokens.AZUL,
        selectforeground=tokens.BRANCO,
        relief="flat",
        bd=0,
        highlightthickness=0,
        width=34,
    )
    entrada.insert(0, valor)
    entrada.pack(fill="x", padx=tokens.px(tokens.BORDA_FINA),
                 pady=tokens.px(tokens.BORDA_FINA))
    entrada.select_range(0, tk.END)

    erro = tk.Label(
        corpo,
        text="",
        font=tipografia.fonte("label"),
        bg=tokens.BG_CANVAS,
        fg=tokens.VERMELHO,
        anchor="w",
    )
    erro.pack(fill="x", pady=(tokens.px(tokens.ESPACO_1), 0))

    Divisor(janela).pack(fill="x", pady=(0, 0))

    acoes = tk.Frame(janela, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0)
    acoes.pack(fill="x", padx=tokens.px(tokens.ESPACO_4), pady=tokens.px(tokens.ESPACO_3))

    def _aceitar():
        texto = entrada.get().strip()
        if not texto:
            erro.configure(text="O NOME NAO PODE FICAR VAZIO.")
            entrada.focus_set()
            return
        resposta["texto"] = texto
        janela.destroy()

    def _cancelar():
        janela.destroy()

    # Os rotulos vem do parametro, nao de um metodo com o mesmo nome: uma
    # funcao local chamada "confirmar" esconderia o texto e o Botao
    # acabaria desenhando o repr da funcao em vez do botao. O texto sai em
    # caixa normal, como os botoes da barra; quem desenha e o Botao que
    # maiusculiza.
    Botao(acoes, confirmar, _aceitar, variante="primario").pack(side="left")
    Botao(acoes, "Cancelar", _cancelar, variante="contorno").pack(
        side="left", padx=(tokens.px(tokens.ESPACO_2), 0)
    )

    entrada.bind("<Return>", lambda _e: _aceitar())
    janela.bind("<Escape>", lambda _e: _cancelar())
    entrada.focus_set()

    janela.update_idletasks()
    _centralizar(janela, pai)
    janela.grab_set()
    pai.wait_window(janela)
    return resposta["texto"]


def _centralizar(janela, pai):
    largura = janela.winfo_reqwidth()
    altura = janela.winfo_reqheight()
    x = pai.winfo_rootx() + (pai.winfo_width() - largura) // 2
    y = pai.winfo_rooty() + (pai.winfo_height() - altura) // 3
    janela.geometry(f"{largura}x{altura}+{max(0, x)}+{max(0, y)}")
