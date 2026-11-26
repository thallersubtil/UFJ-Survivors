"""Cassino do Centro Acadêmico: apostas com as moedas do jogo."""
import random

import pygame
import pytest

from jogo.aplicacao import Aplicacao
from jogo.cenas.cassino import CenaCassino
from jogo.cenas.cassino_mesas import MesaGenerica, mesa_de
from jogo.cenas.loja import CenaLoja
from jogo.loja.cassino import (JOGOS_DE_APOSTA, Cassino, DadoDoMestre, Desfecho, JogoDeAposta,
                               MaquinaDeSalgadinho, SegredosDoCassino)
from jogo.loja.progresso import Progresso


class RngFixo:
    """Devolve sempre os valores dados, em ordem, para testar os prêmios."""

    def __init__(self, *valores):
        self.valores = list(valores)

    def choice(self, sequencia):
        return self.valores.pop(0)

    def randint(self, a, b):
        return self.valores.pop(0)


def test_jogo_de_aposta_e_abstrato():
    with pytest.raises(TypeError):
        JogoDeAposta()


def test_tres_iguais_pagam_mais_que_dois():
    maquina = MaquinaDeSalgadinho()
    tres = maquina.jogar(10, None, RngFixo("Pequi", "Pequi", "Pequi"))
    dois = maquina.jogar(10, None, RngFixo("Pequi", "Pequi", "Café"))
    nada = maquina.jogar(10, None, RngFixo("Pequi", "Café", "Nota 10"))
    assert tres.premio > dois.premio > nada.premio == 0
    assert tres.simbolos == ("Pequi", "Pequi", "Pequi")


def test_67_67_67_e_o_premio_maximo():
    maquina = MaquinaDeSalgadinho()
    jackpot = maquina.jogar(10, None, RngFixo("67", "67", "67"))
    assert jackpot.premio == 10 * max(MaquinaDeSalgadinho.TRIO.values())


def test_dado_acima_ou_abaixo():
    dado = DadoDoMestre()
    assert dado.jogar(10, "acima", RngFixo(15)).premio == 19
    assert dado.jogar(10, "acima", RngFixo(5)).premio == 0
    assert dado.jogar(10, "abaixo", RngFixo(5)).premio == 19
    assert dado.jogar(10, "abaixo", RngFixo(20)).premio == DadoDoMestre.CRITICO * 10   # 20 natural sempre paga
    assert dado.jogar(10, "acima", RngFixo(1)).premio == 0                               # 1 natural sempre perde
    with pytest.raises(ValueError):
        dado.jogar(10, "talvez", RngFixo(3))


def test_a_casa_sempre_ganha_no_longo_prazo():
    rng = random.Random(1)
    for jogo, escolha in ((MaquinaDeSalgadinho(), None), (DadoDoMestre(), "acima")):
        assert sum(jogo.jogar(10, escolha, rng).premio for _ in range(20_000)) < 10 * 20_000


def test_apostar_desconta_e_paga_no_progresso(tmp_path):
    p = Progresso(tmp_path / "p.json")
    p.ganhar(100)
    resultado = Cassino.apostar(p, DadoDoMestre(), 50, "acima", RngFixo(15))
    assert resultado.premio == 95 and p.moedas == 145
    with pytest.raises(ValueError):
        Cassino.apostar(p, DadoDoMestre(), 1000, "acima", RngFixo(15))
    with pytest.raises(ValueError):
        Cassino.apostar(p, DadoDoMestre(), 0, "acima", RngFixo(15))
    assert p.moedas == 145


# ---------------------------------------------------------------- chances exibidas e all in

TODOS_OS_PALPITES = [(classe(), escolha) for classe in JOGOS_DE_APOSTA for escolha in classe.ESCOLHAS]


@pytest.mark.parametrize("jogo,escolha", TODOS_OS_PALPITES)
def test_tabela_de_premios_soma_100_e_a_casa_ganha(jogo, escolha):
    tabela = jogo.tabela(escolha)
    assert sum(linha.chance for linha in tabela) == pytest.approx(1)
    assert 0.8 < jogo.retorno_esperado(escolha) < 1          # esperança negativa para o aluno, exata (sem sorteio)


