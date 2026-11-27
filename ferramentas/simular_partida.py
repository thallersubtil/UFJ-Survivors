"""Joga partidas inteiras sem janela, com um robô que joga razoavelmente, e resume o balanceamento.

O robô desvia rolando de projéteis e de quem encosta, fica perto o bastante para as armas acertarem
(rodeando o alvo, sem parar no lugar), escolhe as cartas por uma prioridade simples (colab, arma inicial,
outras armas, o resto, itens) e caça os mini-chefes: sem chefe vivo, vai ao círculo mais perto, invoca e luta.

Uso:
  python ferramentas/simular_partida.py                          uma partida (Otaku, semente 1), com o resumo
  python ferramentas/simular_partida.py --todas-as-classes --sementes 5 --loja metade
  opções: --heroi 1..7 (ordem de CLASSES) | --todas-as-classes; --semente N | --sementes N (de 1 a N);
          --loja nada|metade|cheia; --sem-caca; --minutos N (padrão 21); --imortal; --processos N;
          --detalhe (uma linha por minuto, para uma partida só)

Saída: uma linha por partida (nível na chegada de cada chefe, hora em que cada chefe caiu, mini-chefes
derrotados, resultado e moedas) e uma tabela-resumo por classe. O pior quadro é tempo de CPU da lógica
(sem desenhar), para conferir o desempenho com o pico real de inimigos.
"""
import argparse
import os
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from jogo.armas.arma import Arma  # noqa: E402
from jogo.coletaveis.coletaveis import PocaoDeVida  # noqa: E402
from jogo.itens.item import Item  # noqa: E402
from jogo.itens.itens import (ITENS, MensalidadeDaAtletica, NoiteSemDormir, ParcelarNoCartao,  # noqa: E402
                              PreTreinoDuvidoso)
from jogo.inimigos.mini_chefes import MiniChefe  # noqa: E402
from jogo.jogador.classes import CLASSES  # noqa: E402
from jogo.jogo import Jogo  # noqa: E402
from jogo.loja.melhorias import MELHORIAS  # noqa: E402
from jogo.opcoes import OpcoesDePartida  # noqa: E402
from jogo.progressao import Progressao  # noqa: E402

DT = 1 / 30
ORCAMENTO_METADE = 5000          # moedas gastas na loja "pela metade" (a especificação do M5)


# ---------------------------------------------------------------- loja

def tudo_desbloqueavel():
    """Nomes das armas e itens que só entram nas cartas depois de comprados."""
    return frozenset(c.__name__ for c in tuple(Progressao.ARMAS) + tuple(ITENS) if c.PRECO_DESBLOQUEIO > 0)


def _compras(loja):
    """O que a loja compra: (melhorias com o nível comprado, desbloqueios, moedas gastas).
    "metade" compra sempre a próxima compra mais barata (nível seguinte de uma melhoria ou um desbloqueio)
    até o orçamento acabar, como um aluno que vai juntando moedas."""
    if loja == "nada":
        return {}, frozenset(), 0
    precos = {c.__name__: c.PRECO_DESBLOQUEIO for c in tuple(Progressao.ARMAS) + tuple(ITENS)
              if c.PRECO_DESBLOQUEIO > 0}
    if loja == "cheia":
        niveis = {m: m.NIVEL_MAXIMO for m in MELHORIAS}
        gasto = sum(m.custo(n) for m in MELHORIAS for n in range(m.NIVEL_MAXIMO)) + sum(precos.values())
        return niveis, frozenset(precos), gasto
    if loja != "metade":
        raise ValueError(f"loja desconhecida: {loja!r} (use nada, metade ou cheia)")
    niveis, desbloqueios, gasto = {m: 0 for m in MELHORIAS}, set(), 0
    while True:
        opcoes = [(m.custo(niveis[m]), "melhoria", m) for m in MELHORIAS if niveis[m] < m.NIVEL_MAXIMO]
        opcoes += [(preco, "desbloqueio", nome) for nome, preco in precos.items() if nome not in desbloqueios]
        cabem = [o for o in opcoes if gasto + o[0] <= ORCAMENTO_METADE]
        if not cabem:
            break
        preco, tipo, coisa = min(cabem, key=lambda o: (o[0], o[1]))
        gasto += preco
        if tipo == "melhoria":
            niveis[coisa] += 1
        else:
            desbloqueios.add(coisa)
    return {m: n for m, n in niveis.items() if n > 0}, frozenset(desbloqueios), gasto


