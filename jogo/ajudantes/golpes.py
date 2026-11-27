"""O que as armas do semestre põem na arena: o dado jogado, o arco da régua e do teclado, as estocadas da caneta, o
lightstick que vai e volta, os alfinetes do mapa e os elos da corrente do WhatsApp. Desenhados por código até a
arte própria ser aprovada."""
import math

import pygame

from jogo.ajudantes.ajudantes import Ajudante
from jogo.efeitos import Efeito, TextoFlutuante
from jogo.formas_supremas import AreaQueFere
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import ProjetilDoHeroi


def mostrar(jogo, texto, posicao, cor, tamanho=18):
    jogo.adicionar(TextoFlutuante(texto, pygame.Vector2(posicao) - (0, 40), cor, tamanho, duracao=0.9))


def camada_transparente(tela):
    return pygame.Surface(tela.get_size(), pygame.SRCALPHA)


# ------------------------------------------------------------------ Dado de 20 Lados

class DadoArremessado(ProjetilDoHeroi):
    """Um d20 voando, com o número que saiu."""

    DURACAO = 1.2
    LADO = 15

    def __init__(self, posicao, velocidade, dano, numero):
        super().__init__(posicao, velocidade, dano, perfuracao=1, raio=12)
        self.numero = numero

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        giro = self.tempo * 720
        pontos = [centro + pygame.Vector2(self.LADO, 0).rotate(giro + 60 * i) for i in range(6)]
        cor = (255, 214, 90) if self.numero == 20 else (200, 60, 60)
        pygame.draw.polygon(tela, cor, pontos)
        pygame.draw.polygon(tela, (30, 20, 30), pontos, 2)
        texto = Recursos.fonte(14).render(str(self.numero), True, (255, 255, 255))
        tela.blit(texto, texto.get_rect(center=(round(centro.x), round(centro.y))))


# ------------------------------------------------------------------ golpes em arco (Régua, Teclado Mecânico)

def no_arco(inimigo, origem, direcao, alcance, abertura):
    """Se o inimigo está no arco de `abertura` graus à frente de `direcao`, até `alcance`."""
    falta = inimigo.posicao - origem
    if falta.length() > alcance + inimigo.raio:
        return False
    if falta.length_squared() < 1:
        return True
    desvio = (direcao.angle_to(falta) + 180) % 360 - 180      # ângulo entre a mira e o inimigo, de -180 a 180
    return abs(desvio) <= abertura / 2


class ArcoDaRegua(Ajudante):
    """Um golpe que varre um arco na frente do aluno: fere quem estiver nele uma vez e some."""

    camada = 3
    DURACAO = 0.18
    COR_DO_ARCO = (250, 230, 120)

    def __init__(self, dono, direcao, alcance, abertura, dano):
        super().__init__(dono.posicao, alcance)
        self.dono = dono
        self.direcao = pygame.Vector2(direcao)
        self.alcance = alcance
        self.abertura = abertura
        self.dano = dano
        self.tempo = 0.0
        self._ja_feriu = False

    def esta_visivel(self, camera):
        return True

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.posicao = pygame.Vector2(self.dono.posicao)
        if not self._ja_feriu:
            self._ja_feriu = True
            for inimigo in jogo.inimigos_proximos(self.posicao, self.alcance):
                if no_arco(inimigo, self.posicao, self.direcao, self.alcance, self.abertura):
                    jogo.causar_dano(inimigo, self.dano, inimigo.posicao - self.posicao)
                    self.ao_ferir(inimigo, jogo)
        if self.tempo >= self.DURACAO:
            self.remover()

    def ao_ferir(self, inimigo, jogo):
        """Gancho: o que mais acontece com quem o golpe pegou."""

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        fracao = min(1.0, self.tempo / self.DURACAO)
        inicio = -self.abertura / 2
        varrido = inicio + self.abertura * fracao               # o golpe passa de um lado ao outro
        base = self.direcao.as_polar()[1]
        pontos = [centro]
        for passo in range(9):
            angulo = base + inicio + (varrido - inicio) * passo / 8
            pontos.append(centro + pygame.Vector2(self.alcance, 0).rotate(angulo))
        cor = self.aura or self.COR_DO_ARCO
        sup = camada_transparente(tela)
        pygame.draw.polygon(sup, (*cor, 90), pontos)
        tela.blit(sup, (0, 0))
        self.desenhar_instrumento(tela, centro, centro + pygame.Vector2(self.alcance, 0).rotate(base + varrido))

    def desenhar_instrumento(self, tela, centro, ponta):
        pygame.draw.line(tela, (200, 150, 70), centro, ponta, 8)            # a régua de madeira
        pygame.draw.line(tela, (90, 60, 30), centro, ponta, 2)


