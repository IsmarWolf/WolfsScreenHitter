"""Carregamento e validacao de perfis."""

import json
import os
from copy import deepcopy
from pathlib import Path

from .detect import DETECTORS


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
DEFAULT_PROFILE_DIR = PROJECT_DIR / "profiles"

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
        # utf-8-sig le UTF-8 normal e tambem descarta a marca de ordem de
        # byte, que e o que o PowerShell 5.1 escreve por padrao.
        bruto = json.loads(caminho.read_text(encoding="utf-8-sig"))
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


def save(perfil, caminho=None):
    """Grava um perfil em JSON e devolve o caminho final.

    Chamar validate antes de gravar e o que impede a interface de salvar
    um perfil que a CLI recusaria em seguida. As chaves _path e _base_dir
    sao informacoes de leitura, nao fazem parte do arquivo.
    """
    destino = Path(caminho) if caminho else perfil.get("_path")

    if not destino:
        raise ProfileError("Diga onde salvar: o perfil nao tem caminho de origem.")

    limpo = {
        chave: valor
        for chave, valor in perfil.items()
        if chave not in ("_path", "_base_dir")
    }
    validate(dict(limpo, _path=str(destino), _base_dir=str(Path(destino).parent)))

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    texto = json.dumps(limpo, indent=2, ensure_ascii=False) + "\n"
    # UTF-8 sem BOM: o PowerShell 5.1 le esse arquivo igual, e o proprio
    # PowerShell 5.1 nao e quem vai reescrever ele. Escrever em arquivo
    # temporario e trocar no lugar evita deixar um perfil pela metade se o
    # programa fechar no meio da escrita.
    temporario = destino.with_name(destino.name + ".tmp")
    temporario.write_text(texto, encoding="utf-8")
    os.replace(temporario, destino)

    return destino


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
