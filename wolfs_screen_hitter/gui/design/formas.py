"""Primitivas geometricas desenhadas no Canvas.

O Tk nao tem canto arredondado, sombra difusa nem rotacao de forma, e o
design system nao quer nenhum dos tres. O que ele quer e circulo, quadrado
e triangulo perfeito, contorno preto grosso e cor chapada. Tudo isso o
Canvas faz de forma exata, entao e no Canvas que as formas nascem.

Estas funcoes desenham sempre em coordenadas absolutas do canvas e devolvem
o id do item, para quem precisar mover ou apagar.
"""

from . import tokens


def circulo(canvas, x, y, raio, preenchimento="", contorno=tokens.PRETO, espessura=2):
    return canvas.create_oval(
        x - raio,
        y - raio,
        x + raio,
        y + raio,
        fill=preenchimento,
        outline=contorno,
        width=espessura,
    )


def quadrado(canvas, x, y, lado, preenchimento="", contorno=tokens.PRETO, espessura=2):
    return canvas.create_rectangle(
        x - lado / 2,
        y - lado / 2,
        x + lado / 2,
        y + lado / 2,
        fill=preenchimento,
        outline=contorno,
        width=espessura,
    )


def triangulo(canvas, x, y, lado, preenchimento="", contorno=tokens.PRETO, espessura=2):
    """Triangulo equilatero com a base embaixo, centrado em (x, y)."""
    altura = lado * (3 ** 0.5) / 2
    return canvas.create_polygon(
        x,
        y - altura * 2 / 3,
        x - lado / 2,
        y + altura / 3,
        x + lado / 2,
        y + altura / 3,
        fill=preenchimento,
        outline=contorno,
        width=espessura,
    )


def losango(canvas, x, y, lado, preenchimento="", contorno=tokens.PRETO, espessura=2):
    """Quadrado girado 45 graus, o mesmo ngulo dos cartazes de 1925."""
    meio = lado / 2
    return canvas.create_polygon(
        x,
        y - meio,
        x + meio,
        y,
        x,
        y + meio,
        x - meio,
        y,
        fill=preenchimento,
        outline=contorno,
        width=espessura,
    )


def marcador(canvas, x, y, forma, cor, lado=8, espessura=2):
    """O marcador de canto dos cards: circulo, quadrado, triangulo ou losango."""
    desenha = {
        "circulo": lambda: circulo(canvas, x, y, lado / 2, cor, tokens.PRETO, espessura),
        "quadrado": lambda: quadrado(canvas, x, y, lado, cor, tokens.PRETO, espessura),
        "triangulo": lambda: triangulo(canvas, x, y, lado, cor, tokens.PRETO, espessura),
        "losango": lambda: losango(canvas, x, y, lado, cor, tokens.PRETO, espessura),
    }
    return desenha.get(forma, desenha["quadrado"])()


def assinatura(canvas, x, y, lado=14, espessura=2):
    """Os tres simbolos classicos: circulo vermelho, quadrado azul, triangulo amarelo.

    E a assinatura visual do produto. Fica no cabecalho, e o que faz a tela
    ser reconhecivel antes de qualquer texto ser lido.
    """
    passo = lado * 1.6
    circulo(canvas, x, y, lado / 2, tokens.VERMELHO, tokens.PRETO, espessura)
    quadrado(canvas, x + passo, y, lado, tokens.AZUL, tokens.PRETO, espessura)
    triangulo(canvas, x + passo * 2, y, lado, tokens.AMARELO, tokens.PRETO, espessura)
    return passo * 2 + lado
