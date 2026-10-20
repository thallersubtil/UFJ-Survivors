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
