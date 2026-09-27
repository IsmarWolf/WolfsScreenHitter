"""Testes do ciclo do perfil na interface, sem abrir nenhuma janela.

O que se testa aqui e o estado: abrir, editar, salvar e o aviso de que o
contexto mudou. A janela em si precisa de tela e nao entra no roteiro
automatizado, entao o desenho fica com o modelo, que ja e testado.
"""

import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from wolfs_screen_hitter import profiles  # noqa: E402
from wolfs_screen_hitter.gui import estado as controlador  # noqa: E402
from wolfs_screen_hitter.gui import model  # noqa: E402

falhas = []


def checar(nome, condicao, detalhe=""):
    print(f"  [{'ok  ' if condicao else 'FALHA'}] {nome}" + (f" -> {detalhe}" if not condicao else ""))
    if not condicao:
        falhas.append(nome)


print("1. perfil novo comeca limpo e sem caminho")
est = controlador.Estado()
checar("sem caminho", est.caminho is None, str(est.caminho))
# Nasce limpo: um perfil novo ainda nao e trabalho do usuario, entao nao
# faz sentido pedir para confirmar descarte ao sair dele.
checar("sem mudanca a perder", est.sujo is False)
checar("digitando vira mudanca", est.definir("target.size.min", "40") is False and est.sujo is True)
checar("tem os campos do padrao", est.texto("detector") == "shape", est.texto("detector"))

print("2. salvar sem destino explica o que fazer")
try:
    est.salvar()
    checar("recusa sem destino", False, "aceitou salvar")
except controlador.EstadoSemDestino as erro:
    checar("recusa sem destino", "Salvar como" in str(erro), str(erro))

print("3. abrir, editar e salvar preserva o arquivo")
with tempfile.TemporaryDirectory() as pasta:
    destino = Path(pasta)
    original = destino / "original.json"
    profiles.save(profiles.load(RAIZ / "profiles" / "circulo_claro.json"), original)

    est = controlador.Estado(destino)
    checar("acha o perfil salvo", est.listar() == [original], str(est.listar()))

    est.abrir(original)
    checar("abre e fica limpo", est.sujo is False and est.caminho == original)
    checar("campo carregado", est.texto("target.bright.v_min") == "150", est.texto("target.bright.v_min"))

    mudou = est.definir("target.bright.v_min", "180")
    checar("editar marca mudanca", est.sujo is True)
    checar("editar nao muda o contexto", mudou is False)
    est.salvar()

    relido = json.loads(original.read_text(encoding="utf-8"))
    checar("valor novo foi para o disco", relido["target"]["bright"]["v_min"] == 180, str(relido["target"]["bright"]))
    checar("salvar limpa a marca", est.sujo is False)
    checar("nada de leitura foi para o arquivo", "_path" not in relido and "_base_dir" not in relido, str(sorted(relido)))

print("4. trocar o detector avisa que a tela precisa mudar")
est = controlador.Estado()
checar("shape nao muda o contexto", est.definir("detector", "shape") is False)
checar("template muda o contexto", est.definir("detector", "template") is True)
checar("template de novo nao muda", est.definir("detector", "template") is False)
checar("voltar para shape muda", est.definir("detector", "shape") is True)

est = controlador.Estado()
checar("regiao muda o contexto", est.definir("region.mode", "fixed") is True)
checar("cursor muda o contexto", est.definir("pointer.mode", "smooth") is True)
checar("campo comum nao muda", est.definir("target.size.min", "50") is False)

# Um caminho de template nao tem nada a ver com o que aparece na tela. Se
# ele contasse como mudanca de contexto, digitar o arquivo reconstruiria o
# formulario inteiro, e o campo-escolher-arquivo sumiria debaixo do dedo
# no momento em que a pessoa terminasse de escrever.
est = controlador.Estado()
checar(
    "escolher o template nao muda o contexto",
    est.definir("target.template", "glifo.png") is False,
    str(model.contexto_dos_campos(est.campos)),
)
checar("o caminho mesmo assim foi guardado", est.texto("target.template") == "glifo.png", "")

