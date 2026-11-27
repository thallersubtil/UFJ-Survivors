"""Armas exclusivas (a arma inicial de cada classe só ela tem, como no HoloCure), as quatro armas exclusivas novas
e as colabs que só usam armas comuns."""
import pygame
import pytest

from jogo.ajudantes.colabs_novas import FolhaEmEspiral, Latido, PequiEmArco, QuadroGigante, RastroDeSinal
from jogo.ajudantes.golpes import (AlfineteDoMapa, EstocadaDaCaneta, GolpeDoTeclado, LightstickGirando, NotaMusical,
                                   OndaDeTeclas, TeclaVoadora, XDeCorrecao)
from jogo.armas.apostila import Apostila
from jogo.armas.arma import Arma
from jogo.armas.caneta_correcao import CanetaDeCorrecao
from jogo.armas.caramelo import Caramelo
from jogo.armas.colabs import AulaExpositiva, Caramelo5G, CatapultaDoCerrado, Colab
from jogo.armas.controle import Controle
from jogo.armas.dado import DadoDeVinteLados
from jogo.armas.fusca import FuscaAzul
from jogo.armas.lightstick import Lightstick
from jogo.armas.mapa_do_campus import MapaDoCampus
from jogo.armas.pequi import PequiExplosivo
from jogo.armas.quadro_branco import QuadroBranco
from jogo.armas.regua import ReguaDeUmMetro
from jogo.armas.teclado import TecladoMecanico
from jogo.armas.wifi import WifiEduroam
from jogo.inimigos.bug import Bug
from jogo.jogador.classes import (CLASSES, Calouro, CaraDaCarona, Gamer, MestreDeRPG, Monitor, Otaku,
                                  Programador)
from jogo.progressao import Progressao

EXCLUSIVAS = {Otaku: Lightstick, Programador: TecladoMecanico, MestreDeRPG: DadoDeVinteLados,
              Monitor: CanetaDeCorrecao, Gamer: Controle, Calouro: MapaDoCampus, CaraDaCarona: FuscaAzul}
NOVAS = [Lightstick, TecladoMecanico, CanetaDeCorrecao, MapaDoCampus]
COLABS_NOVAS = [AulaExpositiva, Caramelo5G, CatapultaDoCerrado]


def jogo_com_bugs(jogo_limpo, *deslocamentos, classe=None):
    jogo = jogo_limpo(classe) if classe else jogo_limpo()
    jogo.jogador.armas = []
    bugs = []
    for deslocamento in deslocamentos:
        bug = Bug(jogo.jogador.posicao + deslocamento)
        bug.velocidade = 0
        bug.vida_maxima = 10_000
        bug.vida = 10_000
        bugs.append(bug)
        jogo.adicionar(bug)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    return jogo, bugs


def novas(jogo, tipo):
    jogo._incorporar_novas()
    return [e for e in jogo.entidades if isinstance(e, tipo)]


def no_maximo(arma):
    arma.nivel = arma.NIVEL_MAXIMO
    return arma


def rodar(jogo, entidades, segundos, dt=1 / 30):
    """Avança só as entidades dadas (e as que elas criarem do mesmo tipo), sem o resto do jogo."""
    tipos = tuple({type(e) for e in entidades})
    for _ in range(round(segundos / dt)):
        for entidade in [e for e in jogo.entidades if isinstance(e, tipos) and e.ativo]:
            entidade.atualizar(dt, jogo)
        jogo._incorporar_novas()


def vida(bug):
    return bug.vida


# ------------------------------------------------------------------ a regra

@pytest.mark.parametrize("classe, arma", EXCLUSIVAS.items())
def test_cada_classe_comeca_com_a_sua_arma_exclusiva(classe, arma):
    heroi = classe((0, 0))
    assert [type(a) for a in heroi.armas] == [arma] and heroi.arma_inicial is heroi.armas[0]
    assert arma.EXCLUSIVA


def test_so_as_armas_iniciais_sao_exclusivas():
    assert not Arma.EXCLUSIVA
    assert all(not a.EXCLUSIVA for a in Progressao.ARMAS)
    assert len(Progressao.ARMAS) == 11