def montar_loja(loja):
    """(melhorias, desbloqueios) prontos para as OpcoesDePartida."""
    niveis, desbloqueios, _ = _compras(loja)
    return tuple(m(n) for m, n in niveis.items()), desbloqueios


def custo_da_loja(loja):
    return _compras(loja)[2]


# ---------------------------------------------------------------- cartas

# Itens com preço alto (vida, dano recebido, moedas): o robô só pega quando não há outra carta.
ITENS_DE_RISCO = (PreTreinoDuvidoso, NoiteSemDormir, ParcelarNoCartao, MensalidadeDaAtletica)


def escolher_carta(opcoes, heroi):
    """Prioridade simples: colab, arma inicial, outras armas (melhorar antes de pegar nova), o que não for
    arma nem item (habilidades), itens, e por último os itens de risco (um jogador razoável só pega se não houver
    outra coisa). Nas cartas de nível máximo: vida se estiver mal, senão moedas."""
    inicial = type(heroi.arma_inicial)

    def prioridade(opcao):
        origem = opcao.origem
        if opcao.tipo == "colab":
            return 0
        if origem is inicial:
            return 1
        if isinstance(origem, type) and issubclass(origem, Arma):
            return 2 if opcao.tipo == "melhoria" else 3
        if origem in ITENS_DE_RISCO:
            return 8
        if isinstance(origem, type) and issubclass(origem, Item):
            return 6 if opcao.tipo == "melhoria" else 7
        if opcao.tipo == "maximo":
            cura = "vida" in opcao.descricao.lower()
            precisa = heroi.vida < heroi.vida_maxima * 0.6
            return 9 if cura == precisa else 10
        return 4                                    # habilidades e o que vier de novo

    return min(opcoes, key=prioridade)


# ---------------------------------------------------------------- o robô

