"""Roda a interface grafica: python -m wolfs_screen_hitter.gui"""

import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m wolfs_screen_hitter.gui",
        description="Janela para editar perfis do WolfsScreenHitter.",
    )
    parser.add_argument(
        "--dir",
        help="diretorio de perfis (padrao: a pasta profiles do projeto)",
    )
    args = parser.parse_args(argv)

    # O import e aqui dentro de proposito: um erro de tela nao pode virar
    # erro de import para quem so quer o modelo, nem para os testes.
    try:
        from .app import Aplicacao
    except ImportError as erro:
        print(f"Nao foi possivel abrir a interface: {erro}", file=sys.stderr)
        return 1

    Aplicacao(args.dir).mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
