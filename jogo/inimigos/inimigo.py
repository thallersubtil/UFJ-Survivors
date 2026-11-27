"""Classe base abstrata dos inimigos."""
import math
from abc import ABC, abstractmethod

import pygame

from jogo.coletaveis.coletaveis import Bau, CopoDeCafe, Ima, Moeda
from jogo.config import DISTANCIA_REPOSICIONAR, Cor
from jogo.nucleo.animacao import Animador
from jogo.efeitos import TextoFlutuante
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.recursos import Recursos
from jogo.nucleo.ser_vivo import SerVivo


class Inimigo(SerVivo, ABC):
    grupo = "inimigo"
    camada = 1

    NOME = "Inimigo"
    IMAGEM = ""
    ALTURA = 40
    PASTA_SPRITE = None   # pasta em assets/sprites/ com as animações; <pasta>_gigante para o mini-chefe
    RAIO = 16
    VIDA = 10
    VELOCIDADE = 80
    DANO = 5
    PONTOS = 10
    EXPERIENCIA = 1
    FATOR_LENTO = 0.6
    TAMANHO_GRUPO = (1, 1)       # (mínimo, máximo) de inimigos que nascem juntos
    CHANCE_IMA = 0.0015        # bem raro: o ímã puxa toda a experiência do mapa
    CONTA_NO_PLACAR = True     # se a morte vale eliminação, combo e itens (objeto quebrável: não)
    ALVO_DA_MIRA = True        # se a mira e as armas que procuram alvo escolhem este (objeto quebrável: não)
    CHANCE_MOEDA = 0.05
    CHANCE_CAFE = 0.03         # copo de café: doses para a Virada de Noite, ou um empurrão no especial
    MOEDAS_GIGANTE = 15

    GANHO_VELOCIDADE = 0.10   # por ponto de dificuldade: a prova vai ficando mais corrida
    TETO_VELOCIDADE = 1.6     # nunca mais que 60% acima da velocidade base
    GANHO_DANO = 0.12         # por ponto de dificuldade: no fim do semestre o encostão dói ~50% a mais

    TENACIDADE = 0.0          # 0 a 1: quanto resiste a puxão, lentidão e empurrão (chefes e mini-chefes: 1)
    TETO_DA_FURIA = 3.0       # depois dos 20:00 a fúria multiplica o dano sem limite, mas a velocidade só até isto

    ESCALA_GIGANTE = 3
    VIDA_GIGANTE = 30
    PONTOS_GIGANTE = 20
    EXPERIENCIA_GIGANTE = 15

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, self.RAIO, self.VIDA * escala)
        self.escala = escala
        self.furia = 1.0             # 1 = normal; depois dos 20:00 o Semestre enfurece quem nasce
        self.velocidade = self.VELOCIDADE * self.fator_de_velocidade(escala)
        self.tempo = 0.0
        self.possuido = 0.0
        self._espera_soco = 0.0
        self.empurrao = pygame.Vector2()
        self.olhando_esquerda = False
        self.gigante = False
        self.solta_bau = False
        self.reposiciona = True
        self.assustado = 0.0
        self.lento = 0.0
        self.travado = 0.0
        self.fator_lento = self.FATOR_LENTO    # quanto anda enquanto está lento (o atraso mais forte vale)
        self.marca = 0.0             # Caneta Vermelha: segundos marcado com o X
        self.vulnerabilidade = 0.0   # dano a mais que leva enquanto está marcado
        self.fraqueza = 0.0          # Calourada: segundos batendo mais fraco
        self.fator_fraqueza = 1.0
        self.animador = Animador(Recursos.animacoes_ou_imagem(self.PASTA_SPRITE, self.IMAGEM, self.ALTURA))

    @classmethod
    def sortear_tamanho_do_grupo(cls, rng):
        """Quantos deste inimigo nascem juntos, entre o mínimo e o máximo de TAMANHO_GRUPO."""
        minimo, maximo = cls.TAMANHO_GRUPO
        return rng.randint(minimo, maximo)

    @classmethod
    def fator_de_velocidade(cls, escala):
        """Quanto a dificuldade acelera este inimigo, de 1 até TETO_VELOCIDADE."""
        return min(cls.TETO_VELOCIDADE, 1 + max(0.0, escala - 1) * cls.GANHO_VELOCIDADE)

    def tornar_gigante(self):
        self.gigante = True
        self.solta_bau = True
        self.reposiciona = False
        self.raio = self.RAIO * self.ESCALA_GIGANTE
        proprias = Recursos.animacoes(f"{self.PASTA_SPRITE}_gigante") if self.PASTA_SPRITE else {}
        self.animador = Animador(proprias or Recursos.animacoes_ou_imagem(
            self.PASTA_SPRITE, self.IMAGEM, self.ALTURA * self.ESCALA_GIGANTE, self.ESCALA_GIGANTE))
        self.vida_maxima = self.vida_maxima * self.VIDA_GIGANTE
        self.vida = self.vida_maxima

    @property
    def nome(self):
        """Nome mostrado no jogo (os chefes possuídos usam o nome da matéria)."""
        return self.NOME

    @property
    def invulneravel(self):
        """Se golpes agora não tiram vida. Inimigos comuns nunca ficam invulneráveis."""
        return False

    @property
    def rotulo_da_barra(self):
        """Texto em cima da barra de vida do chefe."""
        return self.nome.upper()

    @property
    def altura_sprite(self):
        return self.animador.quadro_atual.get_height()

    def escolher_animacao(self):
        """Nome da animação que o inimigo quer agora. Sobrescreva para variar."""
        return "andar"

    @property
    def valor_em_pontos(self):
        return self.PONTOS * (self.PONTOS_GIGANTE if self.gigante else 1)

    @property
    def valor_em_experiencia(self):
        return self.EXPERIENCIA * (self.EXPERIENCIA_GIGANTE if self.gigante else 1)

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.piscar = max(0.0, self.piscar - dt)
        self.animador.tocar(self.escolher_animacao())
        self.animador.atualizar(dt)
        if self.reposiciona and \
                self.posicao.distance_squared_to(jogo.jogador.posicao) > DISTANCIA_REPOSICIONAR ** 2:
            self.posicao = jogo.fase.posicao_de_nascimento(jogo)
        if self.travado > 0:          # Tela Azul: não anda, não ataca e não encosta
            self.travado = max(0.0, self.travado - dt)
            return
        antes = pygame.Vector2(self.posicao)
        if self.assustado > 0:
            self.assustado -= dt
            self._fugir(dt, jogo)
        elif self.possuido > 0:
            self.possuido -= dt
            self._agir_possuido(dt, jogo)
        else:
            self.mover(dt, jogo)
            self.tocar_jogador(jogo)
        if self.lento > 0:            # Quadro Branco: anda só uma fração do que andaria
            self.lento -= dt
            self.posicao = antes + (self.posicao - antes) * self.fator_lento
        self.marca = max(0.0, self.marca - dt)
        self.fraqueza = max(0.0, self.fraqueza - dt)
        if self.empurrao.length_squared() > 1:
            self.posicao += self.empurrao * dt
            self.empurrao *= max(0.0, 1 - 8 * dt)
        self._separar(jogo)
        self.posicao = jogo.resolver_obstaculos(self.posicao, self.raio)
        self.posicao.x = max(jogo.arena.left + self.raio, min(self.posicao.x, jogo.arena.right - self.raio))
        self.posicao.y = max(jogo.arena.top + self.raio, min(self.posicao.y, jogo.arena.bottom - self.raio))

    @abstractmethod
    def mover(self, dt, jogo):
        """Como este inimigo se desloca. Cada tipo tem o seu jeito."""

    def ir_em_direcao(self, alvo, dt, velocidade=None):
        falta = pygame.Vector2(alvo) - self.posicao
        if falta.length_squared() > 1:
            falta.normalize_ip()
            self.posicao += falta * (velocidade or self.velocidade) * dt
            if abs(falta.x) > 0.1:
                self.olhando_esquerda = falta.x < 0

    def tocar_jogador(self, jogo):
        if Colisao.circulos_colidem(self, jogo.jogador):
            jogo.ferir_jogador(self.dano_de_contato)

    @property
    def dano_de_contato(self):
        """O encostão dói mais conforme a prova avança (a mesma escala que dá vida e velocidade ao inimigo)."""
        fraco = self.fator_fraqueza if self.fraqueza > 0 else 1.0
        return self.DANO * (1 + max(0.0, self.escala - 1) * self.GANHO_DANO) * self.furia * fraco

    def enfurecer(self, furia):
        """O fim do semestre passou: o dano de contato multiplica por `furia` e a velocidade também, até
        TETO_DA_FURIA. A fúria só sobe; chamar de novo com o mesmo valor não muda nada."""
        nova = max(self.furia, furia)
        self.velocidade *= min(nova, self.TETO_DA_FURIA) / min(self.furia, self.TETO_DA_FURIA)
        self.furia = nova

    def ao_chegar_o_chefe(self, jogo):
        """Um chefe principal entrou em campo: o lacaio comum sai para abrir espaço para a luta. Fica quem
        ainda deve um baú (os gigantes) e quem luta do lado do aluno (possuído pelo Fusca); chefes e
        mini-chefes sobrescrevem para ficar."""
        if self.solta_bau or self.possuido > 0:
            return
        self.remover()

    def assustar(self, duracao):
        """Greve: por um tempo, foge do aluno em vez de atacar."""
        self.assustado = max(self.assustado, duracao)

    def atrasar(self, duracao, fator=None):
        """Quadro Branco e Horário de Atendimento: por um tempo, anda só `fator` do que andaria (FATOR_LENTO, se
        não disser). Com dois atrasos, vale o mais forte; quem tem tenacidade total nem sente."""
        fator = self.FATOR_LENTO if fator is None else fator
        self.fator_lento = min(self.fator_lento, fator) if self.lento > 0 else fator
        self.lento = max(self.lento, duracao * (1 - self.TENACIDADE))

    def marcar_com_x(self, duracao, dano_extra):
        """Caneta Vermelha: marcado com um X, leva `dano_extra` a mais de dano por um tempo."""
        self.marca = max(self.marca, duracao)
        self.vulnerabilidade = max(self.vulnerabilidade, dano_extra)

    @property
    def marcado(self):
        return self.marca > 0

    @property
    def fator_de_dano_recebido(self):
        """Quanto o dano que ele leva é multiplicado (marcado pela Caneta Vermelha leva mais)."""
        return 1 + self.vulnerabilidade if self.marcado else 1.0

    def enfraquecer(self, duracao, fator):
        """Calourada: por um tempo, o encostão dele dói só `fator` do normal."""
        self.fraqueza = max(self.fraqueza, duracao)
        self.fator_fraqueza = fator

    def travar(self, duracao):
        """Tela Azul: por um tempo, fica parado no lugar (quem tem tenacidade total nem sente)."""
        self.travado = max(self.travado, duracao * (1 - self.TENACIDADE))

    def puxar(self, deslocamento):
        """Arrasta o inimigo (redemoinho da Aula Magna). A tenacidade desconta: chefe não sai do lugar."""
        self.posicao += pygame.Vector2(deslocamento) * (1 - self.TENACIDADE)

    def _fugir(self, dt, jogo):
        longe = self.posicao + (self.posicao - jogo.jogador.posicao)
        self.ir_em_direcao(longe, dt, self.velocidade * 1.2)

    def possuir(self, duracao):
        """Efeito do Fusca Azul: por um tempo, ataca outros inimigos."""
        self.possuido = max(self.possuido, duracao)

    def _agir_possuido(self, dt, jogo):
        self._espera_soco -= dt
        alvo = jogo.inimigo_mais_proximo(self.posicao, 400, excluir=self)
        if alvo is None:
            return
        self.ir_em_direcao(alvo.posicao, dt, self.velocidade * 1.4)
        if self._espera_soco <= 0 and Colisao.circulos_colidem(self, alvo):
            self._espera_soco = 0.5
            jogo.causar_dano(alvo, max(5, self.DANO * 2), alvo.posicao - self.posicao)
            jogo.adicionar(TextoFlutuante("POW!", alvo.posicao, Cor.DESTAQUE, 16))

    def empurrar(self, direcao, forca=180):
        direcao = pygame.Vector2(direcao)
        if direcao.length_squared() > 0:
            self.empurrao += direcao.normalize() * forca * (0.25 if self.gigante else 1)

    def _separar(self, jogo):
        for outro in jogo.grade.proximos(self.posicao, self.raio * 2)[:8]:
            if outro is self:
                continue
            afastar = self.posicao - outro.posicao
            soma = self.raio + outro.raio
            distancia2 = afastar.length_squared()
            if 0 < distancia2 < soma * soma:
                distancia = math.sqrt(distancia2)
                self.posicao += afastar / distancia * (soma - distancia) * 0.25

    def ao_morrer(self, jogo):
        """O que acontece quando morre. Por padrão solta nota e, às vezes, moeda ou (bem raramente) um ímã.
        Cura não: ela vem dos objetos quebráveis do mapa e do Kit de Primeiros Socorros."""
        jogo.soltar_nota(self.posicao, self.valor_em_experiencia)
        if jogo.rng.random() < self.CHANCE_IMA:
            jogo.adicionar(Ima(self.posicao + (10, 0)))
        if self.gigante:
            jogo.adicionar(Moeda(self.posicao - (12, 0), self.MOEDAS_GIGANTE))
        elif jogo.rng.random() < jogo.jogador.chance(self.CHANCE_MOEDA):
            jogo.adicionar(Moeda(self.posicao - (10, 0)))
        elif self.CONTA_NO_PLACAR and jogo.rng.random() < self.CHANCE_CAFE:
            jogo.adicionar(CopoDeCafe(self.posicao + (10, 0)))
        if self.solta_bau:
            jogo.adicionar(Bau(self.posicao))

    @property
    def animado(self):
        return len(self.animador.animacao.quadros) > 1

    def balanco(self):
        """Balanço de quem não tem animação de verdade (arte estática)."""
        return 0 if self.animado else abs(math.sin(self.tempo * 9)) * 3

    def desenhar(self, tela, camera):
        self.desenhar_corpo(tela, camera)
        if self.possuido > 0:
            self._desenhar_possessao(tela, camera)
        if self.marcado:
            self._desenhar_marca(tela, camera)

    def _desenhar_marca(self, tela, camera):
        """O X vermelho da Caneta Vermelha em cima da cabeça."""
        p = camera.para_tela(self.posicao)
        x, y, lado = round(p.x), round(p.y - self.altura_sprite / 2 - 12), 7
        for inicio, fim in (((x - lado, y - lado), (x + lado, y + lado)), ((x + lado, y - lado), (x - lado, y + lado))):
            pygame.draw.line(tela, (230, 30, 40), inicio, fim, 4)

    def desenhar_corpo(self, tela, camera):
        """Desenha o sprite. Inimigos com visual especial sobrescrevem só isto."""
        imagem = self.animador.quadro_atual
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda,
                        piscar=self.piscar > 0, deslocamento_y=self.balanco())

    def _desenhar_possessao(self, tela, camera):
        p = camera.para_tela(self.posicao)
        topo = (round(p.x), round(p.y - self.altura_sprite / 2 - 14))
        pygame.draw.circle(tela, (40, 110, 230), topo, 9)
        marca = Recursos.fonte(14).render("!", True, Cor.TEXTO)
        tela.blit(marca, marca.get_rect(center=topo))
