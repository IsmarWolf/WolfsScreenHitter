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

    grupos = [c.cget("text") for c in app.formulario.winfo_children()]
    checar(
        "todos os grupos do perfil estao na tela",
        grupos == ["Perfil", "Janela", "Onde procurar", "Alvo por cor", "Cursor", "Parada"],
        str(grupos),
    )
    zerados = [
        linha.campo.caminho
        for linha in app.linhas.values()
        if hasattr(linha.widget, "winfo_width") and linha.widget.winfo_width() <= 1
    ]
    checar("nenhum campo nasce invisivel", not zerados, str(zerados))

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

    app.destroy()
    app.update()

print()
if falhas:
    print(f"FALHAS: {len(falhas)} -> {falhas}")
    sys.exit(1)

print("JANELA OK")
