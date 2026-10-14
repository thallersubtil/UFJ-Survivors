"""Transforma uma folha de animação gerada em pixel art de verdade, pronta para o jogo.

Uso:
  python ferramentas/pixelizar.py FOLHA PERSONAGEM ANIMACAO N --altura 48 [--cores 24] [--gigante 144]

Divide a FOLHA em N quadros, reduz cada um para a altura nativa escolhendo a cor
mais frequente de cada bloco (com prioridade para brilhos e contorno escuro),
usa uma paleta comum, deixa a transparência sem meio-termo, põe 1 px de contorno
e grava assets/sprites/<PERSONAGEM>/<ANIMACAO>-<N>.png. Com --gigante, grava
também assets/sprites/<PERSONAGEM>_gigante/ na altura indicada (mini-chefes).
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

PASTA_SPRITES = Path(__file__).resolve().parent.parent / "assets" / "sprites"
LIMIAR_ALFA = 110


def _mascara(img):
    return img.getchannel("A").point(lambda v: 255 if v > 40 else 0)


def dividir(folha, n):
    """Divide a folha em n quadros pelas colunas vazias; se estiverem encostados, em células iguais."""
    alfa = np.array(_mascara(folha)) > 0
    colunas = alfa.any(axis=0)
    trechos, inicio = [], None
    for x, cheia in enumerate(list(colunas) + [False]):
        if cheia and inicio is None:
            inicio = x
        elif not cheia and inicio is not None:
            trechos.append((inicio, x))
            inicio = None
    while len(trechos) > n:   # junta pedacinhos soltos ao vizinho mais próximo
        i = min(range(len(trechos) - 1), key=lambda k: trechos[k + 1][0] - trechos[k][1])
        trechos[i:i + 2] = [(trechos[i][0], trechos[i + 1][1])]
    if len(trechos) < n:
        largura = folha.width
        trechos = [(round(i * largura / n), round((i + 1) * largura / n)) for i in range(n)]
    quadros = []
    for x0, x1 in trechos:
        q = folha.crop((x0, 0, x1, folha.height))
        caixa = _mascara(q).getbbox()
        quadros.append(q.crop(caixa) if caixa else q)
    return quadros


def pixelizar(quadros, altura, cores=24):
    """Reduz os quadros para `altura` pixels, alinhados pela base e com a mesma largura."""
    maior = max(q.height for q in quadros)
    largura_fonte = max(q.width for q in quadros)
    tira = Image.new("RGBA", (largura_fonte * len(quadros), maior), (0, 0, 0, 0))
    for i, q in enumerate(quadros):
        tira.paste(q, (i * largura_fonte + (largura_fonte - q.width) // 2, maior - q.height))
    opaco = np.array(tira.getchannel("A")) > LIMIAR_ALFA
    paletizada = tira.convert("RGB").quantize(cores, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    indices = np.where(opaco, np.array(paletizada).astype(int), -1)
    paleta = np.array(paletizada.getpalette()).reshape(-1, 3)[: indices.max() + 1]
    brilho = paleta.sum(axis=1)
    escuras = [c for c in range(len(paleta)) if brilho[c] < 150]
    claras = [c for c in range(len(paleta)) if brilho[c] > 600]
    mais_escura = int(np.argmin(brilho))

    fator = altura / maior
    largura_saida = max(1, round(largura_fonte * fator)) + 2
    passo = 1 / fator
    saida = []
    for i in range(len(quadros)):
        celula = indices[:, i * largura_fonte:(i + 1) * largura_fonte]
        largura_util = round(largura_fonte * fator)
        margem = (largura_saida - largura_util) // 2
        out = np.full((altura, largura_saida), -1)
        for ty in range(altura):
            y0 = int(ty * passo)
            y1 = max(y0 + 1, int((ty + 1) * passo))
            for tx in range(largura_util):
                x0 = int(tx * passo)
                x1 = max(x0 + 1, int((tx + 1) * passo))
                bloco = celula[y0:y1, x0:x1].ravel()
                opacos = bloco[bloco >= 0]
                if len(opacos) < 0.45 * len(bloco):
                    continue
                contagem = np.bincount(opacos, minlength=len(paleta))
                clara = max(claras, key=lambda c: contagem[c]) if claras else None
                escura = max(escuras, key=lambda c: contagem[c]) if escuras else None
                if clara is not None and contagem[clara] >= 0.25 * len(opacos):
                    out[ty, tx + margem] = clara
                elif escura is not None and contagem[escura] >= 0.35 * len(opacos):
                    out[ty, tx + margem] = escura
                else:
                    out[ty, tx + margem] = int(np.argmax(contagem))
        cheio = out >= 0
        vizinho = np.zeros_like(cheio)
        vizinho[1:, :] |= cheio[:-1, :]
        vizinho[:-1, :] |= cheio[1:, :]
        vizinho[:, 1:] |= cheio[:, :-1]
        vizinho[:, :-1] |= cheio[:, 1:]
        out[vizinho & ~cheio] = mais_escura
        rgba = np.zeros((altura, largura_saida, 4), np.uint8)
        rgba[out >= 0, :3] = paleta[out[out >= 0]]
        rgba[out >= 0, 3] = 255
        saida.append(Image.fromarray(rgba, "RGBA"))
    return saida


def gravar_tira(quadros, pasta, animacao):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    largura, altura = quadros[0].size
    tira = Image.new("RGBA", (largura * len(quadros), altura), (0, 0, 0, 0))
    for i, q in enumerate(quadros):
        tira.paste(q, (i * largura, 0))
    caminho = pasta / f"{animacao}-{len(quadros)}.png"
    for antigo in pasta.glob(f"{animacao}-*.png"):
        antigo.unlink()
    tira.save(caminho)
    return caminho


def main():
    p = argparse.ArgumentParser()
    p.add_argument("folha")
    p.add_argument("personagem")
    p.add_argument("animacao")
    p.add_argument("quadros", type=int)
    p.add_argument("--altura", type=int, required=True)
    p.add_argument("--cores", type=int, default=24)
    p.add_argument("--gigante", type=int)
    a = p.parse_args()
    brutos = dividir(Image.open(a.folha).convert("RGBA"), a.quadros)
    print(gravar_tira(pixelizar(brutos, a.altura, a.cores), PASTA_SPRITES / a.personagem, a.animacao))
    if a.gigante:
        print(gravar_tira(pixelizar(brutos, a.gigante, a.cores + 8), PASTA_SPRITES / f"{a.personagem}_gigante",
                          a.animacao))


if __name__ == "__main__":
    main()


def _ancora_x(quadro):
    """Centro horizontal da cabeça e do tronco (55% de cima), que não mexe ao andar."""
    opaco = np.array(quadro)[..., 3] > 0
    linhas = np.nonzero(opaco.any(axis=1))[0]
    if len(linhas) == 0:
        return quadro.width / 2
    limite = linhas[0] + (linhas[-1] - linhas[0]) * 0.55
    ys, xs = np.nonzero(opaco[: int(limite) + 1])
    return xs.mean() if len(xs) else quadro.width / 2


def alinhar(quadros, ancora="corpo"):
    """Põe todos os quadros na mesma tela, com a âncora na mesma coluna e os pés na base.

    ancora="corpo": centro da cabeça e do tronco (personagens); "esquerda": borda esquerda (mastros).
    """
    ancoras = [_ancora_x(q) if ancora == "corpo" else 0 for q in quadros]
    esquerda = max(int(np.ceil(a)) for a in ancoras)
    direita = max(int(np.ceil(q.width - a)) for q, a in zip(quadros, ancoras))
    altura = max(q.height for q in quadros)
    saida = []
    for q, a in zip(quadros, ancoras):
        tela = Image.new("RGBA", (esquerda + direita + 2, altura), (0, 0, 0, 0))
        tela.paste(q, (int(round(esquerda - a)) + 1, altura - q.height))
        saida.append(tela)
    return saida


def reduzir(quadros, altura, cores=48):
    """Reduz direto ao tamanho de tela com filtro de qualidade, paleta comum e alfa duro, alinhando pelo corpo."""
    maior = max(q.height for q in quadros)
    fator = altura / maior
    reduzidos = [q.resize((max(1, round(q.width * fator)), max(1, round(q.height * fator))), Image.LANCZOS)
                 for q in quadros]
    largura = sum(q.width for q in reduzidos)
    tira = Image.new("RGBA", (largura, max(q.height for q in reduzidos)), (0, 0, 0, 0))
    x = 0
    for q in reduzidos:
        tira.paste(q, (x, 0))
        x += q.width
    alfa = np.array(tira)[..., 3] > 120
    rgb = np.array(tira.convert("RGB").quantize(cores, method=Image.Quantize.MEDIANCUT,
                                                 dither=Image.Dither.NONE).convert("RGB"))
    saida, x = [], 0
    for q in reduzidos:
        bloco = np.zeros((q.height, q.width, 4), np.uint8)
        bloco[..., :3] = rgb[: q.height, x:x + q.width]
        bloco[..., 3] = alfa[: q.height, x:x + q.width] * 255
        saida.append(Image.fromarray(bloco, "RGBA"))
        x += q.width
    return alinhar(saida)


def reduzir_suave(quadros, altura, ancora="corpo"):
    """Para arte ilustrada (não pixel art): reduz com LANCZOS mantendo a borda macia, alinhando pelo corpo."""
    maior = max(q.height for q in quadros)
    fator = altura / maior
    saida = []
    for q in quadros:
        r = q.resize((max(1, round(q.width * fator)), max(1, round(q.height * fator))), Image.LANCZOS)
        a = np.array(r)
        a[a[..., 3] < 24] = 0
        saida.append(Image.fromarray(a, "RGBA"))
    return alinhar(saida, ancora)


def linhas(folha, n):
    """Separa uma folha com várias linhas de quadros em n faixas horizontais (pelas linhas vazias)."""
    rotada = folha.transpose(Image.Transpose.ROTATE_90)
    faixas = dividir(rotada, n)
    return [f.transpose(Image.Transpose.ROTATE_270) for f in faixas]
