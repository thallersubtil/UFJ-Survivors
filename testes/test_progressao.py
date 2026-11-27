import random

import pytest

from jogo.armas.caramelo import Caramelo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.cobra_python import CobraPython
from jogo.armas.colabs import (AulaExpositiva, Caramelo5G, CatapultaDoCerrado, Colab, FakeNews, MetralhadoraDePrompts,
                               SerpenteEstelar)
from jogo.armas.wifi import WifiEduroam
from jogo.armas.gemini import Gemini
from jogo.itens.itens import ITENS, GarrafaTermica, MarmitaDoRU, TenisDeCorrida
from jogo.jogador.classes import MestreDeRPG, Programador, Otaku
from jogo.progressao import Progressao


def no_maximo(arma):
    while not arma.no_maximo:
        arma.subir_nivel()
    return arma


def test_tabelas_dos_itens():
    assert len(ITENS) == 18          # saíram Caderno de Resumos e Relógio de Pulso; entraram cinco
    for classe in ITENS:
        assert len(classe.MELHORIAS) == classe.NIVEL_MAXIMO - 1
        assert classe.NOME and classe.DESCRICAO and classe.ICONE


def test_efeitos_dos_itens():
    """Os itens refeitos e novos do semestre têm os testes próprios em test_itens_do_semestre.py."""
    j = MestreDeRPG((0, 0))
    for classe in (TenisDeCorrida, GarrafaTermica, MarmitaDoRU):
        j.adicionar_item(classe())
    assert j.mult_rolamento == pytest.approx(0.85)
    assert j.mult_cura == pytest.approx(1.2)
    assert j.vida_maxima == j.VIDA + MarmitaDoRU.VIDA_POR_NIVEL


def test_colab_so_aparece_com_as_duas_armas_no_maximo():
    armas = [Caramelo(), WifiEduroam()]
    assert Colab.colabs_disponiveis(armas) == []
    no_maximo(armas[0])
    assert Colab.colabs_disponiveis(armas) == []
    no_maximo(armas[1])
    assert Colab.colabs_disponiveis(armas) == [Caramelo5G]


def test_receitas_das_colabs():
    assert Colab.RECEITAS == [SerpenteEstelar, MetralhadoraDePrompts, FakeNews, AulaExpositiva, Caramelo5G,
                              CatapultaDoCerrado]
    assert set(Caramelo5G.INGREDIENTES) == {Caramelo, WifiEduroam}
    assert set(SerpenteEstelar.INGREDIENTES) == {CobraPython, Gemini}
    assert set(MetralhadoraDePrompts.INGREDIENTES) == {MascoteChatGPT, MascoteClaude}


def test_aplicar_colab_troca_as_duas_armas_pela_colab(jogo_limpo):
    jogo = jogo_limpo(Otaku)
    j = jogo.jogador
    inicial = j.armas[0]
    j.adicionar_arma(no_maximo(Caramelo()))
    j.adicionar_arma(no_maximo(WifiEduroam()))
    j.aplicar_colab(Caramelo5G, jogo)
    assert j.armas[0] is inicial and [type(a) for a in j.armas[1:]] == [Caramelo5G]
    assert {Caramelo, WifiEduroam} <= j.armas_em_colab
    for _ in range(30):
        jogo.atualizar(1 / 60)


@pytest.mark.parametrize("receita", Colab.RECEITAS)
def test_cada_colab_funciona_na_partida(jogo_limpo, receita):
    jogo = jogo_limpo()
    jogo.jogador.armas = [receita()]
    from jogo.inimigos.bug import Bug
    for i in range(10):
        bug = Bug(jogo.jogador.posicao + (150 + i * 20, 0), escala=30)
        bug.velocidade = 0
        jogo.adicionar(bug)
    for _ in range(240):
        jogo.atualizar(1 / 60)
    assert len(jogo.inimigos) < 10 or any(b.vida < b.vida_maxima for b in jogo.inimigos)   # feriu ou matou


def test_opcoes_de_nivel_sao_tres_e_validas():
    j = Programador((0, 0))
    opcoes = Progressao.gerar_opcoes(j, random.Random(1))
    assert len(opcoes) == 3
    assert len({o.titulo for o in opcoes}) == 3


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


