"""Coisas que o herói pega no chão: notas (experiência), café, poção e baú."""
import math
from abc import ABC, abstractmethod

from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Coletavel(Entidade, ABC):
    grupo = "coletavel"
    camada = 0
    IMAGEM = ""
    ALTURA = 24
    MAGNETICO = True
    VELOCIDADE_ATRACAO = 520

    def __init__(self, posicao, raio=12):
        super().__init__(posicao, raio)
        self.tempo = 0.0
        self.atraido = False

    def atualizar(self, dt, jogo):
        self.tempo += dt
        jogador = jogo.jogador
        if self.MAGNETICO and not self.atraido and \
                self.posicao.distance_to(jogador.posicao) <= jogador.alcance_coleta:
            self.atraido = True
        if self.atraido:
            falta = jogador.posicao - self.posicao
            if falta.length_squared() > 0:
                self.posicao += falta.normalize() * min(falta.length(), self.VELOCIDADE_ATRACAO * dt)
        if Colisao.circulos_colidem(self, jogador):
            self.ao_coletar(jogo)
            self.remover()

    @abstractmethod
    def ao_coletar(self, jogo):
        """Efeito de pegar o coletável."""

    def altura_desenho(self):
        return self.ALTURA

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.IMAGEM, self.altura_desenho())
        desenhar_sprite(tela, camera, imagem, self.posicao, deslocamento_y=3 + math.sin(self.tempo * 4) * 2)


class Nota(Coletavel):
    IMAGEM = "sprites/nota.png"
    ALTURA = 20

    def __init__(self, posicao, valor=1):
        super().__init__(posicao)
        self.valor = valor

    def ao_coletar(self, jogo):
        jogo.dar_experiencia(self.valor)
        Recursos.tocar("coleta", 0.2)

    def altura_desenho(self):
        return 26 if self.valor >= 5 else self.ALTURA


class CopoDeCafe(Coletavel):
    IMAGEM = "sprites/cafe.png"
    ALTURA = 30

    def ao_coletar(self, jogo):
        jogo.jogador.encher_cafe()
        jogo.adicionar(TextoFlutuante("CAFÉ!", self.posicao, Cor.CAFE, 18))
        Recursos.tocar("coleta", 0.4)


class PocaoDeVida(Coletavel):
    IMAGEM = "legado/itens/potion_hp_s.png"
    ALTURA = 30
    CURA = 30

    def ao_coletar(self, jogo):
        jogo.jogador.curar(self.CURA)
        jogo.adicionar(TextoFlutuante(f"+{self.CURA}", self.posicao, Cor.CURA, 18))
        Recursos.tocar("coleta", 0.4)


class Bau(Coletavel):
    IMAGEM = "legado/itens/chest_f0.png"
    ALTURA = 52
    MAGNETICO = False

    def __init__(self, posicao):
        super().__init__(posicao, raio=22)

    def ao_coletar(self, jogo):
        jogo.pedir_bau()
