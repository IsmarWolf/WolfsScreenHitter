"""Linha de campo: o ponto onde um Campo do modelo vira um input.

Aqui mora a unica decisao que o Tk nao perdoa: a entrada de texto. Ela
continua sendo um Entry de verdade, e nao um desenho em Canvas, porque o
Entry e o que traz cursor piscando, selecao com o mouse, Ctrl+A, Ctrl+C,
Ctrl+V, Home, End e as setas. Desenhar isso a mao seria refazer o
componente de edicao de texto do sistema inteiro para ficar mais bonito.

O que muda aqui e a moldura: fundo branco, contorno preto de 2px, e o
estado de erro, que troca o fundo por um amarelo de alerta e pinta a dica
de vermelho.

O seletor de opcoes tambem e um Entry, e nao um Combobox, pelo mesmo
motivo: o dropdown do ttk no Windows ignora cor e borda. Aqui a seta e um
triangulo desenhado, e a lista de opcoes e um menu do proprio Tk.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from ..design import tokens, tipografia

VERDADEIRO = ("1", "true", "sim", "s", "yes", "verdadeiro")


def para_texto(valor):
    return "sim" if valor else "nao"


class LinhaCampo(tk.Frame):
    """Rotulo, entrada e dica de um campo, no estilo do design system."""

    def __init__(self, pai, campo, valor, ao_mudar, fundo=tokens.AMARELO_PASTEL, pasta=""):
        super().__init__(pai, bg=fundo, bd=0, highlightthickness=0)
        self.campo = campo
        self.ao_mudar = ao_mudar
        self.fundo = fundo
        self.pasta = pasta
        self.erro = None
        self._trace = None

        self._rotulo = tk.Label(
            self,
            text=tipografia.maiuscula(campo.rotulo),
            font=tipografia.fonte("label"),
            bg=fundo,
            fg=tokens.PRETO,
            anchor="w",
            width=22,
        )
        self._rotulo.pack(
            side="left", padx=(0, tokens.px(tokens.ESPACO_2)), pady=tokens.px(tokens.ESPACO_1)
        )

        if campo.tipo == "bool":
            self._montar_caixa(valor)
        elif campo.tipo == "escolha":
            self._montar_seletor(valor)
        else:
            self._montar_texto(valor)

        self._dica = tk.Label(
            self,
            text=campo.dica,
            font=tipografia.fonte("corpo"),
            bg=fundo,
            fg=tokens.PRETO,
            anchor="w",
            justify="left",
            wraplength=tokens.px(280),
        )
        self._dica.pack(
            side="left", fill="x", expand=True, padx=(tokens.px(tokens.ESPACO_3), 0)
        )

    # -- construcao ------------------------------------------------------

    def _preenchimento(self):
        """Fundo da entrada: amarelo quando o campo esta reprovado."""
        return tokens.AMARELO if self.erro else tokens.BRANCO

    def _caixa(self, lado=None):
        """Fundo preto, entrada por dentro, borda de 2px.

        lado fixa o tamanho, e so o checkbox precisa disso. Nos outros
        tipos a moldura e deixada medir a entrada: um texto longo estica o
        campo, e foi assim que o modelo ja desenhava.
        """
        moldura = tk.Frame(self, bg=tokens.PRETO, bd=0, highlightthickness=0)
        moldura.pack(side="left")
        if lado:
            moldura.configure(width=lado, height=lado)
            moldura.pack_propagate(False)
        return moldura

    def _ligar_var(self):
        self._trace = self._var.trace_add("write", self._mudou)

    def _mudou(self, *_args):
        if self.erro:
            self.limpar_erro()
        self.ao_mudar(self.campo.caminho, self.texto())

    def _montar_caixa(self, valor):
        moldura = self._caixa(tokens.px(18))
        self._var = tk.BooleanVar(value=valor.strip().lower() in VERDADEIRO)
        self.entrada = tk.Checkbutton(
            moldura,
            variable=self._var,
            bg=self._preenchimento(),
            activebackground=self._preenchimento(),
            activeforeground=tokens.PRETO,
            bd=0,
            highlightthickness=tokens.px(tokens.BORDA_FINA),
            highlightbackground=tokens.PRETO,
            highlightcolor=tokens.AMARELO,
            takefocus=1,
            cursor="hand2",
        )
        self.entrada.pack(
            padx=tokens.px(tokens.BORDA_FINA), pady=tokens.px(tokens.BORDA_FINA)
        )
        self._ligar_var()

    def _montar_texto(self, valor):
        moldura = self._caixa()
        self._moldura = moldura
        self.entrada = tk.Entry(
            moldura,
            font=tipografia.fonte("corpo"),
            bg=self._preenchimento(),
            fg=tokens.PRETO,
            insertbackground=tokens.PRETO,
            selectbackground=tokens.AZUL,
            selectforeground=tokens.BRANCO,
            relief="flat",
            bd=0,
            highlightthickness=tokens.px(tokens.BORDA_FINA),
            highlightbackground=tokens.PRETO,
            highlightcolor=tokens.AMARELO,
            width=18,
            takefocus=1,
        )
        self.entrada.insert(0, valor)
        self.entrada.pack(
            side="left", padx=tokens.px(tokens.BORDA_FINA),
            pady=tokens.px(tokens.BORDA_FINA)
        )
        self.entrada.bind("<KeyRelease>", lambda _e: self._mudou())
        self.entrada.bind("<FocusOut>", lambda _e: self._mudou())

        if self.campo.seletor == "arquivo":
            self._montar_arquivo()

    def _montar_arquivo(self):
        """O botao de escolher o arquivo mora dentro da moldura da entrada,
        e nao ao lado dela, para que pareca parte do campo e nao um botao
        solto na linha. E um Canvas em vez de um Botao porque aqui o
        desenho e um quadrado do mesmo tamanho da seta do seletor de
        opcoes, e nao um texto."""
        self._abrir = tk.Canvas(
            self._moldura,
            width=tokens.px(30),
            height=tokens.px(26),
            bg=tokens.BRANCO,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            takefocus=1,
        )
        self._abrir.pack(
            side="left", padx=(0, tokens.px(tokens.BORDA_FINA)),
            pady=tokens.px(tokens.BORDA_FINA),
        )
        self._desenhar_abrir(False)
        self._abrir.bind("<Button-1>", lambda _e: self._escolher_arquivo())
        self._abrir.bind("<Enter>", lambda _e: self._desenhar_abrir(True))
        self._abrir.bind("<Leave>", lambda _e: self._desenhar_abrir(False))

    def _desenhar_abrir(self, sobre=False):
        self._abrir.delete("tudo")
        self._abrir.configure(bg=tokens.AMARELO if sobre else tokens.BRANCO)
        largura, altura = tokens.px(16), tokens.px(12)
        x, y = (tokens.px(30) - largura) // 2, (tokens.px(26) - altura) // 2
        # A pasta: um retangulo com a aba, do mesmo vocabulario de formas
        # usadas no resto da tela.
        self._abrir.create_rectangle(
            x, y + tokens.px(3), x + largura, y + altura,
            fill=tokens.AMARELO if sobre else tokens.BRANCO,
            outline=tokens.PRETO,
            width=tokens.px(tokens.BORDA_FINA),
        )
        self._abrir.create_rectangle(
            x, y, x + tokens.px(7), y + tokens.px(4),
            fill=tokens.AMARELO if sobre else tokens.BRANCO,
            outline=tokens.PRETO,
            width=tokens.px(tokens.BORDA_FINA),
        )

    def _escolher_arquivo(self):
        """Grava o caminho escolhido no campo, pelo mesmo caminho de
        qualquer outro texto digitado, para a validacao e o redesenho nao
        precisarem saber que o valor veio daqui."""
        escolhido = filedialog.askopenfilename(
            title="Escolher o template",
            initialdir=self._onde_procurar(),
            filetypes=[("Imagem PNG", "*.png"), ("Todas as imagens", "*.png *.jpg *.bmp")],
        )
        if not escolhido:
            return
        self.definir(self._caminho_relativo(escolhido))
        self.ao_mudar(self.campo.caminho, self.texto())

    def _onde_procurar(self):
        """O dialogo abre onde o arquivo esta, e nao na pasta do perfil."""
        atual = (self.texto() or "").strip()
        if atual:
            base = Path(atual)
            pasta = base.parent if base.parent != Path("") else None
            if pasta and pasta.is_dir():
                return str(pasta)
        return self.pasta or None

    def _caminho_relativo(self, caminho):
        """Se o PNG estiver na pasta do perfil, guarda so o nome.

        O perfil guarda o caminho, nao a imagem. Com o caminho relativo, o
        JSON continua valendo se a pasta inteira for movida ou copiada para
        outro lugar -- que e o caso normal de quem compartilha um perfil. De
        fora da pasta do perfil nao ha caminho relativo que faca sentido, e
        ai vai o caminho absoluto.
        """
        alvo = Path(caminho).resolve()
        if self.pasta:
            base = Path(self.pasta).resolve()
            try:
                return alvo.relative_to(base).as_posix()
            except ValueError:
                pass
        return str(alvo)

    def _montar_seletor(self, valor):
        moldura = tk.Frame(self, bg=tokens.PRETO, bd=0, highlightthickness=0)
        moldura.pack(side="left")

        self._var = tk.StringVar(value=valor)
        self.entrada = tk.Entry(
            moldura,
            textvariable=self._var,
            font=tipografia.fonte("corpo"),
            bg=self._preenchimento(),
            fg=tokens.PRETO,
            relief="flat",
            bd=0,
            highlightthickness=0,
            width=16,
            takefocus=0,
        )
        self.entrada.pack(
            side="left", padx=tokens.px(tokens.BORDA_FINA), pady=tokens.px(tokens.BORDA_FINA)
        )

        # A seta e um Canvas: o ttk ignoraria a cor, e aqui ela e um
        # triangulo com contorno preto.
        self._seta = tk.Canvas(
            moldura,
            width=tokens.px(26),
            height=tokens.px(24),
            bg=self._preenchimento(),
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self._seta.pack(
            side="left", padx=(0, tokens.px(tokens.BORDA_FINA)),
            pady=tokens.px(tokens.BORDA_FINA),
        )
        self._desenhar_seta()
        self._seta.bind("<Button-1>", lambda _e: self._abrir_opcoes())
        self.entrada.bind("<Button-1>", lambda _e: self._abrir_opcoes())
        self._ligar_var()

    def _desenhar_seta(self):
        self._seta.delete("tudo")
        centro = tokens.px(13)
        self._seta.create_polygon(
            centro - tokens.px(5),
            centro - tokens.px(3),
            centro + tokens.px(5),
            centro - tokens.px(3),
            centro,
            centro + tokens.px(4),
            fill=tokens.PRETO,
            outline=tokens.PRETO,
        )

    def _abrir_opcoes(self):
        """Menu com as opcoes, no lugar do dropdown do ttk."""
        opcoes = list(self.campo.opcoes)
        if not opcoes:
            return "break"
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=tokens.BRANCO,
            fg=tokens.PRETO,
            activebackground=tokens.AMARELO,
            activeforeground=tokens.PRETO,
            activeborderwidth=0,
            font=tipografia.fonte("label"),
            relief="flat",
            borderwidth=0,
        )
        for opcao in opcoes:
            menu.add_command(
                label=tipografia.maiuscula(opcao),
                command=lambda valor=opcao: self._var.set(valor),
            )
        try:
            menu.tk_popup(
                self.entrada.winfo_rootx(),
                self.entrada.winfo_rooty() + self.entrada.winfo_height(),
            )
        finally:
            menu.grab_release()
        return "break"

    # -- estado ----------------------------------------------------------

    @property
    def caminho(self):
        return self.campo.caminho

    @property
    def widget(self):
        """O widget de entrada, para quem precisar focar."""
        return self.entrada

    def texto(self):
        if self.campo.tipo == "bool":
            return para_texto(self._var.get())
        if self.campo.tipo == "escolha":
            return self._var.get()
        return self.entrada.get()

    def definir(self, texto):
        """Coloca um valor na linha. Nao conta como edicao do usuario,
        porque quem chamou ja conhece o valor."""
        if self.campo.tipo == "bool":
            self._var.set(texto.strip().lower() in VERDADEIRO)
        elif self.campo.tipo == "escolha":
            self._var.set(texto)
        else:
            self.entrada.delete(0, tk.END)
            self.entrada.insert(0, texto)

    def focar(self):
        try:
            self.entrada.focus_set()
        except tk.TclError:
            pass

    def marcar_erro(self, mensagem):
        self.erro = mensagem
        self._repintar()
        self._dica.configure(text=mensagem, fg=tokens.VERMELHO)

    def limpar_erro(self):
        if self.erro is None:
            return
        self.erro = None
        self._repintar()
        self._dica.configure(text=self.campo.dica, fg=tokens.PRETO)

    def _repintar(self):
        fundo = self._preenchimento()
        if self.campo.tipo == "bool":
            self.entrada.configure(bg=fundo, activebackground=fundo)
        else:
            self.entrada.configure(bg=fundo)
        if self.campo.tipo == "escolha":
            self._seta.configure(bg=fundo)

    def destroy(self):
        # O trace segura referencia ao widget e sobrevive ao destroy, o que
        # faria o redesenho do formulario escrever num campo morto. Cortar
        # o trace antes e o que impede isso.
        if self._trace:
            try:
                self._var.trace_vdelete("write", self._trace)
            except (tk.TclError, ValueError, AttributeError):
                pass
            self._trace = None
        super().destroy()
