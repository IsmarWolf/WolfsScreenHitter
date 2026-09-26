"""Camadas de Win32 usadas pelo pacote."""

import ctypes
from ctypes import wintypes


user32 = ctypes.windll.user32

SM_CXSCREEN = 0
SM_CYSCREEN = 1
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000
VK_ESCAPE = 0x1B
VK_F12 = 0x7B


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("dados",)
    _fields_ = [
        ("tipo", wintypes.DWORD),
        ("dados", _INPUTUNION),
    ]


def cursor_position():
    point = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def active_window_handle():
    return int(user32.GetForegroundWindow() or 0)


def key_down(vk):
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def _enviar(flags, x=0, y=0):
    entrada = _INPUT(tipo=INPUT_MOUSE)
    entrada.mi = _MOUSEINPUT(
        dx=x,
        dy=y,
        mouseData=0,
        dwFlags=flags,
        time=0,
        dwExtraInfo=None,
    )
    enviados = ctypes.c_ulong(0)
    user32.SendInput(1, ctypes.byref(entrada), ctypes.sizeof(_INPUT))
    return enviados.value


def move_to(x, y):
    """Move o cursor para coordenadas absolutas da area virtual."""
    esquerda = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    topo = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    largura = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    altura = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)

    if largura <= 0 or altura <= 0:
        return False

    normalizado_x = round((x - esquerda) * 65535 / max(1, largura - 1))
    normalizado_y = round((y - topo) * 65535 / max(1, altura - 1))
    normalizado_x = max(0, min(65535, normalizado_x))
    normalizado_y = max(0, min(65535, normalizado_y))

    return (
        _enviar(
            MOUSEEVENTF_MOVE
            | MOUSEEVENTF_ABSOLUTE
            | MOUSEEVENTF_VIRTUALDESK,
            normalizado_x,
            normalizado_y,
        )
        == 1
    )
