"""Confere que comandos, arquivos e campos citados no README existem."""

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

texto = (RAIZ / "README.md").read_text(encoding="utf-8") + (
    RAIZ / "README.pt.md"
).read_text(encoding="utf-8")

falhas = []

print("comandos citados no README")
# Do jeito que o texto usa: com o prefixo do modulo, ou soltos em crases
# dentro de frases ("rode `list-windows` e copie o nome").
citados_cmds = set(re.findall(r"wolfs[_-]screen[_-]hitter ([a-z][a-z-]*)", texto))
citados_cmds |= set(re.findall(r"[`\s]([a-z][a-z-]*)(?=[`\s,.])", texto))
citados_cmds &= {
    c for c in citados_cmds
    if re.fullmatch(r"(check|run|capture|crop|list-[a-z]+)", c)
}
fonte = (RAIZ / "wolfs_screen_hitter" / "app.py").read_text(encoding="utf-8")

# Sobe o parser de verdade, em vez de adivinhar pelo texto.
from wolfs_screen_hitter.app import _construir_parser

parser = _construir_parser()
_sub = [a for a in parser._actions if a.dest == "comando"][0]
comandos_reais = set(_sub.choices)

print(f"  subcomandos reais: {sorted(comandos_reais)}")
for comando in sorted(citados_cmds):
    existe = comando in comandos_reais
    print(f"  {'OK      ' if existe else 'AUSENTE '} {comando}")
    if not existe:
        falhas.append(f"comando inexistente: {comando}")

print()
print("flags citadas no README, por subcomando")
# Mapa flag -> {comandos que aceitam}, montado a partir do parser.
mapa = {}
for nome, subparser in _sub.choices.items():
    for acao in subparser._actions:
        for opcao in acao.option_strings:
            mapa.setdefault(opcao, set()).add(nome)
for global_acao in parser._actions:
    for opcao in global_acao.option_strings:
        mapa.setdefault(opcao, set()).add("<global>")

fontes = fonte + "".join(
    p.read_text(encoding="utf-8") for p in sorted((RAIZ / "tests").glob("*.py"))
)
for flag in sorted(set(re.findall(r"(--[a-z][a-z-]+)", texto))):
    onde = mapa.get(flag)
    em_testes = f'"{flag}"' in fontes
    if onde is None:
        status = "SÓ EM TESTE" if em_testes else "AUSENTE"
    else:
        status = "OK"
    print(f"  {status:<10} {flag} -> {sorted(onde) if onde else 'so nos testes'}")
    if status == "AUSENTE":
        falhas.append(f"flag inexistente: {flag}")

# O README diz qual flag e de qual comando, entao a tabela de flags do
# documento precisa casar com o parser. Extrai as linhas
# "| `--debug FILE` | `check` | ..." de cada README.
print()
print("tabela de flags do README vs parser")
padroes = re.findall(
    r"^\|\s*`(--[a-z-]+)(?:\s+[A-Za-z0-9]+)?`\s*\|\s*`([a-z-]+)`\s*\|",
    texto,
    re.M | re.I,
)
if not padroes:
    falhas.append("nenhuma linha da tabela de flags foi reconhecida")
for flag, cmd in padroes:
    onde = mapa.get(flag, set())
    ok = cmd in onde
    print(f"  {'OK      ' if ok else 'ERRADO '} {flag} em `{cmd}` (real: {sorted(onde)})")
    if not ok:
        falhas.append(
            f"README diz que {flag} e de {cmd}, mas o parser so aceita em {sorted(onde)}"
        )
print(f"  {len(padroes)} linhas conferidas ({len(padroes) // 2} por README)")

print()
print("arquivos citados no README")
citados = set(re.findall(r"profiles/[A-Za-z0-9_./]+", texto))
citados |= set(re.findall(r"tests/[A-Za-z0-9_./]+", texto))
citados |= set(re.findall(r"README(?:\.pt)?\.md", texto))
citados |= set(re.findall(r"\b(?:LICENSE|requirements\.txt|pyproject\.toml)\b", texto))
# Exemplo do tutorial de crop: o usuario cria o arquivo, entao o caminho
# citado nao precisa existir, so o diretorio.
exemplos = {c for c in citados if c.endswith((".png",)) and "letra.png" not in c}
citados -= exemplos
for item in sorted(citados):
    existe = (RAIZ / item).exists()
    print(f"  {'OK      ' if existe else 'AUSENTE '} {item}")
    if not existe:
        falhas.append(f"arquivo inexistente: {item}")
if exemplos:
    print(f"  (ignorados, sao saida do tutorial de crop: {sorted(exemplos)})")
    for item in sorted(exemplos):
        if not (RAIZ / item).parent.is_dir():
            falhas.append(f"diretorio do exemplo nao existe: {item}")

print()
print("chaves de perfil citadas vs perfis validos")
chaves_docs = set(re.findall(r'"([a-z_]+)":', texto))
conhecidas = {
    "name", "detector", "window", "title", "min_width", "min_height",
    "region", "mode", "margin", "left", "top", "width", "height",
    "target", "bright", "dark", "hsv_min", "hsv_max",
    "v_min", "v_max", "s_max",
    "size", "min", "max", "aspect", "fill", "area_min", "work_scale",
    "template", "threshold", "scale_min", "scale_max", "scale_steps",
    "invert", "pointer", "duration", "jitter", "controls",
    "corner_seconds",
}
desconhecidas = chaves_docs - conhecidas
print(f"  {len(chaves_docs)} chaves citadas no documento")
if desconhecidas:
    print(f"  NAO DOCUMENTADAS no codigo: {sorted(desconhecidas)}")
    falhas.append(f"chaves citadas que nao conheço: {sorted(desconhecidas)}")

print()
print("valores de enum citados")
for valor, contexto in [
    ("window", "region.mode"),
    ("screen", "region.mode"),
    ("virtual", "region.mode"),
    ("fixed", "region.mode"),
    ("shape", "detector"),
    ("template", "detector"),
    ("teleport", "pointer.mode"),
    ("smooth", "pointer.mode"),
]:
    citado = re.search(rf"[`\"]{re.escape(valor)}[`\"]", texto) is not None
    print(f"  {'OK      ' if citado else 'AUSENTE '} {contexto} = {valor}")
    if not citado:
        falhas.append(f"valor de enum nao citado: {valor}")

print()
if falhas:
    print("FALHAS:")
    for item in falhas:
        print(f"  {item}")
    sys.exit(1)
print("OK: tudo que o README cita existe no codigo")
