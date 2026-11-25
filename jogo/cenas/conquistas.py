"""Sala de troféus: as conquistas como taças numa estante de vidro (opção A aprovada).

Taça de ouro, prata ou bronze conforme o prêmio; as que faltam ficam escuras com "?". A placa embaixo diz o nome,
o que fazer e quanto vale.
"""
import math

import pygame

from jogo.cenas.cena import Cena
from jogo.loja.conquistas import CONQUISTAS
from jogo.ui.materiais import fundo_desfocado, moldura_madeira
from jogo.ui.pixel import A, L, CamadaPixel, Paleta as P, ease_out, fonte, janela, quebrar, texto

CORES_TACA = {"ouro": ((255, 210, 70), (200, 140, 30), (255, 245, 180)),
              "prata": ((210, 216, 228), (140, 146, 166), (250, 252, 255)),
              "bronze": ((214, 140, 80), (150, 86, 40), (250, 200, 150))}


def tipo_da_taca(conquista):
    """Prêmio alto vira ouro, médio prata, o resto bronze."""
    if conquista.PREMIO >= 150:
        return "ouro"
    return "prata" if conquista.PREMIO >= 80 else "bronze"


def desenhar_taca(tipo, feita, giro=0.0, h=46):
    """Taça em pixel art; `giro` estreita a taça (parece girar)."""
    base, sombra, brilho = CORES_TACA[tipo] if feita else ((60, 56, 70), (40, 36, 48), (80, 76, 90))
    w = 40
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, P.ESC, (8, h - 8, 24, 8))
    pygame.draw.rect(s, (90, 60, 40) if feita else (50, 46, 56), (9, h - 7, 22, 6))
    pygame.draw.rect(s, P.ESC, (17, h - 18, 6, 11))
    pygame.draw.rect(s, sombra, (18, h - 17, 4, 10))
    pygame.draw.ellipse(s, P.ESC, (4, 2, 32, 26))
    pygame.draw.rect(s, P.ESC, (4, 2, 32, 12))
    pygame.draw.ellipse(s, base, (5, 3, 30, 24))
    pygame.draw.rect(s, base, (5, 3, 30, 11))
    pygame.draw.ellipse(s, sombra, (22, 6, 12, 20))
    pygame.draw.line(s, brilho, (10, 6), (10, 18), 2)
    for lado in (-1, 1):                        # alças
        cx = 20 + lado * 18
        pygame.draw.arc(s, P.ESC, (cx - 6, 6, 12, 14), math.pi / 2 if lado < 0 else -math.pi / 2,
                        3 * math.pi / 2 if lado < 0 else math.pi / 2, 3)
    if not feita:
        texto(s, "?", (20, 15), (120, 116, 130), 11, contorno=None, ancora="center")
    if giro:
        s = pygame.transform.scale(s, (max(2, int(w * abs(math.cos(giro)))), h))
    return s