@pytest.mark.parametrize("classe", CLASSES)
def test_nenhuma_carta_nem_bau_oferece_arma_exclusiva(classe):
    heroi = classe((0, 0))
    heroi.desbloqueios = frozenset(c.__name__ for c in Progressao.ARMAS)
    novas_armas = {o.origem for o in Progressao.candidatas(heroi) if o.tipo == "nova"}
    assert novas_armas and not any(getattr(o, "EXCLUSIVA", False) for o in novas_armas)


def test_nenhuma_colab_usa_arma_exclusiva():
    for receita in Colab.RECEITAS:
        assert not any(ingrediente.EXCLUSIVA for ingrediente in receita.INGREDIENTES), receita.NOME


def test_a_arma_exclusiva_continua_subindo_de_nivel_nas_cartas():
    heroi = Otaku((0, 0))
    assert any(o.tipo == "melhoria" and o.origem is Lightstick for o in Progressao.candidatas(heroi))


@pytest.mark.parametrize("classe", NOVAS)
def test_tabelas_das_armas_exclusivas_novas(classe):
    for valores in classe.ATRIBUTOS.values():
        assert len(valores) == classe.NIVEL_MAXIMO
    assert len(classe.MELHORIAS) == classe.NIVEL_MAXIMO - 1
    dano = classe.ATRIBUTOS["dano"]
    assert dano[3] >= 1.6 * dano[2]
    assert classe.NOME and classe.DESCRICAO and classe.ICONE


# ------------------------------------------------------------------ Lightstick

def test_lightstick_vai_acerta_volta_e_acerta_de_novo(jogo_limpo):
    jogo, (bug,) = jogo_com_bugs(jogo_limpo, (150, 0))
    golpes = []
    original = jogo.causar_dano
    jogo.causar_dano = lambda alvo, *a, **k: golpes.append(alvo) or original(alvo, *a, **k)
    assert Lightstick().disparar(jogo, jogo.jogador)
    [bastao] = novas(jogo, LightstickGirando)
    rodar(jogo, [bastao], 2.0)
    assert golpes == [bug, bug]                       # na ida e na volta
    assert not bastao.ativo                           # voltou para a mão


def test_lightstick_sem_alvo_nao_sai(jogo_limpo):
    jogo, _ = jogo_com_bugs(jogo_limpo, (900, 0))
    assert not Lightstick().disparar(jogo, jogo.jogador)


def test_coreografia_tres_lightsticks_que_estouram_em_notas(jogo_limpo):
    jogo, _ = jogo_com_bugs(jogo_limpo, (150, 0))
    no_maximo(Lightstick()).disparar(jogo, jogo.jogador)
    bastoes = novas(jogo, LightstickGirando)
    assert len(bastoes) == 3
    rodar(jogo, bastoes, 2.0)
    assert len(novas(jogo, NotaMusical)) == 3 * Lightstick.NOTAS


# ------------------------------------------------------------------ Teclado Mecânico

def test_teclado_bate_no_arco_e_solta_tecla_no_vizinho(jogo_limpo):
    jogo, (perto, vizinho) = jogo_com_bugs(jogo_limpo, (80, 0), (80, 160))
    jogo.jogador.direcao_mira = pygame.Vector2(1, 0)
    assert TecladoMecanico().disparar(jogo, jogo.jogador)
    [golpe] = novas(jogo, GolpeDoTeclado)
    golpe.atualizar(1 / 30, jogo)
    assert perto.vida < 10_000 and vizinho.vida == 10_000          # o vizinho está fora do arco
    [tecla] = novas(jogo, TeclaVoadora)
    assert tecla.velocidade.y > 0                                  # vai na direção do vizinho
    rodar(jogo, [tecla], 0.6)
    assert vizinho.vida < 10_000


def test_ctrl_alt_del_solta_onda_de_teclas(jogo_limpo):
    jogo, _ = jogo_com_bugs(jogo_limpo, (80, 0))
    no_maximo(TecladoMecanico()).disparar(jogo, jogo.jogador)
    [onda] = novas(jogo, OndaDeTeclas)
    onda.atualizar(1 / 30, jogo)
    assert len(novas(jogo, TeclaVoadora)) >= OndaDeTeclas.QUANTIDADE


# ------------------------------------------------------------------ Caneta de Correção