@pytest.mark.parametrize("jogo,escolha", TODOS_OS_PALPITES)
def test_chance_exibida_bate_com_o_sorteio_de_verdade(jogo, escolha):
    """A porcentagem da tabela sai dos mesmos sorteios que `jogar` usa: jogando muito, a frequência confere."""
    rng = random.Random(42)
    rodadas = 40_000
    contagem = {}
    for _ in range(rodadas):
        resultado = jogo.jogar(100, escolha, rng)
        contagem[resultado.rotulo] = contagem.get(resultado.rotulo, 0) + 1
    tabela = {linha.rotulo: linha for linha in jogo.tabela(escolha)}
    assert set(contagem) <= set(tabela)
    for rotulo, linha in tabela.items():
        assert contagem.get(rotulo, 0) / rodadas == pytest.approx(linha.chance, abs=0.012)


def test_tabela_da_maquina_tem_os_numeros_certos():
    tabela = {linha.rotulo: linha for linha in MaquinaDeSalgadinho().tabela()}
    assert tabela["Três 67"].chance == pytest.approx(1 / 216) and tabela["Três 67"].multiplicador == 30
    assert tabela["Três 67"].chance_formatada == "0,46%" and tabela["Três 67"].multiplicador_formatado == "30x"
    assert tabela["Dois iguais"].chance_formatada == "41,67%" and tabela["Dois iguais"].multiplicador_formatado == "1,5x"
    assert tabela["Nada"].chance_formatada == "55,56%" and tabela["Nada"].multiplicador_formatado == "perde"


def test_premio_arredonda_para_baixo_e_nunca_favorece_o_aluno():
    assert JogoDeAposta.premio_de(1, 1.5) == 1 and JogoDeAposta.premio_de(3, 1.5) == 4
    assert JogoDeAposta.premio_de(30, 1.9) == 57                 # sem erro de ponto flutuante (30 * 1.9 = 56.99...)
    for aposta in range(1, 300):
        for jogo, escolha in TODOS_OS_PALPITES:
            medio = sum(linha.chance * jogo.premio_de(aposta, linha.multiplicador) for linha in jogo.tabela(escolha))
            assert medio < aposta


def test_all_in_aposta_o_saldo_inteiro(tmp_path):
    p = Progresso(tmp_path / "p.json")
    p.ganhar(137)
    assert Cassino.aposta_maxima(p) == 137
    perdeu = Cassino.apostar_tudo(p, DadoDoMestre(), "acima", RngFixo(5))
    assert perdeu.aposta == 137 and p.moedas == 0
    with pytest.raises(ValueError):                              # sem moedas não há all in
        Cassino.apostar_tudo(p, DadoDoMestre(), "acima", RngFixo(15))
    p.ganhar(40)
    ganhou = Cassino.apostar_tudo(p, DadoDoMestre(), "acima", RngFixo(20))
    assert ganhou.aposta == 40 and p.moedas == 100


def test_palpite_invalido_nao_gasta_moedas(tmp_path):
    p = Progresso(tmp_path / "p.json")
    p.ganhar(100)
    with pytest.raises(ValueError):
        Cassino.apostar(p, DadoDoMestre(), 50, "talvez", RngFixo(3))
    assert p.moedas == 100


# ---------------------------------------------------------------- a tela

def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def clique(caixa):
    """Clique no meio de uma caixa da camada de 640x360 (a tela é o dobro)."""
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(caixa.centerx * 2, caixa.centery * 2), button=1)


def cena_com(tmp_path, moedas, *valores):
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.progresso = Progresso(tmp_path / "progresso.json")
    if moedas:
        app.progresso.ganhar(moedas)
    cena = CenaCassino(app, RngFixo(*valores))
    app.trocar(cena)
    return app, cena