class CenaConquistas(Cena):
    ESTANTE = pygame.Rect(60, 40, 520, 268)
    POR_PRATELEIRA = 5

    def __init__(self, app):
        super().__init__(app)
        self.tempo = 0.0
        self.indice = 0
        self.camada = CamadaPixel()

    @property
    def feitas(self):
        return self.app.progresso.conquistas

    def _voltar(self):
        from jogo.cenas.centro_academico import CenaCentroAcademico
        self.app.trocar(CenaCentroAcademico(self.app))

    # ------------------------------------------------------------ posições (camada)
    @property
    def _altura_prateleira(self):
        prateleiras = math.ceil(len(CONQUISTAS) / self.POR_PRATELEIRA)
        return min(132, (self.ESTANTE.h - 10) // max(1, prateleiras))

    def base_da_taca(self, i):
        coluna, prateleira = i % self.POR_PRATELEIRA, i // self.POR_PRATELEIRA
        e = self.ESTANTE
        return e.x + 56 + coluna * 102, e.y + 110 + prateleira * self._altura_prateleira

    def caixa_da_taca(self, i):
        x, y = self.base_da_taca(i)
        return pygame.Rect(x - 45, y - 96, 90, 120)

    # ------------------------------------------------------------ entrada
    def tratar_evento(self, evento):
        n = len(CONQUISTAS)
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_BACKSPACE):
                self._voltar()
            elif evento.key in (pygame.K_LEFT, pygame.K_a):
                self.indice = (self.indice - 1) % n
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.indice = (self.indice + 1) % n
            elif evento.key in (pygame.K_UP, pygame.K_w):
                self.indice = (self.indice - self.POR_PRATELEIRA) % n
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.indice = (self.indice + self.POR_PRATELEIRA) % n
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 3:
            self._voltar()
        elif evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            pos = CamadaPixel.para_camada(evento.pos)
            for i in range(n):
                if self.caixa_da_taca(i).collidepoint(pos):
                    self.indice = i
                    return

    def atualizar(self, dt):
        self.tempo += dt

    # ------------------------------------------------------------ desenho
    def _brilhos(self, ui, centro, raio, n, fase):
        for j in range(n):
            a = (self.tempo + fase) * 1.5 + j * 2 * math.pi / n
            x, y = int(centro[0] + raio * math.cos(a)), int(centro[1] + raio * 0.6 * math.sin(a))
            f = int(2 + 2 * abs(math.sin((self.tempo + fase) * 4 + j)))
            pygame.draw.line(ui, P.BRANCO, (x - f, y), (x + f, y))
            pygame.draw.line(ui, P.BRANCO, (x, y - f), (x, y + f))

    def _placa(self, ui, conquista):
        feita = conquista.CHAVE in self.feitas
        p = pygame.Rect(L // 2 - 225, 318, 450, 38)
        pygame.draw.rect(ui, P.ESC, p.inflate(4, 4), border_radius=3)
        pygame.draw.rect(ui, (196, 156, 70) if feita else (120, 110, 100), p, border_radius=3)
        pygame.draw.rect(ui, (240, 210, 130) if feita else (150, 140, 130), p, 1, border_radius=3)
        for x in (p.x + 6, p.right - 6):
            pygame.draw.circle(ui, (120, 90, 40), (x, p.centery), 2)
        texto(ui, conquista.NOME, (p.centerx, p.y + 4), P.ESC, 11, contorno=None, ancora="midtop")
        extra = "  ·  conquistada" if feita else f"  ·  vale {conquista.PREMIO} moedas"
        texto(ui, conquista.DESCRICAO + extra, (p.centerx, p.y + 20), (60, 40, 20), 11, contorno=None, media=True,
              ancora="midtop")

    def desenhar(self, tela):
        fundo_desfocado(tela, "cenario/centro_academico.png", escuro=150)
        ui = self.camada.limpar()
        feitas = self.feitas
        texto(ui, "SALA DE TROFÉUS", (L // 2, 6), P.OURO, 23, ancora="midtop")
        total = len(feitas & {c.CHAVE for c in CONQUISTAS})
        texto(ui, f"{total} de {len(CONQUISTAS)}", (L - 14, 10), P.CINZA, 11, ancora="topright")
        sobe = int(300 * (1 - ease_out(janela(self.tempo, 0, 0.45))))
        estante = pygame.Surface((L, A), pygame.SRCALPHA)
        self._estante(estante, feitas)
        ui.blit(estante, (0, sobe))
        self._placa(ui, CONQUISTAS[self.indice])
        texto(ui, "Setas ou mouse: ver    Esc: voltar", (14, 10), P.CINZA, 11)
        self.camada.apresentar(tela)

    def _estante(self, ui, feitas):
        e = self.ESTANTE
        moldura_madeira(ui, e, 8, (100, 62, 36))
        pygame.draw.rect(ui, (40, 34, 46), e)
        luz = pygame.Surface(e.size, pygame.SRCALPHA)
        for y in range(40):
            pygame.draw.line(luz, (255, 230, 170, 40 - y), (0, y), (e.w, y))
        altura = self._altura_prateleira
        prateleiras = math.ceil(len(CONQUISTAS) / self.POR_PRATELEIRA)
        for p in range(prateleiras):
            for y in range(30):
                yy = altura * p + 90 - y
                pygame.draw.line(luz, (255, 230, 170, max(0, 22 - y)), (0, yy), (e.w, yy))
        ui.blit(luz, e.topleft)
        for p in range(prateleiras):
            y = e.y + 110 + p * altura
            pygame.draw.rect(ui, (180, 200, 220), (e.x, y, e.w, 4))
            pygame.draw.rect(ui, (120, 140, 160), (e.x, y + 4, e.w, 2))
        for i, conquista in enumerate(CONQUISTAS):
            cx, base = self.base_da_taca(i)
            feita = conquista.CHAVE in feitas
            sel = i == self.indice
            taca = desenhar_taca(tipo_da_taca(conquista), feita, self.tempo * 3 if sel and feita else 0.0)
            taca = pygame.transform.scale(taca, (taca.get_width() * 2, 92))
            ui.blit(taca, taca.get_rect(midbottom=(cx, base - (4 if sel else 0))))
            if feita:
                self._brilhos(ui, (cx, base - 60), 44 if sel else 30, 4 if sel else 2, i)
            if sel:
                pygame.draw.polygon(ui, P.OURO, [(cx - 6, base + 8), (cx + 6, base + 8), (cx, base + 2)])
            cor = P.OURO if sel else (P.CINZA if feita else (110, 106, 120))
            for j, linha in enumerate(quebrar(conquista.NOME, fonte(11), 96)[:2]):   # nome inteiro, em até 2 linhas
                texto(ui, linha, (cx, base + 10 + j * 10), cor, 11, ancora="midtop")
        x = int(((self.tempo * 0.35) % 1.5) * (e.w + 200)) - 100          # reflexo do vidro
        vidro = pygame.Surface(e.size, pygame.SRCALPHA)
        pygame.draw.polygon(vidro, (255, 255, 255, 26), [(x, 0), (x + 40, 0), (x - 60, e.h), (x - 100, e.h)])
        pygame.draw.polygon(vidro, (255, 255, 255, 16), [(x + 60, 0), (x + 70, 0), (x - 30, e.h), (x - 40, e.h)])
        ui.blit(vidro, e.topleft)
        pygame.draw.rect(ui, (200, 180, 120), (e.right - 10, e.centery - 8, 4, 16))      # puxador
