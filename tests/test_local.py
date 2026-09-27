"""Verificacoes locais do pacote.

Por padrao nada aqui mexe no seu mouse. As secoes que movem o cursor so
rodam com --executar.
"""

import argparse
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

from wolfs_screen_hitter import detect, pointer, profiles, windows
from wolfs_screen_hitter.capture import ScreenCapture

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--executar",
    action="store_true",
    help="permite as secoes que movem o cursor de verdade",
)
opcoes = parser.parse_args()

falhas = []
pulados = []


def checar(nome, condicao, detalhe=""):
    marca = "ok  " if condicao else "FALHA"
    print(f"  [{marca}] {nome}{(' -> ' + detalhe) if detalhe else ''}")
    if not condicao:
        falhas.append(nome)


def pular(nome, motivo):
    print(f"  [pulado] {nome} -> {motivo}")
    pulados.append(nome)


print("1. nenhuma chamada de clique no pacote")
nomes = ["mousedown", "mouseup", "leftdown", "leftup", ".click(", "bdown", "bup"]
achou = []
for caminho in sorted(pathlib.Path("wolfs_screen_hitter").glob("*.py")):
    texto = caminho.read_text(encoding="utf-8").lower()
    achou += [(caminho.name, n) for n in nomes if n in texto]
checar("sem mouseDown/mouseUp/click", not achou, str(achou))

print("2. pyautogui nao e dependencia")
resultado = subprocess.run(
    [sys.executable, "-c", "import wolfs_screen_hitter.app, sys; print('pyautogui' in sys.modules)"],
    capture_output=True,
    text=True,
)
checar("pyautogui ausente", resultado.stdout.strip() == "False", resultado.stdout.strip())

print("3. perfis carregam e validam")
lista = profiles.list_profiles()
checar("tres perfis no pacote", len(lista) == 3, f"{len(lista)}")
for caminho in lista:
    try:
        perfis = profiles.load(caminho)
        checar(f"{caminho.name}", True, perfis.get("detector"))
    except profiles.ProfileError as erro:
        checar(f"{caminho.name}", False, str(erro))

print("4. perfil invalido e recusado")
ruim = pathlib.Path("_perfil_ruim.json")
ruim.write_text('{"detector": "inexistente", "target": {}}', encoding="utf-8")
try:
    profiles.load(ruim)
    checar("rejeita detector desconhecido", False)
except profiles.ProfileError:
    checar("rejeita detector desconhecido", True)
ruim.unlink()

print("5. resolucao de regiao")
janela = windows.Window(handle=1, title="x", left=0, top=0, width=1920, height=1040)
checar("window sem margem", windows.resolve_region({"mode": "window"}, janela) == (0, 0, 1920, 1040))
checar("window com margem 130", windows.resolve_region({"mode": "window", "margin": 130}, janela) == (130, 130, 1660, 780))
checar("tela", windows.resolve_region({"mode": "screen"}) == windows.screen())
checar("fixa", windows.resolve_region({"mode": "fixed", "left": 5, "top": 6, "width": 7, "height": 8}) == (5, 6, 7, 8))
checar("sem janela devolve None", windows.resolve_region({"mode": "window"}, None) is None)

print("6. cursor em coordenadas exatas")
if opcoes.executar:
    inicio = pointer.position()
    ok = True
    for alvo in [(300, 400), (1500, 300), (960, 520)]:
        pointer.move_to(*alvo)
        time.sleep(0.3)
        ok = ok and pointer.position() == alvo
    pointer.move_to(*inicio)
    checar("ida e volta exatas", ok)
else:
    pular("ida e volta exatas", "mexeria no seu mouse; rode com --executar")

print("7. detector de forma acha circulo claro e ignora vermelho")
perfil = profiles.load("profiles/circulo_claro.json")
tela = np.zeros((1040, 1920, 3), np.uint8)
cv2.circle(tela, (900, 500), 49, (240, 240, 240), 4)
achado = detect.detect(tela, perfil)
checar("circulo claro achado", achado is not None)
if achado:
    checar("centro correto", abs(achado.center[0] - 900) <= 4 and abs(achado.center[1] - 500) <= 4, str(achado.describe()))
tela = np.zeros((1040, 1920, 3), np.uint8)
cv2.circle(tela, (900, 500), 80, (40, 40, 220), 10)
checar("anel vermelho ignorado", detect.detect(tela, perfil) is None)

print("8. detector de template acha letra")
tela = np.zeros((1040, 1920, 3), np.uint8)
cv2.putText(tela, "A", (700, 500), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (240, 240, 240), 3, cv2.LINE_AA)
spec = profiles.load("profiles/letra_template.json")
achado = detect.detect(tela, spec)
checar("letra A achada", achado is not None)
if achado:
    dentro = 640 < achado.center[0] < 780 and 430 < achado.center[1] < 520
    checar("posicao plausivel", dentro, str(achado.describe()))
tela = np.zeros((1040, 1920, 3), np.uint8)
checar("tela vazia sem template", detect.detect(tela, spec) is None)

