"""Movimento do cursor. Este pacote nunca clica."""

import math
import random
import time

from . import win


def position():
    return win.cursor_position()


def move_to(x, y):
    return win.move_to(int(round(x)), int(round(y)))


def _bezier(t, x0, y0, cx, cy, x1, y1):
    inverso = 1 - t
    a = inverso * inverso
    b = 2 * inverso * t
    c = t * t
    return (
        a * x0 + b * cx + c * x1,
        a * y0 + b * cy + c * y1,
    )


def move_to_smooth(
    alvo_x,
    alvo_y,
    duracao=0.16,
    jitter=1.2,
    curva=0.18,
    min_passo=0.008,
    max_passo=0.014,
):
    """Move o cursor num caminho curvo, com tremor e passos irregulares."""
    inicio_x, inicio_y = position()
    distancia = math.hypot(alvo_x - inicio_x, alvo_y - inicio_y)

    if distancia < 2:
        return move_to(alvo_x, alvo_y)

    dir_x = (alvo_x - inicio_x) / distancia
    dir_y = (alvo_y - inicio_y) / distancia
    desvio = random.uniform(-1.0, 1.0) * min(45.0, max(10.0, distancia * curva))
    controle_x = (inicio_x + alvo_x) / 2 - dir_y * desvio
    controle_y = (inicio_y + alvo_y) / 2 + dir_x * desvio

    intervalo = random.uniform(min_passo, max_passo)
    passos = max(2, int(duracao / intervalo))

    for indice in range(1, passos + 1):
        t = indice / passos
        suave = t * t * (3 - 2 * t)
        px, py = _bezier(suave, inicio_x, inicio_y, controle_x, controle_y, alvo_x, alvo_y)
        move_to(px + random.uniform(-jitter, jitter), py + random.uniform(-jitter, jitter))
        time.sleep(random.uniform(min_passo, max_passo))

    return move_to(alvo_x, alvo_y)


def aplicar(alvo_x, alvo_y, ponteiro):
    """Executa o modo de movimento pedido pelo perfil."""
    ponteiro = ponteiro or {}
    modo = ponteiro.get("mode", "teleport")

    if modo == "smooth":
        return move_to_smooth(
            alvo_x,
            alvo_y,
            duracao=float(ponteiro.get("duration", 0.16)),
            jitter=float(ponteiro.get("jitter", 1.2)),
        )

    return move_to(alvo_x, alvo_y)
