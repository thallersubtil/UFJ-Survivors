"""Partes do boneco do aluno: corpo, penteado, olhos, roupa de cima, roupa de baixo e acessório.

Cada parte é uma classe que sabe se desenhar (polimorfismo): o Boneco não sabe se o
cabelo é longo ou espetado, só chama `desenhar_tras`/`desenhar_frente` do penteado.
As coordenadas são em pixels de tela, com o chão em y = 0 e o boneco olhando para a direita.
O `Pincel` desenha tudo com contorno grosso numa superfície ampliada, que o Boneco reduz
suavizando no fim (é isso que deixa as bordas lisas).
"""
import math
from abc import ABC, abstractmethod

import pygame

CONTORNO = (28, 22, 34)
SAPATO = (62, 56, 74)
BRANCO = (246, 244, 240)
DOURADO = (255, 214, 64)


def escurecer(cor, fator=0.78):
    return tuple(round(c * fator) for c in cor)


def clarear(cor, fator=0.35):
    return tuple(round(c + (255 - c) * fator) for c in cor)


def entre(a, b, t):
    """Ponto a uma fração `t` do caminho de `a` até `b`."""
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


class Pincel:
    """Desenha formas com contorno numa superfície `k` vezes maior que a tela."""

    def __init__(self, superficie, origem, k, espessura):
        self.superficie = superficie
        self.origem = origem
        self.k = k
        self.espessura = espessura

    def ponto(self, p):
        return (self.origem[0] + p[0] * self.k, self.origem[1] + p[1] * self.k)

    def _capsula(self, a, b, raio, cor):
        pa, pb = pygame.Vector2(self.ponto(a)), pygame.Vector2(self.ponto(b))
        r = raio * self.k
        pygame.draw.circle(self.superficie, cor, pa, r)
        pygame.draw.circle(self.superficie, cor, pb, r)
        direcao = pb - pa
        if direcao.length_squared() > 0:
            normal = pygame.Vector2(-direcao.y, direcao.x).normalize() * r
            pygame.draw.polygon(self.superficie, cor, (pa + normal, pb + normal, pb - normal, pa - normal))

    def capsula(self, a, b, raio, cor, contorno=True):
        """Segmento de pontas redondas (braço, perna, mecha de cabelo)."""
        if contorno:
            self._capsula(a, b, raio + self.espessura, CONTORNO)
        self._capsula(a, b, raio, cor)

    def linha(self, a, b, largura, cor):
        self._capsula(a, b, largura / 2, cor)

    def circulo(self, centro, raio, cor, contorno=True):
        if contorno:
            pygame.draw.circle(self.superficie, CONTORNO, self.ponto(centro), (raio + self.espessura) * self.k)
        pygame.draw.circle(self.superficie, cor, self.ponto(centro), raio * self.k)

    def anel(self, centro, raio, largura, cor):
        pygame.draw.circle(self.superficie, cor, self.ponto(centro), raio * self.k, max(1, round(largura * self.k)))

    def elipse(self, centro, rx, ry, cor, contorno=True):
        def retangulo(folga):
            x, y = self.ponto(centro)
            return pygame.Rect(round(x - (rx + folga) * self.k), round(y - (ry + folga) * self.k),
                               round((rx + folga) * 2 * self.k), round((ry + folga) * 2 * self.k))
        if contorno:
            pygame.draw.ellipse(self.superficie, CONTORNO, retangulo(self.espessura))
        pygame.draw.ellipse(self.superficie, cor, retangulo(0))

    def poligono(self, pontos, cor, contorno=True):
        if contorno:
            for a, b in zip(pontos, pontos[1:] + pontos[:1]):
                self._capsula(a, b, self.espessura, CONTORNO)
        pygame.draw.polygon(self.superficie, cor, [self.ponto(p) for p in pontos])

    def arco(self, centro, raio, inicio, fim, largura, cor):
        """Arco de circunferência (ângulos em radianos, sentido da tela) desenhado com segmentos redondos."""
        passos = max(2, int(abs(fim - inicio) / 0.2))
        pontos = [(centro[0] + raio * math.cos(inicio + (fim - inicio) * i / passos),
                   centro[1] + raio * math.sin(inicio + (fim - inicio) * i / passos)) for i in range(passos + 1)]
        for a, b in zip(pontos, pontos[1:]):
            self.linha(a, b, largura, cor)


