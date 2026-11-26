"""Fases: linha do tempo de inimigos, mini-chefes e chefe."""
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

import pygame

from jogo.config import ALTURA, DURACAO_PROVA, LARGURA, MAX_INIMIGOS
from jogo.inimigos.fabrica import FabricaDeInimigos


@dataclass
class EventoDaFase:
    tempo: float
    acao: Callable
    descricao: str = ""
    executado: bool = field(default=False)


class Fase(ABC):
    NOME = "Fase"
    MATERIA = ""                   # o que aparece em "Aprovado em ..." e "Reprovado em ..."
    DURACAO = DURACAO_PROVA
    APRESENTACOES = ()
    INTERVALO_NASCIMENTO = 0.5
    INICIO_DIFICULDADE = 0        # segundos "já jogados": provas seguintes começam mais difíceis
    MULT_MOEDAS = 1.0             # provas mais adiantadas pagam mais moedas
    PASSO_DIFICULDADE = 180       # segundos para a dificuldade subir 1 ponto

    def __init__(self):
        self.tempo = 0.0
        self.ativos = []
        self.pesos = []               # peso de cada nome em `ativos` no sorteio de quem nasce
        self._apresentados = 0
        self._espera = 0.0
        self.chefe_apareceu = False
        self.greve = 0.0              # segundos de greve restantes: sem inimigos novos, chuva de notas
        self._espera_nota = 0.0
        self.eventos = sorted(self.criar_eventos(), key=lambda e: e.tempo)

    @abstractmethod
    def criar_eventos(self):
        """Lista de EventoDaFase (mini-chefes, formações, chefe)."""

    @property
    def escala_dificuldade(self):
        return 1 + (self.INICIO_DIFICULDADE + self.tempo) / self.PASSO_DIFICULDADE

    def alvo_de_inimigos(self):
        alvo = 10 + (self.INICIO_DIFICULDADE + self.tempo) * 0.5
        if self.chefe_apareceu:
            alvo *= 0.5
        return min(MAX_INIMIGOS, int(alvo))

    def atualizar(self, dt, jogo):
        self.tempo += dt
        while self._apresentados < len(self.APRESENTACOES) and \
                self.APRESENTACOES[self._apresentados][0] <= self.tempo:
            apresentacao = self.APRESENTACOES[self._apresentados]
            self.ativos.append(apresentacao[1])
            self.pesos.append(apresentacao[2] if len(apresentacao) > 2 else 1.0)
            self._apresentados += 1
        for evento in self.eventos:
            if not evento.executado and evento.tempo <= self.tempo:
                evento.executado = True
                evento.acao(jogo)
        self._atualizar_greve(dt, jogo)
        self._espera -= dt
        if self._espera <= 0 and self.ativos and self.greve <= 0:
            self._espera = self.INTERVALO_NASCIMENTO
            if len(jogo.inimigos) < self.alvo_de_inimigos():
                self.nascer(jogo, jogo.rng.choices(self.ativos, weights=self.pesos)[0])

    def adiantar_para(self, tempo):
        """Pula a linha do tempo até `tempo` sem executar o que ficou para trás (modo treino)."""
        self.tempo = tempo
        for evento in self.eventos:
            if evento.tempo < tempo:
                evento.executado = True

    def nascer(self, jogo, nome, quantidade=None):
        classe = FabricaDeInimigos.classe(nome)
        quantidade = quantidade or classe.sortear_tamanho_do_grupo(jogo.rng)
        centro = self.posicao_de_nascimento(jogo)
        for _ in range(quantidade):
            espalhar = pygame.Vector2(jogo.rng.uniform(-40, 40), jogo.rng.uniform(-40, 40))
            jogo.adicionar(FabricaDeInimigos.criar(nome, centro + espalhar, self.escala_dificuldade))

    @staticmethod
    def posicao_de_nascimento(jogo):
        """Um ponto logo fora da tela, em volta do herói, dentro da arena e fora dos prédios."""
        distancia = math.hypot(LARGURA, ALTURA) / 2 + 80
        p = pygame.Vector2(jogo.jogador.posicao)
        for tentativa in range(30):
            angulo = jogo.rng.uniform(0, 2 * math.pi)
            p = jogo.jogador.posicao + pygame.Vector2(math.cos(angulo), math.sin(angulo)) * (distancia + tentativa * 10)
            p.x = max(jogo.arena.left + 30, min(p.x, jogo.arena.right - 30))
            p.y = max(jogo.arena.top + 30, min(p.y, jogo.arena.bottom - 30))
            if not jogo.mapa.bloqueado(p, 30):
                return p
        return jogo.mapa.empurrar(p, 30)

    def avisar_formacao(self, jogo, tipo, nome, quantidade):
        """Mostra setas na borda da tela e só depois de AVISO s cria o cerco ou a parede."""
        from jogo.efeitos import AvisoDeFormacao
        if tipo == "parede":
            lado = jogo.rng.choice((-1, 1))
            jogo.adicionar(AvisoDeFormacao((lado,), self.AVISO, lambda: self.formacao_parede(jogo, nome, quantidade, lado)))
            jogo.anunciar("Lá vem a turma!", 1.5)
        else:
            jogo.adicionar(AvisoDeFormacao((-1, 1, -2, 2), self.AVISO,
                                           lambda: self.formacao_circulo(jogo, nome, quantidade)))
            jogo.anunciar("Vão te cercar!", 1.5)

    AVISO = 1.2

    def formacao_circulo(self, jogo, nome, quantidade, raio=560):
        for i in range(quantidade):
            direcao = pygame.Vector2(1, 0).rotate(360 * i / quantidade)
            jogo.adicionar(FabricaDeInimigos.criar(nome, jogo.jogador.posicao + direcao * raio,
                                                   self.escala_dificuldade))

    def formacao_parede(self, jogo, nome, quantidade, lado=None):
        lado = lado or jogo.rng.choice((-1, 1))
        x = jogo.jogador.posicao.x + lado * (LARGURA / 2 + 60)
        for i in range(quantidade):
            y = jogo.jogador.posicao.y + (i - (quantidade - 1) / 2) * 36
            jogo.adicionar(FabricaDeInimigos.criar(nome, (x, y), self.escala_dificuldade))

    DURACAO_GREVE = 30.0
    INTERVALO_NOTA_GREVE = 0.5
    VALOR_NOTA_GREVE = 2

    def iniciar_greve(self, jogo):
        """Evento Greve: sem aula por um tempo. Ninguém novo aparece e chovem notas."""
        self.greve = self.DURACAO_GREVE
        self._espera_nota = 0.0
        for inimigo in jogo.inimigos:
            inimigo.assustar(4.0)
        jogo.anunciar("GREVE! Sem aula por 30 s", 3)

    def _atualizar_greve(self, dt, jogo):
        if self.greve <= 0:
            return
        self.greve -= dt
        if self.greve <= 0:
            jogo.marcos.add("greve")
            jogo.anunciar("Fim da greve: volta às aulas", 2.5)
            return
        self._espera_nota -= dt
        if self._espera_nota <= 0:
            self._espera_nota = self.INTERVALO_NOTA_GREVE
            angulo = jogo.rng.uniform(0, 2 * math.pi)
            distancia = jogo.rng.uniform(120, 380)
            posicao = jogo.jogador.posicao + pygame.Vector2(math.cos(angulo), math.sin(angulo)) * distancia
            jogo.soltar_nota(jogo.mapa.empurrar(posicao, 12), self.VALOR_NOTA_GREVE)

    def chamar_monitor(self, jogo):
        monitor = FabricaDeInimigos.criar("monitor_possuido", self.posicao_de_nascimento(jogo), self.escala_dificuldade)
        jogo.adicionar(monitor)
        jogo.anunciar("Mini-chefe: Monitor Possuído!", 3)

    def chamar_mini_chefe(self, jogo, nome):
        gigante = FabricaDeInimigos.criar_gigante(nome, self.posicao_de_nascimento(jogo), self.escala_dificuldade)
        jogo.adicionar(gigante)
        jogo.anunciar(f"Mini-chefe: {gigante.NOME} Gigante!", 3)

    DISTANCIA_SEM_PREDIO = 900     # mapa sem o prédio do mini-chefe: o círculo fica a esta distância do início

    def abrir_invocacao(self, jogo, nome, anunciar=True):
        """Põe no mapa o círculo de invocação de um mini-chefe opcional (se ele já não estiver por lá)."""
        from jogo.invocacao import LocalDeInvocacao
        classe = FabricaDeInimigos.classe(nome)
        if any(m.NOME == classe.NOME for m in jogo.marcadores()):
            return None
        posicao = jogo.mapa.local_de(classe.LOCAL) if classe.LOCAL else None
        if posicao is None and classe.PONTO is not None and jogo.arena.collidepoint(classe.PONTO):
            posicao = jogo.mapa.empurrar(classe.PONTO, 100)
        if posicao is None:
            rumo = pygame.Vector2(self.DISTANCIA_SEM_PREDIO, 0).rotate(jogo.rng.uniform(0, 360))
            posicao = jogo.mapa.inicio + rumo
            posicao.x = max(jogo.arena.left + 120, min(posicao.x, jogo.arena.right - 120))
            posicao.y = max(jogo.arena.top + 120, min(posicao.y, jogo.arena.bottom - 120))
            posicao = jogo.mapa.empurrar(posicao, 100)
        local = LocalDeInvocacao(posicao, nome)
        jogo.adicionar(local)
        if anunciar and not classe.SECRETO:
            jogo.anunciar(f"{classe.NOME} apareceu {classe.ONDE}!  [M] mapa", 4)
        return local

    ABERTURA_DAS_INVOCACOES = 2.0   # segundos de partida até os círculos dos mini-chefes aparecerem

    def abrir_invocacoes(self, jogo):
        """Espalha pelo campus os círculos de todos os mini-chefes, uma vez só por partida: eles ficam
        disponíveis desde o começo e quem decide a hora de enfrentar cada um é o aluno."""
        from jogo.inimigos.mini_chefes import MINI_CHEFES
        if jogo.invocacoes_abertas:
            return
        jogo.invocacoes_abertas = True
        for nome in MINI_CHEFES:
            self.abrir_invocacao(jogo, nome, anunciar=False)
        jogo.anunciar("Os mini-chefes estão pelo campus  [M] mapa", 4)

    def chamar_chefe(self, jogo, nome):
        self.chefe_apareceu = True
        jogo.iniciar_chefe(FabricaDeInimigos.criar(nome, self.posicao_de_nascimento(jogo)))


