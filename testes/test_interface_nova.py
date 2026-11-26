"""Interface nova (inspirada no HoloCure): HUD, nível, pausa e as telas do Centro Acadêmico."""
import pygame

from jogo.cenas.hud import Hud
from jogo.ui.pixel import A, L, CamadaPixel, barra, moldura, texto


def test_camada_pixel_amplia_para_a_tela_inteira():
    camada = CamadaPixel()
    ui = camada.limpar()
    assert ui.get_size() == (L, A) == (640, 360)
    pygame.draw.rect(ui, (255, 0, 0), (0, 0, 1, 1))
    tela = pygame.Surface((1280, 720))
    camada.apresentar(tela)
    assert tela.get_at((1, 1))[:3] == (255, 0, 0)       # 1 px da camada vira um bloco 2x2
    assert CamadaPixel.para_camada((101, 51)) == (50, 25)


def test_pecas_basicas_desenham_sem_erro():
    ui = CamadaPixel().limpar()
    r = texto(ui, "Olá", (10, 10))
    assert r.w > 0
    moldura(ui, (0, 0, 40, 20), alfa=200)
    barra(ui, (0, 30, 50, 6), 1.4, (255, 0, 0), atraso=0.5, segmentos=5, brilho_t=0.3)


def test_hud_desenha_a_partida(jogo_limpo):
    jogo = jogo_limpo()
    hud = Hud()
    tela = pygame.Surface((1280, 720))
    hud.atualizar(1 / 60, jogo)
    hud.desenhar(tela, jogo)


def test_hud_barra_de_vida_cai_aos_poucos(jogo_limpo):
    jogo = jogo_limpo()
    hud = Hud()
    hud.atualizar(1 / 60, jogo)
    jogo.jogador.vida = jogo.jogador.vida_maxima / 2
    hud.atualizar(1 / 60, jogo)
    assert hud.vida_atrasada > 0.9                   # o branco do dano ainda aparece
    for _ in range(180):
        hud.atualizar(1 / 60, jogo)
    assert abs(hud.vida_atrasada - 0.5) < 0.01


def test_hud_avisa_quando_sobe_de_nivel(jogo_limpo):
    jogo = jogo_limpo()
    hud = Hud()
    hud.atualizar(1 / 60, jogo)
    assert hud.destaque_nivel == 0
    jogo.jogador.nivel += 1
    hud.atualizar(1 / 60, jogo)
    assert hud.destaque_nivel > 0


def _app(tmp_path):
    from jogo.aplicacao import Aplicacao
    from jogo.loja.progresso import Progresso
    from jogo.ranking import Ranking
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.ranking, app.progresso = Ranking(tmp_path / "r.json"), Progresso(tmp_path / "p.json")
    return app


def _tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def test_nivel_carimba_a_escolhida_e_volta_depois(tmp_path):
    from jogo.cenas.nivel import CenaNivel
    from jogo.cenas.partida import CenaPartida
    from jogo.jogador.classes import Programador
    app = _app(tmp_path)
    partida = CenaPartida(app, Programador)
    app.trocar(partida)
    partida.jogo.niveis_pendentes = 1
    app.passo(1 / 60, [])
    cena = app.cena_atual
    assert isinstance(cena, CenaNivel)
    app.passo(1 / 60, [_tecla(pygame.K_2)])
    assert cena.escolhida == 1 and partida.jogo.niveis_pendentes == 0
    app.passo(1 / 60, [_tecla(pygame.K_1)])          # durante o carimbo não escolhe de novo
    assert cena.escolhida == 1
    cena.desenhar(pygame.Surface((1280, 720)))
    for _ in range(40):
        app.passo(1 / 60, [])
    assert app.cena_atual is partida


def test_nivel_mouse_acha_a_folha_na_tela(tmp_path):
    from jogo.cenas.nivel import CenaNivel
    from jogo.cenas.partida import CenaPartida
    from jogo.jogador.classes import Programador
    app = _app(tmp_path)
    partida = CenaPartida(app, Programador)
    cena = CenaNivel(app, partida.jogo)
    alvo = cena.cartoes[-1]
    cena.tratar_evento(pygame.event.Event(pygame.MOUSEMOTION, pos=alvo.center, rel=(0, 0), buttons=(0, 0, 0)))
    assert cena.indice == len(cena.opcoes) - 1


