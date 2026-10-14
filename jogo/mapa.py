"""Mapas da partida: o chão, os obstáculos e as decorações da arena.

`Mapa` é abstrata; `MapaUFJ` é o Campus Jatobá gerado a partir de satélite e
OpenStreetMap (ferramentas/gerar_mapa.py), e `Cenario` (jogo/cenario.py) é o
pátio genérico usado quando o mapa da UFJ não está disponível.
"""
import json
from collections import OrderedDict
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
        imagem = self.animador.quadro_atual
        desenhar_sprite(tela, camera, imagem, self.posicao, sombra=imagem.get_width() < 200)


class Predio(Entidade):
    """Prédio da UFJ: obstáculo com o contorno real e desenho em pixel art 3/4.

    A posição é o meio da base (o ponto mais ao sul), para quem passa atrás do
    prédio ser desenhado antes dele e ficar escondido.
    """

    grupo = "predio"
    camada = 1

    def __init__(self, nome, poligono, sprite, canto, escala=ESCALA_PIXEL):
        pontos = [pygame.Vector2(p) for p in poligono]
        base_y = max(p.y for p in pontos)
        meio_x = sum(p.x for p in pontos) / len(pontos)
        super().__init__((meio_x, base_y), 0)
        self.nome = nome
        self.poligono = [tuple(p) for p in pontos]
        self.sprite = sprite
        self.canto = pygame.Vector2(canto)
        self.escala = escala
        xs = [p.x for p in pontos]
        ys = [p.y for p in pontos]
        self.contorno = pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)

    @property
    def imagem(self):
        return Recursos.imagem_pixel(self.sprite, self.escala)

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
        self.escala = dados.get("escala", ESCALA_PIXEL)
        escala_predios = dados.get("escala_predios", self.escala)
        self.predios = [Predio(p["nome"], p["poligono"], p["sprite"], p["canto"], escala_predios)
                        for p in dados["predios"]]
        self._blocos = OrderedDict()
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

    BLOCO = 128            # lado do bloco do chão, em pixels da imagem reduzida
    MAX_BLOCOS = 80

    def _bloco(self, bx, by):
        """Bloco do chão já ampliado (com suavização), guardado nos mais usados recentemente."""
        chave = (bx, by)
        if chave in self._blocos:
            self._blocos.move_to_end(chave)
            return self._blocos[chave]
        chao = Recursos.imagem(self.chao)
        area = pygame.Rect(bx * self.BLOCO, by * self.BLOCO, self.BLOCO + 1, self.BLOCO + 1).clip(chao.get_rect())
        if area.width <= 0 or area.height <= 0:
            return None
        pedaco = chao.subsurface(area)
        tamanho = (area.width * self.escala, area.height * self.escala)
        try:
            ampliado = pygame.transform.smoothscale(pedaco, tamanho)
        except ValueError:
            ampliado = pygame.transform.scale(pedaco, tamanho)
        self._blocos[chave] = ampliado
        if len(self._blocos) > self.MAX_BLOCOS:
            self._blocos.popitem(last=False)
        return ampliado

    def desenhar_chao(self, tela, camera):
        """O chão fica guardado em resolução reduzida e é desenhado em blocos ampliados com suavização."""
        tela.fill((40, 70, 40))
        visivel = camera.retangulo.clip(self.arena)
        if visivel.width <= 0 or visivel.height <= 0:
            return
        lado = self.BLOCO * self.escala
        for by in range(visivel.top // lado, (visivel.bottom - 1) // lado + 1):
            for bx in range(visivel.left // lado, (visivel.right - 1) // lado + 1):
                bloco = self._bloco(bx, by)
                if bloco is not None:
                    tela.blit(bloco, camera.para_tela((bx * lado, by * lado)))
