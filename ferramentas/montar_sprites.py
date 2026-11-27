"""Monta todos os sprites animados do jogo a partir das folhas geradas em arte_bruta/disgaea/.

A arte é ilustrada (estilo Disgaea: contorno grosso, cores saturadas), não pixel art:
cada quadro é reduzido com filtro de qualidade direto para a altura que terá na tela,
mantendo a borda macia, e todos os quadros de uma animação são alinhados pelo corpo.

Cada linha da RECEITA diz: folha, personagem (pasta em assets/sprites/), animação,
número de quadros e altura na tela em pixels. Extras opcionais:
  linha=(i, n)    a folha tem n linhas de quadros; usa a linha i (começando em 0)
  coluna=True     os quadros estão empilhados em coluna (um por linha)
  faixa=(x0, x1)  usa só essa faixa horizontal (fração da largura) e a maior parte conectada dela
  celulas=True    divide a folha em n células de mesma largura (quadros com rastros soltos)
  usar=[...]      usa só esses quadros
  gigante=altura  grava também <personagem>_gigante (mini-chefe) nessa altura
  ancora="esquerda"  alinha pela borda esquerda (mastro da bandeira) em vez do corpo

Uso: python ferramentas/montar_sprites.py
"""
from pathlib import Path

from PIL import Image

import numpy as np

from pixelizar import PASTA_SPRITES, dividir, gravar_tira, linhas, reduzir_suave


def maior_parte(imagem):
    """Mantém só a maior região conectada (tira pedaços de objetos vizinhos)."""
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    sup = pygame.image.frombytes(imagem.tobytes(), imagem.size, "RGBA")
    mascara = pygame.mask.from_surface(sup, 40).connected_component()
    a = np.array(imagem)
    manter = np.array(mascara.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
                      .get_view("A"), copy=True).T > 0
    a[~manter] = 0
    resultado = Image.fromarray(a, "RGBA")
    return resultado.crop(resultado.getbbox())

BRUTA = Path(__file__).resolve().parent.parent / "arte_bruta" / "disgaea"

RECEITA = [
    ("professor_parado.png", "professor", "parado", 4, 124, {}),
    ("professor_andar.png", "professor", "andar", 4, 124, {}),
    ("bug_andar.png", "bug", "andar", 4, 28, {}),
    ("calculadora_andar.png", "calculadora", "andar", 4, 44, {"gigante": 132}),
    ("mouse_andar.png", "mouse", "andar", 4, 30, {}),
    ("mouse_andar.png", "mouse", "parado", 4, 30, {"usar": [0]}),
    ("caixinha_andar.png", "caixinha", "andar", 4, 38, {}),
    ("caixinha_andar.png", "caixinha_pequena", "andar", 4, 24, {}),
    ("pi_andar.png", "pi", "andar", 4, 38, {}),
    ("ponteiro_andar.png", "ponteiro", "andar", 4, 32, {"celulas": True}),
    ("pilha_andar.png", "pilha", "andar", 4, 44, {}),
    ("pente_ram_andar.png", "pente_ram", "andar", 4, 28, {"coluna": True, "gigante": 84}),
    ("caramelo_mover.png", "caramelo", "mover", 4, 36, {}),
    ("mascotes.png", "chatgpt", "mover", 4, 34, {"linha": (0, 2)}),
    ("mascotes.png", "claude", "mover", 4, 30, {"linha": (1, 2)}),
    ("fusca_mover.png", "fusca", "mover", 4, 52, {}),
    ("caramelo_no_fusca_mover.png", "caramelo_no_fusca", "mover", 4, 58, {}),
    ("cobra_nota.png", "cobra", "mover", 4, 20, {"linha": (0, 2)}),
    ("cobra_nota.png", "nota", "mover", 4, 22, {"linha": (1, 2)}),
    ("bandeira_parado.png", "bandeira", "parado", 4, 120, {"ancora": "esquerda"}),
    ("portal_ufj.png", "portal_ufj", "parado", 1, 240, {}),
    ("decoracoes.png", "palmeira", "parado", 5, 190, {"faixa": (0.0, 0.212)}),
    ("decoracoes.png", "ipe", "parado", 5, 160, {"faixa": (0.18, 0.445)}),
    ("decoracoes.png", "arvore_cerrado", "parado", 5, 150, {"faixa": (0.443, 0.68)}),
    ("decoracoes.png", "poste", "parado", 5, 130, {"faixa": (0.672, 0.775)}),
    ("decoracoes.png", "banco", "parado", 5, 44, {"faixa": (0.765, 1.0)}),
]


def quadros_brutos(folha, n, extras):
    imagem = Image.open(BRUTA / folha).convert("RGBA")
    if "linha" in extras:
        i, total = extras["linha"]
        imagem = linhas(imagem, total)[i]
    if "faixa" in extras:
        x0, x1 = extras["faixa"]
        return [maior_parte(imagem.crop((int(x0 * imagem.width), 0, int(x1 * imagem.width), imagem.height)))]
    if extras.get("coluna"):
        brutos = [q.crop(q.getbbox()) for q in linhas(imagem, n)]
    elif extras.get("celulas"):
        w = imagem.width / n
        brutos = [imagem.crop((round(i * w), 0, round((i + 1) * w), imagem.height)) for i in range(n)]
        brutos = [q.crop(q.getbbox()) for q in brutos]
    else:
        brutos = dividir(imagem, n)
    if "objeto" in extras:
        brutos = [brutos[extras["objeto"]]]
    if "usar" in extras:
        brutos = [brutos[i] for i in extras["usar"]]
    return brutos


def montar(folha, personagem, animacao, n, altura, extras):
    brutos = quadros_brutos(folha, n, extras)
    ancora = extras.get("ancora", "corpo")
    caminhos = [gravar_tira(reduzir_suave(brutos, altura, ancora), PASTA_SPRITES / personagem, animacao)]
    if "gigante" in extras:
        caminhos.append(gravar_tira(reduzir_suave(brutos, extras["gigante"], ancora),
                                    PASTA_SPRITES / f"{personagem}_gigante", animacao))
    return caminhos


def main():
    for linha in RECEITA:
        for caminho in montar(*linha):
            print(caminho.relative_to(PASTA_SPRITES.parent.parent))


if __name__ == "__main__":
    main()