print("9. captura funciona")
with ScreenCapture() as captura:
    quadro = captura.grab(windows.screen())
    checar("formato BGR", quadro is not None and quadro.ndim == 3 and quadro.shape[2] == 3, str(captura.backend))
    checar("tamanho bate", abs(quadro.shape[1] - windows.screen()[2]) <= 2, f"{quadro.shape}")

print("10. movimento smooth chega exato e percorre o caminho")
if opcoes.executar:
    inicio = pointer.position()
    alvo = (inicio[0] + 260, inicio[1] + 120)
    t0 = time.perf_counter()
    pointer.move_to_smooth(*alvo, duracao=0.12)
    decorrido = time.perf_counter() - t0
    time.sleep(0.3)
    checar("smooth termina no alvo exato", pointer.position() == alvo, str(pointer.position()))
    checar("smooth leva tempo (nao teleporta)", decorrido > 0.05, f"{decorrido:.3f}s")
    checar("modo do perfil aplicado", pointer.aplicar(inicio[0], inicio[1], {"mode": "smooth"}) is not None)
    pointer.move_to(*inicio)
else:
    pular("smooth chega no alvo", "mexeria no seu mouse; rode com --executar")

print("11. hsv_min/hsv_max acha vermelho e ignora azul")
perfil = profiles.load("profiles/faixa_hsv.json")
tela = np.zeros((1080, 1920, 3), np.uint8)
cv2.rectangle(tela, (600, 400), (760, 500), (40, 40, 220), -1)
achado = detect.detect(tela, perfil)
checar("faixa vermelha achada", achado is not None)
if achado:
    perto = abs(achado.center[0] - 680) <= 12 and abs(achado.center[1] - 450) <= 12
    checar("centro da faixa correto", perto, achado.describe())
tela = np.zeros((1080, 1920, 3), np.uint8)
cv2.rectangle(tela, (600, 400), (760, 500), (220, 40, 40), -1)
checar("azul ignorado", detect.detect(tela, perfil) is None)

print("12. invert recupera glifo escuro sobre fundo claro")
base = profiles.load("profiles/letra_template.json")
claro = dict(base)
claro["target"] = dict(base["target"], invert=True)
tela = np.full((1040, 1920, 3), 235, np.uint8)
cv2.putText(tela, "A", (700, 500), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (20, 20, 20), 3, cv2.LINE_AA)
achado = detect.detect(tela, claro)
checar("achado com invert", achado is not None)
if achado:
    dentro = 640 < achado.center[0] < 780 and 430 < achado.center[1] < 520
    checar("posicao com invert", dentro, achado.describe())
checar("sem invert nao acha", detect.detect(tela, base) is None)

print("13. perfil sem cor e recusado")
sem_cor = {"detector": "shape", "target": {"work_scale": 0.5}}
try:
    detect.detect(np.zeros((100, 100, 3), np.uint8), sem_cor)
    checar("exige bright/dark/hsv", False)
except ValueError as erro:
    checar("exige bright/dark/hsv", "bright" in str(erro), str(erro)[:48])

print("14. detector desconhecido e recusado")
try:
    detect.detect(np.zeros((100, 100, 3), np.uint8), {"detector": "magia"})
    checar("rejeita detector", False)
except ValueError as erro:
    checar("rejeita detector", "magia" in str(erro), str(erro)[:48])

print("15. perfil com BOM carrega, e perfil invalido sai limpo")
com_bom = pathlib.Path("_perfil_bom.json")
# O BOM e o que o Set-Content -Encoding UTF8 do PowerShell 5.1 escreve.
com_bom.write_bytes(b"\xef\xbb\xbf" + pathlib.Path("profiles/circulo_claro.json").read_bytes())
try:
    carregado = profiles.load(com_bom)
    checar("perfil com BOM carrega", carregado.get("detector") == "shape", carregado.get("detector"))
except profiles.ProfileError as erro:
    checar("perfil com BOM carrega", False, str(erro)[:60])
com_bom.unlink()

invalido = pathlib.Path("_perfil_invalido.json")
invalido.write_text('{"detector": "inexistente", "target": {}}', encoding="utf-8")
resultado = subprocess.run(
    [sys.executable, "-m", "wolfs_screen_hitter", "check", str(invalido)],
    capture_output=True,
    text=True,
)
saida = resultado.stdout + resultado.stderr
checar("perfil invalido sai com codigo 2", resultado.returncode == 2, str(resultado.returncode))
checar("perfil invalido sem stack trace", "Traceback" not in saida, saida.strip()[:70])
checar("perfil invalido nomeia o campo", "detector" in saida and "inexistente" in saida)
invalido.unlink()

print()
if pulados:
    print(f"{len(pulados)} verificacao(oes) pulada(s): {pulados}")

if falhas:
    print(f"FALHAS: {len(falhas)} -> {falhas}")
    sys.exit(1)

print("TODAS AS VERIFICACOES PASSARAM")
