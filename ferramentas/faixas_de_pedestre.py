"""Troca cada ponto em que uma calçada atravessa a rua por uma faixa de pedestre.

No chão gerado (gerar_mapa.py) as calçadas passam por cima do asfalto, atravessando a rua ou invadindo a
pista em vez de correr ao lado dela. Toda calçada em cima da rua é repintada de asfalto. Só vira faixa a
travessia de verdade: num trecho reto de rua (não em cruzamento) e com caminho de pedestre continuando dos
dois lados. A faixa fica reta, perpendicular à pista e de meio-fio a meio-fio; posição, direção e tamanho
vão para "faixas" em mapa_ufj.json e o jogo desenha as listras em resolução de tela.

Depois de rodar, o chão já não tem calçada sobre a rua: rodar de novo não acha nada e mantém as faixas
gravadas. Para refazer do zero, gere o mapa outra vez (gerar_mapa.py) e rode este script.

Uso: python ferramentas/faixas_de_pedestre.py
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "assets" / "cenario" / "mapa_ufj.json"
ASFALTO = ((76, 76, 88), (22, 22, 24))
CALCADA = ((218, 206, 172), (30, 30, 34))
FECHAMENTO = 7                  # metade da maior largura de calçada que conta como travessia (pixels do chão)
TAMANHO_MINIMO = 24             # pixels do chão: menos que isso é só a beira da calçada encostando na rua
RETA_MINIMA = 0.75              # quão reto o trecho de rua precisa ser para receber faixa
LARGURA_DA_FAIXA = 54           # no mundo
DISTANCIA_ENTRE_FAIXAS = 260    # no mundo: duas travessias mais perto que isso viram uma


def da_cor(chao, piso):
    cor, tolerancia = piso
    return np.all(np.abs(chao - np.array(cor)) <= np.array(tolerancia), axis=2)


def filtro(mascara, raio, classe):
    return np.asarray(Image.fromarray((mascara * 255).astype(np.uint8)).filter(classe(2 * raio + 1))) > 0


def componentes(mascara):
    """Grupos de pixels vizinhos da máscara (listas de (y, x))."""
    visto = np.zeros_like(mascara, bool)
    altura, largura = mascara.shape
    for y, x in np.argwhere(mascara):
        if visto[y, x]:
            continue
        pilha, grupo = [(y, x)], []
        visto[y, x] = True
        while pilha:
            cy, cx = pilha.pop()
            grupo.append((cy, cx))
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < altura and 0 <= nx < largura and mascara[ny, nx] and not visto[ny, nx]:
                    visto[ny, nx] = True
                    pilha.append((ny, nx))
        yield np.array(grupo)


def direcao_da_rua(rua, cy, cx, raio=26):
    """Direção (dy, dx) da pista em volta do ponto e o quanto ela é um trecho reto (0 a 1; cruzamento dá baixo)."""
    y0, x0 = max(0, cy - raio), max(0, cx - raio)
    pontos = np.argwhere(rua[y0:cy + raio + 1, x0:cx + raio + 1]) + (y0, x0)
    pontos = pontos[((pontos - (cy, cx)) ** 2).sum(axis=1) <= raio * raio]
    if len(pontos) < 30:
        return None, 0.0
    valores, eixos = np.linalg.eigh(np.cov((pontos - pontos.mean(axis=0)).T))
    return eixos[:, 1], 1 - valores[0] / max(valores[1], 1e-6)


def ate_o_meio_fio(rua, cy, cx, passo, limite=40):
    """Quantos pixels dá para andar do ponto, na direção `passo`, sem sair da pista."""
    for n in range(1, limite):
        y, x = round(cy + passo[0] * n), round(cx + passo[1] * n)
        if not (0 <= y < rua.shape[0] and 0 <= x < rua.shape[1]) or not rua[y, x]:
            return n - 1
    return None                                               # não achou a beira: não é uma rua simples


def tem_calcada(calcada, y, x, raio=4):
    y, x = round(y), round(x)
    return bool(calcada[max(0, y - raio):y + raio + 1, max(0, x - raio):x + raio + 1].any())


def main():
    dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    escala = dados["escala"]
    caminho = RAIZ / "assets" / dados["chao"]
    imagem = Image.open(caminho).convert("RGB")
    chao = np.asarray(imagem).astype(int)
    asfalto = da_cor(chao, ASFALTO)
    calcada = da_cor(chao, CALCADA)
    rua = filtro(filtro(asfalto, FECHAMENTO, ImageFilter.MaxFilter), FECHAMENTO, ImageFilter.MinFilter)   # rua sem buracos
    travessia = rua & filtro(calcada, 1, ImageFilter.MaxFilter) & ~asfalto
    fora = calcada & ~filtro(rua, 2, ImageFilter.MaxFilter)   # calçada de verdade, fora da pista
    novo = np.array(imagem)
    faixas = []
    # toda calçada em cima da rua volta a ser asfalto, atravessando ou só invadindo a pista
    novo[filtro(travessia, 3, ImageFilter.MaxFilter) & rua] = ASFALTO[0]
    for grupo in componentes(travessia):
        if len(grupo) < TAMANHO_MINIMO:
            continue
        cy, cx = (round(v) for v in grupo.mean(axis=0))
        ao_longo, reta = direcao_da_rua(rua, cy, cx)
        if ao_longo is None or reta < RETA_MINIMA:            # cruzamento ou rotatória: ninguém atravessa ali
            continue
        atravessar = np.array((-ao_longo[1], ao_longo[0]))    # perpendicular à pista: por onde o aluno anda
        ida, volta = ate_o_meio_fio(rua, cy, cx, atravessar), ate_o_meio_fio(rua, cy, cx, -atravessar)
        if ida is None or volta is None or not 8 <= ida + volta <= 34:
            continue
        # só é travessia se o caminho de pedestre continua dos dois lados da rua
        if not (tem_calcada(fora, cy + atravessar[0] * (ida + 5), cx + atravessar[1] * (ida + 5))
                and tem_calcada(fora, cy - atravessar[0] * (volta + 5), cx - atravessar[1] * (volta + 5))):
            continue
        meio = np.array((cy, cx)) + atravessar * (ida - volta) / 2          # centro da pista
        x, y = meio[1] * escala, meio[0] * escala
        if any((x - f["x"]) ** 2 + (y - f["y"]) ** 2 < DISTANCIA_ENTRE_FAIXAS ** 2 for f in faixas):
            continue
        faixas.append({"x": round(x), "y": round(y), "dx": round(float(atravessar[1]), 3),
                       "dy": round(float(atravessar[0]), 3), "comprimento": round((ida + volta + 1) * escala),
                       "largura": LARGURA_DA_FAIXA})
    Image.fromarray(novo).save(caminho)
    if not faixas and dados.get("faixas"):
        print("nenhuma travessia nova; mantendo as", len(dados["faixas"]), "faixas gravadas")
        return
    dados["faixas"] = faixas
    ARQUIVO.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    print(len(faixas), "faixas de pedestre")


if __name__ == "__main__":
    main()