def test_all_in_pela_tecla_aposta_tudo(tmp_path):
    app, cena = cena_com(tmp_path, 137, "Pequi", "Café", "67")
    app.passo(1 / 60, [tecla(CenaCassino.TECLA_ALL_IN)])
    assert cena.apostando_tudo and cena.aposta == 137
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert cena.girando and cena.resultado.aposta == 137 and app.progresso.moedas == 0
    assert cena.aposta_na_tela == 137                            # a tela ainda mostra o que está na mesa
    for _ in range(150):
        app.passo(1 / 60, [])
    assert not cena.girando and app.progresso.moedas == 0


def test_all_in_pelo_clique_e_botao_de_jogar(tmp_path):
    app, cena = cena_com(tmp_path, 480, 20)
    app.passo(1 / 60, [tecla(pygame.K_TAB)])                     # Dado do Mestre
    app.passo(1 / 60, [clique(cena.caixa_da_ficha(len(cena.jogo.APOSTAS)))])
    assert cena.apostando_tudo and cena.aposta == 480
    app.passo(1 / 60, [clique(CenaCassino.BOTAO_JOGAR)])
    assert cena.resultado.aposta == 480
    assert app.progresso.moedas == 480 * DadoDoMestre.CRITICO    # 20 natural: 2,5x
    for _ in range(150):
        app.passo(1 / 60, [])
    assert cena.aposta == app.progresso.moedas                   # o all in acompanha o saldo novo


def test_setas_chegam_ao_all_in_e_ficha_clicada_escolhe_a_aposta(tmp_path):
    app, cena = cena_com(tmp_path, 60)
    for _ in range(10):
        app.passo(1 / 60, [tecla(pygame.K_RIGHT)])
    assert cena.apostando_tudo
    app.passo(1 / 60, [tecla(pygame.K_LEFT)])
    assert cena.aposta == cena.jogo.APOSTAS[-1]
    app.passo(1 / 60, [clique(cena.caixa_da_ficha(1))])
    assert cena.aposta == cena.jogo.APOSTAS[1]


def test_aposta_nunca_passa_do_saldo(tmp_path):
    app, cena = cena_com(tmp_path, 60)
    app.passo(1 / 60, [clique(cena.caixa_da_ficha(3))])          # ficha de 100 com 60 moedas
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert not cena.girando and "insuficientes" in cena.mensagem and app.progresso.moedas == 60
    app.progresso.gastar(60)
    app.passo(1 / 60, [tecla(CenaCassino.TECLA_ALL_IN), tecla(pygame.K_RETURN)])    # all in sem nada
    assert not cena.girando and "insuficientes" in cena.mensagem


def test_tela_mostra_as_chances_da_tabela_do_jogo(tmp_path):
    app, cena = cena_com(tmp_path, 1000)
    for _ in range(len(cena.jogos)):
        tabela = cena.jogo.tabela(cena.escolha)
        assert cena.linhas_da_tabela == [
            (linha.rotulo, linha.chance_formatada, linha.multiplicador_formatado,
             cena.jogo.premio_de(cena.aposta, linha.multiplicador)) for linha in tabela]
        assert all(chance.endswith("%") for _, chance, _, _ in cena.linhas_da_tabela)
        app.passo(1 / 60, [tecla(pygame.K_TAB)])


def test_cada_jogo_tem_mesa_e_jogo_novo_cai_na_generica(tmp_path):
    class CaraOuCoroa(JogoDeAposta):
        NOME = "Cara ou Coroa"

        def sorteios(self):
            return ("cara", "coroa")

        def avaliar(self, sorteio, escolha):
            return Desfecho(sorteio, 1.9 if sorteio == "cara" else 0, sorteio, (sorteio,))

    assert isinstance(mesa_de(CaraOuCoroa()), MesaGenerica)
    assert CaraOuCoroa().retorno_esperado() == pytest.approx(0.95)
    app, cena = cena_com(tmp_path, 100, "cara")
    cena.jogos.append(CaraOuCoroa())
    cena.mesas.append(mesa_de(cena.jogos[-1]))
    cena._selecionar_jogo(len(cena.jogos) - 1)
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    for _ in range(150):
        app.passo(1 / 60, [])
    assert app.progresso.moedas == 100 - 10 + 19


