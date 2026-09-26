"""Descoberta de janelas e resolucao de regioes de busca."""

import ctypes
from ctypes import wintypes
from dataclasses import dataclass

from . import win


@dataclass(frozen=True)
class Window:
    handle: int
    title: str
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height

    def area(self):
        return self.width * self.height


def _window_text(handle):
    length = win.user32.GetWindowTextLengthW(handle)
    buffer = ctypes.create_unicode_buffer(length + 1)
    win.user32.GetWindowTextW(handle, buffer, length + 1)
    return buffer.value


def list_windows(min_width=0, min_height=0, visible_only=True):
    """Enumera as janelas de nivel superior que tem titulo."""
    encontradas = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _callback(handle, _lparam):
        if visible_only and not win.user32.IsWindowVisible(handle):
            return True

        titulo = _window_text(handle).strip()

        if not titulo:
            return True

        rect = wintypes.RECT()
        win.user32.GetWindowRect(handle, ctypes.byref(rect))
        largura = rect.right - rect.left
        altura = rect.bottom - rect.top

        if largura < min_width or altura < min_height:
            return True

        encontradas.append(
            Window(
                handle=int(handle),
                title=titulo,
                left=rect.left,
                top=rect.top,
                width=largura,
                height=altura,
            )
        )
        return True

    win.user32.EnumWindows(_callback, 0)
    return encontradas


def find_window(title=None, min_width=200, min_height=200):
    """Procura a janela pelo titulo; sem titulo, devolve a maior."""
    candidatas = list_windows(
        min_width=min_width,
        min_height=min_height,
    )

    if not candidatas:
        return None

    if title:
        alvo = title.casefold()
        filtradas = [w for w in candidatas if alvo in w.title.casefold()]

        if not filtradas:
            return None
    else:
        filtradas = candidatas

    ativa = win.active_window_handle()

    for janela in filtradas:
        if janela.handle == ativa:
            return janela

    return max(filtradas, key=Window.area)


def virtual_screen():
    """Retorna (left, top, width, height) da area virtual de trabalho."""
    largura = win.user32.GetSystemMetrics(win.SM_CXVIRTUALSCREEN)
    altura = win.user32.GetSystemMetrics(win.SM_CYVIRTUALSCREEN)
    esquerda = win.user32.GetSystemMetrics(win.SM_XVIRTUALSCREEN)
    topo = win.user32.GetSystemMetrics(win.SM_YVIRTUALSCREEN)
    return esquerda, topo, largura, altura


def screen():
    """Retorna (left, top, width, height) da tela primaria."""
    return (
        0,
        0,
        win.user32.GetSystemMetrics(win.SM_CXSCREEN),
        win.user32.GetSystemMetrics(win.SM_CYSCREEN),
    )


def resolve_region(spec, window=None):
    """Converte o bloco 'region' de um perfil em (left, top, width, height)."""
    spec = spec or {}
    modo = spec.get("mode", "window")

    if modo == "fixed":
        return (
            int(spec["left"]),
            int(spec["top"]),
            int(spec["width"]),
            int(spec["height"]),
        )

    if modo == "screen":
        return screen()

    if modo == "virtual":
        return virtual_screen()

    if modo == "window":
        if window is None:
            return None

        margem = int(spec.get("margin", 0))
        esquerda, topo, largura, altura = virtual_screen()
        direita = esquerda + largura
        baixo = topo + altura

        esq = max(esquerda, window.left + margem)
        topo_ = max(topo, window.top + margem)
        dir = min(direita, window.right - margem)
        bax = min(baixo, window.bottom - margem)

        largura = dir - esq
        altura = bax - topo_

        if largura < 16 or altura < 16:
            return None

        return esq, topo_, largura, altura

    raise ValueError(f"Modo de regiao desconhecido: {modo!r}")
