from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("calculadora")
class CalculadoraBrava(Inimigo):
    """Calculadora científica emburrada com ERROR no visor. Persegue sem parar."""

    NOME = "Calculadora Brava"
    IMAGEM = "sprites/calculadora.png"
    PASTA_SPRITE = "calculadora"
    ALTURA = 46
    RAIO = 17
    VIDA = 20
    VELOCIDADE = 85
    DANO = 8
    PONTOS = 12
    EXPERIENCIA = 2

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)
