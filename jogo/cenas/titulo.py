import math

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import Botao, MenuDeBotoes, desenhar_fundo, desenhar_texto
from jogo.config import ALTURA, LARGURA, TITULO, Cor
from jogo.nucleo.recursos import Recursos


class CenaTitulo(Cena):
    LOGO = "sprites/logo.png"

    def __init__(self, app):
        super().__init__(app)
        self.tempo = 0.0
        meio = LARGURA // 2
        self.menu = MenuDeBotoes([
            Botao("JOGAR", (meio, 410), self._jogar),
            Botao("TREINO", (meio, 480), self._treino),
            Botao("RANKING", (meio, 550), self._ranking),
            Botao("SAIR", (meio, 620), app.sair),
        ])

    def _jogar(self):
        from jogo.cenas.personalizacao import CenaPersonalizacao
        self.app.trocar(CenaPersonalizacao(self.app))

    def _treino(self):
        from jogo.cenas.treino import CenaTreino
        self.app.trocar(CenaTreino(self.app))

    def _ranking(self):
        from jogo.cenas.ranking import CenaRanking
        self.app.trocar(CenaRanking(self.app))

    def tratar_evento(self, evento):
        self.menu.tratar_evento(evento)

    def atualizar(self, dt):
        self.tempo += dt

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=60)
        y = 200 + math.sin(self.tempo * 2) * 6
        if (Recursos.pasta / self.LOGO).exists():
            logo = Recursos.imagem(self.LOGO, 220)
            tela.blit(logo, logo.get_rect(center=(LARGURA // 2, y)))
        else:
            desenhar_texto(tela, TITULO.upper(), 96, Cor.DESTAQUE, centro=(LARGURA // 2, y))
        self.menu.desenhar(tela)
        desenhar_texto(tela, "Trabalho de Programação Orientada a Objetos - UFJ", 14, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 20))