class Prova(Fase):
    """Fase descrita só por dados: quem aparece e quando, formações, mini-chefes e o chefe.

    Cada prova do semestre é uma subclasse que só preenche as constantes abaixo.
    """

    @property
    @abstractmethod
    def CHEFE(self):
        """Nome do chefe na FabricaDeInimigos. Cada prova define como constante de classe."""

    ROTULO = ""                  # nome curto, para o menu de treino
    NIVEL_TREINO = 1             # nível típico do aluno quando o chefe chega (treino direto no chefe)
    FORMACOES = ()               # um lacaio por minuto, alternando círculo e parede
    AVISO_DO_CHEFE = 3.0         # segundos de "PERIGO!" na tela antes do chefe chegar
    MINI_CHEFES = ()             # (segundos, nome do lacaio que vira gigante)
    GREVE = None                 # segundos em que começa a greve (None: sem greve)
    MONITOR = None               # segundos em que chega o Monitor Possuído (None: não vem)

    def criar_eventos(self):
        eventos = [EventoDaFase(tempo, lambda jogo, n=nome: self.chamar_mini_chefe(jogo, n), f"{nome} gigante")
                   for tempo, nome in self.MINI_CHEFES]
        eventos.append(EventoDaFase(self.ABERTURA_DAS_INVOCACOES, self.abrir_invocacoes, "Mini-chefes no mapa"))
        eventos.append(EventoDaFase(self.DURACAO, lambda jogo: self.chamar_chefe(jogo, self.CHEFE), "Chefe"))
        eventos.append(EventoDaFase(self.DURACAO - self.AVISO_DO_CHEFE,
                                    lambda jogo: jogo.avisar_perigo(self.AVISO_DO_CHEFE), "Aviso do chefe"))
        if self.GREVE is not None:
            eventos.append(EventoDaFase(self.GREVE, self.iniciar_greve, "Greve"))
        if self.MONITOR is not None:
            eventos.append(EventoDaFase(self.MONITOR, self.chamar_monitor, "Monitor Possuído"))
        for i, nome in enumerate(self.FORMACOES):
            if i % 2 == 0:
                acao = lambda jogo, n=nome: self.avisar_formacao(jogo, "circulo", n, 24)
            else:
                acao = lambda jogo, n=nome: self.avisar_formacao(jogo, "parede", n, 20)
            eventos.append(EventoDaFase(60 * (i + 1) - self.AVISO, acao, f"Formação de {nome}"))
        return eventos

    def adiantar_para_o_chefe(self):
        """Modo treino: começa a prova poucos segundos antes do chefe chegar."""
        self.adiantar_para(self.DURACAO - self.AVISO_DO_CHEFE)


