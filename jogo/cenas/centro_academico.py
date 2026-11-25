"""Centro Acadêmico: o hub entre as partidas. A própria arte do CA, com a loja, o mural de conquistas e o
cassino marcados (cinza = dá para usar, amarelo piscando = selecionado); clique ou Enter entra com zoom."""
import math

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR
from jogo.loja.conquistas import CONQUISTAS
from jogo.nucleo.recursos import Recursos
from jogo.ui.area import AreaInterativa
from jogo.ui.pixel import (A, L, CamadaPixel, Paleta as P, ease_out, fonte, icone, janela, moldura, onda, texto)


class CenaCentroAcademico(Cena):
    FUNDO = "cenario/centro_academico.png"
    # contornos medidos no próprio centro_academico.png (1280x720)
    CONTORNOS = {
        "LOJA": [(3, 3), (267, 3), (267, 424), (387, 424), (387, 717), (3, 717)],
        "CONQUISTAS": [(316, 150), (584, 150), (584, 364), (316, 364)],
        "CASSINO": [(1032, 184), (1279, 184), (1279, 533), (1032, 533)],
    }
    # onde fica a etiqueta de cada área (na camada 640x360), sempre visível e sem tampar o objeto
    ROTULOS = {"LOJA": ("midleft", (200, 226)), "CONQUISTAS": ("midbottom", (225, 70)),
               "CASSINO": ("midbottom", (578, 88))}
    LAMPADAS = ((299, 71), (348, 99), (403, 124), (456, 138), (512, 151), (588, 152), (655, 142), (712, 132),
                (766, 112), (811, 92), (858, 67))
    DURACAO_ZOOM = 0.45
    BOTAO_VOLTAR = pygame.Rect(L - 160, 6, 74, 20)

    def __init__(self, app):
        super().__init__(app)
        self.tempo = 0.0
        self.camada = CamadaPixel()
        progresso = app.progresso
        feitas = len(progresso.conquistas) if progresso is not None else 0
        self.areas = [
            AreaInterativa("LOJA", self.CONTORNOS["LOJA"], "Melhorias, desbloqueios e lanches"),
            AreaInterativa("CONQUISTAS", self.CONTORNOS["CONQUISTAS"], f"{feitas} de {len(CONQUISTAS)} feitas"),
            AreaInterativa("CASSINO", self.CONTORNOS["CASSINO"], "Salgadinho, dado e roleta"),
        ]
        self.acoes = {"LOJA": self._loja, "CONQUISTAS": self._conquistas, "CASSINO": self._cassino}
        self.indice = 0
        self.entrando = None           # (área, tempo do clique) durante o zoom

    # ------------------------------------------------------------ destinos
    def _loja(self):
        from jogo.cenas.loja import CenaLoja
        self.app.trocar(CenaLoja(self.app))

    def _cassino(self):
        from jogo.cenas.cassino import CenaCassino
        self.app.trocar(CenaCassino(self.app))

    def _conquistas(self):
        from jogo.cenas.conquistas import CenaConquistas
        self.app.trocar(CenaConquistas(self.app))

    def _voltar(self):
        from jogo.cenas.titulo import CenaTitulo
        self.app.trocar(CenaTitulo(self.app))

    def entrar(self, i):
        if self.entrando is None:
            self.indice = i
            self.entrando = (self.areas[i], self.tempo)

    # ------------------------------------------------------------ entrada
    def tratar_evento(self, evento):
        if self.entrando is not None:
            return
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self._voltar()
            elif evento.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                self.indice = (self.indice - 1) % len(self.areas)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                self.indice = (self.indice + 1) % len(self.areas)
            elif evento.key in TECLAS_CONFIRMAR:
                self.entrar(self.indice)
        elif evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            clique = evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
            if clique and self.BOTAO_VOLTAR.collidepoint(CamadaPixel.para_camada(evento.pos)):
                self._voltar()
                return
            for i, area in enumerate(self.areas):
                if area.contem(evento.pos):
                    self.indice = i
                    if clique:
                        self.entrar(i)
                    return

    def atualizar(self, dt):
        self.tempo += dt
        if self.entrando is not None and self.tempo - self.entrando[1] >= self.DURACAO_ZOOM:
            area = self.entrando[0]
            self.entrando = None
            self.acoes[area.nome]()

    # ------------------------------------------------------------ desenho
    def _fundo(self, tela):
        if (Recursos.pasta / self.FUNDO).exists():
            fundo = Recursos.imagem(self.FUNDO)
            if fundo.get_size() != tela.get_size():
                fundo = pygame.transform.smoothscale(fundo, tela.get_size())
        else:
            fundo = pygame.Surface(tela.get_size())
            fundo.fill(P.NAVY)
        if self.entrando is None:
            tela.blit(fundo, (0, 0))
            return
        area, inicio = self.entrando
        k = ease_out(janela(self.tempo - inicio, 0, self.DURACAO_ZOOM))
        z = 1 + 1.4 * k
        cx, cy = area.centro
        w, h = tela.get_size()
        img = pygame.transform.smoothscale(fundo, (int(w * z), int(h * z)))
        tela.blit(img, (int(w / 2 - cx * z), int(h / 2 - cy * z)))
        veu = pygame.Surface((w, h), pygame.SRCALPHA)
        veu.fill((10, 8, 20, int(255 * janela(self.tempo - inicio, self.DURACAO_ZOOM * 0.6, self.DURACAO_ZOOM * 0.4))))
        tela.blit(veu, (0, 0))

    def _lampadas(self, tela):
        for i, (x, y) in enumerate(self.LAMPADAS):
            brilho = 0.6 + 0.4 * math.sin(self.tempo * 3 + i * 1.7)
            g = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(g, (255, 220, 140, int(60 * brilho)), (20, 20), 16)
            tela.blit(g, (x - 20, y - 20))

    def _etiqueta(self, ui, area):
        w = max(fonte(11).size(area.nome)[0], fonte(11, True).size(area.descricao)[0]) + 20
        r = pygame.Rect(0, 0, w, 32)
        ancora, pos = self.ROTULOS[area.nome]
        setattr(r, ancora, pos)
        r.y -= int(2 * onda(self.tempo, 2))
        r.x = max(4, min(L - w - 4, r.x))
        moldura(ui, r, fundo=P.NAVY, borda=P.OURO, raio=4, brilho=False)
        texto(ui, area.nome, (r.x + 10, r.y + 4), P.OURO, 11)
        texto(ui, area.descricao, (r.x + 10, r.y + 17), P.CINZA, 11, contorno=None, media=True)

    def desenhar(self, tela):
        self._fundo(tela)
        ui = self.camada.limpar()
        if self.entrando is not None:
            if self.tempo - self.entrando[1] > self.DURACAO_ZOOM * 0.6:
                texto(ui, f"entrando: {self.entrando[0].nome.lower()}...", (L // 2, A // 2), P.OURO, 23,
                      ancora="center")
            self.camada.apresentar(tela)
            return
        self._lampadas(tela)
        for i, area in enumerate(self.areas):
            area.desenhar(tela, i == self.indice, self.tempo)
        self._etiqueta(ui, self.areas[self.indice])
        texto(ui, "CENTRO ACADÊMICO", (L // 2, 4), P.OURO, 23, ancora="midtop")
        moldura(ui, self.BOTAO_VOLTAR, fundo=P.NAVY, borda=(200, 200, 210), raio=3, brilho=False)
        texto(ui, "< VOLTAR", self.BOTAO_VOLTAR.center, P.BRANCO, 11, contorno=None, ancora="center")
        moedas = self.app.progresso.moedas if self.app.progresso is not None else 0
        ui.blit(icone("icones/moeda.png", 14), (L - 66, 9))
        texto(ui, str(moedas), (L - 48, 9), P.OURO, 11)
        texto(ui, "Mouse ou setas: escolher    Clique ou Enter: entrar    Esc: voltar", (L // 2, A - 14), P.BRANCO,
              11, ancora="midtop")
        self.camada.apresentar(tela)
