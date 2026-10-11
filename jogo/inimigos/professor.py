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
    ALTURA = 112
    RAIO = 40
    VIDA = 9000
    VELOCIDADE = 75
    DANO = 18
    PONTOS = 5000
    EXPERIENCIA = 0
    LACAIOS_CHAMADA = ("bug", "calculadora", "caixinha", "pi", "pilha")
    TEMPO_CARGA = 0.8
    TEMPO_INVESTIDA = 0.6
    VELOCIDADE_INVESTIDA = 720

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self._carga = 0.0
        self._investida = 0.0
        self._direcao = pygame.Vector2(1, 0)

    def ataques(self):
        return [self.atacar_folhas, self.atacar_investida, self.atacar_folhas, self.atacar_chamada]

    def _mirar(self, jogo):
        falta = jogo.jogador.posicao - self.posicao
        return falta.normalize() if falta.length_squared() > 0 else pygame.Vector2(1, 0)

    def atacar_folhas(self, jogo):
        quantidade = 11 if self.furioso else 7
        base = self._mirar(jogo)
        for i in range(quantidade):
            direcao = base.rotate((i - (quantidade - 1) / 2) * 12)
            jogo.adicionar(FolhaDeProva(self.posicao, direcao * 300, 12))

    def atacar_investida(self, jogo):
        self._carga = self.TEMPO_CARGA
        self._investida = self.TEMPO_INVESTIDA
        self._direcao = self._mirar(jogo)
        self.acao_atual = self._investindo

    def _investindo(self, dt, jogo):
        if self._carga > 0:
            self._carga -= dt
            self._direcao = self._mirar(jogo)
            return False
        self._investida -= dt
        self.posicao += self._direcao * self.VELOCIDADE_INVESTIDA * dt
        return self._investida <= 0

    def atacar_chamada(self, jogo):
        quantidade = 8 if self.furioso else 6
        for i in range(quantidade):
            posicao = self.posicao + pygame.Vector2(140, 0).rotate(360 * i / quantidade)
            nome = jogo.rng.choice(self.LACAIOS_CHAMADA)
            jogo.adicionar(FabricaDeInimigos.criar(nome, posicao, jogo.fase.escala_dificuldade))
        jogo.adicionar(TextoFlutuante("CHAMADA!", self.posicao - (0, 80), Cor.DESTAQUE, 22, duracao=1.2))

    def ao_morrer(self, jogo):
        jogo.terminar(venceu=True)

    def desenhar_corpo(self, tela, camera):
        if self.acao_atual is not None and self._carga > 0:
            inicio = camera.para_tela(self.posicao)
            fim = inicio + self._direcao * self.VELOCIDADE_INVESTIDA * self.TEMPO_INVESTIDA
            pygame.draw.line(tela, (230, 60, 60), inicio, fim, 6)
        super().desenhar_corpo(tela, camera)
