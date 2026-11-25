"""Carrega imagens, fontes e sons uma vez só, com substitutos quando falta arquivo."""
import re
import zlib
from pathlib import Path

import pygame

from jogo.config import ESCALA_PIXEL, FONTE, PASTA_ASSETS
from jogo.nucleo.animacao import Animacao


class SomMudo:
    """Som que não toca nada. Usado quando o arquivo ou o áudio não existem."""

    def play(self, *args, **kwargs):
        pass

    def set_volume(self, *args):
        pass


class Recursos:
    pasta = PASTA_ASSETS
    _imagens = {}
    _derivadas = {}
    _fontes = {}
    _sons = {}
    _ultimo_toque = {}
    INTERVALO_MINIMO_SOM_MS = 45

    @classmethod
    def imagem(cls, caminho, altura=None):
        chave = (caminho, altura)
        if chave not in cls._imagens:
            arquivo = cls.pasta / caminho
            img = None
            if caminho and arquivo.is_file():
                try:
                    img = pygame.image.load(str(arquivo))
                    if pygame.display.get_surface() is not None:
                        img = img.convert_alpha()
                except pygame.error:
                    img = None
            if img is None:
                img = cls.substituto(Path(caminho).stem or "?", altura or 48)
            if altura and img.get_height() != altura:
                largura = max(1, round(img.get_width() * altura / img.get_height()))
                img = cls._redimensionar(img, (largura, int(altura)))
            cls._imagens[chave] = img
        return cls._imagens[chave]

    @classmethod
    def icone(cls, caminho, tamanho):
        """Imagem reduzida para caber num quadrado de `tamanho` pixels."""
        chave = ("icone", caminho, tamanho)
        if chave not in cls._derivadas:
            img = cls.imagem(caminho)
            fator = tamanho / max(img.get_size())
            novo = (max(1, round(img.get_width() * fator)), max(1, round(img.get_height() * fator)))
            cls._derivadas[chave] = cls._redimensionar(img, novo)
        return cls._derivadas[chave]

    @staticmethod
    def _redimensionar(img, tamanho):
        """Ampliar é sempre com vizinho mais próximo (pixel nítido); só reduzir suaviza."""
        if tamanho[0] >= img.get_width() or tamanho[1] >= img.get_height():
            return pygame.transform.scale(img, tamanho)
        try:
            return pygame.transform.smoothscale(img, tamanho)
        except ValueError:
            return pygame.transform.scale(img, tamanho)

    @staticmethod
    def ampliar(img, fator):
        """Amplia por um fator inteiro sem suavizar: cada pixel vira um bloco fator x fator."""
        if fator == 1:
            return img
        return pygame.transform.scale(img, (img.get_width() * fator, img.get_height() * fator))

    @classmethod
    def imagem_pixel(cls, caminho, escala=ESCALA_PIXEL):
        """Imagem de pixel art em resolução nativa, ampliada sem suavizar."""
        chave = ("pixel", caminho, escala)
        if chave not in cls._derivadas:
            cls._derivadas[chave] = cls.ampliar(cls.imagem(caminho), escala)
        return cls._derivadas[chave]

    @classmethod
    def na_altura(cls, imagem, altura):
        """Cópia (em cache) de uma imagem já carregada, redimensionada para `altura`."""
        chave = ("altura", id(imagem), altura)
        if chave not in cls._derivadas:
            largura = max(1, round(imagem.get_width() * altura / imagem.get_height()))
            try:
                cls._derivadas[chave] = pygame.transform.smoothscale(imagem, (largura, altura))
            except ValueError:
                cls._derivadas[chave] = pygame.transform.scale(imagem, (largura, altura))
        return cls._derivadas[chave]

    FPS_PADRAO = {"parado": 5, "andar": 8, "mover": 10, "atacar": 10}
    NAO_REPETE = {"atacar"}

    @classmethod
    def animacoes(cls, pasta, escala=1):
        """Lê as tiras assets/sprites/<pasta>/<nome>-<n>.png (n quadros de mesma largura, já no tamanho de tela)."""
        chave = ("animacoes", pasta, escala)
        if chave not in cls._derivadas:
            resultado = {}
            diretorio = cls.pasta / "sprites" / pasta
            for arquivo in sorted(diretorio.glob("*-*.png")) if diretorio.is_dir() else ():
                achado = re.fullmatch(r"(.+)-(\d+)", arquivo.stem)
                if not achado:
                    continue
                nome, n = achado.group(1), int(achado.group(2))
                tira = pygame.image.load(str(arquivo))
                if pygame.display.get_surface() is not None:
                    tira = tira.convert_alpha()
                largura = tira.get_width() // n
                quadros = [cls.ampliar(tira.subsurface((i * largura, 0, largura, tira.get_height())).copy(), escala)
                           for i in range(n)]
                resultado[nome] = Animacao(quadros, cls.FPS_PADRAO.get(nome, 8), nome not in cls.NAO_REPETE)
            cls._derivadas[chave] = resultado
        return cls._derivadas[chave]

    @classmethod
    def animacoes_ou_imagem(cls, pasta, imagem, altura, escala=1):
        """Animações da pasta; sem elas, uma animação 'parado' com a imagem estática (ou o substituto)."""
        animacoes = cls.animacoes(pasta, escala) if pasta else {}
        return animacoes or {"parado": Animacao([cls.imagem(imagem, altura)])}

    @classmethod
    def silhueta_branca(cls, imagem):
        chave = ("branca", id(imagem))
        if chave not in cls._derivadas:
            branca = imagem.copy()
            branca.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            cls._derivadas[chave] = branca
        return cls._derivadas[chave]

    @classmethod
    def espelhada(cls, imagem):
        chave = ("espelho", id(imagem))
        if chave not in cls._derivadas:
            cls._derivadas[chave] = pygame.transform.flip(imagem, True, False)
        return cls._derivadas[chave]

    @classmethod
    def rotacionada(cls, imagem, angulo):
        passo = int(round(angulo / 6.0)) * 6 % 360
        chave = ("giro", id(imagem), passo)
        if chave not in cls._derivadas:
            cls._derivadas[chave] = pygame.transform.rotate(imagem, passo)
        return cls._derivadas[chave]

    @staticmethod
    def substituto(nome, altura):
        """Círculo colorido com a inicial do nome, para quando falta a arte."""
        tamanho = max(8, int(altura))
        sup = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        cor = pygame.Color(0)
        cor.hsva = (zlib.crc32(nome.encode()) % 360, 60, 90, 100)
        centro = (tamanho // 2, tamanho // 2)
        pygame.draw.circle(sup, cor, centro, tamanho // 2)
        pygame.draw.circle(sup, (20, 20, 30), centro, tamanho // 2, max(1, tamanho // 16))
        if pygame.font.get_init():
            letra = pygame.font.Font(None, int(tamanho * 0.7)).render(nome[:1].upper(), True, (20, 20, 30))
            sup.blit(letra, letra.get_rect(center=centro))
        return sup

    @classmethod
    def fonte(cls, tamanho, arquivo=FONTE):
        chave = (arquivo, tamanho)
        if chave not in cls._fontes:
            caminho = cls.pasta / arquivo
            try:
                fonte = pygame.font.Font(str(caminho) if caminho.exists() else None, tamanho)
                fonte.render("Aa", True, (255, 255, 255))     # algumas fontes abrem mas não desenham
            except (pygame.error, OSError):
                fonte = pygame.font.Font(None, tamanho)        # fonte padrão do pygame
            cls._fontes[chave] = fonte
        return cls._fontes[chave]

    @classmethod
    def som(cls, nome):
        if nome not in cls._sons:
            arquivo = cls.pasta / "sons" / f"{nome}.wav"
            som = SomMudo()
            if pygame.mixer.get_init() and arquivo.exists():
                try:
                    som = pygame.mixer.Sound(str(arquivo))
                except pygame.error:
                    som = SomMudo()
            cls._sons[nome] = som
        return cls._sons[nome]

    @classmethod
    def tocar(cls, nome, volume=0.5):
        """Toca um som, ignorando repetições muito próximas do mesmo som."""
        agora = pygame.time.get_ticks()
        if agora - cls._ultimo_toque.get(nome, -10_000) < cls.INTERVALO_MINIMO_SOM_MS:
            return
        cls._ultimo_toque[nome] = agora
        som = cls.som(nome)
        som.set_volume(volume)
        som.play()

    @classmethod
    def limpar(cls):
        for cache in (cls._imagens, cls._derivadas, cls._fontes, cls._sons, cls._ultimo_toque):
            cache.clear()
