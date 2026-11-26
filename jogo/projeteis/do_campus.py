"""O que os mini-chefes do mapa jogam no aluno: multas, carros desgovernados e o feixe de abdução."""
import pygame

from jogo.nucleo.animacao import Animador
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_faixa_de_aviso, desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.tematicos import GolpeNoChao, ProjetilTematico, arte_existe, imagem_da_arte, imagem_na_largura


class Multa(ProjetilTematico):
    """Multa de atraso da Bibliotecária: quase não fere, mas tira moedas do aluno."""

    def __init__(self, posicao, velocidade, dano, valor, cor):
        super().__init__(posicao, velocidade, dano, "R$", cor, raio=13, arte="multa")
        self.valor = valor

    def verificar_colisao(self, jogo):
        if Colisao.circulos_colidem(self, jogo.jogador):
            if jogo.ferir_jogador(self.dano):
                jogo.multar(self.valor)
            self.remover()


class VeiculoDesgovernado(Entidade):
    """Carro que buzina parado por um instante (a faixa no chão avisa por onde vai passar) e atravessa a tela."""

    grupo = "projetil_inimigo"
    camada = 1

    def __init__(self, posicao, direcao, pasta, velocidade, dano, raio, aviso=0.8, duracao=2.6):
        super().__init__(posicao, raio)
        self.direcao = pygame.Vector2(direcao).normalize()
        self.velocidade = velocidade
        self.dano = dano
        self.aviso = aviso
        self.duracao = duracao
        self.tempo = 0.0
        self.animador = Animador(Recursos.animacoes(pasta))

    @property
    def parado(self):
        return self.tempo < self.aviso

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.parado:
            return
        self.animador.atualizar(dt)
        self.posicao += self.direcao * self.velocidade * dt
        if Colisao.circulos_colidem(self, jogo.jogador):
            jogo.ferir_jogador(self.dano)
        if self.tempo >= self.aviso + self.duracao:
            self.remover()

    def esta_visivel(self, camera):
        return True                       # a faixa de aviso atravessa a tela mesmo com o carro fora dela

    def desenhar(self, tela, camera):
        if self.parado:
            inicio = camera.para_tela(self.posicao)
            fim = inicio + self.direcao * self.velocidade * self.duracao
            desenhar_faixa_de_aviso(tela, inicio, fim, self.raio * 2, tempo=self.tempo)
        desenhar_sprite(tela, camera, self.animador.quadro_atual, self.posicao, espelhar=self.direcao.x < 0)


class FeixeDeAbducao(GolpeNoChao):
    """Anel verde que enche no chão (aviso) e, quando fecha, puxa para cima quem estiver dentro."""

    COR = (130, 255, 110)
    TEXTO = "ABDUZIDO!"
    ARTE_DO_ANEL = "anel_de_abducao"
    ARTE_DO_FEIXE = "feixe_de_luz"
    ARTE_DO_ABDUZIDO = "vaca"
    ALTURA_DO_FEIXE = 420

    def desenhar_chao(self, tela, centro):
        super().desenhar_chao(tela, centro)
        if arte_existe(self.ARTE_DO_ANEL):
            anel = imagem_na_largura(self.ARTE_DO_ANEL, round(self.raio * 2.2 / 8) * 8)
            tela.blit(anel, anel.get_rect(center=(round(centro.x), round(centro.y))))

    def desenhar_golpe(self, tela, centro):
        """A coluna de luz subindo, com uma vaca que estava passando."""
        if not self.disparou:
            return
        base = (round(centro.x), round(centro.y + self.raio * 0.3))
        if arte_existe(self.ARTE_DO_FEIXE):
            feixe = pygame.transform.scale(imagem_da_arte(self.ARTE_DO_FEIXE, 128),
                                           (round(self.raio * 2), self.ALTURA_DO_FEIXE))
            feixe.set_alpha(170)
            tela.blit(feixe, feixe.get_rect(midbottom=base))
        else:
            coluna = pygame.Surface((self.raio * 2, self.ALTURA_DO_FEIXE), pygame.SRCALPHA)
            coluna.fill((170, 255, 140, 90))
            tela.blit(coluna, coluna.get_rect(midbottom=base))
        if arte_existe(self.ARTE_DO_ABDUZIDO):
            subida = (self.tempo - self.AVISO) / self.BRILHO * self.ALTURA_DO_FEIXE * 0.6
            vaca = imagem_da_arte(self.ARTE_DO_ABDUZIDO, 44)
            tela.blit(vaca, vaca.get_rect(center=(base[0], round(base[1] - 60 - subida))))
