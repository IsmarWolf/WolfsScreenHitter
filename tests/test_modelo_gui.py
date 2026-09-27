"""Testes do modelo do formulario, sem tela.

O modelo e a parte do GUI que precisa estar provada: se ele calcula o
perfil errado, nenhuma quantidade de widget conserta. Roda em qualquer
lugar, porque nao importa tkinter.
"""

import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from wolfs_screen_hitter import profiles
from wolfs_screen_hitter.gui import model

falhas = []


def _divergencias(esperado, obtido, prefixo=""):
    """Lista as chaves cujo valor mudou entre o perfil original e a volta."""
    achadas = []
    for chave, valor in esperado.items():
        if isinstance(valor, dict):
            achadas += _divergencias(valor, obtido.get(chave) or {}, f"{prefixo}{chave}.")
        elif obtido.get(chave) != valor:
            achadas.append(f"{prefixo}{chave}: {valor!r} -> {obtido.get(chave)!r}")
    return achadas


def checar(nome, condicao, detalhe=""):
    marca = "ok  " if condicao else "FALHA"
    print(f"  [{marca}] {nome}{(' -> ' + detalhe) if detalhe else ''}")
    if not condicao:
        falhas.append(nome)


print("1. cada campo tem caminho unico e tipo valido")
caminhos = [c.caminho for c in model.CAMPOS]
checar("caminhos unicos", len(caminhos) == len(set(caminhos)), f"{len(caminhos)} campos")
tipos = {c.tipo for c in model.CAMPOS}
checar("tipos conhecidos", tipos <= {"texto", "int", "float", "bool", "escolha"}, str(sorted(tipos)))
com_opcao = [c for c in model.CAMPOS if c.tipo == "escolha"]
checar("toda escolha tem opcoes", all(c.opcoes for c in com_opcao), f"{len(com_opcao)} escolhas")
checar(
    "todo perfilado existe no PERFILADO",
    all(chave in model.PERFILADO for c in model.CAMPOS for chave, _ in c.aparece),
)

print("2. os tres perfis do pacote passam pelo modelo sem perder valor")
# O GUI preenche o que falta com o padrao do campo, entao o perfil de saida
# tem mais chaves que o original. O que nao pode acontecer e o original
# mudar de valor, entao a comparacao e "todo valor do original sobrevive".
for caminho in sorted(profiles.list_profiles()):
    original = profiles.load(caminho)
    limpo = {k: v for k, v in original.items() if not k.startswith("_")}
    campos = model.perfil_para_campos(limpo)
    voltou = model.campos_para_perfil(campos, base=limpo)

    mudou = _divergencias(limpo, voltou)
    checar(f"{caminho.name} nao perde nem troca valor", not mudou, str(mudou))

    try:
        profiles.validate(dict(voltou, _path=original["_path"], _base_dir=original["_base_dir"]))
        checar(f"{caminho.name} continua valido", True)
    except profiles.ProfileError as erro:
        checar(f"{caminho.name} continua valido", False, str(erro))

print("2b. hsv e bright nunca coexistem, porque o hsv venceria o bright")
alvo = model.perfil_padrao()["target"]
checar("padrao usa bright", "bright" in alvo, str(sorted(alvo)))
checar("padrao nao tem hsv", "hsv_min" not in alvo, str(sorted(alvo)))
com_faixa = dict(alvo, hsv_min=[0, 140, 140], hsv_max=[12, 255, 255])
checar("tem as duas coisas antes de podar", "bright" in com_faixa and "hsv_min" in com_faixa)

print("3. perfil novo e valido pelo mesmo validador da CLI")
padrao = model.perfil_padrao()
alvo_padrao = padrao["target"]
checar("o padrao e shape", padrao.get("detector") == "shape", str(padrao.get("detector")))
checar("o padrao tem bright", "bright" in alvo_padrao, str(sorted(alvo_padrao)))
checar("o padrao nao tem campo de template", "threshold" not in alvo_padrao, str(sorted(alvo_padrao)))
checar(
    "work_scale do shape e 0.5",
    alvo_padrao.get("work_scale") == 0.5,
    str(alvo_padrao.get("work_scale")),
)
try:
    profiles.validate(padrao)
    checar("perfil padrao valida", True)
except profiles.ProfileError as erro:
    checar("perfil padrao valida", False, str(erro))

