"""Carregamento e validacao de perfis."""

import json
from copy import deepcopy
from pathlib import Path

from .detect import DETECTORS


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
DEFAULT_PROFILE_DIR = PROJECT_DIR / "profiles"
TEMPLATE_DIR = DEFAULT_PROFILE_DIR / "templates"

DETECTOR_NAMES = ", ".join(sorted(DETECTORS))


class ProfileError(ValueError):
    """Perfil invalido ou incompleto."""


def _require(mapping, chave, tipos, onde):
    if chave not in mapping:
        raise ProfileError(f"Falta '{onde}.{chave}' no perfil.")

    valor = mapping[chave]

    if not isinstance(valor, tipos):
        nomes = (
            tipos.__name__
            if isinstance(tipos, type)
            else "/".join(t.__name__ for t in tipos)
        )
        raise ProfileError(
            f"'{onde}.{chave}' deveria ser {nomes}, veio {type(valor).__name__}."
        )

    return valor


def load(path):
    """Le um perfil JSON e devolve o dict normalizado."""
    caminho = Path(path).resolve()

    if not caminho.exists():
        raise ProfileError(f"Perfil nao encontrado: {caminho}")

    try:
        bruto = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ProfileError(f"JSON invalido em {caminho.name}: {erro}") from erro

    if not isinstance(bruto, dict):
        raise ProfileError("O perfil precisa ser um objeto JSON.")

    perfil = deepcopy(bruto)
    perfil["_path"] = str(caminho)
    perfil["_base_dir"] = str(caminho.parent)

    validate(perfil)
    return perfil


def validate(perfil):
    """Confere os campos obrigatorios."""
    _require(perfil, "detector", str, "perfil")

    if perfil["detector"] not in DETECTORS:
        raise ProfileError(
            f"detector '{perfil['detector']}' invalido. Use: {DETECTOR_NAMES}."
        )

    alvo = _require(perfil, "target", dict, "perfil")

    if perfil["detector"] == "template":
        _require(alvo, "template", str, "target")
    else:
        tem_cor = any(
            chave in alvo for chave in ("bright", "dark", "hsv_min")
        )
        if not tem_cor:
            raise ProfileError(
                "Perfil de forma precisa de 'bright', 'dark' ou 'hsv_min'."
            )

    janela = perfil.get("window")

    if janela is not None and not isinstance(janela, dict):
        raise ProfileError("'window' precisa ser um objeto.")

    regiao = perfil.get("region")

    if regiao is not None and not isinstance(regiao, dict):
        raise ProfileError("'region' precisa ser um objeto.")

    ponteiro = perfil.get("pointer")

    if ponteiro is not None:
        if not isinstance(ponteiro, dict):
            raise ProfileError("'pointer' precisa ser um objeto.")
        modo = ponteiro.get("mode", "teleport")
        if modo not in ("teleport", "smooth"):
            raise ProfileError(
                f"pointer.mode invalido: {modo!r}. Use teleport ou smooth."
            )

    return perfil


def list_profiles(diretorio=None):
    """Lista os perfis .json de um diretorio."""
    base = Path(diretorio) if diretorio else DEFAULT_PROFILE_DIR

    if not base.exists():
        return []

    return sorted(
        caminho
        for caminho in base.glob("*.json")
        if caminho.is_file()
    )


def describe(perfil):
    """Resumo curto de um perfil, para a CLI."""
    detector = perfil.get("detector", "?")
    janela = (perfil.get("window") or {}).get("title") or "tela toda"
    regiao = (perfil.get("region") or {}).get("mode", "window")
    ponteiro = (perfil.get("pointer") or {}).get("mode", "teleport")
    alvo = perfil.get("target", {})
    detalhe = (
        alvo.get("template")
        or "bright" in alvo
        and "pixels claros"
        or "dark" in alvo
        and "pixels escuros"
        or "faixa HSV"
    )
    return {
        "name": perfil.get("name", Path(perfil.get("_path", "?")).stem),
        "detector": detector,
        "window": janela,
        "region": regiao,
        "pointer": ponteiro,
        "detail": detalhe,
    }
