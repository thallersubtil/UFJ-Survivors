"""Fases: linha do tempo de inimigos, mini-chefes e chefes. O jogo tem uma só, o Semestre."""
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

import pygame

from jogo.config import ALTURA, DURACAO_SEMESTRE, LARGURA, MAX_INIMIGOS
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
    DURACAO = DURACAO_SEMESTRE
    APRESENTACOES = ()
    INTERVALO_NASCIMENTO = 0.5    # segundos entre um grupo e outro no começo da partida
    INTERVALO_MINIMO = 0.1        # o intervalo encurta com o tempo, mas nunca passa disto
    TEMPO_PARA_DOBRAR = 240       # segundos de partida para os grupos nascerem duas vezes mais rápido
    ALVO_INICIAL = 10             # inimigos em campo no primeiro segundo
    ALVO_POR_SEGUNDO = 0.3        # quantos a mais a cada segundo de partida...
    ALVO_ACELERACAO = 1.5         # ...e mais isto vezes (minutos de partida)²: o começo é calmo, o fim enche a tela
    PASSO_DIFICULDADE = 400       # segundos para a dificuldade subir 1 ponto

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

    provas = ()                   # as ProvaMarcada desta fase (o Semestre tem o calendário)
    AVISO_DO_FIM = 30.0           # segundos antes do fim em que o aviso aparece (e o relógio fica vermelho)

    @property
    def titulo(self):
        """O que o HUD mostra embaixo do relógio."""
        return self.NOME

    @property
    def prova_em_curso(self):
        """A prova cujo chefe ainda vai chegar, ou None."""
        return None

    @property
    def restante(self):
        """Segundos até o fim do semestre (zero depois disso): o relógio do HUD conta para trás."""
        return max(0.0, self.DURACAO - self.tempo)

    @property
    def escala_dificuldade(self):
        """Quanto vida, dano e velocidade dos inimigos que nascem agora crescem sobre o valor base."""
        return 1 + self.tempo / self.PASSO_DIFICULDADE

    @property
    def furia(self):
        """Multiplicador extra de dano e velocidade de quem nasce agora (1 = nenhum). O Semestre usa no fim."""
        return 1.0

    def alvo_de_inimigos(self):
        """Quantos inimigos a fase quer em campo agora: cresce com o tempo, até o teto."""
        tempo = self.tempo
        alvo = self.ALVO_INICIAL + tempo * self.ALVO_POR_SEGUNDO + self.ALVO_ACELERACAO * (tempo / 60) ** 2
        return min(MAX_INIMIGOS, int(alvo))

    def alvo_com(self, jogo):
        """O alvo deste instante, aliviado enquanto houver chefe ou mini-chefe vivo em campo."""
        return int(self.alvo_de_inimigos() * jogo.alivio_de_nascimento)

    def intervalo_de_nascimento(self):
        """Segundos entre um grupo e o próximo: quanto mais tarde na partida, mais rápido eles chegam."""
        intervalo = self.INTERVALO_NASCIMENTO / (1 + self.tempo / self.TEMPO_PARA_DOBRAR)
        return max(self.INTERVALO_MINIMO, intervalo)

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
            self._espera = self.intervalo_de_nascimento()
            if len(jogo.inimigos) < self.alvo_com(jogo):
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
            jogo.adicionar(self.criar(nome, centro + espalhar))

    def criar(self, nome, posicao):
        """Um lacaio com a força deste instante da fase (escala e fúria)."""
        inimigo = FabricaDeInimigos.criar(nome, posicao, self.escala_dificuldade)
        inimigo.enfurecer(self.furia)
        return inimigo

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
            jogo.adicionar(self.criar(nome, jogo.jogador.posicao + direcao * raio))

    def formacao_parede(self, jogo, nome, quantidade, lado=None):
        lado = lado or jogo.rng.choice((-1, 1))
        x = jogo.jogador.posicao.x + lado * (LARGURA / 2 + 60)
        for i in range(quantidade):
            y = jogo.jogador.posicao.y + (i - (quantidade - 1) / 2) * 36
            jogo.adicionar(self.criar(nome, (x, y)))

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

    def chamar_mini_chefe(self, jogo, nome):
        gigante = FabricaDeInimigos.criar_gigante(nome, self.posicao_de_nascimento(jogo), self.escala_dificuldade)
        gigante.enfurecer(self.furia)
        jogo.adicionar(gigante)
        jogo.anunciar(f"Mini-chefe: {gigante.NOME} Gigante!", 3)

    DISTANCIA_SEM_PREDIO = 900     # mapa sem o prédio do mini-chefe: o círculo fica a esta distância do início

    def abrir_invocacao(self, jogo, nome, anunciar=True):
        """Põe no mapa o círculo de invocação de um mini-chefe opcional (se ele já não estiver por lá)."""
        from jogo.invocacao import LocalDeInvocacao
        classe = FabricaDeInimigos.classe(nome)
        if any(m.CHAVE == nome for m in jogo.marcadores()):
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
        posicao = self._longe_do_inicio(jogo, posicao)
        local = LocalDeInvocacao(posicao, nome)
        local.revelado = jogo.mini_chefe_conhecido(nome)
        jogo.adicionar(local)
        if anunciar and not classe.SECRETO:
            jogo.anunciar(f"{local.NOME} apareceu {classe.ONDE}!  [M] mapa", 4)
        return local

    LONGE_DO_INICIO = 900          # nenhum círculo a menos disto de onde o aluno nasce (não se invoca sem querer)

    def _longe_do_inicio(self, jogo, posicao):
        """Afasta do ponto de partida o círculo que caiu perto dele, na mesma direção, sem entrar em prédio."""
        de_la = pygame.Vector2(posicao) - jogo.mapa.inicio
        if de_la.length() >= self.LONGE_DO_INICIO:
            return pygame.Vector2(posicao)
        if de_la.length_squared() < 1:
            de_la = pygame.Vector2(1, 0)
        distancia = self.LONGE_DO_INICIO + 20
        for _ in range(12):
            ponto = jogo.mapa.empurrar(jogo.mapa.inicio + de_la.normalize() * distancia, 100)
            if ponto.distance_to(jogo.mapa.inicio) >= self.LONGE_DO_INICIO and jogo.arena.collidepoint(ponto):
                return ponto
            de_la.rotate_ip(30)
        return ponto

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

    def chamar_chefe(self, jogo, prova):
        """Põe em campo o chefe da `prova` (uma ProvaMarcada). O relógio segue: quem decide quando o
        próximo vem é a hora dele, não a queda deste."""
        self.chefe_apareceu = True
        jogo.iniciar_chefe(FabricaDeInimigos.criar(prova.chefe, self.posicao_de_nascimento(jogo)), prova)