class TeclaVoadora(ProjetilDoHeroi):
    """Uma tecla que saltou do Teclado Mecânico."""

    DURACAO = 0.9
    LETRAS = "QWERTYASDFGHZXCV"

    def __init__(self, posicao, velocidade, dano, letra, atingidos=None):
        super().__init__(posicao, velocidade, dano, perfuracao=1, raio=9, atingidos=atingidos)
        self.letra = letra

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        caixa = pygame.Rect(0, 0, 18, 18)
        caixa.center = (round(centro.x), round(centro.y))
        pygame.draw.rect(tela, (40, 40, 48), caixa.inflate(4, 4), border_radius=4)
        pygame.draw.rect(tela, self.aura or (225, 230, 240), caixa, border_radius=3)
        texto = Recursos.fonte(12).render(self.letra, True, (30, 30, 40))
        tela.blit(texto, texto.get_rect(center=caixa.center))


class GolpeDoTeclado(ArcoDaRegua):
    """O Teclado Mecânico varre o arco; cada inimigo atingido solta teclas nos vizinhos."""

    COR_DO_ARCO = (130, 240, 130)
    ALCANCE_DAS_TECLAS = 260
    VELOCIDADE_DAS_TECLAS = 520
    FRACAO_DAS_TECLAS = 0.5          # dano de cada tecla, em fração do golpe

    def __init__(self, dono, direcao, alcance, abertura, dano, teclas):
        super().__init__(dono, direcao, alcance, abertura, dano)
        self.teclas = teclas

    def ao_ferir(self, inimigo, jogo):
        vizinhos = sorted((e for e in jogo.inimigos_proximos(inimigo.posicao, self.ALCANCE_DAS_TECLAS)
                           if e is not inimigo and e.ALVO_DA_MIRA),
                          key=lambda e: e.posicao.distance_squared_to(inimigo.posicao))
        for alvo in vizinhos[:self.teclas]:
            rumo = alvo.posicao - inimigo.posicao
            if rumo.length_squared() > 0:
                self.soltar_tecla(jogo, inimigo, rumo.normalize())

    def soltar_tecla(self, jogo, de_quem, direcao):
        """Solta uma tecla de quem foi atingido; ela não volta a bater nele."""
        tecla = TeclaVoadora(de_quem.posicao, direcao * self.VELOCIDADE_DAS_TECLAS, self.dano * self.FRACAO_DAS_TECLAS,
                             jogo.rng.choice(TeclaVoadora.LETRAS), atingidos={de_quem})
        tecla.aura = self.aura
        jogo.adicionar(tecla)

    def desenhar_instrumento(self, tela, centro, ponta):
        eixo = ponta - centro
        if eixo.length_squared() < 1:
            return
        lado = eixo.normalize().rotate(90) * 9
        corpo = [centro + lado, ponta + lado, ponta - lado, centro - lado]
        pygame.draw.polygon(tela, (40, 40, 48), corpo)
        for i in range(1, 7):                                   # fileira de teclas
            p = centro + eixo * (i / 7)
            pygame.draw.circle(tela, (225, 230, 240), (round(p.x), round(p.y)), 3)


