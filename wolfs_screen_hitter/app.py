"""Loop principal e comandos de linha de comando."""

import argparse
import sys
import time
from pathlib import Path

import cv2

from . import __version__, detect, pointer, profiles, windows
from .capture import ScreenCapture
from .win import VK_ESCAPE, VK_F12, key_down


DEFAULT_INTERVALO = 0.002
GRUPO_AVISO = 25
CANTO_TOLERANCIA = 3
CANTO_TEMPO_PADRAO = 1.0


def _janela_do_perfil(perfil):
    janela_spec = perfil.get("window") or {}
    titulo = janela_spec.get("title")
    return windows.find_window(
        title=titulo,
        min_width=int(janela_spec.get("min_width", 200)),
        min_height=int(janela_spec.get("min_height", 200)),
    )


def _parar_por_canto(estado, duracao):
    """Diz se o mouse ficou parado no canto superior esquerdo."""
    x, y = pointer.position()
    no_canto = x <= CANTO_TOLERANCIA and y <= CANTO_TOLERANCIA

    if not no_canto:
        estado["canto"] = None
        return False

    agora = time.monotonic()

    if estado["canto"] is None:
        estado["canto"] = agora
        return False

    return (agora - estado["canto"]) >= duracao


def detectar_uma_vez(captura, perfil, janela):
    """Captura, detecta e devolve (detect, (x, y) globais) ou (None, None)."""
    regiao = windows.resolve_region(perfil.get("region"), janela)

    if regiao is None:
        return None, None

    quadro = captura.grab(regiao)
    achado = detect.detect(quadro, perfil)

    if achado is None:
        return None, regiao

    centro_x, centro_y = achado.center
    return achado, (regiao[0] + centro_x, regiao[1] + centro_y)


