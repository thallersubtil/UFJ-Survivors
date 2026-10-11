import json

import pytest

from jogo.placar import Placar
from jogo.ranking import Ranking, RegistroRanking


def test_pontos_validos():
    p = Placar()
    p.adicionar_pontos(10)
    assert p.pontos == 10
    with pytest.raises(ValueError):
        p.pontos = -1
    with pytest.raises(TypeError):
        p.pontos = 2.5
    with pytest.raises(ValueError):
        p.adicionar_pontos(-5)


def test_combo_67_dispara_a_cada_67_eliminacoes_seguidas():
    p = Placar()
    disparos = [p.registrar_eliminacao(1) for _ in range(134)]
    assert disparos.count(True) == 2
    assert disparos[66] is True and disparos[133] is True
    assert p.combos_67 == 2
    assert p.eliminacoes == 134


def test_levar_dano_zera_o_combo():
    p = Placar()
    for _ in range(60):
        p.registrar_eliminacao(1)
    p.zerar_combo()
    assert p.combo == 0
    assert not any(p.registrar_eliminacao(1) for _ in range(66))


def test_tempo_formatado_e_str():
    p = Placar()
    p.tempo = 125.7
    assert p.tempo_formatado == "02:05"
    assert "02:05" in str(p)


def test_pontuacao_final_premia_tempo_e_vitoria():
    p = Placar()
    p.adicionar_pontos(100)
    p.tempo = 60
    assert p.pontuacao_final(False) == 100 + 120
    assert p.pontuacao_final(True) == 100 + 120 + 5000


def test_registro_compara_por_pontos_e_desempata_pelo_tempo():
    a = RegistroRanking("Ana", "Aluno 1", 500, 300)
    b = RegistroRanking("Bia", "Aluno 2", 800, 300)
    c = RegistroRanking("Caio", "Aluno 1", 800, 200)
    assert a < b
    assert b < c
    assert sorted([c, a, b], reverse=True) == [c, b, a]


def test_registro_igualdade_e_texto():
    a = RegistroRanking("Ana", "Aluno 1", 500, 65)
    assert a == RegistroRanking("Ana", "Aluno 1", 500, 65)
    assert a != RegistroRanking("Ana", "Aluno 1", 501, 65)
    assert str(a) == "Ana (Aluno 1) - 500 pontos em 01:05"


def test_registro_nome_vazio_e_longo():
    assert RegistroRanking("   ", "Aluno 1", 1, 1).nome == "Anônimo"
    assert RegistroRanking("NomeMuitoGrandeDemais", "Aluno 1", 1, 1).nome == "NomeMuitoGra"


def test_ranking_guarda_os_10_melhores_e_persiste(tmp_path):
    arquivo = tmp_path / "ranking.json"
    r = Ranking(arquivo)
    for i in range(12):
        r.adicionar(RegistroRanking(f"J{i}", "Aluno 1", i * 10, 100))
    assert len(r.registros) == 10
    assert r.registros[0].pontos == 110
    assert r.adicionar(RegistroRanking("Ruim", "Aluno 1", 0, 100)) is None
    assert r.adicionar(RegistroRanking("Top", "Aluno 2", 999, 50)) == 1
    recarregado = Ranking(arquivo)
    assert [x.nome for x in recarregado.registros] == [x.nome for x in r.registros]


@pytest.mark.parametrize("conteudo", ["", "{quebrado", '{"a": 1}', '[{"nome": "x"}]'])
def test_ranking_corrompido_comeca_vazio(tmp_path, conteudo):
    arquivo = tmp_path / "ranking.json"
    arquivo.write_text(conteudo, encoding="utf-8")
    assert Ranking(arquivo).registros == []


def test_ranking_cria_pasta_ao_salvar(tmp_path):
    arquivo = tmp_path / "nova" / "ranking.json"
    r = Ranking(arquivo)
    r.adicionar(RegistroRanking("Ana", "Aluno 1", 10, 10))
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    assert dados[0]["nome"] == "Ana"
