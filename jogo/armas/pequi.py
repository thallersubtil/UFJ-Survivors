from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import PequiArremessado

from jogo.formas_supremas import PequiDeOuro


class PequiExplosivo(ArmaDeDisparo):
    NOME = "Pequi Explosivo"
    ICONE = "icones/pequi.png"
    DESCRICAO = "Arremessa um pequi no inimigo mais perto. Ele estoura e espalha espinhos em volta."
    PRECO_DESBLOQUEIO = 400
    ATRIBUTOS = {
        "dano": (14, 18, 25, 44),
        "raio": (70, 85, 100, 150),
        "quantidade": (1, 1, 2, 4),
        "recarga": (1.6, 1.4, 1.3, 0.9),
    }
    MELHORIAS = (
        "Mais dano, estouro maior e recarga menor.",
        "Mais 1 pequi, mais dano e estouro maior.",
        "PEQUIZAL: cada pequi, além de estourar, deixa um tapete de espinhos que fere e segura quem pisa por 3,5 s.",
    )
    VELOCIDADE = 420
    ALCANCE = 450

    def disparar(self, jogo, dono):
        rumo = self.rumo_do_ataque(jogo, dono, self.ALCANCE)
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            direcao = rumo.rotate((i - (quantidade - 1) / 2) * 25)
            self.lancar(jogo, (PequiDeOuro if self.no_maximo else PequiArremessado)(dono.posicao, direcao * self.VELOCIDADE,
                                            self.valor("dano") * dono.multiplicador_dano, self.valor("raio")))
        Recursos.tocar("disparo", 0.12)
