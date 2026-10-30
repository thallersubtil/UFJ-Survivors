"""Loja do Centro Acadêmico: melhorias permanentes e desbloqueio de armas e itens."""
from dataclasses import dataclass
from typing import Callable

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import (TECLAS_CONFIRMAR, desenhar_fundo, desenhar_moedas, desenhar_painel,
                                desenhar_texto)
from jogo.config import ALTURA, LARGURA, Cor
from jogo.loja.melhorias import MELHORIAS
from jogo.nucleo.recursos import Recursos
from jogo.progressao import Progressao


@dataclass
class LinhaDaLoja:
    nome: str
    descricao: str
    icone: str
    situacao: str            # "nível 2/5", "ARMA", "ITEM"
    preco: object            # int, ou None quando não dá mais para comprar
    comprar: Callable


class CenaLoja(Cena):
    ABAS = ("MELHORIAS", "DESBLOQUEIOS")
    ALTURA_LINHA = 58
    TOPO = 168

    def __init__(self, app):
        super().__init__(app)
        self.aba = 0
        self.indice = 0
        self.mensagem = ""
        self._tempo_mensagem = 0.0

    @staticmethod
    def desbloqueaveis():
        """Armas e itens que custam moedas para aparecer nas cartas."""
        return [c for c in Progressao.ARMAS + Progressao.ITENS if c.PRECO_DESBLOQUEIO > 0]

    def linhas(self):
        progresso = self.app.progresso
        if self.aba == 0:
            return [LinhaDaLoja(m.NOME, m.DESCRICAO, m.ICONE, f"nível {progresso.nivel_de(m)}/{m.NIVEL_MAXIMO}",
                                progresso.preco_da_proxima(m), lambda m=m: progresso.comprar_melhoria(m))
                    for m in MELHORIAS]
        linhas = []
        for classe in self.desbloqueaveis():
            tipo = "ARMA" if classe in Progressao.ARMAS else "ITEM"
            preco = None if progresso.desbloqueado(classe) else classe.PRECO_DESBLOQUEIO
            linhas.append(LinhaDaLoja(classe.NOME, classe.DESCRICAO, classe.ICONE, tipo, preco,
                                      lambda c=classe: progresso.desbloquear(c)))
        return linhas

    def _avisar(self, texto):
        self.mensagem = texto
        self._tempo_mensagem = 2.0

    def _comprar(self):
        linha = self.linhas()[self.indice]
        if linha.preco is None:
            self._avisar("Já está no máximo." if self.aba == 0 else "Já foi comprado.")
        elif not self.app.progresso.pode_pagar(linha.preco):
            self._avisar("Moedas insuficientes.")
        elif linha.comprar():
            Recursos.tocar("compra", 0.5)
            self._avisar(f"Comprado: {linha.nome}!")

    def _trocar_aba(self):
        self.aba = (self.aba + 1) % len(self.ABAS)
        self.indice = 0

    def _retangulo(self, i):
        return pygame.Rect(120, self.TOPO + i * self.ALTURA_LINHA, LARGURA - 240, self.ALTURA_LINHA - 6)

    def _voltar(self):
        from jogo.cenas.centro_academico import CenaCentroAcademico
        self.app.trocar(CenaCentroAcademico(self.app))

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
        elif evento.type == pygame.MOUSEMOTION:
            for i in range(quantidade):
                if self._retangulo(i).collidepoint(evento.pos):
                    self.indice = i
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, aba in enumerate(self.ABAS):
                if self._retangulo_aba(i).collidepoint(evento.pos) and i != self.aba:
                    self._trocar_aba()
                    return
            for i in range(quantidade):
                if self._retangulo(i).collidepoint(evento.pos):
                    self.indice = i
                    self._comprar()

    def atualizar(self, dt):
        self._tempo_mensagem = max(0.0, self._tempo_mensagem - dt)
        if self._tempo_mensagem <= 0:
            self.mensagem = ""

    @staticmethod
    def _retangulo_aba(i):
        return pygame.Rect(120 + i * 250, 104, 240, 46)

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/centro_academico.png", escuro=170)
        desenhar_texto(tela, "LOJA DO CENTRO ACADÊMICO", 40, Cor.DESTAQUE, topo_esquerda=(120, 40))
        desenhar_moedas(tela, self.app.progresso.moedas)
        for i, aba in enumerate(self.ABAS):
            caixa = self._retangulo_aba(i)
            desenhar_painel(tela, caixa, cor_borda=Cor.DESTAQUE if i == self.aba else Cor.BORDA,
                            alfa=255 if i == self.aba else 150)
            desenhar_texto(tela, aba, 20, Cor.DESTAQUE if i == self.aba else Cor.TEXTO_FRACO, centro=caixa.center)
        progresso = self.app.progresso
        for i, linha in enumerate(self.linhas()):
            caixa = self._retangulo(i)
            focada = i == self.indice
            desenhar_painel(tela, caixa, cor_borda=Cor.DESTAQUE if focada else Cor.BORDA, alfa=245 if focada else 200)
            icone = Recursos.icone(linha.icone, 40)
            tela.blit(icone, icone.get_rect(center=(caixa.left + 34, caixa.centery)))
            desenhar_texto(tela, linha.nome, 20, Cor.TEXTO, topo_esquerda=(caixa.left + 66, caixa.top + 5))
            desenhar_texto(tela, linha.descricao, 14, Cor.TEXTO_FRACO, topo_esquerda=(caixa.left + 66, caixa.top + 30),
                           sombra=False)
            desenhar_texto(tela, linha.situacao, 16, Cor.TEXTO_FRACO, topo_direita=(caixa.right - 170, caixa.top + 16))
            if linha.preco is None:
                preco, cor = ("MÁXIMO" if self.aba == 0 else "COMPRADO"), Cor.APROVADO
            else:
                preco = f"{linha.preco} moedas"
                cor = Cor.DESTAQUE if progresso.pode_pagar(linha.preco) else Cor.REPROVADO
            desenhar_texto(tela, preco, 18, cor, topo_direita=(caixa.right - 18, caixa.top + 15))
        if self.mensagem:
            desenhar_texto(tela, self.mensagem, 22, Cor.DESTAQUE, centro=(LARGURA // 2, ALTURA - 70))
        desenhar_texto(tela, "Setas: escolher    Tab ou A/D: trocar de aba    Enter: comprar    Esc: voltar", 16,
                       Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 32))
