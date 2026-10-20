"""Bases das armas. O Jogador contém uma lista de Armas (composição)."""
from abc import ABC, abstractmethod
from numbers import Real


class Arma(ABC):
    NOME = "Arma"
    DESCRICAO = ""
    ICONE = ""
    NIVEL_MAXIMO = 7
    ATRIBUTOS = {}
    MELHORIAS = ()

    def __init__(self):
        self._nivel = 1

    @property
    def nivel(self):
        return self._nivel

    @nivel.setter
    def nivel(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("o nível deve ser um número inteiro")
        if not 1 <= valor <= self.NIVEL_MAXIMO:
            raise ValueError(f"o nível de {self.NOME} vai de 1 a {self.NIVEL_MAXIMO}")
        self._nivel = valor

    @property
    def no_maximo(self):
        return self._nivel >= self.NIVEL_MAXIMO

    def subir_nivel(self):
        self.nivel = self._nivel + 1
        self.ao_subir_nivel()

    def ao_subir_nivel(self):
        """Gancho para armas que precisam reagir à melhoria."""

    def valor(self, atributo):
        return self.ATRIBUTOS[atributo][self._nivel - 1]

    def descricao_proxima(self):
        return "" if self.no_maximo else self.MELHORIAS[self._nivel - 1]

    @abstractmethod
    def atualizar(self, dt, jogo, dono):
        """Avança a arma; é aqui que ela ataca."""

    def ao_remover(self, jogo):
        """Chamado quando a arma sai do jogador (por exemplo, virou colab)."""

    def encher(self):
        """Recarrega a munição. Armas sem munição não fazem nada."""

    @property
    def fracao_cafe(self):
        """Fração de café (0 a 1) para o HUD, ou None se a arma não usa café."""
        return None

    def __str__(self):
        return f"{self.NOME} (nível {self._nivel})"


class ArmaDeDisparo(Arma, ABC):
    """Arma que gasta café (munição) a cada disparo. O café recarrega sozinho."""

    MUNICAO_BASE = 12
    RECARGA_CAFE = 0.4
    PENALIDADE_SEM_CAFE = 3.0

    def __init__(self):
        super().__init__()
        self._mult_cafe = 1.0
        self._municao = float(self.MUNICAO_BASE)
        self._espera = 0.0

    @property
    def municao_maxima(self):
        return self.MUNICAO_BASE * self._mult_cafe

    @property
    def municao(self):
        return self._municao

    @municao.setter
    def municao(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, Real):
            raise TypeError("a munição deve ser um número")
        if valor < 0:
            raise ValueError("a munição não pode ser negativa")
        self._municao = min(float(valor), self.municao_maxima)

    @property
    def tem_cafe(self):
        return self._municao >= 1

    @property
    def fracao_cafe(self):
        return self._municao / self.municao_maxima

    def encher(self):
        self._municao = self.municao_maxima

    def atualizar(self, dt, jogo, dono):
        self._mult_cafe = dono.mult_cafe
        self.municao = min(self.municao_maxima, self._municao + self.RECARGA_CAFE * dono.mult_cafe * dt)
        self._espera -= dt
        if self._espera > 0:
            return
        com_cafe = self.tem_cafe
        if self.disparar(jogo, dono):
            if com_cafe:
                self.municao = self._municao - 1
            fator = 1.0 if com_cafe else self.PENALIDADE_SEM_CAFE
            self._espera = self.valor("recarga") * dono.multiplicador_recarga * fator
        else:
            self._espera = 0.1

    @abstractmethod
    def disparar(self, jogo, dono):
        """Cria os projéteis. Retorna False se não havia em que atirar."""


class ArmaDeContato(Arma, ABC):
    """Arma que machuca encostando (ajudantes, veículos, golpes). Não usa café."""
