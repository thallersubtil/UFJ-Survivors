"""Objetos quebráveis espalhados pelo campus: caixa, lixeira e vaso. Quebrados, soltam cura ou moedas.

São Inimigos para que toda arma já saiba acertá-los (entram na mesma busca de alvos), mas não
andam, não ferem e não contam no placar: o que muda fica nos métodos sobrescritos. Não vão para a
FabricaDeInimigos (as fases não os sorteiam): quem os espalha é o Jogo.
"""
from abc import ABC

from jogo.coletaveis.coletaveis import Moeda, PocaoDeVida
from jogo.inimigos.inimigo import Inimigo


class ObjetoQuebravel(Inimigo, ABC):
    grupo = "quebravel"            # fora da lista de inimigos: não pesa no alvo da fase nem no mini-mapa
    NOME = "Objeto"
    ALTURA = 44
    RAIO = 18
    VIDA = 14
    DANO = 0
    PONTOS = 0
    EXPERIENCIA = 0
    TENACIDADE = 1.0               # nada puxa, atrasa ou trava um objeto
    CONTA_NO_PLACAR = False        # quebrar caixa não é eliminação nem entra no combo
    ALVO_DA_MIRA = False           # a mira procura inimigos; o objeto só quebra quando um golpe passa por ele
    CHANCE_DE_CURA = 0.4           # senão, moedas
    MOEDAS = (3, 6)                # (mínimo, máximo) de moedas quando não sai cura

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, 1.0)       # a dificuldade não mexe em objeto: sempre a mesma vida
        self.reposiciona = False

    def atualizar(self, dt, jogo):
        """Só o que um objeto parado precisa: o tempo e o piscar de quando leva um golpe."""
        self.tempo += dt
        self.piscar = max(0.0, self.piscar - dt)

    def mover(self, dt, jogo):
        """Objeto não anda."""

    def tocar_jogador(self, jogo):
        """Objeto não fere."""

    def empurrar(self, direcao, forca=180):
        """Objeto não sai do lugar com o golpe."""

    def possuir(self, duracao):
        """O Fusca não possui objeto."""

    def assustar(self, duracao):
        """Objeto não foge."""

    def balanco(self):
        return 0

    def criar_corpo(self, jogo):
        """Objeto quebrado não deixa corpo: ele já se desfaz no próprio efeito."""
        return None

    def ao_morrer(self, jogo):
        """Quebrou: solta uma poção de vida ou um punhado de moedas."""
        if jogo.rng.random() < self.CHANCE_DE_CURA:
            jogo.adicionar(PocaoDeVida(self.posicao))
        else:
            jogo.adicionar(Moeda(self.posicao, jogo.rng.randint(*self.MOEDAS)))


class CaixaDePapelao(ObjetoQuebravel):
    NOME = "Caixa de Papelão"
    IMAGEM = "sprites/destrutivel_caixa.png"


class Lixeira(ObjetoQuebravel):
    NOME = "Lixeira"
    IMAGEM = "sprites/destrutivel_lixeira.png"
    ALTURA = 50
    VIDA = 20
    CHANCE_DE_CURA = 0.25          # lixeira dá mais moeda que cura


class VasoDePlanta(ObjetoQuebravel):
    NOME = "Vaso de Planta"
    IMAGEM = "sprites/destrutivel_vaso.png"
    ALTURA = 48
    VIDA = 10
    CHANCE_DE_CURA = 0.55          # e o vaso, mais cura


QUEBRAVEIS = (CaixaDePapelao, Lixeira, VasoDePlanta)