print("4. limites sao conferidos, com o nome do campo na mensagem")
# Campos que so existem para um detector sao conferidos no perfil desse
# detector: em um perfil shape, scale_steps nem aparece na tela.
base_shape = model.perfil_padrao()
base_template = model.campos_para_perfil(
    dict(model.perfil_para_campos(base_shape), detector="template",
         **{"target.template": "templates/letra.png"}),
    base=base_shape,
)
casos = [
    (base_shape, {"target.size.min": "abc"}, "texto nao numerico"),
    (base_shape, {"target.bright.v_min": "300"}, "acima do maximo"),
    (base_shape, {"target.fill.max": "2"}, "acima de 1"),
    (base_shape, {"target.work_scale": "0"}, "abaixo do minimo"),
    (base_shape, {"target.hsv_min.0": "200"}, "matiz acima de 179"),
    (base_template, {"target.scale_steps": "0"}, "zero passos"),
    (base_template, {"target.threshold": "1.5"}, "limiar acima de 1"),
]
for base, alteracoes, descricao in casos:
    campos = model.perfil_para_campos(base)
    campos.update(alteracoes)
    try:
        model.campos_para_perfil(campos, base=base)
        checar(descricao, False, "aceitou um valor invalido")
    except model.ErroDeCampo as erro:
        esperava = list(alteracoes)[0]
        checar(descricao, erro.caminho == esperava, f"{erro.caminho}: {erro.mensagem}")

print("5. visibilidade por contexto")
forma = model.perfil_padrao()
visiveis_forma = set(model.visiveis_chat(forma))
checar("forma mostra size.min", "target.size.min" in visiveis_forma)
checar("forma nao mostra threshold", "target.threshold" not in visiveis_forma)
checar(
    "forma com region=screen esconde margin",
    "region.margin" not in set(
        model.visiveis_chat(dict(forma, region={"mode": "screen"}))
    ),
)

template = dict(forma, detector="template", target=dict(forma["target"], template="templates/letra.png"))
visiveis_template = set(model.visiveis_chat(template))
checar("template mostra threshold", "target.threshold" in visiveis_template)
checar("template nao mostra size.min", "target.size.min" not in visiveis_template)

janela = dict(forma, region={"mode": "window"})
visiveis_janela = set(model.visiveis_chat(janela))
checar("region=window mostra margin", "region.margin" in visiveis_janela)
checar("region=window nao mostra left", "region.left" not in visiveis_janela)

fixa = dict(forma, region={"mode": "fixed", "left": 1, "top": 2, "width": 3, "height": 4})
visiveis_fixa = set(model.visiveis_chat(fixa))
checar("region=fixed mostra left", "region.left" in visiveis_fixa)
checar("region=fixed nao mostra margin", "region.margin" not in visiveis_fixa)

smooth = dict(forma, pointer={"mode": "smooth"})
visiveis_smooth = set(model.visiveis_chat(smooth))
checar("cursor smooth mostra duration", "pointer.duration" in visiveis_smooth)
checar("cursor teleport esconde duration", "pointer.duration" not in visiveis_forma)

print("6. listas hsv viram lista de tres, e nao dicionario")
campos = model.perfil_para_campos(forma)
for indice in range(3):
    campos[f"target.hsv_min.{indice}"] = str(10 * (indice + 1))
    campos[f"target.hsv_max.{indice}"] = str(150 + indice)
perfil = model.campos_para_perfil(campos, base=forma)
alvo = perfil["target"]
checar("hsv_min e lista", alvo.get("hsv_min") == [10, 20, 30], str(alvo.get("hsv_min")))
checar("hsv_max e lista", alvo.get("hsv_max") == [150, 151, 152], str(alvo.get("hsv_max")))
checar("preenchendo a faixa, bright sai", "bright" not in alvo, str(sorted(alvo)))
checar("preenchendo a faixa, dark sai", "dark" not in alvo, str(sorted(alvo)))
checar("usa_faixa verdadeiro", model.usa_faixa(campos) is True)
checar("usa_faixa falso no padrao", model.usa_faixa(model.perfil_para_campos(forma)) is False)

print("7. titulo vazio vira null, e mode poda o que nao usa")
perfil = model.campos_para_perfil(model.perfil_para_campos(padrao), base=padrao)
checar("title vazio e null", perfil["window"]["title"] is None, repr(perfil["window"].get("title")))
checar("region=window nao grava left", "left" not in perfil["region"], str(perfil["region"]))

