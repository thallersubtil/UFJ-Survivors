"""Lacaios que acompanham os mini-chefes do mapa. Só aparecem chamados por eles, nunca na linha do tempo da prova.

Cada jeito de andar é uma classe base pequena; o lacaio só escolhe o jeito e preenche os números.
"""
import math
from collections import deque

import pygame

from jogo.efeitos import TextoFlutuante
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.projeteis.tematicos import ProjetilTematico


class LacaioDoCampus(Inimigo):
    """Base: sem arte solta (só a tira animada), pouca experiência e nenhum prêmio extra."""

    ALTURA = 36
    RAIO = 15
    VIDA = 12
    DANO = 5
    PONTOS = 8
    CHANCE_IMA = 0.0

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)


class LacaioEmZiguezague(LacaioDoCampus):
    """Vai até o aluno balançando para os lados (morcego, gato)."""

    AMPLITUDE = 110
    FREQUENCIA = 5.0

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        # cada um balança num compasso próprio; vem de onde nasceu (não do endereço na memória), para a mesma
        # semente repetir a mesma partida
        self.fase_do_balanco = (self.posicao.x * 0.37 + self.posicao.y * 0.61) % (2 * math.pi)

    def mover(self, dt, jogo):
        rumo = jogo.jogador.posicao - self.posicao
        if rumo.length_squared() < 1:
            return
        rumo.normalize_ip()
        lado = pygame.Vector2(-rumo.y, rumo.x) * math.sin(self.tempo * self.FREQUENCIA + self.fase_do_balanco)
        self.posicao += (rumo * self.velocidade + lado * self.AMPLITUDE) * dt
        self.olhando_esquerda = rumo.x < 0


class LacaioQueMergulha(LacaioDoCampus):
    """Mira, dispara em linha reta, passa do ponto e mira de novo (livro, boi)."""

    TEMPO_DE_MERGULHO = 1.6

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.direcao = pygame.Vector2(1, 0)
        self._mira = 0.0

    def mover(self, dt, jogo):
        self._mira -= dt
        if self._mira <= 0:
            falta = jogo.jogador.posicao - self.posicao
            if falta.length_squared() > 0:
                self.direcao = falta.normalize()
            self._mira = self.TEMPO_DE_MERGULHO
        self.posicao += self.direcao * self.velocidade * dt
        self.olhando_esquerda = self.direcao.x < 0


class LacaioQuePula(LacaioDoCampus):
    """Anda aos pulos: só avança enquanto está no ar (carimbo)."""

    CICLO = 0.9
    PULO = 0.4

    def _no_ar(self):
        return self.tempo % self.CICLO < self.PULO

    def mover(self, dt, jogo):
        if self._no_ar():
            self.ir_em_direcao(jogo.jogador.posicao, dt)

    def balanco(self):
        fase = self.tempo % self.CICLO
        return math.sin(math.pi * fase / self.PULO) * 16 if fase < self.PULO else 0


@FabricaDeInimigos.registrar("coxinha")
class Coxinha(LacaioDoCampus):
    """Salgado da cantina com raiva. Vem em fornada."""
    NOME = "Coxinha"
    PASTA_SPRITE = "coxinha"
    VIDA = 14
    VELOCIDADE = 150
    TAMANHO_GRUPO = (4, 6)


@FabricaDeInimigos.registrar("morcego")
class Morcego(LacaioEmZiguezague):
    """Voa em ziguezague. Acompanha o Vigilante e a Gótica."""
    NOME = "Morcego"
    PASTA_SPRITE = "morcego"
    VIDA = 8
    VELOCIDADE = 170
    DANO = 4


@FabricaDeInimigos.registrar("livro_atrasado")
class LivroAtrasado(LacaioQueMergulha):
    """Livro que passou do prazo e voa em cima de quem pegou emprestado."""
    NOME = "Livro Atrasado"
    PASTA_SPRITE = "livro_atrasado"
    VIDA = 16
    VELOCIDADE = 300
    DANO = 6


@FabricaDeInimigos.registrar("cobaia")
class Cobaia(LacaioDoCampus):
    """Rato de laboratório que tomou o que não devia. Rápido e frágil."""
    NOME = "Cobaia"
    PASTA_SPRITE = "cobaia"
    RAIO = 13
    VIDA = 8
    VELOCIDADE = 200
    DANO = 4


@FabricaDeInimigos.registrar("carimbo")
class Carimbo(LacaioQuePula):
    """Carimbo da burocracia: vem aos pulos para carimbar o aluno."""
    NOME = "Carimbo"
    PASTA_SPRITE = "carimbo"
    RAIO = 17
    VIDA = 24
    VELOCIDADE = 240
    DANO = 9


@FabricaDeInimigos.registrar("lobinho")
class Lobinho(LacaioDoCampus):
    """Filhote de lobo-guará. Corre muito."""
    NOME = "Lobinho"
    PASTA_SPRITE = "lobinho"
    VIDA = 12
    VELOCIDADE = 215


@FabricaDeInimigos.registrar("dente")
class Dente(LacaioDoCampus):
    """Dente com cárie: lento, mas aguenta muita pancada."""
    NOME = "Dente"
    PASTA_SPRITE = "dente"
    RAIO = 17
    VIDA = 42
    VELOCIDADE = 75
    DANO = 9


@FabricaDeInimigos.registrar("loirinha")
class Loirinha(LacaioEmZiguezague):
    """A turma da Loira da Odontologia: iguais a ela, em miniatura, e sempre em bando. Vêm desfilando."""
    NOME = "Loirinha"
    PASTA_SPRITE = "loirinha"
    ALTURA = 56
    RAIO = 14
    VIDA = 10
    VELOCIDADE = 165
    DANO = 5
    AMPLITUDE = 60
    FREQUENCIA = 4.0


