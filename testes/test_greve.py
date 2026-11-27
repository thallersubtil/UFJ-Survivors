"""Evento Greve."""

from jogo.coletaveis.coletaveis import Nota
from jogo.fase import Semestre


def test_o_semestre_tem_uma_greve_longe_dos_chefes():
    fase = Semestre()
    greves = [e for e in fase.eventos if e.descricao == "Greve"]
    assert len(greves) == 1 and greves[0].tempo == Semestre.GREVE
    for prova in fase.provas:
        assert not prova.hora - 30 <= Semestre.GREVE <= prova.hora + 30
    assert not any("Monitor" in e.descricao for e in fase.eventos)


def test_greve_para_os_inimigos_e_chove_nota(jogo_limpo):
    jogo = jogo_limpo()
    fase = Semestre()
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
    fase = Semestre()
    fase.iniciar_greve(jogo)
    for _ in range(round(60 * (fase.DURACAO_GREVE + 1))):
        fase._atualizar_greve(1 / 60, jogo)
    assert fase.greve <= 0


