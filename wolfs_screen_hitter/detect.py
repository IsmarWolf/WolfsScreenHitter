"""Detectores de alvo visual: forma por cor e template de imagem."""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class Detection:
    x: int
    y: int
    width: int
    height: int
    score: float = 1.0
    kind: str = "shape"

    @property
    def center(self):
        return self.x + self.width / 2, self.y + self.height / 2

    @property
    def side(self):
        return max(self.width, self.height)

    def describe(self):
        return (
            f"x={self.x} y={self.y} {self.width}x{self.height} "
            f"centro=({self.center[0]:.0f}, {self.center[1]:.0f}) "
            f"nota={self.score:.2f}"
        )


def _intervalo(spec, chave, padrao):
    bloco = spec.get(chave) or {}
    return float(bloco.get("min", padrao[0])), float(bloco.get("max", padrao[1]))


def _reduzir(frame, escala):
    if escala == 1.0:
        return frame
    return cv2.resize(
        frame,
        None,
        fx=escala,
        fy=escala,
        interpolation=cv2.INTER_AREA,
    )


def _mascara_forma(frame, spec, escala):
    """Mascara binaria dos pixels que interessam, em HSV."""
    alvo = spec.get("target", {})
    hsv_min = alvo.get("hsv_min")
    hsv_max = alvo.get("hsv_max")

    if hsv_min and hsv_max:
        hsv = cv2.cvtColor(_reduzir(frame, escala), cv2.COLOR_BGR2HSV)
        return cv2.inRange(
            hsv,
            np.array(hsv_min, dtype=np.uint8),
            np.array(hsv_max, dtype=np.uint8),
        )

    claro = alvo.get("bright")
    escuro = alvo.get("dark")

    if not claro and not escuro:
        raise ValueError(
            "Perfil de forma precisa de 'bright', 'dark' ou um par "
            "'hsv_min'/'hsv_max'."
        )

    hsv = cv2.cvtColor(_reduzir(frame, escala), cv2.COLOR_BGR2HSV)
    matrizes = []

    if claro:
        matrizes.append(
            (hsv[:, :, 2] >= int(claro.get("v_min", 0)))
            & (hsv[:, :, 1] <= int(claro.get("s_max", 255)))
        )

    if escuro:
        matrizes.append(
            (hsv[:, :, 2] <= int(escuro.get("v_max", 255)))
            & (hsv[:, :, 1] <= int(escuro.get("s_max", 255)))
        )

    mascara = matrizes[0]

    for extra in matrizes[1:]:
        mascara = mascara | extra

    return mascara.astype(np.uint8) * 255


def detect_shape(frame, spec):
    """Acha blobs de uma cor cujo formato se aproxima de um circulo."""
    alvo = spec.get("target", {})
    escala = float(alvo.get("work_scale", 0.5))

    mascara = _mascara_forma(frame, spec, escala)
    mascara = cv2.morphologyEx(
        mascara,
        cv2.MORPH_CLOSE,
        np.ones((3, 3), np.uint8),
    )

    total, _, estatisticas, _ = cv2.connectedComponentsWithStats(
        mascara,
        connectivity=8,
    )

    lado_min, lado_max = _intervalo(alvo, "size", (0.0, 1e9))
    aspecto_min, aspecto_max = _intervalo(alvo, "aspect", (0.0, 1e9))
    preench_min, preench_max = _intervalo(alvo, "fill", (0.0, 1.0))
    area_min = float(alvo.get("area_min", 1.0))

    fator = 1.0 / escala
    melhor = None
    melhor_pontos = 0.0

    for indice in range(1, total):
        x, y, largura, altura, area = (
            int(valor) for valor in estatisticas[indice]
        )

        if largura <= 0 or altura <= 0 or area < area_min:
            continue

        lado = max(largura, altura) * fator

        if lado < lado_min or lado > lado_max:
            continue

        aspecto = largura / altura

        if aspecto < aspecto_min or aspecto > aspecto_max:
            continue

        preenchimento = area / (largura * altura)

        if preenchimento < preench_min or preenchimento > preench_max:
            continue

        pontos = lado * lado

        if pontos > melhor_pontos:
            melhor_pontos = pontos
            melhor = Detection(
                x=round(x * fator),
                y=round(y * fator),
                width=round(largura * fator),
                height=round(altura * fator),
            )

    return melhor


def _carregar_template(alvo, base_dir):
    caminho = alvo.get("template")

    if not caminho:
        raise ValueError("Perfil de template sem 'template'.")

    base = Path(caminho)

    if not base.is_absolute():
        base = (Path(base_dir) / base).resolve()

    if not base.exists():
        raise FileNotFoundError(f"Template nao encontrado: {base}")

    referencia = cv2.imread(str(base), cv2.IMREAD_GRAYSCALE)

    if referencia is None:
        raise ValueError(f"Template ilegivel: {base}")

    return referencia


def detect_template(frame, spec):
    """Localiza a imagem de um perfil em varias escalas (letras, simbolos)."""
    alvo = spec.get("target", {})
    referencia = _carregar_template(alvo, spec.get("_base_dir", "."))

    escala_min = float(alvo.get("scale_min", 0.5))
    escala_max = float(alvo.get("scale_max", 2.0))
    passos = max(1, int(alvo.get("scale_steps", 12)))
    limiar = float(alvo.get("threshold", 0.80))
    reducao = float(alvo.get("work_scale", 1.0))
    inverter = bool(alvo.get("invert", False))

    trabalho = _reduzir(frame, reducao)
    cinza = cv2.cvtColor(trabalho, cv2.COLOR_BGR2GRAY)

    if inverter:
        cinza = cv2.bitwise_not(cinza)

    melhor = None
    melhor_nota = -1.0

    for passo in range(passos + 1):
        fracao = passo / passos
        escala = escala_min + (escala_max - escala_min) * fracao
        altura = max(4, round(referencia.shape[0] * escala))
        largura = max(4, round(referencia.shape[1] * escala))

        if altura >= cinza.shape[0] or largura >= cinza.shape[1]:
            continue

        ajustado = cv2.resize(
            referencia,
            (largura, altura),
            interpolation=cv2.INTER_AREA if escala < 1 else cv2.INTER_CUBIC,
        )

        _, nota, _, posicao = cv2.minMaxLoc(
            cv2.matchTemplate(cinza, ajustado, cv2.TM_CCOEFF_NORMED)
        )

        if nota > melhor_nota:
            melhor_nota = nota
            melhor = (
                posicao[0] / reducao,
                posicao[1] / reducao,
                largura / reducao,
                altura / reducao,
            )

    if melhor is None or melhor_nota < limiar:
        return None

    x, y, largura, altura = melhor
    return Detection(
        x=round(x),
        y=round(y),
        width=round(largura),
        height=round(altura),
        score=round(float(melhor_nota), 4),
        kind="template",
    )


DETECTORS = {
    "shape": detect_shape,
    "template": detect_template,
}


def detect(frame, spec):
    """Roda o detector pedido pelo perfil."""
    tipo = spec.get("detector", "shape")

    if tipo not in DETECTORS:
        raise ValueError(
            f"Detector desconhecido: {tipo!r}. Use um de {sorted(DETECTORS)}."
        )

    return DETECTORS[tipo](frame, spec)
