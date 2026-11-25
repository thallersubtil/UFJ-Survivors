import pygame

from jogo.config import Cor
from jogo.efeitos import AuraSSJ, RaioZoltraak, TextoFlutuante
from jogo.jogador.bonus import BonusTemporario
from jogo.jogador.especial import Especial
from jogo.nucleo.recursos import Recursos


class Zoltraak(Especial):
    NOME = "Zoltraak"
    DESCRICAO = "Um raio mágico enorme na direção da mira, que atravessa tudo."
    ICONE = "icones/zoltraak.png"
    DANO_POR_TOQUE = 18

    def ativar(self, dono, jogo):
        jogo.adicionar(RaioZoltraak(dono, self.DANO_POR_TOQUE * dono.multiplicador_dano))
        Recursos.tocar("especial", 0.6)


class SuperSaiyajin(Especial):
    NOME = "Super Saiyajin"
    DESCRICAO = "Cabelo dourado por 10 s: dano em dobro e mais velocidade."
    ICONE = "icones/ssj.png"
    DURACAO = 10.0

    def ativar(self, dono, jogo):
        dono.adicionar_bonus(BonusTemporario("ssj", "dano", 2.0, self.DURACAO))
        dono.adicionar_bonus(BonusTemporario("ssj_velocidade", "velocidade", 1.4, self.DURACAO))
        jogo.adicionar(AuraSSJ(dono, self.DURACAO))
        Recursos.tocar("especial", 0.6)


class ViradaDeNoite(Especial):
    NOME = "Virada de Noite"
    DESCRICAO = "Enche o café de todas as armas, que recarregam 2,5x mais rápido por 8 s."
    ICONE = "icones/energetico.png"
    DURACAO = 8.0
    RECARGA_ARMAS = 0.4

    def ativar(self, dono, jogo):
        dono.encher_cafe()
        dono.adicionar_bonus(BonusTemporario("virada", "recarga", self.RECARGA_ARMAS, self.DURACAO))
        jogo.adicionar(TextoFlutuante("VIRADA DE NOITE!", dono.posicao - (0, 70), Cor.DESTAQUE, 24, duracao=1.5))
        Recursos.tocar("especial", 0.6)


class RevisaoParaProva(Especial):
    NOME = "Revisão para Prova"
    DESCRICAO = "Puxa todas as notas do campus e recupera 30% da vida."
    ICONE = "icones/caderno.png"
    RECARGA = 50.0
    CURA = 0.30

    def ativar(self, dono, jogo):
        from jogo.coletaveis.coletaveis import Nota
        for coletavel in jogo.grupos["coletavel"]:
            if isinstance(coletavel, Nota):
                coletavel.atraido = True
        dono.curar(dono.vida_maxima * self.CURA)
        jogo.adicionar(TextoFlutuante("REVISÃO!", dono.posicao - (0, 70), Cor.DESTAQUE, 24, duracao=1.5))
        Recursos.tocar("especial", 0.6)


class Speedrun(Especial):
    NOME = "Speedrun"
    DESCRICAO = "Por 6 s: muito mais velocidade e invencível."
    ICONE = "icones/rolamento.png"
    RECARGA = 45.0
    DURACAO = 6.0

    def ativar(self, dono, jogo):
        dono.adicionar_bonus(BonusTemporario("speedrun", "velocidade", 1.8, self.DURACAO))
        dono.invencivel = max(dono.invencivel, self.DURACAO)
        jogo.adicionar(TextoFlutuante("SPEEDRUN!", dono.posicao - (0, 70), Cor.DESTAQUE, 24, duracao=1.5))
        Recursos.tocar("especial", 0.6)


class TroteReverso(Especial):
    NOME = "Trote Reverso"
    DESCRICAO = "Os inimigos em volta levam dano e fogem de você por 5 s."
    ICONE = "icones/atletica.png"
    RECARGA = 50.0
    RAIO = 650
    DURACAO = 5.0
    DANO = 15

    def ativar(self, dono, jogo):
        for inimigo in jogo.inimigos_proximos(dono.posicao, self.RAIO):
            jogo.causar_dano(inimigo, self.DANO * dono.multiplicador_dano, inimigo.posicao - dono.posicao)
            inimigo.assustar(self.DURACAO)
        jogo.adicionar(TextoFlutuante("TROTE REVERSO!", dono.posicao - (0, 70), Cor.DESTAQUE, 24, duracao=1.5))
        Recursos.tocar("especial", 0.6)


class Lotacao(Especial):
    NOME = "Lotação"
    DESCRICAO = "Quatro fuscas lotados cruzam a tela atropelando e possuindo inimigos."
    ICONE = "sprites/fusca.png"
    RECARGA = 40.0
    DANO = 20
    POSSESSAO = 4.0

    def ativar(self, dono, jogo):
        from jogo.ajudantes.ajudantes import FuscaVeiculo
        tela = jogo.camera.retangulo
        for i, fracao in enumerate((0.2, 0.4, 0.6, 0.8)):
            da_esquerda = i % 2 == 0
            y = tela.top + tela.height * fracao
            x = tela.left - 120 if da_esquerda else tela.right + 120
            jogo.adicionar(FuscaVeiculo(pygame.Vector2(x, y), 1 if da_esquerda else -1, self.POSSESSAO,
                                        self.DANO * dono.multiplicador_dano))
        jogo.adicionar(TextoFlutuante("LOTAÇÃO!", dono.posicao - (0, 70), Cor.DESTAQUE, 24, duracao=1.5))
        Recursos.tocar("buzina", 0.6)
