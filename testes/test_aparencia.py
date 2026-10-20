import random

import pygame
import pytest

from jogo.aplicacao import Aplicacao
from jogo.cenas.partida import CenaPartida
from jogo.cenas.personalizacao import CenaPersonalizacao
from jogo.cenas.selecao import CenaSelecao
from jogo.jogador import partes
from jogo.jogador.aparencia import OPCOES, Aparencia
from jogo.jogador.boneco import Boneco, Pose
from jogo.jogador.bonus import BonusTemporario
from jogo.jogador.classes import CLASSES, Otaku, Programador
from jogo.ranking import Ranking


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


@pytest.fixture
def app(tmp_path):
    a = Aplicacao(pygame.Surface((1280, 720)))
    a.ranking = Ranking(tmp_path / "ranking.json")
    return a


def test_aparencia_valida_as_escolhas():
    aparencia = Aparencia()
    aparencia.cabelo = "Ruivo"
    aparencia.penteado = "Black power"
    assert aparencia.cabelo == "Ruivo" and aparencia.penteado == "Black power"
    with pytest.raises(ValueError):
        aparencia.pele = "Verde-limão"
    with pytest.raises(ValueError):
        aparencia.penteado = "Moicano de fogo"
    with pytest.raises(ValueError):
        Aparencia(asas="Sim")
    assert aparencia.pele == "Clara"


def test_masculino_e_feminino_tem_padroes_proprios():
    assert Aparencia().genero == "Masculino"
    feminina = Aparencia(genero="Feminino")
    assert feminina.penteado == "Longo" and feminina.baixo == "Saia"


def test_trocar_da_a_volta_na_lista():
    aparencia = Aparencia()
    primeira = OPCOES["cor_baixo"][0]
    aparencia.cor_baixo = primeira
    aparencia.trocar("cor_baixo", -1)
    assert aparencia.cor_baixo == OPCOES["cor_baixo"][-1]
    aparencia.trocar("cor_baixo", 1)
    assert aparencia.cor_baixo == primeira


def test_aparencias_iguais_sao_iguais_e_tem_o_mesmo_hash():
    a = Aparencia(genero="Feminino", cabelo="Preto", acessorio="Laço")
    b = Aparencia(genero="Feminino", cabelo="Preto", acessorio="Laço")
    assert a == b and hash(a) == hash(b)
    assert a != Aparencia()
    assert a.copia() == a and a.copia() is not a


def test_cor_so_existe_para_partes_de_cor():
    aparencia = Aparencia(cor_cima="Vermelho")
    assert aparencia.cor("cor_cima") == (210, 40, 50)
    assert aparencia.cor("penteado") is None


def test_opcoes_de_formato_vem_das_classes_de_partes():
    assert set(OPCOES["penteado"]) == set(partes.PENTEADOS)
    assert set(OPCOES["genero"]) == {"Masculino", "Feminino"}
    for catalogo in (partes.PENTEADOS, partes.OLHOS, partes.ROUPAS_DE_CIMA, partes.ROUPAS_DE_BAIXO,
                     partes.ACESSORIOS, partes.CORPOS):
        for nome, classe in catalogo.items():
            assert issubclass(classe, partes.Parte) and classe.NOME == nome


def test_partes_abstratas_nao_podem_ser_criadas():
    for classe in (partes.Corpo, partes.Penteado, partes.Olhos, partes.Acessorio):
        with pytest.raises(TypeError):
            classe()


def test_boneco_contem_as_partes_escolhidas():
    boneco = Boneco(Aparencia(genero="Feminino", penteado="Coque", cima="Jaqueta", baixo="Bermuda",
                              acessorio="Óculos", olhos="Anime"))
    assert isinstance(boneco.corpo, partes.CorpoFeminino)
    assert isinstance(boneco.penteado, partes.PenteadoCoque)
    assert isinstance(boneco.cima, partes.Jaqueta)
    assert isinstance(boneco.baixo, partes.Bermuda)
    assert isinstance(boneco.acessorio, partes.Oculos)
    assert isinstance(boneco.olhos, partes.OlhosAnime)
    assert isinstance(Boneco(Aparencia(), transformado=True).penteado, partes.PenteadoSuperSaiyajin)


