import math

import pygame

from jogo.config import Cor
from jogo.efeitos import AuraSSJ, Efeito, RaioZoltraak, TextoFlutuante
from jogo.jogador.bonus import BonusTemporario
from jogo.jogador.especial import Especial
from jogo.jogador.garrafa_de_cafe import GarrafaDeCafe
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import ProjetilDoHeroi


def gritar(jogo, dono, texto, cor=Cor.DESTAQUE):
    jogo.adicionar(TextoFlutuante(texto, dono.posicao - (0, 70), cor, 24, duracao=1.5))


class Zoltraak(Especial):
    NOME = "Zoltraak"
    DESCRICAO = "Um raio mágico enorme na direção da mira, que atravessa tudo. O dano é rolado em 8d6."
    ICONE = "icones/zoltraak.png"
    RECARGA = 45.0
    DADOS = 8
    FACES = 6
    DANO_POR_PONTO = 1.0          # cada ponto dos dados vale isto de dano a cada toque do raio

    def ativar(self, dono, jogo):
        rolagem = sum(jogo.rng.randint(1, self.FACES) for _ in range(self.DADOS))
        jogo.adicionar(RaioZoltraak(dono, rolagem * self.DANO_POR_PONTO * dono.multiplicador_dano * self.reforco))
        gritar(jogo, dono, f"{self.DADOS}d{self.FACES} = {rolagem}!", (200, 170, 255))
        Recursos.tocar("especial", 0.6)


class SuperSaiyajin(Especial):
    """Sobe de nível a cada uso na partida: SSJ, SSJ2 e SSJ3."""
    NOME = "Super Saiyajin"
    DESCRICAO = "Cabelo dourado: 2,5x de dano e mais velocidade por 12 s. A cada uso sobe de nível (SSJ2, SSJ3)."
    ICONE = "icones/ssj.png"
    RECARGA = 50.0
    DANO = (2.5, 3.0, 3.5)
    VELOCIDADE = (1.4, 1.5, 1.6)
    DURACAO = (12.0, 14.0, 16.0)

    def __init__(self):
        super().__init__()
        self.usos = 0

    @property
    def nivel(self):
        """O nível do próximo uso: 1 (SSJ), 2 (SSJ2) ou 3 (SSJ3)."""
        return min(len(self.DANO), self.usos + 1)

    def ativar(self, dono, jogo):
        i = self.nivel - 1
        dono.adicionar_bonus(BonusTemporario("ssj", "dano", self.DANO[i], self.DURACAO[i]))
        dono.adicionar_bonus(BonusTemporario("ssj_velocidade", "velocidade", self.VELOCIDADE[i], self.DURACAO[i]))
        jogo.adicionar(AuraSSJ(dono, self.DURACAO[i], self.nivel))
        gritar(jogo, dono, "SUPER SAIYAJIN!" if self.nivel == 1 else f"SUPER SAIYAJIN {self.nivel}!")
        self.usos += 1
        Recursos.tocar("especial", 0.6)


class TelaAzul(Especial):
    NOME = "Tela Azul"
    DESCRICAO = "O jogo dos inimigos trava: os da tela levam um erro fatal, ficam parados por 6 s e os projéteis somem."
    ICONE = "icones/tela_azul.png"
    RECARGA = 40.0
    DURACAO = 6.0
    DANO = 40                      # o erro fatal, em cada inimigo da tela
    RAIO = 800                     # cobre a tela inteira em volta do aluno

    def ativar(self, dono, jogo):
        dano = self.DANO * dono.multiplicador_dano * self.reforco
        for inimigo in jogo.inimigos_proximos(dono.posicao, self.RAIO):
            jogo.causar_dano(inimigo, dano)
            inimigo.travar(self.DURACAO)
        for projetil in jogo.grupos["projetil_inimigo"]:
            projetil.remover()
        gritar(jogo, dono, "TELA AZUL!", (90, 170, 255))
        Recursos.tocar("especial", 0.6)