def test_caneta_de_correcao_estoca_e_marca_com_x(jogo_limpo):
    jogo, (bug,) = jogo_com_bugs(jogo_limpo, (70, 0))
    jogo.jogador.direcao_mira = pygame.Vector2(1, 0)
    caneta = CanetaDeCorrecao()
    assert caneta.disparar(jogo, jogo.jogador)
    [estocada] = novas(jogo, EstocadaDaCaneta)
    rodar(jogo, [estocada], 1.0)
    assert bug.vida < 10_000 and bug.marcado
    assert bug.fator_de_dano_recebido == pytest.approx(1 + caneta.valor("marca"))
    assert novas(jogo, XDeCorrecao) == []


def test_correcao_em_massa_risca_um_x_que_fere(jogo_limpo):
    jogo, (bug,) = jogo_com_bugs(jogo_limpo, (70, 0))
    jogo.jogador.direcao_mira = pygame.Vector2(1, 0)
    no_maximo(CanetaDeCorrecao()).disparar(jogo, jogo.jogador)
    rodar(jogo, novas(jogo, EstocadaDaCaneta), 1.0)
    [x] = novas(jogo, XDeCorrecao)
    antes = bug.vida
    x.atualizar(1 / 30, jogo)
    assert bug.vida < antes


def test_caneta_de_correcao_nao_estoca_o_vazio(jogo_limpo):
    jogo, _ = jogo_com_bugs(jogo_limpo, (400, 0))
    assert not CanetaDeCorrecao().disparar(jogo, jogo.jogador)


# ------------------------------------------------------------------ Mapa do Campus

def test_alfinete_avisa_no_chao_e_so_fere_quando_cai(jogo_limpo):
    jogo, (a, b) = jogo_com_bugs(jogo_limpo, (200, 0), (-200, 100))
    mapa = MapaDoCampus()
    assert mapa.disparar(jogo, jogo.jogador)
    alfinetes = novas(jogo, AlfineteDoMapa)
    assert len(alfinetes) == 2                          # dois inimigos, dois alfinetes (nível 1 solta até 2)
    rodar(jogo, alfinetes, AlfineteDoMapa.ATRASO * 0.5)
    assert a.vida == 10_000 and b.vida == 10_000       # ainda é só o aviso
    rodar(jogo, alfinetes, AlfineteDoMapa.ATRASO)
    assert a.vida < 10_000 and b.vida < 10_000


def test_mapa_sem_ninguem_por_perto_nao_solta(jogo_limpo):
    jogo, _ = jogo_com_bugs(jogo_limpo, (900, 0))
    assert not MapaDoCampus().disparar(jogo, jogo.jogador)


def test_gps_traca_rota_ate_o_maior_bolo(jogo_limpo):
    jogo, _ = jogo_com_bugs(jogo_limpo, (-300, 0), (400, 0), (420, 20), (400, 40), (430, -10))
    mapa = no_maximo(MapaDoCampus())
    mapa.disparar(jogo, jogo.jogador)
    alfinetes = novas(jogo, AlfineteDoMapa)
    assert len(alfinetes) == mapa.valor("quantidade")
    xs = [a.posicao.x - jogo.jogador.posicao.x for a in alfinetes]
    assert xs == sorted(xs) and xs[-1] > 350                       # do aluno até o bolo, à direita
    assert [a.espera for a in alfinetes] == sorted(a.espera for a in alfinetes)   # em sequência


# ------------------------------------------------------------------ colabs novas

@pytest.mark.parametrize("receita, ingredientes", [(AulaExpositiva, {Apostila, QuadroBranco}),
                                                    (Caramelo5G, {Caramelo, WifiEduroam}),
                                                    (CatapultaDoCerrado, {ReguaDeUmMetro, PequiExplosivo})])
def test_colab_nova_aparece_com_os_dois_no_maximo_e_libera_vaga(jogo_limpo, receita, ingredientes):
    assert receita in Colab.RECEITAS and set(receita.INGREDIENTES) == ingredientes
    jogo = jogo_limpo()
    heroi = jogo.jogador
    armas = [no_maximo(c()) for c in receita.INGREDIENTES]
    assert receita not in Colab.colabs_disponiveis(armas[:1] + [type(armas[1])()])
    for arma in armas:
        heroi.adicionar_arma(arma)
    assert receita in Colab.colabs_disponiveis(heroi.armas)
    antes = len(heroi.armas)
    heroi.aplicar_colab(receita, jogo)
    assert len(heroi.armas) == antes - 1 and any(type(a) is receita for a in heroi.armas)


