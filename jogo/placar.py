"""Pontuação, eliminações, tempo de jogo e o combo 67."""
from jogo.config import COMBO_ESPECIAL


class Placar:
    PONTOS_POR_SEGUNDO = 2
    BONUS_VITORIA = 5000

    def __init__(self):
        self._pontos = 0
        self.eliminacoes = 0
        self.tempo = 0.0
        self.combo = 0
        self.combos_67 = 0
        self._moedas = 0

    @property
    def pontos(self):
        return self._pontos

    @pontos.setter
    def pontos(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("pontos devem ser um número inteiro")
        if valor < 0:
            raise ValueError("pontos não podem ser negativos")
        self._pontos = valor

    def adicionar_pontos(self, quantidade):
        if quantidade < 0:
            raise ValueError("não dá para ganhar pontos negativos")
        self.pontos = self._pontos + quantidade

    @property
    def moedas(self):
        """Moedas pegas nesta partida (vão para o Centro Acadêmico no fim)."""
        return self._moedas

    @moedas.setter
    def moedas(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("moedas devem ser um número inteiro")
        if valor < 0:
            raise ValueError("moedas não podem ser negativas")
        self._moedas = valor

    def adicionar_moedas(self, quantidade):
        if quantidade < 0:
            raise ValueError("não dá para ganhar moedas negativas")
        self.moedas = self._moedas + int(quantidade)

    def registrar_eliminacao(self, pontos):
        """Conta uma eliminação. Retorna True quando o combo completa 67."""
        self.eliminacoes += 1
        self.adicionar_pontos(pontos)
        self.combo += 1
        if self.combo % COMBO_ESPECIAL == 0:
            self.combos_67 += 1
            return True
        return False

    def zerar_combo(self):
        self.combo = 0

    def pontuacao_final(self, venceu):
        total = self._pontos + int(self.tempo) * self.PONTOS_POR_SEGUNDO
        return total + (self.BONUS_VITORIA if venceu else 0)

    @property
    def tempo_formatado(self):
        minutos, segundos = divmod(int(self.tempo), 60)
        return f"{minutos:02d}:{segundos:02d}"

    def __str__(self):
        return f"{self._pontos} pontos | {self.eliminacoes} eliminações | {self.tempo_formatado}"