@dataclass(frozen=True)
class ProvaMarcada:
    """Uma prova do calendário: a hora em que o chefe chega e o que mostrar dela nas telas."""
    hora: float              # segundos de partida em que o chefe chega
    chefe: str               # nome do chefe na FabricaDeInimigos
    materia: str             # o que aparece em "Aprovado em ..." e "Reprovado em ..."
    rotulo: str              # nome curto, para o boletim, o calendário e o menu de treino
    nivel_treino: int        # nível típico do aluno quando o chefe chega (treino direto no chefe)
    curto: str               # nome curtinho, para o calendário da pausa
    inicio: float = 0.0      # quando a prova começa a "correr" (a hora da anterior): para a nota de quem cai antes


CALENDARIO = (
    ProvaMarcada(5 * 60, "chefe_calculo", "Cálculo I", "Cálculo I", 7, "Cálculo I"),
    ProvaMarcada(10 * 60, "chefe_arquitetura_ed", "Arquitetura de Computadores e Estrutura de Dados em C",
                 "Arquitetura -> Estrutura de Dados em C", 10, "Arquitetura e ED", inicio=5 * 60),
    ProvaMarcada(15 * 60, "chefe_td_poo", "Transformação Digital e Programação Orientada a Objetos",
                 "Transformação Digital -> POO", 13, "TD e POO", inicio=10 * 60),
)


