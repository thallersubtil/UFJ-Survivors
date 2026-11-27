"""As armas disparam só pela recarga; a munição do jogo é o café da garrafa da Virada de Noite (Programador).
Também: o Programador e as cartas de quem já levou tudo ao nível máximo."""
import random
from types import SimpleNamespace

import pygame
import pytest

from jogo.armas.arma import Arma, ArmaContinua, ArmaDeDisparo
from jogo.armas.cobra_python import CobraPython
from jogo.armas.colabs import CarameloNoFusca, MetralhadoraDePrompts, SerpenteEstelar
from jogo.inimigos.bug import Bug
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.itens.itens import ITENS, GarrafaTermica
from jogo.jogador.classes import Gamer, MestreDeRPG, Programador
from jogo.jogador.especiais import TelaAzul, ViradaDeNoite
from jogo.jogador.habilidades import Cafeinado, Compilar, LacoDeRepeticao
from jogo.progressao import Progressao
from jogo.projeteis.projeteis import ProjetilDaMateria


class Estilingue(ArmaDeDisparo):
    NOME = "Estilingue"
    ATRIBUTOS = {"dano": (1, 2, 3, 4), "recarga": (1.0, 1.0, 1.0, 1.0)}
    MELHORIAS = ("a", "b", "c")

    def __init__(self):
        super().__init__()
        self.disparos = 0
        self.tem_alvo = True

    def disparar(self, jogo, dono):
        if not self.tem_alvo:
            return False
        self.disparos += 1
        return True


def dono(repeticao=0.0, recarga=1.0):
    return SimpleNamespace(multiplicador_recarga=recarga, multiplicador_dano=1.0, chance_repeticao=repeticao,
                           chance=lambda base: base)


def jogo_falso(sorteio=0.99):
    return SimpleNamespace(rng=SimpleNamespace(random=lambda: sorteio))


# ---------------------------------------------------------------- armas só pela recarga

def test_as_armas_nao_tem_municao_a_municao_e_a_garrafa_do_programador():
    arma = Estilingue()
    for nome in ("municao", "municao_maxima", "tem_cafe", "fracao_cafe", "encher"):
        assert not hasattr(arma, nome), nome
    especial = Programador((0, 0)).especial
    assert isinstance(especial, ViradaDeNoite) and especial.garrafa.municao == 0
    assert not hasattr(MestreDeRPG((0, 0)).especial, "garrafa")


def test_arma_de_disparo_atira_sempre_que_a_recarga_acaba():
    arma = Estilingue()
    for _ in range(100):                    # 10 segundos, recarga de 1 s: nunca falta nada
        arma.atualizar(0.1, jogo_falso(), dono())
    assert arma.disparos == 10


def test_espera_tem_property_com_validacao():
    arma = Estilingue()
    assert arma.espera == 0
    arma.espera = 0.5
    assert arma.espera == 0.5
    with pytest.raises(ValueError):
        arma.espera = -0.1
    for errado in ("1", None, True):
        with pytest.raises(TypeError):
            arma.espera = errado
    assert arma.espera == 0.5               # valor inválido não muda nada


def test_fracao_de_recarga_vai_de_zero_a_um_para_o_hud():
    arma = Estilingue()
    assert arma.fracao_de_recarga == 1
    arma.atualizar(0.1, jogo_falso(), dono())
    assert arma.espera == pytest.approx(1.0) and arma.fracao_de_recarga == pytest.approx(0)
    arma.atualizar(0.25, jogo_falso(), dono())
    assert arma.fracao_de_recarga == pytest.approx(0.25)
    assert CarameloNoFusca().fracao_de_recarga is None        # arma contínua não tem recarga de disparo


def test_sem_alvo_tenta_de_novo_logo_e_recarga_mais_rapida_encurta_a_espera():
    arma = Estilingue()
    arma.tem_alvo = False
    arma.atualizar(0.1, jogo_falso(), dono())
    assert arma.espera == pytest.approx(ArmaDeDisparo.ESPERA_SEM_ALVO)
    arma.tem_alvo = True
    arma.espera = 0
    arma.atualizar(0.1, jogo_falso(), dono(recarga=0.5))
    assert arma.espera == pytest.approx(0.5)