class Robo:
    """Decide a cada quadro para onde o aluno anda, para onde mira, quando rola e quando usa o especial."""

    DISTANCIA_DE_TIRO = 200          # arma que atira de longe: fica a esta distância (ou menos, se o alcance for curto)
    ALCANCE_DA_MIRA = 700
    PERTO_DEMAIS = 110               # inimigos mais perto que isso empurram o robô para longe (ou menos, com arma de perto)
    ENCOSTO = 100                    # mas nunca deixa chegar mais perto que isso sem empurrar
    VOLTA_NO_BOLO = 160              # rodeia o bolo de inimigos a esta distância a mais que a de combate
    RAIO_DO_BOLO = 400               # inimigos até esta distância contam para o centro do bolo
    LONGE_DO_CIRCULO = 3500          # círculos mais longe que isso nem são considerados
    ALCANCE_DA_NOTA = 260            # nota mais perto que isso, sem ninguém encostando, é recolhida
    NIVEL_PARA_CACAR = 6             # só invoca mini-chefe a partir deste nível...
    NIVEIS_POR_MINI_CHEFE = 2        # ...mais este tanto por mini-chefe já derrotado (eles ficam mais fortes)
    VIDA_PARA_CACAR = 0.7            # e com pelo menos esta fração da vida
    VIDA_PARA_CURAR = 0.5            # abaixo desta fração da vida, vai atrás de cura (poção ou objeto quebrável)
    VIDA_PARA_LARGAR = 0.3           # e abaixo desta larga o mini-chefe para se curar (o chefe, não: ele vem atrás)
    LONGE_DA_CURA = 1500             # cura mais longe que isso não compensa a viagem
    ESPERA_PARA_TRAVADO = 1.2        # segundos sem sair do lugar (querendo andar) para contar como travado
    DESVIO_DE_TRAVADO = 1.0          # e quanto tempo anda de lado para destravar

    def __init__(self, jogo, cacar=True):
        self.jogo = jogo
        self.cacar = cacar
        self.sentido = 1                     # sentido em que rodeia o alvo (troca quando bate em algo)
        self._ultimo_lugar = pygame.Vector2(jogo.jogador.posicao)
        self._parado_ha = 0.0
        self._desviando = 0.0
        self._lado = pygame.Vector2()
        self._quebrando = None               # objeto quebrável que está quebrando atrás de cura

    # ---- decisão
    def agir(self, dt):
        jogo, heroi = self.jogo, self.jogo.jogador
        rumo = self._rumo(dt)
        jogo.entrada.direcao = rumo
        alvo = self._alvo_da_mira()
        jogo.entrada.mira = pygame.Vector2(alvo.posicao) if alvo is not None else None
        self._esquivar(rumo)
        jogo.entrada.segurando_especial = alvo is not None     # a Virada de Noite atira enquanto houver café e alvo
        if heroi.especial.pronto and (jogo.chefe is not None or
                                      len(jogo.inimigos_proximos(heroi.posicao, 300)) >= 8):
            heroi.usar_especial(jogo)

    def _alvo_da_mira(self):
        jogo = self.jogo
        if self._quebrando is not None and self._quebrando.ativo and \
                self._quebrando.posicao.distance_to(jogo.jogador.posicao) <= 400:
            return self._quebrando                        # a mira do jogo ignora objetos: aponta à mão
        luta = self._luta()
        if luta is not None and luta.posicao.distance_to(jogo.jogador.posicao) <= self.ALCANCE_DA_MIRA:
            perto = jogo.inimigo_mais_proximo(jogo.jogador.posicao, 120)
            return perto or luta                          # quem encosta primeiro; senão o chefe
        return jogo.inimigo_mais_proximo(jogo.jogador.posicao, self.ALCANCE_DA_MIRA)

    def _luta(self):
        """O chefe vivo mais perto ou, sem chefe, o mini-chefe invocado e vivo mais perto (ou None)."""
        jogo, onde = self.jogo, self.jogo.jogador.posicao
        chefes = [c for c in jogo.chefes if c.ativo]
        if not chefes:
            chefes = [m for m in jogo.marcadores() if m.invocado and m.ativo]
        return min(chefes, key=lambda c: c.posicao.distance_squared_to(onde), default=None)

    @property
    def distancia_de_combate(self):
        """A que distância do alvo a arma principal (a de nível mais alto) acerta. Arma com alcance de tiro
        fica longe; arma que age em volta do aluno (Caramelo, Apostila, Wi-Fi) precisa do alvo dentro do raio, e a de
        corpo a corpo (Régua, Teclado Mecânico, Caneta de Correção), dentro do golpe."""
        principal = max(self.jogo.jogador.armas, key=lambda a: a.nivel, default=None)
        if principal is None:
            return self.DISTANCIA_DE_TIRO
        alcance = getattr(principal, "ALCANCE", None)
        if alcance is not None:
            return min(self.DISTANCIA_DE_TIRO, alcance * 0.6)
        if "raio" in principal.ATRIBUTOS:
            return principal.valor("raio") * 0.8
        if "alcance" in principal.ATRIBUTOS:
            return principal.valor("alcance") * 0.7
        return self.DISTANCIA_DE_TIRO

    @property
    def pronto_para_cacar(self):
        """Um jogador razoável não invoca mini-chefe no nível 2 nem com pouca vida."""
        jogo, heroi = self.jogo, self.jogo.jogador
        nivel = self.NIVEL_PARA_CACAR + self.NIVEIS_POR_MINI_CHEFE * jogo.mini_chefes_derrotados
        return self.cacar and heroi.nivel >= nivel and heroi.vida >= heroi.vida_maxima * self.VIDA_PARA_CACAR

    def _circulo(self):
        if not self.pronto_para_cacar:
            return None
        onde = self.jogo.jogador.posicao
        circulos = [m for m in self.jogo.marcadores() if not m.invocado and m.ativo
                    and m.posicao.distance_to(onde) <= self.LONGE_DO_CIRCULO]
        return min(circulos, key=lambda c: c.posicao.distance_squared_to(onde), default=None)

    def _cura(self):
        """Ferido: a poção mais perto no chão ou, sem poção, o objeto quebrável mais perto (pode soltar cura)."""
        jogo, heroi = self.jogo, self.jogo.jogador
        self._quebrando = None
        if heroi.vida >= heroi.vida_maxima * self.VIDA_PARA_CURAR:
            return None
        onde = heroi.posicao
        pocoes = [c for c in jogo.grupos["coletavel"] if isinstance(c, PocaoDeVida) and c.ativo
                  and c.posicao.distance_to(onde) <= self.LONGE_DA_CURA]
        if pocoes:
            return min(pocoes, key=lambda c: c.posicao.distance_squared_to(onde))
        objetos = [o for o in jogo.grupos["quebravel"] if o.ativo and o.posicao.distance_to(onde) <= self.LONGE_DA_CURA]
        self._quebrando = min(objetos, key=lambda o: o.posicao.distance_squared_to(onde), default=None)
        return self._quebrando

    def _rumo(self, dt):
        jogo, heroi = self.jogo, self.jogo.jogador
        onde = heroi.posicao
        luta = self._luta()
        cura = self._cura()
        largar = luta is not None and not jogo.chefes and heroi.vida < heroi.vida_maxima * self.VIDA_PARA_LARGAR
        if cura is not None and (luta is None or largar):
            perto_da_cura = 0 if cura is not self._quebrando else 60
            falta = cura.posicao - onde
            desejo = falta if falta.length() > perto_da_cura else pygame.Vector2()
        elif luta is not None:
            desejo = self._rodear(luta.posicao, self.distancia_de_combate + luta.raio)
        else:
            circulo = self._circulo()
            perto = jogo.inimigo_mais_proximo(onde, 900)
            if circulo is not None:
                falta = circulo.posicao - onde
                desejo = falta if falta.length() > circulo.raio * 0.4 else pygame.Vector2()
            elif perto is not None:                  # rodeia o bolo: quem persegue fica atrás, ao alcance das armas
                bolo = jogo.inimigos_proximos(onde, self.RAIO_DO_BOLO) or [perto]
                centro = sum((e.posicao for e in bolo), pygame.Vector2()) / len(bolo)
                desejo = self._rodear(centro, self.distancia_de_combate + self.VOLTA_NO_BOLO)
            else:
                desejo = pygame.Vector2(jogo.arena.center) - onde
            nota = self._nota_perto()
            if nota is not None and not jogo.inimigos_proximos(onde, self.PERTO_DEMAIS):
                desejo = nota.posicao - onde
            if circulo is None:
                desejo = self._normal(desejo) + self._sair_dos_circulos() * 3.0
        desejo = self._normal(desejo) * 1.0 + self._afastar_dos_perto() * 2.0
        desejo = self._destravar(desejo, dt)
        return self._normal(desejo)

    def _sair_dos_circulos(self):
        """Quem não vai caçar agora não fica parado num círculo (invocaria sem querer): sai pelo lado mais perto.
        Vale também para o círculo secreto, que ainda não está no mapa."""
        onde = self.jogo.jogador.posicao
        for circulo in self.jogo.grupos["invocacao"]:
            de_la = onde - circulo.posicao
            if circulo.ativo and de_la.length() < circulo.raio + 30:
                return self._normal(de_la if de_la.length_squared() > 1 else pygame.Vector2(1, 0))
        return pygame.Vector2()

    def _rodear(self, centro, distancia):
        """Anda em volta de `centro`, chegando ou se afastando até ficar a `distancia` dele."""
        de_la = self.jogo.jogador.posicao - centro
        if de_la.length_squared() < 1:
            de_la = pygame.Vector2(1, 0)
        raio = de_la.length()
        volta = pygame.Vector2(-de_la.y, de_la.x).normalize() * self.sentido
        ajuste = de_la.normalize() * max(-1.5, min(1.5, (distancia - raio) / distancia * 3))
        return volta + ajuste

    def _afastar_dos_perto(self):
        onde = self.jogo.jogador.posicao
        perto_demais = max(self.ENCOSTO, min(self.PERTO_DEMAIS, self.distancia_de_combate * 0.7))
        empurrao = pygame.Vector2()
        for inimigo in self.jogo.inimigos_proximos(onde, perto_demais):
            longe = onde - inimigo.posicao
            if longe.length_squared() > 1:
                empurrao += longe.normalize() * (1 - longe.length() / (perto_demais + inimigo.raio))
        return empurrao

    def _nota_perto(self):
        onde = self.jogo.jogador.posicao
        notas = [c for c in self.jogo.grupos["coletavel"] if c.MAGNETICO and not c.atraido
                 and c.posicao.distance_to(onde) <= self.ALCANCE_DA_NOTA]
        return min(notas, key=lambda c: c.posicao.distance_squared_to(onde), default=None)

    def _destravar(self, desejo, dt):
        """Prédio no caminho: se quer andar e não sai do lugar, anda de lado por um tempo."""
        onde = self.jogo.jogador.posicao
        if self._desviando > 0:
            self._desviando -= dt
            return self._lado
        if desejo.length_squared() > 0.01 and onde.distance_to(self._ultimo_lugar) < 40 * dt:
            self._parado_ha += dt
        else:
            self._parado_ha = 0.0
        self._ultimo_lugar = pygame.Vector2(onde)
        if self._parado_ha >= self.ESPERA_PARA_TRAVADO:
            self._parado_ha = 0.0
            self.sentido *= -1
            self._desviando = self.DESVIO_DE_TRAVADO
            self._lado = pygame.Vector2(-desejo.y, desejo.x) * self.sentido
            return self._lado
        return desejo

    @staticmethod
    def _normal(vetor):
        return vetor.normalize() if vetor.length_squared() > 1e-6 else pygame.Vector2()

    # ---- rolamento
    def _esquivar(self, rumo):
        """Rola de lado quando um projétil vem na direção dele, ou para longe quando alguém encosta."""
        jogo, heroi = self.jogo, self.jogo.jogador
        if not heroi.rolamento.pronto or heroi.rolamento.rolando:
            return
        direcao = self._fuga_do_projetil()
        if direcao is None:
            encostando = jogo.inimigos_proximos(heroi.posicao, heroi.raio + 6)
            if not encostando:
                return
            direcao = self._normal(self._afastar_dos_perto()) or self._normal(rumo) or pygame.Vector2(1, 0)
        heroi.direcao_movimento = pygame.Vector2(direcao)
        heroi.rolar()

    def _fuga_do_projetil(self):
        heroi = self.jogo.jogador
        for tiro in self.jogo.grupos["projetil_inimigo"]:
            velocidade = getattr(tiro, "velocidade", None)        # alguns ataques guardam só a rapidez (um número)
            if not tiro.ativo or not isinstance(velocidade, pygame.Vector2) or velocidade.length_squared() < 1:
                continue
            ate_mim = heroi.posicao - tiro.posicao
            distancia = ate_mim.length()
            if distancia > 160 or ate_mim.dot(velocidade) <= 0:
                continue                                     # longe, ou indo para o outro lado
            rumo = velocidade.normalize()
            de_lado = ate_mim - rumo * ate_mim.dot(rumo)         # quanto passa ao lado do aluno
            if de_lado.length() > tiro.raio + heroi.raio + 12:
                continue
            lado = pygame.Vector2(-rumo.y, rumo.x)
            return lado if lado.dot(de_lado) >= 0 else -lado     # sai pelo lado em que já está
        return None