class Parte(ABC):
    """Uma parte trocável do boneco. NOME é o que aparece na personalização."""

    NOME = ""

    def __str__(self):
        return self.NOME


# Corpo: o gênero muda as proporções do tronco e detalhes do rosto

class Corpo(Parte, ABC):
    RAIO_CABECA = 16

    @property
    @abstractmethod
    def LARGURAS(self):
        """Meia largura do tronco nos ombros, na cintura e no quadril."""

    def desenhar_cabeca(self, p, e, aparencia):
        cx, cy = e["cabeca"]
        pele = aparencia.cor("pele")
        p.elipse((cx, cy), self.RAIO_CABECA, self.RAIO_CABECA - 1, pele)
        p.elipse((cx - 7, cy + 4), 5, 6, escurecer(pele, 0.9), contorno=False)   # sombra do lado de trás
        p.elipse((cx - 6, cy + 3), 2.8, 3.5, pele)                              # orelha
        p.linha((cx - 6.3, cy + 1.8), (cx - 5.8, cy + 4.2), 1.0, escurecer(pele, 0.7))
        p.linha((cx + 7, cy + 9.2), (cx + 10.5, cy + 9.6), 1.3, CONTORNO)    # boca
        self.detalhes_do_rosto(p, e, aparencia)

    def detalhes_do_rosto(self, p, e, aparencia):
        """Gancho para o que muda no rosto de cada corpo."""

    def cilios(self, p, e):
        """Cílios no canto de fora de cada olho."""


class CorpoMasculino(Corpo):
    NOME = "Masculino"
    LARGURAS = (10.5, 9.5, 9.5)


class CorpoFeminino(Corpo):
    NOME = "Feminino"
    LARGURAS = (8.5, 7.0, 10.0)

    def detalhes_do_rosto(self, p, e, aparencia):
        cx, cy = e["cabeca"]
        rubor = (240, 140, 150)
        p.elipse((cx + 12, cy + 7), 2.4, 1.3, rubor, contorno=False)
        p.elipse((cx + 2, cy + 7), 2.2, 1.2, rubor, contorno=False)

    def cilios(self, p, e):
        cx, cy = e["cabeca"]
        for x in (cx + 3, cx + 11):
            p.linha((x + 1.8, cy - 1.2), (x + 3.4, cy - 2.6), 1.1, CONTORNO)


# Olhos

class Olhos(Parte, ABC):
    def centros(self, e):
        cx, cy = e["cabeca"]
        return (cx + 3, cy + 2), (cx + 11, cy + 2)

    def desenhar(self, p, e, corpo, aparencia, piscando):
        cabelo = aparencia.cor("cabelo")
        for x, y in self.centros(e):
            p.linha((x - 1.6, y - 4.6), (x + 1.8, y - 5.0), 1.3, escurecer(cabelo, 0.7))   # sobrancelha
            if piscando:
                p.linha((x - 2, y + 0.5), (x + 2, y + 0.5), 1.3, CONTORNO)
            else:
                self.desenhar_olho(p, (x, y), aparencia)
        if not piscando:
            corpo.cilios(p, e)

    @abstractmethod
    def desenhar_olho(self, p, centro, aparencia):
        """Um olho aberto."""


class OlhosNormais(Olhos):
    NOME = "Normais"

    def desenhar_olho(self, p, centro, aparencia):
        x, y = centro
        p.elipse((x, y), 1.8, 2.8, CONTORNO, contorno=False)
        p.circulo((x + 0.6, y - 1.0), 0.7, BRANCO, contorno=False)