def test_aula_expositiva_gira_o_quadro_fere_e_solta_folhas_que_atrasam(jogo_limpo):
    jogo, (bug,) = jogo_com_bugs(jogo_limpo, (150, 0))
    aula = AulaExpositiva()
    aula.atualizar(1 / 30, jogo, jogo.jogador)
    [quadro] = novas(jogo, QuadroGigante)
    rodar(jogo, [quadro], 3.0)
    assert bug.vida < 10_000
    folhas = novas(jogo, FolhaEmEspiral)
    assert folhas
    folhas[0].ao_acertar(bug, jogo)
    assert bug.lento > 0


def test_caramelo_5g_deixa_rastro_e_late_quando_o_sinal_cai(jogo_limpo):
    jogo, (bug,) = jogo_com_bugs(jogo_limpo, (130, 0))
    colab = Caramelo5G()
    for _ in range(round(30 * (colab.valor("queda") + 0.2))):
        colab.atualizar(1 / 30, jogo, jogo.jogador)
        jogo._incorporar_novas()
    assert novas(jogo, RastroDeSinal)
    [latido] = novas(jogo, Latido)
    latido.posicao = pygame.Vector2(bug.posicao)
    latido.atualizar(1 / 30, jogo)
    assert bug.vida < 10_000 and bug.travado > 0


def test_catapulta_lanca_pequis_por_cima_e_estouram_no_bolo(jogo_limpo):
    jogo, (perto, *bolo) = jogo_com_bugs(jogo_limpo, (60, 0), (400, 0), (410, 20), (420, -20))
    colab = CatapultaDoCerrado()
    colab.atualizar(1 / 30, jogo, jogo.jogador)
    pequis = novas(jogo, PequiEmArco)
    assert len(pequis) == colab.valor("quantidade")
    assert all(p.destino.distance_to(bolo[0].posicao) < 120 for p in pequis)
    from jogo.efeitos import EstouroDePequi
    rodar(jogo, pequis, PequiEmArco.VOO + 0.1)
    estouros = novas(jogo, EstouroDePequi)
    rodar(jogo, estouros, 0.1)
    assert perto.vida == 10_000                          # passou por cima de quem estava no caminho
    assert any(b.vida < 10_000 for b in bolo)


# ------------------------------------------------------------------ desenho

def test_armas_exclusivas_e_colabs_novas_desenham_sem_erro(jogo_limpo):
    jogo, _ = jogo_com_bugs(jogo_limpo, (80, 0), (200, 60), (400, 0), (410, 30))
    jogo.jogador.direcao_mira = pygame.Vector2(1, 0)
    for suprema in (False, True):
        for classe in NOVAS:
            arma = classe()
            if suprema:
                no_maximo(arma)
            arma.disparar(jogo, jogo.jogador)
    for receita in COLABS_NOVAS:
        receita().atualizar(1 / 30, jogo, jogo.jogador)
    tela = pygame.Surface((1280, 720))
    for _ in range(8):
        jogo._incorporar_novas()
        for entidade in list(jogo.entidades):
            if entidade.grupo in ("ajudante", "projetil", "efeito") and entidade.ativo:
                entidade.atualizar(1 / 30, jogo)
        jogo._incorporar_novas()
        jogo.desenhar(tela)


@pytest.mark.parametrize("classe", CLASSES)
def test_veterano_camarada_usa_a_arma_exclusiva_da_classe(jogo_limpo, classe):
    from jogo.ajudantes.ajudantes import Veterano
    from jogo.jogador.habilidades import VeteranoCamarada
    jogo, _ = jogo_com_bugs(jogo_limpo, (120, 0), (200, 40), classe=classe)
    heroi = jogo.jogador
    heroi.armas = [heroi.arma_inicial]
    habilidade = VeteranoCamarada()
    for _ in range(90):
        habilidade.atualizar(1 / 30, heroi, jogo)
        jogo._incorporar_novas()
        for entidade in [e for e in jogo.entidades if e.grupo in ("ajudante", "projetil", "efeito") and e.ativo]:
            entidade.atualizar(1 / 30, jogo)
    [veterano] = novas(jogo, Veterano)
    assert type(veterano.arma) is type(heroi.arma_inicial) and veterano.arma is not heroi.arma_inicial