# ---------------------------------------------------------------- uma partida

@dataclass
class Luta:
    """Uma luta contra mini-chefe: quando ele apareceu, nível e fração da vida do aluno nessa hora, e como acabou."""
    nome: str
    inicio: float
    nivel: int
    vida: float
    fim: float = None
    venceu: bool = False
    vida_do_mini_chefe: float = 1.0      # fração da vida que ele ainda tinha quando a luta acabou

    @property
    def duracao(self):
        return (self.fim if self.fim is not None else self.inicio) - self.inicio


@dataclass
class Resultado:
    classe: str
    semente: int
    loja: str
    cacar: bool
    niveis_nos_chefes: list = field(default_factory=list)   # nível do aluno na chegada de cada chefe
    chefes_caidos: list = field(default_factory=list)       # segundos de partida em que cada chefe caiu
    mini_chefes: int = 0
    resultado: str = ""
    moedas: int = 0
    tempo: float = 0.0
    eliminacoes: int = 0
    nivel_final: int = 1
    pior_quadro_ms: float = 0.0
    quadro_medio_ms: float = 0.0
    pico_inimigos: int = 0
    lutas: list = field(default_factory=list)               # uma Luta por mini-chefe invocado

    @property
    def honras(self):
        return self.resultado == "HONRAS"

    @property
    def fim_do_semestre(self):
        """Derrotou os três chefes (com ou sem honras): é vitória."""
        return self.resultado in ("HONRAS", "FIM")


