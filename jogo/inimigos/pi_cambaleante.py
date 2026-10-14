import math

from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("pi")
class PiCambaleante(Inimigo):
    """A letra π gorducha, de chapeuzinho de festa, andando em zigue-zague."""

    NOME = "Pi Cambaleante"
    IMAGEM = "sprites/pi.png"
    PASTA_SPRITE = "pi"
    ALTURA = 46
    RAIO = 19
    VIDA = 16
    VELOCIDADE = 95
    DANO = 6
    PONTOS = 10
    EXPERIENCIA = 2

    def mover(self, dt, jogo):
        falta = jogo.jogador.posicao - self.posicao
        if falta.length_squared() < 1:
            return
        frente = falta.normalize()
        lado = frente.rotate(90) * math.sin(self.tempo * 4) * 0.9
        self.ir_em_direcao(self.posicao + (frente + lado) * 100, dt)

    def ao_morrer(self, jogo):
        super().ao_morrer(jogo)
        jogo.adicionar(TextoFlutuante("3,14...", self.posicao - (0, 20), Cor.DESTAQUE, 16, duracao=1.0))
