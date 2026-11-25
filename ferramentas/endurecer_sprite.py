"""Deixa uma folha já no tamanho do jogo com cara de pixel art, igual à dos alunos originais.

Uso:
  python ferramentas/endurecer_sprite.py ORIGEM DESTINO [--cores 64]

A arte gerada às vezes sai "lisa" (degradês suaves e borda borrada). Isto deixa a
transparência sem meio-termo, reduz a folha a uma paleta comum (sem pontilhado) e escurece o
anel de 1 px da borda, que vira o contorno escuro dos outros sprites. Com --cores 0 não reduz a
paleta (use quando a redução trocar a cor de detalhes pequenos, como os olhos). Foi usado nas alunas:
  python ferramentas/endurecer_sprite.py arte_bruta/aluna1/parado-4.png assets/sprites/aluna1/parado-4.png
"""
import argparse

import numpy as np
from PIL import Image

LIMIAR_ALFA = 110


def _borda(opaco):
    """Pixels opacos que encostam (vizinhança de 4) num transparente."""
    dentro = opaco.copy()
    dentro[1:, :] &= opaco[:-1, :]
    dentro[:-1, :] &= opaco[1:, :]
    dentro[:, 1:] &= opaco[:, :-1]
    dentro[:, :-1] &= opaco[:, 1:]
    dentro[0, :] = dentro[-1, :] = False
    dentro[:, 0] = dentro[:, -1] = False
    return opaco & ~dentro


def endurecer(imagem, cores=64):
    a = np.array(imagem.convert("RGBA")).astype(float)
    opaco = a[..., 3] > LIMIAR_ALFA
    rgb = Image.fromarray(a[..., :3].clip(0, 255).astype(np.uint8))
    if cores:
        paleta = rgb.quantize(cores, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        q = np.array(paleta.convert("RGB")).astype(float)
    else:   # sem paleta: detalhes pequenos (olhos claros num sprite quase todo amarelo) não mudam de cor
        q = np.array(rgb).astype(float)
    borda = _borda(opaco)
    escuro = (q * 0.28 + np.array([6, 5, 10])).clip(0, 255)
    q[borda] = np.minimum(q[borda], escuro[borda])
    saida = np.zeros_like(a)
    saida[..., :3] = np.where(opaco[..., None], q, 0)
    saida[..., 3] = np.where(opaco, 255, 0)
    return Image.fromarray(saida.astype(np.uint8))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("origem")
    p.add_argument("destino")
    p.add_argument("--cores", type=int, default=64, help="tamanho da paleta (0 = não reduz)")
    args = p.parse_args()
    endurecer(Image.open(args.origem), args.cores).save(args.destino)


if __name__ == "__main__":
    main()
