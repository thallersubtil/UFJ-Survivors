"""A partida: contém o Jogador, a Fase, o Placar e todas as entidades."""
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import pygame

from jogo.cenario import Cenario
from jogo.coletaveis.coletaveis import Nota
from jogo.config import (ALTURA, BONUS_67_DURACAO, BONUS_67_VELOCIDADE, LARGURA,
                         LIMITE_COLETAVEIS, LIMITE_EFEITOS, SORTEIOS_POR_PARTIDA, Cor)
from jogo.efeitos import TextoFlutuante
from jogo.fase import semestre
from jogo.jogador.bonus import BonusTemporario
from jogo.mapa import MapaUFJ
from jogo.nucleo.camera import Camera
from jogo.nucleo.grade import GradeEspacial
from jogo.nucleo.recursos import Recursos
from jogo.placar import Placar
from jogo.ranking import RegistroRanking

import jogo.inimigos  # noqa: F401  (registra todos os inimigos na fábrica)


@dataclass
class Entrada:
    direcao: pygame.Vector2 = field(default_factory=pygame.Vector2)
    mira: Optional[pygame.Vector2] = None


class Jogo:
    MARGEM_BUSCA = 64

    CURA_ENTRE_PROVAS = 0.5      # fração da vida máxima recuperada ao passar de prova

    def __init__(self, classe_jogador, fase=None, semente=None, mapa=None, fases=None, aparencia=None):
        self.rng = random.Random(semente)
        self.mapa = mapa or MapaUFJ.carregar(self.rng) or Cenario(rng=self.rng)
        self.arena = self.mapa.arena
        self.jogador = classe_jogador(self.mapa.inicio)
        if aparencia is not None:
            self.jogador.vestir(aparencia)
        if fases is None:
            fases = [fase] if fase is not None else semestre()
        self.fases = list(fases)
        self.indice_fase = 0
        self.treino = False
        self.fase = self.fases[0]
        self.placar = Placar()
        self.camera = Camera(LARGURA, ALTURA, self.arena)
        self.entrada = Entrada()
        self.grade = GradeEspacial(96)
        self.entidades = []
        self.grupos = defaultdict(list)
        self._novas = []
        self.niveis_pendentes = 0
        self.baus_pendentes = 0
        self.sorteios_restantes = SORTEIOS_POR_PARTIDA
        self.chefe = None
        self.terminou = False
        self.venceu = False
        self.anuncios = []
        self._ultima_nota = None
        self.adicionar(self.jogador)
        for entidade in self.mapa.entidades():
            self.adicionar(entidade)
        self._incorporar_novas()
        self.camera.seguir(self.jogador.posicao)

    @property
    def inimigos(self):
        return self.grupos["inimigo"]

    def adicionar(self, entidade):
        self._novas.append(entidade)

    def _incorporar_novas(self):
        while self._novas:
            novas, self._novas = self._novas, []
            for e in novas:
                self.entidades.append(e)
                self.grupos[e.grupo].append(e)

    def _limpar(self):
        self.entidades = [e for e in self.entidades if e.ativo]
        for nome in list(self.grupos):
            self.grupos[nome] = [e for e in self.grupos[nome] if e.ativo]

    def atualizar(self, dt):
        if self.terminou:
            return
        self.placar.tempo += dt
        self.fase.atualizar(dt, self)
        self._incorporar_novas()
        self.grade.reconstruir(self.inimigos)
        for e in self.entidades:          # polimorfismo: um único laço, sem if por tipo
            if e.ativo:
                e.atualizar(dt, self)
        self._incorporar_novas()
        self._limpar()
        for anuncio in self.anuncios:
            anuncio[1] -= dt
        self.anuncios = [a for a in self.anuncios if a[1] > 0]
        self.camera.seguir(self.jogador.posicao)
        if not self.jogador.esta_vivo:
            self.terminar(False)

    def desenhar(self, tela):
        self.mapa.desenhar_chao(tela, self.camera)
        visiveis = [e for e in self.entidades if e.esta_visivel(self.camera)]
        visiveis.sort(key=lambda e: (e.camada, e.posicao.y))
        for e in visiveis:
            e.desenhar(tela, self.camera)

    def resolver_obstaculos(self, posicao, raio):
        """Posição corrigida para fora dos prédios do mapa."""
        return self.mapa.empurrar(posicao, raio)

    # Buscas

    def inimigos_proximos(self, posicao, raio):
        """Inimigos ativos cujo círculo encosta no círculo (posicao, raio)."""
        resultado = []
        for e in self.grade.proximos(posicao, raio + self.MARGEM_BUSCA):
            if e.ativo:
                limite = raio + e.raio
                if e.posicao.distance_squared_to(posicao) <= limite * limite:
                    resultado.append(e)
        return resultado

    def inimigo_mais_proximo(self, posicao, raio_max, excluir=None):
        melhor, melhor_distancia = None, raio_max * raio_max
        for e in self.grade.proximos(posicao, raio_max):
            if e is excluir or not e.ativo:
                continue
            distancia = e.posicao.distance_squared_to(posicao)
            if distancia <= melhor_distancia:
                melhor, melhor_distancia = e, distancia
        return melhor

    def inimigo_com_mais_vida(self, posicao, raio_max):
        candidatos = [e for e in self.grade.proximos(posicao, raio_max)
                      if e.ativo and e.posicao.distance_squared_to(posicao) <= raio_max * raio_max]
        return max(candidatos, key=lambda e: e.vida, default=None)

    # Regras

    def causar_dano(self, inimigo, dano, direcao=None, forte=False):
        """Fere um inimigo. Retorna True se ele morreu com este golpe."""
        if not inimigo.ativo or not inimigo.esta_vivo or inimigo.invulneravel:
            return False
        dano = max(1, round(dano))
        morreu = inimigo.receber_dano(dano)
        if direcao is not None:
            inimigo.empurrar(direcao)
        if len(self.grupos["efeito"]) < LIMITE_EFEITOS:
            deslocamento = pygame.Vector2(self.rng.uniform(-8, 8), -inimigo.raio)
            self.adicionar(TextoFlutuante(str(dano), inimigo.posicao + deslocamento,
                                          Cor.DANO_FORTE if forte else Cor.DANO, 22 if forte else 16))
        Recursos.tocar("acerto", 0.12)
        if morreu:
            self._registrar_morte(inimigo)
        return morreu

    def _registrar_morte(self, inimigo):
        inimigo.remover()
        if self.placar.registrar_eliminacao(inimigo.valor_em_pontos):
            self._combo_67()
        inimigo.ao_morrer(self)

    def _combo_67(self):
        self.jogador.adicionar_bonus(BonusTemporario("combo67", "velocidade", BONUS_67_VELOCIDADE, BONUS_67_DURACAO))
        self.anunciar("67!", 2.0)
        Recursos.tocar("67", 0.9)

    def ferir_jogador(self, dano):
        if not self.jogador.pode_levar_dano:
            return False
        self.jogador.receber_dano(dano)
        self.placar.zerar_combo()
        self.adicionar(TextoFlutuante(f"-{round(dano)}", self.jogador.posicao - (0, 30), Cor.DANO_HEROI, 18))
        Recursos.tocar("dano", 0.4)
        return True

    def dar_experiencia(self, quantidade):
        niveis = self.jogador.ganhar_experiencia(quantidade)
        self.niveis_pendentes += niveis

    def soltar_nota(self, posicao, valor):
        """Solta uma nota; acima do limite, soma o valor na última nota solta."""
        if len(self.grupos["coletavel"]) + len(self._novas) >= LIMITE_COLETAVEIS and \
                self._ultima_nota is not None and self._ultima_nota.ativo:
            self._ultima_nota.valor += valor
            return
        self._ultima_nota = Nota(posicao, valor)
        self.adicionar(self._ultima_nota)

    def pedir_bau(self):
        self.baus_pendentes += 1
        Recursos.tocar("bau", 0.6)

    def iniciar_chefe(self, chefe):
        self.chefe = chefe
        self.adicionar(chefe)
        self.anunciar(f"{chefe.nome} chegou!", 3)

    @property
    def ultima_fase(self):
        return self.indice_fase + 1 >= len(self.fases)

    def concluir_fase(self):
        """O chefe da prova caiu: passa para a próxima prova ou vence o jogo."""
        concluida = self.fase
        self.chefe = None
        self._incorporar_novas()     # o que nasceu neste quadro também sai
        if self.ultima_fase:
            self.terminar(venceu=True)
            return
        self.indice_fase += 1
        self.fase = self.fases[self.indice_fase]
        for grupo in ("inimigo", "projetil_inimigo"):
            for entidade in self.grupos[grupo]:
                entidade.remover()
        self.jogador.curar(self.jogador.vida_maxima * self.CURA_ENTRE_PROVAS)
        self.pedir_bau()
        self.anunciar(f"Aprovado em {concluida.MATERIA}!", 3)
        self.anunciar(self.fase.NOME, 4)

    def anunciar(self, texto, duracao=2.5):
        self.anuncios.append([texto, duracao])

    def terminar(self, venceu):
        if self.terminou:
            return
        self.terminou = True
        self.venceu = venceu
        Recursos.tocar("vitoria" if venceu else "derrota", 0.7)

    def resultado(self, nome):
        return RegistroRanking(nome, self.jogador.NOME, self.placar.pontuacao_final(self.venceu),
                               self.placar.tempo, self.venceu)
