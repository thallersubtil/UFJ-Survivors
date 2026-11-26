"""Mapas da partida: o chão, os obstáculos e as decorações da arena.

`Mapa` é abstrata; `MapaUFJ` é o Campus Jatobá gerado a partir de satélite e
OpenStreetMap (ferramentas/gerar_mapa.py), e `Cenario` (jogo/cenario.py) é o
pátio genérico usado quando o mapa da UFJ não está disponível.
"""
import json
import random
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

    def local_de(self, nome):
        """Um ponto livre em frente ao prédio chamado `nome`, ou None se o mapa não tem esse prédio."""
        return None

    def miniatura(self, altura):
        """Desenho do mapa inteiro com `altura` pixels (para o mini-mapa)."""
        largura = max(1, round(altura * self.arena.width / self.arena.height))
        imagem = pygame.Surface((largura, altura))
        imagem.fill((52, 92, 52))
        return imagem

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
        self._miniaturas = {}
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

    FRENTE_DO_PREDIO = 150       # distância da base do prédio até o ponto de referência

    def local_de(self, nome):
        """Ponto livre em frente ao prédio; se a frente está tomada por outro prédio, o livre mais próximo."""
        for predio in self.predios:
            if predio.nome == nome:
                frente = pygame.Vector2(predio.posicao.x, predio.contorno.bottom + self.FRENTE_DO_PREDIO)
                candidatos = [frente] + [frente + pygame.Vector2(passo, 0).rotate(angulo)
                                         for passo in range(120, 1201, 120) for angulo in range(0, 360, 30)]
                for ponto in candidatos:
                    if self.arena.inflate(-240, -240).collidepoint(ponto) and not self.bloqueado(ponto, 110):
                        return ponto
                return self.empurrar(frente, 100)
        return None

    def miniatura(self, altura):
        """O chão reduzido com os prédios pintados por cima (guardada: só é montada uma vez por altura)."""
        if altura not in self._miniaturas:
            fator = altura / self.arena.height
            chao = Recursos.imagem(self.chao)
            imagem = pygame.transform.smoothscale(chao, (max(1, round(self.arena.width * fator)), altura))
            for predio in self.predios:
                pontos = [(x * fator, y * fator) for x, y in predio.poligono]
                pygame.draw.polygon(imagem, (196, 150, 110), pontos)
                pygame.draw.polygon(imagem, (70, 44, 40), pontos, 1)
            self._miniaturas[altura] = imagem
        return self._miniaturas[altura]

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
        self._detalhar_grama(ampliado, bx, by)
        self._enfeitar(ampliado, bx, by)
        self._blocos[chave] = ampliado
        if len(self._blocos) > self.MAX_BLOCOS:
            self._blocos.popitem(last=False)
        return ampliado

    # Detalhe da grama: o chão ampliado fica borrado, então folhas claras e escuras em resolução
    # de tela são somadas e subtraídas só onde o bloco é verde (ferramentas/montar_grama.py).
    GRAMA_LUZ = "cenario/grama_luz.png"
    GRAMA_SOMBRA = "cenario/grama_sombra.png"
    VERDES = (((109, 173, 68), (30, 30, 22)), ((53, 110, 52), (26, 30, 18)))   # grama e mata: cor e tolerância
    ENFEITES = ("capim_alto", "capim_baixo", "capim_baixo", "capim_alto", "trevos", "flores_amarelas",
                "margaridas", "flores_rosas", "flores_vermelhas", "petalas_ipe", "pedras", "arbusto",
                "arbusto_florido", "cogumelos")
    ENFEITES_POR_BLOCO = 6

    @staticmethod
    def _existe(caminho):
        return (Recursos.pasta / caminho).is_file()

    def _detalhar_grama(self, bloco, bx, by):
        """Dá textura nítida às partes verdes do bloco, sem mexer em ruas, calçadas e terra."""
        if not (self._existe(self.GRAMA_LUZ) and self._existe(self.GRAMA_SOMBRA)):
            return
        verde = pygame.mask.Mask(bloco.get_size())
        for cor, tolerancia in self.VERDES:
            verde.draw(pygame.mask.from_threshold(bloco, cor, (*tolerancia, 255)), (0, 0))
        if verde.count() == 0:
            return
        detalhado = bloco.convert_alpha()
        lado = self.BLOCO * self.escala
        for caminho, modo in ((self.GRAMA_LUZ, pygame.BLEND_RGB_ADD), (self.GRAMA_SOMBRA, pygame.BLEND_RGB_SUB)):
            ladrilho = Recursos.imagem(caminho)
            largura, altura = ladrilho.get_size()
            for y in range(-((by * lado) % altura), bloco.get_height(), altura):
                for x in range(-((bx * lado) % largura), bloco.get_width(), largura):
                    detalhado.blit(ladrilho, (x, y), special_flags=modo)
        recorte = verde.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))
        detalhado.blit(recorte, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        bloco.blit(detalhado, (0, 0))

    def _e_grama(self, x, y):
        """Diz se o ponto do mundo cai em gramado aberto (não em mata, rua, calçada ou terra)."""
        chao = Recursos.imagem(self.chao)
        px, py = int(x // self.escala), int(y // self.escala)
        if not chao.get_rect().collidepoint(px, py):
            return False
        cor, tolerancia = self.VERDES[0]
        return all(abs(a - b) <= t for a, b, t in zip(chao.get_at((px, py))[:3], cor, tolerancia))

    def _enfeites_do_bloco(self, bx, by):
        """Enfeites (imagem e ponto de apoio no mundo) do bloco; sempre os mesmos para o mesmo bloco."""
        sorteio = random.Random(bx * 73856093 ^ by * 19349663)
        lado = self.BLOCO * self.escala
        achados = []
        for _ in range(self.ENFEITES_POR_BLOCO):
            nome = sorteio.choice(self.ENFEITES)
            x, y = (bx + sorteio.random()) * lado, (by + sorteio.random()) * lado
            caminho = f"cenario/enfeites/{nome}.png"
            if self._e_grama(x, y) and self._existe(caminho):
                achados.append((Recursos.imagem(caminho), x, y))
        return achados

    def _enfeitar(self, bloco, bx, by):
        """Desenha flores, capim e pedras no gramado; os vizinhos entram para nada ficar cortado na emenda."""
        lado = self.BLOCO * self.escala
        enfeites = [e for vy in (by - 1, by, by + 1) for vx in (bx - 1, bx, bx + 1)
                    for e in self._enfeites_do_bloco(vx, vy)]
        for imagem, x, y in sorted(enfeites, key=lambda e: e[2]):
            bloco.blit(imagem, (round(x - bx * lado - imagem.get_width() / 2), round(y - by * lado - imagem.get_height())))

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
