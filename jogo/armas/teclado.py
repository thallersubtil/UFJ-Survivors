"""Teclado Mecânico: a arma exclusiva do Programador. Golpe em arco; cada acerto solta teclas nos vizinhos."""
from jogo.ajudantes.golpes import GolpeDoTeclado, OndaDeTeclas
from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos


class TecladoMecanico(ArmaDeDisparo):
    NOME = "Teclado Mecânico"
    ICONE = "legado/itens/item_watch_l.png"
    DESCRICAO = "Golpe em arco com o teclado na direção da mira; cada inimigo atingido solta teclas nos vizinhos."
    EXCLUSIVA = True
    ATRIBUTOS = {
        "dano": (14, 18, 24, 40),
        "alcance": (100, 110, 120, 135),
        "abertura": (110, 120, 130, 140),     # graus do arco
        "teclas": (1, 2, 2, 3),               # teclas que cada acerto solta
        "recarga": (1.0, 0.9, 0.8, 0.7),
    }
    MELHORIAS = (
        "Mais 1 tecla por acerto, mais dano e mais alcance.",
        "Arco mais largo, mais dano e recarga menor.",
        "CTRL+ALT+DEL: cada golpe também solta uma onda de teclas em volta de você.",
    )

    def disparar(self, jogo, dono):
        alcance = self.valor("alcance")
        if jogo.inimigo_mais_proximo(dono.posicao, alcance) is None:
            return False                       # não gasta o golpe no vazio
        dano = self.valor("dano") * dono.multiplicador_dano
        self.lancar(jogo, GolpeDoTeclado(dono, dono.direcao_mira, alcance, self.valor("abertura"), dano,
                                         self.valor("teclas")))
        if self.no_maximo:
            self.lancar(jogo, OndaDeTeclas(dono.posicao, dano * GolpeDoTeclado.FRACAO_DAS_TECLAS, self.aura))
        Recursos.tocar("disparo", 0.12)
        return True
