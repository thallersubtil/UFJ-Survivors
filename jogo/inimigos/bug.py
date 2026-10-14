from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("bug")
class Bug(Inimigo):
    """Besourinho verde de olhos esbugalhados. Rápido, fraco, vem em bando."""

    NOME = "Bug"
    IMAGEM = "sprites/bug.png"
    PASTA_SPRITE = "bug"
    ALTURA = 30
    RAIO = 12
    VIDA = 6
    VELOCIDADE = 125
    DANO = 3
    PONTOS = 5
    TAMANHO_GRUPO = 6

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)
