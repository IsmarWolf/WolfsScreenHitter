"""Janela do WolfsScreenHitter, no design system Bauhaus.

Nesta etapa a janela faz o ciclo do perfil: listar, abrir, criar, editar e
salvar. O que e valido continua sendo decidido pelo modelo, entao o que
esta na tela e o mesmo que a CLI le.

Sobre a escolha dos widgets: o cabecalho, a faixa de acoes e o rodape sao
Canvas e Frame com cor, e nao ttk. O motivo e medido, nao moda: no Windows
com o tema vista ativo, o ttk ignora cor de fundo, borda e relevo, e o
resultado e um formulario cinza que nao pertence a esta tela. As entradas
de texto continuam nativas, porque quem traz selecao, clipboard, caret e
atalhos e o Entry, e refazer isso seria refazer o editor de texto do
sistema.

A estrutura e de cima para baixo: cabecalho azul com a assinatura, depois a
faixa com o perfil aberto e as acoes, depois o formulario em acordao
ocupando a largura toda, e no pe a barra de status amarela sobre o rodape
preto. Nao ha coluna lateral: todo perfil ja nasce gravado e com nome, a
escolha entre eles cabe em um dropdown, e a coluna inteira seria largura
gasta para repetir essa escolha.
"""

import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .. import profiles
from . import estado as controlador
from . import model
from .componentes import Botao, Divisor
from .componentes.dialogo import pedir_texto
from .componentes.seletor import SeletorPerfil
from .componentes.seletor_regiao import escolher_regiao
from .design import formas, tokens, tipografia
from .widgets import montar_formulario

_LARGURA = 1160
_ALTURA = 720
_SELETOR = 260

# A ordem dos quatro numeros de uma regiao e a ordem de resolve_region, e
# tambem a ordem que o seletor devolve.
_CAMPOS_DE_REGIAO = ("region.left", "region.top", "region.width", "region.height")


# O que o Windows aceita em nome de arquivo, e o que o perfil vai ter que
# sobreviver dentro. Tudo que nao for letra, numero, ponto, hifen ou
# sublinhado vira sublinhado, porque o campo name vai para o cabecalho do
# perfil e para o nome do arquivo ao mesmo tempo.
_INVALIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVADOS = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def nome_de_arquivo(nome):
    """Um nome de perfil vira um nome de arquivo sem perder o que da para
    ler, e sem o Windows recusar depois."""
    limpo = _INVALIDOS.sub("_", nome).strip().strip(".")
    limpo = limpo[:96]
    if not limpo:
        return "perfil"
    if limpo.lower() in _RESERVADOS:
        limpo = f"_{limpo}"
    return limpo