def test_as_duas_familias_de_arma():
    assert issubclass(ArmaDeDisparo, Arma) and issubclass(ArmaContinua, Arma)
    assert issubclass(CobraPython, ArmaDeDisparo) and issubclass(MetralhadoraDePrompts, ArmaContinua)
    with pytest.raises(TypeError):
        ArmaDeDisparo()
    with pytest.raises(TypeError):
        ArmaContinua()


# ---------------------------------------------------------------- o que entrou no lugar do café

# (a lata de energético que entrou no lugar do copo de café durou um dia: virou o ímã, em test_ima_cura_e_quebraveis)


def test_garrafa_termica_faz_toda_cura_render_mais():
    heroi = MestreDeRPG((0, 0))
    heroi.adicionar_item(GarrafaTermica())
    heroi.itens[0].nivel = 2
    heroi.recalcular_atributos()
    assert heroi.mult_cura == pytest.approx(1 + 2 * GarrafaTermica.CURA_POR_NIVEL)
    heroi.vida = 10
    heroi.curar(10)
    assert heroi.vida == pytest.approx(10 + 10 * heroi.mult_cura)
    assert "café" not in (GarrafaTermica.DESCRICAO + "".join(GarrafaTermica.MELHORIAS)).lower()


def test_cafe_e_municao_so_aparecem_no_programador():
    """Só o Programador fala de café (Virada de Noite, Cafeinado); armas, itens, loja e as outras classes não."""
    from jogo.jogador.classes import CLASSES
    from jogo.loja.lanches import LANCHES
    from jogo.loja.melhorias import MELHORIAS
    textos = []
    for classe in CLASSES:
        if classe is Programador:
            continue
        heroi = classe((0, 0))
        textos += [classe.DESCRICAO, heroi.especial.NOME, heroi.especial.DESCRICAO]
        textos += [t for h in heroi.habilidades_da_classe for t in (h.NOME, h.DESCRICAO, *h.MELHORIAS)]
    for classe in Progressao.ARMAS + tuple(ITENS) + tuple(LANCHES) + tuple(MELHORIAS) + \
            (CarameloNoFusca, SerpenteEstelar, MetralhadoraDePrompts):
        textos += [classe.NOME, classe.DESCRICAO, *getattr(classe, "MELHORIAS", ())]
    for texto in textos:
        assert "café" not in texto.lower() and "munição" not in texto.lower(), texto
    assert "café" in (ViradaDeNoite.DESCRICAO + Programador.DESCRICAO).lower()


# ---------------------------------------------------------------- Programador

def test_programador_tem_habilidades_e_especial_novos():
    heroi = Programador((0, 0))
    assert [type(h) for h in heroi.habilidades_da_classe] == [LacoDeRepeticao, Cafeinado, Compilar]
    assert isinstance(heroi.especial, ViradaDeNoite) and isinstance(heroi.armas[0], CobraPython)


def test_laco_de_repeticao_cresce_com_a_carta():
    heroi = Programador((0, 0))
    laco = heroi.habilidades_da_classe[0]
    heroi.adicionar_habilidade(laco)
    assert heroi.chance_repeticao == pytest.approx(LacoDeRepeticao.CHANCE[0])
    heroi.subir_nivel_habilidade(laco)
    heroi.subir_nivel_habilidade(laco)
    assert heroi.chance_repeticao == pytest.approx(LacoDeRepeticao.CHANCE[2])
    assert MestreDeRPG((0, 0)).chance_repeticao == 0


def test_disparo_repetido_sai_logo_em_seguida():
    arma = Estilingue()
    arma.atualizar(0.1, jogo_falso(sorteio=0.0), dono(repeticao=0.3))       # sorteio abaixo da chance: repete
    assert arma.disparos == 1 and arma.espera == pytest.approx(ArmaDeDisparo.ESPERA_DA_REPETICAO)
    arma.atualizar(ArmaDeDisparo.ESPERA_DA_REPETICAO, jogo_falso(sorteio=0.9), dono(repeticao=0.3))
    assert arma.disparos == 2 and arma.espera == pytest.approx(1.0)           # não repetiu: recarga normal


