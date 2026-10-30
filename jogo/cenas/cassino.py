"""Cassino do Centro Acadêmico: apostas com as moedas do jogo."""
import random

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import (TECLAS_CONFIRMAR, desenhar_fundo, desenhar_moedas, desenhar_painel,
                                desenhar_texto)
from jogo.config import ALTURA, LARGURA, Cor
from jogo.loja.cassino import JOGOS_DE_APOSTA, Cassino
from jogo.nucleo.recursos import Recursos


class CenaCassino(Cena):
    DURACAO_GIRO = 1.2
    ICONES = {
        "Pequi": "icones/pequi.png",
        "Café": "sprites/cafe.png",
        "Pão de Queijo": "icones/pao_de_queijo.png",
        "Nota 10": "sprites/nota.png",
        "Caramelo": "sprites/caramelo.png",
    }

    def __init__(self, app, rng=None):
        super().__init__(app)
        self.rng = rng or random.Random()
        self.jogos = [classe() for classe in JOGOS_DE_APOSTA]
        self.indice_jogo = 0
        self.indice_aposta = 0
        self.indice_escolha = 0
        self.resultado = None
        self.girando = 0.0
        self._tique = 0.0
        self._sorteio_visual = ()
        self.mensagem = ""

    @property
    def jogo(self):
        return self.jogos[self.indice_jogo]

    @property
    def aposta(self):
        return self.jogo.APOSTAS[self.indice_aposta]

    @property
    def escolha(self):
        return self.jogo.ESCOLHAS[self.indice_escolha % len(self.jogo.ESCOLHAS)]

    def _jogar(self):
        if self.girando:
            return
        if not self.app.progresso.pode_pagar(self.aposta):
            self.mensagem = "Moedas insuficientes."
            return
        self.resultado = Cassino.apostar(self.app.progresso, self.jogo, self.aposta, self.escolha, self.rng)
        self.girando = self.DURACAO_GIRO
        self.mensagem = ""

    def _trocar_jogo(self):
        if self.girando:
            return
        self.indice_jogo = (self.indice_jogo + 1) % len(self.jogos)
        self.indice_aposta = min(self.indice_aposta, len(self.jogo.APOSTAS) - 1)
        self.indice_escolha = 0
        self.resultado = None
        self.mensagem = ""

    def _voltar(self):
        from jogo.cenas.centro_academico import CenaCentroAcademico
        self.app.trocar(CenaCentroAcademico(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._jogar()
            return
        if evento.type != pygame.KEYDOWN:
            return
        if evento.key == pygame.K_ESCAPE:
            self._voltar()
        elif evento.key == pygame.K_TAB:
            self._trocar_jogo()
        elif evento.key in (pygame.K_LEFT, pygame.K_a) and not self.girando:
            self.indice_aposta = max(0, self.indice_aposta - 1)
        elif evento.key in (pygame.K_RIGHT, pygame.K_d) and not self.girando:
            self.indice_aposta = min(len(self.jogo.APOSTAS) - 1, self.indice_aposta + 1)
        elif evento.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s) and not self.girando:
            self.indice_escolha = (self.indice_escolha + 1) % len(self.jogo.ESCOLHAS)
        elif evento.key in TECLAS_CONFIRMAR:
            self._jogar()

    def atualizar(self, dt):
        if not self.girando:
            return
        self.girando = max(0.0, self.girando - dt)
        self._tique -= dt
        if self._tique <= 0:
            self._tique = 0.08
            Recursos.tocar("giro", 0.2)
            self._sorteio_visual = self._embaralhar()
        if not self.girando:
            Recursos.tocar("premio" if self.resultado.ganhou else "dano", 0.5 if self.resultado.ganhou else 0.2)

    def _embaralhar(self):
        simbolos = getattr(self.jogo, "SIMBOLOS", None)
        if simbolos:
            return tuple(self.rng.choice(simbolos) for _ in range(3))
        return (str(self.rng.randint(1, 20)),)

    @property
    def moedas_na_tela(self):
        """Durante o giro, o prêmio ainda não aparece no saldo."""
        moedas = self.app.progresso.moedas
        return moedas - self.resultado.premio if self.girando and self.resultado else moedas

    def _desenhar_simbolo(self, tela, simbolo, centro, tamanho):
        caixa = pygame.Rect(0, 0, tamanho, tamanho)
        caixa.center = centro
        desenhar_painel(tela, caixa, cor_fundo=(250, 244, 226), alfa=255)
        if simbolo in self.ICONES:
            icone = Recursos.icone(self.ICONES[simbolo], int(tamanho * 0.7))
            tela.blit(icone, icone.get_rect(center=centro))
        else:
            desenhar_texto(tela, simbolo, int(tamanho * 0.45), Cor.REPROVADO, centro=centro)

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/centro_academico.png", escuro=170)
        desenhar_texto(tela, "CASSINO DO CA", 44, Cor.DESTAQUE, centro=(LARGURA // 2, 70))
        desenhar_texto(tela, "Só vale moeda do jogo. A casa sempre ganha um pouquinho.", 16, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, 112))
        desenhar_moedas(tela, self.moedas_na_tela)
        painel = pygame.Rect(0, 0, 820, 430)
        painel.center = (LARGURA // 2, 380)
        desenhar_painel(tela, painel)
        desenhar_texto(tela, self.jogo.NOME.upper(), 30, Cor.DESTAQUE, centro=(painel.centerx, painel.top + 36))
        desenhar_texto(tela, self.jogo.DESCRICAO, 15, Cor.TEXTO_FRACO, centro=(painel.centerx, painel.top + 72),
                       sombra=False)
        if self.girando:
            simbolos = self._sorteio_visual
        elif self.resultado is not None:
            simbolos = self.resultado.simbolos
        else:
            simbolos = ("?",) * (3 if hasattr(self.jogo, "SIMBOLOS") else 1)
        espaco = 170
        for i, simbolo in enumerate(simbolos):
            x = painel.centerx + (i - (len(simbolos) - 1) / 2) * espaco
            self._desenhar_simbolo(tela, simbolo, (x, painel.top + 190), 140)
        if self.resultado is not None and not self.girando:
            cor = Cor.APROVADO if self.resultado.ganhou else Cor.REPROVADO
            texto = f"{self.resultado.mensagem}  +{self.resultado.premio}" if self.resultado.premio \
                else self.resultado.mensagem
            desenhar_texto(tela, texto, 26, cor, centro=(painel.centerx, painel.top + 300))
        if self.mensagem:
            desenhar_texto(tela, self.mensagem, 24, Cor.REPROVADO, centro=(painel.centerx, painel.top + 300))
        linha = f"Aposta: < {self.aposta} >"
        if self.escolha is not None:
            linha += f"      Palpite: {self.escolha.upper()}  (W/S)"
        desenhar_texto(tela, linha, 24, Cor.TEXTO, centro=(painel.centerx, painel.bottom - 50))
        desenhar_texto(tela, "A/D ou setas: valor da aposta    Enter ou clique: jogar    Tab: trocar de jogo    Esc: voltar",
                       16, Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 32))