def jogar(classe, semente, loja="nada", cacar=True, minutos=21.0, imortal=False, detalhe=False):
    """Joga uma partida com o robô e devolve o Resultado."""
    if not pygame.get_init():
        pygame.init()
        pygame.display.set_mode((1, 1))
    melhorias, desbloqueios = montar_loja(loja)
    opcoes = OpcoesDePartida(melhorias=melhorias, desbloqueios=desbloqueios, imortal=imortal)
    jogo = Jogo.a_partir_de(classe, opcoes, semente=semente)
    robo = Robo(jogo, cacar=cacar)
    r = Resultado(classe.NOME, semente, loja, cacar)
    vistos, soma, quadros = set(), 0.0, 0
    lutas = {}                                              # mini-chefe -> Luta, enquanto ele está em campo
    while not jogo.terminou and jogo.placar.tempo < minutos * 60:
        robo.agir(DT)
        antes = time.thread_time()
        jogo.atualizar(DT)
        gasto = time.thread_time() - antes
        soma += gasto
        quadros += 1
        r.pior_quadro_ms = max(r.pior_quadro_ms, gasto * 1000)
        r.pico_inimigos = max(r.pico_inimigos, len(jogo.inimigos))
        for chefe in jogo.chefes:
            if chefe not in vistos:
                vistos.add(chefe)
                r.niveis_nos_chefes.append(jogo.jogador.nivel)
        _acompanhar_lutas(jogo, lutas, r)
        while len(r.chefes_caidos) < jogo.chefes_derrotados:
            r.chefes_caidos.append(jogo.placar.tempo)
        while jogo.niveis_pendentes > 0:
            escolher_carta(Progressao.gerar_opcoes(jogo.jogador, jogo.rng), jogo.jogador).aplicar(jogo.jogador, jogo)
            jogo.niveis_pendentes -= 1
        while jogo.baus_pendentes > 0:
            Progressao.premio_bau(jogo.jogador, jogo.rng).aplicar(jogo.jogador, jogo)
            jogo.baus_pendentes -= 1
        if detalhe and quadros % round(60 / DT) == 0:
            print(f"  {jogo.placar.tempo_formatado}  nível {jogo.jogador.nivel:>2}  vida {jogo.jogador.vida:>5.0f}"
                  f"/{jogo.jogador.vida_maxima:.0f}  inimigos {len(jogo.inimigos):>3}  "
                  f"eliminações {jogo.placar.eliminacoes:>5}  mini-chefes {jogo.mini_chefes_derrotados}  "
                  f"chefes {jogo.chefes_derrotados}  dificuldade {jogo.fase.escala_dificuldade:.1f}", flush=True)
    for inimigo, luta in lutas.items():
        luta.fim = jogo.placar.tempo                        # a partida acabou com ele de pé
        luta.vida_do_mini_chefe = max(0.0, inimigo.vida / inimigo.vida_maxima)
    r.mini_chefes = jogo.mini_chefes_derrotados
    r.resultado = "HONRAS" if jogo.honras else "FIM" if jogo.venceu else "REPROVADO"
    r.moedas = jogo.moedas_ganhas()
    r.tempo = jogo.placar.tempo
    r.eliminacoes = jogo.placar.eliminacoes
    r.nivel_final = jogo.jogador.nivel
    r.quadro_medio_ms = soma / max(1, quadros) * 1000
    return r