class OndaDeTeclas(Efeito):
    """Ctrl+Alt+Del: uma onda de teclas saindo em volta do aluno."""

    QUANTIDADE = 12

    def __init__(self, posicao, dano, aura=None):
        super().__init__(posicao, 0.05)
        self.dano = dano
        self.aura = aura

    def ao_atualizar(self, dt, jogo):
        if self.tempo > dt:
            return
        for i in range(self.QUANTIDADE):
            direcao = pygame.Vector2(1, 0).rotate(i * 360 / self.QUANTIDADE)
            tecla = TeclaVoadora(self.posicao, direcao * GolpeDoTeclado.VELOCIDADE_DAS_TECLAS, self.dano,
                                 TeclaVoadora.LETRAS[i % len(TeclaVoadora.LETRAS)])
            tecla.aura = self.aura
            jogo.adicionar(tecla)

    def desenhar(self, tela, camera):
        """A onda aparece nas teclas."""


# ------------------------------------------------------------------ Caneta de Correção

class EstocadaDaCaneta(Ajudante):
    """Estocadas rápidas da caneta na direção da mira. Quem leva pode ficar marcado com um X; a última estocada da
    série pode deixar algo no chão (`rastro`, uma função que recebe a ponta e devolve a entidade)."""

    camada = 3
    INTERVALO = 0.07
    LARGURA = 18
    COR = (200, 40, 40)

    def __init__(self, dono, direcao, alcance, dano, estocadas, marca=None, rastro=None):
        super().__init__(dono.posicao, alcance)
        self.dono = dono
        self.direcao = pygame.Vector2(direcao)
        self.alcance = alcance
        self.dano = dano
        self.restantes = estocadas
        self.marca = marca                # (duração, dano extra) do X, ou None
        self.rastro = rastro
        self.tempo = 0.0
        self._espera = 0.0

    def esta_visivel(self, camera):
        return True

    @property
    def ponta(self):
        return self.dono.posicao + self.direcao * self.alcance

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self._espera -= dt
        if self._espera > 0:
            return
        if self.restantes <= 0:
            self.remover()
            return
        self.restantes -= 1
        self._espera = self.INTERVALO
        for inimigo in jogo.inimigos_proximos(self.dono.posicao, self.alcance):
            if Colisao.segmento_acerta_circulo(self.dono.posicao, self.ponta, self.LARGURA, inimigo.posicao,
                                               inimigo.raio):
                jogo.causar_dano(inimigo, self.dano, self.direcao)
                if self.marca is not None and inimigo.ativo:
                    inimigo.marcar_com_x(*self.marca)
        if self.rastro is not None and self.restantes == 0:     # só a última estocada da série deixa rastro
            entidade = self.rastro(pygame.Vector2(self.ponta))
            entidade.aura = self.aura
            jogo.adicionar(entidade)

    def desenhar(self, tela, camera):
        inicio = camera.para_tela(self.dono.posicao)
        avanco = 0.6 + 0.4 * abs(math.sin(self.tempo * 40))   # a caneta vai e volta
        fim = camera.para_tela(self.dono.posicao + self.direcao * self.alcance * avanco)
        pygame.draw.line(tela, self.COR, inicio, fim, 7)
        pygame.draw.line(tela, self.aura or (240, 230, 230), inicio, fim, 2)