def test_pausa_desce_do_menu_para_as_fotos_e_volta(tmp_path):
    from jogo.cenas.partida import CenaPartida
    from jogo.cenas.pausa import CenaPausa
    from jogo.jogador.classes import Otaku
    app = _app(tmp_path)
    partida = CenaPartida(app, Otaku)
    app.trocar(partida)
    app.passo(1 / 60, [_tecla(pygame.K_ESCAPE)])
    pausa = app.cena_atual
    assert isinstance(pausa, CenaPausa)
    app.passo(1 / 60, [_tecla(pygame.K_DOWN)] * 3)
    assert not pausa.no_menu and pausa.foto == 0
    pausa.desenhar(pygame.Surface((1280, 720)))       # mostra a descrição da foto no quadro
    app.passo(1 / 60, [_tecla(pygame.K_UP)])
    assert pausa.no_menu
    app.passo(1 / 60, [_tecla(pygame.K_RETURN)])        # "Ir embora"
    from jogo.cenas.titulo import CenaTitulo
    assert isinstance(app.cena_atual, CenaTitulo)


def test_matricula_tira_a_foto_e_so_depois_comeca_a_partida(tmp_path):
    from jogo.cenas.matricula import CenaMatricula
    from jogo.cenas.partida import CenaPartida
    from jogo.jogador.classes import CLASSES
    app = _app(tmp_path)
    cena = CenaMatricula(app)
    app.trocar(cena)
    app.passo(1 / 60, [_tecla(pygame.K_RIGHT)])                           # troca de classe
    cena.desenhar(pygame.Surface((1280, 720)))                            # durante o retrato se abrindo
    app.passo(1 / 60, [_tecla(pygame.K_RETURN)])
    assert cena.foto_tirada_em is not None and app.cena_atual is cena
    app.passo(1 / 60, [_tecla(pygame.K_RIGHT)])                           # depois da foto não mexe mais
    assert cena.indice == 1
    cena.desenhar(pygame.Surface((1280, 720)))                            # carteirinha saindo da impressora
    for _ in range(80):
        app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaPartida)
    assert isinstance(app.cena_atual.jogo.jogador, CLASSES[1])
    assert app.classe_escolhida == 1                                      # lembra a última escolha
    assert CenaMatricula(app).indice == 1


def test_matricula_abas_escolhem_e_o_botao_tira_a_foto(tmp_path):
    from jogo.cenas.matricula import CenaMatricula
    from jogo.jogador.classes import CLASSES
    app = _app(tmp_path)
    cena = CenaMatricula(app)
    app.trocar(cena)
    def clicar(r):
        cena.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(r.centerx * 2, r.centery * 2), button=1))
    clicar(cena.aba(len(CLASSES) - 1))
    assert cena.indice == len(CLASSES) - 1
    app.passo(1 / 60, [_tecla(pygame.K_RIGHT)])                           # dá a volta
    assert cena.indice == 0
    clicar(cena.botao_foto)
    assert cena.foto_tirada_em is not None


def test_matricula_mostra_o_retrato_de_cada_classe(tmp_path):
    from jogo.cenas.matricula import CenaMatricula
    from jogo.jogador.classes import CLASSES
    from jogo.nucleo.recursos import Recursos
    cena = CenaMatricula(_app(tmp_path))
    for i, classe in enumerate(CLASSES):
        assert (Recursos.pasta / classe.RETRATO).is_file()
        retrato = cena._retrato(i, (138, 176))
        assert retrato.get_width() <= 138 and retrato.get_height() <= 176      # cabe inteiro no quadro da webcam
        assert retrato.get_width() == 138 or retrato.get_height() == 176      # e ocupa o quadro todo num dos lados
        cena.escolher(i)
        cena.desenhar(pygame.Surface((1280, 720)))


def test_treino_agenda_mouse_escolhe_e_marca(tmp_path):
    from jogo.cenas.treino import CenaTreino
    app = _app(tmp_path)
    cena = CenaTreino(app)
    app.trocar(cena)
    def clicar(r):
        cena.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(r.centerx * 2, r.centery * 2), button=1))
    clicar(cena.linha(2))
    assert cena.indice == 2
    clicar(cena.caixa_marcar(1))
    assert cena.imortal
    cena.desenhar(pygame.Surface((1280, 720)))
    clicar(cena.linha(2))                       # clicar de novo na escolhida começa
    from jogo.cenas.matricula import CenaMatricula
    assert isinstance(app.cena_atual, CenaMatricula) and app.cena_atual.opcoes.imortal


