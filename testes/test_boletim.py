"""Boletim do fim de jogo: uma nota por prova, a partir do que aconteceu na partida."""
from jogo.boletim import Boletim


def test_prova_aprovada_tira_nota_pela_vida_que_sobrou(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.vida = jogo.jogador.vida_maxima / 2
    assert Boletim.nota_de_aprovacao(jogo.jogador) == 8.0
    jogo.jogador.vida = jogo.jogador.vida_maxima
    assert Boletim.nota_de_aprovacao(jogo.jogador) == 10.0


def _semestre(jogo, indice):
    from jogo.fase import PROVAS
    jogo.fases = [prova() for prova in PROVAS]
    jogo.indice_fase = indice
    jogo.fase = jogo.fases[indice]
    return jogo


def test_boletim_tem_uma_linha_por_prova(jogo_limpo):
    jogo = _semestre(jogo_limpo(), 1)
    jogo.notas = [9.0]                    # passou na 1ª prova e caiu na metade da 2ª
    jogo.fase.tempo = jogo.fase.DURACAO / 2
    linhas = Boletim(jogo).linhas
    assert len(linhas) == 3
    assert linhas[0].nota == 9.0 and linhas[0].aprovado and linhas[0].situacao == "APROVADO"
    assert linhas[1].nota == 2.0 and not linhas[1].aprovado and linhas[1].situacao == "REPROVADO"
    assert linhas[2].nota is None and linhas[2].situacao == "NÃO CURSOU"


def test_media_so_das_provas_cursadas(jogo_limpo):
    jogo = _semestre(jogo_limpo(), 2)
    jogo.notas = [8.0, 10.0, 7.0]
    jogo.venceu = True
    boletim = Boletim(jogo)
    cursadas = [l.nota for l in boletim.linhas if l.nota is not None]
    assert boletim.media == round(sum(cursadas) / len(cursadas), 1)


def test_concluir_a_prova_guarda_a_nota(jogo_limpo):
    jogo = jogo_limpo()
    jogo.concluir_fase()
    assert len(jogo.notas) == 1 and 6 <= jogo.notas[0] <= 10
