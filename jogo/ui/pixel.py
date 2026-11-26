"""Kit da interface em pixel art.

Tudo é desenhado numa `CamadaPixel` de 640x360 e ampliado 2x sem suavizar, para o texto e as molduras
ficarem nítidos como no HoloCure. As funções aqui são as peças: texto com contorno, moldura, barra,
ícones e quadros dos sprites, e as curvas de animação.
"""
import math

import pygame

from jogo.config import ALTURA, FONTE, FONTE_MEDIA, LARGURA
from jogo.nucleo.recursos import Recursos

L, A = LARGURA // 2, ALTURA // 2
ESCALA = 2


class Paleta:
    ESC = (14, 10, 24)
    NAVY = (27, 31, 64)
    NAVY2 = (40, 48, 92)
    SELECAO = (60, 70, 130)
    BRANCO = (248, 244, 232)
    CINZA = (160, 156, 190)
    OURO = (255, 210, 84)
    OURO2 = (214, 150, 40)
    AZUL = (88, 190, 255)
    AZUL2 = (40, 120, 220)
    VERM = (232, 64, 80)
    VERM2 = (170, 30, 50)
    VERDE = (110, 226, 120)
    ROXO = (160, 100, 255)
    PAPEL = (246, 238, 214)
    PAPEL2 = (222, 208, 176)
    LINHA = (150, 180, 230)
    MARGEM = (220, 90, 90)
    GIZ = (236, 236, 226)
    GIZ_AMARELO = (255, 230, 120)
    VERDE_UFJ = (40, 90, 60)


class CamadaPixel:
    """Superfície de 640x360 onde a interface é desenhada; `apresentar` amplia 2x na tela."""

    def __init__(self):
        self.superficie = pygame.Surface((L, A), pygame.SRCALPHA)

    def limpar(self):
        self.superficie.fill((0, 0, 0, 0))
        return self.superficie

    def apresentar(self, tela):
        tela.blit(pygame.transform.scale(self.superficie, (L * ESCALA, A * ESCALA)), (0, 0))

    @staticmethod
    def para_camada(pos):
        """Converte uma posição da tela (mouse) para a camada."""
        return pos[0] // ESCALA, pos[1] // ESCALA


def fonte(tam=11, media=False):
    return Recursos.fonte(tam, FONTE_MEDIA if media else FONTE)


def texto(sup, t, pos, cor=Paleta.BRANCO, tam=11, contorno=Paleta.ESC, ancora="topleft", media=False, alfa=255):
    """Texto nítido (sem suavizar) com contorno de 1 px. Use tamanho 11 ou 23, que ficam limpos nesta escala."""
    f = fonte(tam, media)
    img = f.render(t, False, cor)
    r = img.get_rect(**{ancora: pos})
    if contorno is not None:
        borda = f.render(t, False, contorno)
        if alfa < 255:
            borda.set_alpha(alfa)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            sup.blit(borda, r.move(dx, dy))
    if alfa < 255:
        img.set_alpha(alfa)
    sup.blit(img, r)
    return r


def quebrar(t, f, largura):
    linhas, atual = [], ""
    for palavra in t.split():
        tentativa = f"{atual} {palavra}".strip()
        if f.size(tentativa)[0] <= largura or not atual:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def clarear(cor, q=28):
    return tuple(min(255, c + q) for c in cor[:3])


def escurecer_cor(cor, q=50):
    return tuple(max(0, c - q) for c in cor[:3])


def moldura(sup, r, fundo=Paleta.NAVY, borda=Paleta.BRANCO, escura=Paleta.ESC, raio=3, brilho=True, alfa=255):
    """Painel: contorno escuro, borda clara, fundo e um brilho de 1 px no topo."""
    r = pygame.Rect(r)
    alvo = sup if alfa == 255 else pygame.Surface(r.size, pygame.SRCALPHA)
    base = r if alfa == 255 else pygame.Rect(0, 0, *r.size)
    pygame.draw.rect(alvo, escura, base, border_radius=raio + 1)
    pygame.draw.rect(alvo, borda, base.inflate(-2, -2), border_radius=raio)
    pygame.draw.rect(alvo, fundo, base.inflate(-6, -6), border_radius=max(0, raio - 1))
    if brilho:
        pygame.draw.line(alvo, clarear(fundo), (base.left + 4, base.top + 3), (base.right - 5, base.top + 3))
    if alfa != 255:
        alvo.set_alpha(alfa)
        sup.blit(alvo, r)


