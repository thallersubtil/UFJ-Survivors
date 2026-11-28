import pygame

from jogo.ajudantes.ajudantes import MascoteFlutuante
from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import TiroChatGPT


class MascoteChatGPT(ArmaDeDisparo):
    NOME = "Mascote do ChatGPT"
    ICONE = "sprites/chatgpt.png"
    DESCRICAO = "Atira no inimigo mais próximo. Às vezes alucina e atira para qualquer lado, com dano dobrado."
    ATRIBUTOS = {
        "dano": (9, 13, 18, 32),
        "quantidade": (1, 2, 3, 4),
        "recarga": (0.9, 0.85, 0.7, 0.45),
    }
    MELHORIAS = (
        "Mais 1 disparo e mais dano.",
        "Mais 1 disparo, mais dano e recarga menor.",
        "ALUCINAÇÃO COLETIVA: a cada 3 rajadas ele surta e solta 18 tiros rosa de dano dobrado para todos os lados.",
    )
    CHANCE_ALUCINAR = 0.15
    RAJADAS_POR_ALUCINACAO = 3
    TIROS_DA_ALUCINACAO = 18
    ALCANCE = 520
    VELOCIDADE = 560
    DESLOCAMENTO = (-38, -46)

    def __init__(self):
        super().__init__()
        self.mascote = None
        self._rajadas = 0

    def atualizar(self, dt, jogo, dono):
        if self.mascote is None:
            self.mascote = MascoteFlutuante(dono, self.ICONE, 34, self.DESLOCAMENTO, pasta="chatgpt")
            self.lancar(jogo, self.mascote)
        self.mascote.aura = self.aura
        super().atualizar(dt, jogo, dono)

    def disparar(self, jogo, dono):
        origem = self.mascote.posicao if self.mascote else dono.posicao
        rumo = self.rumo_do_ataque(jogo, dono, self.ALCANCE, origem)
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            alucinou = jogo.rng.random() < self.CHANCE_ALUCINAR
            if alucinou:
                direcao = pygame.Vector2(1, 0).rotate(jogo.rng.uniform(0, 360))
            else:
                direcao = rumo.rotate((i - (quantidade - 1) / 2) * 8)
            dano = self.valor("dano") * dono.multiplicador_dano * (2 if alucinou else 1)
            self.lancar(jogo, TiroChatGPT(origem, direcao * self.VELOCIDADE, dano, alucinado=alucinou))
        if self.no_maximo:                      # alucinação coletiva: a cada poucas rajadas, tiros para todo lado
            self._rajadas += 1
            if self._rajadas % self.RAJADAS_POR_ALUCINACAO == 0:
                for i in range(self.TIROS_DA_ALUCINACAO):
                    direcao = pygame.Vector2(1, 0).rotate(i * 360 / self.TIROS_DA_ALUCINACAO)
                    self.lancar(jogo, TiroChatGPT(origem, direcao * self.VELOCIDADE,
                                                  self.valor("dano") * dono.multiplicador_dano * 2, alucinado=True))
        Recursos.tocar("disparo", 0.12)

    def ao_remover(self, jogo):
        if self.mascote is not None:
            self.mascote.remover()
            self.mascote = None
