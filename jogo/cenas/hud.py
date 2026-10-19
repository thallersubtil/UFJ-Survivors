"""Informações da partida desenhadas por cima do jogo."""
import pygame

from jogo.config import LARGURA, Cor
from jogo.cenas.widgets import desenhar_barra, desenhar_painel, desenhar_texto
from jogo.nucleo.recursos import Recursos


class Hud:
    def desenhar(self, tela, jogo):
        self._experiencia(tela, jogo)
        self._heroi(tela, jogo)
        self._armas_e_itens(tela, jogo)
        self._tempo_e_placar(tela, jogo)
        self._chefe(tela, jogo)
        self._anuncios(tela, jogo)

    def _experiencia(self, tela, jogo):
        j = jogo.jogador
        desenhar_barra(tela, pygame.Rect(4, 4, LARGURA - 8, 12), j.experiencia / j.experiencia_necessaria,
                       Cor.EXPERIENCIA)
        desenhar_texto(tela, f"NV {j.nivel}", 16, Cor.TEXTO, topo_direita=(LARGURA - 10, 18))

    def _heroi(self, tela, jogo):
        j = jogo.jogador
        desenhar_painel(tela, pygame.Rect(10, 24, 300, 70))
        animacoes = Recursos.animacoes_ou_imagem(j.PASTA_SPRITE, j.IMAGEM, 52)
        retrato = Recursos.na_altura(next(iter(animacoes.values())).quadros[0], 52)
        tela.blit(retrato, retrato.get_rect(center=(44, 59)))
        desenhar_texto(tela, j.NOME, 18, Cor.TEXTO, topo_esquerda=(78, 32))
        desenhar_barra(tela, pygame.Rect(78, 58, 160, 16), j.vida / j.vida_maxima, Cor.VIDA)
        desenhar_texto(tela, f"{round(j.vida)}/{round(j.vida_maxima)}", 14, Cor.TEXTO, centro=(158, 66))
        especial = j.especial
        centro = pygame.Vector2(274, 59)
        icone = Recursos.icone(especial.ICONE, 40)
        tela.blit(icone, icone.get_rect(center=centro))
        if not especial.pronto:
            veu = pygame.Surface((44, 44), pygame.SRCALPHA)
            altura = round(44 * (1 - especial.progresso))
            veu.fill((10, 8, 18, 170), pygame.Rect(0, 0, 44, altura))
            tela.blit(veu, veu.get_rect(center=centro))
        else:
            desenhar_texto(tela, "ESPAÇO", 11, Cor.DESTAQUE, centro=(centro.x, centro.y + 26))

    def _armas_e_itens(self, tela, jogo):
        j = jogo.jogador
        for i, arma in enumerate(j.armas):
            caixa = pygame.Rect(12 + i * 46, 102, 42, 42)
            desenhar_painel(tela, caixa, alfa=210)
            icone = Recursos.icone(arma.ICONE, 30)
            tela.blit(icone, icone.get_rect(center=caixa.center))
            desenhar_texto(tela, str(arma.nivel), 12, Cor.DESTAQUE, topo_direita=(caixa.right - 4, caixa.bottom - 16))
            if arma.fracao_cafe is not None:
                desenhar_barra(tela, pygame.Rect(caixa.left + 3, caixa.bottom + 3, caixa.width - 6, 4),
                               arma.fracao_cafe, Cor.CAFE)
        for i, item in enumerate(j.itens):
            caixa = pygame.Rect(12 + i * 38, 156, 34, 34)
            desenhar_painel(tela, caixa, alfa=210)
            icone = Recursos.icone(item.ICONE, 24)
            tela.blit(icone, icone.get_rect(center=caixa.center))
            desenhar_texto(tela, str(item.nivel), 11, Cor.DESTAQUE, topo_direita=(caixa.right - 3, caixa.bottom - 14))

    def _tempo_e_placar(self, tela, jogo):
        desenhar_texto(tela, jogo.placar.tempo_formatado, 34, Cor.TEXTO, centro=(LARGURA // 2, 42))
        desenhar_texto(tela, jogo.fase.NOME, 14, Cor.TEXTO_FRACO, centro=(LARGURA // 2, 66))
        desenhar_texto(tela, f"{jogo.placar.pontos} pts", 20, Cor.DESTAQUE, topo_direita=(LARGURA - 14, 38))
        desenhar_texto(tela, f"{jogo.placar.eliminacoes} eliminações", 14, Cor.TEXTO, topo_direita=(LARGURA - 14, 62))
        combo = jogo.placar.combo % 67
        desenhar_texto(tela, f"COMBO {combo}/67", 14, Cor.DESTAQUE if combo > 50 else Cor.TEXTO_FRACO,
                       topo_direita=(LARGURA - 14, 80))

    def _chefe(self, tela, jogo):
        chefe = jogo.chefe
        if chefe is None or not chefe.ativo:
            return
        retangulo = pygame.Rect(0, 0, 640, 18)
        retangulo.midbottom = (LARGURA // 2, tela.get_height() - 24)
        desenhar_barra(tela, retangulo, chefe.vida / chefe.vida_maxima, Cor.VIDA)
        desenhar_texto(tela, chefe.nome.upper(), 18, Cor.TEXTO, centro=(LARGURA // 2, retangulo.top - 14))

    def _anuncios(self, tela, jogo):
        for i, (texto, restante) in enumerate(jogo.anuncios[-3:]):
            tamanho = 96 if texto == "67!" else 40
            imagem_y = tela.get_height() // 3 + i * 56
            desenhar_texto(tela, texto, tamanho, Cor.DESTAQUE, centro=(LARGURA // 2, imagem_y))