def test_bracos_e_pernas_giram_separados_do_tronco():
    boneco = Boneco(Aparencia())
    parado = boneco.esqueleto(Pose())
    passo = boneco.esqueleto(Pose(perna=30, braco=-28))
    assert passo["pe_frente"][0] > parado["pe_frente"][0] > passo["pe_tras"][0]
    assert passo["mao_frente"][0] < parado["mao_frente"][0]
    assert passo["pe_frente"][1] == pytest.approx(-Boneco.PE, abs=0.01)   # o pé continua no chão
    assert parado["ombro_y"] < parado["quadril_y"] < 0


def test_todas_as_combinacoes_de_partes_desenham():
    rng = random.Random(4)
    for _ in range(25):
        aparencia = Aparencia()
        aparencia.sortear(rng)
        animacoes = Boneco(aparencia).animacoes()
        assert len(animacoes["andar"].quadros) == Boneco.QUADROS_ANDAR
        quadro = animacoes["parado"].quadros[0]
        assert quadro.get_size() == (Boneco.LARGURA, Boneco.ALTURA)
        assert quadro.get_bounding_rect().height > 60


def test_animacoes_ficam_em_cache_por_aparencia():
    a = Boneco.animacoes_de(Aparencia(cabelo="Azul"))
    assert Boneco.animacoes_de(Aparencia(cabelo="Azul")) is a
    assert Boneco.animacoes_de(Aparencia(cabelo="Rosa")) is not a


def test_vestir_troca_os_quadros_do_aluno():
    a = Programador((0, 0))
    antes = a.animador.quadro_atual
    a.vestir(Aparencia(genero="Feminino", cabelo="Rosa"))
    assert a.aparencia.genero == "Feminino"
    assert a.animador.quadro_atual is not antes


def test_cada_classe_tem_uma_aparencia_sugerida():
    vistas = {Aparencia(**classe.APARENCIA) for classe in CLASSES}
    assert len(vistas) == len(CLASSES)


def test_super_saiyajin_troca_o_cabelo_do_boneco():
    j = Otaku((0, 0))
    normal = j.animador.animacoes["andar"]
    j.adicionar_bonus(BonusTemporario("ssj", "dano", 2.0, 5))
    j._atualizar_animacao(0.1)
    assert j.transformado and j.animador.animacoes["andar"] is not normal
    j.bonus = []
    j._atualizar_animacao(0.1)
    assert j.animador.animacoes["andar"] is normal


def test_selecao_leva_a_personalizacao_e_dela_a_partida(app):
    app.trocar(CenaSelecao(app))
    app.passo(1 / 60, [tecla(pygame.K_RIGHT), tecla(pygame.K_RETURN)])
    cena = app.cena_atual
    assert isinstance(cena, CenaPersonalizacao) and cena.classe_jogador is Programador
    cabelo = cena.aparencia.penteado
    app.passo(1 / 60, [tecla(pygame.K_DOWN), tecla(pygame.K_RIGHT)])
    assert cena.aparencia.penteado != cabelo
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    partida = app.cena_atual
    assert isinstance(partida, CenaPartida)
    assert partida.jogo.jogador.aparencia == cena.aparencia
    assert app.aparencia == cena.aparencia      # lembra a última escolha


def test_trocar_o_genero_leva_os_padroes_junto(app):
    cena = CenaPersonalizacao(app, Programador)
    assert cena.aparencia.genero == "Masculino" and cena.aparencia.penteado == "Curto"
    cena.aparencia.cor_cima = "Rosa"
    cena._mudar(1)                                # primeira linha: gênero
    assert cena.aparencia.genero == "Feminino"
    assert cena.aparencia.penteado == "Longo" and cena.aparencia.baixo == "Saia"
    assert cena.aparencia.cor_cima == "Rosa"      # o que foi escolhido fica


def test_personalizacao_aleatoria_e_voltar(app):
    cena = CenaPersonalizacao(app, Programador)
    app.trocar(cena)
    app.passo(1 / 60, [])
    app.passo(1 / 60, [tecla(pygame.K_r), tecla(pygame.K_TAB)])
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert isinstance(app.cena_atual, CenaSelecao)
