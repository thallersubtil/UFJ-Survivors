import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.hud import Hud
from jogo.jogo import Jogo


class CenaPartida(Cena):
    ESPERA_FIM = 1.5

    def __init__(self, app, classe_jogador):
        super().__init__(app)
        self.jogo = Jogo(classe_jogador)
        self.hud = Hud()
        self._espera_fim = self.ESPERA_FIM

    def tratar_evento(self, evento):
        if evento.type != pygame.KEYDOWN:
            return
        if evento.key == pygame.K_ESCAPE:
            self._pausar()
        elif evento.key == pygame.K_SPACE:
            self.jogo.jogador.usar_especial(self.jogo)

    def _pausar(self):
        from jogo.cenas.pausa import CenaPausa
        self.app.empilhar(CenaPausa(self.app, self))

    def _ler_entrada(self):
        teclas = pygame.key.get_pressed()
        x = (teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT])
        y = (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP])
        self.jogo.entrada.direcao = pygame.Vector2(x, y)
        self.jogo.entrada.mira = self.jogo.camera.para_mundo(pygame.mouse.get_pos()) if self.app.mira_mouse else None

    def atualizar(self, dt):
        if self.jogo.terminou:
            self._espera_fim -= dt
            if self._espera_fim <= 0:
                self._encerrar()
            return
        self._ler_entrada()
        self.jogo.atualizar(dt)
        if self.jogo.niveis_pendentes > 0:
            self._abrir("jogo.cenas.nivel", "CenaNivel")
        elif self.jogo.baus_pendentes > 0:
            self._abrir("jogo.cenas.bau", "CenaBau")

    def _abrir(self, modulo, nome):
        import importlib
        try:
            classe = getattr(importlib.import_module(modulo), nome)
        except (ImportError, AttributeError):
            self.jogo.niveis_pendentes = 0
            self.jogo.baus_pendentes = 0
            return
        self.app.empilhar(classe(self.app, self.jogo))

    def _encerrar(self):
        try:
            from jogo.cenas.fim import CenaFimDeJogo
        except ImportError:
            self.app.sair()
            return
        self.app.trocar(CenaFimDeJogo(self.app, self.jogo))

    def desenhar(self, tela):
        self.jogo.desenhar(tela)
        self.hud.desenhar(tela, self.jogo)
