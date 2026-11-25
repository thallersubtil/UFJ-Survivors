"""Rolamento (esquiva): um impulso rápido, com invencibilidade enquanto dura."""
import pygame


class Rolamento:
    """O Jogador contém um Rolamento (composição), como contém o Especial.

    O impulso começa em IMPULSO vezes a velocidade do herói e cai até a
    velocidade normal no fim. Enquanto rola (e por mais TOLERANCIA segundos)
    o herói não leva dano. Depois vem a RECARGA.
    """

    DURACAO = 0.30
    IMPULSO = 3.2          # velocidade no começo, em múltiplos da velocidade do herói
    TOLERANCIA = 0.10      # invencibilidade que sobra depois de parar de rolar
    RECARGA = 1.1

    def __init__(self):
        self.restante = 0.0
        self.protecao = 0.0
        self.espera = 0.0
        self.direcao = pygame.Vector2(1, 0)

    @property
    def rolando(self):
        return self.restante > 0

    @property
    def protegido(self):
        return self.protecao > 0

    @property
    def pronto(self):
        return self.espera <= 0

    @property
    def progresso(self):
        """Quanto da recarga já passou (0 a 1), para o HUD."""
        total = self.DURACAO + self.RECARGA
        return max(0.0, min(1.0, 1 - self.espera / total))

    @property
    def fator_velocidade(self):
        if not self.rolando:
            return 1.0
        resta = self.restante / self.DURACAO
        return 1 + (self.IMPULSO - 1) * resta * resta

    @property
    def fracao(self):
        """Quanto do rolamento já foi (0 a 1), para girar o sprite."""
        return 1 - self.restante / self.DURACAO if self.rolando else 0.0

    def iniciar(self, direcao):
        if not self.pronto:
            return False
        direcao = pygame.Vector2(direcao)
        self.direcao = direcao.normalize() if direcao.length_squared() > 0 else pygame.Vector2(1, 0)
        self.restante = self.DURACAO
        self.protecao = self.DURACAO + self.TOLERANCIA
        self.espera = self.DURACAO + self.RECARGA
        return True

    def atualizar(self, dt, mult_recarga=1.0):
        self.restante = max(0.0, self.restante - dt)
        self.protecao = max(0.0, self.protecao - dt)
        self.espera = max(0.0, self.espera - dt / mult_recarga)