def salvar_debug(caminho, quadro, deteccao, regiao=None):
    """Grava o quadro com a caixa do alvo destacada."""
    imagem = quadro.copy()

    if regiao is not None:
        cv2.rectangle(
            imagem,
            (0, 0),
            (regiao[2] - 1, regiao[3] - 1),
            (0, 255, 255),
            1,
        )

    if deteccao is not None:
        cv2.rectangle(
            imagem,
            (deteccao.x, deteccao.y),
            (deteccao.x + deteccao.width, deteccao.y + deteccao.height),
            (0, 255, 0),
            2,
        )
        cv2.drawMarker(
            imagem,
            (int(deteccao.center[0]), int(deteccao.center[1])),
            (0, 255, 0),
            cv2.MARKER_CROSS,
            18,
            1,
        )
        cv2.putText(
            imagem,
            f"{deteccao.score:.2f}",
            (deteccao.x, max(12, deteccao.y - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(destino), imagem)
    return destino


def rodar_perfil(caminho_perfil, seguir=True, intervalo=DEFAULT_INTERVALO):
    """Executa o loop de deteccao ate o usuario parar."""
    perfil = profiles.load(caminho_perfil)
    resumo = profiles.describe(perfil)
    controle = perfil.get("controls") or {}
    canto_duracao = float(controle.get("corner_seconds", CANTO_TEMPO_PADRAO))
    captura = ScreenCapture()

    print(f"WolfsScreenHitter {__version__}")
    print(f"Perfil : {resumo['name']} [{caminho_perfil}]")
    print(f"Alvo   : detector={resumo['detector']} regiao={resumo['region']} janela={resumo['window']}")
    print(f"Cursor : {resumo['pointer']}")
    print("Pare com Esc, F12, ou mouse parado no canto superior esquerdo.")
    print("O clique e manual: este programa so posiciona o cursor.\n")

    estado = {"canto": None}
    ultimo_aviso = None
    sem_janela = False
    sem_permissao = False
    capturas = 0

    try:
        while True:
            if key_down(VK_ESCAPE) or key_down(VK_F12):
                print("Encerrado pelo usuario.")
                break

            if _parar_por_canto(estado, canto_duracao):
                print("Encerrado: mouse no canto.")
                break

            janela = _janela_do_perfil(perfil)

            if janela is None:
                if not sem_janela:
                    print("Aguardando a janela...")
                    sem_janela = True
                time.sleep(0.2)
                continue

            sem_janela = False
            capturas += 1
            deteccao, destino = detectar_uma_vez(captura, perfil, janela)

            if deteccao is not None and destino is not None:
                alvo_x, alvo_y = destino

                if seguir:
                    if not pointer.aplicar(alvo_x, alvo_y, perfil.get("pointer")):
                        if not sem_permissao:
                            print(
                                "O Windows recusou o movimento do cursor. "
                                "A deteccao continua funcionando, mas o mouse "
                                "nao vai obedecer. Normalmente e privilegio: "
                                "abra o terminal como administrador, ou fora de "
                                "um terminal elevado."
                            )
                            sem_permissao = True
                    else:
                        sem_permissao = False

                grupo = (
                    int(alvo_x) // GRUPO_AVISO,
                    int(alvo_y) // GRUPO_AVISO,
                )

                if grupo != ultimo_aviso:
                    print(
                        f"Alvo em ({alvo_x:.0f}, {alvo_y:.0f}) "
                        f"[{deteccao.kind} {deteccao.score:.2f}]"
                    )
                    ultimo_aviso = grupo

            time.sleep(intervalo)
    except KeyboardInterrupt:
        print("Encerrado pelo usuario.")
    finally:
        captura.close()
        print(f"Capturas realizadas: {capturas}")


def comando_check(caminho_perfil, saida=None, tentativas=40, espera=0.05):
    """Procura o alvo uma unica vez e reporta, sem mover o mouse."""
    perfil = profiles.load(caminho_perfil)
    janela = _janela_do_perfil(perfil)
    captura = ScreenCapture()
    regiao = windows.resolve_region(perfil.get("region"), janela)

    print(f"Perfil: {perfil.get('name')} [{caminho_perfil}]")

    if janela is None:
        print("Janela nao encontrada; usando a regiao do perfil.")
    else:
        print(f"Janela: '{janela.title}' {janela.width}x{janela.height}")

    if regiao is None:
        modo = (perfil.get("region") or {}).get("mode", "window")

        if modo == "window":
            print(
                "Regiao dependia de uma janela que nao foi encontrada. "
                "Abra o programa alvo, ajuste 'window.title' no perfil, "
                "ou use 'region.mode' como 'screen'/'virtual'."
            )
        else:
            print("Regiao invalida: confira os valores de 'region' no perfil.")

        captura.close()
        return 2

    print(f"Regiao: x={regiao[0]} y={regiao[1]} {regiao[2]}x{regiao[3]}")

    try:
        achado = None

        for _ in range(max(1, tentativas)):
            achado, destino = detectar_uma_vez(captura, perfil, janela)

            if achado is not None:
                print(f"DETECTADO: {achado.describe()}")
                print(f"Cursor iria para ({destino[0]:.0f}, {destino[1]:.0f})")
                break

            time.sleep(espera)
        else:
            print("NAO DETECTADO em nenhuma tentativa.")

        if saida:
            quadro = captura.grab(regiao)
            destino_arquivo = salvar_debug(saida, quadro, achado, regiao)
            print(f"Debug salvo em {destino_arquivo}")

        return 0 if achado is not None else 1
    finally:
        captura.close()


def comando_capture(saida, espera=0.0):
    """Salva a tela inteira (ou a janela mais ativa)."""
    if espera > 0:
        time.sleep(espera)

    regiao = windows.screen()
    janela = windows.find_window()

    if janela is not None and janela.left >= 0:
        regiao = (janela.left, janela.top, janela.width, janela.height)

    with ScreenCapture() as captura:
        quadro = captura.grab(regiao)

    destino = Path(saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(destino), quadro)
    print(f"Capturado {quadro.shape[1]}x{quadro.shape[0]} em {destino}")
    return 0


def comando_crop(origem, destino, x, y, largura, altura):
    """Recorta um template de letra ou simbolo a partir de uma captura."""
    imagem = cv2.imread(str(origem))

    if imagem is None:
        print(f"Imagem ilegivel: {origem}")
        return 1

    alt_tela, larg_tela = imagem.shape[:2]
    x1 = max(0, int(x))
    y1 = max(0, int(y))
    x2 = min(larg_tela, int(x) + int(largura))
    y2 = min(alt_tela, int(y) + int(altura))

    if x2 - x1 < 1 or y2 - y1 < 1:
        print("Recorte invalido.")
        return 1

    recorte = imagem[y1:y2, x1:x2]
    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(destino_path), recorte)
    print(f"Template {recorte.shape[1]}x{recorte.shape[0]} salvo em {destino_path}")
    return 0


def comando_list_windows():
    for janela in sorted(
        windows.list_windows(min_width=120, min_height=80),
        key=lambda w: w.area(),
        reverse=True,
    ):
        print(
            f"{janela.handle:>10}  {janela.width:>5}x{janela.height:<5} "
            f"@({janela.left},{janela.top})  {janela.title}"
        )
    return 0


def comando_list_profiles(diretorio=None):
    encontrados = profiles.list_profiles(diretorio)

    if not encontrados:
        print("Nenhum perfil encontrado.")
        return 1

    for caminho in encontrados:
        try:
            resumo = profiles.describe(profiles.load(caminho))
            print(
                f"{caminho.name:<28} {resumo['detector']:<9} "
                f"janela={resumo['window']:<18} {resumo['detail']}"
            )
        except profiles.ProfileError as erro:
            print(f"{caminho.name:<28} INVALIDO: {erro}")
    return 0


def _construir_parser():
    parser = argparse.ArgumentParser(
        prog="wolfs-screen-hitter",
        description=(
            "Aponta o cursor para um alvo visual encontrado na tela. "
            "O clique e sempre manual."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)

    sub = parser.add_subparsers(dest="comando", required=True)

    rodar = sub.add_parser("run", help="segue o alvo e posiciona o cursor")
    rodar.add_argument("perfil", help="caminho do perfil JSON")
    rodar.add_argument(
        "--dry-run",
        action="store_true",
        help="detecta e imprime, sem mover o mouse",
    )
    rodar.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVALO,
        help="pausa entre quadros, em segundos (padrao 0.002)",
    )

    check = sub.add_parser("check", help="procura o alvo uma vez e reporta")
    check.add_argument("perfil", help="caminho do perfil JSON")
    check.add_argument("--debug", help="salva a imagem com a caixa destacada")
    check.add_argument("--tentativas", type=int, default=40)
    check.add_argument("--espera", type=float, default=0.05)

    capturar = sub.add_parser("capture", help="salva uma captura de tela")
    capturar.add_argument("saida", help="arquivo .png de destino")
    capturar.add_argument("--delay", type=float, default=0.0)

    crop = sub.add_parser("crop", help="recorta um template de uma captura")
    crop.add_argument("origem", help="imagem de origem")
    crop.add_argument("destino", help="template .png de destino")
    crop.add_argument("x", type=int)
    crop.add_argument("y", type=int)
    crop.add_argument("largura", type=int)
    crop.add_argument("altura", type=int)

    listar = sub.add_parser("list-windows", help="lista janelas visiveis")
    listar.set_defaults(_funcao=comando_list_windows)

    perfis = sub.add_parser("list-profiles", help="lista perfis disponiveis")
    perfis.add_argument("--dir", help="diretorio de perfis")

    return parser


def main(argv=None):
    parser = _construir_parser()
    args = parser.parse_args(argv)

    try:
        return _despachar(args, parser)
    except profiles.ProfileError as erro:
        # Perfil invalido e erro de digitacao do usuario, nao um bug: mostra
        # a mensagem limpa em vez de entregar uma stack trace.
        print(f"Perfil invalido: {erro}")
        return 2


def _despachar(args, parser):
    if args.comando == "run":
        if args.dry_run:
            return comando_check(args.perfil)
        return rodar_perfil(args.perfil, seguir=True, intervalo=args.interval)

    if args.comando == "check":
        return comando_check(
            args.perfil,
            saida=args.debug,
            tentativas=args.tentativas,
            espera=args.espera,
        )

    if args.comando == "capture":
        return comando_capture(args.saida, args.delay)

    if args.comando == "crop":
        return comando_crop(
            args.origem,
            args.destino,
            args.x,
            args.y,
            args.largura,
            args.altura,
        )

    if args.comando == "list-windows":
        return comando_list_windows()

    if args.comando == "list-profiles":
        return comando_list_profiles(args.dir)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
