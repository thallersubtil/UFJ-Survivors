"""O que as colabs do semestre põem na arena: o quadro branco gigante da Aula Expositiva, o rastro de sinal do
Caramelo 5G e os pequis lançados em arco pela Catapulta do Cerrado. Desenhados por código até a arte ser aprovada."""
import math

import pygame

from jogo.ajudantes.ajudantes import Ajudante
from jogo.efeitos import Efeito, EstouroDePequi
from jogo.formas_supremas import AreaQueFere, CampoDeEspinhos, desenhar_imagem
from jogo.projeteis.projeteis import ProjetilDoHeroi


# ------------------------------------------------------------------ Aula Expositiva

class FolhaEmEspiral(ProjetilDoHeroi):
    """Folha que sai do quadro gigante fazendo uma espiral; quem ela acerta fica lento."""

    DURACAO = 1.6
    GIRO = 110                         # graus por segundo que a folha vira enquanto voa

    def __init__(self, posicao, velocidade, dano, lentidao):
        super().__init__(posicao, velocidade, dano, perfuracao=2, raio=11)
        self.lentidao = lentidao

    def mover(self, dt):
        self.velocidade.rotate_ip(self.GIRO * dt)
        self.posicao += self.velocidade * dt

    def ao_acertar(self, inimigo, jogo):
        inimigo.atrasar(self.lentidao)

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        folha = pygame.Surface((16, 20), pygame.SRCALPHA)
        folha.fill((250, 250, 245))
        pygame.draw.rect(folha, self.aura or (90, 90, 110), folha.get_rect(), 1)
        for y in (6, 10, 14):
            pygame.draw.line(folha, (120, 140, 220), (3, y), (12, y))
        girada = pygame.transform.rotate(folha, self.tempo * 400)
        tela.blit(girada, girada.get_rect(center=(round(centro.x), round(centro.y))))


class QuadroGigante(Ajudante):
    """Um quadro branco gigante que gira em volta do aluno, fere quem encosta e solta folhas em espiral."""

    AMIGO = False
    LARGURA, ALTURA_DO_QUADRO = 78, 52
    ESPERA_ACERTO = 0.5

    def __init__(self, dono, arma, angulo=0.0):
        super().__init__(dono.posicao, 40)
        self.dono = dono
        self.arma = arma
        self.angulo = angulo
        self.tempo = 0.0
        self._espera_folha = 0.0
        self._acertados = {}

    def esta_visivel(self, camera):
        return True

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.angulo += self.arma.valor("velocidade") * dt
        self.posicao = self.dono.posicao + pygame.Vector2(math.cos(self.angulo), math.sin(self.angulo)) * self.arma.valor("raio")
        dano = self.arma.valor("dano") * self.dono.multiplicador_dano
        for inimigo in list(self._acertados):
            self._acertados[inimigo] -= dt
            if self._acertados[inimigo] <= 0:
                del self._acertados[inimigo]
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if inimigo not in self._acertados:
                self._acertados[inimigo] = self.ESPERA_ACERTO
                jogo.causar_dano(inimigo, dano, inimigo.posicao - self.dono.posicao)
        self._espera_folha -= dt
        while self._espera_folha <= 0:
            self._espera_folha += 1 / self.arma.valor("folhas_por_segundo")
            para_fora = self.posicao - self.dono.posicao
            direcao = para_fora.normalize() if para_fora.length_squared() > 0 else pygame.Vector2(1, 0)
            folha = FolhaEmEspiral(self.posicao, direcao * 300, dano * 0.5, self.arma.valor("lentidao"))
            folha.aura = self.aura
            jogo.adicionar(folha)

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        quadro = pygame.Rect(0, 0, self.LARGURA, self.ALTURA_DO_QUADRO)
        quadro.center = (round(centro.x), round(centro.y))
        pygame.draw.rect(tela, self.aura or (150, 150, 165), quadro.inflate(8, 8), border_radius=4)
        pygame.draw.rect(tela, (252, 252, 250), quadro)
        for i, cor in enumerate(((40, 80, 200), (200, 40, 40), (40, 150, 60))):      # a matéria no quadro
            y = quadro.top + 12 + i * 13
            pygame.draw.line(tela, cor, (quadro.left + 8, y), (quadro.right - 10 - i * 12, y), 3)


# ------------------------------------------------------------------ Caramelo 5G

class RastroDeSinal(AreaQueFere):
    """O sinal que o Caramelo 5G deixa por onde corre: fere quem pisa."""

    camada = 0

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        alfa = round(110 * self.alfa_do_fim / 255)
        sup = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        cor = self.aura or (90, 170, 255)
        for fracao in (1.0, 0.66, 0.33):
            pygame.draw.circle(sup, (*cor, alfa), (self.raio, self.raio), round(self.raio * fracao), 2)
        tela.blit(sup, sup.get_rect(center=(round(centro.x), round(centro.y))))


class Latido(Efeito):
    """O sinal caiu e o Caramelo 5G late: quem está perto leva dano e fica parado um instante."""

    camada = 3

    def __init__(self, posicao, raio, dano, atordoa):
        super().__init__(posicao, 0.35, raio)
        self.dano = dano
        self.atordoa = atordoa
        self._latiu = False

    def ao_atualizar(self, dt, jogo):
        if self._latiu:
            return
        self._latiu = True
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            jogo.causar_dano(inimigo, self.dano, inimigo.posicao - self.posicao)
            inimigo.travar(self.atordoa)

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        raio = max(1, round(self.raio * self.fracao))
        sup = pygame.Surface((self.raio * 2 + 4, self.raio * 2 + 4), pygame.SRCALPHA)
        meio = self.raio + 2
        pygame.draw.circle(sup, (*(self.aura or (255, 200, 90)), round(200 * (1 - self.fracao))), (meio, meio), raio, 4)
        tela.blit(sup, sup.get_rect(center=(round(centro.x), round(centro.y))))


# ------------------------------------------------------------------ Catapulta do Cerrado

class PequiEmArco(Efeito):
    """Pequi lançado pela catapulta: voa em arco por cima de todo mundo e só estoura onde cai."""

    camada = 3
    VOO = 0.7                          # segundos no ar
    ALTURA_DO_ARCO = 160

    def __init__(self, origem, destino, raio, dano):
        super().__init__(origem, self.VOO)
        self.origem = pygame.Vector2(origem)
        self.destino = pygame.Vector2(destino)
        self.raio_do_estouro = raio
        self.dano = dano

    def esta_visivel(self, camera):
        return True

    def ao_atualizar(self, dt, jogo):
        self.posicao = self.origem.lerp(self.destino, min(1.0, self.fracao))
        if self.tempo + dt >= self.duracao:
            estouro = EstouroDePequi(self.destino, self.raio_do_estouro, self.dano)
            espinhos = CampoDeEspinhos(self.destino, round(self.raio_do_estouro * 0.8), self.dano * 0.3, 2.0)
            for entidade in (estouro, espinhos):
                entidade.aura = self.aura
                jogo.adicionar(entidade)

    def desenhar(self, tela, camera):
        altura = 4 * self.ALTURA_DO_ARCO * self.fracao * (1 - self.fracao)
        sombra = camera.para_tela(self.posicao)
        pygame.draw.ellipse(tela, (20, 30, 20), pygame.Rect(round(sombra.x) - 10, round(sombra.y) - 4, 20, 8))
        desenhar_imagem(tela, camera, "icones/pequi.png", self.posicao - (0, altura), 26, angulo=self.tempo * 540)