class ZonaDeRevisao(Efeito):
    """O círculo da Revisão para Prova: quem fica dentro não leva dano."""

    camada = 0
    RAIO = 170

    def __init__(self, posicao, duracao):
        super().__init__(posicao, duracao, self.RAIO)

    def ao_atualizar(self, dt, jogo):
        if jogo.jogador.posicao.distance_to(self.posicao) <= self.RAIO:
            jogo.jogador.invencivel = max(jogo.jogador.invencivel, 0.1)

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        pulso = 0.5 + 0.5 * math.sin(self.tempo * 5)
        sup = pygame.Surface((self.RAIO * 2, self.RAIO * 2), pygame.SRCALPHA)
        pygame.draw.circle(sup, (255, 230, 120, round(40 + 30 * pulso)), (self.RAIO, self.RAIO), self.RAIO)
        pygame.draw.circle(sup, (255, 230, 120, 200), (self.RAIO, self.RAIO), self.RAIO, 3)
        tela.blit(sup, sup.get_rect(center=(round(centro.x), round(centro.y))))


class RevisaoParaProva(Especial):
    NOME = "Revisão para Prova"
    DESCRICAO = "Puxa todas as notas do campus, recupera 50% da vida e abre por 12 s uma zona onde nada te fere."
    ICONE = "icones/caderno.png"
    RECARGA = 40.0
    CURA = 0.50
    DURACAO_DA_ZONA = 12.0

    def ativar(self, dono, jogo):
        jogo.puxar_experiencia()
        dono.curar(dono.vida_maxima * self.CURA)
        jogo.adicionar(ZonaDeRevisao(dono.posicao, self.DURACAO_DA_ZONA))
        gritar(jogo, dono, "REVISÃO!")
        Recursos.tocar("especial", 0.6)


class Calourada(Especial):
    NOME = "Calourada"
    DESCRICAO = "Festa! 60% dos inimigos em volta viram seus aliados por 12 s; os outros batem 40% mais fraco."
    ICONE = "icones/calourada.png"
    RECARGA = 40.0
    RAIO = 700
    CHANCE = 0.60
    DURACAO = 12.0
    FRAQUEZA = 0.60

    def ativar(self, dono, jogo):
        for inimigo in jogo.inimigos_proximos(dono.posicao, self.RAIO):
            if jogo.rng.random() < self.CHANCE:
                inimigo.possuir(self.DURACAO)
            else:
                inimigo.enfraquecer(self.DURACAO, self.FRAQUEZA)
        gritar(jogo, dono, "CALOURADA!")
        Recursos.tocar("especial", 0.6)


class Lotacao(Especial):
    NOME = "Lotação"
    DESCRICAO = "Seis fuscas lotados cruzam a tela atropelando e possuindo inimigos."
    ICONE = "sprites/fusca.png"
    RECARGA = 35.0
    DANO = 45
    POSSESSAO = 6.0
    FAIXAS = (0.12, 0.27, 0.42, 0.58, 0.73, 0.88)   # altura de cada fusca na tela

    def ativar(self, dono, jogo):
        from jogo.ajudantes.ajudantes import FuscaVeiculo
        tela = jogo.camera.retangulo
        for i, fracao in enumerate(self.FAIXAS):
            da_esquerda = i % 2 == 0
            y = tela.top + tela.height * fracao
            x = tela.left - 120 if da_esquerda else tela.right + 120
            jogo.adicionar(FuscaVeiculo(pygame.Vector2(x, y), 1 if da_esquerda else -1, self.POSSESSAO,
                                        self.DANO * dono.multiplicador_dano * self.reforco))
        gritar(jogo, dono, "LOTAÇÃO!")
        Recursos.tocar("buzina", 0.6)


