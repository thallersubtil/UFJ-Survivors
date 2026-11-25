"""Evento Greve e o mini-chefe Monitor Possuído."""
import pygame

from jogo.coletaveis.coletaveis import Bau, Nota
from jogo.fase import PROVAS, ProvaDeArquiteturaEED, ProvaDeCalculo
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.monitor_possuido import MonitorPossuido
from jogo.jogador.classes import Programador
from jogo.jogo import Jogo
from jogo.projeteis.projeteis import ProjetilInimigo


def test_toda_prova_tem_greve_e_as_seguintes_tem_monitor():
    for classe in PROVAS:
        assert classe.GREVE is not None
        assert any("Greve" in e.descricao for e in classe().eventos)
    assert not any("Monitor" in e.descricao for e in ProvaDeCalculo().eventos)
    assert any("Monitor" in e.descricao for e in ProvaDeArquiteturaEED().eventos)


def test_greve_para_os_inimigos_e_chove_nota(jogo_limpo):
    jogo = jogo_limpo()
    fase = ProvaDeCalculo()
    fase.iniciar_greve(jogo)
    assert any("GREVE" in t for t, _ in jogo.anuncios)
    inimigos_antes = len(jogo.inimigos)
    for _ in range(60 * 5):
        fase.atualizar(1 / 60, jogo)
    jogo._incorporar_novas()
    assert len(jogo.inimigos) == inimigos_antes
    assert sum(isinstance(e, Nota) for e in jogo.entidades) >= 8


def test_greve_acaba_sozinha(jogo_limpo):
    jogo = jogo_limpo()
    fase = ProvaDeCalculo()
    fase.iniciar_greve(jogo)
    for _ in range(round(60 * (fase.DURACAO_GREVE + 1))):
        fase._atualizar_greve(1 / 60, jogo)
    assert fase.greve <= 0


def test_monitor_possuido_atira_listas_e_solta_bau(jogo_limpo):
    jogo = jogo_limpo()
    monitor = FabricaDeInimigos.criar("monitor_possuido", jogo.jogador.posicao + (300, 0), 1.0)
    assert isinstance(monitor, MonitorPossuido) and monitor.solta_bau
    jogo.adicionar(monitor)
    jogo._incorporar_novas()
    for _ in range(60 * 4):
        monitor.atualizar(1 / 60, jogo)
    jogo._incorporar_novas()
    assert any(isinstance(e, ProjetilInimigo) for e in jogo.entidades)
    monitor.ao_morrer(jogo)
    jogo._incorporar_novas()
    assert any(isinstance(e, Bau) for e in jogo.entidades)