class XDeCorrecao(AreaQueFere):
    """Correção em Massa: um X vermelho gigante riscado no chão, que fere quem está nele."""

    camada = 0

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        alfa = round(200 * self.alfa_do_fim / 255)
        sup = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        cor = (*(self.aura or (220, 40, 40)), alfa)
        r = self.raio
        largura = max(6, r // 4)
        pygame.draw.line(sup, cor, (r * 0.25, r * 0.25), (r * 1.75, r * 1.75), largura)
        pygame.draw.line(sup, cor, (r * 1.75, r * 0.25), (r * 0.25, r * 1.75), largura)
        tela.blit(sup, sup.get_rect(center=(round(centro.x), round(centro.y))))


# ------------------------------------------------------------------ Lightstick

class NotaMusical(ProjetilDoHeroi):
    """Nota musical que estoura do lightstick na Coreografia."""

    DURACAO = 0.8

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        cor = self.aura or (255, 120, 200)
        x, y = round(centro.x), round(centro.y)
        pygame.draw.circle(tela, cor, (x - 3, y + 4), 5)
        pygame.draw.line(tela, cor, (x + 1, y + 4), (x + 1, y - 9), 2)
        pygame.draw.line(tela, cor, (x + 1, y - 9), (x + 7, y - 6), 2)


class LightstickGirando(ProjetilDoHeroi):
    """O lightstick do Otaku: sai girando, atravessa quem estiver no caminho e volta para a mão (acerta de novo na
    volta). Na Coreografia, estoura em notas musicais quando chega de volta."""

    DURACAO = 4.0
    COR = (255, 110, 200)

    def __init__(self, dono, velocidade, dano, alcance, notas=0):
        super().__init__(dono.posicao, velocidade, dano, perfuracao=10 ** 6, raio=16)
        self.dono = dono
        self.alcance = alcance
        self.notas = notas
        self.voltando = False
        self.rapidez = pygame.Vector2(velocidade).length()

    def mover(self, dt):
        if not self.voltando:
            self.posicao += self.velocidade * dt
            if self.posicao.distance_to(self.dono.posicao) >= self.alcance:
                self.voltando = True
                self.atingidos.clear()                       # na volta, acerta de novo
            return
        falta = self.dono.posicao - self.posicao
        if falta.length() <= self.rapidez * dt + 8:
            self.chegou = True
            return
        self.velocidade = falta.normalize() * self.rapidez
        self.posicao += self.velocidade * dt

    chegou = False

    def atualizar(self, dt, jogo):
        super().atualizar(dt, jogo)
        if self.chegou and self.ativo:
            for i in range(self.notas):
                direcao = pygame.Vector2(1, 0).rotate(i * 360 / self.notas + self.tempo * 90)
                nota = NotaMusical(self.dono.posicao, direcao * 420, self.dano * 0.6, perfuracao=1, raio=9)
                nota.aura = self.aura
                jogo.adicionar(nota)
            self.remover()

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        eixo = pygame.Vector2(14, 0).rotate(self.tempo * 900)
        cor = self.aura or self.COR
        sup = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(sup, (*cor, 70), (30, 30), 24)               # brilho
        tela.blit(sup, sup.get_rect(center=(round(centro.x), round(centro.y))))
        pygame.draw.line(tela, (60, 30, 60), centro - eixo, centro + eixo, 9)
        pygame.draw.line(tela, cor, centro - eixo, centro + eixo, 5)
        pygame.draw.line(tela, (255, 240, 250), centro - eixo * 0.6, centro + eixo * 0.6, 2)


# ------------------------------------------------------------------ Mapa do Campus

class AlfineteDoMapa(Efeito):
    """"Você está aqui!": um aviso no chão e, depois de um instante, um alfinete cai do céu e fere quem está perto."""

    camada = 3
    ATRASO = 0.6
    ALTURA_DA_QUEDA = 220

    def __init__(self, posicao, raio, dano, atraso=0.0):
        super().__init__(posicao, atraso + self.ATRASO + 0.25, raio)
        self.dano = dano
        self.espera = atraso                 # no GPS, os alfinetes caem em sequência
        self.caiu = False

    def esta_visivel(self, camera):
        return True

    @property
    def queda(self):
        """0 enquanto não começou a cair, 1 quando o alfinete toca o chão."""
        return max(0.0, min(1.0, (self.tempo - self.espera) / self.ATRASO))

    def ao_atualizar(self, dt, jogo):
        if self.caiu or self.queda < 1:
            return
        self.caiu = True
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            jogo.causar_dano(inimigo, self.dano, inimigo.posicao - self.posicao)

    def desenhar(self, tela, camera):
        if self.tempo < self.espera:
            return
        centro = camera.para_tela(self.posicao)
        cor = self.aura or (230, 50, 60)
        sup = pygame.Surface((self.raio * 2 + 4, self.raio * 2 + 4), pygame.SRCALPHA)
        meio = self.raio + 2
        pygame.draw.circle(sup, (*cor, 60 if not self.caiu else 120), (meio, meio), self.raio)
        pygame.draw.circle(sup, (*cor, 200), (meio, meio), self.raio, 2)
        tela.blit(sup, sup.get_rect(center=(round(centro.x), round(centro.y))))
        topo = centro - (0, self.ALTURA_DA_QUEDA * (1 - self.queda))
        x, y = round(topo.x), round(topo.y)
        pygame.draw.polygon(tela, (60, 20, 20), [(x - 9, y - 18), (x + 9, y - 18), (x, y)])
        pygame.draw.circle(tela, (60, 20, 20), (x, y - 22), 11)
        pygame.draw.circle(tela, cor, (x, y - 22), 9)
        pygame.draw.circle(tela, (255, 255, 255), (x, y - 22), 3)


# ------------------------------------------------------------------ Corrente de WhatsApp

class ElosDaCorrente(Efeito):
    """As linhas entre quem a corrente do WhatsApp acertou, piscando por um instante."""

    camada = 3

    def __init__(self, pontos, cor=(70, 210, 100), duracao=0.3):
        super().__init__(pontos[0], duracao)
        self.pontos = [pygame.Vector2(p) for p in pontos]
        self.cor = cor

    def esta_visivel(self, camera):
        return True

    def desenhar(self, tela, camera):
        if len(self.pontos) < 2:
            return
        na_tela = [camera.para_tela(p) for p in self.pontos]
        cor = self.aura or self.cor
        pygame.draw.lines(tela, (20, 40, 20), False, na_tela, 6)
        pygame.draw.lines(tela, cor, False, na_tela, 3)
        for ponto in na_tela[1:]:
            pygame.draw.circle(tela, cor, (round(ponto.x), round(ponto.y)), 6)


def corrente(jogo, origem, alcance_inicial, saltos, alcance_do_salto, ao_acertar):
    """Acerta o inimigo mais perto de `origem` e pula de inimigo em inimigo, sem repetir. Chama `ao_acertar` em
    cada um e devolve os pontos do caminho (para desenhar os elos), ou [] se não havia ninguém."""
    alvo = jogo.inimigo_mais_proximo(origem, alcance_inicial)
    if alvo is None:
        return []
    pontos, atingidos = [pygame.Vector2(origem)], set()
    while alvo is not None and len(atingidos) <= saltos:
        atingidos.add(alvo)
        pontos.append(pygame.Vector2(alvo.posicao))
        ao_acertar(alvo)
        perto = [i for i in jogo.inimigos_proximos(alvo.posicao, alcance_do_salto)
                 if i not in atingidos and i.ativo and i.ALVO_DA_MIRA]
        alvo = min(perto, key=lambda i: i.posicao.distance_squared_to(pontos[-1]), default=None)
    return pontos


def mais_cheio(jogo, origem, alcance, raio=150):
    """A posição do inimigo com mais vizinhos em volta (o maior bolo), dentro do alcance, ou None."""
    perto = [e for e in jogo.inimigos_proximos(origem, alcance) if e.ALVO_DA_MIRA]
    if not perto:
        return None
    return max(perto, key=lambda e: len(jogo.inimigos_proximos(e.posicao, raio))).posicao
