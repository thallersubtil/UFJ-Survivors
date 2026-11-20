"""Modo treino: a agenda aberta na mesa com a semana de provas; escolha qual professor enfrentar (opção A)."""
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR
from jogo.fase import PROVAS
import jogo.inimigos  # noqa: F401  (importar o pacote registra os chefes na fábrica)
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.nucleo.recursos import Recursos
from jogo.opcoes import OpcoesDePartida
from jogo.ui.materiais import caneta, fita, madeira, papel, ruido
from jogo.ui.pixel import (A, L, CamadaPixel, Paleta as P, ease_back, ease_out, fonte, janela, quadros, quebrar,
                           texto)

TINTA = (40, 50, 110)


class CenaTreino(Cena):
    DIAS = ("SEG 16", "QUA 18", "SEX 20", "SEG 23", "QUA 25")
    CORES = ((220, 80, 80), (70, 130, 220), (150, 90, 210), (60, 160, 100), (220, 150, 60))
    AGENDA = pygame.Rect(36, 16, 568, 318)

    def __init__(self, app):
        super().__init__(app)
        self.direto_no_chefe = False
        self.imortal = False
        self.indice = 0
        self.tempo = 0.0
        self._t_foco = 0.3
        self.camada = CamadaPixel()
        self._mesa = None

    # ------------------------------------------------------------ regras
    def _comecar(self, prova):
        from jogo.cenas.personalizacao import CenaPersonalizacao
        opcoes = OpcoesDePartida.treino_contra(prova, self.direto_no_chefe, self.imortal).com_progresso(self.app.progresso)
        self.app.trocar(CenaPersonalizacao(self.app, opcoes))

    def escolher(self, i):
        i %= len(PROVAS)
        if i != self.indice:
            self.indice, self._t_foco = i, self.tempo

    @staticmethod
    def chefe_da(prova):
        try:
            return FabricaDeInimigos.classe(prova.CHEFE)
        except (KeyError, ValueError):
            return None

    # ------------------------------------------------------------ posições (camada)
    @property
    def _paginas(self):
        ag = self.AGENDA
        return pygame.Rect(ag.x, ag.y, ag.w // 2 - 6, ag.h), pygame.Rect(ag.centerx + 6, ag.y, ag.w // 2 - 6, ag.h)

    def linha(self, i):
        esq, _ = self._paginas
        passo = min(88, (esq.h - 50) // max(1, len(PROVAS)))
        return pygame.Rect(esq.x + 8, esq.y + 44 + i * passo, esq.w - 16, passo - 8)

    def caixa_marcar(self, i):
        _, dir_ = self._paginas
        return pygame.Rect(dir_.x + 14, dir_.y + 152 + i * 18, 160, 14)

    # ------------------------------------------------------------ entrada
    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_c:
                self.direto_no_chefe = not self.direto_no_chefe
            elif evento.key == pygame.K_i:
                self.imortal = not self.imortal
            elif evento.key == pygame.K_ESCAPE:
                from jogo.cenas.titulo import CenaTitulo
                self.app.trocar(CenaTitulo(self.app))
            elif evento.key in (pygame.K_UP, pygame.K_w):
                self.escolher(self.indice - 1)
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.escolher(self.indice + 1)
            elif evento.key in TECLAS_CONFIRMAR:
                self._comecar(PROVAS[self.indice])
        elif evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            pos = CamadaPixel.para_camada(evento.pos)
            clique = evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
            for i in range(len(PROVAS)):
                if self.linha(i).collidepoint(pos):
                    if clique and i == self.indice:
                        self._comecar(PROVAS[i])
                    else:
                        self.escolher(i)
                    return
            if clique and self.caixa_marcar(0).collidepoint(pos):
                self.direto_no_chefe = not self.direto_no_chefe
            elif clique and self.caixa_marcar(1).collidepoint(pos):
                self.imortal = not self.imortal

    def atualizar(self, dt):
        self.tempo += dt

    # ------------------------------------------------------------ desenho
    def _polaroide(self, pasta, w, h, animado, cinza):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((250, 248, 240))
        ruido(s, s.get_rect(), (236, 232, 222), w * h // 12, 9)
        foto = pygame.Rect(5, 5, w - 10, h - 22)
        pygame.draw.rect(s, (196, 186, 214), foto)
        if pasta and (Recursos.pasta / "sprites" / pasta / "parado-4.png").exists():
            quadro = quadros(pasta, altura=int(foto.h * 1.6))[int(self.tempo * 5) % 4 if animado else 0]
            s.subsurface(foto).blit(quadro, quadro.get_rect(midtop=(foto.w // 2, 2)))
        if cinza:
            s.fill((190, 180, 170), special_flags=pygame.BLEND_RGB_MULT)
        pygame.draw.rect(s, (200, 194, 180), s.get_rect(), 1)
        return s

    def _fundo_mesa(self, tela):
        if self._mesa is None or self._mesa.get_size() != tela.get_size():
            mesa = pygame.Surface((L, A))
            madeira(mesa, mesa.get_rect(), (104, 66, 40), tabuas=28, semente=6)
            self._mesa = pygame.transform.scale(mesa, tela.get_size())
        tela.blit(self._mesa, (0, 0))

    def desenhar(self, tela):
        self._fundo_mesa(tela)
        ui = self.camada.limpar()
        sobe = int(360 * (1 - ease_back(janela(self.tempo, 0, 0.5), 1.1)))
        ui_agenda = pygame.Surface((L, A), pygame.SRCALPHA)
        self._agenda(ui_agenda)
        ui.blit(ui_agenda, (0, sobe))
        texto(ui, "Setas: escolher a prova    C e I: marcar    Esc: voltar", (L // 2, A - 14), P.BRANCO, 11,
              ancora="midtop")
        self.camada.apresentar(tela)

    def _agenda(self, ui):
        ag = self.AGENDA
        pygame.draw.rect(ui, (0, 0, 0, 90), ag.inflate(14, 14).move(4, 6), border_radius=10)
        pygame.draw.rect(ui, (90, 40, 40), ag.inflate(14, 14), border_radius=10)
        pygame.draw.rect(ui, (120, 56, 52), ag.inflate(10, 10), 2, border_radius=8)
        esq, dir_ = self._paginas
        papel(ui, esq, (250, 246, 232), semente=11, linhas=(40, 13), sombra=False)
        papel(ui, dir_, (250, 246, 232), semente=12, linhas=(40, 13), sombra=False)
        for y in range(ag.y + 10, ag.bottom - 8, 14):                         # espiral
            pygame.draw.ellipse(ui, P.ESC, (ag.centerx - 10, y, 20, 9))
            pygame.draw.ellipse(ui, (190, 190, 200), (ag.centerx - 9, y + 1, 18, 7), 2)
        for i in range(len(PROVAS)):                                          # abas coloridas
            r = pygame.Rect(dir_.right - 2, dir_.y + 40 + i * 40, 14, 30)
            pygame.draw.rect(ui, self.CORES[i % 5], r, border_top_right_radius=4, border_bottom_right_radius=4)
            pygame.draw.rect(ui, P.ESC, r, 1, border_top_right_radius=4, border_bottom_right_radius=4)
        texto(ui, "NOVEMBRO", (esq.x + 14, esq.y + 10), TINTA, 23, contorno=None)
        texto(ui, "semana de provas", (esq.right - 12, esq.y + 18), P.MARGEM, 11, contorno=None, media=True,
              ancora="topright")
        for i, prova in enumerate(PROVAS):
            self._compromisso(ui, i, prova, esq)
        self._anotacoes(ui, dir_)

    def _compromisso(self, ui, i, prova, esq):
        r = self.linha(i)
        sel = i == self.indice
        cor = self.CORES[i % 5]
        dia_txt = self.DIAS[i % 5].split()
        dia = pygame.Rect(esq.x + 10, r.y, 42, 38)
        pygame.draw.rect(ui, cor, dia, border_radius=3)
        texto(ui, dia_txt[0], (dia.centerx, dia.y + 4), P.BRANCO, 11, contorno=None, ancora="midtop")
        texto(ui, dia_txt[1], (dia.centerx, dia.y + 17), P.BRANCO, 23, contorno=None, ancora="midtop")
        texto(ui, f"{i + 1}ª PROVA", (esq.x + 60, r.y), (60, 60, 90), 11, contorno=None)
        largura = esq.w - 140
        materia = quebrar(prova.ROTULO.replace(" -> ", " e "), fonte(11), largura)[:3]
        if sel:
            prog = ease_out(janela(self.tempo, self._t_foco, 0.35))
            marca = pygame.Surface((int((largura + 4) * prog) + 1, 13 * len(materia) + 1), pygame.SRCALPHA)
            marca.fill((*cor, 90))
            ui.blit(marca, (esq.x + 58, r.y + 12))
        for j, linha in enumerate(materia):
            texto(ui, linha, (esq.x + 60, r.y + 13 + j * 13), (30, 40, 100), 11, contorno=None)
        chefe = self.chefe_da(prova)
        if chefe is not None:
            y = r.y + 15 + len(materia) * 13
            for j, linha in enumerate(quebrar(chefe.NOME, fonte(11, True), largura)[:2]):
                texto(ui, linha, (esq.x + 60, y + j * 12), (120, 120, 140), 11, contorno=None, media=True)
        pasta = getattr(chefe, "PASTA_SPRITE", None) if chefe else None
        pol = self._polaroide(pasta, 58, 68, animado=sel, cinza=not sel)
        ang = (-6, 4, -3, 5, -4)[i % 5] if not sel else 0
        s = pygame.transform.rotate(pol, ang)
        cx, cy = esq.right - 36, r.y + 34 - (6 if sel else 0)
        if sel:
            sombra = pygame.Surface(s.get_size(), pygame.SRCALPHA)
            sombra.fill((0, 0, 0, 60))
            ui.blit(sombra, sombra.get_rect(center=(cx + 4, cy + 6)))
        ui.blit(s, s.get_rect(center=(cx, cy)))
        fita(ui, (cx, cy - 34), ang + 6)

    def _anotacoes(self, ui, dir_):
        prova = PROVAS[self.indice]
        chefe = self.chefe_da(prova)
        troca = ease_out(janela(self.tempo, self._t_foco, 0.3))
        texto(ui, "anotações", (dir_.x + 14, dir_.y + 10), TINTA, 23, contorno=None)
        y = dir_.y + 44
        titulo = quebrar(f"{self.indice + 1}ª prova: {prova.ROTULO.replace(' -> ', ' e ')}", fonte(11), dir_.w - 34)[:2]
        for j, linha in enumerate(titulo):
            texto(ui, linha, (dir_.x + 14, y + j * 13), P.MARGEM, 11, contorno=None, alfa=int(255 * troca))
        y += 13 * (len(titulo) - 1)
        materias = [m.NOME for m in getattr(chefe, "MATERIAS", ())]
        for j, nome in enumerate(materias):
            linha = quebrar(f"{j + 1}ª fase: {nome}", fonte(11, True), dir_.w - 40)[0]
            texto(ui, linha, (dir_.x + 22, y + 26 + j * 13), (40, 40, 80), 11, contorno=None, media=True)
        if len(materias) > 1:
            texto(ui, "- vida extra quando a matéria troca", (dir_.x + 22, y + 26 + len(materias) * 13), (90, 90, 110),
                  11, contorno=None, media=True)
        for i, (tecla, nome, ligado) in enumerate((("C", "começar direto no chefe", self.direto_no_chefe),
                                                   ("I", "aluno imortal", self.imortal))):
            c = self.caixa_marcar(i)
            caixa = pygame.Rect(c.x, c.y, 11, 11)
            pygame.draw.rect(ui, TINTA, caixa, 1)
            if ligado:
                caneta(ui, [(c.x + 2, c.y + 6), (c.x + 5, c.y + 9), (c.x + 12, c.y - 1)], (40, 140, 60), 2)
            texto(ui, f"[{tecla}] {nome}", (c.x + 18, c.y), TINTA, 11, contorno=None, media=True)
        texto(ui, "Treino não entra no ranking.", (dir_.x + 14, dir_.y + 196), (120, 110, 100), 11, contorno=None,
              media=True)
        pygame.draw.circle(ui, (160, 110, 70), (dir_.right - 50, dir_.bottom - 50), 22, 3)       # mancha de café
        pygame.draw.circle(ui, (190, 140, 100), (dir_.right - 50, dir_.bottom - 50), 17, 1)
        pygame.draw.line(ui, (30, 30, 50), (dir_.x + 30, dir_.bottom - 24), (dir_.x + 150, dir_.bottom - 40), 5)
        pygame.draw.line(ui, (60, 110, 200), (dir_.x + 30, dir_.bottom - 24), (dir_.x + 110, dir_.bottom - 35), 5)
        pygame.draw.polygon(ui, (220, 200, 160), [(dir_.x + 150, dir_.bottom - 40), (dir_.x + 160, dir_.bottom - 43),
                                                  (dir_.x + 152, dir_.bottom - 36)])
        texto(ui, "Enter: enfrentar", (dir_.x + 14, dir_.bottom - 20), (40, 140, 60), 11, contorno=None)
