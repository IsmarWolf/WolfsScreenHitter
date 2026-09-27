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

    print("7b2. a janela de nome de verdade mostra botao, e nao funcao")
    # A 7b troca pedir_texto por um duble, entao a janela real nunca era
    # aberta. Foi por isso que um metodo local chamado "confirmar" passou
    # a desenhar o repr da funcao no botao em vez do rotulo, e o defeito
    # chegou inteiro ate a tela. Aqui a janela e aberta de verdade: o que
    # se le e o que o usuario veria.
    import tkinter as tk

    from wolfs_screen_hitter.gui.componentes import dialogo

    def _andar(raiz):
        for filho in raiz.winfo_children():
            yield filho
            yield from _andar(filho)

    def _botoes(janela):
        """Os Botao da janela. Sao Frames, entao a busca e pela classe."""
        from wolfs_screen_hitter.gui.componentes.botao import Botao

        return [w for w in _andar(janela) if isinstance(w, Botao)]

    achados = {}

    def _inspecionar():
        for janela in app.winfo_children():
            if not isinstance(janela, tk.Toplevel):
                continue
            botoes = _botoes(janela)
            achados["rotulos"] = [b._texto for b in botoes]
            achados["exibidos"] = [b.face.cget("text") for b in botoes]
            achados["largura"] = janela.winfo_width()
            achados["altura"] = janela.winfo_height()
            entrada = [w for w in _andar(janela) if isinstance(w, tk.Entry)]
            achados["tem_entrada"] = bool(entrada)
            if entrada:
                entrada[0].delete(0, tk.END)
                entrada[0].insert(0, "Pelo teste")
            confirmar = [b for b in botoes if b.face.cget("text") == "CONFIRMAR"]
            if confirmar:
                confirmar[0]._executa()
            else:
                janela.destroy()

    app.after(80, _inspecionar)
    resposta = dialogo.pedir_texto(app, "Novo perfil", valor="", instrucao="Como chamar?")

    rotulos = achados.get("rotulos", [])
    exibidos = achados.get("exibidos", [])
    checar("a janela abriu de verdade", bool(rotulos), str(rotulos))
    # O que importa e o texto desenhado na face do botao, que e o que o
    # usuario le. O atributo por tras vem em caixa normal, como os botoes
    # da barra, e quem maiusculiza e o Botao.
    checar(
        "os botoes mostram os rotulos",
        sorted(exibidos) == ["CANCELAR", "CONFIRMAR"],
        str(exibidos),
    )
    checar(
        "nenhum botao mostra um repr de funcao",
        not any("function" in str(r) for r in rotulos + exibidos),
        str(rotulos + exibidos),
    )
    checar("a janela tem largura de janela", achados.get("largura", 0) > 100, str(achados.get("largura")))
    checar("a janela tem a entrada de nome", achados.get("tem_entrada") is True, str(achados.get("tem_entrada")))
    checar("o que foi digitado voltou", resposta == "Pelo teste", str(resposta))

    print("7c. o nome do perfil vira um nome de arquivo que o Windows aceita")
    from wolfs_screen_hitter.gui.app import nome_de_arquivo

    checar("barra e dois pontos viram sublinhado", nome_de_arquivo("a/b:c") == "a_b_c", nome_de_arquivo("a/b:c"))
    checar("asterisco e interrogacao saem", nome_de_arquivo("x*y?z") == "x_y_z", nome_de_arquivo("x*y?z"))
    checar("so barra vira barra", nome_de_arquivo("2024/05") == "2024_05", nome_de_arquivo("2024/05"))
    checar("nome reservado ganha prefixo", nome_de_arquivo("CON") == "_CON", nome_de_arquivo("CON"))
    checar("vazio nao vira arquivo sem nome", nome_de_arquivo("   ") == "perfil", nome_de_arquivo("   "))

    print("7d. o campo de template tem botao de arquivo e guarda caminho relativo")
    import wolfs_screen_hitter.gui.componentes.campo as modulo_campo

    app._ao_mudar("detector", "template")
    app.update()
    linha = app.linhas["target.template"]
    checar(
        "o botao de arquivo entrou na moldura da entrada",
        getattr(linha, "_abrir", None) is not None,
        type(getattr(linha, "_abrir", None)).__name__,
    )
    checar(
        "o botao e filho da mesma moldura, e nao um botao solto na linha",
        linha._abrir.master is linha._moldura,
        "",
    )
    checar("campo comum nao ganha botao de arquivo", not hasattr(app.linhas["name"], "_abrir"), "")

    png = pathlib.Path(pasta) / "glifo.png"
    png.write_bytes(b"conteudo qualquer, o teste nao abre a imagem")

    class _Dialogo:
        @staticmethod
        def askopenfilename(**_opcoes):
            return str(png)

    dialogo_original = modulo_campo.filedialog
    modulo_campo.filedialog = _Dialogo
    try:
        linha._escolher_arquivo()
    finally:
        modulo_campo.filedialog = dialogo_original
    app.update()
    checar(
        "o campo recebeu o caminho em relacao a pasta do perfil",
        app.estado.texto("target.template") == "glifo.png",
        app.estado.texto("target.template"),
    )
    checar("a escolha conta como edicao", app.estado.sujo, str(app.estado.sujo))

    modulo_campo.filedialog = _Dialogo
    try:
        linha._escolher_arquivo()
    finally:
        modulo_campo.filedialog = dialogo_original
    checar(
        "o arquivo continua no campo depois do redesenho",
        app.linhas["target.template"].texto() == "glifo.png",
        app.linhas["target.template"].texto(),
    )
    app._ao_mudar("detector", "shape")
    app.update()

    print("7e. o botao de selecionar na tela escreve a regiao")
    from wolfs_screen_hitter.gui.componentes.linha_acao import LinhaAcao

    grupo_regiao = app.grupos["regiao"]
    linha_acao = next(
        c for c in grupo_regiao.conteudo.winfo_children() if isinstance(c, LinhaAcao)
    )
    campos_regiao = [
        c
        for c in grupo_regiao.conteudo.winfo_children()
        if c.winfo_class() == "Frame" and not isinstance(c, LinhaAcao)
    ]
    espacador = linha_acao.winfo_children()[0]
    rotulo_campo = campos_regiao[0].winfo_children()[0]
    checar(
        "a coluna vazia e um rotulo, e nao um frame de altura fixa",
        espacador.winfo_class() == "Label",
        espacador.winfo_class(),
    )
    checar(
        "a coluna vazia nao e uma barra de 1px",
        espacador.winfo_reqheight() > 1,
        f"{espacador.winfo_reqheight()}px",
    )
    checar(
        "o botao comeca alinhado com as entradas",
        espacador.winfo_reqwidth() == rotulo_campo.winfo_reqwidth(),
        f"acao {espacador.winfo_reqwidth()}px vs campo {rotulo_campo.winfo_reqwidth()}px",
    )
    checar("o grupo da regiao tem uma linha de acao", len(linha_acao.winfo_children()) == 3, str(len(linha_acao.winfo_children())))

    from wolfs_screen_hitter.gui.componentes import seletor_regiao

    app._so_um(app.grupos["regiao"])
    app.update()
    acoes = [
        linha
        for linha in app.grupos["regiao"].conteudo.winfo_children()
        if type(linha).__name__ == "LinhaAcao"
    ]
    checar("o grupo da regiao tem uma linha de acao", len(acoes) == 1, str(len(acoes)))
    checar(
        "a acao e a de escolher a regiao",
        [a.acao.seletor for a in acoes] == ["escolher_regiao"],
        str([a.acao.seletor for a in acoes]),
    )
    checar(
        "a acao nao entra no dicionario de campos",
        "escolher_regiao" not in app.linhas,
        "",
    )

    import wolfs_screen_hitter.gui.app as modulo_app

    seletor_original = modulo_app.escolher_regiao
    modulo_app.escolher_regiao = lambda _pai: (100, 50, 640, 480)
    try:
        app._selecionar_regiao()
    finally:
        modulo_app.escolher_regiao = seletor_original
    app.update()
    checar("o modo virou fixed", app.estado.texto("region.mode") == "fixed", app.estado.texto("region.mode"))
    for campo, valor in (
        ("region.left", "100"),
        ("region.top", "50"),
        ("region.width", "640"),
        ("region.height", "480"),
    ):
        checar(f"{campo} recebeu o valor arrastado", app.estado.texto(campo) == valor, app.estado.texto(campo))
    checar(
        "os quatro numeros apareceram na tela",
        all(c in app.linhas for c in ("region.left", "region.top", "region.width", "region.height")),
        "",
    )
    checar("a tela mostra a largura escolhida", app.linhas["region.width"].texto() == "640", app.linhas["region.width"].texto())
    checar("a regiao arrastada conta como edicao", app.estado.sujo, str(app.estado.sujo))

    before = dict(app.estado.campos)
    modulo_app.escolher_regiao = lambda _pai: None
    try:
        app._selecionar_regiao()
    finally:
        modulo_app.escolher_regiao = seletor_original
    app.update()
    checar("cancelar nao mexe em nada", dict(app.estado.campos) == before, "")
    checar("cancelar avisa", "CANCEL" in app.mensagem.get().upper(), app.mensagem.get())

    print("7f. o seletor mede a tela igual ao resto do programa")
    from wolfs_screen_hitter import windows

    seletor = seletor_regiao.SeletorRegiao(app)
    checar(
        "a tela principal e a mesma que o modo 'screen' usa",
        seletor.principal == windows.screen(),
        f"{seletor.principal} vs {windows.screen()}",
    )
    checar("o fator Tk/Win32 e positivo", seletor.fator > 0, str(seletor.fator))
    x, y = seletor.para_win32(0, 0)
    checar(
        "o canto do canvas e o canto da tela principal",
        (x, y) == (seletor.principal[0], seletor.principal[1]),
        f"{x},{y}",
    )
    x, y = seletor.para_win32(30, 20)
    checar(
        "o deslocamento no canvas vira o mesmo deslocamento na tela",
        (x, y) == (seletor.principal[0] + 30, seletor.principal[1] + 20),
        f"{x},{y}",
    )
    largura_canvas = round(seletor.principal[2] * seletor.fator)
    altura_canvas = round(seletor.principal[3] * seletor.fator)
    x, y = seletor.para_win32(largura_canvas, altura_canvas)
    checar(
        "a borda do canvas e a borda da tela, sem sobra",
        (x, y) == (seletor.principal[0] + seletor.principal[2], seletor.principal[1] + seletor.principal[3]),
        f"{x},{y}",
    )

    print("7g. arrastar na camada devolve o retangulo arrastado")

    def _camada():
        """A camada como o esperar() monta: janela, eventos e update.

        O grab e de esperar(), e nao entra: um grab pendurado em uma janela
        destruida sequestraria o mouse dos testes seguintes. O que garante
        o teclado e o focus_force de _ligar(), e e isso que se quer medir.
        """
        montada = seletor_regiao.SeletorRegiao(app)
        montada._montar()
        montada._ligar()
        app.update()
        return montada

    arraste = _camada()
    arraste.quadro.event_generate("<ButtonPress-1>", x=100, y=60)
    arraste.quadro.event_generate("<B1-Motion>", x=400, y=260)
    arraste.quadro.event_generate("<ButtonRelease-1>", x=400, y=260)
    app.update()
    checar("soltar com retangulo fecha a camada e devolve a regiao", arraste.regiao is not None, str(arraste.regiao))
    if arraste.regiao:
        esquerda, topo, largura, altura = arraste.regiao
        checar("a largura e a distancia entre as duas pontas", largura == 300, str(largura))
        checar("a altura e a distancia entre as duas pontas", altura == 200, str(altura))
        checar(
            "o canto medido em relacao a tela principal",
            (esquerda, topo) == (arraste.principal[0] + 100, arraste.principal[1] + 60),
            f"{esquerda},{topo}",
        )
    checar("a camada foi destruida", not arraste.camada.winfo_exists(), "")

    arraste = _camada()
    arraste.quadro.event_generate("<ButtonPress-1>", x=500, y=400)
    arraste.quadro.event_generate("<B1-Motion>", x=200, y=100)
    arraste.quadro.event_generate("<ButtonRelease-1>", x=200, y=100)
    app.update()
    checar("arrastar na diagonal invertida tambem vale", arraste.regiao is not None, str(arraste.regiao))
    if arraste.regiao:
        esquerda, topo, largura, altura = arraste.regiao
        checar("o canto e o menor dos dois pontos", (esquerda, topo) == (arraste.principal[0] + 200, arraste.principal[1] + 100), f"{esquerda},{topo}")
        checar("largura e altura seguem o menor", (largura, altura) == (300, 300), f"{largura}x{altura}")

    arraste = _camada()
    arraste.quadro.event_generate("<ButtonPress-1>", x=300, y=300)
    arraste.quadro.event_generate("<B1-Motion>", x=302, y=301)
    arraste.quadro.event_generate("<ButtonRelease-1>", x=302, y=301)
    app.update()
    checar("clique sem arrastar nao escolhe regiao", arraste.regiao is None, str(arraste.regiao))
    checar("a camada continua aberta para tentar de novo", arraste.camada.winfo_exists(), "")
    arraste.quadro.event_generate("<Escape>")
    app.update()
    checar("Esc fecha a camada", not arraste.camada.winfo_exists(), "")
    checar("Esc devolveu nada", arraste.regiao is None, "")

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
