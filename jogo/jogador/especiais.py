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
    DADOS = 8
    FACES = 6
    DANO_POR_PONTO = 0.65         # cada ponto dos dados vale isto de dano a cada toque do raio

    def ativar(self, dono, jogo):
        rolagem = sum(jogo.rng.randint(1, self.FACES) for _ in range(self.DADOS))
        jogo.adicionar(RaioZoltraak(dono, rolagem * self.DANO_POR_PONTO * dono.multiplicador_dano))
        gritar(jogo, dono, f"{self.DADOS}d{self.FACES} = {rolagem}!", (200, 170, 255))
        Recursos.tocar("especial", 0.6)


class SuperSaiyajin(Especial):
    """Sobe de nível a cada uso na partida: SSJ, SSJ2 e SSJ3."""
    NOME = "Super Saiyajin"
    DESCRICAO = "Cabelo dourado: dano em dobro e mais velocidade. A cada uso sobe de nível (SSJ2, SSJ3)."
    ICONE = "icones/ssj.png"
    DANO = (2.0, 2.5, 3.0)
    VELOCIDADE = (1.4, 1.5, 1.6)
    DURACAO = (10.0, 12.0, 14.0)

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
    DESCRICAO = "O jogo dos inimigos trava: os da tela ficam parados por 4 s e os projéteis deles somem."
    ICONE = "icones/tela_azul.png"
    RECARGA = 50.0
    DURACAO = 4.0
    RAIO = 800                     # cobre a tela inteira em volta do aluno

    def ativar(self, dono, jogo):
        for inimigo in jogo.inimigos_proximos(dono.posicao, self.RAIO):
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
    DESCRICAO = "Puxa todas as notas do campus, recupera 30% da vida e abre por 10 s uma zona onde nada te fere."
    ICONE = "icones/caderno.png"
    RECARGA = 50.0
    CURA = 0.30
    DURACAO_DA_ZONA = 10.0

    def ativar(self, dono, jogo):
        jogo.puxar_experiencia()
        dono.curar(dono.vida_maxima * self.CURA)
        jogo.adicionar(ZonaDeRevisao(dono.posicao, self.DURACAO_DA_ZONA))
        gritar(jogo, dono, "REVISÃO!")
        Recursos.tocar("especial", 0.6)


class Calourada(Especial):
    NOME = "Calourada"
    DESCRICAO = "Festa! 40% dos inimigos em volta viram seus aliados por 8 s; os outros batem 30% mais fraco."
    ICONE = "icones/calourada.png"
    RECARGA = 50.0
    RAIO = 650
    CHANCE = 0.40
    DURACAO = 8.0
    FRAQUEZA = 0.70

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
        gritar(jogo, dono, "LOTAÇÃO!")
        Recursos.tocar("buzina", 0.6)


class CodigoDisparado(ProjetilDoHeroi):
    """Um pedaço de código da rajada da Virada de Noite: teclas e ponto e vírgula voando."""

    SIMBOLOS = (";", "{", "}", "=", "<", ">", "()")
    COR = (130, 240, 130)
    DURACAO = 1.1

    def __init__(self, posicao, velocidade, dano, simbolo):
        super().__init__(posicao, velocidade, dano, perfuracao=1, raio=9)
        self.simbolo = simbolo

    def desenhar(self, tela, camera):
        imagem = Recursos.fonte(20).render(self.simbolo, True, self.COR)
        tela.blit(imagem, imagem.get_rect(center=camera.para_tela(self.posicao)))


class ViradaDeNoite(Especial):
    """O especial do Programador e a munição do jogo: enche a Garrafa de Café e, segurando o especial, atira uma
    rajada de código enquanto houver café. Sem café, vem a abstinência."""

    NOME = "Virada de Noite"
    DESCRICAO = "Enche a garrafa com 100 doses de café; segurando Espaço, cada dose é um tiro de código na mira."
    ICONE = "icones/virada_de_noite.png"
    RECARGA = 45.0
    TIROS_POR_SEGUNDO = 10
    DANO = 9
    VELOCIDADE = 620
    ABERTURA = 6                  # graus de espalhamento da rajada
    DOSES_DO_COPO = 10            # cada copo de café caído
    ABSTINENCIA = 3.0             # segundos mais lento depois que o café acaba
    LENTIDAO = 0.7

    def __init__(self):
        super().__init__()
        self.garrafa = GarrafaDeCafe()
        self._espera = 0.0

    @property
    def pronto(self):
        """Só enche de novo com a garrafa vazia: com café sobrando, Espaço é para atirar."""
        return super().pronto and self.garrafa.vazia

    def ativar(self, dono, jogo):
        self.garrafa.capacidade = dono.capacidade_cafe
        self.garrafa.encher()
        gritar(jogo, dono, "VIRADA DE NOITE!", Cor.CAFE)
        Recursos.tocar("especial", 0.6)

    def agir(self, dt, dono, jogo):
        if not jogo.entrada.segurando_especial or self.garrafa.vazia:
            self._espera = max(0.0, self._espera - dt)
            return
        self._espera -= dt
        while self._espera <= 0 and not self.garrafa.vazia:      # cadência exata, qualquer que seja o quadro
            self._espera += 1 / self.TIROS_POR_SEGUNDO
            self._disparar(dono, jogo)

    def _disparar(self, dono, jogo):
        self.garrafa.gastar()
        direcao = dono.direcao_mira.rotate(jogo.rng.uniform(-self.ABERTURA, self.ABERTURA))
        jogo.adicionar(CodigoDisparado(dono.posicao, direcao * self.VELOCIDADE, self.DANO * dono.multiplicador_dano,
                                       jogo.rng.choice(CodigoDisparado.SIMBOLOS)))
        if self.garrafa.vazia:
            dono.adicionar_bonus(BonusTemporario("sem_cafe", "velocidade", self.LENTIDAO, self.ABSTINENCIA))
            gritar(jogo, dono, "SEM CAFÉ!", Cor.CAFE)

    def ao_pegar_cafe(self, dono, jogo):
        self.garrafa.capacidade = dono.capacidade_cafe
        self.garrafa.acrescentar(self.DOSES_DO_COPO)

    @property
    def medidor_extra(self):
        return self.garrafa.municao, self.garrafa.capacidade, Cor.CAFE
