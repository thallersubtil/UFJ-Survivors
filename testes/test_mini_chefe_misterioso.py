"""Mini-chefe misterioso: até ser invocado pela primeira vez, o círculo, o mini-mapa e a seta mostram só "?"."""
import pygame

from jogo.invocacao import LocalDeInvocacao
from jogo.jogador.classes import Programador
from jogo.jogo import Jogo
from jogo.loja.progresso import Progresso
from jogo.opcoes import OpcoesDePartida


def circulo(jogo, nome="tia_da_cantina"):
    local = LocalDeInvocacao(jogo.jogador.posicao + (2000, 900), nome)
    jogo.adicionar(local)
    jogo.atualizar(1 / 60)
    return local


def test_circulo_de_quem_nunca_foi_invocado_esconde_nome_e_rosto(jogo_limpo):
    jogo = jogo_limpo()
    local = circulo(jogo)
    assert not local.revelado
    assert local.NOME == LocalDeInvocacao.NOME_MISTERIOSO == "Mini-boss misterioso"
    assert local.rosto == LocalDeInvocacao.ROSTO_MISTERIOSO and "tia" not in local.rosto
    assert local.CHAVE == "tia_da_cantina"            # por dentro ele sabe quem é: a marcação usa isto
    tela = pygame.Surface((1280, 720))
    jogo.camera.seguir(local.posicao)
    local.desenhar(tela, jogo.camera)


def test_invocar_revela_para_sempre_nesta_partida_e_nas_proximas(jogo_limpo, tmp_path):
    jogo = jogo_limpo()
    local = circulo(jogo)
    chefe = local.invocar(jogo)
    assert "tia_da_cantina" in jogo.mini_chefes_conhecidos
    assert chefe.NOME == "Tia da Cantina"              # o invocado sempre mostra quem é (e a apresentação também)
    outro = circulo(jogo)
    assert outro.revelado and outro.NOME == "Tia da Cantina" and "tia" in outro.rosto
    progresso = Progresso(tmp_path / "progresso.json")
    progresso.conhecer_mini_chefe("tia_da_cantina")
    assert Progresso(tmp_path / "progresso.json").mini_chefes_conhecidos == {"tia_da_cantina"}
    proxima = Jogo.a_partir_de(Programador, OpcoesDePartida().com_progresso(progresso), semente=2)
    assert proxima.mini_chefes_conhecidos == {"tia_da_cantina"}


def test_cada_misterioso_e_marcado_sozinho_no_mapa(jogo_limpo):
    jogo = jogo_limpo()
    tia, vigia = circulo(jogo, "tia_da_cantina"), circulo(jogo, "vigilante")
    assert tia.NOME == vigia.NOME
    jogo.marcar_no_mapa(tia.CHAVE)
    assert jogo.marcados == {"tia_da_cantina"}


def test_partida_guarda_no_progresso_quem_foi_invocado(tmp_path):
    from jogo.aplicacao import Aplicacao
    from jogo.cenas.partida import CenaPartida
    from jogo.ranking import Ranking
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.ranking = Ranking(tmp_path / "ranking.json")
    app.progresso = Progresso(tmp_path / "progresso.json")
    partida = CenaPartida(app, Programador)
    app.trocar(partida)
    local = circulo(partida.jogo, "vigilante")
    local.invocar(partida.jogo)
    app.passo(1 / 60, [])
    assert Progresso(tmp_path / "progresso.json").mini_chefes_conhecidos == {"vigilante"}