def test_cassino_desenha_ganho_e_perda_em_todos_os_jogos(tmp_path):
    for indice, valores in ((0, ("67", "67", "67")), (0, ("Pequi", "Café", "67")), (1, (20,)), (1, (1,)),
                            (2, ("Strogonoff",)), (2, ("Fila",))):
        app, cena = cena_com(tmp_path, 300, *valores)
        cena._selecionar_jogo(indice)
        app.passo(1 / 60, [tecla(CenaCassino.TECLA_ALL_IN), tecla(pygame.K_RETURN)])
        for _ in range(200):                                     # giro, resultado e as animações até o fim
            app.passo(1 / 60, [])
        assert cena.tempo_do_resultado > 1


# ---------------------------------------------------------------- segredos do cassino (item da loja)

def test_tabela_de_chances_fica_trancada_sem_o_item_da_loja(tmp_path):
    app, cena = cena_com(tmp_path, 1000)
    assert not cena.segredos_liberados and not cena.tabela_aberta
    app.passo(1 / 60, [clique(CenaCassino.BOTAO_SEGREDOS)])
    assert not cena.tabela_aberta and "Trancado" in cena.mensagem
    app.passo(1 / 60, [tecla(CenaCassino.TECLA_SEGREDOS)])
    assert not cena.tabela_aberta
    assert app.progresso.moedas == 1000                          # clicar no cadeado não aposta nem gasta


def test_com_o_item_a_tabela_abre_e_fecha_por_clique_e_por_tecla(tmp_path):
    app, cena = cena_com(tmp_path, 1000)
    assert app.progresso.desbloquear(SegredosDoCassino)
    assert app.progresso.moedas == 1000 - SegredosDoCassino.PRECO_DESBLOQUEIO
    assert cena.segredos_liberados and not cena.tabela_aberta    # liberada, mas só aparece quando consultada
    app.passo(1 / 60, [clique(CenaCassino.BOTAO_SEGREDOS)])
    assert cena.tabela_aberta and not cena.mensagem
    app.passo(1 / 60, [clique(CenaCassino.PAINEL)])              # clicar na tabela aberta fecha, sem apostar
    assert not cena.tabela_aberta and not cena.girando
    app.passo(1 / 60, [tecla(CenaCassino.TECLA_SEGREDOS)])
    assert cena.tabela_aberta
    app.passo(1 / 60, [clique(CenaCassino.BOTAO_SEGREDOS)])
    assert not cena.tabela_aberta
    app.passo(1 / 60, [tecla(CenaCassino.TECLA_SEGREDOS), tecla(pygame.K_TAB)])
    assert cena.tabela_aberta                                    # continua aberta ao trocar de jogo
    novo_app, nova_cena = cena_com(tmp_path, 0)                   # o item fica salvo; a consulta começa fechada
    assert nova_cena.segredos_liberados and not nova_cena.tabela_aberta


def test_loja_vende_os_segredos_do_cassino(tmp_path):
    app, _ = cena_com(tmp_path, 5000)
    loja = CenaLoja(app)
    app.trocar(loja)
    loja._trocar_aba(CenaLoja.ABAS.index("DESBLOQUEIOS"))
    nomes = [linha.nome for linha in loja.linhas()]
    assert SegredosDoCassino.NOME == "Segredos do Cassino do CA" and SegredosDoCassino.NOME in nomes
    loja.indice = nomes.index(SegredosDoCassino.NOME)
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert app.progresso.desbloqueado(SegredosDoCassino)
    assert app.progresso.moedas == 5000 - SegredosDoCassino.PRECO_DESBLOQUEIO
    assert loja.linhas()[loja.indice].preco is None              # não dá para comprar duas vezes
    for _ in range(30):
        app.passo(1 / 60, [])
