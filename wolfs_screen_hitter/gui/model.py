"""Modelo do perfil: campos, leitura e escrita, sem interface grafica.

Este modulo nao importa tkinter de proposito. Ele sabe apenas o que um
perfil tem, que valor padrao cada campo tem, e como transformar um dicionario
em texto para a tela e o texto de volta em dicionario. A interface grafica
desenha os campos declarados aqui e delega a conversao.

Um campo e um caminho pontilhado, como "target.bright.v_min", e um tipo.
Isso mantem as quatro familias (janela, regiao, alvo, cursor) no mesmo
formato, entao adicionar um campo e uma linha so.
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


class ErroDeCampo(ValueError):
    """Valor invalido em um campo do formulario.

    Guardar qual campo falhou permite que a interface marque a entrada
    errada em vez de so dizer que algo deu errado.
    """

    def __init__(self, caminho, mensagem):
        super().__init__(f"{caminho}: {mensagem}")
        self.caminho = caminho
        self.mensagem = mensagem


@dataclass(frozen=True)
class Campo:
    """Um campo editavel do perfil."""

    caminho: str
    rotulo: str
    tipo: str
    padrao: Any = None
    opcoes: tuple = ()
    dica: str = ""
    minimo: float = None
    maximo: float = None
    # Quando preenchido, o campo so aparece se este predicado for verdadeiro.
    aparece: tuple = ()
    # Como o campo se escolhe na tela, quando digitar o caminho na mao e
    # ruim. Por enquanto so "arquivo", que e o seletor de PNG. Fica
    # declarado aqui, e nao no componente, porque e o perfil que diz que
    # aquele caminho e um arquivo -- a tela so desenha o botao.
    seletor: str = ""

    def visivel(self, contexto):
        return all(PERFILADO[chave](contexto) for chave, _ in self.aparece)


# Contexto que decide quais grupos e campos aparecem. A interface monta esse
# dicionario a cada mudanca e redesenha a partir dele.
def contexto_de(perfil):
    perfil = perfil or {}
    regiao = perfil.get("region") or {}
    ponteiro = perfil.get("pointer") or {}
    return {
        "detector": perfil.get("detector") or "shape",
        "regiao": regiao.get("mode", "window"),
        "cursor": ponteiro.get("mode", "teleport"),
    }


PERFILADO = {
    "shape": lambda c: c["detector"] == "shape",
    "template": lambda c: c["detector"] == "template",
    "regiao_janela": lambda c: c["regiao"] == "window",
    "regiao_fixa": lambda c: c["regiao"] == "fixed",
    "cursor_smooth": lambda c: c["cursor"] == "smooth",
}


# --------------------------------------------------------------------------
# Grupos de campos. A ordem aqui e a ordem em que aparecem na tela.
# Cada grupo tem uma condicao propria, alem da condicao de cada campo:
# o grupo de alvo por forma so existe para o detector shape.
# --------------------------------------------------------------------------

GRUPOS = (
    (
        "identidade",
        "Perfil",
        None,
        (
            Campo("name", "Nome", "texto", "", dica="so para voce saber qual e qual"),
        ),
    ),
    (
        "janela",
        "Janela",
        None,
        (
            Campo(
                "window.title",
                "Titulo da janela",
                "texto",
                "",
                dica="vazio = qualquer janela. O casamento ignora maiusculas e e parcial",
            ),
            Campo("window.min_width", "Largura minima", "int", 200, minimo=0),
            Campo("window.min_height", "Altura minima", "int", 200, minimo=0),
        ),
    ),
    (
        "regiao",
        "Onde procurar",
        None,
        (
            Campo(
                "region.mode",
                "Regiao",
                "escolha",
                "window",
                opcoes=("window", "screen", "virtual", "fixed"),
                dica="window=janela, screen=tela principal, virtual=todo o desktop, fixed=retangulo",
            ),
            Campo(
                "region.margin",
                "Margem",
                "int",
                0,
                minimo=0,
                dica="so no modo window; corta as bordas de todos os lados",
                aparece=(("regiao_janela", True),),
            ),
            Campo("region.left", "Esquerda", "int", 0, aparece=(("regiao_fixa", True),)),
            Campo("region.top", "Topo", "int", 0, aparece=(("regiao_fixa", True),)),
            Campo("region.width", "Largura", "int", 1920, minimo=1, aparece=(("regiao_fixa", True),)),
            Campo("region.height", "Altura", "int", 1080, minimo=1, aparece=(("regiao_fixa", True),)),
        ),
    ),
    (
        "alvo_forma",
        "Alvo por cor",
        "shape",
        (
            Campo(
                "detector",
                "Detector",
                "escolha",
                "shape",
                opcoes=("shape", "template"),
                dica="shape=cor, template=imagem",
            ),
            Campo("target.bright.v_min", "Brilho minimo (claro)", "int", 150, minimo=0, maximo=255),
            Campo("target.bright.s_max", "Saturacao max (claro)", "int", 110, minimo=0, maximo=255),
            Campo("target.dark.v_max", "Brilho max (escuro)", "int", 90, minimo=0, maximo=255),
            Campo("target.dark.s_max", "Saturacao max (escuro)", "int", 110, minimo=0, maximo=255),
            # Padrao None quer dizer "desligado". Se a faixa HSV tivesse um
            # intervalo plausivel como padrao, o modelo acharia que o HSV
            # esta em uso e apagaria o bright, que e justamente o que o
            # perfil esta usando.
            Campo("target.hsv_min.0", "Matiz min", "int", None, minimo=0, maximo=179, dica="faixa HSV, opcional"),
            Campo("target.hsv_min.1", "Saturacao min", "int", None, minimo=0, maximo=255),
            Campo("target.hsv_min.2", "Valor min", "int", None, minimo=0, maximo=255),
            Campo("target.hsv_max.0", "Matiz max", "int", None, minimo=0, maximo=179),
            Campo("target.hsv_max.1", "Saturacao max", "int", None, minimo=0, maximo=255),
            Campo("target.hsv_max.2", "Valor max", "int", None, minimo=0, maximo=255),
            Campo("target.size.min", "Lado minimo", "int", 30, minimo=0),
            Campo("target.size.max", "Lado maximo", "int", 400, minimo=0),
            Campo("target.aspect.min", "Proporcao min", "float", 0.5, minimo=0.0, maximo=100.0),
            Campo("target.aspect.max", "Proporcao max", "float", 2.0, minimo=0.0, maximo=100.0),
            Campo("target.fill.min", "Preenchimento min", "float", 0.03, minimo=0.0, maximo=1.0),
            Campo("target.fill.max", "Preenchimento max", "float", 0.45, minimo=0.0, maximo=1.0),
            Campo("target.area_min", "Area minima", "int", 10, minimo=0),
            Campo("target.work_scale", "Escala de trabalho", "float", 0.5, minimo=0.05, maximo=1.0,
                  dica="menor = mais rapido e menos sensivel a ruido; maior = melhor para alvo pequeno"),
        ),
    ),
    (
        "alvo_template",
        "Alvo por imagem",
        "template",
        (
            Campo(
                "target.template",
                "Arquivo do template",
                "texto",
                "",
                dica="png do alvo. o nome fica guardado, nao a imagem",
                seletor="arquivo",
            ),
            Campo("target.threshold", "Limiar", "float", 0.8, minimo=0.0, maximo=1.0,
                  dica="0.80 por padrao; abaixe se a imagem nunca casar"),
            Campo("target.scale_min", "Escala minima", "float", 0.5, minimo=0.01),
            Campo("target.scale_max", "Escala maxima", "float", 2.0, minimo=0.01),
            Campo("target.scale_steps", "Passos de escala", "int", 12, minimo=1, maximo=60),
            Campo("target.invert", "Inverter", "bool", False,
                  dica="para glifo escuro sobre fundo claro"),
            Campo("target.work_scale", "Escala de trabalho", "float", 1.0, minimo=0.05, maximo=1.0,
                  dica="para template o padrao e 1.0; baixar deixa mais rapido e mais grosseiro"),
        ),
    ),
    (
        "cursor",
        "Cursor",
        None,
        (
            Campo(
                "pointer.mode",
                "Movimento",
                "escolha",
                "teleport",
                opcoes=("teleport", "smooth"),
                dica="teleport=instantaneo, smooth=caminho curvo com tremor",
            ),
            Campo("pointer.duration", "Duracao (s)", "float", 0.16, minimo=0.01, maximo=5.0,
                  aparece=(("cursor_smooth", True),)),
            Campo("pointer.jitter", "Tremor (px)", "float", 1.2, minimo=0.0, maximo=50.0,
                  aparece=(("cursor_smooth", True),)),
        ),
    ),
    (
        "controles",
        "Parada",
        None,
        (
            Campo("controls.corner_seconds", "Segundos no canto", "float", 1.0, minimo=0.0, maximo=60.0,
                  dica="Esc e F12 sempre param, isso e um extra"),
        ),
    ),
)


# Os dois grupos de alvo tem work_scale com padroes diferentes, 0.5 para
# forma e 1.0 para template, entao o mesmo caminho aparece duas vezes. Isso
# e de proposito: cada formulario mostra o seu. Mas a lista de campos usada
# para ler e escrever tem de ser unica, senao o campo e processado duas vezes
# e o dicionario de consulta fica com so o ultimo padrao.
CAMPOS = tuple(
    {campo.caminho: campo for _, _, _, grupo in GRUPOS for campo in grupo}.values()
)
CAMPOS_POR_CAMINHO = {campo.caminho: campo for campo in CAMPOS}

# Campos que gravam sempre, mesmo fora do grupo que esta visivel. Sem isso
# o proprio seletor do contexto some: "detector" mora no grupo "Alvo por cor",
# entao escolher template pulava o grupo e o perfil continuava em shape.
# "target.work_scale" entra aqui porque os dois detectores leem esse valor,
# ainda que cada formulario mostre o seu padrao.
SEMPRE = frozenset({"detector", "region.mode", "pointer.mode", "target.work_scale"})


# --------------------------------------------------------------------------
# Leitura e escrita por caminho pontilhado
# --------------------------------------------------------------------------


def caminho_partes(caminho):
    return caminho.split(".")


def pegar(perfil, caminho):
    """Le um valor por caminho, com o padrao do campo se nao existir."""
    no_caminho = perfil
    for parte in caminho_partes(caminho):
        if isinstance(no_caminho, dict):
            if parte not in no_caminho:
                return CAMPOS_POR_CAMINHO[caminho].padrao if caminho in CAMPOS_POR_CAMINHO else None
            no_caminho = no_caminho[parte]
        elif isinstance(no_caminho, list):
            indice = int(parte)
            if indice >= len(no_caminho):
                return CAMPOS_POR_CAMINHO[caminho].padrao
            no_caminho = no_caminho[indice]
        else:
            return None
    return no_caminho


def por(perfil, caminho, valor):
    """Escreve um valor por caminho, criando os blocos intermediarios.

    O proximo segmento decide o tipo do bloco: um segmento numerico cria
    lista, qualquer outro cria dicionario. E assim que "target.hsv_min.0"
    vira [h, s, v] sem o chamador precisar saber disso.
    """
    partes = caminho_partes(caminho)
    no_caminho = perfil

    for indice, parte in enumerate(partes[:-1]):
        if isinstance(no_caminho, list):
            no_caminho = no_caminho[int(parte)]
            continue
        proxima = partes[indice + 1]
        if not isinstance(no_caminho.get(parte), (dict, list)):
            no_caminho[parte] = [] if proxima.isdigit() else {}
        no_caminho = no_caminho[parte]

    ultima = partes[-1]
    if isinstance(no_caminho, list):
        indice = int(ultima)
        # A lista pode ainda ser curta: "target.hsv_min.2" chega antes de
        # ".0" quando o usuario digita, e precisa crescer em vez de estourar.
        while len(no_caminho) <= indice:
            no_caminho.append(0)
        no_caminho[indice] = valor
    else:
        no_caminho[ultima] = valor


# --------------------------------------------------------------------------
# Perfil -> texto, e texto -> perfil
# --------------------------------------------------------------------------


def para_texto(valor):
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "sim" if valor else "nao"
    if isinstance(valor, (list, tuple)):
        return ", ".join(str(v) for v in valor)
    return str(valor)


def de_texto(texto, tipo, caminho):
    """Converte o texto de um campo no valor tipado, com mensagem util."""
    texto = texto.strip()

    if tipo == "texto":
        return texto
    if tipo == "bool":
        return texto.lower() in ("1", "true", "sim", "s", "yes", "verdadeiro")
    if tipo == "escolha":
        return texto
    if tipo in ("int", "float"):
        if not texto:
            # Vazio em campo numerico e zero, nao erro: e assim que o
            # formulario se comporta quando o usuario limpa a caixa.
            return 0 if tipo == "int" else 0.0
        try:
            numero = int(texto) if tipo == "int" else float(texto.replace(",", "."))
        except ValueError:
            raise ErroDeCampo(
                caminho, f"esperava {'inteiro' if tipo == 'int' else 'numero'}, veio {texto!r}"
            ) from None
        return numero

    raise ErroDeCampo(caminho, f"tipo desconhecido {tipo!r}")


def perfil_para_campos(perfil):
    """Achata um perfil em {caminho: texto} para preencher as caixas."""
    return {campo.caminho: para_texto(pegar(perfil, campo.caminho)) for campo in CAMPOS}


def contexto_dos_campos(campos):
    """Deduz o contexto antes de gravar, porque detector, regiao e cursor
    sao eles mesmos campos do formulario.

    Sao so as tres chaves que algum filtro de PERFILADO le. Um caminho de
    template nao entra aqui: nada depende dele para aparecer ou sumir, e
    se entrasse, digitar o nome do arquivo reconstruiria o formulario
    inteiro uma vez so, sem nenhuma mudanca na tela.
    """
    return {
        "detector": (campos.get("detector") or "shape").strip() or "shape",
        "regiao": (campos.get("region.mode") or "window").strip() or "window",
        "cursor": (campos.get("pointer.mode") or "teleport").strip() or "teleport",
    }


def campos_ativos(contexto):
    """Os campos a gravar e conferir, uma vez cada, na ordem do formulario.

    "target.work_scale" aparece nos dois grupos de alvo, com padroes
    diferentes, porque cada detector tem o seu. Aqui ele vira um campo so, o
    do grupo que esta visivel, e cai no primeiro quando nenhum esta.
    """
    variantes = {}
    for _, _, condicao, grupo in GRUPOS:
        for campo in grupo:
            variantes.setdefault(campo.caminho, []).append((condicao, campo))

    ativos = []
    for opcoes in variantes.values():
        do_contexto = [c for cond, c in opcoes if cond is None or PERFILADO[cond](contexto)]
        if do_contexto:
            ativos.append(do_contexto[0])
        elif opcoes[0][1].caminho in SEMPRE:
            ativos.append(opcoes[0][1])
    return ativos


def campos_para_perfil(campos, base=None):
    """Monta um perfil a partir de {caminho: texto}, validando campo a campo.

    So grava o que o contexto atual mostra, e isso importa mais do que
    parece: em _mascara_forma a faixa HSV tem prioridade sobre bright e
    dark. Um perfil que carrega as duas coisas, com o HSV preenchido no
    padrao, para de usar bright sem ninguem perceber. Por isso o que nao
    pertence ao contexto e apagado, em vez de receber o valor padrao.
    """
    perfil = _copia(base) if base else {}
    contexto = contexto_dos_campos(campos)

    for campo in campos_ativos(contexto):
        if not campo.visivel(contexto):
            continue
        texto = campos.get(campo.caminho, "")
        if campo.tipo in ("int", "float") and not texto.strip():
            # Caixa vazia: usa o que ja estava no perfil, ou o padrao do
            # campo. Padrao None e o campo desligado, e nesse caso nao
            # escreve nada, para a chave nao nascer com zero.
            anterior = pegar(perfil, campo.caminho)
            if anterior is None and campo.padrao is None:
                continue
            texto = para_texto(anterior if anterior is not None else campo.padrao)
        valor = de_texto(texto, campo.tipo, campo.caminho)
        _conferir_limite(campo, valor)
        por(perfil, campo.caminho, valor)

    _consolidar_listas(perfil)

    # Titulo vazio e o mesmo que nao citar titulo nenhum.
    if not (perfil.get("window") or {}).get("title"):
        perfil.setdefault("window", {})["title"] = None

    # HSV e bright sao metodos alternativos de descrever a mesma coisa, e
    # dois ao mesmo tempo nao tem sentido: em _mascara_forma a faixa HSV tem
    # prioridade, entao um perfil com as duas usaria a faixa sem querer.
    _escolher_um_ou_outro(perfil, campos)
    _podar_alvo(perfil, contexto)
    _podar_regiao(perfil)
    _podar_cursor(perfil)

    return perfil


def _conferir_limite(campo, valor):
    if valor is None:
        return
    if campo.minimo is not None and valor < campo.minimo:
        raise ErroDeCampo(campo.caminho, f"minimo e {campo.minimo:g}, veio {valor:g}")
    if campo.maximo is not None and valor > campo.maximo:
        raise ErroDeCampo(campo.caminho, f"maximo e {campo.maximo:g}, veio {valor:g}")


def _consolidar_listas(perfil):
    alvo = perfil.get("target") or {}
    for chave in ("hsv_min", "hsv_max"):
        bruto = alvo.get(chave)
        if isinstance(bruto, dict):
            alvo[chave] = [bruto.get("0", 0), bruto.get("1", 0), bruto.get("2", 0)]


CAMPOS_HSV = tuple(
    campo.caminho for campo in CAMPOS if campo.caminho.startswith("target.hsv_")
)


def usa_faixa(campos):
    """True quando o usuario preencheu algum campo da faixa HSV."""
    return any((campos.get(caminho) or "").strip() for caminho in CAMPOS_HSV)


def _escolher_um_ou_outro(perfil, campos):
    alvo = perfil.get("target") or {}

    if usa_faixa(campos):
        alvo.pop("bright", None)
        alvo.pop("dark", None)
    else:
        alvo.pop("hsv_min", None)
        alvo.pop("hsv_max", None)


def _podar_alvo(perfil, contexto):
    """Cada detector le um conjunto proprio de campos, entao o do outro sai.

    Isso nao e so limpeza: em detect.py, detect_shape ignora threshold e
    scale_steps, e detect_template ignora size, aspect e fill. Deixar os dois
    no arquivo e um convite a editar o campo que nao esta sendo lido.
    """
    alvo = perfil.get("target") or {}
    do_shape = {"size", "aspect", "fill", "bright", "dark", "hsv_min", "hsv_max", "area_min"}
    do_template = {"template", "threshold", "scale_min", "scale_max", "scale_steps", "invert"}

    so_o_outro = do_shape if contexto["detector"] == "template" else do_template
    for chave in so_o_outro:
        alvo.pop(chave, None)


def _podar_regiao(perfil):
    """Deixa so os campos que o modo escolhido usa."""
    regiao = perfil.get("region") or {}
    modo = regiao.get("mode", "window")

    if modo != "window":
        regiao.pop("margin", None)
    if modo != "fixed":
        for chave in ("left", "top", "width", "height"):
            regiao.pop(chave, None)


def _podar_cursor(perfil):
    ponteiro = perfil.get("pointer") or {}
    if ponteiro.get("mode") != "smooth":
        ponteiro.pop("duration", None)
        ponteiro.pop("jitter", None)


def _copia(perfil):
    limpo = deepcopy(perfil)
    limpo.pop("_path", None)
    limpo.pop("_base_dir", None)
    return limpo


def perfil_padrao():
    """Um perfil novo e valido, montado a partir dos padroes dos campos.

    Os defaults sao os do contexto em que o perfil comeca, que e shape com
    regiao de janela: campo que so existe no outro contexto nao entra.
    """
    return campos_para_perfil(
        {campo.caminho: para_texto(campo.padrao) for campo in campos_ativos(contexto_de(None))}
    )


def visiveis(perfil):
    """Os (grupo, campo) que devem aparecer para o estado atual do perfil."""
    contexto = contexto_de(perfil)
    por_grupo = {}

    for identificador, titulo, condicao, grupo in GRUPOS:
        if condicao and not PERFILADO[condicao](contexto):
            por_grupo[identificador] = (titulo, [])
            continue
        por_grupo[identificador] = (titulo, [c for c in grupo if c.visivel(contexto)])

    return por_grupo


def visiveis_chat(perfil):
    """Versao achatada, so os caminhos visiveis."""
    return [c.caminho for _, lista in visiveis(perfil).values() for c in lista]