def test_area_interativa_aceita_forma_em_l():
    from jogo.ui.area import AreaInterativa
    loja = AreaInterativa("LOJA", [(0, 0), (100, 0), (100, 50), (200, 50), (200, 100), (0, 100)])
    assert loja.contem((50, 20)) and loja.contem((150, 80))
    assert not loja.contem((150, 20))               # o canto vazio do L não conta


def test_centro_academico_mouse_destaca_e_clique_entra_com_zoom(tmp_path):
    from jogo.cenas.cassino import CenaCassino
    from jogo.cenas.centro_academico import CenaCentroAcademico
    app = _app(tmp_path)
    cena = CenaCentroAcademico(app)
    app.trocar(cena)
    cena.tratar_evento(pygame.event.Event(pygame.MOUSEMOTION, pos=(1150, 350), rel=(0, 0), buttons=(0, 0, 0)))
    assert cena.areas[cena.indice].nome == "CASSINO"
    cena.desenhar(pygame.Surface((1280, 720)))
    cena.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1150, 350), button=1))
    assert cena.entrando is not None
    cena.desenhar(pygame.Surface((1280, 720)))
    for _ in range(40):
        app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaCassino)


def test_centro_academico_botao_voltar(tmp_path):
    from jogo.cenas.centro_academico import CenaCentroAcademico
    from jogo.cenas.titulo import CenaTitulo
    app = _app(tmp_path)
    cena = CenaCentroAcademico(app)
    app.trocar(cena)
    c = cena.BOTAO_VOLTAR.center
    cena.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(c[0] * 2, c[1] * 2), button=1))
    assert isinstance(app.cena_atual, CenaTitulo)


def test_toda_melhoria_tem_um_objeto_na_estante():
    """Melhoria nova precisa de um objeto em CenaLoja.OBJETOS (o retângulo dela na arte do CA)."""
    from jogo.cenas.loja import CenaLoja
    from jogo.loja.melhorias import MELHORIAS
    assert {m.CHAVE for m in MELHORIAS} <= set(CenaLoja.OBJETOS)


def test_loja_clique_escolhe_o_objeto_e_segundo_clique_compra(tmp_path):
    from jogo.cenas.loja import CenaLoja
    app = _app(tmp_path)
    app.progresso.ganhar(1000)
    cena = CenaLoja(app)
    app.trocar(cena)
    area = cena.areas()[4]
    cena.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=area.centro, button=1))
    assert cena.indice == 4 and app.progresso.moedas == 1000
    cena.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=area.centro, button=1))
    assert app.progresso.moedas < 1000
    for aba in range(3):
        cena._trocar_aba(aba)
        cena.desenhar(pygame.Surface((1280, 720)))


def test_sala_de_trofeus_navega_e_volta(tmp_path):
    from jogo.cenas.centro_academico import CenaCentroAcademico
    from jogo.cenas.conquistas import CenaConquistas, tipo_da_taca
    from jogo.loja.conquistas import CONQUISTAS
    app = _app(tmp_path)
    app.progresso.registrar_conquista(CONQUISTAS[0].CHAVE)
    cena = CenaConquistas(app)
    app.trocar(cena)
    app.passo(1 / 60, [_tecla(pygame.K_DOWN), _tecla(pygame.K_RIGHT)])
    assert cena.indice == 6
    cena.desenhar(pygame.Surface((1280, 720)))
    assert {tipo_da_taca(c) for c in CONQUISTAS} <= {"ouro", "prata", "bronze"}
    app.passo(1 / 60, [_tecla(pygame.K_ESCAPE)])
    assert isinstance(app.cena_atual, CenaCentroAcademico)


def test_ranking_podio_e_lista(tmp_path):
    from jogo.cenas.ranking import CenaRanking
    from jogo.ranking import RegistroRanking
    app = _app(tmp_path)
    tela = pygame.Surface((1280, 720))
    CenaRanking(app).desenhar(tela)                          # vazio
    registros = [RegistroRanking(f"Aluno{i}", "Otaku", 1000 - i * 50, 300 + i, venceu=i == 0) for i in range(10)]
    for r in registros:
        app.ranking.adicionar(r)
    cena = CenaRanking(app, destaque=registros[5])
    cena.atualizar(2.0)
    cena.desenhar(tela)
    assert cena.pasta_do_heroi("Otaku") == "otaku"


