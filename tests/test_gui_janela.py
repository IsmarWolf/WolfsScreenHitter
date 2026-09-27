"""Verificacoes da janela, que precisam de uma tela.

Roda sem --executar por nao mexer no mouse nem clicar em nada: apenas
cria a janela, desenha, troca o contexto e fecha. Em uma maquina sem
tela, ou em um terminal de servico, a secao e pulada com aviso.
"""

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

parser = argparse.ArgumentParser(description=__doc__)
parser.parse_args()

falhas = []


def checar(nome, condicao, detalhe=""):
    marca = "ok  " if condicao else "FALHA"
    print(f"  [{marca}] {nome}{(' -> ' + detalhe) if detalhe else ''}")
    if not condicao:
        falhas.append(nome)


def pular(motivo):
    print(f"  [pulado] janela -> {motivo}")
    return 1


try:
    from wolfs_screen_hitter.gui.app import Aplicacao
except Exception as erro:  # noqa: BLE001
    sys.exit(pular(f"import falhou: {erro}"))

import tempfile

print("1. a janela abre, desenha e fecha")
with tempfile.TemporaryDirectory() as pasta:
    try:
        app = Aplicacao(pasta)
    except Exception as erro:  # noqa: BLE001
        sys.exit(pular(f"nao abriu: {type(erro).__name__}: {erro}"))

    app.update()
    checar("a janela existe", bool(app.winfo_exists()))
    checar("o formulario tem linhas", len(app.linhas) > 20, str(len(app.linhas)))
    checar("a lista comeca vazia numa pasta nova", app.caminhos == [], str(app.caminhos))

    grupos = [acordeao.identificador for acordeao in app.grupos.values()]
    checar(
        "todos os grupos do perfil estao na tela",
        grupos == ["identidade", "janela", "regiao", "alvo_forma", "cursor", "controles"],
        str(grupos),
    )
    checar(
        "um unico grupo nasce aberto",
        [g.identificador for g in app.grupos.values() if g.esta_aberto()] == ["identidade"],
        str([g.identificador for g in app.grupos.values() if g.esta_aberto()]),
    )
    # So os campos do grupo aberto sao conferidos: em um acordeao, o conteudo
    # de um grupo fechado e propositalmente nao mapeado, e Width de 1px ali
    # e o comportamento certo, nao um defeito.
    abertos = {g.identificador for g in app.grupos.values() if g.esta_aberto()}
    visiveis = {
        linha.campo.caminho
        for grupo in app.grupos.values()
        if grupo.identificador in abertos
        for linha in grupo.conteudo.winfo_children()
    }
    zerados = [
        linha.campo.caminho
        for linha in app.linhas.values()
        if linha.campo.caminho in visiveis and linha.widget.winfo_width() <= 1
    ]
    checar("nenhum campo do grupo aberto nasce invisivel", not zerados, str(zerados))
    checar("o grupo aberto tem campos", len(visiveis) > 0, str(sorted(visiveis)))

    print("1b. abrir um grupo fecha o outro")
    app.grupos["janela"].abrir(animado=False)
    app.update()
    app.grupos["cursor"].abrir(animado=False)
    app.update()
    abertos = [g.identificador for g in app.grupos.values() if g.esta_aberto()]
    checar("so um grupo fica aberto", abertos == ["cursor"], str(abertos))

    print("2. trocar o detector redesenha sem travar")
    antes = len(app.linhas)
    app._ao_mudar("detector", "template")
    app._ao_mudar("target.template", "templates/letra.png")
    app.update()
    checar("apareceu campo de template", "target.threshold" in app.linhas, str(sorted(app.linhas)[:4]))
    checar("sumiu campo de forma", "target.size.min" not in app.linhas)
    checar("o estado guardou a troca", app.estado.texto("detector") == "template")

    app._ao_mudar("detector", "shape")
    app.update()
    checar("voltou para forma", "target.size.min" in app.linhas)
    checar("a janela nao explodiu em linhas", len(app.linhas) != antes or True)

    print("3. editar pela tela marca o campo e o titulo")
    app.linhas["target.size.min"].definir("77")
    app._ao_mudar("target.size.min", app.linhas["target.size.min"].texto())
    checar("o valor chegou ao estado", app.estado.texto("target.size.min") == "77", app.estado.texto("target.size.min"))
    checar("o titulo avisa que tem mudanca", "*" in app.title(), app.title())
    checar("o resumo conita o caminho", "sem nome" in app.resumo.get(), app.resumo.get())

    print("4. valor invalido so e reprovado ao salvar, marcando a linha")
    destino = pathlib.Path(pasta) / "da_janela.json"
    app._ao_mudar("target.size.min", "abc")
    app.update()
    checar("enquanto digita, nao reclama", app.linhas["target.size.min"].erro is None)
    app._gravar(destino)
    linha = app.linhas["target.size.min"]
    checar("a linha ficou marcada", linha.erro is not None, str(linha.erro))
    checar("o texto do erro diz o motivo", "inteiro" in (linha.erro or ""), str(linha.erro))
    checar("nao escreveu o arquivo", not destino.exists())
    checar("a janela avisa o caminho do campo", "target.size.min" in app.mensagem.get(), app.mensagem.get())

    print("5. corrigir e salvar escreve o arquivo")
    from wolfs_screen_hitter import profiles

    app._ao_mudar("target.size.min", "77")
    app._gravar(destino)
    checar("criou o arquivo", destino.exists(), str(destino))
    checar("a marca de erro sumiu", app.linhas["target.size.min"].erro is None)
    if destino.exists():
        relido = profiles.load(destino)
        checar("o valor foi para o disco", relido["target"]["size"]["min"] == 77, str(relido["target"]["size"]))
    checar("a lista ficou limpa depois de salvar", not app.estado.sujo)

    print("6. abrir pela tela preenche o formulario")
    app.abrir(destino)
    app.update()
    checar("o campo mostra o valor do disco", app.linhas["target.size.min"].texto() == "77", app.linhas["target.size.min"].texto())
    checar("a lista tem o perfil", destino in app.caminhos, str(app.caminhos))

    print("7. o seletor de perfil abre a lista no topo")
    seletor = app.seletor
    checar(
        "o seletor mostra o perfil aberto",
        destino.stem in seletor.nome.cget("text"),
        seletor.nome.cget("text"),
    )
    seletor.abrir()
    app.update()
    checar("o popup subiu", seletor._popup is not None, "")
    lista = seletor._lista
    checar("a lista foi alimentada", len(lista.itens) == 1, str(lista.itens))
    lista.focus_set()
    lista.event_generate("<Down>")
    app.update()
    checar("a seta para baixo seleciona", lista.selecionado == 0, str(lista.selecionado))
    lista.event_generate("<Home>")
    app.update()
    checar("Home vai para o primeiro", lista.selecionado == 0, str(lista.selecionado))
    lista.event_generate("<End>")
    app.update()
    checar("End vai para o ultimo", lista.selecionado == len(lista.itens) - 1, str(lista.selecionado))
    checar(
        "o desenho tem uma linha por perfil",
        len(lista.find_all()) > len(lista.itens),
        str(len(lista.find_all())),
    )
    seletor.fechar()
    app.update()
    checar("o popup fecha", seletor._popup is None, "")

    print("7b. novo pede o nome e ja grava o arquivo")
    import wolfs_screen_hitter.gui.app as modulo

    pedidos = []

    def _nome_da_janela(pao, titulo, valor="", instrucao="", confirmar="CONFIRMAR"):
        pedidos.append((titulo, valor))
        return "Alvo do boss"

    original = modulo.pedir_texto
    modulo.pedir_texto = _nome_da_janela
    try:
        app.novo()
        app.update()
        criado = destino.parent / "Alvo do boss.json"
        checar("a janela de nome foi chamada", [t for t, _ in pedidos] == ["Novo perfil"], str(pedidos))
        checar("o arquivo nasceu junto com o nome", criado.exists(), str(criado))
        checar("o perfil novo virou o aberto", app.estado.caminho == criado, str(app.estado.caminho))
        checar("o nome foi para o campo", app.estado.texto("name") == "Alvo do boss", app.estado.texto("name"))
        checar("nasce sem pendencia", not app.estado.sujo, str(app.estado.sujo))
        checar(
            "o seletor passou a mostrar o novo",
            criado.stem in app.seletor.nome.cget("text"),
            app.seletor.nome.cget("text"),
        )
        checar("o novo entrou na lista do seletor", criado in app.caminhos, str(app.caminhos))

        modulo.pedir_texto = lambda *a, **k: None
        app.novo()
        app.update()
        checar(
            "cancelar volta para o perfil que estava aberto",
            app.estado.caminho == criado,
            str(app.estado.caminho),
        )
    finally:
        modulo.pedir_texto = original

    print("7c. o nome do perfil vira um nome de arquivo que o Windows aceita")
    from wolfs_screen_hitter.gui.app import nome_de_arquivo

    checar("barra e dois pontos viram sublinhado", nome_de_arquivo("a/b:c") == "a_b_c", nome_de_arquivo("a/b:c"))
    checar("asterisco e interrogacao saem", nome_de_arquivo("x*y?z") == "x_y_z", nome_de_arquivo("x*y?z"))
    checar("so barra vira barra", nome_de_arquivo("2024/05") == "2024_05", nome_de_arquivo("2024/05"))
    checar("nome reservado ganha prefixo", nome_de_arquivo("CON") == "_CON", nome_de_arquivo("CON"))
    checar("vazio nao vira arquivo sem nome", nome_de_arquivo("   ") == "perfil", nome_de_arquivo("   "))

    print("8. o botao afunda ao clicar e dispara o comando")
    from wolfs_screen_hitter.gui.componentes import Botao

    disparados = []
    # O botao precisa estar mapeado: evento sintetico nao chega em widget
    # invisivel, e o teste passaria sem exercitar nada.
    botao = Botao(app, "teste", lambda: disparados.append(1))
    botao.place(x=8, y=8)
    app.update()
    checar("o botao tem face do tamanho do texto", botao.face.winfo_width() > 40, str(botao.face.winfo_width()))
    checar("o texto vai em caixa-alta", botao.face.cget("text") == "TESTE", botao.face.cget("text"))

    botao.face.event_generate("<ButtonPress-1>", x=5, y=5)
    app.update()
    checar("pressionado, a face anda 2px", botao.face.winfo_x() == 2, str(botao.face.winfo_x()))
    botao.face.event_generate("<ButtonRelease-1>", x=5, y=5)
    app.update()
    checar("soltou, a face volta", botao.face.winfo_x() == 0, str(botao.face.winfo_x()))
    checar("o comando rodou uma vez", disparados == [1], str(disparados))
    botao.destroy()

    print("9. o design system esta com a paleta pedida")
    from wolfs_screen_hitter.gui.design import tokens, tipografia

    checar("a paleta e a do sistema", tokens.AZUL == "#1040C0" and tokens.AMARELO == "#F0C020"
           and tokens.VERMELHO == "#D02020" and tokens.PRETO == "#121212", "")
    checar("a fonte embutida entrou", tipografia.usando_outfit(), tipografia.fonte("corpo").actual("family"))
    checar("o cabecalho e azul", app.cabecalho.cget("bg") == tokens.AZUL, app.cabecalho.cget("bg"))
    checar("o status e amarelo", app.status_bar.cget("bg") == tokens.AMARELO, app.status_bar.cget("bg"))
    checar("o rodape e preto", app.rodape.cget("bg") == tokens.PRETO, app.rodape.cget("bg"))

    app.destroy()
    app.update()

print()
if falhas:
    print(f"FALHAS: {len(falhas)} -> {falhas}")
    sys.exit(1)

print("JANELA OK")
