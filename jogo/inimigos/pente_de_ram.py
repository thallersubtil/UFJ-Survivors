import math

import pygame

from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.nucleo.desenho import desenhar_sombra
from jogo.nucleo.recursos import Recursos


@FabricaDeInimigos.registrar("pente_ram")
class PenteDeRAM(Inimigo):
    """Pente de memória que anda como centopeia: lento e resistente."""

    NOME = "Pente de RAM"
    IMAGEM = "sprites/pente_ram.png"
    ALTURA = 26
    RAIO = 22
    VIDA = 60
    VELOCIDADE = 55
    DANO = 10
    PONTOS = 25
    EXPERIENCIA = 4
    FATIAS = 5

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)

    def desenhar_corpo(self, tela, camera):
        """Desenha o pente em fatias que ondulam, como as patas de uma centopeia."""
        imagem = Recursos.imagem(self.IMAGEM, int(self.altura_sprite))
        if self.piscar > 0:
            imagem = Recursos.silhueta_branca(imagem)
        if self.olhando_esquerda:
            imagem = Recursos.espelhada(imagem)
        centro = camera.para_tela(self.posicao)
        largura, altura = imagem.get_size()
        desenhar_sombra(tela, (centro.x, centro.y + altura / 2), largura * 0.9)
        fatia = math.ceil(largura / self.FATIAS)
        for i in range(self.FATIAS):
            area = pygame.Rect(i * fatia, 0, min(fatia, largura - i * fatia), altura)
            onda = math.sin(self.tempo * 8 + i * 0.9) * altura * 0.12
            tela.blit(imagem, (round(centro.x - largura / 2 + i * fatia), round(centro.y - altura / 2 - onda - 2)), area)
