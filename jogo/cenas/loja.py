"""Loja do Centro Acadêmico: a própria estante do CA, onde cada objeto pintado é uma melhoria (opção A aprovada).

Lanches e desbloqueios ficam numa prateleira com os ícones. Cinza = dá para comprar ou ver; amarelo piscando =
escolhido; o preço fica numa plaquinha fixa no canto de cada moldura.
"""
import math
from dataclasses import dataclass
from typing import Callable

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR
from jogo.loja.cassino import SegredosDoCassino
from jogo.loja.lanches import LANCHES
from jogo.loja.melhorias import MELHORIAS
from jogo.nucleo.recursos import Recursos
from jogo.progressao import Progressao
from jogo.ui.area import AreaInterativa
from jogo.ui.materiais import fundo_desfocado, madeira
from jogo.ui.pixel import A, L, CamadaPixel, Paleta as P, fonte, icone, janela, moldura, onda, quebrar, texto


@dataclass
class LinhaDaLoja:
    nome: str
    descricao: str
    icone: str
    situacao: str            # "nível 2/5", "ARMA", "ITEM"
    preco: object            # int, ou None quando não dá mais para comprar
    comprar: Callable
    nivel: int = 0
    nivel_maximo: int = 0


class CenaLoja(Cena):
    ABAS = ("MELHORIAS", "DESBLOQUEIOS", "LANCHES")
    FUNDO = "cenario/centro_academico.png"
    # melhoria (CHAVE) -> objeto pintado na estante do centro_academico.png (retângulo exato, em 1280x720)
    OBJETOS = {
        "velocidade": (8, 62, 214, 80), "dano": (6, 156, 220, 88), "recarga": (8, 280, 102, 62),
        "vida": (144, 285, 76, 56), "moedas": (240, 346, 72, 94), "rolamento": (8, 385, 112, 79),
        "critico": (126, 419, 98, 30), "experiencia": (1, 516, 188, 78), "coleta": (243, 470, 89, 77),
    }
    RECORTE_ESTANTE = pygame.Rect(0, 0, 392, 626)
    ZOOM, ORIGEM = 1.15, (40, 0)
    PAINEL = pygame.Rect(300, 70, 230, 250)
    OUTROS_DESBLOQUEIOS = (SegredosDoCassino,)       # o que se compra na mesma aba e não é arma nem item

    def __init__(self, app):
        super().__init__(app)
        self.aba = 0
        self.indice = 0
        self.tempo = 0.0
        self.camada = CamadaPixel()
        self.mensagem = ""
        self._tempo_mensagem = 0.0
        self._compra = None          # (preço, tempo) para a animação das moedas

    # ------------------------------------------------------------ dados
    @staticmethod
    def desbloqueaveis():
        """Armas e itens que custam moedas para aparecer nas cartas, e os outros desbloqueios (segredos do cassino)."""
        return [c for c in Progressao.ARMAS + Progressao.ITENS if c.PRECO_DESBLOQUEIO > 0] + \
            list(CenaLoja.OUTROS_DESBLOQUEIOS)

    def linhas(self):
        progresso = self.app.progresso
        if self.aba == 0:
            return [LinhaDaLoja(m.NOME, m.DESCRICAO, m.ICONE, f"nível {progresso.nivel_de(m)}/{m.NIVEL_MAXIMO}",
                                progresso.preco_da_proxima(m), lambda m=m: progresso.comprar_melhoria(m),
                                progresso.nivel_de(m), m.NIVEL_MAXIMO)
                    for m in MELHORIAS]
        if self.aba == 2:
            guardado = progresso.lanche_reservado
            return [LinhaDaLoja(c.NOME, c.DESCRICAO, c.ICONE, "GUARDADO" if c is guardado else "vale 1 partida",
                                None if c is guardado else c.PRECO, lambda c=c: progresso.comprar_lanche(c))
                    for c in LANCHES]
        linhas = []
        for classe in self.desbloqueaveis():
            tipo = "ARMA" if classe in Progressao.ARMAS else "ITEM" if classe in Progressao.ITENS else classe.TIPO
            preco = None if progresso.desbloqueado(classe) else classe.PRECO_DESBLOQUEIO
            linhas.append(LinhaDaLoja(classe.NOME, classe.DESCRICAO, classe.ICONE, tipo, preco,
                                      lambda c=classe: progresso.desbloquear(c)))
        return linhas

    def areas(self):
        """Uma AreaInterativa (em coordenadas da tela) para cada linha da aba atual."""
        if self.aba == 0:
            ox, oy = self.ORIGEM
            areas = []
            for m in MELHORIAS:
                r = pygame.Rect(self.OBJETOS[m.CHAVE])
                tela = pygame.Rect(ox + int(r.x * self.ZOOM), oy + int(r.y * self.ZOOM), int(r.w * self.ZOOM),
                                   int(r.h * self.ZOOM))
                areas.append(AreaInterativa.retangulo(m.NOME, tela.inflate(8, 8)))
            return areas
        quantidade = len(self.linhas())
        return [AreaInterativa.retangulo(str(i), self._vaga_prateleira(i, quantidade)) for i in range(quantidade)]

    def _vaga_prateleira(self, i, quantidade):
        """Lugar de um item na prateleira genérica (lanches e desbloqueios), 3 por tábua."""
        coluna, tabua = i % 3, i // 3
        return pygame.Rect(70 + coluna * 136, 90 + tabua * 190, 112, 112)

    # ------------------------------------------------------------ regras
    def _avisar(self, texto_aviso):
        self.mensagem = texto_aviso
        self._tempo_mensagem = 2.0

    def _comprar(self):
        linha = self.linhas()[self.indice]
        if linha.preco is None:
            self._avisar(("Já está no máximo.", "Já foi comprado.", "Já está guardado para a próxima partida.")[self.aba])
        elif not self.app.progresso.pode_pagar(linha.preco):
            self._avisar("Moedas insuficientes.")
        elif linha.comprar():
            Recursos.tocar("compra", 0.5)
            self._compra = (linha.preco, self.tempo)
            self._avisar(f"Comprado: {linha.nome}!")
        else:
            self._avisar("Você já tem um lanche guardado: ele vale na próxima partida.")

    def _trocar_aba(self, nova=None):
        self.aba = (self.aba + 1) % len(self.ABAS) if nova is None else nova
        self.indice = 0

    def _voltar(self):
        from jogo.cenas.centro_academico import CenaCentroAcademico
        self.app.trocar(CenaCentroAcademico(self.app))

    # ------------------------------------------------------------ entrada
    def aba_rect(self, i):
        return pygame.Rect(290 + i * 110, 38, 104, 18)

    @property
    def botao_comprar(self):
        r = self.PAINEL
        return pygame.Rect(r.x + 14, r.bottom - 40, r.w - 28, 28)

    def tratar_evento(self, evento):
        quantidade = len(self.linhas())
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_w):
                self.indice = (self.indice - 1) % quantidade
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.indice = (self.indice + 1) % quantidade
            elif evento.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                self._trocar_aba()
            elif evento.key in TECLAS_CONFIRMAR:
                self._comprar()
            elif evento.key == pygame.K_ESCAPE:
                self._voltar()
        elif evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            clique = evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
            pos = CamadaPixel.para_camada(evento.pos)
            if clique:
                for i in range(len(self.ABAS)):
                    if self.aba_rect(i).collidepoint(pos):
                        if i != self.aba:
                            self._trocar_aba(i)
                        return
                if self.botao_comprar.collidepoint(pos):
                    self._comprar()
                    return
            for i, area in enumerate(self.areas()):
                if area.contem(evento.pos):
                    if clique and i == self.indice:
                        self._comprar()
                    self.indice = i
                    return

    def atualizar(self, dt):
        self.tempo += dt
        self._tempo_mensagem = max(0.0, self._tempo_mensagem - dt)
        if self._tempo_mensagem <= 0:
            self.mensagem = ""

    # ------------------------------------------------------------ desenho
    def _estante(self, tela):
        if not (Recursos.pasta / self.FUNDO).exists():
            return None
        fundo = Recursos.imagem(self.FUNDO)
        estante = fundo.subsurface(self.RECORTE_ESTANTE)
        estante = pygame.transform.scale(estante, (int(estante.get_width() * self.ZOOM),
                                                   int(estante.get_height() * self.ZOOM)))
        tela.blit(estante, self.ORIGEM)
        pygame.draw.rect(tela, P.ESC, (*self.ORIGEM, *estante.get_size()), 3)
        return fundo

    def _prateleira(self, tela):
        """Armário de madeira para lanches e desbloqueios: fundo escuro, três tábuas e os ícones em cima delas."""
        caixa = pygame.Rect(self.ORIGEM[0], 0, 451, tela.get_height())
        madeira(tela, caixa, (66, 40, 26), tabuas=44, semente=8)
        sombra = pygame.Surface(caixa.size, pygame.SRCALPHA)
        for x in range(0, caixa.w, 4):                    # sombra das laterais
            alfa = int(90 * max(0.0, 1 - min(x, caixa.w - x) / 60))
            pygame.draw.line(sombra, (0, 0, 0, alfa), (x, 0), (x, caixa.h), 4)
        tela.blit(sombra, caixa)
        for tabua in range(3):
            y = 90 + tabua * 190 + 116
            pygame.draw.rect(tela, (0, 0, 0, 0), (caixa.x, y + 20, caixa.w, 10))
            pygame.draw.rect(tela, (168, 112, 64), (caixa.x + 4, y, caixa.w - 8, 12))
            pygame.draw.line(tela, (200, 146, 92), (caixa.x + 4, y), (caixa.right - 5, y), 2)
            pygame.draw.rect(tela, (84, 52, 30), (caixa.x + 4, y + 12, caixa.w - 8, 8))
            luz = pygame.Surface((caixa.w - 8, 40), pygame.SRCALPHA)
            for k in range(40):
                pygame.draw.line(luz, (0, 0, 0, 70 - k * 70 // 40), (0, k), (caixa.w - 8, k))
            tela.blit(luz, (caixa.x + 4, y + 20))
        pygame.draw.rect(tela, (40, 24, 14), caixa, 10)
        pygame.draw.rect(tela, P.ESC, caixa, 3)
        for i, linha in enumerate(self.linhas()):
            vaga = self._vaga_prateleira(i, 0)
            img = icone(linha.icone, 84)
            sombra_item = pygame.Surface((70, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(sombra_item, (0, 0, 0, 90), sombra_item.get_rect())
            tela.blit(sombra_item, sombra_item.get_rect(center=(vaga.centerx, vaga.bottom + 2)))
            tela.blit(img, img.get_rect(midbottom=(vaga.centerx, vaga.bottom + 2 + int(2 * onda(self.tempo + i, 0.4)))))

    def _molduras_e_precos(self, tela, ui):
        linhas = self.linhas()
        for i, (area, linha) in enumerate(zip(self.areas(), linhas)):
            area.desenhar(tela, i == self.indice, self.tempo, largura=2, preencher=True)
            plaquinha = pygame.Rect(0, 0, 34, 13)
            plaquinha.bottomright = ((area.caixa.right - 1) // 2, (area.caixa.bottom - 1) // 2 + 6)
            if linha.preco is None:
                rotulo = ("MÁX", "OK", "GUARD.")[self.aba]
            else:
                rotulo = str(linha.preco)
            plaquinha.w = max(34, fonte(11).size(rotulo)[0] + 8)
            plaquinha.right = (area.caixa.right - 1) // 2
            pygame.draw.rect(ui, (250, 244, 220), plaquinha)
            pygame.draw.rect(ui, P.OURO if i == self.indice else (120, 100, 70), plaquinha, 1)
            pode = linha.preco is None or self.app.progresso.pode_pagar(linha.preco)
            texto(ui, rotulo, plaquinha.center, (170, 60, 30) if pode else (150, 150, 150), 11, contorno=None,
                  ancora="center")

    def _painel(self, ui, fundo):
        linhas = self.linhas()
        linha = linhas[self.indice]
        r = self.PAINEL
        moldura(ui, r, fundo=P.NAVY, raio=5, alfa=245)
        if self.aba == 0 and fundo is not None:
            ret = pygame.Rect(self.OBJETOS[MELHORIAS[self.indice].CHAVE])
            escala = min(110 / ret.w, 60 / ret.h)
            figura = pygame.transform.smoothscale(fundo.subsurface(ret), (int(ret.w * escala), int(ret.h * escala)))
        else:
            figura = icone(linha.icone, 56)
        figura = pygame.transform.scale_by(figura, 1 + 0.05 * onda(self.tempo, 1))
        ui.blit(figura, figura.get_rect(center=(r.centerx, r.y + 46)))
        texto(ui, linha.nome, (r.centerx, r.y + 84), P.BRANCO, 11, ancora="midtop")
        y = r.y + 100
        if linha.nivel_maximo:
            for j in range(linha.nivel_maximo):
                q = pygame.Rect(r.centerx - linha.nivel_maximo * 9 // 2 + j * 9, y, 7, 7)
                cor = P.OURO if j < linha.nivel else (70, 70, 110)
                if j == linha.nivel and int(self.tempo * 4) % 2 == 0:
                    cor = P.BRANCO
                pygame.draw.rect(ui, cor, q)
                pygame.draw.rect(ui, P.ESC, q, 1)
        for j, texto_linha in enumerate(quebrar(linha.descricao, fonte(11, True), r.w - 24)[:3]):
            texto(ui, texto_linha, (r.x + 12, r.y + 118 + j * 12), P.CINZA, 11, contorno=None, media=True)
        texto(ui, linha.situacao[:1].upper() + linha.situacao[1:], (r.x + 12, r.y + 158), P.AZUL, 11)
        b = self.botao_comprar
        if linha.preco is None:
            moldura(ui, b, fundo=(40, 110, 60), borda=P.VERDE, raio=4)
            texto(ui, ("NO MÁXIMO", "JÁ COMPRADO", "GUARDADO")[self.aba], b.center, P.BRANCO, 11, contorno=None,
                  ancora="center")
        else:
            pode = self.app.progresso.pode_pagar(linha.preco)
            moldura(ui, b, fundo=P.SELECAO if pode else (60, 40, 50), borda=P.OURO if pode else P.CINZA, raio=4)
            ui.blit(icone("icones/moeda.png", 12), (b.centerx - 34, b.y + 8))
            texto(ui, f"{linha.preco}  COMPRAR", (b.centerx - 18, b.y + 8), P.OURO if pode else P.CINZA, 11,
                  contorno=None)

    def _moedas(self, ui):
        x, y = L - 66, 9
        ui.blit(icone("icones/moeda.png", 14), (x, y))
        texto(ui, str(self.app.progresso.moedas), (x + 18, y), P.OURO, 11)
        if self._compra is None:
            return
        preco, inicio = self._compra
        k = janela(self.tempo, inicio, 0.6)
        if k >= 1:
            return
        texto(ui, f"-{preco}", (x + 18, y + 14 + int(10 * k)), P.VERM, 11)
        for j in range(10):                               # moedas espirrando do botão
            a = j * math.pi / 5
            d = 20 + 50 * k
            b = self.botao_comprar
            ui.blit(icone("icones/moeda.png", 8), (b.centerx + d * math.cos(a), b.centery + d * math.sin(a)))

    def desenhar(self, tela):
        fundo_desfocado(tela, self.FUNDO, escuro=150)
        ui = self.camada.limpar()
        fundo = self._estante(tela) if self.aba == 0 else None
        if fundo is None:
            self._prateleira(tela)
        self._molduras_e_precos(tela, ui)
        texto(ui, "LOJA DO CA", (290, 8), P.OURO, 23)
        for i, aba in enumerate(self.ABAS):
            r = self.aba_rect(i)
            sel = i == self.aba
            moldura(ui, r, fundo=P.SELECAO if sel else (30, 34, 66), borda=P.OURO if sel else P.CINZA, raio=3,
                    brilho=False)
            texto(ui, aba, r.center, P.OURO if sel else P.CINZA, 11, contorno=None, ancora="center")
        self._painel(ui, fundo)
        self._moedas(ui)
        if self.mensagem:
            texto(ui, self.mensagem, (self.PAINEL.centerx, self.PAINEL.bottom + 8), P.OURO, 11, ancora="midtop")
        texto(ui, "Clique ou Enter: comprar    Tab: aba    Esc: voltar", (290, A - 14), P.BRANCO, 11)
        self.camada.apresentar(tela)
