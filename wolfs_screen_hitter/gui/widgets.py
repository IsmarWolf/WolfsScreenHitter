"""Monta o formulario a partir do modelo, um acordeao por grupo.

O modelo diz quais grupos existem, em que ordem, e quais campos aparecem em
cada um conforme o contexto. Aqui isso vira uma arvore de Acordeao, e cada
campo vira uma LinhaCampo. Nada aqui decide o que e um perfil valido.

Dois detalhes de comportamento moram aqui e nao no modelo, porque sao da
tela e nao do perfil:

Um grupo nasce fechado, menos o primeiro. Com tudo aberto a janela
comeca parecendo um formulario gigante em vez de uma lista de coisas para
abrir.

E o grupo aberto continua aberto depois de um redesenho. Trocar o detector
reconstroi a arvore inteira, e esquecer qual estava aberto faria a tela
pular a cada clique.
"""

from . import model
from .componentes import Acordeao, LinhaCampo
from .componentes.linha_acao import LinhaAcao
from .design import tokens

_RESPIRO = tokens.px(tokens.ESPACO_1) // 2


def montar_formulario(quadro, campos, ao_mudar, aberto=None, ao_grupo=None, pasta="", acoes=None,
                      nivel=None):
    """Desenha os grupos visiveis e devolve (linhas, acordeoes).

    Recebe o dicionario achatado que a janela mantem, e nao o perfil
    aninhado: assim a tela mostra exatamente o que esta em edicao, sem
    passar por uma conversao que poderia esconder um valor.

    pasta e onde o perfil esta. Serve para os seletores de arquivo abrirem
    o dialogo no lugar certo, e nada mais: quem escolhe o arquivo continua
    sendo o usuario.

    acoes mapeia o seletor de um botao para o comando da janela. Um botao
    cujo seletor nao esta no dicionario nao e desenhado, e nao e erro: quem
    chamador nao sabe fazer aquilo e prefere um grupo sem o botao a um
    botao quebrado.

    nivel escolhe a aba: "basico" desenha o que se responde sem pensar,
    "avancado" desenha os numeros de ajuste, None desenha tudo. E um filtro
    de desenho e nada mais -- quem grava le os dois niveis, senao trocar de
    aba apagaria o que estava na outra.
    """
    acoes = acoes or {}
    contexto = model.contexto_dos_campos(campos)
    visiveis = model.visiveis(campos, nivel, contexto)
    linhas = {}
    grupos = {}
    primeiro = True

    for identificador, titulo, _condicao, _grupo in model.GRUPOS:
        if identificador not in visiveis:
            continue
        _titulo, grupo = visiveis[identificador]

        acordeao = Acordeao(quadro, identificador, titulo, ao_mudar=ao_grupo)
        acordeao.pack(fill="x", pady=(0, tokens.px(tokens.ESPACO_2)))
        grupos[identificador] = acordeao

        for acao in model.ACOES.get(identificador, ()):
            if nivel is not None and acao.nivel != nivel:
                continue
            comando = acoes.get(acao.seletor)
            if comando is None:
                continue
            LinhaAcao(acordeao.conteudo, acao, comando).pack(
                fill="x", pady=_RESPIRO
            )

        for campo in grupo:
            linha = LinhaCampo(
                acordeao.conteudo,
                campo,
                campos.get(campo.caminho, ""),
                ao_mudar,
                pasta=pasta,
            )
            linha.pack(fill="x", pady=_RESPIRO)
            linhas[campo.caminho] = linha

        # O primeiro grupo desenhado nasce aberto, seja qual for. Fixar um
        # identificador quebrava com as duas abas: o grupo "Perfil" so tem
        # campo basico, entao na aba de ajustes ele nem existe, e a aba
        # inteira abria fechada.
        if aberto is not None and identificador == aberto:
            acordeao.abrir(animado=False)
        elif aberto is None and primeiro:
            acordeao.abrir(animado=False)
        primeiro = False

    return linhas, grupos
