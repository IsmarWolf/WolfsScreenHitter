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
comandos = sorted(
    set(re.findall(r"wolfs_screen_hitter ([a-z-]+)", texto))
    | set(re.findall(r"wolfs-screen-hitter ([a-z-]+)", texto))
)
fonte = (RAIZ / "wolfs_screen_hitter" / "app.py").read_text(encoding="utf-8")
for comando in comandos:
    existe = f'"{comando}"' in fonte
    print(f"  {'OK      ' if existe else 'AUSENTE '} {comando}")
    if not existe:
        falhas.append(f"comando inexistente: {comando}")

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
print("flags citadas no README")
flags = sorted(set(re.findall(r"(--[a-z][a-z-]+)", texto)))
fontes = fonte + "".join(
    p.read_text(encoding="utf-8") for p in sorted((RAIZ / "tests").glob("*.py"))
)
for flag in flags:
    existe = f'"{flag}"' in fontes
    print(f"  {'OK      ' if existe else 'AUSENTE '} {flag}")
    if not existe:
        falhas.append(f"flag inexistente: {flag}")


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
