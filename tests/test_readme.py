"""Confere que os dois READMEs tem a mesma estrutura e links validos."""

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def slug(titulo):
    """Como o GitHub monta a ancora de um heading: minusculas, sem acento visual."""
    titulo = re.sub(r"^#{1,6}\s+", "", titulo)
    titulo = re.sub(r"[^\w\s-]", "", titulo, flags=re.UNICODE)
    return re.sub(r"\s+", "-", titulo.strip()).lower()


def analisar(caminho):
    texto = caminho.read_text(encoding="utf-8")
    linhas = texto.splitlines()

    heads = [l for l in linhas if re.match(r"^#{1,6} ", l)]
    h2 = [l for l in linhas if re.match(r"^## ", l)]
    h3 = [l for l in linhas if re.match(r"^### ", l)]
    tabelas = [l for l in linhas if l.startswith("|")]
    blocos = texto.count("```") // 2
    alvos = {slug(h) for h in heads}

    quebrados = []
    for link in re.findall(r"\]\(#([^)]+)\)", texto):
        if link not in alvos:
            quebrados.append(link)

    return {
        "nome": caminho.name,
        "linhas": len(linhas),
        "h2": h2,
        "h3": h3,
        "h2_n": len(h2),
        "h3_n": len(h3),
        "tabelas_n": len(tabelas),
        "blocos_n": blocos,
        "quebrados": quebrados,
    }


ing = analisar(RAIZ / "README.md")
pt = analisar(RAIZ / "README.pt.md")

falhas = []

print(f"{'arquivo':<14} {'linhas':>7} {'h2':>4} {'h3':>4} {'tabelas':>8} {'blocos':>7}")
for r in (ing, pt):
    print(
        f"{r['nome']:<14} {r['linhas']:>7} {r['h2_n']:>4} {r['h3_n']:>4} "
        f"{r['tabelas_n']:>8} {r['blocos_n']:>7}"
    )
    print(f"  secoes h2: {[h[3:] for h in r['h2']]}")
    if r["quebrados"]:
        print(f"  LINKS QUEBRADOS: {r['quebrados']}")
        falhas.append(f"{r['nome']}: {r['quebrados']}")

print()
if ing["h2_n"] != pt["h2_n"]:
    falhas.append(
        f"numero de secoes h2 diverge: {ing['h2_n']} vs {pt['h2_n']}"
    )
if ing["h3_n"] != pt["h3_n"]:
    falhas.append(
        f"numero de subsecoes h3 diverge: {ing['h3_n']} vs {pt['h3_n']}"
    )

# Os titulos sao em idiomas diferentes, entao so comparamos a ordem dos
# niveis (h2 na posicao N tem de ser h2 do outro lado tambem).
niveis_ing = [len(h) - len(h.lstrip("#")) for h in ing["h2"]]
niveis_pt = [len(h) - len(h.lstrip("#")) for h in pt["h2"]]
if niveis_ing != niveis_pt:
    falhas.append("ordem das secoes divergente")

# O setup tem de ser a primeira secao, e o troubleshooting tem de ser unico.
for r, nome in ((ing, "ing"), (pt, "pt")):
    primeira = r["h2"][0].lower()
    if not ("setup" in primeira or "instala" in primeira):
        falhas.append(f"{nome}: primeira secao e {primeira!r}, nao o setup")
    troubles = [h for h in r["h2"] if "troubleshoot" in h.lower() or "solu" in h.lower()]
    if len(troubles) != 1:
        falhas.append(f"{nome}: {len(troubles)} secoes de troubleshooting, esperava 1")

if falhas:
    print("FALHAS:")
    for f in falhas:
        print(f"  {f}")
    sys.exit(1)

print("OK: os dois READMEs tem a mesma estrutura, links validos, setup primeiro")
