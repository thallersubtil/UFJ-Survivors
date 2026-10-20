"""Personalização do aluno antes da partida: gênero, cabelo, olhos, roupas, acessório e cores."""
import random

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_ENTER, desenhar_fundo, desenhar_painel, desenhar_texto
from jogo.config import ALTURA, LARGURA, Cor
from jogo.jogador.aparencia import PADRAO, PADRAO_FEMININO, Aparencia
from jogo.jogador.boneco import Boneco
from jogo.opcoes import OpcoesDePartida


class CenaPersonalizacao(Cena):
    LINHAS = (("genero", "Gênero"), ("penteado", "Cabelo"), ("cabelo", "Cor do cabelo"), ("olhos", "Olhos"),
              ("pele", "Tom de pele"), ("cima", "Parte de cima"), ("cor_cima", "Cor de cima"),
              ("baixo", "Parte de baixo"), ("cor_baixo", "Cor de baixo"), ("acessorio", "Acessório"))
    PADROES = {"Masculino": PADRAO, "Feminino": PADRAO_FEMININO}
    ESCALA_PREVIA = 3

    def __init__(self, app, classe_jogador, opcoes=None):
        super().__init__(app)
        self.classe_jogador = classe_jogador
        self.opcoes = opcoes or OpcoesDePartida()
        anterior = getattr(app, "aparencia", None)
        self.aparencia = anterior.copia() if anterior is not None else Aparencia(**classe_jogador.APARENCIA)
        self.linha = 0
        self.tempo = 0.0
        self.andando = True
        self.retangulos = []
        for i in range(len(self.LINHAS)):
            r = pygame.Rect(0, 0, 640, 48)
            r.topleft = (560, 128 + i * 54)
            self.retangulos.append(r)

    def _mudar(self, passo):
        parte = self.LINHAS[self.linha][0]
        genero_antes = self.aparencia.genero
        self.aparencia.trocar(parte, passo)
        if parte == "genero":
            self._ajustar_ao_genero(genero_antes)

    def _ajustar_ao_genero(self, genero_antes):
        """O que ainda estava no padrão do gênero anterior passa para o padrão do novo."""
        antes, depois = self.PADROES[genero_antes], self.PADROES[self.aparencia.genero]
        for parte in ("penteado", "baixo", "cor_baixo"):
            if self.aparencia.escolha(parte) == antes[parte]:
                setattr(self.aparencia, parte, depois[parte])

    def _sortear(self):
        self.aparencia.sortear(random)

    def _comecar(self):
        from jogo.cenas.partida import CenaPartida
        escolhida = self.aparencia.copia()
        self.app.aparencia = escolhida
        self.app.trocar(CenaPartida(self.app, self.classe_jogador, self.opcoes.com_aparencia(escolhida)))

    def _voltar(self):
        from jogo.cenas.selecao import CenaSelecao
        self.app.trocar(CenaSelecao(self.app, self.opcoes))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_w):
                self.linha = (self.linha - 1) % len(self.LINHAS)
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.linha = (self.linha + 1) % len(self.LINHAS)
            elif evento.key in (pygame.K_LEFT, pygame.K_a):
                self._mudar(-1)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self._mudar(1)
            elif evento.key == pygame.K_r:
                self._sortear()
            elif evento.key == pygame.K_TAB:
                self.andando = not self.andando
            elif evento.key in TECLAS_ENTER:
                self._comecar()
            elif evento.key == pygame.K_ESCAPE:
                self._voltar()
        elif evento.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.retangulos):
                if r.collidepoint(evento.pos):
                    self.linha = i
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, r in enumerate(self.retangulos):
                if r.collidepoint(evento.pos):
                    self.linha = i
                    self._mudar(-1 if evento.pos[0] < r.left + 400 else 1)

    def atualizar(self, dt):
        self.tempo += dt

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=170)
        desenhar_texto(tela, "MONTE SEU PERSONAGEM", 44, Cor.DESTAQUE, centro=(LARGURA // 2, 60))
        if self.opcoes.treino:
            desenhar_texto(tela, "MODO TREINO", 18, Cor.TEXTO_FRACO, centro=(LARGURA // 2, 100))
        palco = pygame.Rect(80, 128, 440, 534)
        desenhar_painel(tela, palco)
        animacoes = Boneco.animacoes_de(self.aparencia, escala=self.ESCALA_PREVIA)
        sprite = animacoes["andar" if self.andando else "parado"].quadro(self.tempo)
        tela.blit(sprite, sprite.get_rect(midbottom=(palco.centerx, palco.bottom - 90)))
        desenhar_texto(tela, self.classe_jogador.NOME, 28, Cor.TEXTO, centro=(palco.centerx, palco.bottom - 60))
        desenhar_texto(tela, "[Tab] parado/andando", 14, Cor.TEXTO_FRACO, centro=(palco.centerx, palco.bottom - 28))
        for i, ((parte, rotulo), r) in enumerate(zip(self.LINHAS, self.retangulos)):
            focado = i == self.linha
            desenhar_painel(tela, r, cor_borda=Cor.DESTAQUE if focado else Cor.BORDA_ESCURA)
            desenhar_texto(tela, rotulo, 18, Cor.TEXTO_FRACO, topo_esquerda=(r.left + 18, r.top + 14))
            desenhar_texto(tela, f"<  {self.aparencia.escolha(parte)}  >", 22, Cor.DESTAQUE if focado else Cor.TEXTO,
                           centro=(r.left + 400, r.centery))
            cor = self.aparencia.cor(parte)
            if cor is not None:
                amostra = (r.right - 34, r.centery)
                pygame.draw.circle(tela, Cor.BORDA_ESCURA, amostra, 16)
                pygame.draw.circle(tela, cor, amostra, 13)
        desenhar_texto(tela, "[Cima/Baixo] escolher    [<- ->] trocar    [R] sortear    "
                       "[Enter] começar    [Esc] voltar", 16, Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 24))
