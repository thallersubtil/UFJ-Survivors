"""Materiais desenhados em pixel art para as telas de papel: papel com textura, madeira, cortiça, fita, carimbo, giz."""
import math
import random

import pygame

from jogo.nucleo.recursos import Recursos
from jogo.ui.pixel import Paleta, fonte, texto

ESC, PAPEL, PAPEL2, MARGEM, LINHA = Paleta.ESC, Paleta.PAPEL, Paleta.PAPEL2, Paleta.MARGEM, Paleta.LINHA

_cache = {}


def ruido(sup, r, cor, n, semente, tam=1):
    rnd = random.Random(semente)
    for _ in range(n):
        sup.fill(cor, (r.x + rnd.randrange(max(1, r.w)), r.y + rnd.randrange(max(1, r.h)), tam, tam))


def papel(sup, r, cor=PAPEL, semente=1, linhas=None, margem=None, sombra=True, borda=(150, 132, 100), dobra=False):
    """Folha com textura de fibras, sombra suave, linhas de caderno e canto dobrado opcional."""
    r = pygame.Rect(r)
    if sombra:
        s = pygame.Surface((r.w + 6, r.h + 6), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 60), (4, 5, r.w, r.h))
        pygame.draw.rect(s, (0, 0, 0, 40), (2, 3, r.w, r.h))
        sup.blit(s, r.topleft)
    pygame.draw.rect(sup, cor, r)
    escuro = tuple(max(0, c - 10) for c in cor)
    claro = tuple(min(255, c + 6) for c in cor)
    ruido(sup, r, escuro, r.w * r.h // 18, semente)
    ruido(sup, r, claro, r.w * r.h // 30, semente + 1)
    if linhas:
        for y in range(r.y + linhas[0], r.bottom - 3, linhas[1]):
            pygame.draw.line(sup, LINHA, (r.x + 1, y), (r.right - 2, y))
    if margem:
        pygame.draw.line(sup, MARGEM, (r.x + margem, r.y), (r.x + margem, r.bottom - 1))
    pygame.draw.rect(sup, borda, r, 1)
    if dobra:
        p = [(r.right - 14, r.bottom - 1), (r.right - 1, r.bottom - 14), (r.right - 1, r.bottom - 1)]
        pygame.draw.polygon(sup, (60, 50, 40), p)
        pygame.draw.polygon(sup, tuple(max(0, c - 30) for c in cor), [(r.right - 14, r.bottom - 1), (r.right - 1, r.bottom - 14),
                                                                      (r.right - 14, r.bottom - 14)])
        pygame.draw.lines(sup, borda, False, [(r.right - 14, r.bottom - 1), (r.right - 14, r.bottom - 14), (r.right - 1, r.bottom - 14)])


def madeira(sup, r, base=(128, 82, 48), semente=2, tabuas=22):
    r = pygame.Rect(r)
    rnd = random.Random(semente)
    for i, y in enumerate(range(r.y, r.bottom, tabuas)):
        h = min(tabuas, r.bottom - y)
        tom = tuple(max(0, min(255, c + rnd.randint(-10, 10))) for c in base)
        pygame.draw.rect(sup, tom, (r.x, y, r.w, h))
        for _ in range(r.w // 18):
            x = r.x + rnd.randrange(r.w)
            comp = rnd.randint(14, 60)
            yy = y + rnd.randint(2, max(2, h - 3))
            pygame.draw.line(sup, tuple(max(0, c - 18) for c in tom), (x, yy), (min(r.right - 1, x + comp), yy))
        pygame.draw.line(sup, tuple(max(0, c - 40) for c in base), (r.x, y), (r.right - 1, y))
        pygame.draw.line(sup, tuple(min(255, c + 18) for c in base), (r.x, y + 1), (r.right - 1, y + 1))
        if rnd.random() < 0.5:
            x = r.x + rnd.randrange(r.w)
            pygame.draw.ellipse(sup, tuple(max(0, c - 30) for c in tom), (x, y + h // 2 - 2, 6, 4))


def cortica(sup, r, semente=3):
    r = pygame.Rect(r)
    pygame.draw.rect(sup, (196, 150, 96), r)
    ruido(sup, r, (176, 128, 78), r.w * r.h // 9, semente)
    ruido(sup, r, (214, 172, 118), r.w * r.h // 14, semente + 1)
    ruido(sup, r, (150, 104, 60), r.w * r.h // 60, semente + 2, 2)


def moldura_madeira(sup, r, larg=8, base=(120, 74, 40)):
    r = pygame.Rect(r)
    pygame.draw.rect(sup, ESC, r.inflate(2 * larg + 2, 2 * larg + 2))
    pygame.draw.rect(sup, base, r.inflate(2 * larg, 2 * larg))
    pygame.draw.rect(sup, tuple(min(255, c + 30) for c in base), r.inflate(2 * larg, 2 * larg), 2)
    pygame.draw.rect(sup, tuple(max(0, c - 40) for c in base), r.inflate(2, 2), 2)


def fita(sup, centro, ang=0, w=40, h=12, cor=(240, 230, 170, 170)):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(cor)
    for x in (0, w - 1):
        for y in range(0, h, 2):
            s.set_at((x, y), (0, 0, 0, 0))
    s = pygame.transform.rotate(s, ang)
    sup.blit(s, s.get_rect(center=centro))


def tachinha(sup, c, cor=(220, 50, 60)):
    pygame.draw.circle(sup, (0, 0, 0, 80), (c[0] + 1, c[1] + 2), 4)
    pygame.draw.circle(sup, ESC, c, 4)
    pygame.draw.circle(sup, cor, c, 3)
    sup.set_at((c[0] - 1, c[1] - 1), (255, 220, 220))


def carimbo(texto_c, cor, ang, escala=1.0, tam=23, alfa=210, semente=5, borda_dupla=True):
    f = fonte(tam)
    w, h = f.size(texto_c)
    s = pygame.Surface((w + 24, h + 14), pygame.SRCALPHA)
    pygame.draw.rect(s, cor, s.get_rect(), 3, border_radius=4)
    if borda_dupla:
        pygame.draw.rect(s, cor, s.get_rect().inflate(-8, -8), 1, border_radius=3)
    texto(s, texto_c, (s.get_width() // 2, s.get_height() // 2), cor, tam, contorno=None, ancora="center")
    rnd = random.Random(semente)                        # falhas de tinta
    for _ in range(s.get_width() * s.get_height() // 14):
        x, y = rnd.randrange(s.get_width()), rnd.randrange(s.get_height())
        if s.get_at((x, y)).a:
            s.set_at((x, y), (0, 0, 0, 0))
    s = pygame.transform.rotozoom(s, ang, escala)
    s.set_alpha(alfa)
    return s


def giz(sup, t_, pos, tam=11, cor=(236, 236, 226), ancora="topleft", semente=7, progresso=1.0):
    """Texto de giz: falhas e pó. `progresso` escreve aos poucos."""
    t_ = t_[:max(0, int(len(t_) * progresso))]
    if not t_:
        return pygame.Rect(pos, (0, 0))
    img = fonte(tam, media=True).render(t_, False, cor)
    rnd = random.Random(semente + len(t_))
    for _ in range(img.get_width() * img.get_height() // 7):
        x, y = rnd.randrange(img.get_width()), rnd.randrange(img.get_height())
        if img.get_at((x, y))[:3] == cor:
            img.set_at((x, y), (*[max(0, c - 70) for c in cor], 255))
    img.set_colorkey((0, 0, 0))
    r = img.get_rect(**{ancora: pos})
    sup.blit(img, r)
    return r


def lousa(sup, r, semente=4):
    r = pygame.Rect(r)
    moldura_madeira(sup, r, 7)
    pygame.draw.rect(sup, (36, 60, 48), r)
    rnd = random.Random(semente)
    for _ in range(50):                           # marcas de giz apagado
        x, y = r.x + rnd.randrange(r.w), r.y + rnd.randrange(r.h)
        pygame.draw.line(sup, (48, 74, 60), (x, y), (x + rnd.randint(10, 40), y + rnd.randint(-3, 3)), 2)
    ruido(sup, r, (42, 68, 54), r.w * r.h // 20, semente + 1)
    pygame.draw.rect(sup, (90, 60, 34), (r.x, r.bottom, r.w, 5))                    # aparador
    pygame.draw.rect(sup, (236, 236, 226), (r.right - 50, r.bottom - 2, 16, 4))      # giz
    pygame.draw.rect(sup, (230, 120, 120), (r.right - 30, r.bottom - 2, 12, 4))


def caneta(sup, pontos, cor=MARGEM, larg=2):
    if len(pontos) > 1:
        pygame.draw.lines(sup, cor, False, pontos, larg)


def circulo_caneta(sup, r, prog, cor=MARGEM, inicio=-2.4):
    pts = [(r.centerx + r.w / 2 * math.cos(a) + math.sin(a * 3) * 2, r.centery + r.h / 2 * math.sin(a))
           for a in [inicio + j / 60 * 2 * math.pi * 1.08 * prog for j in range(61)]]
    caneta(sup, pts, cor, 2)


def fundo_desfocado(tela, caminho="cenario/centro_academico.png", escuro=150, desfoque=True):
    """Fundo da tela inteira a partir de uma arte do jogo, desfocada e escurecida (cache)."""
    chave = (caminho, escuro, desfoque)
    if chave not in _cache:
        img = pygame.transform.smoothscale(Recursos.imagem(caminho), tela.get_size())
        if desfoque:
            img = pygame.transform.smoothscale(pygame.transform.smoothscale(img, (320, 180)), tela.get_size())
        s = img.copy()
        veu = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        veu.fill((10, 8, 20, escuro))
        s.blit(veu, (0, 0))
        _cache[chave] = s
    tela.blit(_cache[chave], (0, 0))
