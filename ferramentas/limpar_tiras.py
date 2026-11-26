"""Tira das tiras de animação os pedacinhos do quadro vizinho que sobraram no recorte.

Algumas tiras antigas foram cortadas com o desenho encostando na divisa dos quadros: um pedaço
do braço ou da perna de um quadro ficou colado na borda do quadro ao lado e aparece "solto" ao
lado do personagem durante a animação. Este script apaga, em cada quadro, as ilhas pequenas de
pixels que ficam junto da borda esquerda ou direita e não tocam no corpo.

Uso: python ferramentas/limpar_tiras.py [--conferir]     (--conferir só lista, sem gravar)
"""
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SPRITES = Path(__file__).resolve().parent.parent / "assets" / "sprites"
FAIXA_DA_BORDA = 0.2          # fração da largura do quadro, de cada lado, onde uma ilha é suspeita
TAMANHO_MAXIMO = 0.08         # ilha com menos que isso da área do corpo é sobra, não parte do desenho
# efeitos e personagens novos têm partículas soltas de propósito (faíscas, gotas de suor, aura)
IGNORAR = {"golpe_claude", "estouro_pequi", "tiro_chatgpt", "tiro_chatgpt_alucinado", "folha_apostila",
           "serpente_estelar", "metralhadora", "calouro", "cara_da_carona", "otaku", "otaku_ssj", "programador",
           "mestre_de_rpg", "monitor", "gamer", "caramelo"}


def ilhas(opaco):
    """Rótulos das ilhas de pixels opacos (vizinhança de 8) e a área de cada uma."""
    rotulos = np.zeros(opaco.shape, np.int32)
    areas = [0]
    for y, x in zip(*np.nonzero(opaco)):
        if rotulos[y, x]:
            continue
        atual, pilha, area = len(areas), [(y, x)], 0
        rotulos[y, x] = atual
        while pilha:
            cy, cx = pilha.pop()
            area += 1
            for ny in range(max(0, cy - 1), min(opaco.shape[0], cy + 2)):
                for nx in range(max(0, cx - 1), min(opaco.shape[1], cx + 2)):
                    if opaco[ny, nx] and not rotulos[ny, nx]:
                        rotulos[ny, nx] = atual
                        pilha.append((ny, nx))
        areas.append(area)
    return rotulos, areas


def limpar(tira, quadros):
    """Devolve a tira consertada e quantas sobras foram tratadas.

    A sobra que encosta na divisa é a continuação do desenho do quadro vizinho: volta para ele
    (os quadros ficam um pouco mais largos para caber). A que só está perto da borda é apagada.
    """
    pixels = np.array(tira.convert("RGBA"))
    altura, largura = pixels.shape[0], pixels.shape[1] // quadros
    partes = [pixels[:, q * largura:(q + 1) * largura].copy() for q in range(quadros)]
    a_esquerda = [None] * quadros          # pedaço que continua o quadro pela esquerda (veio do vizinho anterior)
    a_direita = [None] * quadros
    tratadas = 0
    for q, quadro in enumerate(partes):
        rotulos, areas = ilhas(quadro[..., 3] > 24)
        if len(areas) < 3:
            continue
        corpo = max(areas)
        faixa = max(2, int(largura * FAIXA_DA_BORDA))
        for i in range(1, len(areas)):
            if areas[i] >= corpo * TAMANHO_MAXIMO:
                continue
            ilha = rotulos == i
            colunas = np.nonzero(ilha.any(axis=0))[0]
            na_esquerda, na_direita = colunas.max() < faixa, colunas.min() >= largura - faixa
            if not (na_esquerda or na_direita):
                continue
            pedaco = np.where(ilha[..., None], quadro, 0)
            if na_esquerda and colunas.min() == 0 and q > 0:              # é o fim do quadro anterior
                corte = pedaco[:, :colunas.max() + 1]
                a_direita[q - 1] = corte if a_direita[q - 1] is None else np.maximum(a_direita[q - 1][:, :corte.shape[1]], corte)
            elif na_direita and colunas.max() == largura - 1 and q < quadros - 1:   # é o começo do próximo
                a_esquerda[q + 1] = pedaco[:, colunas.min():]
            quadro[ilha] = 0
            tratadas += 1
    extra_e = max((p.shape[1] for p in a_esquerda if p is not None), default=0)
    extra_d = max((p.shape[1] for p in a_direita if p is not None), default=0)
    nova_largura = largura + extra_e + extra_d
    saida = np.zeros((altura, nova_largura * quadros, 4), np.uint8)
    for q, quadro in enumerate(partes):
        x = q * nova_largura + extra_e
        saida[:, x:x + largura] = quadro
        if a_esquerda[q] is not None:
            w = a_esquerda[q].shape[1]
            saida[:, x - w:x] = a_esquerda[q]
        if a_direita[q] is not None:
            w = a_direita[q].shape[1]
            saida[:, x + largura:x + largura + w] = a_direita[q]
    return Image.fromarray(saida), tratadas


def main():
    conferir = "--conferir" in sys.argv
    for arquivo in sorted(SPRITES.glob("*/*-*.png")):
        achado = re.fullmatch(r".+-(\d+)", arquivo.stem)
        if not achado or int(achado.group(1)) < 2 or arquivo.parent.name in IGNORAR:
            continue
        limpa, apagadas = limpar(Image.open(arquivo), int(achado.group(1)))
        if apagadas:
            print(f"{arquivo.relative_to(SPRITES)}: {apagadas} sobra(s)")
            if not conferir:
                limpa.save(arquivo)


if __name__ == "__main__":
    main()
