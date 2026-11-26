"""Deixa um inimigo pequeno mais fácil de ver: amplia as tiras dele e põe um contorno escuro em volta.

Uso: python ferramentas/destacar_sprite.py PASTA FATOR      (ex.: mouse 1.6)
Mexe em assets/sprites/<PASTA>/*.png e em assets/sprites/<PASTA>.png. Rode uma vez só por pasta:
cada execução amplia de novo.
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

SPRITES = Path(__file__).resolve().parent.parent / "assets" / "sprites"
CONTORNO = (26, 22, 34)
GROSSURA = 2


def destacar(quadro, fator):
    maior = quadro.resize((round(quadro.width * fator), round(quadro.height * fator)), Image.LANCZOS)
    tela = Image.new("RGBA", (maior.width + 2 * GROSSURA, maior.height + 2 * GROSSURA), (0, 0, 0, 0))
    tela.alpha_composite(maior, (GROSSURA, GROSSURA))
    alfa = tela.getchannel("A").point(lambda v: 255 if v > 90 else 0)
    borda = ImageChops.subtract(alfa.filter(ImageFilter.MaxFilter(2 * GROSSURA + 1)), alfa)
    contorno = Image.new("RGBA", tela.size, (*CONTORNO, 255))
    contorno.putalpha(borda)
    contorno.alpha_composite(tela)
    return contorno


def main():
    pasta, fator = sys.argv[1], float(sys.argv[2])
    arquivos = sorted((SPRITES / pasta).glob("*.png")) + [SPRITES / f"{pasta}.png"]
    for arquivo in arquivos:
        if not arquivo.is_file():
            continue
        achado = re.fullmatch(r".+-(\d+)", arquivo.stem)
        quadros = int(achado.group(1)) if achado else 1
        tira = Image.open(arquivo).convert("RGBA")
        largura = tira.width // quadros
        novos = [destacar(tira.crop((i * largura, 0, (i + 1) * largura, tira.height)), fator) for i in range(quadros)]
        saida = Image.new("RGBA", (novos[0].width * quadros, novos[0].height), (0, 0, 0, 0))
        for i, novo in enumerate(novos):
            saida.alpha_composite(novo, (i * novo.width, 0))
        saida.save(arquivo)
        print(arquivo.relative_to(SPRITES), saida.size)


if __name__ == "__main__":
    main()
