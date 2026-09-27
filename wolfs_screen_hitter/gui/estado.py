"""Estado do formulario: o que esta aberto, o que mudou, o que salvar.

Fica separado da interface de proposito. A janela so desenha e avisa quando
o contexto muda; quem decide o que acontece com o perfil e este modulo, e
ele nao importa tkinter, entao da para testar o ciclo inteiro sem abrir
nenhuma janela.
"""

from pathlib import Path

from .. import profiles
from . import model


class EstadoSemDestino(ValueError):
    """O perfil nao tem onde ser gravado ainda."""


class Estado:
    """O perfil em edicao, os caminhos disponiveis e se ha mudanca salva."""

    def __init__(self, diretorio=None):
        self.diretorio = Path(diretorio) if diretorio else profiles.DEFAULT_PROFILE_DIR
        self.caminho = None
        self.campos = {}
        self.sujo = False
        self.novo()

    # -- inventario ------------------------------------------------------

    def listar(self):
        """Os perfis do diretorio, ja ordenados."""
        return profiles.list_profiles(self.diretorio)

    def existe(self, caminho):
        return Path(caminho) in self.listar()

    # -- ciclo do perfil --------------------------------------------------

    def novo(self):
        """Comeca um perfil em branco, sem caminho de destino.

        Nasce limpo: um perfil novo ainda nao e trabalho do usuario, entao
        nao faz sentido pedir para confirmar descarte ao sair dele.
        """
        self.caminho = None
        self.campos = model.perfil_para_campos(model.perfil_padrao())
        self.sujo = False

    def abrir(self, caminho):
        """Le um perfil do disco e preenche os campos."""
        carregado = profiles.load(caminho)
        self.caminho = Path(caminho)
        self.campos = model.perfil_para_campos(
            {k: v for k, v in carregado.items() if not k.startswith("_")}
        )
        self.sujo = False

    def salvar(self, caminho=None):
        """Grava o formulario em disco e volta a ser o perfil aberto.

        Levanta model.ErroDeCampo com o caminho do campo errado, para a
        janela poder marcar a entrada, e profiles.ProfileError quando o
        perfil e invalido por um motivo que nao e um campo.
        """
        destino = Path(caminho) if caminho else self.caminho

        if not destino:
            raise EstadoSemDestino(
                "Esse perfil ainda nao tem nome. Use Salvar como para escolher onde ele vai."
            )

        perfil = model.campos_para_perfil(self.campos)
        profiles.save(perfil, destino)

        self.caminho = destino
        self.sujo = False
        return destino

    # -- edicao ----------------------------------------------------------

    def definir(self, campo, texto):
        """Guarda o que o usuario digitou e diz se o contexto mudou.

        O contexto mudar e o que faz a janela redesenhar o formulario: e
        por isso que o seletor de detector e o de regiao mudam a tela
        inteira, e nao so o proprio campo.
        """
        antes = model.contexto_dos_campos(self.campos)
        self.campos[campo] = texto
        depois = model.contexto_dos_campos(self.campos)
        self.sujo = True
        return antes != depois

    def texto(self, campo):
        return self.campos.get(campo, "")

    def rotulo(self):
        """Nome do perfil aberto, para o titulo da janela."""
        if not self.caminho:
            return "perfil sem nome" + (" *" if self.sujo else "")
        return self.caminho.name + (" *" if self.sujo else "")

    def resumo(self):
        """Linha curta de estado, para a barra de cima.

        So o nome do arquivo. A pasta tambem e o diretorio de todos os
        perfis, e por isso ela ja esta no unico lugar onde muda: o seletor
        de perfil, que abre em cima dela. Repetir o caminho inteiro na
        barra empurrava o botao de fechar para fora da janela e nao
        acrescentava informacao nenhuma.
        """
        if not self.caminho:
            return "perfil novo, sem nome"
        return self.caminho.name
