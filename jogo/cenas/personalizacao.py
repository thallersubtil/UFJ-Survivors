"""Montar o aluno: cadastro do calouro na secretaria, com webcam e carteirinha impressa (opção N aprovada).

Vem antes da escolha de classe. Cada troca de cor se espalha pelo aluno a partir da parte trocada; Enter tira a
foto, a impressora solta a carteirinha e a escolha de classe abre.
"""
import math
import random

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_ENTER
from jogo.jogador.aparencia import CORES, OPCOES, Aparencia
from jogo.jogador.classes import Programador
from jogo.nucleo.recursos import Recursos
from jogo.opcoes import OpcoesDePartida
from jogo.ui.materiais import madeira, papel
from jogo.ui.pixel import A, L, CamadaPixel, Paleta as P, ease_out, janela, no_quadrado, texto

FOTO_AZUL = (200, 214, 236)


class CenaPersonalizacao(Cena):
    LINHAS = (("genero", "Gênero"), ("pele", "Pele"), ("cabelo", "Cabelo"), ("moletom", "Moletom"),
              ("calca", "Calça"))
    ALTURA_PARTE = {"genero": 0.45, "pele": 0.32, "cabelo": 0.14, "moletom": 0.55, "calca": 0.8}
    CLASSE_DA_PREVIA = Programador     # o aluno "base" mostrado enquanto personaliza
    DURACAO_TROCA = 0.45
    DURACAO_FOTO = 1.1                 # flash + carteirinha saindo da impressora

    MONITOR = pygame.Rect(30, 18, 420, 236)

    def __init__(self, app, opcoes=None):
        super().__init__(app)
        self.opcoes = opcoes or OpcoesDePartida()
        anterior = getattr(app, "aparencia", None)
        self.aparencia = Aparencia(*anterior.chave()) if anterior is not None else Aparencia()
        self.linha = 0
        self.tempo = 0.0
        self.camada = CamadaPixel()
        self.previa = self.CLASSE_DA_PREVIA((0, 0))
        self.previa.vestir(self.aparencia)
        self._antes = None             # quadro do aluno antes da última troca (para a cor se espalhar)
        self._t_troca = -10.0
        self._parte_trocada = "genero"
        self.foto_tirada_em = None

    # ------------------------------------------------------------ regras
    def _vestir_de_novo(self, parte):
        self._antes = self._quadro_aluno()
        self._t_troca, self._parte_trocada = self.tempo, parte
        self.previa.vestir(Aparencia(*self.aparencia.chave()))

    def _mudar(self, passo):
        parte = self.LINHAS[self.linha][0]
        self.aparencia.trocar(parte, passo)
        self._vestir_de_novo(parte)

    def _sortear(self):
        for parte in CORES:          # sorteia as cores; o gênero fica como está
            setattr(self.aparencia, parte, random.choice([n for n, _ in OPCOES[parte]]))
        self._vestir_de_novo("moletom")

    def _restaurar(self):
        """Volta todas as cores para as originais do desenho (o gênero fica)."""
        self.aparencia.restaurar_cores()
        self._vestir_de_novo("moletom")

    def tirar_foto(self):
        if self.foto_tirada_em is None:
            self.foto_tirada_em = self.tempo
            Recursos.tocar("nivel", 0.3)

    def _comecar(self):
        from jogo.cenas.selecao import CenaSelecao
        escolhida = Aparencia(*self.aparencia.chave())
        self.app.aparencia = escolhida
        self.app.trocar(CenaSelecao(self.app, self.opcoes.com_aparencia(escolhida)))

    def _voltar(self):
        if self.opcoes.treino:
            from jogo.cenas.treino import CenaTreino
            self.app.trocar(CenaTreino(self.app))
        else:
            from jogo.cenas.titulo import CenaTitulo
            self.app.trocar(CenaTitulo(self.app))

    # ------------------------------------------------------------ posições na camada
    @property
    def _tela_monitor(self):
        return self.MONITOR.inflate(-24, -24)

    @property
    def _webcam(self):
        t = self._tela_monitor
        return pygame.Rect(t.x + 8, t.y + 24, 150, 180)

    def campo(self, i):
        cam = self._webcam
        return pygame.Rect(cam.right + 76, cam.y + 15 + i * 26, 150, 18)

    @property
    def botao_foto(self):
        cam = self._webcam
        return pygame.Rect(cam.right + 12, cam.bottom - 22, 214, 22)

    # ------------------------------------------------------------ entrada
    def tratar_evento(self, evento):
        if self.foto_tirada_em is not None:
            return
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
            elif evento.key in (pygame.K_p, pygame.K_BACKSPACE):
                self._restaurar()
            elif evento.key in TECLAS_ENTER:
                self.tirar_foto()
            elif evento.key == pygame.K_ESCAPE:
                self._voltar()
        elif evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            pos = CamadaPixel.para_camada(evento.pos)
            clique = evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
            for i in range(len(self.LINHAS)):
                r = self.campo(i).inflate(80, 6).move(-40, 0)
                if r.collidepoint(pos):
                    self.linha = i
                    if clique:
                        self._mudar(-1 if pos[0] < self.campo(i).centerx else 1)
                    return
            if clique and self.botao_foto.collidepoint(pos):
                self.tirar_foto()

    def atualizar(self, dt):
        self.tempo += dt
        self.previa.animador.tocar("parado")
        self.previa.animador.atualizar(dt)
        if self.foto_tirada_em is not None and self.tempo - self.foto_tirada_em >= self.DURACAO_FOTO:
            self._comecar()

    # ------------------------------------------------------------ desenho
    def _quadro_aluno(self, altura=250):
        quadro = self.previa.animador.quadro_atual
        caixa = quadro.get_bounding_rect()
        if caixa.w and caixa.h:
            quadro = quadro.subsurface(caixa)
        return no_quadrado(quadro, altura)

    def _aluno_na_webcam(self):
        """O aluno atual; logo depois de uma troca, a cor nova se espalha em círculo a partir da parte trocada."""
        novo = self._quadro_aluno()
        dt = self.tempo - self._t_troca
        if self._antes is None or dt >= self.DURACAO_TROCA or self._antes.get_size() != novo.get_size():
            return novo, None
        w, h = novo.get_size()
        centro = (w // 2, int(h * self.ALTURA_PARTE[self._parte_trocada]))
        raio = int(math.hypot(w, h) * ease_out(dt / self.DURACAO_TROCA))
        mascara = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(mascara, (255, 255, 255, 255), centro, raio)
        parte = novo.copy()
        parte.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        img = self._antes.copy()
        img.blit(parte, (0, 0))
        return img, (centro, raio)

    def _sala(self, ui):
        pygame.draw.rect(ui, (176, 196, 170), (0, 0, L, 270))
        for y in range(0, 270, 30):
            pygame.draw.line(ui, (160, 182, 156), (0, y), (L, y))
        pygame.draw.rect(ui, (120, 140, 116), (0, 200, L, 6))
        madeira(ui, pygame.Rect(0, 262, L, 98), (128, 86, 52), tabuas=10, semente=4)
        pygame.draw.line(ui, P.ESC, (0, 262), (L, 262), 2)
        papel(ui, pygame.Rect(470, 14, 150, 22), P.PAPEL, semente=2)
        texto(ui, "SECRETARIA ACADÊMICA", (545, 19), (40, 60, 40), 11, contorno=None, ancora="midtop")
        painel = pygame.Rect(470, 42, 150, 44)
        pygame.draw.rect(ui, (20, 16, 20), painel, border_radius=4)
        pygame.draw.rect(ui, P.ESC, painel, 2, border_radius=4)
        texto(ui, "SENHA", (painel.x + 8, painel.y + 6), (200, 200, 200), 11, contorno=None)
        chamando = 0.4 <= self.tempo < 1.2 and int(self.tempo * 6) % 2 == 0
        texto(ui, "041" if self.tempo < 0.4 else "042", (painel.x + 70, painel.y + 9),
              (120, 30, 30) if chamando else (255, 70, 60), 23, contorno=None)
        if 0.4 <= self.tempo < 1.0:
            texto(ui, "DING!", (painel.right - 2, painel.bottom + 4), P.OURO, 11, ancora="topright")
        # caneca com vapor e o papel da senha
        caneca = pygame.Rect(40, 288, 44, 46)
        pygame.draw.rect(ui, (230, 230, 240), caneca, border_radius=4)
        pygame.draw.circle(ui, (230, 230, 240), (caneca.right + 4, caneca.centery), 10, 4)
        pygame.draw.rect(ui, P.ESC, caneca, 2, border_radius=4)
        pygame.draw.ellipse(ui, (90, 50, 30), (caneca.x + 3, caneca.y + 2, caneca.w - 6, 8))
        texto(ui, "UFJ", (caneca.centerx, caneca.y + 18), P.VERDE_UFJ, 11, contorno=None, ancora="midtop")
        for j in range(2):
            ys = caneca.y - 6 - int((self.tempo * 20 + j * 10) % 20)
            x = caneca.x + 14 + j * 14
            pygame.draw.line(ui, (240, 240, 250), (x + int(2 * math.sin(self.tempo * 4 + j)), ys), (x, ys - 6), 2)
        papel(ui, pygame.Rect(150, 284, 130, 60), P.PAPEL2, semente=8)
        texto(ui, "Senha 042", (160, 292), (60, 60, 90), 11, contorno=None)
        texto(ui, "MODO TREINO" if self.opcoes.treino else "CALOURO", (160, 318), P.MARGEM, 11, contorno=None)

    def _monitor(self, ui):
        mon = self.MONITOR
        pygame.draw.rect(ui, (214, 208, 190), mon, border_radius=8)
        pygame.draw.rect(ui, P.ESC, mon, 2, border_radius=8)
        pygame.draw.rect(ui, (180, 174, 156), (mon.centerx - 30, mon.bottom, 60, 10))
        pygame.draw.rect(ui, (160, 154, 136), (mon.centerx - 60, mon.bottom + 8, 120, 6))
        tela_m = self._tela_monitor
        pygame.draw.rect(ui, (30, 50, 110), tela_m)
        pygame.draw.rect(ui, (60, 90, 170), (tela_m.x, tela_m.y, tela_m.w, 16))
        texto(ui, "SIGAA  ·  Cadastro de calouro  ·  foto da carteirinha", (tela_m.x + 6, tela_m.y + 2), P.BRANCO, 11,
              contorno=None, media=True)
        cam = self._webcam
        s = pygame.Surface(cam.size)
        s.fill(FOTO_AZUL)
        img, onda_tinta = self._aluno_na_webcam()
        r = img.get_rect(midtop=(cam.w // 2, 8))
        s.blit(img, r)
        if onda_tinta and onda_tinta[1] > 2:
            (cx, cy), raio = onda_tinta
            pygame.draw.circle(s, P.BRANCO, (r.x + cx, r.y + cy), raio, 2)
        ui.blit(s, cam)
        pygame.draw.rect(ui, P.BRANCO, cam, 1)
        pygame.draw.circle(ui, P.VERM if int(self.tempo * 2) % 2 else (100, 20, 20), (cam.x + 10, cam.y + 10), 3)
        texto(ui, "AO VIVO", (cam.x + 16, cam.y + 4), P.BRANCO, 11, contorno=None, media=True)
        guia = pygame.Rect(0, 0, 70, 90)
        guia.center = (cam.centerx, cam.y + 70)
        for canto, (dx, dy) in ((guia.topleft, (1, 1)), (guia.topright, (-1, 1)), (guia.bottomleft, (1, -1)),
                                (guia.bottomright, (-1, -1))):
            pygame.draw.line(ui, P.BRANCO, canto, (canto[0] + 12 * dx, canto[1]))
            pygame.draw.line(ui, P.BRANCO, canto, (canto[0], canto[1] + 12 * dy))
        # campos do cadastro
        x = cam.right + 12
        texto(ui, "Nome: Calouro(a) 2026/2", (x, cam.y - 4), P.CINZA, 11, contorno=None, media=True)
        for i, (parte, rotulo) in enumerate(self.LINHAS):
            c = self.campo(i)
            sel = i == self.linha
            texto(ui, rotulo, (x, c.y + 3), P.OURO if sel else P.BRANCO, 11)
            pygame.draw.rect(ui, P.BRANCO if sel else (220, 224, 236), c)
            pygame.draw.rect(ui, P.OURO if sel else (120, 130, 160), c, 1)
            cor = self.aparencia.cor(parte) if parte != "genero" else None
            dx = 4
            if cor is not None:
                pygame.draw.rect(ui, cor, (c.x + 4, c.y + 4, 10, 10))
                pygame.draw.rect(ui, P.ESC, (c.x + 4, c.y + 4, 10, 10), 1)
                dx = 20
            texto(ui, self.aparencia.escolha(parte), (c.x + dx, c.y + 3), (30, 30, 60), 11, contorno=None, media=True)
            texto(ui, "< >", (c.right - 4, c.y + 3), (90, 100, 140) if not sel else P.MARGEM, 11, contorno=None,
                  ancora="topright")
        b = self.botao_foto
        apertado = self.foto_tirada_em is not None
        pygame.draw.rect(ui, (30, 90, 45) if apertado else (40, 120, 60), b, border_radius=3)
        pygame.draw.rect(ui, P.OURO, b, 1, border_radius=3)
        texto(ui, "TIRAR FOTO  (Enter)", b.center, P.BRANCO, 11, contorno=None, ancora="center")

    def _impressora(self, ui):
        imp = pygame.Rect(470, 200, 150, 50)
        foto_t = None if self.foto_tirada_em is None else self.tempo - self.foto_tirada_em
        if foto_t is not None and foto_t >= 0.1:
            k = ease_out(janela(foto_t, 0.1, 0.5))
            c = pygame.Rect(0, 0, 130, 82)
            c.midbottom = (imp.centerx, imp.y + 94 - int(100 * k))
            papel(ui, c, P.PAPEL, semente=5)
            pygame.draw.rect(ui, P.VERDE_UFJ, (c.x, c.y, c.w, 12))
            texto(ui, "UFJ · ESTUDANTE", (c.x + 4, c.y + 1), P.PAPEL, 11, contorno=None, media=True)
            foto = pygame.Surface((40, 52))
            foto.fill(FOTO_AZUL)
            mini = self._quadro_aluno(90)
            foto.blit(mini, mini.get_rect(midtop=(20, 2)))
            ui.blit(foto, (c.x + 6, c.y + 16))
            for j in range(3):
                pygame.draw.line(ui, (140, 140, 160), (c.x + 54, c.y + 24 + j * 12), (c.right - 8, c.y + 24 + j * 12))
        pygame.draw.rect(ui, (70, 72, 84), imp, border_radius=4)
        pygame.draw.rect(ui, P.ESC, imp, 2, border_radius=4)
        pygame.draw.rect(ui, (20, 20, 26), (imp.x + 20, imp.y + 10, imp.w - 40, 5))
        pygame.draw.circle(ui, P.VERDE if foto_t is not None else (40, 70, 40), (imp.right - 12, imp.bottom - 12), 3)
        if foto_t is not None and foto_t < 0.25:
            flash = pygame.Surface((L, A), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(240 * (1 - foto_t / 0.25))))
            ui.blit(flash, (0, 0))

    def desenhar(self, tela):
        tela.fill(P.ESC)
        ui = self.camada.limpar()
        self._sala(ui)
        self._monitor(ui)
        self._impressora(ui)
        texto(ui, "Cima/baixo: campo   Lados: opção   R: sortear   P: padrão   Enter: foto   Esc: voltar",
              (L - 8, A - 16), P.BRANCO, 11, ancora="topright")
        self.camada.apresentar(tela)
