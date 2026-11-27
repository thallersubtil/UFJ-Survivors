"""Bases das armas. O Jogador contém uma lista de Armas (composição)."""
from abc import ABC, abstractmethod
from numbers import Real


class Arma(ABC):
    NOME = "Arma"
    DESCRICAO = ""
    ICONE = ""
    NIVEL_MAXIMO = 4           # poucos níveis, cada um pesa; o último é a forma suprema da arma
    ATRIBUTOS = {}
    MELHORIAS = ()
    PRECO_DESBLOQUEIO = 0      # > 0: só aparece nas cartas depois de comprado no Centro Acadêmico

    PESO = 1.0                 # chance relativa de aparecer nas cartas
    MAX_CARIMBOS = 3           # vezes que a Bigorna pode afiar esta arma
    BONUS_CARIMBO = 0.15       # +15% de dano por carimbo
    COR_SUPREMA = (255, 214, 90)   # contorno do que a arma solta quando está no nível máximo

    def __init__(self):
        self._nivel = 1
        self.carimbos = 0

    @classmethod
    def liberada(cls, desbloqueios):
        """Se pode aparecer nas cartas, dado o conjunto de nomes de classes desbloqueadas."""
        return cls.PRECO_DESBLOQUEIO <= 0 or cls.__name__ in desbloqueios

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

    @property
    def aura(self):
        """Cor do contorno da forma suprema (nível máximo), ou None antes disso."""
        return self.COR_SUPREMA if self.no_maximo else None

    def lancar(self, jogo, entidade):
        """Põe no jogo o que a arma cria (projétil, ajudante, efeito), já com o visual do nível dela."""
        entidade.aura = self.aura
        jogo.adicionar(entidade)
        return entidade

    def subir_nivel(self):
        self.nivel = self._nivel + 1
        self.ao_subir_nivel()

    def ao_subir_nivel(self):
        """Gancho para armas que precisam reagir à melhoria."""

    def valor(self, atributo):
        valor = self.ATRIBUTOS[atributo][self._nivel - 1]
        if atributo == "dano":
            valor *= 1 + self.BONUS_CARIMBO * self.carimbos
        return valor

    @property
    def pode_afiar(self):
        return self.carimbos < self.MAX_CARIMBOS

    def descricao_proxima(self):
        return "" if self.no_maximo else self.MELHORIAS[self._nivel - 1]

    @abstractmethod
    def atualizar(self, dt, jogo, dono):
        """Avança a arma; é aqui que ela ataca."""

    def ao_remover(self, jogo):
        """Chamado quando a arma sai do jogador (por exemplo, virou colab)."""

    @property
    def fracao_de_recarga(self):
        """Quanto da recarga já passou (0 a 1) para o HUD, ou None se a arma não espera para atirar."""
        return None

    def __str__(self):
        return f"{self.NOME} (nível {self._nivel})"


class ArmaDeDisparo(Arma, ABC):
    """Arma que dispara e espera a recarga para disparar de novo. Não gasta nada: só o tempo."""

    ESPERA_SEM_ALVO = 0.1          # sem ter em quem atirar, tenta de novo logo
    ESPERA_DA_REPETICAO = 0.12     # Laço de Repetição (Programador): o disparo repetido sai quase junto

    def __init__(self):
        super().__init__()
        self._espera = 0.0         # segundos até o próximo disparo
        self._recarga_atual = 0.0  # quanto durava a espera quando ela começou (para o HUD)

    @property
    def espera(self):
        """Segundos que faltam para o próximo disparo."""
        return self._espera

    @espera.setter
    def espera(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, Real):
            raise TypeError("a espera deve ser um número")
        if valor < 0:
            raise ValueError("a espera não pode ser negativa")
        self._espera = float(valor)
        self._recarga_atual = max(self._recarga_atual, self._espera) if self._espera > 0 else 0.0

    @property
    def fracao_de_recarga(self):
        return 1.0 if self._recarga_atual <= 0 else 1 - self._espera / self._recarga_atual

    def atualizar(self, dt, jogo, dono):
        self.espera = max(0.0, self._espera - dt)
        if self._espera > 0:
            return
        if not self.disparar(jogo, dono):
            self.espera = self.ESPERA_SEM_ALVO
        elif self._repete(jogo, dono):
            self.espera = self.ESPERA_DA_REPETICAO
        else:
            self.espera = self.valor("recarga") * dono.multiplicador_recarga

    @staticmethod
    def _repete(jogo, dono):
        """Sorteia se o disparo repete na hora (só sorteia para quem tem essa chance)."""
        chance = dono.chance(dono.chance_repeticao)
        return chance > 0 and jogo.rng.random() < chance

    @abstractmethod
    def disparar(self, jogo, dono):
        """Cria os projéteis. Retorna False se não havia em que atirar."""


class ArmaContinua(Arma, ABC):
    """Arma que age o tempo todo, no próprio ritmo: ajudantes, veículos, golpes e campos
    (Caramelo, Claude, Fusca, Wi-Fi, Apostila, Quadro Branco e as colabs)."""
