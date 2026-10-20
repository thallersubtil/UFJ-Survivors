"""Aparência do aluno: tom de pele, cor do cabelo, do moletom e da calça.

A arte dos alunos não muda: as cores são trocadas na hora de carregar os sprites.
Cada pixel é classificado (pele, cabelo, moletom, calça, boné) pela cor original e
recebe o novo tom mantendo o sombreado (a claridade relativa do pixel).
"""
import numpy as np
import pygame

# (nome, cor) - "Original" (None) deixa como foi desenhado
TONS_DE_PELE = (
    ("Original", None),
    ("Muito clara", (255, 226, 204)),
    ("Clara", (240, 196, 160)),
    ("Média", (210, 154, 110)),
    ("Morena", (165, 108, 70)),
    ("Escura", (105, 66, 44)),
)
CORES_DE_CABELO = (
    ("Original", None),
    ("Preto", (52, 44, 50)),
    ("Castanho claro", (150, 100, 60)),
    ("Loiro", (236, 196, 100)),
    ("Ruivo", (200, 90, 40)),
    ("Grisalho", (180, 180, 186)),
    ("Azul", (70, 110, 220)),
    ("Rosa", (236, 110, 170)),
)
CORES_DE_MOLETOM = (
    ("Original", None),
    ("Verde", (50, 150, 80)),
    ("Laranja", (250, 140, 30)),
    ("Azul", (50, 100, 210)),
    ("Vermelho", (210, 40, 50)),
    ("Roxo", (130, 70, 200)),
    ("Preto", (52, 50, 60)),
    ("Branco", (236, 236, 240)),
    ("Amarelo", (245, 205, 50)),
)
CORES_DE_CALCA = (
    ("Original", None),
    ("Preta", (50, 50, 58)),
    ("Cinza", (130, 132, 140)),
    ("Cáqui", (190, 165, 115)),
    ("Verde-oliva", (100, 110, 60)),
    ("Vinho", (120, 40, 60)),
)

OPCOES = {
    "pele": TONS_DE_PELE,
    "cabelo": CORES_DE_CABELO,
    "moletom": CORES_DE_MOLETOM,
    "calca": CORES_DE_CALCA,
}


class Aparencia:
    """Escolhas de cor do aluno. Cada atributo só aceita uma das opções da sua lista."""

    PARTES = tuple(OPCOES)

    def __init__(self, pele="Original", cabelo="Original", moletom="Original", calca="Original"):
        self._escolhas = {}
        self.pele = pele
        self.cabelo = cabelo
        self.moletom = moletom
        self.calca = calca

    def _definir(self, parte, nome):
        nomes = [n for n, _ in OPCOES[parte]]
        if nome not in nomes:
            raise ValueError(f"{parte} inválido: {nome!r} (opções: {', '.join(nomes)})")
        self._escolhas[parte] = nome

    @property
    def pele(self):
        return self._escolhas["pele"]

    @pele.setter
    def pele(self, nome):
        self._definir("pele", nome)

    @property
    def cabelo(self):
        return self._escolhas["cabelo"]

    @cabelo.setter
    def cabelo(self, nome):
        self._definir("cabelo", nome)

    @property
    def moletom(self):
        return self._escolhas["moletom"]

    @moletom.setter
    def moletom(self, nome):
        self._definir("moletom", nome)

    @property
    def calca(self):
        return self._escolhas["calca"]

    @calca.setter
    def calca(self, nome):
        self._definir("calca", nome)

    def escolha(self, parte):
        return self._escolhas[parte]

    def cor(self, parte):
        """Cor alvo da parte, ou None se ficar como o original."""
        return dict(OPCOES[parte])[self._escolhas[parte]]

    def trocar(self, parte, passo):
        """Vai para a opção anterior (-1) ou seguinte (+1) da parte, dando a volta na lista."""
        nomes = [n for n, _ in OPCOES[parte]]
        indice = (nomes.index(self._escolhas[parte]) + passo) % len(nomes)
        self._definir(parte, nomes[indice])

    @property
    def original(self):
        return all(self.cor(parte) is None for parte in self.PARTES)

    def chave(self):
        return tuple(self._escolhas[parte] for parte in self.PARTES)

    def __eq__(self, outra):
        return isinstance(outra, Aparencia) and self.chave() == outra.chave()

    def __hash__(self):
        return hash(self.chave())

    def __str__(self):
        return ", ".join(f"{parte}: {self._escolhas[parte]}" for parte in self.PARTES)

    # Recoloração

    def recolorir(self, imagem, moletom_original="verde", cabelo_natural=True):
        """Cópia da imagem com as cores trocadas. `moletom_original` diz como achar o moletom
        na arte ("verde" ou "laranja"); `cabelo_natural=False` não mexe no cabelo (Super Saiyajin)."""
        if self.original:
            return imagem
        rgb = pygame.surfarray.array3d(imagem).astype(np.float32) / 255
        alfa = pygame.surfarray.array_alpha(imagem)
        mascaras = classificar(rgb, alfa, moletom_original, cabelo_natural)
        alvos = {"pele": self.cor("pele"), "cabelo": self.cor("cabelo"), "moletom": self.cor("moletom"),
                 "bone": self.cor("moletom"), "calca": self.cor("calca")}
        h, s, v = rgb_para_hsv(rgb)
        for parte, cor in alvos.items():
            mascara = mascaras[parte]
            if cor is None or not mascara.any():
                continue
            ref_s = max(float(np.median(s[mascara])), 1e-3)
            ref_v = max(float(np.median(v[mascara])), 1e-3)
            alvo_h, alvo_s, alvo_v = (float(x.item()) for x in rgb_para_hsv(np.array(cor, np.float32) / 255))
            h[mascara] = alvo_h
            s[mascara] = np.clip(s[mascara] / ref_s * alvo_s, 0, 1)
            v[mascara] = np.clip(v[mascara] / ref_v * alvo_v, 0, 1)
        nova = imagem.copy()
        pygame.surfarray.blit_array(nova, (hsv_para_rgb(h, s, v) * 255).round().astype(np.uint8))
        canal_alfa = pygame.surfarray.pixels_alpha(nova)
        canal_alfa[:] = alfa
        del canal_alfa   # libera a trava da superfície
        return nova