def test_fim_de_jogo_boletim_desenha_aprovado_e_reprovado(tmp_path):
    from jogo.cenas.fim import CenaFimDeJogo
    from jogo.cenas.partida import CenaPartida
    from jogo.jogador.classes import Otaku
    for venceu in (True, False):
        app = _app(tmp_path)
        partida = CenaPartida(app, Otaku)
        partida.jogo.terminar(venceu)
        cena = CenaFimDeJogo(app, partida.jogo)
        cena.nome = "Ana"
        for t in (0.1, 1.5, 3.1, 4.0):
            cena.tempo = t
            cena.desenhar(pygame.Surface((1280, 720)))
        assert len(cena.boletim.linhas) == len(partida.jogo.fases)


def test_cada_classe_tem_rosto_e_o_hud_e_a_carteirinha_usam_ele(tmp_path):
    from jogo.cenas.hud import Hud
    from jogo.cenas.matricula import CenaMatricula
    from jogo.jogador.classes import CLASSES
    from jogo.jogador.jogador import Jogador
    from jogo.jogo import Jogo
    assert Jogador.rosto(80) is None                                   # a base não tem arte
    for classe in CLASSES:
        assert classe.rosto(80).get_size() == (80, 80)
    jogo = Jogo(CLASSES[0], semente=1)
    tela = pygame.Surface((1280, 720))
    hud = Hud()
    hud.desenhar(tela, jogo)
    quadro = Hud.RETRATO
    centro = tela.get_at((quadro.centerx * 2, quadro.centery * 2 + 10))
    assert centro[:3] != (52, 74, 150)                                 # o rosto cobre o fundo azul do quadro
    cena = CenaMatricula(_app(tmp_path))
    cena.tirar_foto()
    cena.tempo += 0.8
    cena.desenhar(tela)
    assert cena._foto_impressa is not None


def test_perigo_avisa_antes_e_a_partida_para_para_apresentar_o_chefe(tmp_path):
    from jogo.cenas.chefe import CenaChefe
    from jogo.cenas.partida import CenaPartida
    from jogo.fase import ProvaDeCalculo
    from jogo.jogador.classes import Programador
    from jogo.opcoes import OpcoesDePartida
    app = _app(tmp_path)
    opcoes = OpcoesDePartida.treino_contra(ProvaDeCalculo, direto_no_chefe=True, imortal=True)
    partida = CenaPartida(app, Programador, opcoes)
    app.trocar(partida)
    jogo = partida.jogo
    app.passo(1 / 60, [])
    assert jogo.perigo > 0 and jogo.chefe is None                      # primeiro o aviso
    tela = pygame.Surface((1280, 720))
    partida.desenhar(tela)                                              # faixas de PERIGO! por cima do HUD
    for _ in range(4 * 60):
        app.passo(1 / 60, [])
        if isinstance(app.cena_atual, CenaChefe):
            break
    apresentacao = app.cena_atual
    assert isinstance(apresentacao, CenaChefe) and jogo.chefe is not None and jogo.perigo == 0
    assert apresentacao.frase == "O Professor de Cálculo Flávio apareceu!"
    tempo_da_partida = jogo.placar.tempo
    for _ in range(40):
        app.passo(1 / 60, [])
        apresentacao.desenhar(tela)
    assert jogo.placar.tempo == tempo_da_partida                        # a partida fica parada
    app.passo(1 / 60, [_tecla(pygame.K_RETURN)])                        # Enter pula
    assert app.cena_atual is partida
    app.passo(1 / 60, [])
    assert jogo.placar.tempo > tempo_da_partida and app.cena_atual is partida    # e não apresenta de novo


def test_a_professora_e_apresentada_no_feminino():
    from jogo.cenas.chefe import CenaChefe
    from jogo.inimigos.professora_de_td_e_poo import ProfessoraDeTDEPOO
    from jogo.nucleo.recursos import Recursos
    assert ProfessoraDeTDEPOO.ARTIGO == "Uma" and (Recursos.pasta / ProfessoraDeTDEPOO.ILUSTRACAO).is_file()


def test_apresentacao_dos_chefes_usa_o_nome_de_cada_professor():
    from jogo.cenas.chefe import CenaChefe
    from jogo.inimigos.fabrica import FabricaDeInimigos
    esperado = {"chefe_calculo": "O Professor de Cálculo Flávio apareceu!",
                "chefe_arquitetura_ed": "O Professor de Arquitetura e ED Bruno apareceu!",
                "chefe_td_poo": "A Professora de TD e POO Emília apareceu!"}
    for nome, frase in esperado.items():
        assert CenaChefe(None, FabricaDeInimigos.criar(nome, (0, 0))).frase == frase
