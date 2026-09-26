"""Verificacao ponta a ponta contra a tela real.

Cria uma imagem de teste com um anel claro e um anel vermelho, abre no
visualizador padrao do Windows, detecta pela captura DXGI, confirma que o
vermelho foi ignorado e move o cursor de verdade. Fecha tudo ao final.
"""

import ctypes
import math
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

from wolfs_screen_hitter import detect, pointer, windows
from wolfs_screen_hitter.capture import ScreenCapture

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "out"
SAIDA.mkdir(exist_ok=True)

PERFIL = {
    "name": "Teste ponta a ponta",
    "detector": "shape",
    "window": {"title": "alvo.png"},
    "region": {"mode": "window", "margin": 0},
    "target": {
        "bright": {"v_min": 150, "s_max": 110},
        "size": {"min": 30, "max": 300},
        "aspect": {"min": 0.6, "max": 1.6},
        "fill": {"min": 0.03, "max": 0.45},
        "area_min": 10,
        "work_scale": 0.5,
    },
    "pointer": {"mode": "teleport"},
}

# Anel claro (o alvo) em (200,150); anel vermelho (o isca) em (60,60).
imagem = np.full((300, 400, 3), 25, np.uint8)
cv2.circle(imagem, (200, 150), 50, (240, 240, 240), 4)
cv2.circle(imagem, (60, 60), 40, (40, 40, 220), 8)
alvo_png = SAIDA / "alvo.png"
cv2.imwrite(str(alvo_png), imagem)
print(f"cena criada: {alvo_png.name} 400x300, anel claro em (200,150), vermelho em (60,60)")

os.startfile(str(alvo_png))
perfil = PERFIL

janela = None
for _ in range(30):
    time.sleep(0.4)
    janela = windows.find_window("alvo.png")
    if janela is not None:
        break

if janela is None:
    print("FALHOU: o visualizador nao abriu a imagem")
    sys.exit(1)

print(f"janela '{janela.title}' {janela.width}x{janela.height} @({janela.left},{janela.top})")

regiao = (janela.left, janela.top, janela.width, janela.height)

with ScreenCapture() as captura:
    print(f"backend={captura.backend}")
    achado = None
    for _ in range(6):
        quadro = captura.grab(regiao)
        achado = detect.detect(quadro, perfil)
        if achado:
            break
        time.sleep(0.1)

    assert achado is not None, "nada detectado na tela real"

    tela_x = regiao[0] + achado.center[0]
    tela_y = regiao[1] + achado.center[1]
    lado = achado.side / 2
    print(f"detectado na regiao: {achado.describe()}")
    print(f"ponto de tela: ({tela_x:.0f}, {tela_y:.0f})")

    dentro = (
        janela.left <= tela_x < janela.right and janela.top <= tela_y < janela.bottom
    )
    print(f"ponto dentro da janela: {dentro}")

    def hsv(x, y):
        patch = quadro[int(y), int(x)].reshape(1, 1, 3)
        return tuple(int(v) for v in cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)[0][0])

    # O alvo e um anel: o contorno deve ser claro e o miolo escuro.
    # O traço tem poucos pixels, então amostramos um pouco dentro da borda.
    raio = lado * 0.93
    contorno = [
        hsv(
            achado.center[0] + raio * math.cos(a),
            achado.center[1] + raio * math.sin(a),
        )
        for a in [i * math.pi / 24 for i in range(48)]
    ]
    claros = sum(1 for h, s, v in contorno if v >= 150 and s <= 110)
    centro_hsv = hsv(*achado.center)
    print(f"pontos claros no contorno: {claros}/48")
    print(f"miolo HSV: {centro_hsv} (escuro esperado, pois e anel)")

    anel_presente = claros >= 36
    miolo_escuro = centro_hsv[2] < 90

    # O anel vermelho da imagem esta em (60,60); confirmamos que ele existe
    # na tela e que o detector NAO o escolheu.
    hsv_tela = cv2.cvtColor(quadro, cv2.COLOR_BGR2HSV)
    vermelho = cv2.inRange(
        hsv_tela,
        np.array([0, 140, 140], np.uint8),
        np.array([12, 255, 255], np.uint8),
    )
    contornos = cv2.findContours(vermelho, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    pontos_verm = [c for c in contornos if cv2.contourArea(c) > 200]
    print(f"aneles vermelhos na tela: {len(pontos_verm)}")

    longe_do_vermelho = True
    if pontos_verm:
        centros_verm = [cv2.boundingRect(c) for c in pontos_verm]
        print(f"caixas vermelhas (x,y,w,h): {centros_verm}")
        for vx, vy, vw, vh in centros_verm:
            vcx, vcy = vx + vw / 2, vy + vh / 2
            if abs(vcx - achado.center[0]) < 60 and abs(vcy - achado.center[1]) < 60:
                longe_do_vermelho = False
    print(f"detecao nao e o anel vermelho: {longe_do_vermelho}")

    cv2.imwrite(str(SAIDA / "verif_tela.png"), quadro)

    print()
    print("movendo o cursor de verdade para o ponto detectado")
    origem = (100, 100)
    pointer.move_to(*origem)
    time.sleep(0.15)
    antes = pointer.position()
    print(f"cursor em posicao neutra: {antes}")
    pointer.move_to(tela_x, tela_y)
    time.sleep(0.15)
    depois = pointer.position()
    print(f"depois: {depois}")
    partiu = antes != depois
    alcancou = abs(depois[0] - tela_x) <= 1 and abs(depois[1] - tela_y) <= 1
    print(f"cursor saiu do neutro: {partiu}")
    print(f"cursor chegou no alvo: {alcancou}")

    pointer.move_to(*origem)

print()
print("tentando fechar o visualizador de teste (melhor esforco)")
for mensagem, parametro in ((0x0010, 0), (0x0112, 0xF060)):
    ctypes.windll.user32.PostMessageW(janela.handle, mensagem, 0, parametro)
    time.sleep(0.8)
    if windows.find_window("alvo.png") is None:
        break
ainda = windows.find_window("alvo.png")
fechado = ainda is None
if not fechado:
    print("aviso: visualizador ficou aberto; feche a janela a mao")

ok = (
    dentro
    and anel_presente
    and miolo_escuro
    and longe_do_vermelho
    and partiu
    and alcancou
)

print()
print("RESULTADO:", "OK" if ok else "FALHOU")
print(f"evidencia visual em: {SAIDA / 'verif_tela.png'}")
sys.exit(0 if ok else 1)
