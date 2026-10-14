import pygame
import pytest

from jogo.nucleo.animacao import Animacao, Animador
from jogo.nucleo.recursos import Recursos


def quadros(n, largura=4, altura=6):
    lista = []
    for i in range(n):
        q = pygame.Surface((largura, altura), pygame.SRCALPHA)
        q.fill((i * 40, 0, 0, 255))
        lista.append(q)
    return lista


def test_animacao_exige_quadros():
    with pytest.raises(ValueError):
        Animacao([])


def test_animacao_repetida_volta_ao_inicio():
    q = quadros(4)
    a = Animacao(q, fps=10)
    assert a.quadro(0.0) is q[0]
    assert a.quadro(0.25) is q[2]
    assert a.quadro(0.45) is q[0]
    assert a.duracao == pytest.approx(0.4)


def test_animacao_sem_repetir_para_no_ultimo_quadro():
    q = quadros(3)
    a = Animacao(q, fps=10, repetir=False)
    assert a.quadro(5.0) is q[2]
    assert not a.terminou(0.1)
    assert a.terminou(0.3)


def test_animador_troca_e_reinicia_so_quando_muda():
    parado, andar = quadros(2), quadros(6)
    anim = Animador({"parado": Animacao(parado, 4), "andar": Animacao(andar, 10)})
    assert anim.atual == "parado"
    anim.tocar("andar")
    anim.atualizar(0.25)
    assert anim.quadro_atual is andar[2]
    anim.tocar("andar")
    assert anim.quadro_atual is andar[2]
    anim.tocar("parado")
    assert anim.quadro_atual is parado[0]


def test_animador_ignora_animacao_que_nao_existe():
    anim = Animador({"parado": Animacao(quadros(2), 4)})
    anim.tocar("voar")
    assert anim.atual == "parado"


def test_animador_troca_de_conjunto_mantendo_o_ritmo():
    normal = {"andar": Animacao(quadros(6), 10)}
    dourado = {"andar": Animacao(quadros(6, largura=8), 10)}
    anim = Animador(normal)
    anim.atualizar(0.3)
    anim.trocar_conjunto(dourado)
    assert anim.quadro_atual is dourado["andar"].quadros[3]


def test_recursos_le_tiras_pelo_nome_e_amplia_sem_suavizar(tmp_path, monkeypatch):
    pasta = tmp_path / "sprites" / "teste"
    pasta.mkdir(parents=True)
    tira = pygame.Surface((12, 5), pygame.SRCALPHA)
    tira.fill((255, 0, 0, 255), pygame.Rect(0, 0, 4, 5))
    tira.fill((0, 255, 0, 255), pygame.Rect(4, 0, 4, 5))
    tira.fill((0, 0, 255, 255), pygame.Rect(8, 0, 4, 5))
    pygame.image.save(tira, str(pasta / "andar-3.png"))
    monkeypatch.setattr(Recursos, "pasta", tmp_path)
    Recursos.limpar()
    animacoes = Recursos.animacoes("teste", escala=2)
    assert set(animacoes) == {"andar"}
    q = animacoes["andar"].quadros
    assert len(q) == 3 and q[0].get_size() == (8, 10)
    assert q[1].get_at((7, 9))[:3] == (0, 255, 0)
    Recursos.limpar()


def test_recursos_pasta_ausente_cai_na_imagem_estatica():
    Recursos.limpar()
    animacoes = Recursos.animacoes_ou_imagem("nao_existe", "sprites/nao_existe.png", 30)
    assert set(animacoes) == {"parado"}
    assert animacoes["parado"].quadros[0].get_height() == 30
