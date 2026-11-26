import math
import random

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_ENTER, desenhar_painel, desenhar_texto, escurecer, quebrar_linhas
from jogo.config import ALTURA, LARGURA, Cor
from jogo.nucleo.recursos import Recursos
from jogo.tesouro import COMUM, LENDARIO, Tesouro


class CenaBau(Cena):
    """Abre um baú: quanto mais raro, mais longa e mais vistosa a abertura.

    Comum: treme e abre. Épico: feixes roxos girando atrás. Lendário: suspense maior, raios dourados,
    clarão na hora de abrir e chuva de moedas.
    """

    INTERVALO_ENTRE_PREMIOS = 0.28
    CENTRO = (LARGURA // 2, 255)
    TREMOR_EXTRA = {"comum": 0.0, "epico": 0.5, "lendario": 1.2}     # o baú raro treme mais antes de abrir

    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.tempo = 0.0
        self.tesouro = Tesouro.sortear(jogo.jogador, jogo.rng)
        self.aberto = False
        self._desde_abrir = 0.0
        enfeite = random.Random(7)       # só enfeite: não gasta o sorteio da partida
        self._moedas_caindo = [(enfeite.uniform(0, LARGURA), enfeite.random(), enfeite.uniform(260, 520))
                               for _ in range(70)]
        if self.raridade is not COMUM:
            Recursos.tocar("especial", 0.5)

    @property
    def raridade(self):
        return self.tesouro.raridade

    @property
    def premio(self):
        """O primeiro prêmio (None antes de abrir)."""
        return self.tesouro.premios[0] if self.tesouro.premios else None

    @property
    def tudo_mostrado(self):
        return self.aberto and self._desde_abrir >= self.INTERVALO_ENTRE_PREMIOS * len(self.tesouro.premios) + 0.3

    def tratar_evento(self, evento):
        confirmou = evento.type == pygame.KEYDOWN and evento.key in TECLAS_ENTER
        clicou = evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
        if not (confirmou or clicou):
            return
        if not self.aberto:
            self.tempo = self.raridade.abertura        # apressa a abertura
        elif self.tudo_mostrado:
            self.jogo.baus_pendentes = max(0, self.jogo.baus_pendentes - 1)
            self.app.desempilhar()
        else:
            self._desde_abrir = 99.0                   # mostra todos os prêmios de uma vez

    def atualizar(self, dt):
        self.tempo += dt
        if self.aberto:
            self._desde_abrir += dt
        elif self.tempo >= self.raridade.abertura:
            self.tesouro.abrir(self.jogo)
            self.aberto = True
            Recursos.tocar("bau", 0.7)
            if self.raridade is LENDARIO:
                Recursos.tocar("vitoria", 0.5)

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela):
        escurecer(tela, 185)
        if self.raridade is not COMUM:
            self._raios(tela)
        if self.raridade is LENDARIO and self.aberto:
            self._chuva_de_moedas(tela)
        pulso = 1 + 0.04 * math.sin(self.tempo * 9) if self.raridade is not COMUM else 1
        desenhar_texto(tela, self.raridade.nome, round(52 * pulso), self.raridade.cor, centro=(LARGURA // 2, 70))
        if self.tesouro.critico:
            desenhar_texto(tela, "CRÍTICO DE SORTE!", 20, Cor.TEXTO, centro=(LARGURA // 2, 112))
        self._bau(tela)
        if self.aberto:
            self._premios(tela)
            self._clarao(tela)
        else:
            desenhar_texto(tela, "abrindo...", 16, Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 40))

    def _bau(self, tela):
        fracao = min(1.0, self.tempo / self.raridade.abertura)
        quadros = self.raridade.quadros
        # a tampa só abre no fim: antes disso o baú treme cada vez mais forte
        quadro = 0 if fracao < 0.75 else min(len(quadros) - 1, 1 + int((fracao - 0.75) / 0.25 * (len(quadros) - 1)))
        forca = 0 if self.aberto else 3 + 9 * fracao * (1 + self.TREMOR_EXTRA[self.raridade.chave])
        dx = round(forca * math.sin(self.tempo * 47))
        dy = round(forca * 0.5 * math.sin(self.tempo * 61))
        salto = -round(16 * max(0.0, 1 - self._desde_abrir * 4)) if self.aberto else 0
        bau = Recursos.imagem(quadros[quadro], 200)
        tela.blit(bau, bau.get_rect(center=(self.CENTRO[0] + dx, self.CENTRO[1] + dy + salto)))

    def _raios(self, tela):
        """Feixes de luz girando atrás do baú (mais largos e mais vivos depois de abrir)."""
        camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        quantos = 14 if self.raridade is LENDARIO else 9
        alfa = (95 if self.aberto else 45) + (30 if self.raridade is LENDARIO else 0)
        alcance = 950 if self.aberto else 260 + 160 * min(1.0, self.tempo / self.raridade.abertura)
        giro = self.tempo * (0.9 if self.raridade is LENDARIO else 0.5)
        for i in range(quantos):
            a = giro + i * 2 * math.pi / quantos
            largura = math.pi / quantos * 0.55
            pontos = [self.CENTRO] + [(self.CENTRO[0] + math.cos(a + d) * alcance,
                                       self.CENTRO[1] + math.sin(a + d) * alcance) for d in (-largura, largura)]
            pygame.draw.polygon(camada, (*self.raridade.cor, alfa), pontos)
        tela.blit(camada, (0, 0))

    def _chuva_de_moedas(self, tela):
        moeda = Recursos.icone("icones/moeda.png", 26)
        for x, fase, velocidade in self._moedas_caindo:
            y = ((fase * ALTURA + self._desde_abrir * velocidade) % (ALTURA + 60)) - 30
            tela.blit(moeda, (x + 10 * math.sin(self._desde_abrir * 3 + fase * 9), y))

    def _clarao(self, tela):
        duracao = 0.5 if self.raridade is LENDARIO else 0.25
        if self.raridade is COMUM or self._desde_abrir >= duracao:
            return
        clarao = pygame.Surface((LARGURA, ALTURA))
        clarao.fill((255, 250, 225))
        clarao.set_alpha(int(230 * (1 - self._desde_abrir / duracao)))
        tela.blit(clarao, (0, 0))

    def _premios(self, tela):
        premios = self.tesouro.premios
        largura, altura, vao = 208, 190, 16
        total = len(premios) * largura + (len(premios) - 1) * vao
        esquerda = (LARGURA - total) // 2
        fonte = Recursos.fonte(17)
        for i, premio in enumerate(premios):
            nascido = self._desde_abrir - i * self.INTERVALO_ENTRE_PREMIOS
            if nascido < 0:
                continue
            subida = round(30 * max(0.0, 1 - nascido * 5))
            carta = pygame.Rect(esquerda + i * (largura + vao), 395 + subida, largura, altura)
            desenhar_painel(tela, carta, cor_borda=self.raridade.cor)
            icone = Recursos.icone(premio.icone, 64)
            tela.blit(icone, icone.get_rect(center=(carta.centerx, carta.y + 50)))
            y = carta.y + 96
            for linha in quebrar_linhas(premio.titulo, fonte, largura - 20)[:2]:
                desenhar_texto(tela, linha, 17, Cor.TEXTO, centro=(carta.centerx, y))
                y += 20
            if premio.rotulo:
                desenhar_texto(tela, premio.rotulo, 14, Cor.DESTAQUE, centro=(carta.centerx, carta.bottom - 20))
        if self._desde_abrir >= len(premios) * self.INTERVALO_ENTRE_PREMIOS:
            texto = f"+{self.tesouro.moedas_ganhas} moedas"
            if self.tesouro.moedas_criticas:
                texto += f"  (CRÍTICO x{Tesouro.MULT_MOEDAS_CRITICAS}!)"
            cor = Cor.DESTAQUE if self.tesouro.moedas_criticas else Cor.TEXTO
            moeda = Recursos.icone("icones/moeda.png", 30)
            centro = (LARGURA // 2, 620)
            largura_texto = Recursos.fonte(26).size(texto)[0]
            tela.blit(moeda, moeda.get_rect(center=(centro[0] - largura_texto // 2 - 24, centro[1])))
            desenhar_texto(tela, texto, 26, cor, centro=centro)
        if self.tudo_mostrado:
            desenhar_texto(tela, "[Enter] continuar", 16, Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 40))
