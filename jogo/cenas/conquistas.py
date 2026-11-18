"""Lista das conquistas no Centro Acadêmico: as alcançadas em destaque, as outras apagadas."""
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import desenhar_fundo, desenhar_moedas, desenhar_painel, desenhar_texto
from jogo.config import ALTURA, LARGURA, Cor
from jogo.loja.conquistas import CONQUISTAS


class CenaConquistas(Cena):
    def tratar_evento(self, evento):
        saiu = (evento.type == pygame.KEYDOWN and evento.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER)) \
            or (evento.type == pygame.MOUSEBUTTONDOWN and evento.button in (1, 3))
        if saiu:
            from jogo.cenas.centro_academico import CenaCentroAcademico
            self.app.trocar(CenaCentroAcademico(self.app))

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/centro_academico.png", escuro=170)
        feitas = self.app.progresso.conquistas
        desenhar_texto(tela, "CONQUISTAS", 44, Cor.DESTAQUE, centro=(LARGURA // 2, 60))
        desenhar_texto(tela, f"{len(feitas & {c.CHAVE for c in CONQUISTAS})} de {len(CONQUISTAS)}", 18,
                       Cor.TEXTO_FRACO, centro=(LARGURA // 2, 98))
        desenhar_moedas(tela, self.app.progresso.moedas)
        for i, classe in enumerate(CONQUISTAS):
            coluna, linha = i % 2, i // 2
            caixa = pygame.Rect(0, 0, 560, 96)
            caixa.topleft = (LARGURA // 2 - 575 + coluna * 590, 130 + linha * 108)
            feita = classe.CHAVE in feitas
            desenhar_painel(tela, caixa, cor_borda=Cor.APROVADO if feita else Cor.BORDA, alfa=240 if feita else 140)
            desenhar_texto(tela, classe.NOME, 22, Cor.DESTAQUE if feita else Cor.TEXTO_FRACO,
                           topo_esquerda=(caixa.left + 18, caixa.top + 14))
            desenhar_texto(tela, classe.DESCRICAO, 16, Cor.TEXTO if feita else Cor.TEXTO_FRACO,
                           topo_esquerda=(caixa.left + 18, caixa.top + 52), sombra=False)
            desenhar_texto(tela, "FEITA" if feita else f"+{classe.PREMIO} moedas", 18,
                           Cor.APROVADO if feita else Cor.TEXTO_FRACO, topo_direita=(caixa.right - 18, caixa.top + 16))
        desenhar_texto(tela, "Esc ou Enter: voltar", 16, Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 24))
