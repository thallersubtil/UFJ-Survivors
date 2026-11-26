"""Monta itens soltos (coletáveis, projéteis, baú) na pasta de preparação, sem tocar em assets/.

Cada item novo é encaixado na mesma tela e na mesma área ocupada pelo desenho atual em
assets/, então entra no jogo com o mesmo tamanho. O baú usa uma escala única para os
quatro quadros, para a base não pular enquanto a tampa abre.

Uso: python ferramentas/montar_itens.py
"""
from pathlib import Path

from PIL import Image

from pixelizar import dividir, linhas

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"
PREPARACAO = RAIZ / "nova_arte"
BRUTO = PREPARACAO / "_bruto"

# folha, linhas, colunas, {posição na grade: destinos (caminhos iguais aos de assets/)}
FOLHAS = (
    ("itens_lote1.png", 2, 4, {
        0: ("legado/itens/potion_hp_s.png", "legado/itens/potion_hp.png"),
        1: ("sprites/controle.png",),
        2: ("sprites/estrela_gemini.png",),
        3: ("legado/itens/item_watch_l.png", "legado/itens/item_watch_s.png"),
        4: ("legado/itens/item_dice.png",),
    }),
    ("icones_lote2.png", 2, 4, {7: ("sprites/cafe.png",)}),
)
BAU = ("bau_4q.png", tuple(f"legado/itens/chest_f{i}.png" for i in range(4)))


def celulas(folha, n_linhas, colunas, borda=0.04):
    """Células da grade, com uma faixa da borda apagada (tira sobras do desenho vizinho)."""
    partes = [c.copy() for faixa in linhas(folha, n_linhas) for c in dividir(faixa, colunas)]
    for parte in partes:
        limpa = Image.new("RGBA", parte.size, (0, 0, 0, 0))
        dx, dy = round(parte.width * borda), round(parte.height * borda)
        limpa.paste(parte.crop((dx, dy, parte.width - dx, parte.height - dy)), (dx, dy))
        parte.paste(limpa)
    return partes


def encaixar(desenho, tamanho, area):
    """Põe o desenho (já recortado) dentro da área, sem deformar, centrado e apoiado embaixo."""
    esquerda, topo, direita, base = area
    escala = min((direita - esquerda) / desenho.width, (base - topo) / desenho.height)
    novo = desenho.resize((max(1, round(desenho.width * escala)), max(1, round(desenho.height * escala))),
                          Image.LANCZOS)
    tela = Image.new("RGBA", tamanho, (0, 0, 0, 0))
    tela.alpha_composite(novo, (esquerda + (direita - esquerda - novo.width) // 2, base - novo.height))
    return tela


def gravar(imagem, destino):
    saida = PREPARACAO / destino
    saida.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(saida)
    print(saida)


def main():
    for nome, n_linhas, colunas, destinos in FOLHAS:
        partes = celulas(Image.open(BRUTO / nome).convert("RGBA"), n_linhas, colunas)
        for posicao, caminhos in destinos.items():
            desenho = partes[posicao].crop(partes[posicao].getbbox())
            for caminho in caminhos:
                atual = Image.open(ASSETS / caminho).convert("RGBA")
                gravar(encaixar(desenho, atual.size, atual.getbbox()), caminho)

    nome, caminhos = BAU
    quadros = celulas(Image.open(BRUTO / nome).convert("RGBA"), 1, len(caminhos))
    caixas = [q.getbbox() for q in quadros]
    uniao = (min(c[0] for c in caixas), min(c[1] for c in caixas), max(c[2] for c in caixas), max(c[3] for c in caixas))
    for quadro, caminho in zip(quadros, caminhos):
        tamanho = Image.open(ASSETS / caminho).size
        gravar(encaixar(quadro.crop(uniao), tamanho, (0, 0, *tamanho)), caminho)


if __name__ == "__main__":
    main()
