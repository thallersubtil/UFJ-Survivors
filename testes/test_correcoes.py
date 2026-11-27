"""Correções apontadas na revisão de código (docs/PENDENCIAS.md). Cada teste falhava antes da correção."""
import random

import pygame

from jogo.cenas.nivel import CenaNivel
from jogo.cenas.partida import CenaPartida
from jogo.coletaveis.coletaveis import Nota
from jogo.config import COMBO_ESPECIAL, LIMITE_COLETAVEIS
from jogo.inimigos.bug import Bug
from jogo.jogador.classes import Programador
from jogo.projeteis.projeteis import ProjetilDoHeroi as Projetil


class InimigoFalso:
    """Inimigo mínimo para testar a memória de acertos sem depender do mapa."""
    def __init__(self, posicao):
        self.posicao = pygame.Vector2(posicao)


class JogoFalso:
    def __init__(self, inimigos):
        self.inimigos = inimigos
        self.danos = []

    def inimigos_proximos(self, posicao, raio):
        return list(self.inimigos)

    def causar_dano(self, inimigo, dano, direcao):
        self.danos.append(inimigo)


def test_projetil_guarda_o_proprio_inimigo_e_nao_o_id():
    a = InimigoFalso((0, 0))
    jogo = JogoFalso([a])
    projetil = Projetil((0, 0), (1, 0), 5, perfuracao=5)
    projetil.verificar_colisao(jogo)
    assert a in projetil.atingidos
    assert id(a) not in projetil.atingidos


def test_inimigo_novo_com_id_reaproveitado_ainda_e_acertado():
    a = InimigoFalso((0, 0))
    projetil = Projetil((0, 0), (1, 0), 5, perfuracao=5)
    projetil.verificar_colisao(JogoFalso([a]))
    b = InimigoFalso((0, 0))
    projetil.atingidos.add(id(b))      # simula o lixo de um id antigo igual ao do novo inimigo
    jogo = JogoFalso([b])
    projetil.verificar_colisao(jogo)
    assert jogo.danos == [b]


def test_limite_de_notas_ignora_entidades_que_nao_sao_coletaveis(jogo_limpo):
    jogo = jogo_limpo()
    longe = jogo.jogador.posicao + (1000, 0)
    for _ in range(LIMITE_COLETAVEIS - 1):
        jogo.soltar_nota(longe, 1)
        jogo._incorporar_novas()
    for _ in range(5):                 # efeitos ou projéteis esperando na fila no mesmo quadro
        jogo._novas.append(Projetil(longe, (1, 0), 1))
    jogo.soltar_nota(longe, 1)
    novas_notas = [e for e in jogo._novas if isinstance(e, Nota)]
    assert len(novas_notas) == 1


def test_nivel_nao_abre_sobre_partida_que_acabou_no_mesmo_quadro(tmp_path):
    from jogo.aplicacao import Aplicacao
    from jogo.loja.progresso import Progresso
    from jogo.ranking import Ranking
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.ranking = Ranking(tmp_path / "r.json")
    app.progresso = Progresso(tmp_path / "p.json")
    partida = CenaPartida(app, Programador)
    app.trocar(partida)
    partida.jogo.niveis_pendentes = 1
    partida.jogo.jogador.vida = 0      # morre no mesmo quadro em que subiria de nível
    app.passo(1 / 60, [])
    assert not isinstance(app.cena_atual, CenaNivel)


def test_barra_do_chefe_fica_no_topo(jogo_limpo, monkeypatch):
    from jogo.cenas import hud as modulo
    jogo = jogo_limpo()
    class ChefeFalso:
        ativo = True
        vida, vida_maxima = 50, 100
        rotulo_da_barra = "Chefe"
    jogo.chefes = [ChefeFalso(), ChefeFalso()]
    barras = []
    monkeypatch.setattr(modulo, "barra", lambda ui, ret, *a, **k: barras.append(pygame.Rect(ret)))
    ui = pygame.Surface((640, 360), pygame.SRCALPHA)       # o HUD desenha na camada de 640x360
    modulo.Hud()._chefe(ui, jogo)
    assert len(barras) == 2 and barras[0].top < barras[1].top < 360 // 4      # uma barra por chefe em campo


def test_hud_usa_combo_especial_da_config(jogo_limpo, monkeypatch):
    from jogo.cenas import hud as modulo
    monkeypatch.setattr(modulo, "COMBO_ESPECIAL", 10, raising=False)
    jogo = jogo_limpo()
    jogo.placar.combo = 13
    textos = []
    monkeypatch.setattr(modulo, "texto", lambda ui, t, *a, **k: textos.append(t) or pygame.Rect(0, 0, 1, 1))
    modulo.Hud()._tempo_e_placar(pygame.Surface((640, 360), pygame.SRCALPHA), jogo)
    assert "COMBO 3/10" in textos


def test_bando_de_bugs_tem_de_5_a_8():
    rng = random.Random(1)
    tamanhos = {Bug.sortear_tamanho_do_grupo(rng) for _ in range(300)}
    assert tamanhos == {5, 6, 7, 8}


def test_arma_que_nao_dispara_tem_nome_claro():
    from jogo.armas import arma
    from jogo.armas.caramelo import Caramelo
    assert issubclass(Caramelo, arma.ArmaContinua)
    assert not hasattr(arma, "ArmaSemMunicao")              # o nome antigo falava de uma munição que não existe mais
    assert not hasattr(arma, "ArmaDeContato")