class OlhosAnime(Olhos):
    NOME = "Anime"

    def desenhar_olho(self, p, centro, aparencia):
        x, y = centro
        p.elipse((x, y + 0.3), 2.7, 3.9, CONTORNO, contorno=False)
        p.elipse((x, y + 1.0), 1.9, 2.8, clarear(escurecer(aparencia.cor("cabelo"), 0.8), 0.15), contorno=False)
        p.circulo((x + 0.8, y - 1.2), 1.0, BRANCO, contorno=False)
        p.circulo((x - 0.8, y + 2.0), 0.5, BRANCO, contorno=False)
        p.linha((x - 2.8, y - 3.4), (x + 2.8, y - 3.8), 1.4, CONTORNO)


class OlhosSonolentos(Olhos):
    NOME = "Sonolentos"

    def desenhar_olho(self, p, centro, aparencia):
        x, y = centro
        p.elipse((x, y + 1.0), 2.0, 1.4, CONTORNO, contorno=False)
        p.linha((x - 2.4, y - 0.4), (x + 2.4, y - 0.4), 1.2, CONTORNO)


# Penteados: uma parte atrás da cabeça e outra na frente

def calota(p, centro, raio, cor, franja_y, pontas=4, fundo=0.55, profundidade=3.0):
    """Cabelo que cobre o alto e a nuca, com a franja em zigue-zague na testa."""
    cx, cy = centro
    inicio, fim = math.pi - fundo, 2 * math.pi - 0.3
    passos = 14
    arco = [(cx + (raio + 1.5) * math.cos(inicio + (fim - inicio) * i / passos),
             cy + (raio + 1.5) * math.sin(inicio + (fim - inicio) * i / passos)) for i in range(passos + 1)]
    frente, tras = arco[-1], arco[0]
    franja = []
    for i in range(1, 2 * pontas + 1):
        t = i / (2 * pontas + 1)
        x = frente[0] + (tras[0] - frente[0]) * t
        y = franja_y + (tras[1] - franja_y) * t ** 2
        franja.append((x, y + (profundidade if i % 2 else 0)))
    p.poligono(arco + [(frente[0], franja_y)] + franja, cor)
    p.arco((cx - 2, cy - 2), raio - 3, math.pi * 1.25, math.pi * 1.5, 1.6, clarear(cor, 0.4))   # brilho


class Penteado(Parte, ABC):
    def desenhar_tras(self, p, e, cor, balanco):
        """Parte do cabelo atrás da cabeça e do corpo (por padrão nenhuma)."""

    @abstractmethod
    def desenhar_frente(self, p, e, cor, balanco):
        """Parte do cabelo por cima da cabeça."""


