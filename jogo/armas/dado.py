"""Dado de 20 Lados: a arma inicial do Mestre de RPG. O dano é o número que sai."""
from jogo.ajudantes.golpes import DadoArremessado, mostrar
from jogo.armas.arma import ArmaDeDisparo
from jogo.config import Cor
from jogo.nucleo.recursos import Recursos


class DadoDeVinteLados(ArmaDeDisparo):
    NOME = "Dado de 20 Lados"
    ICONE = "icones/dado_20.png"
    DESCRICAO = "Joga um d20 no inimigo mais perto: o dano é o número que sai. 20 é crítico triplo; 1 erra."
    EXCLUSIVA = True
    ATRIBUTOS = {
        "dano": (1.0, 1.2, 1.4, 2.3),          # dano por ponto do dado
        "quantidade": (1, 1, 2, 3),
        "recarga": (1.0, 0.9, 0.8, 0.65),
    }
    MELHORIAS = (
        "Mais dano por ponto e recarga menor.",
        "Mais 1 dado, mais dano e recarga menor.",
        "VANTAGEM: três dados, e cada um rola duas vezes e fica com o melhor número.",
    )
    FACES = 20
    CRITICO = 3                                # o 20 natural vale o triplo
    VELOCIDADE = 520
    ALCANCE = 560
    ABERTURA = 14                              # graus entre os dados de uma mesma jogada

    def rolar(self, rng):
        """Um número de 1 a 20; no nível máximo, com vantagem (rola duas vezes, fica com o maior)."""
        numero = rng.randint(1, self.FACES)
        if self.no_maximo:
            numero = max(numero, rng.randint(1, self.FACES))
        return numero

    def dano_da_rolagem(self, numero, dono):
        """O dano de um dado: o número vezes o dano por ponto; o 20 vale o triplo e o 1 não fere."""
        if numero <= 1:
            return 0
        dano = numero * self.valor("dano") * dono.multiplicador_dano
        return dano * self.CRITICO if numero == self.FACES else dano

    def disparar(self, jogo, dono):
        rumo = self.rumo_do_ataque(jogo, dono, self.ALCANCE)
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            numero = self.rolar(jogo.rng)
            if numero <= 1:
                mostrar(jogo, "1... errou!", dono.posicao, Cor.DANO, 16)
                continue
            if numero == self.FACES:
                mostrar(jogo, "20 NATURAL!", dono.posicao, Cor.DESTAQUE, 20)
            direcao = rumo.rotate((i - (quantidade - 1) / 2) * self.ABERTURA)
            self.lancar(jogo, DadoArremessado(dono.posicao, direcao * self.VELOCIDADE,
                                              self.dano_da_rolagem(numero, dono), numero))
        Recursos.tocar("disparo", 0.12)
