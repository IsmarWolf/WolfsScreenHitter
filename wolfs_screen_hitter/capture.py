"""Captura de tela com DXGI e queda para mss."""

import numpy as np


class ScreenCapture:
    """Captura regioes da tela.

    Usa DXGI (dxcam) por ser o caminho mais rapido e cai para mss
    automaticamente se a DXGI nao estiver disponivel.
    """

    def __init__(self):
        self._camera = None
        self._tela = None
        self._tentou_dxgi = False

    @property
    def backend(self):
        self._garantir_camera()
        return "dxcam" if self._camera else "mss"

    def _garantir_camera(self):
        if not self._tentou_dxgi:
            self._tentou_dxgi = True
            try:
                import dxcam

                self._camera = dxcam.create(output_color="BGR") or False
            except Exception:
                self._camera = False

    def _garantir_mss(self):
        if self._tela is None:
            import mss

            factory = getattr(mss, "MSS", None) or mss.mss
            self._tela = factory()

    def grab(self, regiao):
        """Retorna a regiao (left, top, width, height) como array BGR."""
        esquerda, topo, largura, altura = regiao

        if largura <= 0 or altura <= 0:
            raise ValueError("Regiao com tamanho invalido.")

        self._garantir_camera()

        if self._camera:
            try:
                imagem = self._camera.grab(
                    region=(esquerda, topo, esquerda + largura, topo + altura),
                    new_frame_only=False,
                )
                if imagem is not None:
                    return imagem
            except Exception:
                pass

        self._garantir_mss()
        imagem = self._tela.grab(
            {
                "left": esquerda,
                "top": topo,
                "width": largura,
                "height": altura,
            }
        )
        return np.asarray(imagem)[:, :, :3]

    def close(self):
        if self._camera:
            try:
                self._camera.release()
            except Exception:
                pass
            self._camera = False

        if self._tela is not None:
            try:
                self._tela.close()
            except Exception:
                pass
            self._tela = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
