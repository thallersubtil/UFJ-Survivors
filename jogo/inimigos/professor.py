"""O Professor: chefe final da Semana de Provas (arte genérica provisória)."""
import pygame

from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.inimigos.chefe import Chefe
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.projeteis.projeteis import FolhaDeProva


@FabricaDeInimigos.registrar("professor")
class Professor(Chefe):
    NOME = "Professor"
    IMAGEM = "sprites/professor.png"
    PASTA_SPRITE = "professor"
    ALTURA = 112
    RAIO = 46
    VIDA = 3200
    VELOCIDADE = 75
    DANO = 18
    PONTOS = 5000
    EXPERIENCIA = 0
    LACAIOS_CHAMADA = ("bug", "calculadora", "caixinha", "pi", "pilha")

    def ataques(self):
        return [self.atacar_folhas, self.atacar_investida, self.atacar_folhas, self.atacar_chamada]

    def atacar_folhas(self, jogo):
        quantidade = 11 if self.furioso else 7
        base = self.mirar(jogo)
        for i in range(quantidade):
            direcao = base.rotate((i - (quantidade - 1) / 2) * 12)
            jogo.adicionar(FolhaDeProva(self.posicao, direcao * 300, 12))

    def atacar_investida(self, jogo):
        self.investir()

    def atacar_chamada(self, jogo):
        quantidade = 8 if self.furioso else 6
        for i in range(quantidade):
            posicao = self.posicao + pygame.Vector2(140, 0).rotate(360 * i / quantidade)
            nome = jogo.rng.choice(self.LACAIOS_CHAMADA)
            jogo.adicionar(FabricaDeInimigos.criar(nome, posicao, jogo.fase.escala_dificuldade))
        jogo.adicionar(TextoFlutuante("CHAMADA!", self.posicao - (0, 80), Cor.DESTAQUE, 22, duracao=1.2))

    def ao_morrer(self, jogo):
        jogo.terminar(venceu=True)
