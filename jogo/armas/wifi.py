from jogo.ajudantes.ajudantes import SinalWifi
from jogo.armas.arma import ArmaDeContato


class WifiEduroam(ArmaDeContato):
    NOME = "Wi-Fi Eduroam"
    ICONE = "icones/wifi.png"
    DESCRICAO = "Um campo de sinal em volta de você fere quem entra. Às vezes o sinal cai."
    PRECO_DESBLOQUEIO = 500
    ATRIBUTOS = {
        "dano": (4, 5, 6, 7, 8, 9, 11),
        "raio": (90, 100, 110, 120, 130, 140, 160),
        "intervalo": (0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4),
        "queda": (0.25, 0.25, 0.2, 0.2, 0.15, 0.1, 0.0),
    }
    MELHORIAS = (
        "Mais dano e área.",
        "Pulsos mais rápidos; o sinal cai menos.",
        "Mais dano e área.",
        "Pulsos mais rápidos; o sinal cai menos.",
        "Mais dano e área.",
        "Fibra óptica: o sinal nunca cai.",
    )

    def __init__(self):
        super().__init__()
        self.sinal = None

    def atualizar(self, dt, jogo, dono):
        if self.sinal is None or not self.sinal.ativo:
            self.sinal = SinalWifi(dono, self)
            jogo.adicionar(self.sinal)

    def ao_remover(self, jogo):
        if self.sinal is not None:
            self.sinal.remover()
            self.sinal = None
