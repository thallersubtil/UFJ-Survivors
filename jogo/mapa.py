"""Mapas da partida: o chão, os obstáculos e as decorações da arena.

`Mapa` é abstrata; `MapaUFJ` é o Campus Jatobá gerado a partir de satélite e
OpenStreetMap (ferramentas/gerar_mapa.py), e `Cenario` (jogo/cenario.py) é o
pátio genérico usado quando o mapa da UFJ não está disponível.
"""
import json
from abc import ABC, abstractmethod

import pygame

from jogo.config import ESCALA_PIXEL, PASTA_ASSETS
from jogo.nucleo.animacao import Animador
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Decoracao(Entidade):
    """Enfeite (árvore, banco, poste, bandeira). Só existe para ser visto; pode ser animado."""

    grupo = "decoracao"
    camada = 1

    def __init__(self, posicao, imagem=None, altura=None, pasta=None):
        super().__init__(posicao, 0)
        self.imagem = imagem
        self.altura = altura
        self.animador = Animador(Recursos.animacoes_ou_imagem(pasta, imagem or "", altura or 48))

    def atualizar(self, dt, jogo):
        self.animador.atualizar(dt)

    def desenhar(self, tela, camera):
        desenhar_sprite(tela, camera, self.animador.quadro_atual, self.posicao)


class Predio(Entidade):
    """Prédio da UFJ: obstáculo com o contorno real e desenho em pixel art 3/4.

    A posição é o meio da base (o ponto mais ao sul), para quem passa atrás do
    prédio ser desenhado antes dele e ficar escondido.
    """

    grupo = "predio"
    camada = 1

    def __init__(self, nome, poligono, sprite, canto):
        pontos = [pygame.Vector2(p) for p in poligono]
        base_y = max(p.y for p in pontos)
        meio_x = sum(p.x for p in pontos) / len(pontos)
        super().__init__((meio_x, base_y), 0)
        self.nome = nome
        self.poligono = [tuple(p) for p in pontos]
        self.sprite = sprite
        self.canto = pygame.Vector2(canto)
        xs = [p.x for p in pontos]
        ys = [p.y for p in pontos]
        self.contorno = pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)

    @property
    def imagem(self):
        return Recursos.imagem_pixel(self.sprite)

    def atualizar(self, dt, jogo):
        pass

    def esta_visivel(self, camera):
        area = pygame.Rect(self.canto, self.imagem.get_size()).union(self.contorno)
        return camera.retangulo.inflate(64, 64).colliderect(area)

    def desenhar(self, tela, camera):
        tela.blit(self.imagem, camera.para_tela(self.canto))

    def empurrar(self, centro, raio):
        return Colisao.empurrar_para_fora(centro, raio, self.poligono)


class Mapa(ABC):
    """O que um mapa oferece ao Jogo: tamanho, ponto inicial, entidades, chão e obstáculos."""

    def __init__(self, arena, inicio):
        self.arena = arena
        self.inicio = pygame.Vector2(inicio)

    @abstractmethod
    def entidades(self):
        """Entidades fixas do mapa (prédios, decorações) para entrarem no Jogo."""

    @abstractmethod
    def desenhar_chao(self, tela, camera):
        """Desenha o chão visível pela câmera."""

    def obstaculos_perto(self, posicao, raio):
        return []

    def empurrar(self, posicao, raio):
        """Posição corrigida para não ficar dentro de nenhum obstáculo."""
        posicao = pygame.Vector2(posicao)
        for obstaculo in self.obstaculos_perto(posicao, raio):
            nova = obstaculo.empurrar(posicao, raio)
            if nova is not None:
                posicao = nova
        return posicao

    def bloqueado(self, posicao, raio):
        return any(Colisao.circulo_poligono(posicao, raio, o.poligono) for o in self.obstaculos_perto(posicao, raio))


class MapaUFJ(Mapa):
    """Campus Jatobá da UFJ, lido de assets/cenario/mapa_ufj.json."""

    ARQUIVO = "cenario/mapa_ufj.json"
    CELULA = 128
    DECORACOES = {
        "palmeira": "palmeira", "ipe": "ipe", "arvore": "arvore_cerrado", "poste": "poste",
        "banco": "banco", "portal": "portal_ufj", "bandeira": "bandeira",
    }

    def __init__(self, dados, rng=None):
        super().__init__(pygame.Rect(0, 0, dados["largura"], dados["altura"]), dados["inicio"])
        self.chao = dados["chao"]
        self.predios = [Predio(p["nome"], p["poligono"], p["sprite"], p["canto"]) for p in dados["predios"]]
        self.decoracoes = [Decoracao((d["x"], d["y"]), pasta=self.DECORACOES.get(d["tipo"], d["tipo"]))
                           for d in dados["decoracoes"]]
        self._celulas = {}
        for predio in self.predios:
            r = predio.contorno
            for cx in range(r.left // self.CELULA, r.right // self.CELULA + 1):
                for cy in range(r.top // self.CELULA, r.bottom // self.CELULA + 1):
                    self._celulas.setdefault((cx, cy), []).append(predio)

    @classmethod
    def carregar(cls, rng=None):
        """Lê o mapa gerado; devolve None se ele não existir."""
        arquivo = PASTA_ASSETS / cls.ARQUIVO
        if not arquivo.is_file():
            return None
        return cls(json.loads(arquivo.read_text(encoding="utf-8")), rng)

    def entidades(self):
        return self.predios + self.decoracoes

    def obstaculos_perto(self, posicao, raio):
        x0, y0 = int((posicao[0] - raio) // self.CELULA), int((posicao[1] - raio) // self.CELULA)
        x1, y1 = int((posicao[0] + raio) // self.CELULA), int((posicao[1] + raio) // self.CELULA)
        achados = []
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                for predio in self._celulas.get((cx, cy), ()):
                    if predio not in achados:
                        achados.append(predio)
        return achados

    def desenhar_chao(self, tela, camera):
        """O chão é pixel art em metade da resolução; desenha só o pedaço visível, ampliado."""
        tela.fill((40, 70, 40))
        chao = Recursos.imagem(self.chao)
        visivel = camera.retangulo.clip(self.arena)
        if visivel.width <= 0 or visivel.height <= 0:
            return
        origem = pygame.Rect(visivel.left // ESCALA_PIXEL, visivel.top // ESCALA_PIXEL,
                             visivel.width // ESCALA_PIXEL + 2, visivel.height // ESCALA_PIXEL + 2)
        origem = origem.clip(chao.get_rect())
        if origem.width <= 0 or origem.height <= 0:
            return
        pedaco = pygame.transform.scale(chao.subsurface(origem),
                                        (origem.width * ESCALA_PIXEL, origem.height * ESCALA_PIXEL))
        tela.blit(pedaco, camera.para_tela((origem.left * ESCALA_PIXEL, origem.top * ESCALA_PIXEL)))
