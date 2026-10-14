import math

from jogo.efeitos import FaiscaExplosao
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("pilha")
class PilhaAA(Inimigo):
    """Pilha AA brava que anda aos saltos e solta faíscas ao morrer."""

    NOME = "Pilha AA"
    IMAGEM = "sprites/pilha.png"
    PASTA_SPRITE = "pilha"
    ALTURA = 44
    RAIO = 15
    VIDA = 20
    VELOCIDADE = 75
    DANO = 9
    PONTOS = 12
    EXPERIENCIA = 2
    RAIO_EXPLOSAO = 70
    DANO_EXPLOSAO = 10

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)

    def balanco(self):
        return abs(math.sin(self.tempo * 6)) * 8

    def ao_morrer(self, jogo):
        super().ao_morrer(jogo)
        jogo.adicionar(FaiscaExplosao(self.posicao, self.RAIO_EXPLOSAO, self.DANO_EXPLOSAO))
