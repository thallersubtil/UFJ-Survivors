"""A partida: contém o Jogador, a Fase, o Placar e todas as entidades."""
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import pygame

from jogo.boletim import Boletim

from jogo.cenario import Cenario
from jogo.coletaveis.coletaveis import Moeda, Nota
from jogo.config import (ALTURA, BONUS_67_DURACAO, BONUS_67_VELOCIDADE, LARGURA,
                         LIMITE_COLETAVEIS, LIMITE_EFEITOS, MAX_INIMIGOS, SORTEIOS_POR_PARTIDA, BANIMENTOS_POR_PARTIDA, Cor)
from jogo.efeitos import TextoFlutuante
from jogo.fase import Semestre
from jogo.jogador.bonus import BonusTemporario
from jogo.mapa import MapaUFJ
from jogo.nucleo.camera import Camera
from jogo.nucleo.grade import GradeEspacial
from jogo.nucleo.recursos import Recursos
from jogo.placar import Placar
from jogo.progressao import Progressao
from jogo.ranking import RegistroRanking

import jogo.inimigos  # noqa: F401  (registra todos os inimigos na fábrica)
from jogo.inimigos.quebraveis import QUEBRAVEIS


@dataclass
class Entrada:
    direcao: pygame.Vector2 = field(default_factory=pygame.Vector2)
    mira: Optional[pygame.Vector2] = None
    segurando_especial: bool = False     # Espaço apertado (a Virada de Noite atira enquanto segura)