def test_sem_o_laco_de_repeticao_o_disparo_nem_sorteia():
    def explodir():
        raise AssertionError("não deveria sortear")
    arma = Estilingue()
    arma.atualizar(0.1, SimpleNamespace(rng=SimpleNamespace(random=explodir)), dono(repeticao=0.0))
    assert arma.disparos == 1


def test_programador_atira_mais_que_outra_classe_com_a_mesma_arma(jogo_limpo):
    disparos = {}
    for classe in (Programador, MestreDeRPG):
        jogo = jogo_limpo(classe)
        heroi = jogo.jogador
        heroi.imortal = True
        heroi.armas = [Estilingue()]
        for habilidade in heroi.habilidades_da_classe[:1]:          # Laço de Repetição (Programador) no máximo
            heroi.adicionar_habilidade(habilidade)
            habilidade.nivel = habilidade.NIVEL_MAXIMO
        heroi.recalcular_atributos()
        for _ in range(60 * 60):
            jogo.atualizar(1 / 60)
        disparos[classe] = heroi.armas[0].disparos
    assert disparos[Programador] > disparos[MestreDeRPG] * 1.2


def test_tela_azul_trava_os_inimigos_e_apaga_os_projeteis_deles(jogo_limpo):
    jogo = jogo_limpo(Gamer)
    heroi = jogo.jogador
    heroi.imortal = True
    heroi.armas = []
    perto = Bug(heroi.posicao + (200, 0))
    chefe = FabricaDeInimigos.criar("chefe_calculo", heroi.posicao + (0, 300))
    tiro = ProjetilDaMateria(heroi.posicao + (150, 150), (0, 0), 5, "dx", (255, 255, 255))
    for entidade in (perto, chefe, tiro):
        jogo.adicionar(entidade)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    assert heroi.usar_especial(jogo)
    assert not tiro.ativo
    assert perto.travado == pytest.approx(TelaAzul.DURACAO) and chefe.travado == 0     # chefe tem tenacidade total
    parado = pygame.Vector2(perto.posicao)
    for _ in range(30):
        jogo.atualizar(1 / 60)
    assert perto.posicao == parado
    for _ in range(round(60 * TelaAzul.DURACAO)):
        jogo.atualizar(1 / 60)
    assert perto.travado == 0 and perto.posicao != parado


# ---------------------------------------------------------------- cartas no nível máximo

def aluno_com_tudo_no_maximo(jogo):
    heroi = jogo.jogador
    heroi.armas = [CarameloNoFusca(), SerpenteEstelar(), MetralhadoraDePrompts(), CarameloNoFusca()]
    heroi.itens = []
    for classe in ITENS[:4]:
        item = classe()
        item.nivel = item.NIVEL_MAXIMO
        heroi.itens.append(item)
    heroi.habilidades = list(heroi.habilidades_da_classe)
    for habilidade in heroi.habilidades:
        habilidade.nivel = habilidade.NIVEL_MAXIMO
    heroi.recalcular_atributos()
    return heroi


def test_com_tudo_no_maximo_as_cartas_sao_vida_ou_50_moedas(jogo_limpo):
    jogo = jogo_limpo()
    heroi = aluno_com_tudo_no_maximo(jogo)
    opcoes = Progressao.gerar_opcoes(heroi, random.Random(2))
    assert len(opcoes) == 2 and {o.tipo for o in opcoes} == {"maximo"}
    vida, moedas = sorted(opcoes, key=lambda o: "moedas" in o.descricao)
    heroi.vida = 1
    vida.aplicar(heroi, jogo)
    assert heroi.vida == pytest.approx(1 + heroi.vida_maxima * Progressao.CURA_NO_MAXIMO)
    heroi.mult_moedas = 2.0                                   # a carta paga 50 certinho, sem multiplicador
    moedas.aplicar(heroi, jogo)
    assert jogo.placar.moedas == Progressao.MOEDAS_NO_MAXIMO == 50


def test_antes_do_maximo_as_cartas_continuam_sendo_armas_e_itens(jogo_limpo):
    jogo = jogo_limpo()
    opcoes = Progressao.gerar_opcoes(jogo.jogador, random.Random(2))
    assert len(opcoes) == 3 and "maximo" not in {o.tipo for o in opcoes}
