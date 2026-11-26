"""Prepara o detalhe do chão que não é gramado: asfalto das ruas e terra batida, e o ladrilho da lavoura.

Como a grama (montar_grama.py), cada textura vira duas imagens que o jogo soma e subtrai por cima do
chão já ampliado, só onde o chão tem a cor daquele piso. Assim o desenho do mapa não muda: ganha grão,
pedrinhas, rachaduras e, na lavoura, as fileiras da plantação.

Também recorta os enfeites da lavoura (espantalhos, fardos, marcas de disco voador...), que o jogo
espalha pela plantação para ela não ficar uniforme.

Entradas em nova_arte/_bruto/: chao_asfalto.png, chao_terra.png, lavoura_plantas_12.png
(os pés de soja, milho e trigo em 3/4, que formam as fileiras com volume) e lavoura_enfeites_12.png.
Uso: python ferramentas/montar_chao.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from montar_grama import BRUTO, SAIDA, ladrilho
from pixelizar import dividir, linhas

# nome: (força do contraste que vai para o chão, desfoque que tira o grão miúdo). Valores baixos de
# propósito: com contraste cheio a tela ficava cheia de ruído e os inimigos sumiam no chão.
PISOS = {"asfalto": (0.45, 1.6), "terra": (0.40, 1.4)}
LADO_DA_LAVOURA = 768
PLANTAS = (("soja", 40), ("milho", 92), ("trigo", 56))      # cultura e altura do pé na tela, na ordem da folha
FORA_DE_USO = ("aboboras", "espantalho_abobora", "caixote_de_legumes")   # a lavoura é de soja, milho e trigo
ENFEITES = (          # nome e altura em pixels de tela, na ordem da folha (3 linhas de 4)
    ("espantalho", 86), ("espantalho_abobora", 90), ("fardo_de_feno", 62), ("aboboras", 44),
    ("circulo_alienigena", 150), ("marca_de_pouso", 104), ("pegadas_alienigenas", 96), ("placa_alienigena", 62),
    ("corvo", 30), ("caixote_de_legumes", 48), ("carrinho_de_mao", 50), ("irrigador", 42),
)


def sem_nevoa(celula):
    """Apaga a névoa esbranquiçada que a folha traz no fundo: pixels claros, sem cor e meio transparentes."""
    dados = np.array(celula.convert("RGBA"))
    cor, alfa = dados[..., :3].astype(int), dados[..., 3]
    palido = (cor.max(axis=2) - cor.min(axis=2) < 30) & (cor.min(axis=2) > 165)
    dados[..., 3] = np.where((alfa < 150) | (palido & (alfa < 215)), 0, alfa)
    return Image.fromarray(dados)


def main():
    for nome, (forca, desfoque) in PISOS.items():
        textura = ladrilho(Image.open(BRUTO / f"chao_{nome}.png").filter(ImageFilter.GaussianBlur(desfoque * 1254 / 768)))
        desvio = (textura - textura.mean(axis=(0, 1))) * forca
        Image.fromarray(np.clip(desvio, 0, 255).astype(np.uint8)).save(SAIDA / f"{nome}_luz.png")
        Image.fromarray(np.clip(-desvio, 0, 255).astype(np.uint8)).save(SAIDA / f"{nome}_sombra.png")
        print(nome, textura.shape)
    for sobra in ("lavoura.png", "lavoura_luz.png", "lavoura_sombra.png", "lavoura_soja.png", "lavoura_milho.png",
                  "lavoura_trigo.png", "lavoura_solo.png"):
        (SAIDA / sobra).unlink(missing_ok=True)
    plantas = Image.open(BRUTO / "lavoura_plantas_12.png").convert("RGBA")       # pés em 3/4, para as fileiras
    (SAIDA / "plantas").mkdir(exist_ok=True)
    for (cultura, altura), faixa in zip(PLANTAS, linhas(plantas, len(PLANTAS))):
        for i, celula in enumerate(dividir(faixa, 4)):
            desenho = sem_nevoa(celula)
            desenho = desenho.crop(desenho.getbbox())
            largura = max(1, round(desenho.width * altura / desenho.height))
            desenho.resize((largura, altura), Image.LANCZOS).save(SAIDA / "plantas" / f"{cultura}_{i}.png")
        print(cultura, altura)
    folha = Image.open(BRUTO / "lavoura_enfeites_12.png").convert("RGBA")
    celulas = [c for faixa in linhas(folha, 3) for c in dividir(faixa, 4)]
    (SAIDA / "enfeites").mkdir(exist_ok=True)
    for (nome, altura), celula in zip(ENFEITES, celulas):
        if nome in FORA_DE_USO:
            continue
        celula = sem_nevoa(celula)
        desenho = celula.crop(celula.getbbox())
        largura = max(1, round(desenho.width * altura / desenho.height))
        desenho.resize((largura, altura), Image.LANCZOS).save(SAIDA / "enfeites" / f"{nome}.png")
        print(nome, (largura, altura))


if __name__ == "__main__":
    main()
