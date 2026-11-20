"""Escolha de classe: a carteirinha de estudante, que vira ao trocar de classe (opção B aprovada)."""
import math

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR
from jogo.jogador.classes import CLASSES
from jogo.opcoes import OpcoesDePartida
from jogo.ui.materiais import fundo_desfocado
from jogo.ui.pixel import (A, ESCALA, L, CamadaPixel, Paleta as P, barra, ease_back, ease_out, fonte, icone, janela,
                           moldura, no_quadrado, onda, quebrar, texto)


class CenaSelecao(Cena):
    LARGURA_CARTAO, ALTURA_CARTAO = 420, 250
    CENTRO_CARTAO = (L // 2, 172)
    DURACAO_GIRO = 0.35
    VIDA_MAXIMA_BARRA, VELOCIDADE_MAXIMA_BARRA = 130, 240

    def __init__(self, app, opcoes=None):
        super().__init__(app)
        self.opcoes = opcoes or OpcoesDePartida()
        self.indice = 0
        self.tempo = 0.0
        self.camada = CamadaPixel()
        self._anterior = 0
        self._t_troca = -10.0
        self.exemplos = [classe((0, 0)) for classe in CLASSES]
        for exemplo in self.exemplos:            # o aluno personalizado, caracterizado para cada classe
            if self.opcoes.aparencia is not None:
                exemplo.vestir(self.opcoes.aparencia)

    # ------------------------------------------------------------ regras
    def escolher(self, i):
        i %= len(CLASSES)
        if i != self.indice:
            self._anterior, self.indice, self._t_troca = self.indice, i, self.tempo

    def _comecar(self):
        from jogo.cenas.partida import CenaPartida
        self.app.trocar(CenaPartida(self.app, CLASSES[self.indice], self.opcoes))

    def _voltar(self):
        from jogo.cenas.personalizacao import CenaPersonalizacao
        self.app.trocar(CenaPersonalizacao(self.app, self.opcoes))

    def aba(self, i):
        r = pygame.Rect(0, 0, 76, 20)
        r.center = (L // 2 + (i - (len(CLASSES) - 1) / 2) * 82, A - 32)
        return r

    @property
    def cartoes(self):
        """Área da carteirinha na tela (para o mouse)."""
        r = pygame.Rect(0, 0, self.LARGURA_CARTAO * ESCALA, self.ALTURA_CARTAO * ESCALA)
        r.center = (self.CENTRO_CARTAO[0] * ESCALA, self.CENTRO_CARTAO[1] * ESCALA)
        return [r]

    # ------------------------------------------------------------ entrada
    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_LEFT, pygame.K_a):
                self.escolher(self.indice - 1)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.escolher(self.indice + 1)
            elif evento.key in TECLAS_CONFIRMAR:
                self._comecar()
            elif evento.key == pygame.K_ESCAPE:
                self._voltar()
        elif evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            pos = CamadaPixel.para_camada(evento.pos)
            clique = evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
            for i in range(len(CLASSES)):
                if self.aba(i).collidepoint(pos):
                    if clique:
                        self.escolher(i)
                    return
            if clique and self.cartoes[0].collidepoint(evento.pos):
                self._comecar()

    def atualizar(self, dt):
        self.tempo += dt

    # ------------------------------------------------------------ desenho
    def _foto(self, heroi, altura):
        animacoes = heroi.animador.animacoes
        animacao = animacoes.get("parado") or next(iter(animacoes.values()))
        quadro = animacao.quadros[int(self.tempo * 6) % len(animacao.quadros)]
        caixa = quadro.get_bounding_rect()
        if caixa.w and caixa.h:
            quadro = quadro.subsurface(caixa)
        return no_quadrado(quadro, altura)

    def _info(self, s, r, heroi):
        tinta, fraco = (40, 50, 110), (100, 100, 130)
        texto(s, heroi.NOME.upper(), (r.x + 12, r.y + 8), P.MARGEM, 23, contorno=None)
        texto(s, heroi.DESCRICAO, (r.x + 12, r.y + 36), fraco, 11, contorno=None, media=True)
        for i, (nome, valor, maximo, cor) in enumerate((("Vida", heroi.VIDA, self.VIDA_MAXIMA_BARRA, P.VERM),
                                                        ("Velocidade", heroi.VELOCIDADE, self.VELOCIDADE_MAXIMA_BARRA,
                                                         P.AZUL))):
            y = r.y + 54 + i * 14
            texto(s, nome, (r.x + 12, y), fraco, 11, contorno=None, media=True)
            barra(s, (r.x + 80, y + 2, r.w - 120, 8), valor / maximo, cor)
            texto(s, str(round(valor)), (r.right - 12, y), tinta, 11, contorno=None, ancora="topright")
        arma, passiva, especial = heroi.armas[0], heroi.passiva, heroi.especial
        blocos = (("ARMA", arma.NOME, arma.DESCRICAO, arma.ICONE), ("PASSIVA", passiva.NOME, passiva.DESCRICAO, None),
                  ("ESPECIAL", especial.NOME, especial.DESCRICAO, especial.ICONE))
        for i, (tipo, nome, descricao, ic) in enumerate(blocos):
            y = r.y + 88 + i * 44
            caixa = pygame.Rect(r.x + 12, y, 34, 34)
            moldura(s, caixa, fundo=(22, 26, 52), borda=(150, 160, 220), raio=2, brilho=False)
            if ic:
                img = icone(ic, 26)
                s.blit(img, img.get_rect(center=caixa.center))
            else:
                texto(s, "P", caixa.center, P.OURO, 23, contorno=None, ancora="center")
            texto(s, tipo, (r.x + 54, y - 1), fraco, 11, contorno=None)
            texto(s, nome, (r.x + 54 + fonte(11).size(tipo)[0] + 8, y - 1), tinta, 11, contorno=None)
            for j, linha in enumerate(quebrar(descricao, fonte(11, True), r.w - 70)[:2]):
                texto(s, linha, (r.x + 54, y + 12 + j * 11), fraco, 11, contorno=None, media=True)

    def _carteirinha(self, i):
        heroi = self.exemplos[i]
        w, h = self.LARGURA_CARTAO, self.ALTURA_CARTAO
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, P.ESC, (0, 0, w, h), border_radius=10)
        pygame.draw.rect(s, P.PAPEL, (2, 2, w - 4, h - 4), border_radius=9)
        pygame.draw.rect(s, P.VERDE_UFJ, (2, 2, w - 4, 34), border_top_left_radius=9, border_top_right_radius=9)
        texto(s, "UFJ  ·  CARTEIRINHA DE ESTUDANTE", (14, 10), P.PAPEL, 11, contorno=None)
        texto(s, "MODO TREINO" if self.opcoes.treino else "2026/2", (w - 14, 10), (255, 230, 150), 11, contorno=None,
              ancora="topright")
        foto = pygame.Rect(14, 46, 92, 116)
        pygame.draw.rect(s, (200, 214, 236), foto)
        retrato = self._foto(heroi, 150)
        s.subsurface(foto).blit(retrato, retrato.get_rect(midtop=(46, 6)))
        pygame.draw.rect(s, (60, 60, 80), foto, 1)
        self._info(s, pygame.Rect(108, 40, w - 114, h - 44), heroi)
        semente = sum(map(ord, heroi.NOME))
        for j in range(30):                                       # código de barras
            pygame.draw.rect(s, P.ESC, (16 + j * 3, 172, 1 if (semente >> (j % 9)) & 1 else 2, 26))
        texto(s, f"matr. 2026{semente * 37 % 9000 + 1000}", (16, 202), (90, 90, 110), 11, contorno=None)
        return s

    def desenhar(self, tela):
        fundo_desfocado(tela, "cenario/titulo_fundo.png", escuro=150, desfoque=False)
        ui = self.camada.limpar()
        texto(ui, "Qual é a sua?", (L // 2, 8), P.PAPEL, 23, ancora="midtop")
        dt = self.tempo - self._t_troca
        girando = dt < self.DURACAO_GIRO
        k = ease_out(dt / self.DURACAO_GIRO) if girando else 1.0
        mostrar = self._anterior if girando and k < 0.5 else self.indice
        largura = abs(math.cos((1 - k) * math.pi)) if girando else 1.0
        cartao = pygame.transform.scale(self._carteirinha(mostrar),
                                        (max(1, int(self.LARGURA_CARTAO * largura)), self.ALTURA_CARTAO))
        cartao = pygame.transform.rotate(cartao, -3 + 2 * onda(self.tempo, 0.3))
        entrada = ease_back(janela(self.tempo, 0.05, 0.5), 1.4)
        cx, cy = self.CENTRO_CARTAO
        cy += int(260 * (1 - entrada)) + int(2 * onda(self.tempo, 0.5))
        sombra = pygame.mask.from_surface(cartao).to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))
        ui.blit(sombra, sombra.get_rect(center=(cx + 6, cy + 8)))
        ui.blit(cartao, cartao.get_rect(center=(cx, cy)))
        for i, heroi in enumerate(self.exemplos):
            r = self.aba(i)
            sel = i == self.indice
            if sel:
                r.y -= 4
            pygame.draw.rect(ui, P.VERDE_UFJ if sel else (30, 40, 34), r, border_radius=3)
            pygame.draw.rect(ui, P.OURO if sel else (90, 110, 96), r, 1, border_radius=3)
            nome = heroi.NOME if fonte(11).size(heroi.NOME)[0] <= r.w - 6 else heroi.NOME.split()[0]
            texto(ui, nome, r.center, P.OURO if sel else P.PAPEL, 11, contorno=None, ancora="center")
        texto(ui, "Setas: escolher    Enter: matricular    Esc: voltar", (L // 2, A - 16), P.CINZA, 11,
              ancora="midtop")
        self.camada.apresentar(tela)
