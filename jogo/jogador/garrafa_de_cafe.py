"""A munição do jogo: o café da garrafa do Programador, gasto na Virada de Noite.

É o requisito "munição com @property e validação" do trabalho: `municao` só aceita número inteiro, entre 0 e a
capacidade da garrafa.
"""


class GarrafaDeCafe:
    def __init__(self, capacidade=100):
        self._capacidade = 1
        self._municao = 0
        self.capacidade = capacidade

    @property
    def capacidade(self):
        return self._capacidade

    @capacidade.setter
    def capacidade(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("a capacidade da garrafa deve ser um número inteiro")
        if valor < 1:
            raise ValueError("a garrafa leva pelo menos 1 dose")
        self._capacidade = valor
        self._municao = min(self._municao, valor)

    @property
    def municao(self):
        """Doses de café na garrafa: cada uma é um tiro da Virada de Noite."""
        return self._municao

    @municao.setter
    def municao(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("a munição deve ser um número inteiro de doses")
        if not 0 <= valor <= self._capacidade:
            raise ValueError(f"a munição vai de 0 a {self._capacidade} doses")
        self._municao = valor

    @property
    def vazia(self):
        return self._municao == 0

    def encher(self):
        self.municao = self._capacidade

    def acrescentar(self, doses):
        """Põe mais café, sem passar da capacidade."""
        self.municao = min(self._capacidade, self._municao + doses)

    def gastar(self, doses=1):
        """Tira `doses` da garrafa. Devolve False (e não tira nada) se não houver café suficiente."""
        if self._municao < doses:
            return False
        self.municao = self._municao - doses
        return True
