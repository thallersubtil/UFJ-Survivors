"""Subiu de nível: folhas de prova presas com clipe numa mesa de estudo (opção E aprovada)."""
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_ENTER, escurecer
from jogo.config import CURA_AO_PULAR
from jogo.nucleo.recursos import Recursos
from jogo.progressao import Progressao
from jogo.ui.materiais import carimbo
from jogo.ui.pixel import (A, ESCALA, L, CamadaPixel, Paleta as P, ease_back, ease_out, fonte, icone, janela,
                           moldura, quebrar, texto)

COR_ROTULO = {"colab": (150, 100, 20), "nova": (40, 140, 60), "melhoria": P.AZUL2, "lanche": (40, 140, 60),
              "atributo": (40, 140, 60)}


class CenaNivel(Cena):
    LARGURA_CARTA, ALTURA_CARTA = 152, 204
    ESPACO = 172
    DURACAO_ESCOLHA = 0.5          # tempo do carimbo "ESCOLHIDO" antes de voltar à partida

    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.camada = CamadaPixel()
        self.tempo = 0.0
        self.indice = 0
        self.escolhida = None       # índice carimbado (a escolha já foi aplicada)
        self._fechando = None
        self._sortear()
        Recursos.tocar("nivel", 0.5)

    # ------------------------------------------------------------ regras
    def _sortear(self):
        self.opcoes = Progressao.gerar_opcoes(self.jogo.jogador, self.jogo.rng)
        self.indice = 0
        self.tempo_cartas = self.tempo          # as folhas caem de novo a cada sorteio

    def centro_carta(self, i):
        return L // 2 + (i - (len(self.opcoes) - 1) / 2) * self.ESPACO, 190

    @property
    def cartoes(self):
        """Retângulos das folhas na tela (coordenadas da janela, para o mouse)."""
        caixas = []
        for i in range(len(self.opcoes)):
            r = pygame.Rect(0, 0, self.LARGURA_CARTA * ESCALA, self.ALTURA_CARTA * ESCALA)
            x, y = self.centro_carta(i)
            r.center = (int(x * ESCALA), int(y * ESCALA))
            caixas.append(r)
        return caixas

    def escolher(self, i):
        if self.escolhida is not None:
            return
        self.opcoes[i].aplicar(self.jogo.jogador, self.jogo)
        self.jogo.niveis_pendentes = max(0, self.jogo.niveis_pendentes - 1)
        self.escolhida, self.indice = i, i
        self._fechando = self.DURACAO_ESCOLHA

    def sortear_de_novo(self):
        if self.jogo.sorteios_restantes > 0:
            self.jogo.sorteios_restantes -= 1
            self._sortear()

    def banir(self):
        """Tira a carta destacada das cartas pelo resto da partida e sorteia de novo (sem gastar sorteio)."""
        opcao = self.opcoes[self.indice]
        if self.jogo.banimentos_restantes <= 0 or opcao.origem is None:
            return
        self.jogo.banimentos_restantes -= 1
        self.jogo.jogador.banir(opcao.origem)
        self._sortear()

    def pular(self):
        self.jogo.jogador.curar(CURA_AO_PULAR)
        self.jogo.niveis_pendentes = max(0, self.jogo.niveis_pendentes - 1)
        self.app.desempilhar()

    # ------------------------------------------------------------ entrada
    def tratar_evento(self, evento):
        if self.escolhida is not None:
            return
        if evento.type == pygame.KEYDOWN:
            numeros = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
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
            elif evento.key == pygame.K_b:
                self.banir()
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
        self.tempo += dt
        if self._fechando is not None:
            self._fechando -= dt
            if self._fechando <= 0:
                self._fechando = None
                self.app.desempilhar()

    # ------------------------------------------------------------ desenho
    def _folha(self, opcao, numero, selecionada):
        w, h = self.LARGURA_CARTA, self.ALTURA_CARTA
        c = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(c, (0, 0, 0, 70), (3, 4, w - 3, h - 4))
        pygame.draw.rect(c, P.PAPEL, (0, 0, w - 3, h - 4))
        for y in range(40, h - 6, 11):
            pygame.draw.line(c, P.LINHA, (0, y), (w - 4, y))
        pygame.draw.line(c, P.MARGEM, (14, 0), (14, h - 5))
        pygame.draw.rect(c, (140, 120, 90), (0, 0, w - 3, h - 4), 1)
        texto(c, f"{numero}.  Nome: ______", (18, 6), (110, 110, 130), 11, contorno=None, media=True)
        pygame.draw.circle(c, P.MARGEM, (w - 26, 20), 15, 2)
        texto(c, "+1", (w - 26, 20), P.MARGEM, 11, contorno=None, ancora="center")
        img = icone(opcao.icone, 46)
        c.blit(img, img.get_rect(center=(w // 2, 64)))
        titulo = quebrar(opcao.titulo, fonte(23), w - 16)
        tam = 23 if len(titulo) == 1 else 11
        texto(c, opcao.titulo if tam == 23 else titulo[0], (w // 2, 92), (30, 40, 100), tam, contorno=None,
              ancora="midtop")
        if tam == 11 and len(titulo) > 1:
            texto(c, " ".join(titulo[1:]), (w // 2, 104), (30, 40, 100), 11, contorno=None, ancora="midtop")
        if opcao.rotulo:
            texto(c, opcao.rotulo, (w // 2, 118), COR_ROTULO.get(opcao.tipo, P.AZUL2), 11, contorno=None,
                  ancora="midtop")
        for j, linha in enumerate(quebrar(opcao.descricao, fonte(11, True), w - 30)[:5]):
            texto(c, linha, (20, 136 + j * 12), (60, 60, 90), 11, contorno=None, media=True)
        if selecionada:
            pygame.draw.rect(c, P.OURO, (0, 0, w - 3, h - 4), 3)
        return c

    def _mesa(self, ui):
        km = ease_out(janela(self.tempo, 0, 0.35))
        mesa = pygame.Rect(20, 60 + int(300 * (1 - km)), L - 40, 270)
        pygame.draw.rect(ui, (0, 0, 0, 90), mesa.move(4, 6), border_radius=8)
        pygame.draw.rect(ui, (120, 78, 48), mesa, border_radius=8)
        for y in range(mesa.y + 8, mesa.bottom, 14):
            pygame.draw.line(ui, (104, 66, 40), (mesa.x + 6, y), (mesa.right - 6, y + 3))
        pygame.draw.rect(ui, (70, 44, 28), mesa, 3, border_radius=8)
        pygame.draw.polygon(ui, (250, 200, 60), [(mesa.right - 120, mesa.bottom - 22), (mesa.right - 40, mesa.bottom - 30),
                                                  (mesa.right - 38, mesa.bottom - 24), (mesa.right - 118, mesa.bottom - 16)])
        pygame.draw.rect(ui, (240, 140, 160), (mesa.x + 26, mesa.bottom - 30, 22, 12))

    def _rodape(self, ui):
        itens = (("1-3", "escolher"), ("R", f"sortear ({self.jogo.sorteios_restantes})"),
                 ("B", f"banir ({self.jogo.banimentos_restantes})"), ("P", f"pular +{CURA_AO_PULAR} vida"))
        x = 120
        for tecla, desc in itens:
            w = fonte(11).size(tecla)[0] + 8
            moldura(ui, (x, A - 22, w, 14), fundo=P.NAVY2, borda=P.CINZA, raio=2, brilho=False)
            texto(ui, tecla, (x + w // 2, A - 15), P.BRANCO, 11, contorno=None, ancora="center")
            r = texto(ui, desc, (x + w + 4, A - 21), P.BRANCO, 11)
            x = r.right + 18

    def desenhar(self, tela):
        escurecer(tela, int(175 * ease_out(janela(self.tempo, 0, 0.3))))
        ui = self.camada.limpar()
        self._mesa(ui)
        titulo = "Subiu de nível!"
        texto(ui, titulo[:max(1, int(len(titulo) * janela(self.tempo, 0.2, 0.5)))], (L // 2, 14), P.PAPEL, 23,
              ancora="midtop")
        t_cartas = self.tempo - self.tempo_cartas
        saida = 0.0 if self._fechando is None else ease_out(1 - self._fechando / self.DURACAO_ESCOLHA)
        for i, opcao in enumerate(self.opcoes):
            kd = ease_out(janela(t_cartas, 0.15 + i * 0.12, 0.35))
            sel = i == self.indice
            x, y = self.centro_carta(i)
            y += int(-300 * (1 - kd))
            ang = (-3, 2, -2, 3)[i % 4]
            if sel:
                y, ang = y - 10, 0
            if self.escolhida is not None:
                if i == self.escolhida:
                    y -= 20 * saida
                else:
                    x += (x - L // 2) * 2 * saida
            img = pygame.transform.rotate(self._folha(opcao, i + 1, sel), ang)
            ui.blit(img, img.get_rect(center=(int(x), int(y))))
            pygame.draw.rect(ui, (180, 180, 196), (int(x) - 8, int(y) - 108, 16, 18), 2, border_radius=4)   # clipe
            if i == self.escolhida:
                k = ease_back(janela(saida, 0, 0.5), 2.5)
                marca = carimbo("ESCOLHIDO", P.MARGEM, -12, escala=2.2 - 1.2 * k, tam=11)
                ui.blit(marca, marca.get_rect(center=(int(x), int(y) + 20)))
        self._rodape(ui)
        self.camada.apresentar(tela)
