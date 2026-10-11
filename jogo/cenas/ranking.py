import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR, desenhar_fundo, desenhar_painel, desenhar_texto
from jogo.config import ALTURA, LARGURA, Cor


class CenaRanking(Cena):
    def __init__(self, app, destaque=None):
        super().__init__(app)
        self.destaque = destaque

    def _voltar(self):
        from jogo.cenas.titulo import CenaTitulo
        self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and (evento.key == pygame.K_ESCAPE or evento.key in TECLAS_CONFIRMAR):
            self._voltar()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._voltar()

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=170)
        desenhar_texto(tela, "RANKING", 48, Cor.DESTAQUE, centro=(LARGURA // 2, 70))
        painel = pygame.Rect(0, 0, 820, 520)
        painel.center = (LARGURA // 2, 390)
        desenhar_painel(tela, painel)
        registros = self.app.ranking.registros
        if not registros:
            desenhar_texto(tela, "Ninguém jogou ainda. Seja o primeiro!", 24, Cor.TEXTO, centro=painel.center)
        for i, r in enumerate(registros):
            y = painel.top + 30 + i * 46
            cor = Cor.DESTAQUE if self.destaque is not None and r == self.destaque else Cor.TEXTO
            minutos, segundos = divmod(int(r.tempo), 60)
            desenhar_texto(tela, f"{i + 1}.", 24, cor, topo_esquerda=(painel.left + 30, y))
            desenhar_texto(tela, r.nome, 24, cor, topo_esquerda=(painel.left + 90, y))
            desenhar_texto(tela, r.heroi, 18, Cor.TEXTO_FRACO, topo_esquerda=(painel.left + 330, y + 4))
            desenhar_texto(tela, f"{minutos:02d}:{segundos:02d}", 20, cor, topo_esquerda=(painel.left + 460, y + 2))
            desenhar_texto(tela, f"{r.pontos}", 24, cor, topo_direita=(painel.right - 140, y))
            if r.venceu:
                desenhar_texto(tela, "APROVADO", 14, Cor.APROVADO, topo_esquerda=(painel.right - 120, y + 6))
        desenhar_texto(tela, "[Enter] voltar", 16, Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 24))
