"""Boletim do fim de jogo: uma nota por prova, a partir do que aconteceu na partida."""
from jogo.boletim import Boletim


def test_prova_aprovada_tira_nota_pela_vida_que_sobrou(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.vida = jogo.jogador.vida_maxima / 2
    assert Boletim.nota_de_aprovacao(jogo.jogador) == 8.0
    jogo.jogador.vida = jogo.jogador.vida_maxima
    assert Boletim.nota_de_aprovacao(jogo.jogador) == 10.0


def _semestre(jogo, tempo):
    """A partida com o calendário inteiro, parada em `tempo` segundos."""
    from jogo.fase import Semestre
    jogo.fase = Semestre()
    jogo.fase.tempo = tempo
    return jogo


def test_boletim_tem_uma_linha_por_prova(jogo_limpo):
    from jogo.fase import CALENDARIO
    jogo = _semestre(jogo_limpo(), 7.5 * 60)
    jogo.notas = {CALENDARIO[0]: 9.0}     # passou na 1ª prova e caiu na metade da 2ª
    linhas = Boletim(jogo).linhas
    assert len(linhas) == 3
    assert linhas[0].nota == 9.0 and linhas[0].aprovado and linhas[0].situacao == "APROVADO"
    assert linhas[1].nota == 2.0 and not linhas[1].aprovado and linhas[1].situacao == "REPROVADO"
    assert linhas[2].nota is None and linhas[2].situacao == "NÃO CURSOU"


def test_media_so_das_provas_cursadas(jogo_limpo):
    from jogo.fase import CALENDARIO
    jogo = _semestre(jogo_limpo(), 16 * 60)
    jogo.notas = dict(zip(CALENDARIO, (8.0, 10.0, 7.0)))
    jogo.venceu = True
    boletim = Boletim(jogo)
    cursadas = [l.nota for l in boletim.linhas if l.nota is not None]
    assert boletim.media == round(sum(cursadas) / len(cursadas), 1)


def test_derrubar_o_chefe_guarda_a_nota_da_prova_dele(jogo_limpo):
    from jogo.inimigos.fabrica import FabricaDeInimigos
    from jogo.fase import CALENDARIO
    jogo = _semestre(jogo_limpo(), 7 * 60)
    chefe = FabricaDeInimigos.criar("chefe_calculo", jogo.jogador.posicao + (300, 0))
    jogo.iniciar_chefe(chefe, CALENDARIO[0])        # o chefe da 1ª prova ainda vivo durante a 2ª
    jogo.aprovar(chefe)
    assert list(jogo.notas) == [CALENDARIO[0]] and 6 <= jogo.notas[CALENDARIO[0]] <= 10


def test_prova_com_o_chefe_vivo_conta_como_reprovada_pelo_dano_nele(jogo_limpo):
    from jogo.inimigos.fabrica import FabricaDeInimigos
    from jogo.fase import CALENDARIO
    jogo = _semestre(jogo_limpo(), 7 * 60)
    chefe = FabricaDeInimigos.criar("chefe_calculo", jogo.jogador.posicao + (300, 0))
    jogo.iniciar_chefe(chefe, CALENDARIO[0])
    chefe.vida = chefe.vida_maxima / 2
    primeira = Boletim(jogo).linhas[0]
    assert primeira.situacao == "REPROVADO" and primeira.nota == Boletim.nota_contra_o_chefe(chefe) == 5.0
