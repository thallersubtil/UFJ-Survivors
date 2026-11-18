import math

import pygame

from jogo.coletaveis.coletaveis import Moeda
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.nucleo.animacao import Animador
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import ProjetilDaMateria


@FabricaDeInimigos.registrar("monitor_possuido")
class MonitorPossuido(Inimigo):
    """Monitor da disciplina possuído pela matéria: persegue o aluno e arremessa listas de exercícios.

    Mini-chefe das provas 2 e 3. Ao morrer solta um baú e moedas. Usa a arte do aluno
    (provisória) com uma aura roxa por cima.
    """

    NOME = "Monitor Possuído"
    IMAGEM = "sprites/aluno1.png"
    PASTA_SPRITE = "aluno1"
    ALTURA = 110
    RAIO = 30
    VIDA = 700
    VELOCIDADE = 120
    DANO = 14
    PONTOS = 400
    EXPERIENCIA = 40
    MOEDAS = 12
    INTERVALO_LISTA = 2.2
    LISTAS_POR_VEZ = 3
    VELOCIDADE_LISTA = 260
    DANO_LISTA = 9
    ALCANCE = 650
    COR = (170, 90, 230)
    ESCALA = 1.4                 # maior que um aluno comum

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.solta_bau = True
        self.reposiciona = False
        self._espera_lista = 1.5
        self.animador = Animador(Recursos.animacoes_ou_imagem(self.PASTA_SPRITE, self.IMAGEM,
                                                              self.ALTURA * self.ESCALA, self.ESCALA))

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)
        self._espera_lista -= dt
        if self._espera_lista > 0:
            return
        self._espera_lista = self.INTERVALO_LISTA
        rumo = jogo.jogador.posicao - self.posicao
        if rumo.length_squared() == 0 or rumo.length() > self.ALCANCE:
            return
        rumo = rumo.normalize()
        for i in range(self.LISTAS_POR_VEZ):
            direcao = rumo.rotate((i - (self.LISTAS_POR_VEZ - 1) / 2) * 18)
            jogo.adicionar(ProjetilDaMateria(self.posicao, direcao * self.VELOCIDADE_LISTA, self.DANO_LISTA,
                                             "?", self.COR))

    def assustar(self, duracao):
        """Monitor possuído não cai em trote."""

    def ao_morrer(self, jogo):
        super().ao_morrer(jogo)
        jogo.adicionar(Moeda(self.posicao - (16, 0), self.MOEDAS))

    def desenhar_corpo(self, tela, camera):
        c = camera.para_tela(self.posicao)
        brilho = 0.75 + 0.25 * math.sin(self.tempo * 8)
        aura = pygame.Surface((130, 170), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (140, 30, 220, int(120 * brilho)), (5, 10, 120, 155))
        pygame.draw.ellipse(aura, (190, 80, 255, int(230 * brilho)), (5, 10, 120, 155), 3)
        tela.blit(aura, aura.get_rect(midbottom=(round(c.x), round(c.y + 40))))
        imagem = self.animador.quadro_atual.copy()
        imagem.fill((205, 165, 255), special_flags=pygame.BLEND_RGB_MULT)     # tom roxo da possessão
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda,
                        piscar=self.piscar > 0, deslocamento_y=self.balanco())
