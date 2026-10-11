"""Prepara imagens geradas para o jogo.

Uso:
  python ferramentas/preparar_arte.py ENTRADA SAIDA --altura 64      sprite: recorta o vazio e reduz
  python ferramentas/preparar_arte.py ENTRADA SAIDA --ladrilho 256   chão: quadrado que se repete sem emenda
  python ferramentas/preparar_arte.py ENTRADA SAIDA --tela 1280x720  fundo: cobre a tela inteira
"""
import argparse
from pathlib import Path

from PIL import Image, ImageChops


def recortar_vazio(img):
    alfa = img.getchannel("A").point(lambda a: 255 if a > 8 else 0)
    caixa = alfa.getbbox()
    return img.crop(caixa) if caixa else img


def reduzir_para_altura(img, altura):
    largura = max(1, round(img.width * altura / img.height))
    return img.resize((largura, altura), Image.LANCZOS)


def tornar_ladrilhavel(img, lado):
    img = img.convert("RGB").resize((lado, lado), Image.LANCZOS)
    rolada = ImageChops.offset(img, lado // 2, lado // 2)
    mascara = Image.new("L", (lado, lado))
    metade = lado / 2
    pixels = mascara.load()
    for y in range(lado):
        for x in range(lado):
            perto_da_borda = max(abs(x - metade), abs(y - metade)) / metade
            pixels[x, y] = int(255 * max(0.0, min(1.0, (perto_da_borda - 0.55) / 0.4)))
    return Image.composite(rolada, img, mascara)


def cobrir_tela(img, largura, altura):
    img = img.convert("RGB")
    fator = max(largura / img.width, altura / img.height)
    img = img.resize((round(img.width * fator), round(img.height * fator)), Image.LANCZOS)
    esquerda = (img.width - largura) // 2
    topo = (img.height - altura) // 2
    return img.crop((esquerda, topo, esquerda + largura, topo + altura))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("entrada")
    p.add_argument("saida")
    p.add_argument("--altura", type=int)
    p.add_argument("--ladrilho", type=int)
    p.add_argument("--tela")
    a = p.parse_args()
    img = Image.open(a.entrada)
    if a.ladrilho:
        img = tornar_ladrilhavel(img, a.ladrilho)
    elif a.tela:
        largura, altura = (int(v) for v in a.tela.lower().split("x"))
        img = cobrir_tela(img, largura, altura)
    else:
        img = recortar_vazio(img.convert("RGBA"))
        if a.altura:
            img = reduzir_para_altura(img, a.altura)
    Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
    img.save(a.saida)
    print(f"{a.saida}: {img.width}x{img.height}")


if __name__ == "__main__":
    main()
