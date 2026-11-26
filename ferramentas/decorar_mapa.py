"""Redistribui árvores, postes e bancos do mapa seguindo o campus de verdade.

- Árvores (e ipês) só nas manchas de verde-escuro, que no satélite são onde há árvores; o gramado claro
  é só mato e fica sem árvore. Nada dentro dos talhões de lavoura nem em cima de rua ou calçada.
- Postes em fila ao longo das ruas, à beira do asfalto, com espaçamento uniforme.
- Bancos só à beira das ruas e calçadas, entre os postes.

Palmeiras, portal e bandeira continuam onde o gerador (gerar_mapa.py) pôs, menos as palmeiras que caíam
na rua. Rode depois dele e antes de faixas_de_pedestre.py (que apaga a calçada de cima do asfalto).
Uso: python ferramentas/decorar_mapa.py
"""
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from jogo.mapa import MapaUFJ  # noqa: E402
from jogo.nucleo.colisao import Colisao  # noqa: E402

ARQUIVO = RAIZ / "assets" / "cenario" / "mapa_ufj.json"
MANTIDOS = ("palmeira", "portal", "bandeira")
ESPACO_ENTRE_ARVORES = 150
MAXIMO_DE_ARVORES = 650
CHANCE_DE_IPE = 0.18
ESPACO_ENTRE_POSTES = 300
ESPACO_ENTRE_BANCOS = 640
BEIRA_DO_POSTE = (7, 9)          # distância do asfalto, em pixels do chão reduzido
BEIRA_DO_BANCO = (11, 13)
ALTURA_DA_COPA = 52              # altura da árvore, em pixels do chão
LONGE_DO_PAVIMENTO = 22          # árvore e palmeira ficam a pelo menos isto da rua e da calçada (pixels do chão)


def da_cor(chao, piso):
    cor, tolerancia = piso
    return np.all(np.abs(chao - np.array(cor)) <= np.array(tolerancia), axis=2)


def crescer(mascara, raio):
    """Dilata a máscara `raio` pixels."""
    imagem = Image.fromarray((mascara * 255).astype(np.uint8))
    return np.asarray(imagem.filter(ImageFilter.MaxFilter(2 * raio + 1))) > 0


def faixa(mascara, perto, longe):
    """Pixels fora da máscara que ficam entre `perto` e `longe` pixels dela (a beira da rua)."""
    return crescer(mascara, longe) & ~crescer(mascara, perto)


def espalhar(candidatos, escala, espaco, livre, maximo=None, evitar=()):
    """Escolhe pontos (no mundo) entre os candidatos, na ordem dada, sempre a pelo menos `espaco` uns dos outros."""
    escolhidos, grade = [], {}
    for x, y in evitar:
        grade.setdefault((int(x // espaco), int(y // espaco)), []).append((x, y))
    for py, px in candidatos:
        x, y = int(px) * escala, int(py) * escala
        celula = (x // espaco, y // espaco)
        vizinhos = [p for dx in (-1, 0, 1) for dy in (-1, 0, 1) for p in grade.get((celula[0] + dx, celula[1] + dy), ())]
        if all((x - vx) ** 2 + (y - vy) ** 2 >= espaco ** 2 for vx, vy in vizinhos) and livre(x, y):
            escolhidos.append((x, y))
            grade.setdefault(celula, []).append((x, y))
            if maximo and len(escolhidos) >= maximo:
                break
    return escolhidos


def main():
    dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    escala = dados["escala"]
    chao = np.asarray(Image.open(RAIZ / "assets" / dados["chao"]).convert("RGB")).astype(int)
    poligonos = [[tuple(q) for q in p["poligono"]] for p in dados["predios"]]
    sorteio = random.Random(51)

    def livre(x, y, folga=60):
        if not (100 < x < dados["largura"] - 100 and 100 < y < dados["altura"] - 100):
            return False
        if any(talhao.inflate(80, 80).collidepoint(x, y) for talhao in MapaUFJ.LAVOURAS):
            return False
        return not any(Colisao.circulo_poligono((x, y), folga, pol) for pol in poligonos)

    asfalto = da_cor(chao, MapaUFJ.PISOS[2][1][0])
    calcada = da_cor(chao, MapaUFJ.PISOS[2][1][1])
    base_do_pavimento = crescer(asfalto | calcada, LONGE_DO_PAVIMENTO)
    pavimento = base_do_pavimento.copy()                              # rua, calçada e a beira delas
    for subida in range(4, ALTURA_DA_COPA + 1, 4):                    # a árvore é alta: a copa não pode cobrir
        pavimento[subida:] |= base_do_pavimento[:-subida]            # rua nem calçada que passam atrás dela
    mata = ~crescer(~da_cor(chao, MapaUFJ.VERDE_ESCURO), 2) & ~pavimento   # miolo do verde-escuro, fora da rua

    def fora_da_rua(d):
        py, px = int(d["y"] // escala), int(d["x"] // escala)
        return not pavimento[min(py, pavimento.shape[0] - 1), min(px, pavimento.shape[1] - 1)]

    arvores = [tuple(v) for v in np.argwhere(mata)]
    sorteio.shuffle(arvores)
    arvores = espalhar(arvores, escala, ESPACO_ENTRE_ARVORES, livre, MAXIMO_DE_ARVORES)
    # em ordem de varredura os postes saem em fila ao longo da rua, e não salpicados
    postes = espalhar(np.argwhere(faixa(asfalto, *BEIRA_DO_POSTE) & ~calcada), escala, ESPACO_ENTRE_POSTES,
                      lambda x, y: livre(x, y, 40))
    bancos = espalhar(np.argwhere(faixa(asfalto | calcada, *BEIRA_DO_BANCO)), escala, ESPACO_ENTRE_BANCOS,
                      lambda x, y: livre(x, y, 40) and all((x - px) ** 2 + (y - py) ** 2 > 110 ** 2 for px, py in postes))

    decoracoes = [d for d in dados["decoracoes"]
                  if d["tipo"] in MANTIDOS and livre(d["x"], d["y"], 0) and (d["tipo"] != "palmeira" or fora_da_rua(d))]
    decoracoes += [{"tipo": "ipe" if sorteio.random() < CHANCE_DE_IPE else "arvore", "x": x, "y": y} for x, y in arvores]
    decoracoes += [{"tipo": "poste", "x": x, "y": y} for x, y in postes]
    decoracoes += [{"tipo": "banco", "x": x, "y": y} for x, y in bancos]
    dados["decoracoes"] = decoracoes
    ARQUIVO.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    print(f"{len(arvores)} árvores, {len(postes)} postes, {len(bancos)} bancos, {len(decoracoes)} decorações no total")


if __name__ == "__main__":
    main()
