"""Itens do semestre de 20 min: os refeitos (Energético, Mochila, Marmita, Fone) e os novos (Atestado Médico,
Noite sem Dormir, Pré-treino Duvidoso, Parcelar no Cartão, Mensalidade da Atlética)."""
import pygame
import pytest

from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.itens.itens import (AtestadoMedico, Cola, Energetico, FoneDeOuvido, ITENS, MarmitaDoRU,
                              MensalidadeDaAtletica, MochilaPesada, NoiteSemDormir, OculosDeGrau, ParcelarNoCartao,
                              PreTreinoDuvidoso)
from jogo.jogador.classes import MestreDeRPG, Programador


def no_nivel(item, nivel):
    item.nivel = nivel
    return item


def colocar(jogo, deslocamento, nome="pente_ram", escala=1.0):
    inimigo = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + pygame.Vector2(deslocamento), escala)
    jogo.adicionar(inimigo)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    return inimigo


def test_sairam_caderno_e_relogio():
    nomes = {classe.__name__ for classe in ITENS}
    assert not {"CadernoDeResumos", "RelogioDePulso", "BandejaoCompleto"} & nomes
    assert {"AtestadoMedico", "NoiteSemDormir", "PreTreinoDuvidoso", "ParcelarNoCartao",
            "MensalidadeDaAtletica"} <= nomes


def test_energetico_corre_mais_e_vive_menos():
    j = MestreDeRPG((0, 0))
    j.adicionar_item(no_nivel(Energetico(), 4))
    j.recalcular_atributos()
    assert j.mult_velocidade == pytest.approx(1.4)
    assert j.mult_recarga == pytest.approx(0.9)
    assert j.vida_maxima == pytest.approx(j.VIDA * 0.8)


def test_marmita_da_vida_e_reforca_a_arma_inicial_e_o_especial():
    j = MestreDeRPG((0, 0))
    inicial = j.armas[0]
    antes = inicial.valor("dano")
    j.adicionar_item(no_nivel(MarmitaDoRU(), 4))
    j.recalcular_atributos()
    assert j.vida_maxima == j.VIDA + 60
    esperado = 1 + j.vida_maxima / MarmitaDoRU.VIDA_POR_PONTO / 100
    assert inicial.valor("dano") == pytest.approx(antes * esperado)
    assert j.especial.reforco == pytest.approx(esperado)


