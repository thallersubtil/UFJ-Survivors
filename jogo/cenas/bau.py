import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR, desenhar_texto, escurecer
from jogo.config import ALTURA, LARGURA, Cor
from jogo.nucleo.recursos import Recursos
from jogo.progressao import Progressao


class CenaBau(Cena):
    QUADROS = tuple(f"legado/itens/chest_f{i}.png" for i in range(4))
    DURACAO_ABERTURA = 1.0

    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.tempo = 0.0
        self.premio = Progressao.premio_bau(jogo.jogador, jogo.rng)
        self.aberto = False

    def tratar_evento(self, evento):
        if not self.aberto:
            return
        confirmou = evento.type == pygame.KEYDOWN and evento.key in TECLAS_CONFIRMAR
        clicou = evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
        if confirmou or clicou:
            self.jogo.baus_pendentes = max(0, self.jogo.baus_pendentes - 1)
            self.app.desempilhar()

    def atualizar(self, dt):
        self.tempo += dt
        if not self.aberto and self.tempo >= self.DURACAO_ABERTURA:
            self.premio.aplicar(self.jogo.jogador, self.jogo)
            self.aberto = True
            Recursos.tocar("bau", 0.6)

    def desenhar(self, tela):
        escurecer(tela, 170)
        desenhar_texto(tela, "BAÚ!", 56, Cor.DESTAQUE, centro=(LARGURA // 2, 110))
        quadro = min(len(self.QUADROS) - 1, int(self.tempo / self.DURACAO_ABERTURA * len(self.QUADROS)))
        tremor = 0 if self.aberto else round(4 * ((self.tempo * 30) % 2 - 1))
        bau = Recursos.imagem(self.QUADROS[quadro], 210)
        tela.blit(bau, bau.get_rect(center=(LARGURA // 2 + tremor, 300)))
        if self.aberto:
            icone = Recursos.icone(self.premio.icone, 72)
            tela.blit(icone, icone.get_rect(center=(LARGURA // 2, 470)))
            desenhar_texto(tela, f"Você ganhou: {self.premio.titulo}", 28, Cor.TEXTO, centro=(LARGURA // 2, 540))
            if self.premio.rotulo:
                desenhar_texto(tela, self.premio.rotulo, 18, Cor.DESTAQUE, centro=(LARGURA // 2, 572))
            desenhar_texto(tela, "[Enter] continuar", 16, Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 40))