def test_sem_nada_para_oferecer_aparecem_as_cartas_de_vida_e_de_moedas(jogo_limpo):
    jogo = jogo_limpo()
    j = jogo.jogador
    j.armas = [AulaExpositiva(), SerpenteEstelar(), MetralhadoraDePrompts(), Caramelo5G()]
    j.itens = []
    for classe in ITENS[:4]:
        item = classe()
        item.nivel = item.NIVEL_MAXIMO
        j.itens.append(item)
    j.habilidades = list(j.habilidades_da_classe)
    for habilidade in j.habilidades:
        habilidade.nivel = habilidade.NIVEL_MAXIMO
    opcoes = Progressao.gerar_opcoes(j, random.Random(2))
    assert [o.titulo for o in opcoes] == ["Lanche da Cantina", "Bolsa de Monitoria"]
    assert {o.tipo for o in opcoes} == {"maximo"}
    j.vida = 10
    Progressao.opcao_lanche().aplicar(j, jogo)
    assert j.vida == pytest.approx(10 + j.vida_maxima * Progressao.CURA_NO_MAXIMO * j.mult_cura)


def test_premio_do_bau_prefere_melhorar(jogo_limpo):
    jogo = jogo_limpo()
    premio = Progressao.premio_bau(jogo.jogador, random.Random(3))
    assert premio.tipo == "melhoria"
    premio.aplicar(jogo.jogador, jogo)
    assert jogo.jogador.armas[0].nivel == 2


def test_arma_que_virou_colab_nao_volta_como_nova():
    j = Otaku((0, 0))
    j.armas_em_colab = {Caramelo, WifiEduroam}
    j.armas = []
    j.desbloqueios = frozenset({"WifiEduroam"})
    titulos = {o.titulo for o in Progressao.candidatas(j)}
    assert "Caramelo" not in titulos and "Wi-Fi Eduroam" not in titulos


def test_limite_de_quatro_armas_e_quatro_itens():
    j = Programador((0, 0))
    assert j.MAX_ARMAS == 4 and j.MAX_ITENS == 4
    for classe in (Caramelo, MascoteChatGPT, MascoteClaude):
        j.adicionar_arma(classe())
    with pytest.raises(ValueError):
        j.adicionar_arma(Gemini())
    for classe in ITENS[:4]:
        j.adicionar_item(classe())
    with pytest.raises(ValueError):
        j.adicionar_item(ITENS[4]())


def test_no_limite_so_aparecem_melhorias():
    j = Programador((0, 0))
    for classe in (Caramelo, MascoteChatGPT, MascoteClaude):
        j.adicionar_arma(classe())
    for classe in ITENS[:4]:
        j.adicionar_item(classe())
    for habilidade in j.habilidades_da_classe:          # as habilidades não ocupam vaga, mas são só três
        j.adicionar_habilidade(habilidade)
    candidatas = Progressao.candidatas(j)
    assert candidatas and all(o.tipo == "melhoria" for o in candidatas)


def test_colab_funde_as_armas_e_libera_vaga_para_uma_nova(jogo_limpo):
    jogo = jogo_limpo()
    j = jogo.jogador                     # começa com o Teclado Mecânico, exclusivo do Programador
    for classe in (CobraPython, Gemini, MascoteChatGPT):
        j.adicionar_arma(classe())
    no_maximo(j.armas[1])
    no_maximo(j.armas[2])
    assert not any(o.tipo == "nova" and o.rotulo == "NOVA" for o in Progressao.candidatas(j))
    colab = next(o for o in Progressao.candidatas(j) if o.tipo == "colab")
    colab.aplicar(j, jogo)
    assert len(j.armas) == 3
    novas = {o.titulo for o in Progressao.candidatas(j) if o.rotulo == "NOVA"}
    assert novas == {"Caramelo", "Mascote do Claude", "Apostila", "Quadro Branco", "Régua de 1 Metro",
                     "Corrente de WhatsApp"}


def test_armas_tem_quatro_niveis_e_o_ultimo_e_bem_mais_forte():
    for classe in Progressao.ARMAS:
        assert classe.NIVEL_MAXIMO == 4
        dano = classe.ATRIBUTOS["dano"]
        assert dano[3] >= 1.6 * dano[2], classe.NOME          # o salto do nível máximo é o maior de todos
        assert dano[3] - dano[2] > dano[2] - dano[1], classe.NOME
        assert classe.MELHORIAS[-1].split(":")[0].isupper()     # a carta do nível máximo anuncia a forma nova