def _acompanhar_lutas(jogo, lutas, r):
    """Abre uma Luta quando um mini-chefe aparece e fecha quando ele sai de campo (vencido se a vida zerou)."""
    heroi = jogo.jogador
    for inimigo in jogo.inimigos:
        if isinstance(inimigo, MiniChefe) and inimigo not in lutas and inimigo.ativo:
            luta = Luta(inimigo.NOME, jogo.placar.tempo, heroi.nivel, heroi.vida / heroi.vida_maxima)
            lutas[inimigo] = luta
            r.lutas.append(luta)
    for inimigo in [i for i in lutas if not i.ativo]:
        luta = lutas.pop(inimigo)
        luta.fim, luta.venceu = jogo.placar.tempo, inimigo.vida <= 0
        luta.vida_do_mini_chefe = max(0.0, inimigo.vida / inimigo.vida_maxima)


def _relogio(segundos):
    minutos, resto = divmod(int(segundos), 60)
    return f"{minutos:02d}:{resto:02d}"


def linha_da_partida(r):
    niveis = " / ".join(str(n) for n in r.niveis_nos_chefes) or "-"
    caidos = " / ".join(_relogio(t) for t in r.chefes_caidos) or "-"
    return (f"{r.classe:<15} semente {r.semente:>2}  nível nos chefes {niveis:<10}  chefes caíram {caidos:<21}  "
            f"mini-chefes {r.mini_chefes:>2}  {r.resultado:<9} em {_relogio(r.tempo)}  moedas {r.moedas:>5}  "
            f"{_primeira_luta(r)}  (nível final {r.nivel_final}, pior quadro {r.pior_quadro_ms:.0f} ms, "
            f"pico {r.pico_inimigos})")