@FabricaDeInimigos.registrar("cultista")
class Cultista(LacaioDoCampus):
    """Roda em volta do aluno, fechando o círculo aos poucos."""
    NOME = "Cultista"
    PASTA_SPRITE = "cultista"
    VIDA = 20
    VELOCIDADE = 130
    DANO = 7
    RAIO_DO_CIRCULO = 230
    APERTO = 22                  # pixels por segundo que o círculo fecha

    def mover(self, dt, jogo):
        raio = max(0.0, self.RAIO_DO_CIRCULO - self.APERTO * self.tempo)
        afastado = self.posicao - jogo.jogador.posicao
        if afastado.length_squared() < 1:
            afastado = pygame.Vector2(1, 0)
        alvo = jogo.jogador.posicao + afastado.normalize().rotate(35) * raio
        self.ir_em_direcao(alvo, dt)


@FabricaDeInimigos.registrar("mini_ovni")
class MiniOvni(LacaioDoCampus):
    """Disco voador pequeno: fica à distância e atira."""
    NOME = "Mini OVNI"
    PASTA_SPRITE = "mini_ovni"
    VIDA = 18
    VELOCIDADE = 140
    DANO = 5
    DISTANCIA = 260
    INTERVALO = 2.4
    COR = (130, 255, 110)

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self._espera = self.INTERVALO

    def mover(self, dt, jogo):
        falta = jogo.jogador.posicao - self.posicao
        distancia = falta.length()
        if distancia > self.DISTANCIA + 30:
            self.ir_em_direcao(jogo.jogador.posicao, dt)
        elif distancia < self.DISTANCIA - 30 and distancia > 0:
            self.posicao -= falta / distancia * self.velocidade * dt
        self._espera -= dt
        if self._espera <= 0 and distancia > 0:
            self._espera = self.INTERVALO
            jogo.adicionar(ProjetilTematico(self.posicao, falta / distancia * 250, self.DANO, "*", self.COR, raio=9,
                                            arte="laser"))

    def balanco(self):
        return 10 + 4 * math.sin(self.tempo * 5)


@FabricaDeInimigos.registrar("boi")
class Boi(LacaioQueMergulha):
    """Boi do Agroboy: abaixa a cabeça e arranca em linha reta."""
    NOME = "Boi"
    PASTA_SPRITE = "boi"
    RAIO = 22
    VIDA = 45
    VELOCIDADE = 260
    DANO = 10
    TEMPO_DE_MERGULHO = 2.0


@FabricaDeInimigos.registrar("gato_alienigena")
class GatoAlienigena(LacaioEmZiguezague):
    """Gato verde do ET de Varginha: corre em ziguezague, difícil de acertar."""
    NOME = "Gato Alienígena"
    PASTA_SPRITE = "gato_alienigena"
    VIDA = 12
    VELOCIDADE = 190
    AMPLITUDE = 150
    FREQUENCIA = 7.0


@FabricaDeInimigos.registrar("malandro")
class Malandro(LacaioDoCampus):
    """Aluno malandro do fundão, de olho vermelho e saco de salgadinho na mão. Morre de medo do Leão do PROERD:
    se o leão chega perto, ele foge dele; fora isso, vem para cima do aluno."""
    NOME = "Malandro"
    PASTA_SPRITE = "malandro"
    ALTURA = 48
    RAIO = 15
    VIDA = 14
    VELOCIDADE = 170
    DANO = 6
    MEDO = 170                   # a que distância do leão ele sai correndo
    GRITO = "SUJOU!"
    COR_DO_GRITO = (255, 205, 50)
    INTERVALO_DO_GRITO = 4.0     # segundos até poder gritar de novo

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.temido = None       # quem ele teme (o leão que o chamou)
        self._espera_grito = 0.0

    @property
    def com_medo(self):
        return (self.temido is not None and self.temido.ativo
                and self.posicao.distance_to(self.temido.posicao) < self.MEDO)

    def mover(self, dt, jogo):
        self._espera_grito -= dt
        if not self.com_medo:
            super().mover(dt, jogo)
            return
        if self._espera_grito <= 0:
            self._espera_grito = self.INTERVALO_DO_GRITO
            jogo.adicionar(TextoFlutuante(self.GRITO, self.posicao - (0, 34), self.COR_DO_GRITO, 14))
        longe = self.posicao + (self.posicao - self.temido.posicao)
        self.ir_em_direcao(longe, dt, self.velocidade * 1.3)


@FabricaDeInimigos.registrar("cao_farejador")
class CaoFarejador(LacaioDoCampus):
    """Cão farejador do Leão do PROERD: não vê o aluno, segue o cheiro. Vai aonde ele estava ATRASO segundos
    antes, então quem fica parado é pego e quem corre fazendo curva despista."""
    NOME = "Cão Farejador"
    PASTA_SPRITE = "cao_farejador"
    ALTURA = 44
    RAIO = 17
    VIDA = 22
    VELOCIDADE = 230
    DANO = 8
    ATRASO = 0.6                 # segundos de atraso do rastro que ele segue

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.rastro = deque()    # (instante, onde o aluno estava)
        self.alvo = pygame.Vector2(posicao)

    def mover(self, dt, jogo):
        self.rastro.append((self.tempo, pygame.Vector2(jogo.jogador.posicao)))
        while len(self.rastro) > 1 and self.rastro[1][0] <= self.tempo - self.ATRASO:
            self.rastro.popleft()
        self.alvo = self.rastro[0][1]
        self.ir_em_direcao(self.alvo, dt)
