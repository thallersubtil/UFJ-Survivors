"""Base dos chefes: alternam ataques e ficam furiosos com pouca vida."""
from abc import ABC, abstractmethod

import pygame

from jogo.inimigos.acoes_do_chefe import Investida, RaiosPelosOlhos
from jogo.inimigos.inimigo import Inimigo


class Chefe(Inimigo, ABC):
    TENACIDADE = 1.0             # nada puxa, atrasa ou prende um chefe no meio do ataque
    CHANCE_CAFE = 0.0
    CHANCE_POCAO = 0.0
    INTERVALO_ATAQUE = 2.6
    INTERVALO_FURIOSO = 1.6
    DISTANCIA_PREFERIDA = 260
    TEMPO_DO_ATAQUE = 0.6        # segundos da animação "atacar" a cada ataque (se a pasta tiver a tira)
    ALTURA_DO_OLHO = 14          # pixels abaixo do alto da cabeça, no sprite de perfil
    RECUO_DO_OLHO = 3            # pixels para trás da frente do rosto
    _olhos_medidos = {}          # quadro do sprite -> onde fica o olho nele (a partir do centro, olhando à direita)

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, 1.0)
        self.reposiciona = False
        self._espera_ataque = 2.0
        self._indice = 0
        self.acao_atual = None
        self._atacando = 0.0     # segundos que faltam da animação de ataque

    @property
    def furioso(self):
        return self.vida < self.vida_maxima / 2

    @property
    def intervalo_ataque(self):
        """Segundos entre um ataque e o próximo (menos quando furioso)."""
        return self.INTERVALO_FURIOSO if self.furioso else self.INTERVALO_ATAQUE

    @abstractmethod
    def ataques(self):
        """Lista de ataques (funções que recebem o jogo), usados em sequência."""

    def mirar(self, jogo):
        """Direção (vetor unitário) do chefe até o herói."""
        falta = jogo.jogador.posicao - self.posicao
        return falta.normalize() if falta.length_squared() > 0 else pygame.Vector2(1, 0)

    def executar(self, acao):
        """Começa uma ação de várias etapas (AcaoDoChefe). Só o chefe mexe na própria ação atual."""
        self.acao_atual = acao

    def investir(self, vezes=1, **ajustes):
        """Começa uma investida (ou várias seguidas) em direção ao herói."""
        self.executar(Investida(self, vezes, **ajustes))

    def olho_no_quadro(self, quadro):
        """Mede no próprio desenho onde está o olho: na altura dos olhos, logo atrás da frente do rosto.
        Cada quadro da animação tem a cabeça num lugar, então a medida é por quadro (e fica guardada)."""
        if id(quadro) not in Chefe._olhos_medidos:
            mascara = pygame.mask.from_surface(quadro, 128)
            largura, altura = quadro.get_size()
            y = min(altura - 1, quadro.get_bounding_rect().top + self.ALTURA_DO_OLHO)
            frente = max((x for x in range(largura) if mascara.get_at((x, y))), default=largura // 2)
            Chefe._olhos_medidos[id(quadro)] = (frente - self.RECUO_DO_OLHO - largura / 2, y - altura / 2)
        return Chefe._olhos_medidos[id(quadro)]

    def olhos(self):
        """Onde ficam os olhos, no mundo: é exatamente daí que saem os raios. De perfil aparece um olho só;
        o outro fica colado nele."""
        x, y = self.olho_no_quadro(self.animador.quadro_atual)
        lado = -1 if self.olhando_esquerda else 1
        return [self.posicao + ((x + recuo) * lado, y) for recuo in (-1, 1)]

    def fuzilar_com_os_olhos(self, dano, vezes=1):
        """Começa os raios pelos olhos: mira, trava e dispara."""
        self.executar(RaiosPelosOlhos(self, dano, vezes))

    def mover(self, dt, jogo):
        if self.acao_atual is not None:
            if self.acao_atual(dt, jogo):
                self.acao_atual = None
            return
        if self.posicao.distance_to(jogo.jogador.posicao) > self.DISTANCIA_PREFERIDA:
            self.ir_em_direcao(jogo.jogador.posicao, dt)
        self._espera_ataque -= dt
        if self._espera_ataque <= 0:
            lista = self.ataques()
            lista[self._indice % len(lista)](jogo)
            self._indice += 1
            self._espera_ataque = self.intervalo_ataque
            self._atacando = self.TEMPO_DO_ATAQUE

    def atualizar(self, dt, jogo):
        super().atualizar(dt, jogo)
        if self._atacando > 0:                   # o quadro do ataque segue o tempo do ataque, não um relógio
            self._atacando = max(0.0, self._atacando - dt)
            animacao = self.animador.animacoes.get("atacar")
            if animacao is not None and self._atacando > 0:
                indice = min(len(animacao.quadros) - 1,
                             int((1 - self._atacando / self.TEMPO_DO_ATAQUE) * len(animacao.quadros)))
                self.animador.tempo = (indice + 0.5) / animacao.fps

    def escolher_animacao(self):
        """Lançando um ataque, toca a tira "atacar" (quem não tem a tira continua andando)."""
        if self._atacando > 0 and "atacar" in self.animador.animacoes:
            return "atacar"
        return super().escolher_animacao()

    def possuir(self, duracao):
        """Chefes não são possuídos pelo Fusca."""

    def assustar(self, duracao):
        """Professor não cai em trote."""

    def empurrar(self, direcao, forca=180):
        """Chefe não é empurrado: um golpe não tira ele do ataque que está fazendo."""

    def desenhar_corpo(self, tela, camera):
        if self.acao_atual is not None and not self.acao_atual.POR_CIMA:
            self.acao_atual.desenhar_aviso(tela, camera)
        super().desenhar_corpo(tela, camera)
        if self.acao_atual is not None and self.acao_atual.POR_CIMA:
            self.acao_atual.desenhar_aviso(tela, camera)
