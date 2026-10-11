import pygame

from jogo.cenas.bau import CenaBau
from jogo.cenas.cena import Cena
from jogo.cenas.fim import CenaFimDeJogo
from jogo.cenas.hud import Hud
from jogo.cenas.nivel import CenaNivel
from jogo.cenas.pausa import CenaPausa
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
            self.app.empilhar(CenaPausa(self.app, self))
        elif evento.key == pygame.K_SPACE:
            self.jogo.jogador.usar_especial(self.jogo)

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
                self.app.trocar(CenaFimDeJogo(self.app, self.jogo))
            return
        self._ler_entrada()
        self.jogo.atualizar(dt)
        if self.jogo.niveis_pendentes > 0:
            self.app.empilhar(CenaNivel(self.app, self.jogo))
        elif self.jogo.baus_pendentes > 0:
            self.app.empilhar(CenaBau(self.app, self.jogo))

    def desenhar(self, tela):
        self.jogo.desenhar(tela)
        self.hud.desenhar(tela, self.jogo)
