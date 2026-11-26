"""Etapa 3: a hierarquia está completa e o laço do Jogo continua polimórfico."""
import inspect
import sys
from pathlib import Path

import pygame
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
import demonstrar_polimorfismo as demonstracao  # noqa: E402

from jogo.inimigos.fabrica import FabricaDeInimigos  # noqa: E402
from jogo.jogo import Jogo  # noqa: E402


@pytest.fixture(scope="module")
def classes():
    return demonstracao.carregar_classes()


def test_entidade_e_abstrata_e_toda_concreta_implementa_os_dois_metodos(classes):
    entidade = classes["Entidade"]
    assert {"atualizar", "desenhar"} <= set(entidade.__abstractmethods__)
    with pytest.raises(TypeError):
        entidade((0, 0), 1)
    concretas = demonstracao.concretas(entidade)
    assert len(concretas) > 50
    for classe in concretas:
        assert not classe.__abstractmethods__, classe.__name__


def test_todo_inimigo_da_fabrica_herda_de_inimigo_e_tem_o_proprio_mover(classes):
    inimigo = classes["Inimigo"]
    nomes = FabricaDeInimigos.nomes()
    assert len(nomes) >= 3
    for nome in nomes:
        classe = FabricaDeInimigos.classe(nome)
        assert issubclass(classe, inimigo), nome
        dona = next(c for c in classe.__mro__ if "mover" in vars(c))
        assert dona is not inimigo, nome


def test_laco_do_jogo_nao_pergunta_o_tipo():
    fonte = inspect.getsource(Jogo.atualizar) + inspect.getsource(Jogo.desenhar)
    assert "for e in self.entidades" in fonte
    for proibido in ("isinstance", "type(", "__class__"):
        assert proibido not in fonte


def test_um_inimigo_de_cada_tipo_anda_so_com_jogo_atualizar(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    inimigos = []
    for i, nome in enumerate(FabricaDeInimigos.nomes()):
        direcao = pygame.Vector2(420, 0).rotate(10 * i)
        inimigo = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + direcao)
        jogo.adicionar(inimigo)
        inimigos.append((nome, inimigo, inimigo.posicao.copy()))
    for _ in range(120):
        jogo.atualizar(1 / 60)
    for nome, inimigo, origem in inimigos:
        assert inimigo.posicao.distance_to(origem) > 20, nome