_vestidas = {}


def vestir_animacoes(animacoes, aparencia, moletom_original="verde", cabelo_natural=True):
    """Conjunto de animações com as cores da aparência (guardado em cache)."""
    if aparencia is None or aparencia.original:
        return animacoes
    from jogo.nucleo.animacao import Animacao
    chave = (id(animacoes), aparencia.chave(), moletom_original, cabelo_natural)
    if chave not in _vestidas:
        _vestidas[chave] = (animacoes, {
            nome: Animacao([aparencia.recolorir(q, moletom_original, cabelo_natural) for q in animacao.quadros],
                           animacao.fps, animacao.repetir)
            for nome, animacao in animacoes.items()})
    return _vestidas[chave][1]


def rgb_para_hsv(rgb):
    """Matiz em graus (0-360), saturação e valor (0-1), para um array (..., 3)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maximo = rgb.max(-1)
    minimo = rgb.min(-1)
    delta = np.maximum(maximo - minimo, 1e-6)
    matiz = np.where(maximo == r, ((g - b) / delta) % 6,
                     np.where(maximo == g, (b - r) / delta + 2, (r - g) / delta + 4)) * 60
    saturacao = np.where(maximo > 0, (maximo - minimo) / np.maximum(maximo, 1e-6), 0)
    return matiz, saturacao, maximo


def hsv_para_rgb(h, s, v):
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    m = v - c
    setor = (h // 60).astype(int) % 6
    zeros = np.zeros_like(c)
    tabela = [(c, x, zeros), (x, c, zeros), (zeros, c, x), (zeros, x, c), (x, zeros, c), (c, zeros, x)]
    rgb = np.zeros(h.shape + (3,), np.float32)
    for i, (r, g, b) in enumerate(tabela):
        sel = setor == i
        rgb[sel] = np.stack([r[sel], g[sel], b[sel]], -1)
    return rgb + m[..., None]


def classificar(rgb, alfa, moletom_original="verde", cabelo_natural=True):
    """Máscaras booleanas de cada parte do aluno, pela cor original de cada pixel.

    Os arrays vêm de pygame.surfarray, então o primeiro eixo é x e o segundo é y.
    """
    h, s, v = rgb_para_hsv(rgb)
    visivel = alfa > 128
    altura = rgb.shape[1]
    y = np.broadcast_to(np.arange(altura)[None, :] / altura, alfa.shape)
    contorno = v < 0.08
    base = visivel & ~contorno
    calca = base & (h >= 190) & (h < 250) & (s > 0.2)
    if moletom_original == "verde":
        moletom = base & (h >= 90) & (h < 180) & (s > 0.2)
    else:   # laranja: bem mais saturado que a pele
        moletom = base & (h >= 5) & (h < 45) & (s >= 0.85) & (v > 0.4) & (y > 0.35)
    bone = base & ((h < 12) | (h >= 330)) & (s >= 0.55) & (v > 0.2) & (y < 0.45)
    dourado = (h >= 38) & (h < 65) & (s > 0.6)
    pele = base & (h >= 5) & (h < 40) & (s >= 0.25) & (s < 0.85) & (v > 0.5) & ~moletom & ~dourado
    cabelo = np.zeros_like(base)
    if cabelo_natural:
        escuro = ((h >= 270) | (h < 55)) & (s >= 0.12) & (s < 0.62) & (v < 0.5) & (y < 0.42)
        reflexo = (h >= 10) & (h < 55) & (v >= 0.5) & (s < 0.85) & (y < 0.16)
        cabelo = base & (escuro | reflexo) & ~bone
        pele &= ~cabelo
    return {"pele": pele, "cabelo": cabelo, "moletom": moletom & ~pele, "calca": calca, "bone": bone}
