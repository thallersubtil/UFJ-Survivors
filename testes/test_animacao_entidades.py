from types import SimpleNamespace

import pygame
import pytest

from jogo.inimigos.bug import Bug
from jogo.inimigos.mouse_de_bolinha import MouseDeBolinha
from jogo.jogador.alunos import AlunoAgil, AlunoResistente
from jogo.jogador.bonus import BonusTemporario
from jogo.nucleo.recursos import Recursos


def gravar_tira(pasta, nome, n, largura, altura, cor):
    pasta.mkdir(parents=True, exist_ok=True)
    tira = pygame.Surface((largura * n, altura), pygame.SRCALPHA)
    tira.fill((*cor, 255))
    pygame.image.save(tira, str(pasta / f"{nome}-{n}.png"))


@pytest.fixture
def arte_falsa(tmp_path, monkeypatch):
    s = tmp_path / "sprites"
    gravar_tira(s / "heroi", "parado", 4, 10, 20, (200, 0, 0))
    gravar_tira(s / "heroi", "andar", 6, 12, 20, (0, 200, 0))
    gravar_tira(s / "heroi_ssj", "parado", 4, 10, 22, (250, 220, 0))
    gravar_tira(s / "heroi_ssj", "andar", 6, 12, 22, (250, 220, 0))
    gravar_tira(s / "inseto", "andar", 4, 8, 6, (0, 0, 200))
    gravar_tira(s / "inseto_gigante", "andar", 4, 24, 18, (0, 0, 120))
    gravar_tira(s / "rato", "andar", 4, 9, 5, (90, 90, 90))
    gravar_tira(s / "rato", "parado", 2, 9, 5, (60, 60, 60))
    monkeypatch.setattr(Recursos, "pasta", tmp_path)
    monkeypatch.setattr(AlunoAgil, "PASTA_SPRITE", "heroi")
    monkeypatch.setattr(AlunoResistente, "PASTA_SPRITE", "heroi")
    monkeypatch.setattr(AlunoResistente, "PASTA_TRANSFORMADO", "heroi_ssj")
    monkeypatch.setattr(Bug, "PASTA_SPRITE", "inseto")
    monkeypatch.setattr(MouseDeBolinha, "PASTA_SPRITE", "rato")
    Recursos.limpar()
    yield
    Recursos.limpar()


def jogo_falso(direcao=(0, 0)):
    return SimpleNamespace(entrada=SimpleNamespace(direcao=pygame.Vector2(direcao), mira=None),
                           arena=pygame.Rect(0, 0, 3000, 3000), adicionar=lambda e: None,
                           resolver_obstaculos=lambda posicao, raio: posicao,
                           jogador=SimpleNamespace(posicao=pygame.Vector2(500, 500)))


def test_heroi_parado_e_andando(arte_falsa):
    j = AlunoAgil((100, 100))
    j.atualizar(0.1, jogo_falso())
    assert j.animador.atual == "parado"
    assert j.animador.quadro_atual.get_height() == 40
    j.atualizar(0.1, jogo_falso((1, 0)))
    assert j.animador.atual == "andar"


def test_super_saiyajin_troca_o_conjunto_de_animacoes(arte_falsa):
    j = AlunoResistente((100, 100))
    j.atualizar(0.1, jogo_falso())
    assert j.animador.quadro_atual.get_height() == 40
    j.adicionar_bonus(BonusTemporario("ssj", "dano", 2.0, 5))
    j.atualizar(0.1, jogo_falso())
    assert j.animador.quadro_atual.get_height() == 44
    j.atualizar(6, jogo_falso())
    assert j.animador.quadro_atual.get_height() == 40


def test_inimigo_anda_animado(arte_falsa):
    b = Bug((0, 0))
    assert b.animador.atual == "andar"
    primeiro = b.animador.quadro_atual
    b.animador.atualizar(0.1)
    assert b.animador.quadro_atual is not primeiro


def test_gigante_usa_sprite_proprio_em_resolucao_maior(arte_falsa):
    g = Bug((0, 0))
    g.tornar_gigante()
    assert g.animador.quadro_atual.get_size() == (48, 36)


def test_gigante_sem_sprite_proprio_amplia_sem_suavizar(arte_falsa):
    g = MouseDeBolinha((0, 0))
    g.tornar_gigante()
    assert g.animador.quadro_atual.get_height() == 5 * 2 * 3


def test_mouse_parado_e_correndo(arte_falsa):
    m = MouseDeBolinha((0, 0))
    m.correndo = False
    assert m.escolher_animacao() == "parado"
    m.correndo = True
    assert m.escolher_animacao() == "andar"


def test_sem_arte_animada_usa_imagem_estatica(monkeypatch):
    monkeypatch.setattr(Bug, "PASTA_SPRITE", "pasta_que_nao_existe")
    Recursos.limpar()
    b = Bug((0, 0))
    assert b.animador.quadro_atual.get_height() == Bug.ALTURA


def test_ajudantes_projeteis_e_coletaveis_animam(tmp_path, monkeypatch):
    from jogo.ajudantes.ajudantes import CachorroCaramelo, MascoteFlutuante
    from jogo.coletaveis.coletaveis import Nota
    from jogo.projeteis.projeteis import CobraProjetil
    s = tmp_path / "sprites"
    for pasta in ("cao", "cobrinha", "moeda", "robo"):
        gravar_tira(s / pasta, "mover", 4, 6, 6, (10, 200, 10))
    monkeypatch.setattr(Recursos, "pasta", tmp_path)
    monkeypatch.setattr(CachorroCaramelo, "PASTA_SPRITE", "cao")
    monkeypatch.setattr(CobraProjetil, "PASTA_SPRITE", "cobrinha")
    monkeypatch.setattr(Nota, "PASTA_SPRITE", "moeda")
    Recursos.limpar()
    dono = SimpleNamespace(posicao=pygame.Vector2(0, 0), multiplicador_dano=1.0)
    arma = SimpleNamespace(valor=lambda nome: {"velocidade": 3, "raio": 50, "dano": 5}[nome])
    jogo = SimpleNamespace(inimigos_proximos=lambda p, r: [], jogador=SimpleNamespace(
        posicao=pygame.Vector2(900, 900), alcance_coleta=10, raio=10), arena=pygame.Rect(0, 0, 2000, 2000))
    for entidade in (CachorroCaramelo(dono, 0, arma), CobraProjetil((5, 5), (100, 0), 1), Nota((0, 0)),
                     MascoteFlutuante(dono, "sprites/x.png", 20, (0, 0), pasta="robo")):
        primeiro = entidade.animador.quadro_atual
        entidade.atualizar(0.11, jogo)
        assert entidade.animador.quadro_atual is not primeiro, type(entidade).__name__
    Recursos.limpar()
