from types import SimpleNamespace

import pygame
import pytest

from jogo.inimigos.bug import Bug
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


def test_inimigo_e_abstrato():
    with pytest.raises(TypeError):
        Inimigo((0, 0))


def test_fabrica_cria_bug_pelo_nome():
    bug = FabricaDeInimigos.criar("bug", (10, 20))
    assert isinstance(bug, Bug)
    assert bug.posicao == pygame.Vector2(10, 20)
    assert Bug.CHAVE == "bug"
    assert "bug" in FabricaDeInimigos.nomes()


def test_fabrica_recusa_nome_desconhecido():
    with pytest.raises(ValueError):
        FabricaDeInimigos.criar("dragao", (0, 0))


def test_registrar_inimigo_novo_sem_mexer_nas_classes(monkeypatch):
    monkeypatch.setattr(FabricaDeInimigos, "_registro", dict(FabricaDeInimigos._registro))

    @FabricaDeInimigos.registrar("bug_de_teste")
    class BugDeTeste(Bug):
        VIDA = 1

    assert isinstance(FabricaDeInimigos.criar("bug_de_teste", (0, 0)), BugDeTeste)
    with pytest.raises(ValueError):
        FabricaDeInimigos.registrar("bug_de_teste")(BugDeTeste)


def test_escala_aumenta_vida_e_um_pouco_a_velocidade():
    normal = Bug((0, 0))
    forte = Bug((0, 0), escala=3.0)
    assert forte.vida == pytest.approx(normal.vida * 3)
    assert forte.velocidade > normal.velocidade


def test_gigante_e_maior_mais_forte_e_solta_bau():
    g = FabricaDeInimigos.criar_gigante("bug", (0, 0))
    assert g.gigante and g.solta_bau and not g.reposiciona
    assert g.raio == Bug.RAIO * 3
    assert g.vida == Bug.VIDA * 30
    assert g.valor_em_pontos == Bug.PONTOS * 20


def test_bug_anda_em_direcao_ao_heroi():
    bug = Bug((0, 0))
    jogo = SimpleNamespace(jogador=SimpleNamespace(posicao=pygame.Vector2(100, 0)))
    bug.mover(0.1, jogo)
    assert bug.posicao.x == pytest.approx(Bug.VELOCIDADE * 0.1)
    assert bug.posicao.y == pytest.approx(0)
    assert not bug.olhando_esquerda
