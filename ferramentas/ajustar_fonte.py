"""Abre mais o "C" da Pixelify Sans, que no original quase fecha e parece um "O" ("Cola" lia "Oola").

A Pixelify Sans é OFL; a versão modificada ganha outro nome de família ("Pixelify Sans UFJ"),
como a licença pede. Uso: python ferramentas/ajustar_fonte.py
O "Ç" é composto do "C" com a cedilha, então muda junto.
"""
from pathlib import Path

from fontTools.ttLib import TTFont

PASTA = Path(__file__).resolve().parent.parent / "assets" / "fontes"
ORIGINAIS = {"pixelify-sans-latin-700-normal.ttf": "pixelify-sans-ufj-700.ttf",
             "pixelify-sans-latin-500-normal.ttf": "pixelify-sans-ufj-500.ttf"}
ABERTURA = (0.36, 0.68)      # a abertura do C vai de 36% a 68% da altura da letra


def abrir_c(fonte):
    glifo = fonte["glyf"][fonte.getBestCmap()[ord("C")]]
    coordenadas = glifo.coordinates
    ys = sorted({y for _, y in coordenadas})
    base, topo = ys[0], ys[-1]
    direita = max(x for x, _ in coordenadas)
    # os dois "y" da abertura são os que aparecem na borda direita sem ser o canto de cima nem o de baixo
    meio = sorted({y for x, y in coordenadas if x == direita} - {min(y for x, y in coordenadas if x == direita),
                                                                  max(y for x, y in coordenadas if x == direita)})
    if len(meio) != 2:
        raise ValueError(f"forma do C inesperada: {meio}")
    novo_baixo = round(base + (topo - base) * ABERTURA[0])
    novo_alto = round(base + (topo - base) * ABERTURA[1])
    for i, (x, y) in enumerate(coordenadas):
        if y == meio[0]:
            coordenadas[i] = (x, novo_baixo)
        elif y == meio[1]:
            coordenadas[i] = (x, novo_alto)


def renomear(fonte):
    for registro in fonte["name"].names:
        if registro.nameID in (1, 3, 4, 6, 16):
            texto = registro.toUnicode().replace("Pixelify Sans", "Pixelify Sans UFJ").replace("PixelifySans",
                                                                                                "PixelifySansUFJ")
            registro.string = texto


def main():
    for original, novo in ORIGINAIS.items():
        fonte = TTFont(PASTA / original)
        abrir_c(fonte)
        renomear(fonte)
        fonte.save(PASTA / novo)
        print(f"{original} -> {novo}")


if __name__ == "__main__":
    main()
