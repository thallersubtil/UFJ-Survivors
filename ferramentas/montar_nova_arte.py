"""Monta uma tira de animação nova na pasta de preparação, sem tocar em assets/.

A arte nova fica em nova_arte/, espelhando assets/ (mesmos caminhos e nomes), e só é
copiada para assets/ depois de aprovada. Usa a mesma redução suave de montar_sprites.py
(arte ilustrada, borda macia), então o resultado tem o mesmo acabamento das tiras atuais.

Uso:
  python ferramentas/montar_nova_arte.py FOLHA PERSONAGEM ANIMACAO N --altura 28 [--linhas 2] [--espelhar]

FOLHA tem fundo transparente e N quadros, em --linhas linhas lidas da esquerda para a
direita e de cima para baixo. Grava nova_arte/sprites/<PERSONAGEM>/<ANIMACAO>-<N>.png.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageOps

from pixelizar import dividir, gravar_tira, linhas, reduzir_suave

PREPARACAO = Path(__file__).resolve().parent.parent / "nova_arte"


def quadros_da_folha(folha, n, n_linhas=1):
    por_linha = n // n_linhas
    faixas = linhas(folha, n_linhas) if n_linhas > 1 else [folha]
    return [q for faixa in faixas for q in dividir(faixa, por_linha)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("folha")
    p.add_argument("personagem")
    p.add_argument("animacao")
    p.add_argument("quadros", type=int)
    p.add_argument("--altura", type=int, required=True)
    p.add_argument("--linhas", type=int, default=1)
    p.add_argument("--espelhar", action="store_true", help="vira cada quadro (o jogo espera a arte olhando para a direita)")
    a = p.parse_args()
    brutos = quadros_da_folha(Image.open(a.folha).convert("RGBA"), a.quadros, a.linhas)
    if a.espelhar:
        brutos = [ImageOps.mirror(q) for q in brutos]
    print(gravar_tira(reduzir_suave(brutos, a.altura), PREPARACAO / "sprites" / a.personagem, a.animacao))


if __name__ == "__main__":
    main()