class Jogo:
    MARGEM_BUSCA = 64

    CURA_ENTRE_PROVAS = 0.5      # fração da vida máxima recuperada quando um chefe cai
    MOEDAS_POR_PROVA = 150       # bônus de moedas a cada prova aprovada
    MOEDAS_POR_MINUTO = 6        # bolsa pelo tempo sobrevivido, paga no fim
    BONUS_HONRAS = 400           # fim do semestre com honras (os três chefes derrotados): bônus pago no fim...
    MOEDAS_POR_MINI_CHEFE = 40   # ...mais isto por mini-chefe derrotado na partida
    QUEBRAVEIS_NO_INICIO = 80    # caixas, lixeiras e vasos espalhados pelo campus quando a partida começa (não voltam)
    ESPACO_ENTRE_QUEBRAVEIS = 320    # distância mínima entre dois deles
    LONGE_DO_ALUNO = 900         # nenhum nasce na tela de onde o aluno começa
    FOLGA_DO_QUEBRAVEL = 40      # espaço livre de prédio em volta do objeto

    def __init__(self, classe_jogador, fase=None, semente=None, mapa=None):
        self.rng = random.Random(semente)
        self.mapa = mapa or MapaUFJ.carregar(self.rng) or Cenario(rng=self.rng)
        self.arena = self.mapa.arena
        self.jogador = classe_jogador(self.mapa.inicio)
        self.treino = False
        self.fase = fase if fase is not None else Semestre()
        self.placar = Placar()
        self.camera = Camera(LARGURA, ALTURA, self.arena)
        self.entrada = Entrada()
        self.grade = GradeEspacial(96)
        self.entidades = []
        self.grupos = defaultdict(list)
        self._novas = []
        self.niveis_pendentes = 0
        self.baus_pendentes = 0
        self.sorteios_restantes = SORTEIOS_POR_PARTIDA
        self.banimentos_restantes = BANIMENTOS_POR_PARTIDA
        self.chefes = []                 # chefes em campo, do mais antigo para o mais novo (podem ser dois)
        self._prova_de = {}              # chefe -> ProvaMarcada que ele encerra (a nota vai para ela)
        self.chefe_a_apresentar = None   # chefe que acabou de chegar e ainda não foi apresentado (a cena consome)
        self.perigo = 0.0                # segundos de aviso de PERIGO antes do chefe (o HUD desenha)
        self.lentidao = 0.0              # segundos de câmera lenta (Frame Perfect)
        self.terminou = False
        self.venceu = False           # derrotou os três chefes ("Fim do semestre!")
        self._honras = False          # e ainda chegou vivo aos 20:00 ("Fim do semestre com honras!")
        self.anuncios = []
        self.invocacoes_abertas = False   # os círculos dos mini-chefes já foram espalhados pelo campus
        self.marcados = set()         # CHAVEs dos mini-chefes que o aluno marcou no mini-mapa (ganham seta na tela)
        self.mini_chefes_conhecidos = set()   # CHAVEs dos já invocados alguma vez (os outros são misteriosos)
        self.marcos = set()           # coisas que aconteceram na partida (para as conquistas)
        self.notas = {}               # ProvaMarcada -> nota de quem derrotou o chefe dela (para o boletim)
        self.mini_chefes_derrotados = 0
        self._ultima_nota = None
        self.adicionar(self.jogador)
        for entidade in self.mapa.entidades():
            self.adicionar(entidade)
        self._rng_do_cenario = random.Random(semente)    # sorteio próprio: não mexe na sequência do combate
        self._espalhar_quebraveis()
        self._incorporar_novas()
        self.camera.seguir(self.jogador.posicao)

    TENTATIVAS_DE_QUEBRAVEL = 40     # sorteios por objeto antes de desistir dele (mapa cheio demais)

    def _espalhar_quebraveis(self):
        """Espalha os objetos quebráveis uma vez só, no começo, em pontos sorteados do campus: fora dos
        prédios, afastados uns dos outros e longe de onde o aluno começa. Sem semente (o jogo de verdade),
        cada partida tem o próprio arranjo. Quebrado, o objeto não volta."""
        rng, colocados = self._rng_do_cenario, []
        area = self.arena.inflate(-120, -120)
        for _ in range(self.QUEBRAVEIS_NO_INICIO):
            for _ in range(self.TENTATIVAS_DE_QUEBRAVEL):
                ponto = pygame.Vector2(rng.uniform(area.left, area.right), rng.uniform(area.top, area.bottom))
                if self._cabe_quebravel(ponto, colocados):
                    colocados.append(ponto)
                    self.adicionar(rng.choice(QUEBRAVEIS)(ponto))
                    break

    def _cabe_quebravel(self, ponto, colocados):
        return ponto.distance_to(self.jogador.posicao) >= self.LONGE_DO_ALUNO and \
            all(ponto.distance_to(outro) >= self.ESPACO_ENTRE_QUEBRAVEIS for outro in colocados) and \
            not self.mapa.bloqueado(ponto, self.FOLGA_DO_QUEBRAVEL)

    @classmethod
    def a_partir_de(cls, classe_jogador, opcoes, semente=None):
        """Monta a partida a partir das OpcoesDePartida (treino, imortal, compras da loja)."""
        jogo = cls(classe_jogador, fase=opcoes.criar_fase(), semente=semente)
        jogo.treino = opcoes.treino
        jogo.jogador.imortal = opcoes.imortal
        jogo.jogador.desbloqueios = opcoes.desbloqueios
        jogo.mini_chefes_conhecidos = set(opcoes.mini_chefes_conhecidos)
        lanche = (opcoes.lanche(),) if opcoes.lanche is not None else ()
        jogo.jogador.receber_melhorias(tuple(opcoes.melhorias) + lanche)
        if opcoes.direto_no_chefe:
            jogo.evoluir_jogador(opcoes.prova.nivel_treino - 1)
        return jogo

    def evoluir_jogador(self, niveis):
        """Sobe o aluno `niveis` níveis escolhendo cartas sozinho (treino direto no chefe)."""
        for _ in range(niveis):
            self.jogador.ganhar_experiencia(self.jogador.experiencia_necessaria - self.jogador.experiencia)
            Progressao.gerar_opcoes(self.jogador, self.rng)[0].aplicar(self.jogador, self)
        self.jogador.vida = self.jogador.vida_maxima

    @property
    def inimigos(self):
        return self.grupos["inimigo"]

    @property
    def campo_cheio(self):
        """Se já há inimigos demais em campo: quem chama reforço (os chefes) espera esvaziar."""
        return len(self.inimigos) >= MAX_INIMIGOS

    TEMPO_DO_MINI_CHEFE = 180     # a cada tantos segundos de partida o mini-chefe ganha mais uma vez a vida base

    @property
    def escala_dos_mini_chefes(self):
        """Quanto mais tarde na partida o aluno invoca, mais forte o mini-chefe vem (vida, dano e lacaios)."""
        return 1 + self.placar.tempo / self.TEMPO_DO_MINI_CHEFE

    def marcadores(self):
        """O que aparece no mini-mapa: círculos de invocação à espera e mini-chefes já invocados e vivos."""
        esperando = [e for e in self.grupos["invocacao"] + self._novas
                     if e.ativo and e.grupo == "invocacao" and e.no_mapa]
        vivos = [e for e in self.inimigos if e.ativo and getattr(e, "ROSTO", "")]
        return esperando + vivos

    def adicionar(self, entidade):
        self._novas.append(entidade)

    def _incorporar_novas(self):
        while self._novas:
            novas, self._novas = self._novas, []
            for e in novas:
                self.entidades.append(e)
                self.grupos[e.grupo].append(e)

    def _limpar(self):
        self.entidades = [e for e in self.entidades if e.ativo]
        for nome in list(self.grupos):
            self.grupos[nome] = [e for e in self.grupos[nome] if e.ativo]

    FATOR_DA_CAMERA_LENTA = 0.35

    def camera_lenta(self, duracao):
        """Tudo anda mais devagar por `duracao` segundos de relógio (Frame Perfect)."""
        self.lentidao = max(self.lentidao, duracao)

    def atualizar(self, dt):
        if self.terminou:
            return
        if self.lentidao > 0:
            self.lentidao = max(0.0, self.lentidao - dt)
            dt *= self.FATOR_DA_CAMERA_LENTA
        self.placar.tempo += dt
        self.perigo = max(0.0, self.perigo - dt)
        self.fase.atualizar(dt, self)
        self._incorporar_novas()
        self.grade.reconstruir(self.inimigos + self.grupos["quebravel"])    # tudo o que as armas podem acertar
        for e in self.entidades:          # polimorfismo: um único laço, sem if por tipo
            if e.ativo:
                e.atualizar(dt, self)
        self._incorporar_novas()
        self._limpar()
        for anuncio in self.anuncios:
            anuncio[1] -= dt
        self.anuncios = [a for a in self.anuncios if a[1] > 0]
        self.camera.seguir(self.jogador.posicao)
        if not self.jogador.esta_vivo:
            self.terminar()
        elif self.venceu and not self._honras and self.fase.tempo >= self.fase.DURACAO:
            self._honras = True               # vivo aos 20:00 com os três chefes: honras, mesmo caindo depois
            self.anunciar("Fim do semestre com honras!", 5)

    @property
    def honras(self):
        """Derrotou os três chefes e estava vivo quando o relógio chegou aos 20:00."""
        return self._honras

    def desenhar(self, tela):
        self.mapa.desenhar_chao(tela, self.camera)
        visiveis = [e for e in self.entidades if e.esta_visivel(self.camera)]
        visiveis.sort(key=lambda e: (e.camada, e.posicao.y))
        for e in visiveis:
            e.desenhar(tela, self.camera)

    def resolver_obstaculos(self, posicao, raio):
        """Posição corrigida para fora dos prédios do mapa."""
        return self.mapa.empurrar(posicao, raio)

    def passo_do_chao(self, posicao):
        """Quanto o chão deixa o aluno andar ali (1 = normal; mato e plantação seguram o passo)."""
        return self.mapa.fator_de_velocidade(posicao)

    # Buscas

    def inimigos_proximos(self, posicao, raio):
        """Inimigos ativos cujo círculo encosta no círculo (posicao, raio)."""
        resultado = []
        for e in self.grade.proximos(posicao, raio + self.MARGEM_BUSCA):
            if e.ativo:
                limite = raio + e.raio
                if e.posicao.distance_squared_to(posicao) <= limite * limite:
                    resultado.append(e)
        return resultado

    def inimigo_mais_proximo(self, posicao, raio_max, excluir=None):
        melhor, melhor_distancia = None, raio_max * raio_max
        for e in self.grade.proximos(posicao, raio_max):
            if e is excluir or not e.ativo or not e.ALVO_DA_MIRA:
                continue
            distancia = e.posicao.distance_squared_to(posicao)
            if distancia <= melhor_distancia:
                melhor, melhor_distancia = e, distancia
        return melhor

    def inimigo_com_mais_vida(self, posicao, raio_max):
        candidatos = [e for e in self.grade.proximos(posicao, raio_max)
                      if e.ativo and e.ALVO_DA_MIRA and e.posicao.distance_squared_to(posicao) <= raio_max * raio_max]
        return max(candidatos, key=lambda e: e.vida, default=None)

    # Regras

    def causar_dano(self, inimigo, dano, direcao=None, forte=False):
        """Fere um inimigo. Retorna True se ele morreu com este golpe."""
        if not inimigo.ativo or not inimigo.esta_vivo or inimigo.invulneravel:
            return False
        critico = self._rolar_critico()
        if critico:
            sobra = self.jogador.chance(self.jogador.chance_critico) - 1
            dano *= self.jogador.MULT_CRITICO + max(0.0, sobra)   # passou de 100%: crítico mais forte
        duplo = self.jogador.multiplicador("golpe_duplo") - 1     # Combo do Gamer: chance de golpe duplo
        if duplo > 0 and self.rng.random() < duplo:
            dano *= 2
        dano *= inimigo.fator_de_dano_recebido                     # marcado pela Caneta Vermelha leva mais
        dano = max(1, round(dano * self.rng.uniform(1 - self.VARIACAO_DANO, 1 + self.VARIACAO_DANO)))
        morreu = inimigo.receber_dano(dano)
        if inimigo.CONTA_NO_PLACAR:
            self.jogador.avisar_acerto(inimigo, self)
            if critico:
                self.jogador.avisar_critico(inimigo, self)
        if direcao is not None:
            inimigo.empurrar(direcao)
        if len(self.grupos["efeito"]) < LIMITE_EFEITOS:
            deslocamento = pygame.Vector2(self.rng.uniform(-8, 8), -inimigo.raio)
            if critico:
                texto = TextoFlutuante(f"{dano}!", inimigo.posicao + deslocamento, Cor.DESTAQUE, 26)
            else:
                texto = TextoFlutuante(str(dano), inimigo.posicao + deslocamento,
                                       Cor.DANO_FORTE if forte else Cor.DANO, 22 if forte else 16)
            self.adicionar(texto)
        Recursos.tocar("acerto", 0.12)
        if morreu:
            self._registrar_morte(inimigo)
        return morreu

    DESVIO_MAXIMO = 0.6           # nem com muita sorte o aluno desvia de tudo
    FOLGA_DO_DESVIO = 0.25        # segundos sem levar dano depois de desviar (o mesmo golpe não acerta em seguida)
    VARIACAO_DANO = 0.10          # cada golpe varia ±10%, para os números não repetirem

    def _rolar_critico(self):
        """Sorteia um acerto crítico com a chance do herói, já com a sorte (só sorteia se a chance existir)."""
        chance = self.jogador.chance(self.jogador.chance_critico)
        return chance > 0 and self.rng.random() < chance

    def _registrar_morte(self, inimigo):
        inimigo.remover()
        if inimigo.CONTA_NO_PLACAR:
            self._contar_eliminacao(inimigo)
        inimigo.ao_morrer(self)

    def _contar_eliminacao(self, inimigo):
        """Eliminação de verdade (objeto quebrável não passa por aqui): moeda da carona, placar, combo e
        os itens que reagem a cada eliminação."""
        carona = self.jogador.chance(self.jogador.chance_carona)
        if inimigo.possuido > 0 and carona > 0 and self.rng.random() < carona:
            self.adicionar(Moeda(inimigo.posicao + (12, 0)))     # Carona Solidária
        if self.placar.registrar_eliminacao(inimigo.valor_em_pontos):
            self._combo_67()
        self.jogador.avisar_eliminacao(inimigo, self)

    def _combo_67(self):
        self.jogador.adicionar_bonus(BonusTemporario("combo67", "velocidade", BONUS_67_VELOCIDADE, BONUS_67_DURACAO))
        self.anunciar("67!", 2.0)
        Recursos.tocar("67", 0.9)

    def ferir_jogador(self, dano):
        if not self.jogador.pode_levar_dano:
            return False
        desvio = min(self.DESVIO_MAXIMO, self.jogador.chance(self.jogador.chance_desvio))
        if desvio > 0 and self.rng.random() < desvio:
            self.jogador.invencivel = self.FOLGA_DO_DESVIO
            self.adicionar(TextoFlutuante("DESVIOU!", self.jogador.posicao - (0, 30), Cor.CURA, 18))
            return False
        dano = self.jogador.filtrar_dano(dano, self)      # itens e habilidades podem reduzir ou anular o golpe
        if dano <= 0:
            self.jogador.invencivel = max(self.jogador.invencivel, self.FOLGA_DO_DESVIO)
            return False
        self.jogador.receber_dano(dano)
        self.placar.zerar_combo()
        self.adicionar(TextoFlutuante(f"-{round(dano)}", self.jogador.posicao - (0, 30), Cor.DANO_HEROI, 18))
        Recursos.tocar("dano", 0.4)
        return True

    def dar_experiencia(self, quantidade):
        heroi = self.jogador
        niveis = heroi.ganhar_experiencia(quantidade * heroi.mult_experiencia * heroi.fator_experiencia)
        self.niveis_pendentes += niveis
        for _ in range(niveis):
            heroi.ao_subir_de_nivel(self)

    def puxar_experiencia(self):
        """Ímã e Revisão para Prova: toda a experiência caída no mapa voa até o aluno. Cada coletável
        decide se atende (só a Nota atende), então aqui não se pergunta o tipo de ninguém."""
        recem_caidos = [e for e in self._novas if e.grupo == "coletavel"]     # ainda na fila deste quadro
        for coletavel in self.grupos["coletavel"] + recem_caidos:
            coletavel.puxar_experiencia()

    def ganhar_moedas(self, quantidade):
        self.placar.adicionar_moedas(round(quantidade * self.jogador.mult_moedas))

    def multar(self, quantidade):
        """Tira moedas pegas nesta partida (multa da Bibliotecária). Não deixa o saldo negativo."""
        perdidas = min(self.placar.moedas, round(quantidade))
        if perdidas > 0:
            self.placar.moedas -= perdidas
            self.adicionar(TextoFlutuante(f"-{perdidas} moedas", self.jogador.posicao - (0, 54), Cor.DESTAQUE, 18))
        return perdidas

    def marcar_no_mapa(self, chave):
        """Liga ou desliga a marcação de um mini-chefe (pela CHAVE: vários misteriosos têm o mesmo nome na tela);
        devolve True se ficou marcado."""
        if chave in self.marcados:
            self.marcados.discard(chave)
            return False
        self.marcados.add(chave)
        return True

    def mini_chefe_conhecido(self, chave):
        return chave in self.mini_chefes_conhecidos

    def conhecer_mini_chefe(self, chave):
        """Foi invocado: o nome e o rosto deixam de ser segredo (a CenaPartida guarda isso no progresso)."""
        self.mini_chefes_conhecidos.add(chave)

    def contar_mini_chefe(self):
        """Um mini-chefe do mapa caiu (conta para o bônus de honras e o HUD)."""
        self.mini_chefes_derrotados += 1

    @property
    def bonus_de_honras(self):
        """O bônus do fim do semestre com honras; zero para quem não chegou vivo aos 20:00 com os três chefes."""
        if not self.honras:
            return 0
        return round((self.BONUS_HONRAS + self.MOEDAS_POR_MINI_CHEFE * self.mini_chefes_derrotados)
                     * self.jogador.mult_moedas)

    def moedas_ganhas(self):
        """Moedas que vão para o Centro Acadêmico: as pegas, a bolsa pelo tempo e, com honras, o bônus.
        Treino não paga."""
        if self.treino:
            return 0
        bolsa = round(self.placar.tempo / 60 * self.MOEDAS_POR_MINUTO * self.jogador.mult_moedas)
        return self.placar.moedas + bolsa + self.bonus_de_honras

    def soltar_nota(self, posicao, valor):
        """Solta uma nota; acima do limite, soma o valor na última nota solta."""
        if len(self.grupos["coletavel"]) + sum(e.grupo == "coletavel" for e in self._novas) >= LIMITE_COLETAVEIS and \
                self._ultima_nota is not None and self._ultima_nota.ativo:
            self._ultima_nota.valor += valor
            return
        self._ultima_nota = Nota(posicao, valor)
        self.adicionar(self._ultima_nota)

    def pedir_bau(self):
        self.baus_pendentes += 1
        Recursos.tocar("bau", 0.6)

    @property
    def chefe(self):
        """O chefe em campo há mais tempo, ou None. Com dois em campo, o outro está em `chefes`."""
        return self.chefes[0] if self.chefes else None

    def chefe_da_prova(self, prova):
        """O chefe vivo que encerra a `prova` (uma ProvaMarcada), ou None."""
        return next((c for c in self.chefes if self._prova_de.get(c) == prova), None)

    def iniciar_chefe(self, chefe, prova=None):
        """Põe em campo o chefe que encerra `prova`. Os lacaios comuns saem para abrir espaço; chefes
        vivos e mini-chefes ficam (cada um decide em `ao_chegar_o_chefe`)."""
        for inimigo in self.inimigos:
            inimigo.ao_chegar_o_chefe(self)
        if prova is not None:
            self._prova_de[chefe] = prova
        self.chefes.append(chefe)
        self.chefe_a_apresentar = chefe
        self.perigo = 0.0
        self.adicionar(chefe)
        self.anunciar(f"{chefe.nome} chegou!", 3)

    def avisar_perigo(self, duracao):
        """Liga o aviso de PERIGO por `duracao` segundos: o chefe está chegando."""
        self.perigo = duracao
        Recursos.tocar("buzina", 0.5)

    @property
    def chefes_derrotados(self):
        return len(self.notas)

    def aprovar(self, chefe):
        """O chefe caiu: a prova dele está aprovada (nota, moedas, cura e baú). Com as provas todas
        aprovadas o semestre está vencido: o treino acaba aí; a partida segue até o aluno cair."""
        prova = self._prova_de.pop(chefe, None)
        if chefe in self.chefes:
            self.chefes.remove(chefe)
        if prova is not None:
            self.notas[prova] = Boletim.nota_de_aprovacao(self.jogador)
            self.anunciar(f"Aprovado em {prova.materia}!", 3)
        self.ganhar_moedas(self.MOEDAS_POR_PROVA)
        self.jogador.curar(self.jogador.vida_maxima * self.CURA_ENTRE_PROVAS)
        self.pedir_bau()
        if prova is not None and len(self.notas) >= len(self.fase.provas):
            self.venceu = True
            if self.treino:
                self.terminar()
            else:
                self.anunciar("Semestre aprovado! Agora é aguentar até o fim", 5)

    def anunciar(self, texto, duracao=2.5):
        self.anuncios.append([texto, duracao])

    def terminar(self, venceu=None):
        """Acaba a partida. Quem já derrotou os três chefes termina com honras, mesmo caindo depois;
        `venceu` só é passado para forçar o resultado (testes e telas)."""
        if self.terminou:
            return
        self.terminou = True
        if venceu is not None:
            self.venceu = venceu
        Recursos.tocar("vitoria" if self.venceu else "derrota", 0.7)

    def resultado(self, nome):
        return RegistroRanking(nome, self.jogador.NOME, self.placar.pontuacao_final(self.venceu),
                               self.placar.tempo, self.venceu, self.chefes_derrotados, self.honras)
