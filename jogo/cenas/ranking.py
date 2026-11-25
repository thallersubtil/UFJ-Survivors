"""Ranking: pódio com os três primeiros e a lista dos outros (opção A aprovada)."""
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR
from jogo.jogador.classes import CLASSES
from jogo.nucleo.recursos import Recursos
from jogo.ui.materiais import fundo_desfocado
from jogo.ui.pixel import A, L, CamadaPixel, Paleta as P, ease_back, ease_out, janela, moldura, quadros, texto

PODIO = ((L // 2, 70, P.OURO), (L // 2 - 110, 50, (200, 200, 220)), (L // 2 + 110, 36, (210, 140, 80)))


def _pontos(valor):
    return f"{valor:,}".replace(",", ".")


class CenaRanking(Cena):
    def __init__(self, app, destaque=None):
        super().__init__(app)
        self.destaque = destaque
        self.tempo = 0.0
        self.camada = CamadaPixel()

    def _voltar(self):
        from jogo.cenas.titulo import CenaTitulo
        self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and (evento.key == pygame.K_ESCAPE or evento.key in TECLAS_CONFIRMAR):
            self._voltar()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._voltar()

    def atualizar(self, dt):
        self.tempo += dt

    @staticmethod
    def pasta_do_heroi(nome):
        for classe in CLASSES:
            if classe.NOME == nome and classe.PASTA_SPRITE:
                return classe.PASTA_SPRITE
        return "aluno2"

    def _e_destaque(self, registro):
        return self.destaque is not None and registro == self.destaque

    def _podio(self, ui, registros):
        for pos, (x, h, cor) in enumerate(PODIO):
            k = ease_back(janela(self.tempo, 0.2 + pos * 0.15, 0.4), 1.5)
            hh = max(1, int(h * k))
            degrau = pygame.Rect(x - 50, 176 - hh, 100, hh)
            pygame.draw.rect(ui, P.ESC, degrau.inflate(2, 2))
            pygame.draw.rect(ui, cor, degrau)
            texto(ui, str(pos + 1), (x, degrau.y + 4), P.ESC, 23, contorno=None, ancora="midtop")
            if pos >= len(registros):
                texto(ui, "vago", (x, 180), P.CINZA, 11, ancora="midtop")
                continue
            r = registros[pos]
            pasta = self.pasta_do_heroi(r.heroi)
            if (Recursos.pasta / "sprites" / pasta / "parado-4.png").exists():
                quadro = quadros(pasta, altura=60)[int(self.tempo * 6 + pos) % 4]
                ui.blit(quadro, quadro.get_rect(midbottom=(x, degrau.y)))
            cor_nome = P.OURO if self._e_destaque(r) else P.BRANCO
            texto(ui, r.nome, (x, 180), cor_nome, 11, ancora="midtop")
            texto(ui, _pontos(int(r.pontos * ease_out(janela(self.tempo, 0.5, 0.8)))), (x, 192), P.OURO, 11,
                  ancora="midtop")
            if r.venceu:
                texto(ui, "APROVADO", (x, 204), P.VERDE, 11, ancora="midtop")

    def _lista(self, ui, registros):
        p = pygame.Rect(120, 220, 400, 124)
        moldura(ui, p, fundo=P.NAVY, raio=4, alfa=240)
        resto = registros[3:]
        if not registros:
            texto(ui, "Ninguém jogou ainda. Seja o primeiro!", p.center, P.BRANCO, 11, ancora="center")
            return
        if not resto:
            texto(ui, "Só três nomes até agora.", p.center, P.CINZA, 11, ancora="center")
            return
        altura = min(30, (p.h - 12) // len(resto))
        for i, r in enumerate(resto):
            ki = janela(self.tempo, 0.8 + i * 0.08, 0.3)
            if ki <= 0:
                continue
            y = p.y + 8 + i * altura
            if self._e_destaque(r):
                pygame.draw.rect(ui, P.SELECAO, (p.x + 6, y - 2, p.w - 12, altura - 2), border_radius=3)
            minutos, segundos = divmod(int(r.tempo), 60)
            texto(ui, f"{i + 4}º", (p.x + 16, y), P.CINZA, 11)
            texto(ui, r.nome, (p.x + 50, y), P.BRANCO, 11)
            texto(ui, r.heroi, (p.x + 160, y), P.CINZA, 11, contorno=None, media=True)
            texto(ui, f"{minutos:02d}:{segundos:02d}", (p.x + 262, y), P.CINZA, 11, contorno=None, media=True)
            texto(ui, _pontos(r.pontos), (p.right - 16, y), P.OURO if not r.venceu else P.VERDE, 11, ancora="topright")

    def desenhar(self, tela):
        fundo_desfocado(tela, "cenario/titulo_fundo.png", escuro=170, desfoque=False)
        ui = self.camada.limpar()
        texto(ui, "RANKING", (L // 2, 6), P.OURO, 23, ancora="midtop")
        registros = self.app.ranking.registros
        self._podio(ui, registros)
        self._lista(ui, registros)
        texto(ui, "Enter ou clique: voltar", (L // 2, A - 14), P.CINZA, 11, ancora="midtop")
        self.camada.apresentar(tela)