class Aplicacao(tk.Tk):
    def __init__(self, diretorio=None):
        # A fonte tem de estar registrada antes de existir a janela: o Tk so
        # enxerga o que o Windows ja informa quando a raiz e criada.
        tipografia.registrar_fonte_embutida()
        super().__init__()

        tokens.configurar_escala(self)
        tipografia.carregar(self)

        self.geometry(f"{tokens.px(_LARGURA)}x{tokens.px(_ALTURA)}")
        self.minsize(tokens.px(880), tokens.px(tokens.ESPACO_8 * 18))
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
        self._travando = False

        self.mensagem = tk.StringVar()
        self.resumo = tk.StringVar()
        self._montar()
        self.atualizar_lista()

        # O formulario nasce antes de tentar abrir qualquer coisa. Se o
        # primeiro perfil da pasta estiver corrompido, abrir() so avisa e
        # devolve, e sem esta linha a tela ficaria sem um unico campo.
        self.novo(silencioso=True)
        if self.caminhos:
            self.abrir(self.caminhos[0])

        self._atualizar_titulo()

    # -- layout ----------------------------------------------------------

    def _montar(self):
        self._montar_cabecalho()
        self._montar_acoes()
        self._montar_formulario_cheio()
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

        # O perfil aberto vem antes dos botoes: e ele que diz o que os botoes
        # vao mexer. Um "Salvar" sem saber em qual arquivo se salva e a
        # duvida que fica, e ela nao precisa existir.
        # O botao "Atualizar" foi embora. Todo campo ja grava ao perder o
        # foco, o perfil ja nasce gravado e a lista e relida no instante em
        # que o seletor abre, entao nao sobrava nada para ele mudar: ele so
        # ocupava espaco na barra e dava a ideia de que algo precisava
        # ser atualizado a mao.
        self.seletor = SeletorPerfil(
            barra, self._abrir_da_lista, ao_abrir=self.atualizar_lista, largura=_SELETOR
        )
        self.seletor.pack(side="left")

        tk.Frame(barra, bg=tokens.CINZA, width=tokens.px(tokens.BORDA_GROSSA)).pack(
            side="left", fill="y", padx=tokens.px(tokens.ESPACO_3)
        )

        acoes = (
            ("Novo", self.novo, "primario"),
            ("Abrir", self.escolher_arquivo, "secundario"),
            ("Salvar", self.salvar, "amarelo"),
            ("Salvar como", self.salvar_como, "contorno"),
        )
        for rotulo, comando, variante in acoes:
            Botao(barra, rotulo, comando, variante=variante).pack(
                side="left", padx=(0, tokens.px(tokens.ESPACO_1))
            )

        tk.Label(
            barra,
            textvariable=self.resumo,
            font=tipografia.fonte("label"),
            bg=tokens.BG_CANVAS,
            fg=tokens.PRETO,
            anchor="e",
        ).pack(side="right", fill="x", expand=True, padx=(tokens.px(tokens.ESPACO_3), 0))

    def _montar_formulario_cheio(self):
        """O formulario ocupa a largura toda, dentro de um canvas com rolagem
        porque um grupo aberto pode ser mais alto que a janela."""
        Divisor(self).pack(fill="x")
        self.formulario = tk.Frame(self, bg=tokens.BG_CANVAS, bd=0, highlightthickness=0)
        self._rolagem = Rolagem(self, self.formulario)
        self._rolagem.pack(fill="both", expand=True, padx=tokens.px(tokens.ESPACO_4),
                           pady=tokens.px(tokens.ESPACO_4))

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
        self.seletor.definir_itens(self.caminhos)
        self.seletor.definir_perfil(anterior, self.estado.sujo)

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

    def novo(self, silencioso=False):
        """Perfil novo com nome e ja gravado.

        A regra mudou com o pedido da tela: um perfil so existe depois de ter
        nome e arquivo. Antes, "Novo" deixava um formulario solto e o
        trabalho de dar nome a ele vinha no "Salvar como", num dialogo do
        sistema. Agora o nome e pedido logo no comeco, em uma janela da
        propria tela, e o arquivo nasce junto -- o que faz a lista de
        perfis nunca mostrar item sem nome, e faz "Novo" deixar a tela num
        estado em que ja da para salvar sem pensar em nome de arquivo.

        O cancelamento nao perde nada: volta para o perfil que estava
        aberto, ou para um formulario em branco se nao havia nenhum.
        """
        anterior = self.estado.caminho
        self.estado.novo()

        if silencioso:
            self._grupo_aberto = None
            self._redesenhar()
            return None

        nome = pedir_texto(
            self,
            "Novo perfil",
            valor=self._nome_livre(),
            instrucao="O nome vira o nome do arquivo. Da para trocar depois, em Salvar como.",
        )
        if nome is None:
            return self._voltar_para(anterior)

        destino = self._destino_de(nome)
        if destino is None:
            return self._voltar_para(anterior)

        self.estado.campos["name"] = nome
        self._grupo_aberto = None
        self._redesenhar()
        return self._gravar(destino, recado=f"CRIADO: {nome}")

    def _voltar_para(self, caminho):
        """Desfaz um "Novo" cancelado."""
        if caminho and caminho.exists():
            return self.abrir(caminho)
        return self.novo(silencioso=True)

    def _nome_livre(self):
        """Um nome sugerido que ainda nao existe na pasta."""
        base = "perfil"
        if not (self.estado.diretorio / f"{base}.json").exists():
            return base
        numero = 2
        while (self.estado.diretorio / f"{base} {numero}.json").exists():
            numero += 1
        return f"{base} {numero}"

    def _destino_de(self, nome):
        """O caminho que o perfil novo vai ter, ou None se o usuario nao
        quiser substituir um arquivo que ja existe."""
        destino = self.estado.diretorio / f"{nome_de_arquivo(nome)}.json"
        if destino.exists() and not messagebox.askyesno(
            "Esse perfil ja existe",
            f"Ja existe {destino.name} na pasta de perfis.\n\nSubstituir esse arquivo?",
        ):
            return None
        return destino

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

    def _gravar(self, destino, recado=None):
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
        self.avisar(recado or f"SALVO: {salvo.name}")
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

    def _comandos_de_seletor(self):
        """O que cada botao de seletor do formulario faz.

        Montado como dicionario, e nao espalhado em if dentro da montagem,
        porque quem desenha o botao nao deveria saber o que ele faz: ele so
        precisa de um comando para o seletor declarado no modelo.
        """
        return {"escolher_regiao": self._selecionar_regiao}

    def _selecionar_regiao(self):
        """Pede a area na tela e escreve os quatro numeros da regiao.

        Arrastar a regiao define tambem o modo: quem acabou de escolher um
        retangulo quer "fixed", e nao "screen" ou "janela". Deixar o modo
        como estava faria os quatro numeros aparecerem na tela e nao serem
        usados, que e a pior das duas metades.
        """
        regiao = escolher_regiao(self)
        if regiao is None:
            self.avisar("SELECAO CANCELADA. A REGIAO FICOU COMO ESTAVA.")
            return

        for caminho, valor in zip(_CAMPOS_DE_REGIAO, regiao):
            self.estado.definir(caminho, str(valor))
        self.estado.definir("region.mode", "fixed")
        self._grupo_aberto = "regiao"
        self._redesenhar()
        esquerda, topo, largura, altura = regiao
        self.avisar(f"REGIAO {largura} x {altura} EM ({esquerda}, {topo})")

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
                pasta=str(self.estado.diretorio),
                acoes=self._comandos_de_seletor(),
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
        """Abre o grupo de um campo, para o erro aparecer na tela.

        Nem toda linha do grupo e um campo: o botao de seletor tambem mora
        ali dentro, e nao tem campo nenhum.
        """
        for grupo in self.grupos.values():
            caminhos = (
                linha.campo.caminho
                for linha in grupo.conteudo.winfo_children()
                if getattr(linha, "campo", None) is not None
            )
            if caminho in caminhos:
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