def _primeira_luta(r):
    if not r.lutas:
        return "nenhum mini-chefe"
    luta = r.lutas[0]
    desfecho = "venceu" if luta.venceu else "perdeu"
    return (f"1º mini-chefe no nível {luta.nivel} às {_relogio(luta.inicio)} com {luta.vida:.0%} da vida: "
            f"{desfecho} em {luta.duracao:.0f} s, ele com {luta.vida_do_mini_chefe:.0%}")


def _porcento(parte, todo):
    return f"{100 * parte / todo:>4.0f}%" if todo else "    -"


def _media_do_nivel(resultados, indice):
    niveis = [r.niveis_nos_chefes[indice] for r in resultados if len(r.niveis_nos_chefes) > indice]
    return f"{statistics.mean(niveis):>5.1f}" if niveis else "    -"


def _nivel_da_primeira_luta(resultados):
    niveis = [r.lutas[0].nivel for r in resultados if r.lutas]
    return f"{statistics.mean(niveis):.1f}" if niveis else "-"


def tabela_por_classe(resultados):
    """Tabela-resumo: por classe e no total, quanto vence cada chefe, fim do semestre (os três chefes), honras
    (os três e vivo aos 20:00), tempo, níveis e moedas; e a 1ª luta contra mini-chefe (o nível, e se venceu,
    perdeu ou morreu antes de lutar: as três colunas somam 100%)."""
    grupos = {}
    for r in resultados:
        grupos.setdefault(r.classe, []).append(r)
    grupos["TOTAL"] = list(resultados)
    cabecalho = (f"{'classe':<15} {'partidas':>8} {'1º chefe':>8} {'2º chefe':>8} {'fim sem.':>8} {'honras':>7} "
                 f"{'tempo med.':>10} {'nível 1º':>8} {'nível 2º':>8} {'nível 3º':>8} {'mini-chefes':>11} "
                 f"{'moedas med.':>11} {'nível 1º mini':>13} {'vence 1º mini':>13} {'perde 1º mini':>13} "
                 f"{'sem luta':>8}")
    linhas = [cabecalho, "-" * len(cabecalho)]
    for nome, lista in grupos.items():
        n = len(lista)
        linhas.append(
            f"{nome:<15} {n:>8} {_porcento(sum(len(r.chefes_caidos) >= 1 for r in lista), n):>8} "
            f"{_porcento(sum(len(r.chefes_caidos) >= 2 for r in lista), n):>8} "
            f"{_porcento(sum(r.fim_do_semestre for r in lista), n):>8} "
            f"{_porcento(sum(r.honras for r in lista), n):>7} "
            f"{_relogio(statistics.median(r.tempo for r in lista)):>10} "
            f"{_media_do_nivel(lista, 0):>8} {_media_do_nivel(lista, 1):>8} {_media_do_nivel(lista, 2):>8} "
            f"{statistics.mean(r.mini_chefes for r in lista):>11.1f} "
            f"{statistics.median(r.moedas for r in lista):>11.0f} {_nivel_da_primeira_luta(lista):>13} "
            f"{_porcento(sum(bool(r.lutas) and r.lutas[0].venceu for r in lista), n):>13} "
            f"{_porcento(sum(bool(r.lutas) and not r.lutas[0].venceu for r in lista), n):>13} "
            f"{_porcento(sum(not r.lutas for r in lista), n):>8}")
    return "\n".join(linhas)


