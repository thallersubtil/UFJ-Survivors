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


def crescer(semente, permitido):
    """Região conectada (vizinhança de 4) a partir da semente, andando só por pixels permitidos."""
    regiao = semente & permitido
    while True:
        vizinhos = regiao.copy()
        vizinhos[1:, :] |= regiao[:-1, :]
        vizinhos[:-1, :] |= regiao[1:, :]
        vizinhos[:, 1:] |= regiao[:, :-1]
        vizinhos[:, :-1] |= regiao[:, 1:]
        vizinhos &= permitido
        if (vizinhos == regiao).all():
            return regiao
        regiao = vizinhos


def preencher_buracos(mascara):
    """Inclui os pixels cercados pela máscara (ex.: os reflexos claros no meio do cabelo)."""
    fora = np.zeros_like(mascara)
    fora[0, :] = fora[-1, :] = True
    fora[:, 0] = fora[:, -1] = True
    fora = crescer(fora, ~mascara)
    return mascara | ~fora


def classificar(rgb, alfa, moletom_original="verde", cabelo_natural=True):
    """Máscaras booleanas de cada parte do aluno.

    A cor sozinha confunde partes parecidas (olhos e sobrancelhas têm o tom do cabelo; bochecha e
    sombra da pele têm o tom do moletom laranja). Por isso cada parte é a REGIÃO CONECTADA de pixels
    da sua cor que nasce no lugar certo do corpo: o cabelo a partir do topo da cabeça, o moletom a
    partir do tronco, a calça a partir das pernas. O rosto fica separado pelo contorno e pela pele.

    Os arrays vêm de pygame.surfarray, então o primeiro eixo é x e o segundo é y.
    """
    h, s, v = rgb_para_hsv(rgb)
    visivel = alfa > 128
    altura = rgb.shape[1]
    y = np.broadcast_to(np.arange(altura)[None, :] / altura, alfa.shape)
    contorno = v < 0.08
    base = visivel & ~contorno
    topo = visivel.any(0).argmax() / altura          # primeira linha com pixel visível

    tom_de_pele = (h >= 5) & (h < 40) & (s >= 0.2) & (s < 0.8) & (v > 0.55)
    cor_de_bone = base & ((h < 12) | (h >= 330)) & (s >= 0.55) & (v > 0.2) & (y < 0.45)
    bone = crescer(cor_de_bone & (y < topo + 0.1), cor_de_bone)   # só o boné, não a boca nem a bochecha

    calca_cor = base & (h >= 190) & (h < 250) & (s > 0.2)
    calca = crescer(calca_cor & (y > 0.7), calca_cor & (y > 0.5))

    if moletom_original == "verde":
        moletom_cor = base & (h >= 90) & (h < 180) & (s > 0.2)
        sombra_do_moletom = moletom_cor
    else:   # laranja: bem mais saturado que a pele
        moletom_cor = base & (h >= 5) & (h < 45) & (s >= 0.85) & (v > 0.4)
        sombra_do_moletom = base & (h >= 5) & (h < 45) & (s >= 0.6) & (v > 0.3)
    tronco = (y > 0.5) & (y < 0.65)
    capuz = (y > 0.35) & (y < 0.5) & (s >= 0.95)    # o capuz fica atrás da alça da mochila, separado do tronco
    moletom = crescer(moletom_cor & (tronco | capuz), (moletom_cor | sombra_do_moletom) & (y > 0.22))   # inclui o capuz

    cabelo = np.zeros_like(base)
    if cabelo_natural:
        cor_de_cabelo = base & ~bone & ((h >= 270) | (h < 55)) & (s >= 0.1) & (v < 0.45) & (y < 0.5) \
            & ~tom_de_pele
        cabelo = crescer(cor_de_cabelo & (y < topo + 0.08), cor_de_cabelo)
        cabelo = preencher_buracos(cabelo) & base & ~bone & (y < 0.5)
        cabelo &= ~moletom

    livre = base & tom_de_pele & ~moletom & ~cabelo & ~bone & ~calca
    rosto_e_maos = ((y > topo + 0.2) & (y < 0.45)) | ((y > 0.5) & (y < 0.8))
    pele = crescer(livre & rosto_e_maos, livre)
    if cabelo_natural:   # pontas claras do cabelo, encostadas nele e longe do rosto
        pontas = base & ~pele & ~moletom & ~bone & ~calca & ((h < 60) | (h >= 300)) & (y < topo + 0.2)
        cabelo = crescer(cabelo, cabelo | pontas)
    pele &= ~cabelo
    return {"pele": pele, "cabelo": cabelo, "moletom": moletom, "calca": calca, "bone": bone}
