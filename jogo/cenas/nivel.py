import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_ENTER, desenhar_painel, desenhar_texto, escurecer, quebrar_linhas
from jogo.config import ALTURA, CURA_AO_PULAR, LARGURA, Cor
from jogo.nucleo.recursos import Recursos
from jogo.progressao import Progressao

CORES_ROTULO = {"colab": Cor.DESTAQUE, "nova": Cor.APROVADO, "melhoria": Cor.EXPERIENCIA, "lanche": Cor.CURA}


class CenaNivel(Cena):
    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.indice = 0
        self._sortear()
        Recursos.tocar("nivel", 0.5)

    def _sortear(self):
        self.opcoes = Progressao.gerar_opcoes(self.jogo.jogador, self.jogo.rng)
        self.indice = 0
        self.cartoes = []
        for i in range(len(self.opcoes)):
            r = pygame.Rect(0, 0, 310, 380)
            r.center = (LARGURA // 2 + (i - (len(self.opcoes) - 1) / 2) * 340, 380)
            self.cartoes.append(r)

    def escolher(self, i):
        self.opcoes[i].aplicar(self.jogo.jogador, self.jogo)
        self._fechar()

    def sortear_de_novo(self):
        if self.jogo.sorteios_restantes > 0:
            self.jogo.sorteios_restantes -= 1
            self._sortear()

    def pular(self):
        self.jogo.jogador.curar(CURA_AO_PULAR)
        self._fechar()

    def _fechar(self):
        self.jogo.niveis_pendentes = max(0, self.jogo.niveis_pendentes - 1)
        self.app.desempilhar()

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            numeros = (pygame.K_1, pygame.K_2, pygame.K_3)
            if evento.key in numeros and numeros.index(evento.key) < len(self.opcoes):
                self.escolher(numeros.index(evento.key))
            elif evento.key in (pygame.K_LEFT, pygame.K_a):
                self.indice = (self.indice - 1) % len(self.opcoes)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.indice = (self.indice + 1) % len(self.opcoes)
            elif evento.key in TECLAS_ENTER:
                self.escolher(self.indice)
            elif evento.key == pygame.K_r:
                self.sortear_de_novo()
            elif evento.key == pygame.K_p:
                self.pular()
        elif evento.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.cartoes):
                if r.collidepoint(evento.pos):
                    self.indice = i
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, r in enumerate(self.cartoes):
                if r.collidepoint(evento.pos):
                    self.escolher(i)
                    return

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        escurecer(tela, 170)
        desenhar_texto(tela, "SUBIU DE NÍVEL!", 48, Cor.DESTAQUE, centro=(LARGURA // 2, 110))
        fonte_titulo, fonte_texto = Recursos.fonte(22), Recursos.fonte(16)
        for i, (opcao, r) in enumerate(zip(self.opcoes, self.cartoes)):
            focado = i == self.indice
            desenhar_painel(tela, r, cor_borda=Cor.DESTAQUE if focado else Cor.BORDA)
            desenhar_texto(tela, str(i + 1), 18, Cor.TEXTO_FRACO, topo_esquerda=(r.left + 14, r.top + 10))
            icone = Recursos.icone(opcao.icone, 80)
            tela.blit(icone, icone.get_rect(center=(r.centerx, r.top + 75)))
            if opcao.rotulo:
                desenhar_texto(tela, opcao.rotulo, 16, CORES_ROTULO[opcao.tipo], centro=(r.centerx, r.top + 135))
            y = r.top + 160
            for linha in quebrar_linhas(opcao.titulo, fonte_titulo, r.width - 30):
                desenhar_texto(tela, linha, 22, Cor.TEXTO, centro=(r.centerx, y))
                y += 26
            y += 10
            for linha in quebrar_linhas(opcao.descricao, fonte_texto, r.width - 36):
                desenhar_texto(tela, linha, 16, Cor.TEXTO_FRACO, centro=(r.centerx, y))
                y += 20
        rodape = (f"[1] [2] [3] ou Enter: escolher    [R] sortear de novo ({self.jogo.sorteios_restantes})    "
                  f"[P] pular (+{CURA_AO_PULAR} de vida)")
        desenhar_texto(tela, rodape, 16, Cor.TEXTO, centro=(LARGURA // 2, ALTURA - 60))