class Semestre(Fase):
    """O semestre inteiro numa linha do tempo só: os lacaios de cada matéria entram perto do chefe dela,
    os três chefes chegam com hora marcada (o relógio não para na luta) e, das 15:00 em diante, a
    dificuldade dispara até ninguém passar muito dos 20:00.

    Para o treino, `provas` pode ser só a prova escolhida: a fase chama apenas aquele chefe.
    """

    NOME = "Semestre"
    AVISO_DO_CHEFE = 3.0         # segundos de "PERIGO!" na tela antes de cada chefe
    APRESENTACOES = (            # (segundos, inimigo, peso no sorteio): cada matéria perto do seu chefe
        (0, "bug", 2.0),
        (30, "calculadora", 3.0),
        (70, "pi", 3.0),
        (110, "caixinha", 1.0),
        (170, "mouse", 1.0),
        (320, "pente_ram", 3.0),
        (370, "ponteiro", 3.0),
        (420, "pilha", 2.0),
    )
    FORMACOES = (                # (segundos, lacaio): alternando cerco e parede, uma a cada ~90 s
        (90, "bug"), (180, "calculadora"), (270, "pi"), (390, "mouse"), (480, "ponteiro"),
        (570, "pente_ram"), (690, "caixinha"), (780, "pilha"), (870, "bug"),
    )
    GIGANTES = ((180, "calculadora"), (480, "pente_ram"), (780, "caixinha"))   # lacaios gigantes com hora marcada
    GREVE = 450                  # 7:30, longe das horas dos chefes

    INICIO_DA_RETA_FINAL = 15 * 60     # daqui em diante a dificuldade multiplica (o antigo "modo sem fim")
    APERTO = 18 * 60             # e daqui em diante multiplica mais depressa
    INTERVALO_DE_ONDA = 15.0     # a cada tantos segundos da reta final...
    FATOR_POR_ONDA = 1.15        # ...a dificuldade é multiplicada por isto
    FATOR_NO_APERTO = 1.3        # ...ou por isto, depois do APERTO
    FURIA_POR_SEGUNDO = 1.35     # depois dos 20:00, dano e velocidade de quem nasce multiplicam por isto a cada segundo
    INTERVALO_FORMACAO_FINAL = 45.0    # na reta final, um cerco ou uma parede de tanto em tanto tempo
    INTERVALO_GIGANTE_FINAL = 60.0     # e um gigante

    def __init__(self, provas=CALENDARIO):
        self.provas = tuple(provas)           # antes do super(): criar_eventos usa
        super().__init__()
        self._formacoes_finais = 0           # cercos e paredes já chamados na reta final
        self._gigantes_finais = 0

    def criar_eventos(self):
        eventos = [EventoDaFase(self.ABERTURA_DAS_INVOCACOES, self.abrir_invocacoes, "Mini-chefes no mapa"),
                   EventoDaFase(self.GREVE, self.iniciar_greve, "Greve")]
        for prova in self.provas:
            eventos.append(EventoDaFase(prova.hora - self.AVISO_DO_CHEFE,
                                        lambda jogo: jogo.avisar_perigo(self.AVISO_DO_CHEFE), "Aviso do chefe"))
            eventos.append(EventoDaFase(prova.hora, lambda jogo, p=prova: self.chamar_chefe(jogo, p), prova.rotulo))
        for tempo, nome in self.GIGANTES:
            eventos.append(EventoDaFase(tempo, lambda jogo, n=nome: self.chamar_mini_chefe(jogo, n), f"{nome} gigante"))
        for i, (tempo, nome) in enumerate(self.FORMACOES):
            tipo, quantidade = ("circulo", 24) if i % 2 == 0 else ("parede", 20)
            eventos.append(EventoDaFase(tempo - self.AVISO, lambda jogo, n=nome, t=tipo, q=quantidade:
                                        self.avisar_formacao(jogo, t, n, q), f"Formação de {nome}"))
        eventos.append(EventoDaFase(self.INICIO_DA_RETA_FINAL,
                                    lambda jogo: jogo.anunciar("Reta final: a dificuldade só sobe daqui em diante!", 4),
                                    "Reta final"))
        eventos.append(EventoDaFase(self.DURACAO - self.AVISO_DO_FIM,
                                    lambda jogo: jogo.anunciar("Faltam 30 s para o fim do semestre!", 4),
                                    "Aviso do fim"))
        eventos.append(EventoDaFase(self.DURACAO, lambda jogo: jogo.anunciar("O semestre acabou!", 4), "Fim"))
        return eventos

    @property
    def reta_final(self):
        return self.tempo >= self.INICIO_DA_RETA_FINAL

    @property
    def escala_dificuldade(self):
        """Cresce em linha até as 15:00; na reta final multiplica a cada onda, mais depressa depois das 18:00."""
        base = 1 + min(self.tempo, self.INICIO_DA_RETA_FINAL) / self.PASSO_DIFICULDADE
        ondas = max(0.0, min(self.tempo, self.APERTO) - self.INICIO_DA_RETA_FINAL) / self.INTERVALO_DE_ONDA
        ondas_no_aperto = max(0.0, self.tempo - self.APERTO) / self.INTERVALO_DE_ONDA
        return base * self.FATOR_POR_ONDA ** int(ondas) * self.FATOR_NO_APERTO ** int(ondas_no_aperto)

    @property
    def furia(self):
        """Depois dos 20:00, dano e velocidade de quem nasce disparam: fugir, rolar e desviar deixam de bastar."""
        return self.FURIA_POR_SEGUNDO ** max(0.0, self.tempo - self.DURACAO)

    def alvo_de_inimigos(self):
        return MAX_INIMIGOS if self.tempo >= self.DURACAO else super().alvo_de_inimigos()

    def alvo_com(self, jogo):
        return self.alvo_de_inimigos() if self.tempo >= self.DURACAO else super().alvo_com(jogo)

    @property
    def prova_em_curso(self):
        return next((p for p in self.provas if p.hora > self.tempo), None)

    @property
    def titulo(self):
        prova = self.prova_em_curso
        if prova is None:
            return "Reta final"
        return f"{CALENDARIO.index(prova) + 1}ª prova: {prova.rotulo.replace(' -> ', ' e ')}" \
            if prova in CALENDARIO else prova.rotulo

    def adiantar_para_a_prova(self, prova):
        """Modo treino: começa poucos segundos antes de o chefe da `prova` chegar."""
        self.adiantar_para(prova.hora - self.AVISO_DO_CHEFE)

    def atualizar(self, dt, jogo):
        super().atualizar(dt, jogo)
        if self.tempo >= self.DURACAO:
            for inimigo in jogo.inimigos:        # quem já estava em campo também se enfurece
                inimigo.enfurecer(self.furia)
        if not self.reta_final or not self.ativos:
            return
        decorrido = self.tempo - self.INICIO_DA_RETA_FINAL
        if decorrido >= (self._formacoes_finais + 1) * self.INTERVALO_FORMACAO_FINAL:
            self._formacoes_finais += 1
            tipo = "circulo" if self._formacoes_finais % 2 else "parede"
            self.avisar_formacao(jogo, tipo, jogo.rng.choice(self.ativos), 24)
        if decorrido >= (self._gigantes_finais + 1) * self.INTERVALO_GIGANTE_FINAL:
            self._gigantes_finais += 1
            self.chamar_mini_chefe(jogo, jogo.rng.choice(self.ativos))
