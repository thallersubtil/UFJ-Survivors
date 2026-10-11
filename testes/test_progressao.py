import random

import pytest

from jogo.armas.caramelo import Caramelo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.cobra_python import CobraPython
from jogo.armas.colabs import CarameloNoFusca, Colab, CobrasGemeas, DebateDasIAs
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.itens.itens import ITENS, FoneDeOuvido, GarrafaTermica, MarmitaDoRU, MochilaPesada, RelogioDePulso
from jogo.jogador.alunos import AlunoAgil, AlunoResistente
from jogo.progressao import Progressao


def no_maximo(arma):
    while not arma.no_maximo:
        arma.subir_nivel()
    return arma


def test_tabelas_dos_itens():
    assert len(ITENS) == 7
    for classe in ITENS:
        assert len(classe.MELHORIAS) == classe.NIVEL_MAXIMO - 1
        assert classe.NOME and classe.DESCRICAO and classe.ICONE


def test_efeitos_dos_itens():
    j = AlunoAgil((0, 0))
    for classe in (FoneDeOuvido, RelogioDePulso, GarrafaTermica, MarmitaDoRU, MochilaPesada):
        j.adicionar_item(classe())
    assert j.alcance_coleta == pytest.approx(90 * 1.3)
    assert j.mult_recarga == pytest.approx(0.92)
    assert j.mult_cafe == pytest.approx(1.25)
    assert j.regeneracao == pytest.approx(1 / 3)
    assert j.vida_maxima == 100


def test_colab_so_aparece_com_as_duas_armas_no_maximo():
    armas = [Caramelo(), FuscaAzul()]
    assert Colab.colabs_disponiveis(armas) == []
    no_maximo(armas[0])
    assert Colab.colabs_disponiveis(armas) == []
    no_maximo(armas[1])
    assert Colab.colabs_disponiveis(armas) == [CarameloNoFusca]


def test_receitas_das_tres_colabs():
    assert set(CarameloNoFusca.INGREDIENTES) == {Caramelo, FuscaAzul}
    assert set(CobrasGemeas.INGREDIENTES) == {CobraPython, Gemini}
    assert set(DebateDasIAs.INGREDIENTES) == {MascoteChatGPT, MascoteClaude}


def test_aplicar_colab_troca_as_duas_armas_pela_colab(jogo_limpo):
    jogo = jogo_limpo(AlunoResistente)
    j = jogo.jogador
    no_maximo(j.armas[0])
    j.adicionar_arma(no_maximo(FuscaAzul()))
    j.aplicar_colab(CarameloNoFusca, jogo)
    assert [type(a) for a in j.armas] == [CarameloNoFusca]
    assert {Caramelo, FuscaAzul} <= j.armas_em_colab
    for _ in range(30):
        jogo.atualizar(1 / 60)


@pytest.mark.parametrize("receita", [CarameloNoFusca, CobrasGemeas, DebateDasIAs])
def test_cada_colab_funciona_na_partida(jogo_limpo, receita):
    jogo = jogo_limpo()
    jogo.jogador.armas = [receita()]
    from jogo.inimigos.bug import Bug
    for i in range(10):
        bug = Bug(jogo.jogador.posicao + (150 + i * 20, 40), escala=30)
        bug.velocidade = 0
        jogo.adicionar(bug)
    for _ in range(240):
        jogo.atualizar(1 / 60)
    assert any(b.vida < b.vida_maxima for b in jogo.inimigos)


def test_opcoes_de_nivel_sao_tres_e_validas():
    j = AlunoAgil((0, 0))
    opcoes = Progressao.gerar_opcoes(j, random.Random(1))
    assert len(opcoes) == 3
    assert len({o.titulo for o in opcoes}) == 3


def test_colab_disponivel_sempre_aparece_primeiro():
    j = AlunoAgil((0, 0))
    no_maximo(j.armas[0])
    j.adicionar_arma(no_maximo(Gemini()))
    opcoes = Progressao.gerar_opcoes(j, random.Random(5))
    assert opcoes[0].tipo == "colab"


def test_aplicar_opcoes_de_melhoria_e_de_arma_nova(jogo_limpo):
    jogo = jogo_limpo()
    j = jogo.jogador
    candidatas = Progressao.candidatas(j)
    melhoria = next(o for o in candidatas if o.tipo == "melhoria")
    melhoria.aplicar(j, jogo)
    assert j.armas[0].nivel == 2
    nova = next(o for o in candidatas if o.tipo == "nova" and o.titulo == "Gemini")
    nova.aplicar(j, jogo)
    assert isinstance(j.armas[-1], Gemini)


def test_sem_nada_para_oferecer_aparece_o_lanche(jogo_limpo):
    jogo = jogo_limpo()
    j = jogo.jogador
    j.armas = [CarameloNoFusca(), CobrasGemeas(), DebateDasIAs(), CarameloNoFusca(), CobrasGemeas(), DebateDasIAs()]
    j.itens = []
    for classe in ITENS[:6]:
        item = classe()
        item.nivel = item.NIVEL_MAXIMO
        j.itens.append(item)
    opcoes = Progressao.gerar_opcoes(j, random.Random(2))
    assert [o.tipo for o in opcoes] == ["lanche"]
    j.vida = 10
    opcoes[0].aplicar(j, jogo)
    assert j.vida == 40


def test_premio_do_bau_prefere_melhorar(jogo_limpo):
    jogo = jogo_limpo()
    premio = Progressao.premio_bau(jogo.jogador, random.Random(3))
    assert premio.tipo == "melhoria"
    premio.aplicar(jogo.jogador, jogo)
    assert jogo.jogador.armas[0].nivel == 2


def test_arma_que_virou_colab_nao_volta_como_nova():
    j = AlunoResistente((0, 0))
    j.armas_em_colab = {Caramelo, FuscaAzul}
    j.armas = []
    titulos = {o.titulo for o in Progressao.candidatas(j)}
    assert "Caramelo" not in titulos and "Fusca Azul" not in titulos
