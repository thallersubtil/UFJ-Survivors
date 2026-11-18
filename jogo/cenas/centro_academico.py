"""Centro Acadêmico: o hub entre as partidas, com a loja e o cassino."""
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import Botao, MenuDeBotoes, desenhar_fundo, desenhar_moedas, desenhar_texto
from jogo.config import ALTURA, LARGURA, Cor


class CenaCentroAcademico(Cena):
    FUNDO = "cenario/centro_academico.png"

    def __init__(self, app):
        super().__init__(app)
        meio = LARGURA // 2
        self.menu = MenuDeBotoes([
            Botao("LOJA", (meio, 330), self._loja, largura=420),
            Botao("CASSINO DO CA", (meio, 410), self._cassino, largura=420),
            Botao("VOLTAR", (meio, 490), self._voltar, largura=420),
        ])

    def _loja(self):
        from jogo.cenas.loja import CenaLoja
        self.app.trocar(CenaLoja(self.app))

    def _cassino(self):
        from jogo.cenas.cassino import CenaCassino
        self.app.trocar(CenaCassino(self.app))

    def _voltar(self):
        from jogo.cenas.titulo import CenaTitulo
        self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self._voltar()
            return
        self.menu.tratar_evento(evento)

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        desenhar_fundo(tela, self.FUNDO, escuro=110)
        desenhar_texto(tela, "CENTRO ACADÊMICO", 64, Cor.DESTAQUE, centro=(LARGURA // 2, 150))
        desenhar_texto(tela, "Gaste as moedas das provas em melhorias permanentes, armas e itens novos.", 18,
                       Cor.TEXTO, centro=(LARGURA // 2, 210))
        desenhar_moedas(tela, self.app.progresso.moedas)
        self.menu.desenhar(tela)
        desenhar_texto(tela, "Setas + Enter ou mouse    Esc: voltar", 16, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 40))