def test_mochila_reduz_o_dano_deixa_lento_e_devolve(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    heroi = jogo.jogador
    heroi.adicionar_item(no_nivel(MochilaPesada(), 4))
    heroi.recalcular_atributos()
    assert heroi.mult_velocidade == pytest.approx(1 - MochilaPesada.LENTIDAO)
    alvo = colocar(jogo, (60, 0), escala=100)
    vida_alvo = alvo.vida
    jogo.rng.random = lambda: 0.0                 # sempre devolve
    jogo.ferir_jogador(40)
    assert heroi.vida == pytest.approx(heroi.vida_maxima - 30)
    assert alvo.vida < vida_alvo


def test_fone_de_ouvido_anula_o_golpe_e_empurra(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    heroi = jogo.jogador
    heroi.adicionar_item(FoneDeOuvido())
    alvo = colocar(jogo, (80, 0))
    jogo.rng.random = lambda: 0.0
    assert not jogo.ferir_jogador(30) and heroi.vida == heroi.vida_maxima
    assert alvo.empurrao.length() > 0


def test_atestado_medico_salva_uma_vez_e_derruba_os_comuns(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    heroi = jogo.jogador
    heroi.adicionar_item(AtestadoMedico())
    comum = colocar(jogo, (100, 0))
    mini = colocar(jogo, (150, 0), "tia_da_cantina")
    assert not jogo.ferir_jogador(heroi.vida * 10)
    jogo._incorporar_novas()
    assert heroi.vida == pytest.approx(heroi.vida_maxima * AtestadoMedico.VIDA)
    assert not comum.ativo and mini.ativo
    assert not any(isinstance(i, AtestadoMedico) for i in heroi.itens)     # gastou: a vaga fica livre
    heroi.invencivel = 0
    jogo.ferir_jogador(heroi.vida * 10)
    assert not heroi.esta_vivo


def test_noite_sem_dormir_bate_mais_e_apanha_mais(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    heroi = jogo.jogador
    heroi.adicionar_item(no_nivel(NoiteSemDormir(), 4))
    assert heroi.mult_dano == pytest.approx(1.3) and heroi.mult_recarga == pytest.approx(0.9)
    jogo.ferir_jogador(10)
    assert heroi.vida == pytest.approx(heroi.vida_maxima - 13)


def test_pre_treino_escorre_a_vida_ate_sobrar_1(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    heroi = jogo.jogador
    heroi.armas = []
    heroi.adicionar_item(no_nivel(PreTreinoDuvidoso(), 4))
    assert heroi.mult_dano == pytest.approx(1.4)
    for _ in range(30 * 25):
        jogo.atualizar(1 / 30)
    assert heroi.vida == pytest.approx(1) and heroi.esta_vivo


def test_parcelar_no_cartao_cobra_o_resto_aos_poucos(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    heroi = jogo.jogador
    heroi.armas = []
    cartao = ParcelarNoCartao()
    heroi.adicionar_item(cartao)
    jogo.ferir_jogador(20)
    assert heroi.vida == pytest.approx(heroi.vida_maxima - 6) and cartao.em_aberto == pytest.approx(14)
    for _ in range(30 * 4):
        jogo.atualizar(1 / 30)
    assert cartao.em_aberto == 0 and heroi.vida == pytest.approx(heroi.vida_maxima - 20, abs=0.5)


def rodar(jogo, segundos):
    for _ in range(round(30 * segundos)):
        jogo.atualizar(1 / 30)


@pytest.mark.parametrize("cartao_primeiro", [True, False])
def test_parcela_que_mataria_passa_pelo_atestado_em_qualquer_ordem(jogo_limpo, cartao_primeiro):
    jogo = jogo_limpo(MestreDeRPG)
    heroi = jogo.jogador
    heroi.armas = []
    cartao, atestado = ParcelarNoCartao(), AtestadoMedico()
    for item in ((cartao, atestado) if cartao_primeiro else (atestado, cartao)):
        heroi.adicionar_item(item)
    jogo.ferir_jogador(heroi.vida * 2)           # na hora entra só 60% da vida; o resto mataria em parcelas
    rodar(jogo, 6)
    assert heroi.esta_vivo
    assert atestado not in heroi.itens and cartao.em_aberto == 0


def test_parcela_que_mataria_passa_pelo_bis(jogo_limpo):
    from jogo.jogador.classes import Otaku
    from jogo.jogador.habilidades import Bis
    jogo = jogo_limpo(Otaku)
    heroi = jogo.jogador
    heroi.armas = []
    heroi.adicionar_item(ParcelarNoCartao())         # itens vêm antes das habilidades nos reagentes
    heroi.adicionar_habilidade(next(h for h in heroi.habilidades_da_classe if isinstance(h, Bis)))
    jogo.ferir_jogador(heroi.vida * 2)
    rodar(jogo, 6)
    assert heroi.esta_vivo and heroi.itens[0].em_aberto == 0


def test_parcela_nao_cobra_durante_a_invencibilidade(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    heroi = jogo.jogador
    heroi.armas = []
    cartao = ParcelarNoCartao()
    heroi.adicionar_item(cartao)
    jogo.ferir_jogador(20)
    vida = heroi.vida
    heroi.invencivel = 10
    rodar(jogo, 2)
    assert cartao.em_aberto == pytest.approx(14) and heroi.vida == pytest.approx(vida)


def test_marmita_reforca_a_propria_arma_inicial_e_nao_a_colab_que_ela_vira():
    j = MestreDeRPG((0, 0))
    assert j.armas == [j.arma_inicial]               # a mesma instância, sem criar uma arma a mais
    outra = type(j.arma_inicial)()                    # outra do mesmo tipo (veterano, carta) não é a inicial
    j.armas.append(outra)
    j.adicionar_item(no_nivel(MarmitaDoRU(), 4))
    assert j.arma_inicial.reforco > 1 and outra.reforco == 1.0
    j.armas.remove(j.arma_inicial)                    # virou colab: o reforço sai junto
    j.recalcular_atributos()
    assert all(a.reforco == 1.0 for a in j.armas)


def test_mensalidade_cobra_moedas_e_da_bonus_enquanto_paga(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    heroi = jogo.jogador
    heroi.armas = []
    heroi.adicionar_item(no_nivel(MensalidadeDaAtletica(), 4))
    jogo.placar.moedas = 4
    jogo.atualizar(1 / 30)
    assert heroi.multiplicador("dano") == pytest.approx(1.3)
    for _ in range(30 * 2):
        jogo.atualizar(1 / 30)
    assert jogo.placar.moedas == 0
    for _ in range(30):
        jogo.atualizar(1 / 30)
    assert heroi.multiplicador("dano") == 1


def test_oculos_disfarcam_a_cola_sem_perguntar_o_tipo(jogo_limpo):
    jogo = jogo_limpo(Programador)
    heroi = jogo.jogador
    cola = Cola()
    heroi.adicionar_item(cola)
    sem = cola.chance_de_flagra(heroi, jogo)
    heroi.adicionar_item(no_nivel(OculosDeGrau(), 2))
    assert cola.chance_de_flagra(heroi, jogo) == pytest.approx(sem * 0.6)
    assert Cola().disfarce_de_cola == 0