campos = model.perfil_para_campos(padrao)
campos["region.mode"] = "fixed"
campos["region.left"] = "5"
campos["region.top"] = "6"
campos["region.width"] = "800"
campos["region.height"] = "600"
perfil = model.campos_para_perfil(campos, base=padrao)
checar("region=fixed grava o retangulo", perfil["region"].get("width") == 800, str(perfil["region"]))
checar("region=fixed nao grava margin", "margin" not in perfil["region"], str(perfil["region"]))

print("8. cursor teleport nao grava duration")
campos = model.perfil_para_campos(padrao)
campos["pointer.mode"] = "teleport"
campos["pointer.duration"] = "0.9"
perfil = model.campos_para_perfil(campos, base=padrao)
checar("teleport limpa duration", "duration" not in perfil["pointer"], str(perfil["pointer"]))

campos["pointer.mode"] = "smooth"
perfil = model.campos_para_perfil(campos, base=padrao)
checar("smooth guarda duration", perfil["pointer"].get("duration") == 0.9, str(perfil["pointer"]))

print("9. valor numerico vazio cai no padrao do campo")
campos = model.perfil_para_campos(padrao)
campos["target.size.min"] = ""
perfil = model.campos_para_perfil(campos, base=padrao)
checar("vazio usa o padrao", perfil["target"]["size"]["min"] == 30, str(perfil["target"]["size"]))

print("11. trocar de detector apaga os campos que o outro usava")
campos = model.perfil_para_campos(padrao)
campos["detector"] = "template"
campos["target.template"] = "templates/letra.png"
virou_template = model.campos_para_perfil(campos, base=padrao)
checar("virou template", virou_template["detector"] == "template", str(virou_template["detector"]))
checar("o alvo nao tem mais campo de cor", "bright" not in virou_template["target"], str(sorted(virou_template["target"])))
checar("o alvo nao tem mais campo de forma", "size" not in virou_template["target"], str(sorted(virou_template["target"])))
checar("guardou o template", virou_template["target"]["template"] == "templates/letra.png", str(virou_template["target"].get("template")))
checar("work_scale continua la", "work_scale" in virou_template["target"], str(sorted(virou_template["target"])))

campos = model.perfil_para_campos(virou_template)
campos["detector"] = "shape"
voltou_shape = model.campos_para_perfil(campos, base=virou_template)
checar("voltou shape", voltou_shape["detector"] == "shape", str(voltou_shape["detector"]))
checar("o shape nao herdou threshold", "threshold" not in voltou_shape["target"], str(sorted(voltou_shape["target"])))
checar("o shape nao herdou template", "template" not in voltou_shape["target"], str(sorted(voltou_shape["target"])))
checar("o shape tem bright de novo", "bright" in voltou_shape["target"], str(sorted(voltou_shape["target"])))

print("12. escrever duas vezes nao acumula nem duplica")
uma = model.campos_para_perfil(model.perfil_para_campos(padrao), base=padrao)
duas = model.campos_para_perfil(model.perfil_para_campos(padrao), base=uma)
checar("ida e volta no perfil novo estavel", uma == duas, str(_divergencias(uma, duas)))
checar("hsv continua lista", isinstance(duas["target"].get("hsv_min", []), list))

print("13. o modelo nao importa tkinter")
# A intencao e o modelo rodar sem interface, entao o que importa e o
# import, nao a palavra "tkinter" no texto. Um comentario sobre o assunto
# nao deve reprovar o teste.
import ast

fonte = (RAIZ / "wolfs_screen_hitter" / "gui" / "model.py").read_text(encoding="utf-8")
arvore = ast.parse(fonte)
importados = set()
for no in ast.walk(arvore):
    if isinstance(no, ast.Import):
        importados |= {alias.name.split(".")[0] for alias in no.names}
    elif isinstance(no, ast.ImportFrom) and no.module:
        importados.add(no.module.split(".")[0])

checar("modelo nao importa tkinter", "tkinter" not in importados, str(sorted(importados)))
checar("modelo nao importa ttk", "ttk" not in importados, str(sorted(importados)))
checar("tkinter nem carregou no processo", "tkinter" not in sys.modules)

print()
if falhas:
    print(f"FALHAS: {len(falhas)} -> {falhas}")
    sys.exit(1)

print("MODELO OK")
