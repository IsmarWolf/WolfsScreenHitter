"""Janela do WolfsScreenHitter, no design system Bauhaus.

Nesta etapa a janela faz o ciclo do perfil: listar, abrir, criar, editar e
salvar. O que e valido continua sendo decidido pelo modelo, entao o que
esta na tela e o mesmo que a CLI le.

Sobre a escolha dos widgets: a barra superior, a lateral e o rodape sao
Canvas e Frame com cor, e nao ttk. O motivo e medido, nao moda: no Windows
com o tema vista ativo, o ttk ignora cor de fundo, borda e relevo, e o
resultado e um formulario cinza que nao pertence a esta tela. As entradas
de texto continuam nativas, porque quem traz selecao, clipboard, caret e
atalhos e o Entry, e refazer isso seria refazer o editor de texto do
sistema.

A estrutura e de cima para baixo: cabecalho azul com a assinatura, depois a
faixa de acoes, depois a lateral de perfis ao lado do formulario, e no pe
a barra de status amarela sobre o rodape preto.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .. import profiles
from . import estado as controlador
from . import model
from .componentes import Botao, Divisor, ListaPerfis, Painel
from .design import formas, tokens, tipografia
from .widgets import montar_formulario

_LARGURA = 1160
_ALTURA = 720
_LATERAL = 260


class Aplicacao(tk.Tk):
    def __init__(self, diretorio=None):
        # A fonte tem de estar registrada antes de existir a janela: o Tk so
        # enxerga o que o Windows ja informa quando a raiz e criada.
        tipografia.registrar_fonte_embutida()
        super().__init__()

        tokens.configurar_escala(self)
        tipografia.carregar(self)

        self.geometry(f"{tokens.px(_LARGURA)}x{tokens.px(_ALTURA)}")
        self.minsize(tokens.px(880), tokens.px(560))
        self.configure(bg=tokens.BG_CANVAS)

        self.estado = controlador.Estado(diretorio)
        self.caminhos = []
        self.linhas = {}
        self.grupos = {}
        self._grupo_aberto = None
        # Redesenhar o formulario escreve nos campos, e escrever num
        # checkbox dispara o evento dele de volta. Sem esta trava, trocar o
        # detector entraria em laco.
        self._reconstruindo = False

        self.mensagem = tk.StringVar()
        self.resumo = tk.StringVar()
        self._montar()
        self.atualizar_lista()

        # O formulario nasce antes de tentar abrir qualquer coisa. Se o
        # primeiro perfil da pasta estiver corrompido, abrir() so avisa e
        # devolve, e sem esta linha a tela ficaria sem um unico campo.
        self.novo()
        if self.caminhos:
            self.abrir(self.caminhos[0])

        self._atualizar_titulo()

    # -- layout ----------------------------------------------------------

    def _montar(self):
        self._montar_cabecalho()
        self._montar_acoes()

        Divisor(self).pack(fill="x")

        corpo = tk.Frame(self, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0)
        corpo.pack(fill="both", expand=True, padx=tokens.px(tokens.ESPACO_4),
                   pady=tokens.px(tokens.ESPACO_4))
        corpo.grid_columnconfigure(0, minsize=tokens.px(_LATERAL))
        corpo.grid_columnconfigure(1, weight=1)
        corpo.grid_rowconfigure(0, weight=1)

        self._montar_lateral(corpo)
        self._montar_formulario(corpo)
        self._montar_status()

    def _montar_cabecalho(self):
        """Azul, com a assinatura de circulo, quadrado e triangulo."""
        cabecalho = tk.Frame(self, bg=tokens.AZUL, bd=0, highlightthickness=0)
        cabecalho.pack(fill="x")
        self.cabecalho = cabecalho
        tk.Frame(cabecalho, bg=tokens.PRETO, height=tokens.px(tokens.BORDA_GROSSA)).pack(
            fill="x", side="bottom"
        )

        linha = tk.Frame(cabecalho, bg=tokens.AZUL, bd=0, highlightthickness=0)
        linha.pack(fill="x", padx=tokens.px(tokens.ESPACO_4), pady=tokens.px(tokens.ESPACO_3))

        marca = tk.Canvas(
            linha,
            width=tokens.px(92),
            height=tokens.px(32),
            bg=tokens.AZUL,
            bd=0,
            highlightthickness=0,
        )
        marca.pack(side="left", padx=(0, tokens.px(tokens.ESPACO_3)))
        formas.assinatura(
            marca,
            tokens.px(12),
            tokens.px(16),
            lado=tokens.px(18),
            espessura=tokens.px(tokens.BORDA_FINA),
        )

        tk.Label(
            linha,
            text="WOLFS SCREEN HITTER",
            font=tipografia.fonte("display"),
            bg=tokens.AZUL,
            fg=tokens.BRANCO,
        ).pack(side="left")

        tk.Label(
            linha,
            text="PERFIL DE DETECCAO",
            font=tipografia.fonte("label"),
            bg=tokens.AZUL,
            fg=tokens.AMARELO,
        ).pack(side="right", anchor="s")

    def _montar_acoes(self):
        """A barra de acoes fica entre o cabecalho e o conteudo, no cinza."""
        barra = tk.Frame(self, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0)
        barra.pack(fill="x", padx=tokens.px(tokens.ESPACO_4), pady=tokens.px(tokens.ESPACO_3))

        acoes = (
            ("Novo", self.novo, "primario"),
            ("Abrir", self.escolher_arquivo, "secundario"),
            ("Salvar", self.salvar, "amarelo"),
            ("Salvar como", self.salvar_como, "contorno"),
        )
        for rotulo, comando, variante in acoes:
            Botao(barra, rotulo, comando, variante=variante).pack(
                side="left", padx=(0, tokens.px(tokens.ESPACO_2))
            )

        Botao(barra, "Atualizar", self.atualizar_lista, variante="fantasma").pack(side="left")

        tk.Label(
            barra,
            textvariable=self.resumo,
            font=tipografia.fonte("label"),
            bg=tokens.BG_CANVAS,
            fg=tokens.PRETO,
            anchor="e",
        ).pack(side="right", fill="x", expand=True, padx=(tokens.px(tokens.ESPACO_3), 0))

    def _montar_lateral(self, pai):
        cartao = Painel(pai, marcador="circulo")
        cartao.grid(row=0, column=0, sticky="nsew", padx=(0, tokens.px(tokens.ESPACO_4)))

        tk.Label(
            cartao.corpo,
            text="PERFIS",
            font=tipografia.fonte("h3"),
            bg=tokens.BRANCO,
            fg=tokens.PRETO,
            anchor="w",
        ).pack(fill="x", pady=(0, tokens.px(tokens.ESPACO_2)))

        # A lista e um Canvas, entao o cartão precisa de uma altura propria
        # para ela poder rolar dentro.
        lista_area = tk.Frame(cartao.corpo, bg=tokens.BRANCO, bd=0, highlightthickness=0)
        lista_area.pack(fill="both", expand=True)

        self.lista = ListaPerfis(
            lista_area, ao_selecionar=self._abrir_da_lista, fundo=tokens.BRANCO, tinta=tokens.PRETO
        )
        self.lista.pack(fill="both", expand=True)

    def _montar_formulario(self, pai):
        """O formulario vai num canvas com rolagem, porque um grupo pode
        ser mais alto que a janela."""
        area = tk.Frame(pai, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0)
        area.grid(row=0, column=1, sticky="nsew")

        self.formulario = tk.Frame(area, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0)
        self._rolagem = Rolagem(area, self.formulario)
        self._rolagem.pack(fill="both", expand=True)

    def _montar_status(self):
        Divisor(self).pack(fill="x")

        status = tk.Frame(self, bg=tokens.AMARELO, bd=0, highlightthickness=0)
        status.pack(fill="x", padx=tokens.px(tokens.ESPACO_4), pady=tokens.px(tokens.ESPACO_2))
        self.status_bar = status
        self.status_label = tk.Label(
            status,
            textvariable=self.mensagem,
            font=tipografia.fonte("label"),
            bg=tokens.AMARELO,
            fg=tokens.PRETO,
            anchor="w",
        )
        self.status_label.pack(side="left", padx=tokens.px(tokens.ESPACO_2),
                               pady=tokens.px(tokens.ESPACO_1))

        # O rodape preto carrega a versao, para o bloco de status ficar
        # com uma funcao so: dizer o que aconteceu.
        rodape = tk.Frame(self, bg=tokens.PRETO, bd=0, highlightthickness=0)
        rodape.pack(fill="x")
        self.rodape = rodape
        tk.Label(
            rodape,
            text="APENAS MOVE O CURSOR. NAO CLICA, NAO DIGITA.",
            font=tipografia.fonte("label"),
            bg=tokens.PRETO,
            fg=tokens.BRANCO,
        ).pack(side="left", padx=tokens.px(tokens.ESPACO_4), pady=tokens.px(tokens.ESPACO_1))
        tk.Label(
            rodape,
            textvariable=self.resumo,
            font=tipografia.fonte("label"),
            bg=tokens.PRETO,
            fg=tokens.AMARELO,
            anchor="e",
        ).pack(side="right", padx=tokens.px(tokens.ESPACO_4))

    # -- lista de perfis -------------------------------------------------

    def atualizar_lista(self):
        """Redesenha a lista, mantendo selecionado o perfil aberto."""
        anterior = self.estado.caminho
        self.caminhos = self.estado.listar()
        self.lista.definir_itens(self.caminhos, anterior)

    def _abrir_da_lista(self, caminho):
        if caminho != self.estado.caminho:
            self._confirmar_descarte(lambda: self.abrir(caminho))

    def _confirmar_descarte(self, continuar):
        """Nao perde o que foi digitado sem perguntar."""
        if not self.estado.sujo or messagebox.askyesno(
            "Descartar mudancas", "Tem mudanca nao salva. Continuar?"
        ):
            continuar()

    # -- acoes -----------------------------------------------------------

    def novo(self):
        self.estado.novo()
        self._grupo_aberto = None
        self._redesenhar()
        self.avisar(tipografia.maiuscula("perfil novo. use salvar para escolher o nome."))

    def abrir(self, caminho):
        try:
            self.estado.abrir(caminho)
        except profiles.ProfileError as erro:
            self.avisar(str(erro), erro=True)
            return
        self._grupo_aberto = None
        self._redesenhar()
        self.avisar(f"ABERTO: {Path(caminho).name}")

    def escolher_arquivo(self):
        escolhido = filedialog.askopenfilename(
            title="Abrir perfil",
            initialdir=self.estado.diretorio,
            filetypes=[("Perfis JSON", "*.json")],
        )
        if escolhido:
            self.abrir(Path(escolhido))

    def salvar(self):
        return self.salvar_como() if not self.estado.caminho else self._gravar(self.estado.caminho)

    def salvar_como(self):
        nome = self.estado.texto("name").strip() or "perfil"
        escolhido = filedialog.asksaveasfilename(
            title="Salvar perfil",
            initialdir=self.estado.diretorio,
            initialfile=f"{nome}.json",
            defaultextension=".json",
            filetypes=[("Perfis JSON", "*.json")],
        )
        return self._gravar(Path(escolhido)) if escolhido else None

    def _gravar(self, destino):
        try:
            salvo = self.estado.salvar(destino)
        except model.ErroDeCampo as erro:
            self._marcar(erro.caminho, erro.mensagem)
            return None
        except (controlador.EstadoSemDestino, profiles.ProfileError) as erro:
            messagebox.showerror("Nao deu para salvar", str(erro))
            return None

        self.limpar_erros()
        self.atualizar_lista()
        self.avisar(f"SALVO: {salvo.name}")
        return salvo

    def _marcar(self, caminho, mensagem):
        """Aponta o campo errado, e nao so a mensagem."""
        self.limpar_erros()
        linha = self.linhas.get(caminho)
        if linha:
            linha.marcar_erro(mensagem)
            self._revelar_grupo_de(caminho)
            linha.focar()
        self.avisar(f"{caminho}: {mensagem}", erro=True)

    def limpar_erros(self):
        for linha in self.linhas.values():
            linha.limpar_erro()

    # -- formulario ------------------------------------------------------

    def _ao_mudar(self, campo, texto):
        if self._reconstruindo:
            return
        mudou_contexto = self.estado.definir(campo, texto)
        if mudou_contexto:
            self._redesenhar()
        self._atualizar_titulo()

    def _redesenhar(self):
        self._reconstruindo = True
        # Solta os grupos antigos antes de derruba-los: se um aviso chegar
        # no meio da reconstrucao, ele nao pode achar um acordeao morto.
        self.grupos = {}
        try:
            for child in self.formulario.winfo_children():
                if hasattr(child, "parar"):
                    child.parar()
                child.destroy()
            self.linhas, self.grupos = montar_formulario(
                self.formulario,
                self.estado.campos,
                self._ao_mudar,
                aberto=self._grupo_aberto,
                ao_grupo=self._so_um,
            )
        finally:
            self._reconstruindo = False
            self._travando = False

        if self._grupo_aberto is None and self.grupos:
            self._grupo_aberto = next(iter(self.grupos))
        self._rolagem.reenquadrar()
        self._atualizar_titulo()

    def _so_um(self, acordeao):
        """So um grupo fica aberto: abrir um fecha o outro.

        A trava existe porque fechar tambem notifica, senao fechar o
        primeiro grupo dispararia este metodo de novo, no meio da varredura,
        sobre um conjunto pela metade. E durante a reconstrucao o aviso e
        ignorado de proposito: os grupos antigos ja foram destruidos, e
        chamar fechar() neles mexeria em widget morto.
        """
        if self._reconstruindo or self._travando:
            return
        self._travando = True
        try:
            for outro in self.grupos.values():
                if outro is not acordeao and outro.esta_aberto():
                    outro.fechar()
        finally:
            self._travando = False
        self._grupo_aberto = acordeao.identificador

    def _revelar_grupo_de(self, caminho):
        """Abre o grupo de um campo, para o erro aparecer na tela."""
        for grupo in self.grupos.values():
            if caminho in (linha.campo.caminho for linha in grupo.conteudo.winfo_children()):
                if not grupo.esta_aberto():
                    self._so_um(grupo)
                return

    def _atualizar_titulo(self):
        self.title(f"WolfsScreenHitter - {self.estado.rotulo()}")
        self.resumo.set(self.estado.resumo())

    def avisar(self, texto, erro=False):
        """A barra de status. O texto ja vem no caso que o autor quis."""
        self.mensagem.set(texto)
        self.status_label.configure(fg=tokens.VERMELHO if erro else tokens.PRETO)


class Rolagem(tk.Frame):
    """Rolagem do formulario: um canvas, uma barra e o botao do sistema.

    A barra e um ttk.Scrollbar, e nao um desenho nosso, porque ela precisa
    de thumb, track e das setas que o Windows ja resolve. E ela so carrega
    a geometria; a cor dela fica no tema, e nao e a identidade da tela.
    """

    def __init__(self, pai, conteudo):
        super().__init__(pai, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0)
        self.canvas = tk.Canvas(self, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0,
                                takefocus=0)
        self.barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.barra.set)

        self.barra.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self._janela = self.canvas.create_window((0, 0), window=conteudo, anchor="nw")
        conteudo.bind("<Configure>", lambda _e: self.reenquadrar())
        self.canvas.bind("<Configure>", self._enquadrar)
        self.canvas.bind("<MouseWheel>", self._rolar)

    def reenquadrar(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._enquadrar(None)

    def _enquadrar(self, evento):
        if evento:
            self.canvas.itemconfigure(self._janela, width=evento.width)

    def _rolar(self, evento):
        self.canvas.yview_scroll(-1 if evento.delta > 0 else 1, "units")


def main():
    Aplicacao().mainloop()
