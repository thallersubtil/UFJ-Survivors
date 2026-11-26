"""Cassino do Centro Acadêmico: apostas com as moedas do jogo.

A tela é um salãozinho: letreiro de lâmpadas, cortinas, o crupiê atrás da mesa e o aparelho do jogo em cima dela
(veja `cassino_mesas.py`). Embaixo ficam as fichas de aposta (a última é o ALL IN, que aposta o saldo inteiro)
e, no canto das abas, o ícone dos Segredos do Cassino: clicando nele (ou com a tecla C) abre por cima do salão a
tabela de prêmios com a chance de cada um, lida de `JogoDeAposta.tabela`, a mesma conta que o sorteio usa. O ícone
fica trancado até o aluno comprar o item "Segredos do Cassino do CA" na loja.
"""
import math
import random
from dataclasses import dataclass

import pygame

from jogo.cenas.cassino_crupie import Crupie
from jogo.cenas.cassino_mesas import mesa_de
from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR
from jogo.loja.cassino import JOGOS_DE_APOSTA, Cassino, SegredosDoCassino
from jogo.nucleo.recursos import Recursos
from jogo.ui.materiais import fundo_desfocado, madeira
from jogo.ui.pixel import (A, L, CamadaPixel, Paleta as P, clarear, ease_back, ease_out, escurecer_cor, fonte, icone,
                           janela, moldura, onda, piscar, quebrar, texto)


@dataclass
class Voadora:
    """Moeda ou ficha que voa de um ponto a outro, em arco."""
    tipo: str
    origem: tuple
    destino: tuple
    inicio: float
    duracao: float
    altura: float
    cor: tuple = P.OURO

    def posicao(self, tempo):
        k = ease_out(janela(tempo, self.inicio, self.duracao))
        x = self.origem[0] + (self.destino[0] - self.origem[0]) * k
        y = self.origem[1] + (self.destino[1] - self.origem[1]) * k - math.sin(math.pi * k) * self.altura
        return int(x), int(y)

    def terminou(self, tempo):
        return tempo >= self.inicio + self.duracao