class ProvaDeCalculo(Prova):
    NOME = "1ª prova: Cálculo I"
    MATERIA = "Cálculo I"
    CHEFE = "chefe_calculo"
    ROTULO = "Cálculo I"
    NIVEL_TREINO = 7
    INICIO_DIFICULDADE = 0
    APRESENTACOES = (          # (segundos, inimigo, peso no sorteio): os da matéria aparecem mais
        (0, "bug", 2.0),
        (30, "calculadora", 3.0),
        (70, "pi", 3.0),
        (110, "caixinha", 1.0),
        (170, "mouse", 1.0),
    )
    FORMACOES = ("bug", "calculadora", "pi", "calculadora")
    MINI_CHEFES = ((150, "calculadora"),)
    GREVE = 200


class ProvaDeArquiteturaEED(Prova):
    NOME = "2ª prova: Arquitetura e Estrutura de Dados"
    MATERIA = "Arquitetura de Computadores e Estrutura de Dados em C"
    CHEFE = "chefe_arquitetura_ed"
    ROTULO = "Arquitetura -> Estrutura de Dados em C"
    NIVEL_TREINO = 11
    INICIO_DIFICULDADE = 240
    MULT_MOEDAS = 1.2
    APRESENTACOES = (
        (0, "bug", 2.0),
        (0, "mouse", 2.0),
        (30, "pente_ram", 3.0),
        (70, "ponteiro", 3.0),
        (110, "pilha", 2.0),
        (170, "calculadora", 0.5),
    )
    FORMACOES = ("mouse", "ponteiro", "pente_ram", "pilha")
    MINI_CHEFES = ((150, "pente_ram"),)
    GREVE = 210
    MONITOR = 100


class ProvaDeTDEPOO(Prova):
    NOME = "3ª prova: Transformação Digital e POO"
    MATERIA = "Transformação Digital e Programação Orientada a Objetos"
    CHEFE = "chefe_td_poo"
    ROTULO = "Transformação Digital -> POO"
    NIVEL_TREINO = 14
    INICIO_DIFICULDADE = 480
    MULT_MOEDAS = 1.4
    APRESENTACOES = (
        (0, "bug", 2.0),
        (0, "caixinha", 3.0),
        (30, "pi", 1.0),
        (60, "ponteiro", 2.0),
        (90, "pilha", 1.0),
        (120, "mouse", 1.0),
        (150, "pente_ram", 1.0),
        (180, "calculadora", 1.0),
    )
    FORMACOES = ("caixinha", "bug", "ponteiro", "caixinha")
    MINI_CHEFES = ((120, "caixinha"), (210, "ponteiro"))
    GREVE = 165
    MONITOR = 75


PROVAS = (ProvaDeCalculo, ProvaDeArquiteturaEED, ProvaDeTDEPOO)


def semestre():
    """As três provas em ordem, cada uma uma instância nova."""
    return [classe() for classe in PROVAS]