def test_no_nivel_maximo_o_que_a_arma_solta_sai_com_o_visual_supremo():
    class JogoFalso:
        def __init__(self):
            self.adicionados = []

        def adicionar(self, e):
            self.adicionados.append(e)

    from jogo.projeteis.projeteis import CobraProjetil
    arma, jogo = CobraPython(), JogoFalso()
    comum = arma.lancar(jogo, CobraProjetil((0, 0), (100, 0), 1))
    assert arma.aura is None and comum.aura is None
    no_maximo(arma)
    suprema = arma.lancar(jogo, CobraProjetil((0, 0), (100, 0), 1))
    assert suprema.aura == CobraPython.COR_SUPREMA and jogo.adicionados == [comum, suprema]
    quadro = suprema.animador.quadro_atual
    from jogo.nucleo.recursos import Recursos
    assert Recursos.suprema(quadro, suprema.aura).get_width() > quadro.get_width()      # maior e com contorno


@pytest.mark.parametrize("receita", Colab.RECEITAS)
def test_colab_ja_nasce_pronta_sem_bigorna_e_bate_mais_que_os_ingredientes(receita):
    colab = receita()
    assert colab.no_maximo and not colab.pode_afiar and colab.aura == receita.COR_SUPREMA
    with pytest.raises(ValueError):
        colab.subir_nivel()
    j = Programador((0, 0))
    j.armas = [colab]
    assert not [o for o in Progressao.candidatas(j) if o.titulo == colab.NOME]       # não volta às cartas
    assert colab.NOME not in [i.NOME for i in receita.INGREDIENTES]                   # é uma arma nova
    for ingrediente in receita.INGREDIENTES:
        if ingrediente is not MascoteClaude:        # o golpe único do Claude vira 20 prompts por segundo
            assert receita.ATRIBUTOS["dano"][0] > ingrediente.ATRIBUTOS["dano"][-1]


def test_colab_e_secreta_mas_garantida_quando_as_duas_armas_chegam_ao_maximo():
    j = Programador((0, 0))
    j.adicionar_arma(no_maximo(CobraPython()))
    assert not any(o.tipo == "colab" for o in Progressao.candidatas(j))       # nada avisa a receita antes
    j.adicionar_arma(no_maximo(Gemini()))
    for semente in range(20):
        opcoes = Progressao.gerar_opcoes(j, random.Random(semente))
        assert opcoes[0].tipo == "colab" and opcoes[0].rotulo == "COLAB SECRETA!"


def test_metralhadora_de_prompts_atira_sem_parar_na_direcao_da_mira(jogo_limpo):
    from jogo.formas_supremas import PromptDisparado
    jogo = jogo_limpo()
    jogo.jogador.armas = [MetralhadoraDePrompts()]
    for _ in range(60):
        jogo.atualizar(1 / 60)
    prompts = [e for e in jogo.entidades if isinstance(e, PromptDisparado)]
    assert len(prompts) >= 15
    assert all(p.velocidade.normalize().dot(jogo.jogador.direcao_mira) > 0.96 for p in prompts)


def test_bigorna_nao_afia_colab(jogo_limpo):
    from jogo.coletaveis.coletaveis import Bigorna
    jogo = jogo_limpo()
    colab = MetralhadoraDePrompts()
    jogo.jogador.armas = [colab]
    Bigorna(jogo.jogador.posicao).ao_coletar(jogo)
    assert colab.carimbos == 0


def test_cada_carta_tem_icone_proprio():
    """Arma, colab, item e habilidade não repetem ícone: na carta e no HUD, ícone igual confunde."""
    from collections import Counter
    from jogo.jogador.classes import CLASSES
    habilidades = [type(h) for classe in CLASSES for h in classe((0, 0)).habilidades_da_classe]
    cartas = list(Progressao.ARMAS) + list(Colab.RECEITAS) + list(ITENS) + habilidades
    repetidos = {icone: n for icone, n in Counter(c.ICONE for c in cartas).items() if n > 1}
    assert not repetidos