# ---------------------------------------------------------------- linha de comando

def _jogar_tarefa(tarefa):
    indice, semente, loja, cacar, minutos, imortal = tarefa
    return jogar(CLASSES[indice], semente, loja, cacar, minutos, imortal)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--heroi", type=int, default=1, help="1 a 7, na ordem de CLASSES")
    p.add_argument("--todas-as-classes", action="store_true")
    p.add_argument("--semente", type=int, default=1)
    p.add_argument("--sementes", type=int, help="joga as sementes de 1 a N")
    p.add_argument("--loja", choices=("nada", "metade", "cheia"), default="nada")
    p.add_argument("--sem-caca", action="store_true", help="o robô não vai aos círculos dos mini-chefes")
    p.add_argument("--minutos", type=float, default=21.0)
    p.add_argument("--imortal", action="store_true")
    p.add_argument("--processos", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    p.add_argument("--detalhe", action="store_true", help="uma linha por minuto (só com uma partida)")
    a = p.parse_args()
    classes = range(len(CLASSES)) if a.todas_as_classes else [a.heroi - 1]
    sementes = range(1, a.sementes + 1) if a.sementes else [a.semente]
    tarefas = [(c, s, a.loja, not a.sem_caca, a.minutos, a.imortal) for c in classes for s in sementes]
    print(f"loja: {a.loja} ({custo_da_loja(a.loja)} moedas gastas); caça aos mini-chefes: "
          f"{'não' if a.sem_caca else 'sim'}; {len(tarefas)} partida(s)", flush=True)
    inicio = time.perf_counter()
    if len(tarefas) == 1:
        resultados = [jogar(CLASSES[tarefas[0][0]], *tarefas[0][1:], detalhe=a.detalhe)]
        print(linha_da_partida(resultados[0]))
    else:
        resultados = []
        with ProcessPoolExecutor(max_workers=a.processos) as executor:
            for r in executor.map(_jogar_tarefa, tarefas):
                resultados.append(r)
                print(linha_da_partida(r), flush=True)
    print()
    print(tabela_por_classe(resultados))
    pior = max(resultados, key=lambda r: r.pior_quadro_ms)
    print(f"\npior quadro da lógica: {pior.pior_quadro_ms:.1f} ms de CPU ({pior.classe}, semente {pior.semente}); "
          f"pico de inimigos: {max(r.pico_inimigos for r in resultados)}; "
          f"tempo real: {time.perf_counter() - inicio:.0f} s")


if __name__ == "__main__":
    main()
