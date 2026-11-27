"""Lightstick: a arma exclusiva do Otaku. O bastão sai girando e volta para a mão."""
import pygame

from jogo.ajudantes.golpes import LightstickGirando
from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos


class Lightstick(ArmaDeDisparo):
    NOME = "Lightstick"
    ICONE = "legado/itens/potion_hp_s.png"
    DESCRICAO = "Arremessa o lightstick, que gira, acerta quem estiver no caminho e volta para a mão."
    EXCLUSIVA = True
    ATRIBUTOS = {
        "dano": (10, 13, 17, 28),
        "quantidade": (1, 1, 2, 3),
        "alcance": (260, 280, 300, 340),
        "recarga": (1.2, 1.1, 1.0, 0.8),
    }
    MELHORIAS = (
        "Mais dano, mais longe e recarga menor.",
        "Mais 1 lightstick, mais dano e recarga menor.",
        "COREOGRAFIA: três lightsticks em leque, que estouram em notas musicais quando voltam para a mão.",
    )
    VELOCIDADE = 480
    ABERTURA = 30                     # graus entre os lightsticks do leque
    NOTAS = 8                         # notas musicais de cada lightstick na Coreografia

    def disparar(self, jogo, dono):
        alvo = jogo.inimigo_mais_proximo(dono.posicao, self.valor("alcance") + 120)
        if alvo is None:
            return False
        rumo = alvo.posicao - dono.posicao
        rumo = rumo.normalize() if rumo.length_squared() > 0 else pygame.Vector2(dono.direcao_mira)
        quantidade = self.valor("quantidade")
        notas = self.NOTAS if self.no_maximo else 0
        for i in range(quantidade):
            direcao = rumo.rotate((i - (quantidade - 1) / 2) * self.ABERTURA)
            self.lancar(jogo, LightstickGirando(dono, direcao * self.VELOCIDADE, self.valor("dano") * dono.multiplicador_dano,
                                                self.valor("alcance"), notas))
        Recursos.tocar("disparo", 0.12)
        return True
