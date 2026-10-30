"""Moedas, progresso salvo, melhorias permanentes e desbloqueios da loja do Centro Acadêmico."""
import json

import pytest

from jogo.armas.pequi import PequiExplosivo
from jogo.armas.wifi import WifiEduroam
from jogo.coletaveis.coletaveis import Moeda
from jogo.itens.itens import OculosDeGrau, TenisDeCorrida
from jogo.jogador.classes import Programador
from jogo.loja.melhorias import MELHORIAS, Melhoria, Monitoria, TreinoNoGinasio
from jogo.loja.progresso import Progresso
from jogo.opcoes import OpcoesDePartida
from jogo.placar import Placar
from jogo.progressao import Progressao


def test_progresso_valida_as_moedas(tmp_path):
    p = Progresso(tmp_path / "progresso.json")
    assert p.moedas == 0
    p.ganhar(50)
    assert p.moedas == 50
    with pytest.raises(ValueError):
        p.gastar(51)
    p.gastar(20)
    assert p.moedas == 30
    with pytest.raises(ValueError):
        p.moedas = -1
    with pytest.raises(TypeError):
        p.moedas = 2.5
    with pytest.raises(ValueError):
        p.ganhar(-3)


def test_progresso_sobrevive_a_fechar_o_jogo(tmp_path):
    caminho = tmp_path / "progresso.json"
    p = Progresso(caminho)
    p.ganhar(10_000)
    assert p.comprar_melhoria(TreinoNoGinasio)
    assert p.desbloquear(PequiExplosivo)
    de_novo = Progresso(caminho)
    assert de_novo.moedas == p.moedas
    assert de_novo.nivel_de(TreinoNoGinasio) == 1
    assert de_novo.desbloqueado(PequiExplosivo)


def test_arquivo_estragado_comeca_do_zero(tmp_path):
    caminho = tmp_path / "progresso.json"
    caminho.write_text("{ isto não é json", encoding="utf-8")
    assert Progresso(caminho).moedas == 0
    caminho.write_text(json.dumps({"moedas": -5, "melhorias": {"x": "y"}}), encoding="utf-8")
    assert Progresso(caminho).moedas == 0


def test_melhoria_fica_mais_cara_e_para_no_maximo(tmp_path):
    p = Progresso(tmp_path / "p.json")
    p.ganhar(1_000_000)
    custos = []
    while p.nivel_de(Monitoria) < Monitoria.NIVEL_MAXIMO:
        custos.append(Monitoria.custo(p.nivel_de(Monitoria)))
        assert p.comprar_melhoria(Monitoria)
    assert custos == sorted(custos) and len(set(custos)) == len(custos)
    assert not p.comprar_melhoria(Monitoria)


def test_sem_dinheiro_nao_compra_nem_desconta(tmp_path):
    p = Progresso(tmp_path / "p.json")
    assert not p.comprar_melhoria(TreinoNoGinasio)
    assert not p.desbloquear(WifiEduroam)
    assert p.moedas == 0 and p.nivel_de(TreinoNoGinasio) == 0


def test_tabela_das_melhorias():
    assert len(MELHORIAS) >= 8
    assert len({m.CHAVE for m in MELHORIAS}) == len(MELHORIAS)
    for classe in MELHORIAS:
        assert issubclass(classe, Melhoria)
        assert classe.NOME and classe.DESCRICAO and classe.ICONE and classe.NIVEL_MAXIMO >= 1


def test_melhorias_compradas_entram_na_partida(tmp_path):
    p = Progresso(tmp_path / "p.json")
    p.ganhar(100_000)
    p.comprar_melhoria(TreinoNoGinasio)
    p.comprar_melhoria(TreinoNoGinasio)
    base = Programador((0, 0)).velocidade
    j = Programador((0, 0))
    j.receber_melhorias(p.melhorias_compradas())
    assert j.velocidade == pytest.approx(base * (1 + 2 * TreinoNoGinasio.POR_NIVEL))
    opcoes = OpcoesDePartida().com_progresso(p)
    assert opcoes.melhorias and isinstance(opcoes.desbloqueios, frozenset)


def test_cada_melhoria_mexe_em_algum_atributo():
    for classe in MELHORIAS:
        antes, depois = Programador((0, 0)), Programador((0, 0))
        depois.receber_melhorias([classe(classe.NIVEL_MAXIMO)])
        atributos = ("velocidade", "multiplicador_dano", "multiplicador_recarga", "chance_critico", "vida_maxima",
                     "alcance_coleta", "mult_rolamento", "mult_experiencia", "mult_moedas")
        assert any(getattr(antes, a) != getattr(depois, a) for a in atributos), classe.NOME


def test_conteudo_novo_so_aparece_nas_cartas_depois_de_comprado():
    novas = {PequiExplosivo, WifiEduroam, TenisDeCorrida, OculosDeGrau}
    for classe in novas:
        assert classe.PRECO_DESBLOQUEIO > 0
    j = Programador((0, 0))
    titulos = {o.titulo for o in Progressao.candidatas(j)}
    assert not titulos & {c.NOME for c in novas}
    j.desbloqueios = frozenset(c.__name__ for c in novas)
    titulos = {o.titulo for o in Progressao.candidatas(j)}
    assert {c.NOME for c in novas} <= titulos


def test_placar_conta_moedas_validadas():
    p = Placar()
    p.adicionar_moedas(7)
    assert p.moedas == 7
    with pytest.raises(ValueError):
        p.adicionar_moedas(-1)
    with pytest.raises(TypeError):
        p.moedas = 1.5


def test_moeda_coletada_vai_para_o_placar_com_bonus(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.mult_moedas = 1.5
    jogo.adicionar(Moeda(jogo.jogador.posicao, 10))
    jogo.atualizar(1 / 60)
    assert jogo.placar.moedas == 15


def test_passar_de_prova_paga_moedas(jogo_limpo):
    from jogo.fase import semestre
    jogo = jogo_limpo()
    jogo.fases = semestre()
    jogo.fase = jogo.fases[0]
    jogo.concluir_fase()
    assert jogo.placar.moedas == jogo.MOEDAS_POR_PROVA


def test_bolsa_pelo_tempo_no_fim_e_treino_nao_paga(jogo_limpo):
    jogo = jogo_limpo()
    jogo.placar.tempo = 120
    jogo.placar.adicionar_moedas(5)
    assert jogo.moedas_ganhas() == 5 + 2 * jogo.MOEDAS_POR_MINUTO
    jogo.treino = True
    assert jogo.moedas_ganhas() == 0