class CodigoDisparado(ProjetilDoHeroi):
    """Um pedaço de código da rajada da Virada de Noite: símbolos grandes numa telinha escura, com contorno e brilho."""

    SIMBOLOS = ("{ }", "=>", "</>", "()", "&&", "++", "[ ]", "!=")
    COR = (130, 240, 130)
    CONTORNO = (10, 40, 20)
    TAMANHO = 34
    DURACAO = 1.1
    _imagens = {}                 # um desenho por símbolo, feito uma vez só

    def __init__(self, posicao, velocidade, dano, simbolo, perfuracao=2):
        super().__init__(posicao, velocidade, dano, perfuracao=perfuracao, raio=18)
        self.simbolo = simbolo

    @classmethod
    def imagem(cls, simbolo):
        if simbolo not in cls._imagens:
            fonte = Recursos.fonte(cls.TAMANHO)
            texto = fonte.render(simbolo, True, cls.COR)
            borda = fonte.render(simbolo, True, cls.CONTORNO)
            sup = pygame.Surface((texto.get_width() + 20, texto.get_height() + 12), pygame.SRCALPHA)
            meio = (sup.get_width() // 2, sup.get_height() // 2)
            pygame.draw.rect(sup, (*cls.COR, 70), sup.get_rect(), border_radius=10)              # brilho
            pygame.draw.rect(sup, (16, 28, 20, 225), sup.get_rect().inflate(-6, -6), border_radius=8)   # tela de código
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
                sup.blit(borda, borda.get_rect(center=(meio[0] + dx, meio[1] + dy)))
            sup.blit(texto, texto.get_rect(center=meio))
            cls._imagens[simbolo] = sup
        return cls._imagens[simbolo]

    def desenhar(self, tela, camera):
        imagem = self.imagem(self.simbolo)
        tela.blit(imagem, imagem.get_rect(center=camera.para_tela(self.posicao)))


class ViradaDeNoite(Especial):
    """O especial do Programador e a munição do jogo. A Garrafa de Café enche aos poucos enquanto o especial
    recarrega; ativado com a garrafa cheia, ele atira sozinho uma rajada de código na mira até o café acabar."""

    NOME = "Virada de Noite"
    DESCRICAO = ("A garrafa de café enche aos poucos; cheia, Espaço solta uma rajada de código na mira, "
                 "uma dose por tiro, até o café acabar.")
    ICONE = "icones/virada_de_noite.png"
    RECARGA = 40.0
    TIROS_POR_SEGUNDO = 14
    DANO = 13
    PERFURACAO = 2
    VELOCIDADE = 680
    ABERTURA = 8                  # graus de espalhamento da rajada
    DOSES_DO_COPO = 10            # cada copo de café caído

    def __init__(self):
        super().__init__()
        self.garrafa = GarrafaDeCafe()
        self.disparando = False
        self._espera = 0.0

    @property
    def pronto(self):
        """Durante a rajada, Espaço não faz nada: ela segue sozinha até o café acabar."""
        return super().pronto and not self.disparando

    def atualizar(self, dt, mult_recarga=1.0):
        if not self.disparando:              # a garrafa só volta a encher depois da rajada
            super().atualizar(dt, mult_recarga)

    def ativar(self, dono, jogo):
        self.garrafa.capacidade = dono.capacidade_cafe
        self.garrafa.encher()
        self.disparando = True
        self._espera = 0.0
        gritar(jogo, dono, "VIRADA DE NOITE!", Cor.CAFE)
        Recursos.tocar("especial", 0.6)

    def agir(self, dt, dono, jogo):
        self.garrafa.capacidade = dono.capacidade_cafe
        if not self.disparando:
            self._encher_aos_poucos()
            return
        self._espera -= dt
        while self._espera <= 0 and not self.garrafa.vazia:      # cadência exata, qualquer que seja o quadro
            self._espera += 1 / self.TIROS_POR_SEGUNDO
            self._disparar(dono, jogo)
        if self.garrafa.vazia:
            self.disparando = False
            gritar(jogo, dono, "SEM CAFÉ!", Cor.CAFE)

    def _encher_aos_poucos(self):
        """Fora da rajada, a garrafa mostra a recarga: cheia quando o especial está pronto."""
        cheia = self.cargas > 0
        self.garrafa.municao = self.garrafa.capacidade if cheia else int(self.progresso * self.garrafa.capacidade)

    def _disparar(self, dono, jogo):
        self.garrafa.gastar()
        direcao = dono.direcao_mira.rotate(jogo.rng.uniform(-self.ABERTURA, self.ABERTURA))
        jogo.adicionar(CodigoDisparado(dono.posicao, direcao * self.VELOCIDADE,
                                       self.DANO * dono.multiplicador_dano * self.reforco,
                                       jogo.rng.choice(CodigoDisparado.SIMBOLOS), self.PERFURACAO))

    def ao_pegar_cafe(self, dono, jogo):
        """Na rajada, o copo vira mais tiros; fora dela, adianta a garrafa em 10 doses."""
        self.garrafa.capacidade = dono.capacidade_cafe
        if self.disparando:
            self.garrafa.acrescentar(self.DOSES_DO_COPO)
        else:
            self.adiantar(self.DOSES_DO_COPO / self.garrafa.capacidade)
            self._encher_aos_poucos()

    @property
    def medidor_extra(self):
        return self.garrafa.municao, self.garrafa.capacidade, Cor.CAFE