print("5. o que o formulario mostra e o que esta em edicao")
est = controlador.Estado()
est.definir("detector", "template")
est.definir("target.template", "templates/letra.png")
contexto = model.contexto_dos_campos(est.campos)
visiveis = set()
for _i, _t, condicao, grupo in model.GRUPOS:
    if condicao and not model.PERFILADO[condicao](contexto):
        continue
    visiveis |= {campo.caminho for campo in grupo if campo.visivel(contexto)}
checar("apos virar template, threshold aparece", "target.threshold" in visiveis)
checar("apos virar template, size.min some", "target.size.min" not in visiveis)
checar("o campo digitado continua no estado", est.texto("target.template") == "templates/letra.png")

print("6. valor invalido aponta o campo, e nada e gravado")
with tempfile.TemporaryDirectory() as pasta:
    destino = Path(pasta) / "ruim.json"
    est = controlador.Estado()
    est.definir("target.size.min", "abc")
    try:
        est.salvar(destino)
        checar("recusa valor invalido", False, "aceitou")
    except model.ErroDeCampo as erro:
        checar("recusa valor invalido", True)
        checar("aponta o campo", erro.caminho == "target.size.min", erro.caminho)
    checar("nao criou arquivo", not destino.exists())
    checar("continua sujo", est.sujo is True)

print("7. nao da para limpar a cor, e o perfil continua valido")
# Limpar as caixas de claro e escuro nao apaga nada: campo numerico vazio
# volta ao padrao. E o que impede a interface de gravar um perfil de forma
# sem cor nenhuma, que a CLI recusaria.
with tempfile.TemporaryDirectory() as pasta:
    destino = Path(pasta) / "sem_caixa_preenchida.json"
    est = controlador.Estado()
    for campo in ("target.bright.v_min", "target.bright.s_max", "target.dark.v_max", "target.dark.s_max"):
        est.definir(campo, "")
    est.salvar(destino)
    relido = json.loads(destino.read_text(encoding="utf-8"))
    checar("o arquivo foi gravado", destino.exists())
    checar("a cor continua la", "bright" in relido["target"], str(sorted(relido["target"])))

print("7b. profiles.save recusa o que a CLI recusa")
with tempfile.TemporaryDirectory() as pasta:
    try:
        profiles.save({"detector": "shape", "target": {}}, Path(pasta) / "sem_cor.json")
        checar("recusa perfil sem cor", False, "aceitou")
    except profiles.ProfileError as erro:
        checar("recusa perfil sem cor", "bright" in str(erro), str(erro))
    checar("nao criou o arquivo recusado", not (Path(pasta) / "sem_cor.json").exists())

print("8. salvar cria a pasta se ela nao existir")
with tempfile.TemporaryDirectory() as pasta:
    destino = Path(pasta) / "nova" / "perfil.json"
    est = controlador.Estado()
    est.salvar(destino)
    checar("criou a pasta e o arquivo", destino.exists(), str(destino))
    # A listagem e do nivel de cima, que e como os perfis sao organizados.
    checar("a listacao acha quem esta na mesma pasta", controlador.Estado(destino.parent).listar() == [destino])
    checar("listar nao desce em subpasta", controlador.Estado(Path(pasta)).listar() == [])

print("9. o estado nao importa tkinter")
import ast

fonte = (RAIZ / "wolfs_screen_hitter" / "gui" / "estado.py").read_text(encoding="utf-8")
importados = set()
for no in ast.walk(ast.parse(fonte)):
    if isinstance(no, ast.Import):
        importados |= {a.name.split(".")[0] for a in no.names}
    elif isinstance(no, ast.ImportFrom) and no.module:
        importados.add(no.module.split(".")[0])
checar("estado nao importa tkinter", "tkinter" not in importados, str(sorted(importados)))
checar("tkinter nem carregou", "tkinter" not in sys.modules)

print()
if falhas:
    print(f"FALHAS: {len(falhas)} -> {falhas}")
    sys.exit(1)

print("ESTADO OK")