def barra(sup, r, frac, cor, cor2=None, fundo=(30, 24, 44), atraso=None, segmentos=0, brilho_t=None):
    """Barra pixelada. `atraso`: parte branca do dano recente. `brilho_t`: varredura de brilho."""
    r = pygame.Rect(r)
    pygame.draw.rect(sup, Paleta.ESC, r)
    dentro = r.inflate(-2, -2)
    pygame.draw.rect(sup, fundo, dentro)
    frac = max(0.0, min(1.0, frac))
    if atraso is not None and atraso > frac:
        pygame.draw.rect(sup, Paleta.BRANCO, (dentro.x, dentro.y, int(dentro.w * min(1.0, atraso)), dentro.h))
    w = int(dentro.w * frac)
    if w > 0:
        pygame.draw.rect(sup, cor, (dentro.x, dentro.y, w, dentro.h))
        if cor2 is not None:
            h2 = max(1, dentro.h // 3)
            pygame.draw.rect(sup, cor2, (dentro.x, dentro.bottom - h2, w, h2))
        pygame.draw.line(sup, clarear(cor, 60), (dentro.x, dentro.y), (dentro.x + w - 1, dentro.y))
        if brilho_t is not None:
            x = dentro.x + int((brilho_t % 1.0) * (dentro.w + 30)) - 15
            for i in range(6):
                xx = x + i
                if dentro.x <= xx < dentro.x + w:
                    pygame.draw.line(sup, Paleta.BRANCO, (xx, dentro.y), (xx - 3, dentro.bottom - 1))
    for i in range(1, segmentos):
        x = dentro.x + dentro.w * i // segmentos
        pygame.draw.line(sup, Paleta.ESC, (x, dentro.y), (x, dentro.bottom - 1))


def icone(caminho, tam):
    return Recursos.icone(caminho, tam)


_quadros = {}


def quadros(pasta, nome="parado-4.png", altura=None):
    """Os 4 quadros de uma folha de sprite, recortados e na altura pedida (cache)."""
    chave = (pasta, nome, altura)
    if chave not in _quadros:
        folha = Recursos.imagem(f"sprites/{pasta}/{nome}")
        q = folha.get_width() // 4
        lista = []
        for i in range(4):
            fr = folha.subsurface((i * q, 0, q, folha.get_height())).copy()
            caixa = fr.get_bounding_rect()
            if caixa.w and caixa.h:
                fr = fr.subsurface(caixa).copy()
            if altura:
                fr = pygame.transform.scale(fr, (max(1, round(fr.get_width() * altura / fr.get_height())), altura))
            lista.append(fr)
        _quadros[chave] = lista
    return _quadros[chave]


_bonecos = {}


def boneco_nitido(pasta, animacao="andar", altura=None):
    """Quadros do boneco na arte grande (assets/retratos/chibis/<pasta>), para desenhar direto na tela: ampliar o
    sprite da partida pela camada deixaria o traço serrilhado ou fora de foco. `altura` reduz (suavizando).
    Devolve None se a classe não tem essa arte."""
    chave = (pasta, animacao, altura)
    if chave not in _bonecos:
        tiras = sorted((Recursos.pasta / "retratos" / "chibis" / pasta).glob(f"{animacao}-*.png"))
        lista = None
        if tiras:
            n = int(tiras[0].stem.split("-")[-1])
            tira = Recursos.imagem(f"retratos/chibis/{pasta}/{tiras[0].name}")
            largura = tira.get_width() // n
            lista = [tira.subsurface((i * largura, 0, largura, tira.get_height())) for i in range(n)]
            if altura and altura != tira.get_height():
                novo = (max(1, round(largura * altura / tira.get_height())), altura)
                lista = [pygame.transform.smoothscale(q, novo) for q in lista]
        _bonecos[chave] = lista
    return _bonecos[chave]


def no_quadrado(img, altura):
    """Redimensiona um quadro já carregado para `altura`, sem suavizar."""
    return pygame.transform.scale(img, (max(1, round(img.get_width() * altura / img.get_height())), altura))


# ---------- curvas de animação

def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_back(t, s=1.7):
    t = max(0.0, min(1.0, t)) - 1
    return t * t * ((s + 1) * t + s) + 1


def janela(t, inicio, dur):
    """0 antes de `inicio`, de 0 a 1 durante `dur`, 1 depois."""
    return max(0.0, min(1.0, (t - inicio) / dur))


def onda(t, freq=1.0, amp=1.0):
    return math.sin(t * freq * 2 * math.pi) * amp


def piscar(t, freq=5.0):
    """De 0,55 a 1, para bordas que piscam."""
    return 0.55 + 0.45 * abs(math.sin(t * freq))
