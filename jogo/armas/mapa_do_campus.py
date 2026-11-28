"""Mapa do Campus: a arma exclusiva do Calouro. "Você está aqui!": alfinetes caem do céu sobre os inimigos."""
from jogo.ajudantes.golpes import AlfineteDoMapa, mais_cheio
from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos


class MapaDoCampus(ArmaDeDisparo):
    NOME = "Mapa do Campus"
    ICONE = "icones/mapa_do_campus.png"
    DESCRICAO = "\"Você está aqui!\": alfinetes caem do céu sobre inimigos perto de você, com aviso no chão."
    EXCLUSIVA = True
    ATRIBUTOS = {
        "dano": (16, 21, 27, 45),
        "quantidade": (2, 3, 4, 7),            # alfinetes por vez
        "raio": (45, 50, 55, 65),
        "recarga": (1.6, 1.5, 1.3, 1.0),
    }
    MELHORIAS = (
        "Mais 1 alfinete, mais dano e área maior.",
        "Mais 1 alfinete, mais dano e recarga menor.",
        "GPS: os alfinetes caem em sequência, traçando uma rota de você até o maior bolo de inimigos.",
    )
    ALCANCE = 600
    DISTANCIA_NO_VAZIO = 220      # sem ninguém perto, os alfinetes caem a esta distância, na mira...
    ABERTURA_NO_VAZIO = 20        # ...em leque, separados por estes graus
    INTERVALO_DO_GPS = 0.12                    # segundos entre um alfinete e o próximo na rota

    def disparar(self, jogo, dono):
        perto = [e for e in jogo.inimigos_proximos(dono.posicao, self.ALCANCE) if e.ALVO_DA_MIRA]
        dano, raio, quantidade = self.valor("dano") * dono.multiplicador_dano, self.valor("raio"), self.valor("quantidade")
        if self.no_maximo:
            destino = mais_cheio(jogo, dono.posicao, self.ALCANCE)
            if destino is None:                 # ninguém perto: a rota vai na direção da mira
                destino = dono.posicao + dono.direcao_mira * self.DISTANCIA_NO_VAZIO * 2
            for i in range(quantidade):
                ponto = dono.posicao.lerp(destino, (i + 1) / quantidade)
                self.lancar(jogo, AlfineteDoMapa(ponto, raio, dano, atraso=i * self.INTERVALO_DO_GPS))
        elif perto:
            for alvo in jogo.rng.sample(perto, min(quantidade, len(perto))):     # cai onde o alvo vai estar
                self.lancar(jogo, AlfineteDoMapa(alvo.onde_estara(jogo, AlfineteDoMapa.ATRASO), raio, dano))
        else:                                   # ninguém perto: os alfinetes caem à frente, na direção da mira
            for i in range(quantidade):
                desvio = (i - (quantidade - 1) / 2) * self.ABERTURA_NO_VAZIO
                ponto = dono.posicao + dono.direcao_mira.rotate(desvio) * self.DISTANCIA_NO_VAZIO
                self.lancar(jogo, AlfineteDoMapa(ponto, raio, dano))
        Recursos.tocar("disparo", 0.1)
