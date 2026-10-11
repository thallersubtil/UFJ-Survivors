from abc import ABC, abstractmethod


class Cena(ABC):
    """Uma tela do jogo (título, partida, pausa...)."""

    def __init__(self, app):
        self.app = app

    @abstractmethod
    def tratar_evento(self, evento):
        """Recebe um evento do Pygame (tecla, mouse)."""

    @abstractmethod
    def atualizar(self, dt):
        """Avança a cena."""

    @abstractmethod
    def desenhar(self, tela):
        """Desenha a cena."""