class CenaCassino(Cena):
    DURACAO_GIRO = 1.6
    TECLA_ALL_IN = pygame.K_t
    TECLA_SEGREDOS = pygame.K_c
    PREMIO_GRANDE = 5                    # multiplicador a partir do qual a festa é maior

    SALAO = pygame.Rect(16, 62, 608, 198)
    BORDA_DA_MESA = 208                  # onde o tampo da mesa começa (o crupiê fica atrás dele)
    PAINEL = pygame.Rect(380, 60, 244, 200)      # a tabela de prêmios, quando aberta (por cima do salão)
    BOTAO_SEGREDOS = pygame.Rect(L - 16 - 28, 39, 28, 21)
    CRUPIE_X = 104                       # centro do crupiê (camada); ele fica atrás da mesa, à esquerda
    BOTAO_VOLTAR = pygame.Rect(8, 8, 74, 20)
    CAIXA_SALDO = pygame.Rect(L - 116, 8, 108, 20)
    BOTAO_JOGAR = pygame.Rect(500, 271, 124, 44)
    LETREIRO = pygame.Rect(196, 4, 248, 32)
    FICHAS_Y = 287
    APOSTA_NA_MESA = (474, 230)
    CORES_DAS_FICHAS = (P.AZUL2, (40, 140, 80), P.ROXO, (214, 110, 40), (50, 46, 66))

    def __init__(self, app, rng=None):
        super().__init__(app)
        self.rng = rng or random.Random()
        self.jogos = [classe() for classe in JOGOS_DE_APOSTA]
        self.mesas = [mesa_de(jogo) for jogo in self.jogos]
        self._crupies = {}               # um crupiê por mesa, criado quando ela aparece
        self.indice_jogo = 0
        self.indice_aposta = 0           # igual a len(APOSTAS): all in
        self.indice_escolha = 0
        self.resultado = None
        self.girando = 0.0
        self.tempo = 0.0
        self.tique = 0                   # conta os estalos do giro (as mesas usam para embaralhar o que mostram)
        self._tique = 0.0
        self._fim_do_giro = None         # quando o último giro parou
        self._saldo_mostrado = float(app.progresso.moedas)
        self._perdeu_tudo = False
        self.voadoras = []
        self.mensagem = ""
        self.tabela_aberta = False       # a tabela de prêmios e chances só aparece quando o aluno consulta
        self._abertura = 0.0             # de 0 (tabela fechada) a 1 (aberta): anima a tabela e afasta a mesa
        self.camada = CamadaPixel()
        self.camada_do_fundo = CamadaPixel()      # a parede: fica atrás do crupiê, que é desenhado em resolução cheia
        self._cenario = None

    # ------------------------------------------------------------ estado
    @property
    def jogo(self):
        return self.jogos[self.indice_jogo]

    @property
    def mesa(self):
        return self.mesas[self.indice_jogo]

    def crupie_de(self, mesa):
        if id(mesa) not in self._crupies:
            self._crupies[id(mesa)] = Crupie(mesa.PASTA_CRUPIE, mesa.FALAS)
        return self._crupies[id(mesa)]

    @property
    def crupie(self):
        return self.crupie_de(self.mesa)

    @property
    def crupies(self):
        return [self.crupie_de(mesa) for mesa in self.mesas]

    @property
    def apostando_tudo(self):
        return self.indice_aposta >= len(self.jogo.APOSTAS)

    @property
    def aposta(self):
        """A aposta escolhida. No all in é o saldo inteiro, então nunca passa do que o aluno tem."""
        if self.apostando_tudo:
            return Cassino.aposta_maxima(self.app.progresso)
        return self.jogo.APOSTAS[self.indice_aposta]

    @property
    def escolha(self):
        return self.jogo.ESCOLHAS[self.indice_escolha % len(self.jogo.ESCOLHAS)]

    @property
    def fracao_do_giro(self):
        """De 0 a 1 enquanto o sorteio roda; None parado."""
        return 1 - self.girando / self.DURACAO_GIRO if self.girando else None

    @property
    def tempo_do_resultado(self):
        """Segundos desde que o sorteio parou; None se ainda não há resultado na mesa."""
        if self.girando or self.resultado is None or self._fim_do_giro is None:
            return None
        return self.tempo - self._fim_do_giro

    @property
    def moedas_na_tela(self):
        """Durante o giro, o prêmio ainda não aparece no saldo."""
        moedas = self.app.progresso.moedas
        return moedas - self.resultado.premio if self.girando and self.resultado else moedas

    @property
    def segredos_liberados(self):
        """A tabela de prêmios e chances só pode ser consultada depois de comprada na loja."""
        return self.app.progresso.desbloqueado(SegredosDoCassino)

    @property
    def deslocamento(self):
        """Quanto o aparelho anda para a esquerda para a tabela aberta não ficar em cima dele."""
        return -int(112 * ease_out(self._abertura))

    @property
    def origem_do_premio(self):
        x, y = self.mesa.origem_do_premio()
        return x + self.deslocamento, y

    @property
    def aposta_na_tela(self):
        """Durante o giro vale a aposta que está na mesa (no all in, o saldo já foi descontado)."""
        return self.resultado.aposta if self.girando and self.resultado else self.aposta

    @property
    def linhas_da_tabela(self):
        """O que a tabela de prêmios mostra: (nome, chance, multiplicador, moedas com a aposta atual)."""
        aposta = self.aposta_na_tela
        return [(linha.rotulo, linha.chance_formatada, linha.multiplicador_formatado,
                 self.jogo.premio_de(aposta, linha.multiplicador)) for linha in self.jogo.tabela(self.escolha)]

    # ------------------------------------------------------------ ações
    def _jogar(self):
        if self.girando:
            return
        aposta = self.aposta
        if aposta <= 0 or not self.app.progresso.pode_pagar(aposta):
            self.mensagem = "Moedas insuficientes."
            self.resultado = None
            Recursos.tocar("dano", 0.15)
            return
        origem = self._centro_da_ficha(self.indice_aposta)
        cor = P.VERM if self.apostando_tudo else self.CORES_DAS_FICHAS[self.indice_aposta % len(self.CORES_DAS_FICHAS)]
        fichas = self._fichas_da_aposta(aposta)
        self.resultado = Cassino.apostar(self.app.progresso, self.jogo, aposta, self.escolha, self.rng)
        self.girando = self.DURACAO_GIRO
        self._perdeu_tudo = self.app.progresso.moedas == 0
        self.mensagem = ""
        self.voadoras = [Voadora("ficha", origem, (self.APOSTA_NA_MESA[0], self.APOSTA_NA_MESA[1] - 3 * k),
                                 self.tempo + 0.06 * k, 0.35, 46, cor) for k in range(fichas)]
        Recursos.tocar("moeda", 0.4)

    def _fichas_da_aposta(self, aposta):
        return 6 if self.apostando_tudo else 1 + min(4, sum(aposta >= valor for valor in self.jogo.APOSTAS))

    def _selecionar_jogo(self, i):
        if self.girando or i == self.indice_jogo:
            return
        tudo = self.apostando_tudo
        self.indice_jogo = i % len(self.jogos)
        self.indice_aposta = len(self.jogo.APOSTAS) if tudo else min(self.indice_aposta, len(self.jogo.APOSTAS) - 1)
        self.indice_escolha = 0
        self.resultado = None
        self.voadoras = []
        self.mensagem = ""
        self.crupie.entrar(self.tempo)

    def _trocar_jogo(self):
        self._selecionar_jogo((self.indice_jogo + 1) % len(self.jogos))

    def _selecionar_aposta(self, i):
        if not self.girando:
            self.indice_aposta = max(0, min(len(self.jogo.APOSTAS), i))
            self.mensagem = ""

    def _all_in(self):
        self._selecionar_aposta(len(self.jogo.APOSTAS))

    def _consultar_segredos(self):
        """Abre ou fecha a tabela de prêmios e chances. Sem o item da loja, só avisa."""
        if self.segredos_liberados:
            self.tabela_aberta = not self.tabela_aberta
            self.mensagem = ""
            Recursos.tocar("coleta", 0.3)
        else:
            self.tabela_aberta = False
            self.mensagem = "Trancado: compre os Segredos do Cassino na loja."
            Recursos.tocar("dano", 0.15)

    def _voltar(self):
        from jogo.cenas.centro_academico import CenaCentroAcademico
        self.app.trocar(CenaCentroAcademico(self.app))

    # ------------------------------------------------------------ áreas clicáveis (camada)
    def _centro_da_ficha(self, i):
        if i >= len(self.jogo.APOSTAS):
            return 46 + len(self.jogo.APOSTAS) * 38 + 14, self.FICHAS_Y
        return 40 + i * 38, self.FICHAS_Y

    def caixa_da_ficha(self, i):
        raio = 21 if i >= len(self.jogo.APOSTAS) else 16
        caixa = pygame.Rect(0, 0, 2 * raio, 2 * raio)
        caixa.center = self._centro_da_ficha(i)
        return caixa

    def caixa_da_aba(self, i):
        return pygame.Rect(self.SALAO.x + i * 128, 40, 124, 20)

    def caixa_do_palpite(self, i):
        if len(self.jogo.ESCOLHAS) <= 2:
            return pygame.Rect(306, 269 + i * 21, 112, 19)
        return pygame.Rect(298 + (i % 2) * 100, 269 + (i // 2) * 21, 98, 19)      # quatro palpites: duas colunas

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._clicar(CamadaPixel.para_camada(evento.pos))
            return
        if evento.type != pygame.KEYDOWN:
            return
        if evento.key == pygame.K_ESCAPE:
            self._voltar()
        elif evento.key == pygame.K_TAB:
            self._trocar_jogo()
        elif evento.key in (pygame.K_LEFT, pygame.K_a):
            self._selecionar_aposta(self.indice_aposta - 1)
        elif evento.key in (pygame.K_RIGHT, pygame.K_d):
            self._selecionar_aposta(self.indice_aposta + 1)
        elif evento.key == self.TECLA_ALL_IN:
            self._all_in()
        elif evento.key == self.TECLA_SEGREDOS:
            self._consultar_segredos()
        elif evento.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s) and not self.girando:
            self.indice_escolha = (self.indice_escolha + 1) % len(self.jogo.ESCOLHAS)
        elif evento.key in TECLAS_CONFIRMAR:
            self._jogar()

    def _clicar(self, pos):
        if self.BOTAO_VOLTAR.collidepoint(pos):
            self._voltar()
        elif self.BOTAO_SEGREDOS.collidepoint(pos):
            self._consultar_segredos()
        elif self.tabela_aberta and self.PAINEL.collidepoint(pos):          # clicar na tabela aberta fecha
            self._consultar_segredos()
        elif self.BOTAO_JOGAR.collidepoint(pos) or self.SALAO.collidepoint(pos):
            self._jogar()
        else:
            for i in range(len(self.jogo.APOSTAS) + 1):
                if self.caixa_da_ficha(i).collidepoint(pos):
                    return self._selecionar_aposta(i)
            for i in range(len(self.jogos)):
                if self.caixa_da_aba(i).collidepoint(pos):
                    return self._selecionar_jogo(i)
            if len(self.jogo.ESCOLHAS) > 1 and not self.girando:
                for i in range(len(self.jogo.ESCOLHAS)):
                    if self.caixa_do_palpite(i).collidepoint(pos):
                        self.indice_escolha = i

    # ------------------------------------------------------------ atualização
    def atualizar(self, dt):
        self.tempo += dt
        alvo_da_tabela = 1.0 if self.tabela_aberta and self.segredos_liberados else 0.0
        passo = dt * 5
        self._abertura = max(alvo_da_tabela, self._abertura - passo) if self._abertura > alvo_da_tabela \
            else min(alvo_da_tabela, self._abertura + passo)
        alvo = self.moedas_na_tela
        self._saldo_mostrado += (alvo - self._saldo_mostrado) * min(1.0, dt * 7)
        if abs(alvo - self._saldo_mostrado) < 0.6:
            self._saldo_mostrado = float(alvo)
        self.voadoras = [v for v in self.voadoras if v.tipo == "ficha" or not v.terminou(self.tempo)]
        self.crupie.atualizar(self)
        if not self.girando:
            return
        self.girando = max(0.0, self.girando - dt)
        self._tique -= dt
        if self._tique <= 0:
            self._tique = 0.05 + 0.12 * (self.fracao_do_giro or 1.0)        # os estalos vão espaçando
            self.tique += 1
            Recursos.tocar("giro", 0.2)
        if not self.girando:
            self._ao_parar()
            self.crupie.atualizar(self)

    def _ao_parar(self):
        self._fim_do_giro = self.tempo
        resultado = self.resultado
        Recursos.tocar("premio" if resultado.ganhou else "dano", 0.5 if resultado.ganhou else 0.2)
        if not resultado.premio:
            crupie = (self.CRUPIE_X, self.BORDA_DA_MESA + 6)                   # a casa recolhe as fichas
            self.voadoras = [Voadora("ficha", v.destino, crupie, self.tempo + 0.25 + 0.04 * k, 0.45, 10, v.cor)
                             for k, v in enumerate(self.voadoras)]
            return
        moedas = min(44, 5 + int(resultado.multiplicador * 5)) if resultado.ganhou else 4
        origem = self.origem_do_premio
        sorte = random.Random(self.tique)
        self.voadoras += [Voadora("moeda", (origem[0] + sorte.randint(-26, 26), origem[1] + sorte.randint(-8, 8)),
                                  self.CAIXA_SALDO.center, self.tempo + 0.03 * k, 0.55 + sorte.random() * 0.3,
                                  sorte.randint(20, 70)) for k in range(moedas)]

    # ------------------------------------------------------------ desenho: salão
    def _montar_cenario(self):
        """Parede, cortinas e mesa: não mudam, então são pintadas uma vez só."""
        s = pygame.Surface(self.SALAO.size, pygame.SRCALPHA)
        w, h = s.get_size()
        topo_da_mesa = self.BORDA_DA_MESA - self.SALAO.y
        s.fill((52, 18, 44))
        for y in range(-12, topo_da_mesa, 24):                              # papel de parede de losangos
            for x in range(-12 + (y // 24 % 2) * 12, w, 24):
                pygame.draw.polygon(s, (64, 24, 54), [(x + 12, y), (x + 24, y + 12), (x + 12, y + 24), (x, y + 12)], 1)
                if 0 <= x + 12 < w and 0 <= y + 12 < h:
                    s.set_at((x + 12, y + 12), P.OURO2)
        pygame.draw.rect(s, (36, 12, 32), (0, topo_da_mesa - 22, w, 22))    # rodapé
        pygame.draw.line(s, P.OURO2, (0, topo_da_mesa - 22), (w, topo_da_mesa - 22))
        for lado in (0, 1):                                                 # cortinas de veludo
            for k in range(5):
                x = k * 7 if lado == 0 else w - 7 - k * 7
                altura = topo_da_mesa - 8 - k * 5
                pygame.draw.rect(s, P.VERM2 if k % 2 == 0 else (130, 20, 40), (x, 0, 7, altura))
                dobra = x + (6 if lado == 0 else 0)
                pygame.draw.line(s, (96, 12, 30), (dobra, 0), (dobra, altura - 1))
            pygame.draw.rect(s, P.OURO2, (0 if lado == 0 else w - 35, 0, 35, 5))
            pygame.draw.rect(s, P.OURO, (0 if lado == 0 else w - 35, 0, 35, 2))
        for cx, naipe in ((150, "ouros"), (w - 150, "copas")):               # quadros e arandelas na parede
            quadro = pygame.Rect(cx - 19, 22, 38, 30)
            pygame.draw.rect(s, P.ESC, quadro.inflate(2, 2))
            pygame.draw.rect(s, P.OURO2, quadro)
            pygame.draw.rect(s, (28, 12, 30), quadro.inflate(-6, -6))
            if naipe == "ouros":
                pygame.draw.polygon(s, P.VERM, [(cx, 28), (cx + 7, 37), (cx, 46), (cx - 7, 37)])
            else:
                pygame.draw.circle(s, P.VERM, (cx - 3, 34), 4)
                pygame.draw.circle(s, P.VERM, (cx + 3, 34), 4)
                pygame.draw.polygon(s, P.VERM, [(cx - 7, 36), (cx + 7, 36), (cx, 45)])
            for lx in (cx - 44, cx + 44):
                halo = pygame.Surface((44, 44), pygame.SRCALPHA)
                pygame.draw.circle(halo, (255, 210, 110, 34), (22, 22), 22)
                pygame.draw.circle(halo, (255, 220, 140, 50), (22, 22), 12)
                s.blit(halo, (lx - 22, 14))
                pygame.draw.rect(s, P.ESC, (lx - 4, 32, 8, 10))
                pygame.draw.rect(s, P.OURO2, (lx - 3, 38, 6, 3))
                pygame.draw.polygon(s, P.OURO, [(lx - 5, 36), (lx + 5, 36), (lx + 3, 28), (lx - 3, 28)])
        self._parede = s.subsurface((0, 0, w, topo_da_mesa)).copy()
        mesa = pygame.Surface((w, h - topo_da_mesa), pygame.SRCALPHA)       # tampo de feltro com beirada de madeira
        mesa.fill((24, 96, 60))
        sorte = random.Random(11)
        for _ in range(900):
            mesa.set_at((sorte.randrange(w), sorte.randrange(mesa.get_height())), (30, 108, 68))
        pygame.draw.rect(mesa, (18, 76, 48), (0, 0, w, 3))
        pygame.draw.ellipse(mesa, (40, 124, 80), (w // 2 - 200, 6, 400, 62), 1)
        madeira(mesa, pygame.Rect(0, mesa.get_height() - 9, w, 9), tabuas=9)
        pygame.draw.line(mesa, P.ESC, (0, mesa.get_height() - 10), (w, mesa.get_height() - 10))
        for cx, n, cor in ((w - 58, 5, P.AZUL2), (w - 42, 3, P.VERM), (w - 30, 6, (40, 140, 80))):   # pilhas de fichas da casa
            for k in range(n):
                self._ficha_de_lado(mesa, (cx, 30 - k * 3), cor)
        self._tampo = mesa
        self._cenario = True

    @staticmethod
    def _ficha_de_lado(sup, centro, cor):
        x, y = int(centro[0]), int(centro[1])
        pygame.draw.rect(sup, P.ESC, (x - 8, y - 2, 16, 5))
        pygame.draw.rect(sup, cor, (x - 7, y - 1, 14, 3))
        for dx in (-5, -1, 3):
            pygame.draw.rect(sup, P.BRANCO, (x + dx, y - 1, 2, 3))

    def _raios(self, ui, centro, t):
        """Raios dourados girando atrás do aparelho quando o aluno ganha."""
        forca = janela(t, 0, 0.25) * (1 - janela(t, 1.6, 0.8))
        if forca <= 0:
            return
        s = pygame.Surface(self.SALAO.size, pygame.SRCALPHA)
        cx, cy = centro[0] - self.SALAO.x, centro[1] - self.SALAO.y
        for k in range(10):
            a = self.tempo * 0.9 + k * math.pi / 5
            pontos = [(cx, cy), (cx + 260 * math.cos(a), cy + 260 * math.sin(a)),
                      (cx + 260 * math.cos(a + 0.2), cy + 260 * math.sin(a + 0.2))]
            pygame.draw.polygon(s, (255, 220, 110, int(70 * forca)), pontos)
        ui.blit(s, self.SALAO.topleft, (0, 0, self.SALAO.w, self.BORDA_DA_MESA - self.SALAO.y))

    def _parede_do_salao(self, ui):
        """O que fica atrás do crupiê: a parede e os raios de quando o aluno ganha."""
        if self._cenario is None:
            self._montar_cenario()
        t = self.tempo_do_resultado
        ui.blit(self._parede, self.SALAO.topleft)
        if t is not None and self.resultado.ganhou:
            self._raios(ui, self.origem_do_premio, t)

    def _desenhar_crupie(self, tela):
        """O crupiê, direto na tela (ilustração lisa, sem ampliar em blocos), com os pés escondidos pela mesa."""
        recorte = pygame.Rect(self.SALAO.x * 2, self.SALAO.y * 2, self.SALAO.w * 2, (self.BORDA_DA_MESA - self.SALAO.y) * 2 + 8)
        self.crupie.desenhar(tela, self.tempo, (self.CRUPIE_X + self.deslocamento // 4) * 2, self.BORDA_DA_MESA * 2 + 40,
                             recorte)

    def _salao(self, ui):
        """O que fica na frente do crupiê: a mesa, o aparelho, as fichas e o resultado."""
        t = self.tempo_do_resultado
        perdeu = t is not None and not self.resultado.premio
        ui.blit(self._tampo, (self.SALAO.x, self.BORDA_DA_MESA))
        tremor = int(onda(t, 14, 5) * (1 - janela(t, 0, 0.45))) if perdeu else 0
        self.mesa.desenhar_aparelho(ui, self, tremor + self.deslocamento)
        for v in self.voadoras:
            if v.tipo == "ficha" and self.tempo >= v.inicio and not (perdeu and v.terminou(self.tempo)):
                self._ficha_de_lado(ui, v.posicao(self.tempo), v.cor)
        if perdeu and t < 0.9:                                               # o salão escurece num susto vermelho
            veu = pygame.Surface(self.SALAO.size, pygame.SRCALPHA)
            veu.fill((120, 0, 20, int(90 * (1 - t / 0.9))))
            ui.blit(veu, self.SALAO.topleft)
        pygame.draw.rect(ui, P.ESC, self.SALAO.inflate(4, 4), 2, border_radius=3)
        pygame.draw.rect(ui, P.OURO2, self.SALAO.inflate(2, 2), 1, border_radius=2)
        self.crupie.desenhar_fala(ui, self.tempo, (self.CRUPIE_X + self.deslocamento // 4, self.BORDA_DA_MESA + 2))
        self._faixa_do_resultado(ui, t)

    def _faixa_do_resultado(self, ui, t):
        centro = (self.SALAO.centerx + self.deslocamento, self.SALAO.bottom - 14)
        if self.mensagem:
            faixa = pygame.Rect(0, 0, max(200, fonte(11).size(self.mensagem)[0] + 24), 20)
            faixa.center = centro
            moldura(ui, faixa, fundo=P.VERM2, borda=P.VERM, brilho=False)
            texto(ui, self.mensagem, centro, P.BRANCO, 11, ancora="center")
            return
        if t is None:
            return
        resultado = self.resultado
        ganhou, premio = resultado.ganhou, resultado.premio
        entrada = ease_back(janela(t, 0, 0.3))
        frase = resultado.mensagem
        if premio:
            frase += f"  +{premio}" if ganhou else f"  voltou {premio}"
        elif self._perdeu_tudo:
            frase += "  Acabou a mesada."
        largura = fonte(11).size(frase)[0] + 28
        faixa = pygame.Rect(0, 0, largura, 22)
        faixa.center = (centro[0], centro[1] + int(30 * (1 - entrada)))
        if faixa.bottom <= self.SALAO.bottom:
            cor = (30, 110, 60) if ganhou else P.NAVY if premio else (96, 20, 36)
            moldura(ui, faixa, fundo=cor, borda=P.OURO if ganhou else P.CINZA, brilho=False)
            texto(ui, frase, faixa.center, P.OURO if ganhou else P.BRANCO, 11, ancora="center")
        if ganhou and resultado.multiplicador >= self.PREMIO_GRANDE:
            self._placa(ui, "JACKPOT!", t - 0.15, P.VERM2, P.OURO, P.OURO if int(t * 8) % 2 else P.BRANCO)
        elif not premio and self._perdeu_tudo:
            self._placa(ui, "FALIU", t - 0.3, P.ESC, P.VERM, P.VERM)

    def _placa(self, ui, frase, t, fundo, borda, cor):
        """Placa que desce do teto do salão nos resultados grandes."""
        if t <= 0:
            return
        placa = pygame.Rect(0, 0, fonte(23).size(frase)[0] + 28, 30)
        placa.midtop = (self.SALAO.centerx + self.deslocamento, self.SALAO.y - 34 + int(38 * ease_back(janela(t, 0, 0.35))))
        recorte = ui.get_clip()
        ui.set_clip(self.SALAO)
        for x in (placa.x + 12, placa.right - 13):                           # as correntes
            pygame.draw.line(ui, P.OURO2, (x, self.SALAO.y), (x, placa.y), 1)
        moldura(ui, placa, fundo=fundo, borda=borda, raio=4, brilho=False)
        texto(ui, frase, (placa.centerx, placa.centery - 1), cor, 23, ancora="center")
        ui.set_clip(recorte)

    # ------------------------------------------------------------ desenho: letreiro, abas, tabela, fichas
    def _letreiro(self, ui):
        r = self.LETREIRO
        t = self.tempo_do_resultado
        festa = t is not None and t < 2.2 and self.resultado.ganhou
        moldura(ui, r, fundo=(60, 14, 40), borda=P.OURO2, raio=5, brilho=False)
        neon = P.OURO if festa or math.sin(self.tempo * 23) > -0.96 else P.OURO2        # o neon falha de vez em quando
        texto(ui, "CASSINO DO CA", (r.centerx, r.centery - 1), neon, 23, contorno=P.VERM2, ancora="center")
        lampadas = [(x, y) for x in range(r.x + 4, r.right - 2, 10) for y in (r.y, r.bottom - 1)] + \
                   [(x, y) for y in range(r.y + 10, r.bottom - 6, 10) for x in (r.x, r.right - 1)]
        passo = int(self.tempo * (12 if festa else 4))
        for i, (x, y) in enumerate(lampadas):
            acesa = (i + passo) % (2 if festa else 3) == 0
            pygame.draw.circle(ui, P.ESC, (x, y), 3)
            pygame.draw.circle(ui, (P.BRANCO if festa else P.OURO) if acesa else (120, 70, 30), (x, y), 2)

    def _topo(self, ui):
        moldura(ui, self.BOTAO_VOLTAR, fundo=P.NAVY, borda=(200, 200, 210), raio=3, brilho=False)
        texto(ui, "< VOLTAR", self.BOTAO_VOLTAR.center, P.BRANCO, 11, contorno=None, ancora="center")
        self._letreiro(ui)
        t = self.tempo_do_resultado
        subindo = self._saldo_mostrado < self.moedas_na_tela
        caixa = self.CAIXA_SALDO.move(0, -1 if subindo and int(self.tempo * 20) % 2 else 0)
        moldura(ui, caixa, fundo=P.NAVY, borda=P.OURO if subindo else P.OURO2, raio=3, brilho=False)
        ui.blit(icone("icones/moeda.png", 14), (caixa.x + 6, caixa.y + 3))
        texto(ui, str(round(self._saldo_mostrado)), (caixa.right - 8, caixa.y + 4), P.OURO, 11, ancora="topright")
        if t is not None and t < 1.8 and self.resultado.premio:
            k = janela(t, 0.3, 1.5)
            texto(ui, f"+{self.resultado.premio}", (caixa.centerx, caixa.bottom + 2 + int(10 * (1 - ease_out(k)))),
                  P.VERDE if self.resultado.ganhou else P.CINZA, 11, ancora="midtop", alfa=int(255 * (1 - k ** 3)))
        for i, jogo in enumerate(self.jogos):
            atual = i == self.indice_jogo
            aba = self.caixa_da_aba(i).move(0, 0 if atual else 2)
            moldura(ui, aba, fundo=P.SELECAO if atual else P.NAVY, borda=P.OURO if atual else P.CINZA, raio=3,
                    brilho=atual)
            texto(ui, self.mesas[i].titulo, aba.center, P.OURO if atual else P.CINZA, 11, contorno=None, ancora="center",
                  media=not atual)

    def _botao_dos_segredos(self, ui):
        """O ícone que abre a tabela de prêmios e chances; com cadeado enquanto o item não é comprado."""
        r = self.BOTAO_SEGREDOS
        liberado = self.segredos_liberados
        borda = P.OURO if self.tabela_aberta else clarear(P.OURO2, int(50 * piscar(self.tempo, 3))) if liberado else P.CINZA
        moldura(ui, r, fundo=P.SELECAO if self.tabela_aberta else P.NAVY, borda=borda, raio=3, brilho=False)
        figura = icone(SegredosDoCassino.ICONE, 15)
        if not liberado:
            figura = figura.copy()
            figura.fill((90, 90, 110, 255), special_flags=pygame.BLEND_RGBA_MULT)
        ui.blit(figura, figura.get_rect(center=r.center))
        if not liberado:                                                     # cadeadinho no canto
            x, y = r.right - 10, r.bottom - 10
            pygame.draw.rect(ui, P.ESC, (x + 1, y - 4, 6, 6), 1)
            pygame.draw.rect(ui, P.ESC, (x - 1, y, 10, 8))
            pygame.draw.rect(ui, P.VERM, (x, y + 1, 8, 6))

    def _tabela(self, ui):
        """A tabela de prêmios e chances, por cima do salão, só enquanto o aluno a consulta."""
        self._botao_dos_segredos(ui)
        if self._abertura <= 0:
            return
        r = self.PAINEL.move(int((L - self.PAINEL.x) * (1 - ease_out(self._abertura))), 0)     # entra pela direita
        sombra = pygame.Surface((r.w + 8, r.h + 8), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 110), sombra.get_rect(), border_radius=6)
        ui.blit(sombra, (r.x - 2, r.y + 2))
        moldura(ui, r, fundo=P.NAVY, borda=P.OURO, raio=4)
        ui.blit(icone(SegredosDoCassino.ICONE, 14), (r.x + 8, r.y + 5))
        texto(ui, "PRÊMIOS E CHANCES", (r.centerx, r.y + 7), P.OURO, 11, ancora="midtop")
        texto(ui, "C: fechar", (r.right - 10, r.y + 7), P.CINZA, 11, contorno=None, ancora="topright", media=True)
        colunas = (r.x + 10, r.right - 98, r.right - 58, r.right - 10)
        for x, titulo, ancora in ((colunas[0], "prêmio", "topleft"), (colunas[1], "chance", "topright"),
                                  (colunas[2], "paga", "topright"), (colunas[3], "moedas", "topright")):
            texto(ui, titulo, (x, r.y + 22), P.CINZA, 11, contorno=None, ancora=ancora, media=True)
        pygame.draw.line(ui, P.NAVY2, (r.x + 8, r.y + 36), (r.right - 9, r.y + 36))
        t = self.tempo_do_resultado
        linhas = self.jogo.tabela(self.escolha)
        for i, (linha, (_, chance, paga, moedas)) in enumerate(zip(linhas, self.linhas_da_tabela)):
            y = r.y + 40 + i * 17
            caiu = t is not None and self.resultado.rotulo == linha.rotulo
            if caiu and (t > 1.2 or int(t * 8) % 2 == 0):
                cor_faixa = (40, 120, 70) if self.resultado.ganhou else (120, 30, 46)
                pygame.draw.rect(ui, cor_faixa, (r.x + 5, y - 2, r.w - 10, 16), border_radius=2)
            cor = P.BRANCO if linha.multiplicador else P.CINZA
            self.mesa.desenhar_rotulo(ui, linha, (colunas[0], y), cor)
            texto(ui, chance, (colunas[1], y), P.BRANCO if caiu else P.AZUL, 11, contorno=None, ancora="topright")
            texto(ui, paga, (colunas[2], y), P.OURO if linha.multiplicador > 1 else cor, 11, contorno=None,
                  ancora="topright", media=not linha.multiplicador)
            texto(ui, str(moedas), (colunas[3], y), cor, 11, contorno=None, ancora="topright", media=True)
            largura = max(1, round((r.w - 20) * linha.chance))                # barrinha do tamanho da chance
            pygame.draw.line(ui, P.NAVY2, (r.x + 10, y + 13), (r.right - 11, y + 13))
            pygame.draw.line(ui, P.AZUL2, (r.x + 10, y + 13), (r.x + 9 + largura, y + 13))
        retorno = self.jogo.retorno_esperado(self.escolha) * 100
        pe = f"Retorno médio: {retorno:.1f}%  (casa: {100 - retorno:.1f}%)".replace(".", ",")
        pygame.draw.line(ui, P.NAVY2, (r.x + 8, r.bottom - 21), (r.right - 9, r.bottom - 21))
        texto(ui, pe, (r.centerx, r.bottom - 18), P.CINZA, 11, contorno=None, ancora="midtop", media=True)

    def _ficha(self, ui, centro, raio, cor, rotulo, selecionada, apagada):
        cx, cy = centro
        if selecionada:
            cy -= 3 + int(onda(self.tempo, 1.5, 1.5))
            pygame.draw.circle(ui, P.OURO, (cx, cy), raio + 3, 2)
        if apagada:
            cor = escurecer_cor(cor, 70)
        pygame.draw.circle(ui, P.ESC, (cx, cy + 2), raio + 1)
        pygame.draw.circle(ui, P.ESC, (cx, cy), raio + 1)
        pygame.draw.circle(ui, cor, (cx, cy), raio)
        for k in range(8):                                                   # marcas brancas da borda
            a = k * math.pi / 4 + (self.tempo * 1.5 if selecionada else 0)
            pygame.draw.line(ui, P.CINZA if apagada else P.BRANCO,
                             (cx + (raio - 3) * math.cos(a), cy + (raio - 3) * math.sin(a)),
                             (cx + (raio - 1) * math.cos(a), cy + (raio - 1) * math.sin(a)), 2)
        pygame.draw.circle(ui, clarear(cor, 30), (cx, cy), raio - 4)
        pygame.draw.circle(ui, escurecer_cor(cor, 30), (cx, cy), raio - 4, 1)
        texto(ui, rotulo, (cx, cy), P.CINZA if apagada else P.BRANCO, 11, ancora="center")

    def _apostas(self, ui):
        saldo = Cassino.aposta_maxima(self.app.progresso)
        base = pygame.Rect(16, 265, L - 32, 60)
        moldura(ui, base, fundo=(20, 22, 48), borda=P.NAVY2, raio=4, brilho=False)
        for i, valor in enumerate(self.jogo.APOSTAS):
            self._ficha(ui, self._centro_da_ficha(i), 14, self.CORES_DAS_FICHAS[i % len(self.CORES_DAS_FICHAS)],
                        str(valor), i == self.indice_aposta, valor > saldo)
        tudo = self.apostando_tudo
        cx, cy = self._centro_da_ficha(len(self.jogo.APOSTAS))
        if saldo > 0:                                                        # o all in chama atenção: brilho pulsando
            brilho = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(brilho, (255, 80, 80, int(50 + 40 * piscar(self.tempo, 3))), (30, 30),
                               24 + int(onda(self.tempo, 1, 2)))
            ui.blit(brilho, (cx - 30, cy - 30))
        self._ficha(ui, (cx, cy), 19, P.VERM, "ALL IN", tudo, saldo <= 0)
        aposta = self.aposta_na_tela
        resumo = f"ALL IN: {aposta} moedas, tudo ou nada" if tudo else f"Aposta: {aposta} moedas"
        maior = max(linha.multiplicador for linha in self.jogo.tabela(self.escolha))
        if self.segredos_liberados:                                          # sem o caderninho, nada de valores
            resumo += f"    Maior prêmio: {self.jogo.premio_de(aposta, maior)}"
        texto(ui, resumo, (26, 310), P.OURO if tudo else P.BRANCO, 11, contorno=None, media=not tudo)
        if len(self.jogo.ESCOLHAS) > 1:
            for i, escolha in enumerate(self.jogo.ESCOLHAS):
                caixa = self.caixa_do_palpite(i)
                marcada = i == self.indice_escolha % len(self.jogo.ESCOLHAS)
                moldura(ui, caixa, fundo=P.SELECAO if marcada else P.NAVY, borda=P.OURO if marcada else P.CINZA,
                        raio=3, brilho=False)
                cor = self.mesa.cor_da_escolha(escolha)
                if cor is not None:                                          # a cor do palpite no aparelho
                    pygame.draw.rect(ui, P.ESC, (caixa.x + 5, caixa.y + 5, 9, 9))
                    pygame.draw.rect(ui, cor, (caixa.x + 6, caixa.y + 6, 7, 7))
                texto(ui, self.mesa.rotulo_da_escolha(escolha), (caixa.centerx + (5 if cor else 0), caixa.centery),
                      P.OURO if marcada else P.CINZA, 11, contorno=None, ancora="center", media=not marcada)
        botao = self.BOTAO_JOGAR
        if self.girando:
            moldura(ui, botao, fundo=P.NAVY2, borda=P.CINZA, raio=5, brilho=False)
            texto(ui, "GIRANDO" + "." * (1 + int(self.tempo * 4) % 3), botao.center, P.CINZA, 11, ancora="center")
        else:
            borda = clarear(P.OURO, int(40 * piscar(self.tempo, 4)))
            moldura(ui, botao, fundo=P.VERM2 if tudo else (30, 110, 60), borda=borda, raio=5)
            texto(ui, "ALL IN!" if tudo else "JOGAR", (botao.centerx, botao.centery - 1), P.BRANCO, 23, ancora="center")

    def desenhar(self, tela):
        fundo_desfocado(tela, escuro=205)
        self._parede_do_salao(self.camada_do_fundo.limpar())
        self.camada_do_fundo.apresentar(tela)
        self._desenhar_crupie(tela)
        ui = self.camada.limpar()
        self._salao(ui)
        self._apostas(ui)
        self._topo(ui)
        self._tabela(ui)
        texto(ui, self.jogo.DESCRICAO, (L // 2, A - 33), P.CINZA, 11, contorno=None, ancora="midtop", media=True)
        for v in self.voadoras:
            if v.tipo == "moeda" and self.tempo >= v.inicio:
                moeda = icone("icones/moeda.png", 10)
                ui.blit(moeda, moeda.get_rect(center=v.posicao(self.tempo)))
        texto(ui, "A/D: aposta   T: all in   C: segredos   W/S: palpite   Enter: jogar   Tab: outro jogo   Esc: voltar",
              (L // 2, A - 17), (120, 116, 150), 11, contorno=None, ancora="midtop", media=True)
        self.camada.apresentar(tela)
