import pygame

from jogo.cenas.bau import CenaBau
from jogo.cenas.cena import Cena
from jogo.cenas.fim import CenaFimDeJogo
from jogo.cenas.hud import Hud
from jogo.cenas.nivel import CenaNivel
from jogo.cenas.pausa import CenaPausa
from jogo.cenas.widgets import desenhar_texto
from jogo.config import Cor
from jogo.jogo import Jogo
from jogo.opcoes import OpcoesDePartida


class CenaPartida(Cena):
    ESPERA_FIM = 1.5
    ALCANCE_MIRA_AUTOMATICA = 700

    def __init__(self, app, classe_jogador, opcoes=None):
        super().__init__(app)
        self.opcoes = opcoes or OpcoesDePartida()
        self.jogo = Jogo.a_partir_de(classe_jogador, self.opcoes)
        self.hud = Hud()
        self._espera_fim = self.ESPERA_FIM

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            modo = self.app.alternar_mira()
            self.jogo.anunciar("Mira automática" if modo == "automatica" else "Mira no mouse", 1.2)
            return
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
        if self.app.modo_mira == "automatica":
            alvo = self.jogo.inimigo_mais_proximo(self.jogo.jogador.posicao, self.ALCANCE_MIRA_AUTOMATICA)
            self.jogo.entrada.mira = pygame.Vector2(alvo.posicao) if alvo is not None else None
        else:
            self.jogo.entrada.mira = self.jogo.camera.para_mundo(pygame.mouse.get_pos())

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
        self._desenhar_mira(tela)

    def _desenhar_mira(self, tela):
        mira_propria = self.app.modo_mira == "mouse" and self.app.cenas and self.app.cena_atual is self
        if pygame.display.get_init():
            pygame.mouse.set_visible(not mira_propria)
        if mira_propria:
            x, y = pygame.mouse.get_pos()
            pygame.draw.circle(tela, (20, 16, 30), (x, y), 9, 3)
            pygame.draw.circle(tela, (255, 236, 160), (x, y), 9, 1)
            pygame.draw.line(tela, (255, 236, 160), (x - 13, y), (x - 5, y))
            pygame.draw.line(tela, (255, 236, 160), (x + 5, y), (x + 13, y))
            pygame.draw.line(tela, (255, 236, 160), (x, y - 13), (x, y - 5))
            pygame.draw.line(tela, (255, 236, 160), (x, y + 5), (x, y + 13))
        texto = "MIRA: MOUSE  (clique: automática)" if self.app.modo_mira == "mouse" \
            else "MIRA: AUTOMÁTICA  (clique: mouse)"
        desenhar_texto(tela, texto, 14, Cor.TEXTO_FRACO, topo_esquerda=(14, tela.get_height() - 24))