class PenteadoCurto(Penteado):
    NOME = "Curto"

    def desenhar_frente(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        calota(p, (cx, cy), 16, cor, cy - 5, pontas=4)


class PenteadoEspetado(Penteado):
    NOME = "Espetado"
    PONTAS = ((200, 9), (225, 11), (250, 12), (275, 12), (300, 11), (325, 8))

    def desenhar_tras(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        for angulo, tamanho in self.PONTAS:
            a, largura = math.radians(angulo), 0.32
            base1 = (cx + 14 * math.cos(a - largura), cy + 14 * math.sin(a - largura))
            base2 = (cx + 14 * math.cos(a + largura), cy + 14 * math.sin(a + largura))
            ponta = (cx + (16 + tamanho) * math.cos(a) + balanco * 0.3, cy + (16 + tamanho) * math.sin(a))
            p.poligono([base1, ponta, base2], cor)

    def desenhar_frente(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        calota(p, (cx, cy), 16, cor, cy - 6, pontas=3, profundidade=4)


class PenteadoSuperSaiyajin(PenteadoEspetado):
    """Só aparece no especial do Otaku: espetado, maior e dourado, seja qual for o cabelo."""

    NOME = "Super Saiyajin"
    PONTAS = ((190, 12), (212, 16), (236, 19), (260, 21), (284, 19), (308, 16), (332, 11))

    def desenhar_tras(self, p, e, cor, balanco):
        super().desenhar_tras(p, e, DOURADO, balanco)

    def desenhar_frente(self, p, e, cor, balanco):
        super().desenhar_frente(p, e, DOURADO, balanco)


class PenteadoFranja(Penteado):
    NOME = "Chanel"

    def desenhar_tras(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        p.poligono([(cx - 18, cy - 6), (cx + 6, cy - 14), (cx + 8, cy + 13), (cx - 18 + balanco * 0.3, cy + 14)],
                   cor)

    def desenhar_frente(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        calota(p, (cx, cy), 16, cor, cy - 3, pontas=5, fundo=1.1, profundidade=1.5)


class PenteadoLongo(Penteado):
    NOME = "Longo"

    def desenhar_tras(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        p.poligono([(cx - 17, cy - 8), (cx + 5, cy - 15), (cx + 6, cy + 14),
                    (cx + 2 + balanco, cy + 30), (cx - 19 + balanco, cy + 31), (cx - 20, cy + 10)], cor)

    def desenhar_frente(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        calota(p, (cx, cy), 16, cor, cy - 4, pontas=4, fundo=1.2)


class PenteadoRaboDeCavalo(Penteado):
    NOME = "Rabo de cavalo"

    def desenhar_tras(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        prende = (cx - 15, cy - 7)
        meio = (cx - 23 + balanco * 0.5, cy + 3)
        ponta = (cx - 24 + balanco * 1.3, cy + 17)
        p.capsula(meio, ponta, 3.2, cor)
        p.capsula(prende, meio, 4.6, cor)

    def desenhar_frente(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        calota(p, (cx, cy), 16, cor, cy - 5, pontas=3, profundidade=2)
        p.circulo((cx - 15, cy - 7), 2.2, (230, 70, 110))                     # elástico


class PenteadoCoque(Penteado):
    NOME = "Coque"

    def desenhar_tras(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        p.circulo((cx - 7, cy - 17), 7.5, cor)

    def desenhar_frente(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        calota(p, (cx, cy), 16, cor, cy - 5, pontas=3, profundidade=2)


class PenteadoBlackPower(Penteado):
    NOME = "Black power"

    def desenhar_tras(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        for dx, dy in ((-10, -14), (2, -18), (12, -12), (-16, -2), (-14, 9), (-2, -8)):
            p.circulo((cx + dx, cy + dy), 11, cor)

    def desenhar_frente(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        calota(p, (cx, cy), 16, cor, cy - 6, pontas=5, profundidade=1.5)


class Careca(Penteado):
    NOME = "Careca"

    def desenhar_frente(self, p, e, cor, balanco):
        cx, cy = e["cabeca"]
        p.arco((cx - 1, cy - 1), 12, math.pi * 1.25, math.pi * 1.5, 2.0, BRANCO)   # brilho


# Roupa de cima: o tronco e as mangas

class RoupaDeCima(Parte, ABC):
    MANGA = 1.0                   # fração do braço coberta pela manga
    GOLA = None                   # (rx, ry) do decote mostrando a pele

    def desenhar_tronco(self, p, e, corpo, aparencia):
        cor = aparencia.cor("cor_cima")
        ombro, cintura, quadril = corpo.LARGURAS
        y_ombro, y_quadril = e["ombro_y"], e["quadril_y"]
        y_cintura = y_ombro + 9
        p.poligono([(-ombro, y_ombro + 1), (-ombro + 3, y_ombro - 1), (ombro - 3, y_ombro - 1), (ombro, y_ombro + 1),
                    (cintura, y_cintura), (quadril, y_quadril + 3), (-quadril, y_quadril + 3), (-cintura, y_cintura)],
                   cor)
        p.poligono([(-ombro + 1.5, y_ombro + 1), (-ombro + 5, y_ombro + 1), (-quadril + 5, y_quadril + 2),
                    (-quadril + 1.5, y_quadril + 2)], escurecer(cor, 0.85), contorno=False)
        if self.GOLA:
            p.elipse((1.5, y_ombro), *self.GOLA, aparencia.cor("pele"))
        self.detalhes(p, e, corpo, aparencia, cor)

    def detalhes(self, p, e, corpo, aparencia, cor):
        """Gancho para bolso, capuz, zíper..."""

    def desenhar_braco(self, p, ombro, mao, aparencia, sombra):
        pele = aparencia.cor("pele")
        cor = aparencia.cor("cor_cima")
        if sombra:
            pele, cor = escurecer(pele, 0.85), escurecer(cor, 0.8)
        if self.MANGA < 1:
            p.capsula(ombro, mao, 2.9, pele)
        if self.MANGA > 0:
            p.capsula(ombro, entre(ombro, mao, self.MANGA), 3.5, cor)
        p.circulo(mao, 3.5, pele)


class Moletom(RoupaDeCima):
    NOME = "Moletom"

    def detalhes(self, p, e, corpo, aparencia, cor):
        y_ombro, y_quadril = e["ombro_y"], e["quadril_y"]
        p.elipse((-3, y_ombro), 7, 2.6, escurecer(cor, 0.75))                    # capuz
        p.linha((2.5, y_ombro + 2), (2.5, y_ombro + 8), 1.0, BRANCO)              # cordões
        p.linha((5.5, y_ombro + 2), (5.5, y_ombro + 7), 1.0, BRANCO)
        p.poligono([(-3, y_quadril - 6), (7, y_quadril - 6), (8, y_quadril - 1), (-4, y_quadril - 1)],
                   escurecer(cor, 0.88))                                           # bolso


class Camiseta(RoupaDeCima):
    NOME = "Camiseta"
    MANGA = 0.4
    GOLA = (3.6, 1.8)


class Jaqueta(RoupaDeCima):
    NOME = "Jaqueta"

    def detalhes(self, p, e, corpo, aparencia, cor):
        y_ombro, y_quadril = e["ombro_y"], e["quadril_y"]
        p.poligono([(0.5, y_ombro - 0.5), (6.5, y_ombro - 0.5), (5.5, y_quadril + 2.5), (1.5, y_quadril + 2.5)], BRANCO)
        p.linha((0.5, y_ombro), (3, y_ombro + 7), 1.2, escurecer(cor, 0.7))      # lapela
        p.linha((6.5, y_ombro), (4.5, y_ombro + 7), 1.2, escurecer(cor, 0.7))


class Regata(RoupaDeCima):
    NOME = "Regata"
    MANGA = 0.0
    GOLA = (4.8, 2.6)


# Roupa de baixo: as pernas, o quadril e (a saia) por cima do tronco

class RoupaDeBaixo(Parte, ABC):
    COMPRIMENTO = 1.0             # fração da perna coberta

    def desenhar_perna(self, p, quadril, pe, aparencia, sombra):
        pele, cor = aparencia.cor("pele"), aparencia.cor("cor_baixo")
        sapato = SAPATO
        if sombra:
            pele, cor, sapato = escurecer(pele, 0.85), escurecer(cor, 0.8), escurecer(SAPATO, 0.8)
        tornozelo = (pe[0], pe[1] - 1.5)
        if self.COMPRIMENTO < 1:
            p.capsula(quadril, tornozelo, 3.4, pele)
        if self.COMPRIMENTO > 0:
            p.capsula(quadril, entre(quadril, tornozelo, self.COMPRIMENTO), 4.0, cor)
        p.elipse((pe[0] + 2.2, pe[1]), 5.2, 2.8, sapato)

    def desenhar_quadril(self, p, e, corpo, aparencia):
        if self.COMPRIMENTO <= 0:
            return
        largura = corpo.LARGURAS[2]
        y = e["quadril_y"]
        p.poligono([(-largura, y - 3), (largura, y - 3), (largura + 0.5, y + 4), (-largura - 0.5, y + 4)],
                   aparencia.cor("cor_baixo"))

    def desenhar_sobre_tronco(self, p, e, corpo, aparencia, balanco):
        """Gancho para o que fica por cima da camisa (a saia)."""


class Calca(RoupaDeBaixo):
    NOME = "Calça"


class Bermuda(RoupaDeBaixo):
    NOME = "Bermuda"
    COMPRIMENTO = 0.55


class Saia(RoupaDeBaixo):
    NOME = "Saia"
    COMPRIMENTO = 0.0

    def desenhar_sobre_tronco(self, p, e, corpo, aparencia, balanco):
        cor = aparencia.cor("cor_baixo")
        largura = corpo.LARGURAS[2]
        y = e["quadril_y"]
        balanco *= 0.4
        p.poligono([(-largura + 0.5, y - 2), (largura - 0.5, y - 2), (largura + 4 + balanco, y + 9),
                    (-largura - 4 + balanco, y + 9)], cor)
        for x in (-4, 1, 6):
            p.linha((x * 0.6, y + 1), (x + balanco * 0.5, y + 8), 0.9, escurecer(cor, 0.75))


# Acessórios

class Acessorio(Parte, ABC):
    @abstractmethod
    def desenhar(self, p, e, aparencia):
        """Desenha o acessório por cima da cabeça."""


class SemAcessorio(Acessorio):
    NOME = "Nenhum"

    def desenhar(self, p, e, aparencia):
        pass


class Oculos(Acessorio):
    NOME = "Óculos"

    def desenhar(self, p, e, aparencia):
        cx, cy = e["cabeca"]
        for x in (cx + 3, cx + 11):
            p.anel((x, cy + 2), 3.9, 1.3, CONTORNO)
        p.linha((cx + 6.9, cy + 1.5), (cx + 7.1, cy + 1.5), 1.3, CONTORNO)
        p.linha((cx - 0.9, cy + 1.5), (cx - 5, cy + 1), 1.3, CONTORNO)


class Bone(Acessorio):
    NOME = "Boné"

    def desenhar(self, p, e, aparencia):
        cx, cy = e["cabeca"]
        cor = escurecer(aparencia.cor("cor_cima"), 0.9)
        passos = 12
        inicio, fim = math.pi - 0.15, 2 * math.pi - 0.05
        copa = [(cx + 17.5 * math.cos(inicio + (fim - inicio) * i / passos),
                 cy - 1 + 17.5 * math.sin(inicio + (fim - inicio) * i / passos)) for i in range(passos + 1)]
        p.poligono(copa, cor)
        p.poligono([(cx + 8, cy - 5), (cx + 26, cy - 3), (cx + 25, cy), (cx + 8, cy - 1)], escurecer(cor, 0.85))
        p.circulo((cx - 1, cy - 18), 1.6, escurecer(cor, 0.8))


class Fone(Acessorio):
    NOME = "Fone"

    def desenhar(self, p, e, aparencia):
        cx, cy = e["cabeca"]
        p.arco((cx - 3, cy + 1), 18, math.pi * 1.05, math.pi * 1.62, 3.4, CONTORNO)
        p.arco((cx - 3, cy + 1), 18, math.pi * 1.05, math.pi * 1.62, 1.6, (90, 90, 104))
        p.elipse((cx - 6, cy + 3), 3.8, 5.0, (230, 60, 80))


class Laco(Acessorio):
    NOME = "Laço"

    def desenhar(self, p, e, aparencia):
        cx, cy = e["cabeca"]
        centro = (cx - 6, cy - 16)
        cor = (235, 80, 125)
        p.poligono([centro, (centro[0] - 8, centro[1] - 5), (centro[0] - 8, centro[1] + 4)], cor)
        p.poligono([centro, (centro[0] + 8, centro[1] - 5), (centro[0] + 8, centro[1] + 4)], cor)
        p.circulo(centro, 2.3, escurecer(cor, 0.85))


def _catalogo(*classes):
    return {classe.NOME: classe for classe in classes}


CORPOS = _catalogo(CorpoMasculino, CorpoFeminino)
PENTEADOS = _catalogo(PenteadoCurto, PenteadoEspetado, PenteadoFranja, PenteadoLongo, PenteadoRaboDeCavalo,
                      PenteadoCoque, PenteadoBlackPower, Careca)
OLHOS = _catalogo(OlhosNormais, OlhosAnime, OlhosSonolentos)
ROUPAS_DE_CIMA = _catalogo(Moletom, Camiseta, Jaqueta, Regata)
ROUPAS_DE_BAIXO = _catalogo(Calca, Bermuda, Saia)
ACESSORIOS = _catalogo(SemAcessorio, Oculos, Bone, Fone, Laco)
