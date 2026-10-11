import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import Botao, MenuDeBotoes, desenhar_texto, escurecer
from jogo.config import ALTURA, LARGURA, Cor


class CenaPausa(Cena):
    def __init__(self, app, partida):
        super().__init__(app)
        self.partida = partida
        meio = LARGURA // 2
        self.menu = MenuDeBotoes([
            Botao("CONTINUAR", (meio, 300), self._continuar, largura=380),
            Botao(self._texto_mira(), (meio, 380), self._alternar_mira, largura=380),
            Botao("SAIR PARA O TÍTULO", (meio, 460), self._sair, largura=380),
        ])

    def _texto_mira(self):
        return "MIRA: MOUSE" if self.app.mira_mouse else "MIRA: TECLADO"

    def _alternar_mira(self):
        self.app.mira_mouse = not self.app.mira_mouse
        self.menu.botoes[1].texto = self._texto_mira()

    def _continuar(self):
        self.app.desempilhar()

    def _sair(self):
        from jogo.cenas.titulo import CenaTitulo
        self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self._continuar()
        else:
            self.menu.tratar_evento(evento)

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        escurecer(tela, 160)
        desenhar_texto(tela, "PAUSADO", 56, Cor.DESTAQUE, centro=(LARGURA // 2, 180))
        self.menu.desenhar(tela)
        desenhar_texto(tela, "WASD ou setas: andar    Espaço: especial    Esc: pausar", 16, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 40))
