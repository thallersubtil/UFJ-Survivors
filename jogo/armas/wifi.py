from jogo.ajudantes.ajudantes import SinalWifi
from jogo.armas.arma import ArmaSemMunicao

from jogo.formas_supremas import FeixeDeFibra


class WifiEduroam(ArmaSemMunicao):
    NOME = "Wi-Fi Eduroam"
    ICONE = "icones/wifi.png"
    DESCRICAO = "Um campo de sinal em volta de você fere quem entra. Às vezes o sinal cai."
    PRECO_DESBLOQUEIO = 500
    ATRIBUTOS = {
        "dano": (4, 6, 8, 15),
        "raio": (90, 110, 130, 190),
        "intervalo": (0.7, 0.6, 0.5, 0.32),
        "queda": (0.25, 0.2, 0.15, 0.0),
    }
    MELHORIAS = (
        "Mais dano e área; o sinal cai menos.",
        "Mais dano e área; pulsos mais rápidos.",
        "FIBRA ÓPTICA: o sinal nunca cai e um feixe de luz gira em volta de você queimando bem além do campo.",
    )

    def __init__(self):
        super().__init__()
        self.sinal = None
        self.feixe = None

    def atualizar(self, dt, jogo, dono):
        if self.sinal is None or not self.sinal.ativo:
            self.sinal = SinalWifi(dono, self)
            self.lancar(jogo, self.sinal)
        if self.no_maximo and (self.feixe is None or not self.feixe.ativo):     # fibra óptica: o feixe giratório
            self.feixe = self.lancar(jogo, FeixeDeFibra(dono, self))

    def ao_remover(self, jogo):
        for entidade in (self.sinal, self.feixe):
            if entidade is not None:
                entidade.remover()
        self.sinal = self.feixe = None
