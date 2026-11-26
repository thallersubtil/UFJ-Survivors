"""Tela de título: menu na lateral no estilo HoloCure e alunos correndo pelo campus (opção A aprovada)."""
import math

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR
from jogo.config import ALTURA, LARGURA, TITULO
from jogo.nucleo.recursos import Recursos
from jogo.ui.pixel import (A, ESCALA, L, CamadaPixel, Paleta as P, boneco_nitido, ease_back, icone, janela, onda,
                           texto)


class CenaTitulo(Cena):
    LOGO = "sprites/logo.png"
    FUNDO = "cenario/titulo_fundo.png"
    CORREDORES = ("otaku", "programador", "gamer", "calouro", "cara_da_carona")
    _fundo_cache = {}

    def __init__(self, app):
        super().__init__(app)
        self.tempo = 0.0
        self.indice = 0
        self.camada = CamadaPixel()
        self.opcoes = [("JOGAR", self._jogar), ("CENTRO ACADÊMICO", self._centro_academico),
                       ("TREINO", self._treino), ("RANKING", self._ranking), ("SAIR", app.sair)]

    # ------------------------------------------------------------ ações
    def _jogar(self):
        from jogo.cenas.matricula import CenaMatricula
        from jogo.opcoes import OpcoesDePartida
        self.app.trocar(CenaMatricula(self.app, OpcoesDePartida().com_progresso(self.app.progresso)))

    def _centro_academico(self):
        from jogo.cenas.centro_academico import CenaCentroAcademico
        self.app.trocar(CenaCentroAcademico(self.app))

    def _treino(self):
        from jogo.cenas.treino import CenaTreino
        self.app.trocar(CenaTreino(self.app))

    def _ranking(self):
        from jogo.cenas.ranking import CenaRanking
        self.app.trocar(CenaRanking(self.app))

    # ------------------------------------------------------------ entrada
    def botao(self, i):
        """Retângulo do botão i na camada (a animação de entrada não muda a área de clique)."""
        return pygame.Rect(0, 120 + i * 38, 204, 30)

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_w):
                self.indice = (self.indice - 1) % len(self.opcoes)
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.indice = (self.indice + 1) % len(self.opcoes)
            elif evento.key in TECLAS_CONFIRMAR:
                self.opcoes[self.indice][1]()
        elif evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            pos = CamadaPixel.para_camada(evento.pos)
            for i in range(len(self.opcoes)):
                if self.botao(i).collidepoint(pos):
                    self.indice = i
                    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                        self.opcoes[i][1]()
                    return

    def atualizar(self, dt):
        self.tempo += dt

    # ------------------------------------------------------------ desenho
    def _fundo(self, tela):
        if not (Recursos.pasta / self.FUNDO).exists():
            tela.fill(P.NAVY)
            return
        chave = tela.get_size()
        if chave not in self._fundo_cache:
            img = pygame.transform.smoothscale(Recursos.imagem(self.FUNDO), (LARGURA + 60, ALTURA + 34))
            veu = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            veu.fill((10, 8, 20, 70))
            img.blit(veu, (0, 0))
            self._fundo_cache[chave] = img
        tela.blit(self._fundo_cache[chave], (-30 + int(30 * math.sin(self.tempo * 0.15)), -17))

    def _logo(self, ui):
        entrada = janela(self.tempo, 0.1, 0.6)
        y = 110 + int(3 * onda(self.tempo, 0.5))
        if (Recursos.pasta / self.LOGO).exists():
            img = pygame.transform.scale_by(icone(self.LOGO, 250), 0.3 + 0.7 * ease_back(entrada, 2.2))
            ui.blit(img, img.get_rect(center=(440, y)))
        else:
            texto(ui, TITULO.upper(), (440, y), P.OURO, 23, ancora="center")

    def _corredores(self, tela):
        """Os alunos correndo no rodapé, direto na tela (a arte grande reduzida, sem passar pela camada)."""
        for i, pasta in enumerate(self.CORREDORES):
            quadros_do_andar = boneco_nitido(pasta, "andar", altura=40 * ESCALA)
            if not quadros_do_andar:
                continue
            x = (self.tempo * 70 + i * 120) % (L + 120) - 60
            quadro = quadros_do_andar[int(self.tempo * 10 + i) % len(quadros_do_andar)]
            tela.blit(quadro, quadro.get_rect(midbottom=(int(x * ESCALA), 344 * ESCALA)))

    def _menu(self, ui):
        for i, (nome, _) in enumerate(self.opcoes):
            k = ease_back(janela(self.tempo, 0.4 + i * 0.08, 0.4), 1.3)
            sel = i == self.indice
            r = pygame.Rect(int(-200 * (1 - k)) + (14 if sel else 0), 120 + i * 38, 190, 30)
            pygame.draw.polygon(ui, P.ESC, [(r.x, r.y - 1), (r.right + 9, r.y - 1), (r.right - 1, r.bottom + 1),
                                            (r.x, r.bottom + 1)])
            pygame.draw.polygon(ui, P.SELECAO if sel else P.NAVY, [(r.x, r.y), (r.right + 8, r.y), (r.right, r.bottom),
                                                                   (r.x, r.bottom)])
            pygame.draw.line(ui, P.OURO if sel else (190, 205, 240), (r.x, r.y + 1), (r.right + 6, r.y + 1), 2)
            texto(ui, nome, (r.x + 22, r.y + 9), P.OURO if sel else P.BRANCO, 11)
            if sel:                                               # seta apontando para a opção escolhida
                x, y = r.right + 16 + int(3 * abs(onda(self.tempo, 1.2))), r.centery
                pygame.draw.polygon(ui, P.ESC, [(x - 2, y), (x + 11, y - 10), (x + 11, y - 5), (x + 23, y - 5),
                                                (x + 23, y + 5), (x + 11, y + 5), (x + 11, y + 10)])
                pygame.draw.polygon(ui, P.OURO, [(x, y), (x + 10, y - 8), (x + 10, y - 3), (x + 21, y - 3),
                                                 (x + 21, y + 3), (x + 10, y + 3), (x + 10, y + 8)])

    def desenhar(self, tela):
        self._fundo(tela)
        ui = self.camada.limpar()
        self._logo(ui)
        self._menu(ui)
        texto(ui, "Trabalho de POO  ·  UFJ 2026", (L - 8, A - 14), P.CINZA, 11, ancora="topright")
        self.camada.apresentar(tela)
        self._corredores(tela)
