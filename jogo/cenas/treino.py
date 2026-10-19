"""Modo treino: escolher qual professor enfrentar, sem ranking."""
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import Botao, MenuDeBotoes, desenhar_fundo, desenhar_texto
from jogo.config import ALTURA, LARGURA, Cor
from jogo.fase import PROVAS
from jogo.opcoes import OpcoesDePartida


class CenaTreino(Cena):
    def __init__(self, app):
        super().__init__(app)
        self.direto_no_chefe = False
        self.imortal = False
        meio = LARGURA // 2
        botoes = []
        for i, prova in enumerate(PROVAS):
            botoes.append(Botao(prova.ROTULO, (meio, 230 + i * 84), lambda p=prova: self._comecar(p), largura=760))
        self.menu = MenuDeBotoes(botoes)

    def _comecar(self, prova):
        from jogo.cenas.selecao import CenaSelecao
        opcoes = OpcoesDePartida.treino_contra(prova, self.direto_no_chefe, self.imortal)
        self.app.trocar(CenaSelecao(self.app, opcoes))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_c:
                self.direto_no_chefe = not self.direto_no_chefe
                return
            if evento.key == pygame.K_i:
                self.imortal = not self.imortal
                return
            if evento.key == pygame.K_ESCAPE:
                from jogo.cenas.titulo import CenaTitulo
                self.app.trocar(CenaTitulo(self.app))
                return
        self.menu.tratar_evento(evento)

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=170)
        desenhar_texto(tela, "MODO TREINO", 44, Cor.DESTAQUE, centro=(LARGURA // 2, 80))
        desenhar_texto(tela, "Escolha qual professor enfrentar. Treino não entra no ranking.", 18, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, 130))
        self.menu.desenhar(tela)
        sim_nao = {True: "SIM", False: "NÃO"}
        desenhar_texto(tela, f"[C] Começar direto no chefe: {sim_nao[self.direto_no_chefe]}", 22,
                       Cor.DESTAQUE if self.direto_no_chefe else Cor.TEXTO, centro=(LARGURA // 2, 520))
        desenhar_texto(tela, f"[I] Aluno imortal: {sim_nao[self.imortal]}", 22,
                       Cor.DESTAQUE if self.imortal else Cor.TEXTO, centro=(LARGURA // 2, 560))
        desenhar_texto(tela, "[Enter] escolher    [Esc] voltar", 16, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 24))
