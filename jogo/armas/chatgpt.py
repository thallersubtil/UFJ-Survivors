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
        "dano": (9, 11, 13, 15, 17, 20, 24),
        "quantidade": (1, 1, 2, 2, 2, 3, 3),
        "recarga": (0.9, 0.85, 0.85, 0.75, 0.7, 0.65, 0.55),
    }
    MELHORIAS = (
        "Mais dano.",
        "Mais 1 disparo.",
        "Mais dano e recarga menor.",
        "Mais dano.",
        "Mais 1 disparo.",
        "Mais dano e recarga menor.",
    )
    CHANCE_ALUCINAR = 0.15
    ALCANCE = 520
    VELOCIDADE = 560
    DESLOCAMENTO = (-38, -46)

    def __init__(self):
        super().__init__()
        self.mascote = None

    def atualizar(self, dt, jogo, dono):
        if self.mascote is None:
            self.mascote = MascoteFlutuante(dono, self.ICONE, 34, self.DESLOCAMENTO, pasta="chatgpt")
            jogo.adicionar(self.mascote)
        super().atualizar(dt, jogo, dono)

    def disparar(self, jogo, dono):
        origem = self.mascote.posicao if self.mascote else dono.posicao
        alvo = jogo.inimigo_mais_proximo(origem, self.ALCANCE)
        if alvo is None:
            return False
        rumo = alvo.posicao - origem
        rumo = rumo.normalize() if rumo.length_squared() > 0 else pygame.Vector2(1, 0)
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            alucinou = jogo.rng.random() < self.CHANCE_ALUCINAR
            if alucinou:
                direcao = pygame.Vector2(1, 0).rotate(jogo.rng.uniform(0, 360))
            else:
                direcao = rumo.rotate((i - (quantidade - 1) / 2) * 8)
            dano = self.valor("dano") * dono.multiplicador_dano * (2 if alucinou else 1)
            jogo.adicionar(TiroChatGPT(origem, direcao * self.VELOCIDADE, dano, alucinado=alucinou))
        Recursos.tocar("disparo", 0.12)
        return True

    def ao_remover(self, jogo):
        if self.mascote is not None:
            self.mascote.remover()
            self.mascote = None
