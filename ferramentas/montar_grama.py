"""Prepara o detalhe da grama e os enfeites de chão do mapa (assets/cenario/).

O chão do mapa é guardado em resolução reduzida e ampliado no jogo, então a grama fica
borrada. Aqui saem duas imagens que o jogo soma e subtrai por cima da grama já ampliada
(folhas claras e escuras, em resolução de tela) e os enfeites pequenos (flores, tufos,
pedras) que o jogo espalha pelo gramado.

Entradas em nova_arte/_bruto/: grama_textura.png e grama_enfeites_12.png.
Uso: python ferramentas/montar_grama.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

from pixelizar import dividir, linhas

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "nova_arte" / "_bruto"
SAIDA = RAIZ / "assets" / "cenario"
LADO = 768            # lado do ladrilho de detalhe, em pixels de tela
FORCA = 0.85          # quanto do contraste da textura vai para o chão
ENFEITES = (          # nome e altura em pixels de tela, na ordem da folha (3 linhas de 4)
    ("capim_alto", 40), ("capim_baixo", 26), ("flores_amarelas", 34), ("margaridas", 34),
    ("flores_rosas", 34), ("flores_vermelhas", 32), ("arbusto", 44), ("arbusto_florido", 46),
    ("pedras", 22), ("trevos", 26), ("petalas_ipe", 22), ("cogumelos", 28),
)


def ladrilho(imagem):
    """Torna a textura repetível: mistura com ela mesma deslocada meia volta, sumindo com as emendas."""
    a = np.asarray(imagem.convert("RGB").resize((LADO, LADO), Image.LANCZOS), np.float32)
    b = np.roll(a, (LADO // 2, LADO // 2), axis=(0, 1))
    rampa = 1 - np.abs(np.linspace(-1, 1, LADO))
    peso = np.clip(np.minimum.outer(rampa, rampa) * 4, 0, 1)[..., None]
    return a * peso + b * (1 - peso)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    textura = ladrilho(Image.open(BRUTO / "grama_textura.png"))
    desvio = (textura - textura.mean(axis=(0, 1))) * FORCA
    Image.fromarray(np.clip(desvio, 0, 255).astype(np.uint8)).save(SAIDA / "grama_luz.png")
    Image.fromarray(np.clip(-desvio, 0, 255).astype(np.uint8)).save(SAIDA / "grama_sombra.png")

    folha = Image.open(BRUTO / "grama_enfeites_12.png").convert("RGBA")
    celulas = [c for faixa in linhas(folha, 3) for c in dividir(faixa, 4)]
    (SAIDA / "enfeites").mkdir(exist_ok=True)
    for (nome, altura), celula in zip(ENFEITES, celulas):
        desenho = celula.crop(celula.getbbox())
        largura = max(1, round(desenho.width * altura / desenho.height))
        desenho.resize((largura, altura), Image.LANCZOS).save(SAIDA / "enfeites" / f"{nome}.png")
        print(nome, (largura, altura))


if __name__ == "__main__":
    main()
