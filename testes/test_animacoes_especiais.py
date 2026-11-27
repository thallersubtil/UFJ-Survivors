"""Animações especiais dos mini-chefes (arremessos, golpes, segunda fase) e o que a base MiniChefe oferece para
elas: encenar uma animação, agendar o golpe para o quadro certo e mudar de fase com pouca vida."""
import pygame
import pytest

from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.mini_chefes import MINI_CHEFES
from jogo.nucleo.recursos import Recursos

COM_ANIMACOES_ESPECIAIS = {
    "leao_do_proerd": {"andar_bastao", "golpe", "comer"},
    "tia_da_cantina": {"arremessar", "panelao", "girar", "andar_concha"},
    "lobo_guara": {"uivar", "bote", "cavar", "emergir"},
    "vigilante": {"lanterna", "arrancada", "gancho", "voadora"},
    "bibliotecaria": {"anotar", "arremessar", "shhh"},
    "tecnico_do_laboratorio": {"arremessar", "socar_chao", "andar_furia"},
    "reitor": {"carimbar", "apresentar"},
    "loira_da_odontologia": {"chamar", "chave", "broca"},
    "agroboy": {"dinheiro", "laco", "andar_touro"},
    "grao_mestre_do_culto": {"ritual", "andar_ascensao"},
    "gotica_trevosa": {"sumir", "vodu"},
    "et_de_varginha": {"telepatia", "andar_disco"},
}


def pes(quadro):
    """A última linha com algo desenhado."""
    mascara = pygame.mask.from_surface(quadro, 40)
    caixas = mascara.get_bounding_rects()
    return max(c.bottom for c in caixas)


@pytest.mark.parametrize("nome", sorted(COM_ANIMACOES_ESPECIAIS))
def test_animacoes_especiais_existem_e_nao_fazem_o_personagem_pular(nome):
    """O jogo desenha cada quadro centrado na posição: os pés têm de ficar à mesma distância do meio em todas
    as animações, a mesma do andar, para ele não afundar nem flutuar ao trocar de animação."""
    pasta = FabricaDeInimigos.classe(nome).PASTA_SPRITE
    animacoes = Recursos.animacoes(pasta)
    assert COM_ANIMACOES_ESPECIAIS[nome] <= set(animacoes)
    andar = animacoes["andar"].quadros[0]
    distancia = pes(andar) - andar.get_height() / 2
    for animacao in animacoes.values():
        larguras = {q.get_width() for q in animacao.quadros}
        assert len(larguras) == 1
        for quadro in animacao.quadros:
            if pes(quadro) < quadro.get_height() - 3:                # quadro no ar (bote, voadora): não conta
                continue
            assert abs((pes(quadro) - quadro.get_height() / 2) - distancia) <= 3


def test_encenar_toca_a_animacao_do_primeiro_ao_ultimo_quadro_e_pode_parar_o_chefe(jogo_limpo):
    jogo = jogo_limpo()
    tia = FabricaDeInimigos.criar("tia_da_cantina", jogo.jogador.posicao + (300, 0))
    jogo.adicionar(tia)
    tia._espera_ataque = 99
    tia.encenar("panelao", 0.6, parado=True)
    parada = pygame.Vector2(tia.posicao)
    vistos = []
    while tia.encenando:
        tia.mover(1 / 30, jogo)
        if tia.encenando:
            assert tia.posicao == parada
            vistos.append(tia.animador.animacao.quadros.index(tia.animador.quadro_atual))
    assert vistos == sorted(vistos) and set(vistos) == set(range(6))
    tia.mover(1 / 30, jogo)
    assert tia.posicao != parada and tia.escolher_animacao() == "andar"


def test_agendar_faz_a_acao_na_hora_certa(jogo_limpo):
    jogo = jogo_limpo()
    tia = FabricaDeInimigos.criar("tia_da_cantina", jogo.jogador.posicao + (300, 0))
    tia._espera_ataque = 99
    feito = []
    tia.agendar(0.3, lambda j: feito.append(j))
    for _ in range(8):
        tia.mover(1 / 30, jogo)
    assert feito == []
    for _ in range(2):
        tia.mover(1 / 30, jogo)
    assert feito == [jogo]


def test_so_quem_tem_segunda_fase_muda_de_fase(jogo_limpo):
    jogo = jogo_limpo()
    for nome in MINI_CHEFES:
        chefe = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + (300, 0))
        chefe._espera_ataque = 99
        chefe.vida = chefe.vida_maxima * 0.1
        chefe.mover(1 / 30, jogo)
        assert chefe.segunda_fase == bool(chefe.SEGUNDA_FASE_ABAIXO_DE), nome


# ---- Tia da Cantina

from jogo.inimigos.mini_chefes import TiaDaCantina  # noqa: E402
from jogo.projeteis.tematicos import Marca, PanelaoDeSopa, ProjetilTematico, arte_existe  # noqa: E402


def novas(jogo, classe):
    return [e for e in jogo._novas + jogo.entidades if isinstance(e, classe) and e.ativo]


def criar(jogo, nome, distancia=300):
    chefe = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + (distancia, 0))
    chefe._espera_ataque = 99
    jogo.adicionar(chefe)
    return chefe


def na_segunda_fase(jogo, chefe):
    chefe.vida = chefe.vida_maxima * chefe.SEGUNDA_FASE_ABAIXO_DE
    chefe.mover(1 / 30, jogo)
    assert chefe.segunda_fase


def test_tia_arremessa_a_bandeja_no_quadro_do_arremesso(jogo_limpo):
    jogo = jogo_limpo()
    tia = criar(jogo, "tia_da_cantina")
    tia.ataques = 1
    tia.atacar(jogo)
    assert tia.escolher_animacao() == "arremessar" and not novas(jogo, ProjetilTematico)
    tia.cumprir_agenda(TiaDaCantina.SAIDA_DA_BANDEJA, jogo)
    assert {p.arte for p in novas(jogo, ProjetilTematico)} == {"bandeja"}


def test_tia_ergue_o_panelao_parada_e_joga_onde_o_aluno_esta_na_hora(jogo_limpo):
    jogo = jogo_limpo()
    tia = criar(jogo, "tia_da_cantina")
    tia.ataques = 3
    tia.atacar(jogo)
    assert tia.escolher_animacao() == "panelao" and not novas(jogo, PanelaoDeSopa)
    jogo.jogador.posicao += (0, 120)                        # o aluno andou enquanto ela erguia
    tia.cumprir_agenda(TiaDaCantina.SAIDA_DO_PANELAO, jogo)
    panelao, = novas(jogo, PanelaoDeSopa)
    assert panelao.posicao == jogo.jogador.posicao


def test_tia_pega_a_concha_gigante_com_metade_da_vida(jogo_limpo):
    jogo = jogo_limpo()
    tia = criar(jogo, "tia_da_cantina")
    assert tia.escolher_animacao() == "andar"
    na_segunda_fase(jogo, tia)
    assert tia.escolher_animacao() == "andar_concha"


def test_tia_gira_com_a_concha_atras_do_aluno_e_bate_de_tempos_em_tempos(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.vida_maxima = jogo.jogador.vida = 10 ** 6
    tia = criar(jogo, "tia_da_cantina", distancia=400)
    na_segunda_fase(jogo, tia)
    tia.ataques = 3
    tia.atacar(jogo)
    assert tia.girando and tia.escolher_animacao() == "girar"
    inicio = tia.posicao.distance_to(jogo.jogador.posicao)
    quadros = set()
    for _ in range(15):
        tia.perseguir(1 / 30, jogo)
        quadros.add(tia.animador.animacao.quadros.index(tia.animador.quadro_atual))
    andou = inicio - tia.posicao.distance_to(jogo.jogador.posicao)
    assert andou > tia.velocidade * 0.5 * 1.5 and quadros == {0, 1, 2, 3}     # mais rápida que andando
    tia.posicao = pygame.Vector2(jogo.jogador.posicao) + (30, 0)
    for _ in range(int(TiaDaCantina.INTERVALO_DO_GIRO * 30) * 2 + 5):            # três conchadas, não quatro
        tia.perseguir(1 / 30, jogo)
        jogo.jogador.invencivel = 0
    assert jogo.jogador.vida_maxima - jogo.jogador.vida == pytest.approx(3 * TiaDaCantina.DANO_DO_GIRO)
    assert any(p.arte == "concha" for p in novas(jogo, ProjetilTematico))
    for _ in range(int(TiaDaCantina.DURACAO_DO_GIRO * 30)):
        tia.perseguir(1 / 30, jogo)
    assert not tia.girando


# ---- Lobo-Guará

from jogo.inimigos.mini_chefes import LoboGuara  # noqa: E402
from jogo.projeteis.do_campus import MordidaDaToca  # noqa: E402


def quadro_de(chefe):
    return chefe.animador.animacao.quadros.index(chefe.animador.quadro_atual)


def test_lobo_mira_agachado_e_da_o_bote_quadro_a_quadro(jogo_limpo):
    jogo = jogo_limpo()
    lobo = criar(jogo, "lobo_guara")
    lobo.ataques = 1
    lobo.atacar(jogo)
    assert lobo.arrancada.ativa and lobo.escolher_animacao() == "bote"
    vistos = []
    while lobo.arrancada.mirando:
        lobo.perseguir(1 / 30, jogo)
        vistos.append(quadro_de(lobo))
    while lobo.arrancada.correndo:
        lobo.perseguir(1 / 30, jogo)
        vistos.append(quadro_de(lobo))
    assert vistos[0] == 0 and {1, 2, 3} <= set(vistos)


def test_lobo_uiva_parado_e_so_depois_da_o_bote(jogo_limpo):
    jogo = jogo_limpo()
    lobo = criar(jogo, "lobo_guara")
    lobo.ataques = LoboGuara.REFORCO_A_CADA
    lobo.atacar(jogo)
    assert lobo.escolher_animacao() == "uivar" and not lobo.arrancada.ativa
    lobo.cumprir_agenda(LoboGuara.TEMPO_DO_UIVO, jogo)
    assert lobo.arrancada.ativa


def test_lobo_na_lua_cheia_cava_some_e_sai_do_chao_mordendo(jogo_limpo):
    jogo = jogo_limpo()
    lobo = criar(jogo, "lobo_guara", distancia=500)
    na_segunda_fase(jogo, lobo)
    lobo.ataques = 2
    lobo.atacar(jogo)
    assert lobo.escolher_animacao() == "cavar"
    parado = pygame.Vector2(lobo.posicao)
    for _ in range(int(LoboGuara.TEMPO_CAVANDO * 30) + 1):
        lobo.perseguir(1 / 30, jogo)
    assert lobo.posicao == parado and lobo.escondido                # cava parado e some
    vida = lobo.vida
    assert lobo.invulneravel and not jogo.causar_dano(lobo, 500) and lobo.vida == vida
    jogo.jogador.posicao = pygame.Vector2(lobo.posicao)
    lobo.tocar_jogador(jogo)
    assert jogo.jogador.vida == jogo.jogador.vida_maxima            # debaixo da terra não encosta
    lobo.desenhar(pygame.Surface((1280, 720)), jogo.camera)
    jogo.jogador.posicao = parado + (300, 200)
    for _ in range(int(LoboGuara.TEMPO_ESCONDIDO * 30) + 1):
        lobo.perseguir(1 / 30, jogo)
    mordida, = novas(jogo, MordidaDaToca)
    assert lobo.posicao == jogo.jogador.posicao == mordida.posicao   # sai bem debaixo do aluno
    assert lobo.escolher_animacao() == "emergir" and not lobo.escondido
    for _ in range(int(LoboGuara.TEMPO_EMERGINDO * 30) + 1):
        lobo.perseguir(1 / 30, jogo)
    assert not lobo.invulneravel and lobo.escolher_animacao() == "andar"


def test_mordida_da_toca_avisa_e_morde_quem_ficou_em_cima(jogo_limpo):
    jogo = jogo_limpo()
    jogo.adicionar(MordidaDaToca(jogo.jogador.posicao, 90, 22))
    for _ in range(int(MordidaDaToca.AVISO * 30) - 1):
        jogo.atualizar(1 / 30)
    assert jogo.jogador.vida == jogo.jogador.vida_maxima
    for _ in range(3):
        jogo.atualizar(1 / 30)
    assert jogo.jogador.vida == jogo.jogador.vida_maxima - 22


# ---- Vigilante

from jogo.inimigos.mini_chefes import BatGancho, Vigilante  # noqa: E402


def test_vigilante_aponta_a_lanterna_enquanto_mira_e_corre_de_capa(jogo_limpo):
    jogo = jogo_limpo()
    vigilante = criar(jogo, "vigilante")
    vigilante.ataques = 1
    vigilante.atacar(jogo)
    vistos = []
    while vigilante.arrancada.mirando:
        vigilante.perseguir(1 / 30, jogo)
        if vigilante.arrancada.mirando:
            assert vigilante.escolher_animacao() == "lanterna"
            vistos.append(quadro_de(vigilante))
    assert vistos == sorted(vistos) and vistos[0] == 0 and vistos[-1] == 3
    vigilante.perseguir(1 / 30, jogo)
    assert vigilante.arrancada.correndo and vigilante.escolher_animacao() == "arrancada"


def preparar_gancho(jogo, distancia=300):
    vigilante = criar(jogo, "vigilante", distancia=distancia)
    na_segunda_fase(jogo, vigilante)
    vigilante.ataques = 2
    vigilante.atacar(jogo)
    assert vigilante.gancho.ativo and vigilante.escolher_animacao() == "gancho"
    return vigilante


def ate_o_gancho_chegar(jogo, vigilante):
    while vigilante.gancho.etapa in ("mirando", "voando"):
        vigilante.mover(1 / 30, jogo)


def test_gancho_fisga_puxa_o_aluno_e_vem_a_voadora(jogo_limpo):
    jogo = jogo_limpo()
    vigilante = preparar_gancho(jogo)
    ate_o_gancho_chegar(jogo, vigilante)
    assert vigilante.gancho.etapa == "puxando"
    longe = jogo.jogador.posicao.distance_to(vigilante.posicao)
    while vigilante.gancho.ativo:
        vigilante.mover(1 / 30, jogo)
    assert jogo.jogador.posicao.distance_to(vigilante.posicao) < min(longe, Vigilante.ALCANCE_DA_VOADORA)
    assert vigilante.escolher_animacao() == "voadora"
    jogo.jogador.invencivel = 0
    vida = jogo.jogador.vida
    vigilante.cumprir_agenda(Vigilante.TEMPO_DA_VOADORA, jogo)
    assert vida - jogo.jogador.vida == pytest.approx(Vigilante.DANO_DA_VOADORA)


def test_quem_sai_da_linha_do_gancho_escapa(jogo_limpo):
    jogo = jogo_limpo()
    vigilante = preparar_gancho(jogo)
    while vigilante.gancho.etapa == "mirando":
        vigilante.mover(1 / 30, jogo)
    jogo.jogador.posicao += (0, 200)                          # saiu de onde o gancho foi mirado
    ate_o_gancho_chegar(jogo, vigilante)
    assert not vigilante.gancho.ativo and not vigilante.encenando
    assert jogo.jogador.vida == jogo.jogador.vida_maxima


def test_quem_rola_na_hora_escapa_do_gancho(jogo_limpo):
    jogo = jogo_limpo()
    vigilante = preparar_gancho(jogo)
    while vigilante.gancho.etapa == "mirando" or vigilante.gancho.falta_para_chegar > 2 / 30:
        vigilante.mover(1 / 30, jogo)
    jogo.jogador.direcao_movimento = pygame.Vector2(0, 1)
    assert jogo.jogador.rolar()
    ate_o_gancho_chegar(jogo, vigilante)
    assert not vigilante.gancho.ativo and not vigilante.encenando


def test_gancho_tem_alcance(jogo_limpo):
    jogo = jogo_limpo()
    vigilante = preparar_gancho(jogo, distancia=BatGancho.ALCANCE + 300)
    assert vigilante.gancho.alvo.distance_to(vigilante.posicao) == pytest.approx(BatGancho.ALCANCE)



# ---- Bibliotecária

from jogo.inimigos.mini_chefes import Bibliotecaria  # noqa: E402
from jogo.projeteis.do_campus import Multa, Silencio  # noqa: E402


def test_bibliotecaria_anota_no_caderno_e_as_multas_saem_quando_ela_fecha(jogo_limpo):
    jogo = jogo_limpo()
    bibliotecaria = criar(jogo, "bibliotecaria")
    bibliotecaria.ataques = 1
    bibliotecaria.atacar(jogo)
    assert bibliotecaria.escolher_animacao() == "anotar" and not novas(jogo, Multa)
    bibliotecaria.cumprir_agenda(Bibliotecaria.SAIDA_DAS_MULTAS, jogo)
    assert len(novas(jogo, Multa)) == Bibliotecaria.MULTAS


def test_bibliotecaria_arremessa_o_livro_de_tres_em_tres(jogo_limpo):
    jogo = jogo_limpo()
    bibliotecaria = criar(jogo, "bibliotecaria")
    bibliotecaria.ataques = 3
    bibliotecaria.atacar(jogo)
    assert bibliotecaria.escolher_animacao() == "arremessar"
    bibliotecaria.cumprir_agenda(Bibliotecaria.SAIDA_DO_LIVRO, jogo)
    assert {p.arte for p in novas(jogo, ProjetilTematico)} >= {"livro", "multa"}


def test_shhh_da_bibliotecaria_deixa_as_armas_lentas_de_quem_ficou_perto(jogo_limpo):
    jogo = jogo_limpo()
    bibliotecaria = criar(jogo, "bibliotecaria", distancia=120)
    na_segunda_fase(jogo, bibliotecaria)
    normal = jogo.jogador.multiplicador_recarga
    bibliotecaria.ataques = 2
    bibliotecaria.atacar(jogo)
    silencio, = novas(jogo, Silencio)
    assert bibliotecaria.escolher_animacao() == "shhh" and silencio.posicao == bibliotecaria.posicao
    for _ in range(int(Silencio.AVISO * 30) + 2):
        jogo.atualizar(1 / 30)
    assert jogo.jogador.tem_bonus("silencio")
    assert jogo.jogador.multiplicador_recarga == pytest.approx(normal * Silencio.LENTIDAO)


# ---- Técnico do Laboratório

from jogo.inimigos.mini_chefes import TecnicoDoLaboratorio  # noqa: E402
from jogo.projeteis.do_campus import OndaDeChoque  # noqa: E402


def test_tecnico_arremessa_a_seringa_no_quadro_do_arremesso(jogo_limpo):
    jogo = jogo_limpo()
    tecnico = criar(jogo, "tecnico_do_laboratorio")
    tecnico.ataques = 1
    tecnico.atacar(jogo)
    assert tecnico.escolher_animacao() == "arremessar" and not novas(jogo, ProjetilTematico)
    tecnico.cumprir_agenda(TecnicoDoLaboratorio.SAIDA_DA_SERINGA, jogo)
    assert {p.arte for p in novas(jogo, ProjetilTematico)} == {"seringa"}


def test_furia_do_tecnico_e_a_segunda_fase_e_nao_passa_quando_ele_regenera(jogo_limpo):
    jogo = jogo_limpo()
    tecnico = criar(jogo, "tecnico_do_laboratorio")
    assert not tecnico.em_furia and tecnico.escolher_animacao() == "andar"
    na_segunda_fase(jogo, tecnico)
    assert tecnico.em_furia and tecnico.escolher_animacao() == "andar_furia"
    tecnico.vida = tecnico.vida_maxima
    tecnico.mover(1 / 30, jogo)
    assert tecnico.em_furia


def test_tecnico_em_furia_soca_o_chao_em_volta_dele(jogo_limpo):
    jogo = jogo_limpo()
    tecnico = criar(jogo, "tecnico_do_laboratorio", distancia=100)
    na_segunda_fase(jogo, tecnico)
    tecnico.ataques = 3
    tecnico.atacar(jogo)
    onda, = novas(jogo, OndaDeChoque)
    assert tecnico.escolher_animacao() == "socar_chao" and onda.posicao == tecnico.posicao
    assert onda.raio == TecnicoDoLaboratorio.RAIO_DA_PANCADA
    for _ in range(int(OndaDeChoque.AVISO * 30) + 2):
        jogo.atualizar(1 / 30)
    assert jogo.jogador.vida < jogo.jogador.vida_maxima


# ---- Reitor

from jogo.inimigos.mini_chefes import Reitor  # noqa: E402
from jogo.projeteis.do_campus import ChegadaDoCeia  # noqa: E402
from jogo.projeteis.tematicos import Carimbada  # noqa: E402


def test_reitor_carimba_parado_e_os_oficios_saem_quando_o_carimbo_bate(jogo_limpo):
    jogo = jogo_limpo()
    reitor = criar(jogo, "reitor")
    reitor.ataques = 1
    reitor.atacar(jogo)
    assert reitor.escolher_animacao() == "carimbar" and len(novas(jogo, Carimbada)) == 1
    assert not any(p.arte == "oficio" for p in novas(jogo, ProjetilTematico))
    reitor.cumprir_agenda(Reitor.SAIDA_DOS_OFICIOS, jogo)
    assert sum(p.arte == "oficio" for p in novas(jogo, ProjetilTematico)) == 16


def test_reitor_joga_emblemas_da_ufj_a_distancia(jogo_limpo):
    jogo = jogo_limpo()
    reitor = criar(jogo, "reitor")
    reitor.ataques = 2
    reitor.atacar(jogo)
    assert "logo_ufj" in {p.arte for p in novas(jogo, ProjetilTematico)} and arte_existe("logo_ufj")


def test_reitor_na_segunda_fase_apresenta_o_projeto_e_o_ceia_cai_do_ceu(jogo_limpo):
    jogo = jogo_limpo()
    reitor = criar(jogo, "reitor")
    na_segunda_fase(jogo, reitor)
    reitor.ataques = 2
    reitor.atacar(jogo)
    assert reitor.escolher_animacao() == "apresentar" and not novas(jogo, ChegadaDoCeia)
    reitor.cumprir_agenda(Reitor.SAIDA_DAS_PLACAS, jogo)
    placas = novas(jogo, ChegadaDoCeia)
    assert len(placas) == Reitor.PLACAS and any(p.posicao == jogo.jogador.posicao for p in placas)
    assert {p.arte for p in novas(jogo, ProjetilTematico)} == {"ceia_icone", "logo_ufj"}
    assert arte_existe("ceia_logo") and arte_existe("ceia_icone")


# ---- Loira da Odontologia

from jogo.inimigos.mini_chefes import LoiraDaOdontologia  # noqa: E402
from jogo.projeteis.do_campus import VeiculoDesgovernado  # noqa: E402


def test_loira_joga_o_cabelo_e_a_turma_chega_depois(jogo_limpo):
    jogo = jogo_limpo()
    loira = criar(jogo, "loira_da_odontologia")
    loira.ataques = 1
    loira.atacar(jogo)
    loirinha = FabricaDeInimigos.classe("loirinha")
    assert loira.escolher_animacao() == "chamar" and not novas(jogo, loirinha)
    loira.cumprir_agenda(LoiraDaOdontologia.SAIDA_DA_TURMA, jogo)
    assert len(novas(jogo, loirinha)) == LoiraDaOdontologia.LACAIOS_POR_CHAMADA


def test_loira_aperta_a_chave_e_os_hb20_vem(jogo_limpo):
    jogo = jogo_limpo()
    loira = criar(jogo, "loira_da_odontologia")
    loira.ataques = 2
    loira.atacar(jogo)
    assert loira.escolher_animacao() == "chave" and novas(jogo, VeiculoDesgovernado)


def test_loira_com_a_broca_atravessa_o_aluno_uma_vez_so(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.vida_maxima = jogo.jogador.vida = 10 ** 6
    loira = criar(jogo, "loira_da_odontologia", distancia=250)
    na_segunda_fase(jogo, loira)
    loira.ataques = 2
    loira.atacar(jogo)
    assert loira.arrancada.ativa and loira.escolher_animacao() == "broca"
    while loira.arrancada.ativa:
        loira.perseguir(1 / 30, jogo)
        jogo.jogador.invencivel = 0
    assert jogo.jogador.vida_maxima - jogo.jogador.vida == pytest.approx(LoiraDaOdontologia.DANO_DA_BROCA)



# ---- Agroboy

from jogo.inimigos.mini_chefes import Agroboy  # noqa: E402


def test_agroboy_faz_chover_dinheiro_no_quadro_do_arremesso(jogo_limpo):
    jogo = jogo_limpo()
    agroboy = criar(jogo, "agroboy")
    agroboy.ataques = 1
    agroboy.atacar(jogo)
    assert agroboy.escolher_animacao() == "dinheiro" and not novas(jogo, ProjetilTematico)
    agroboy.cumprir_agenda(Agroboy.SAIDA_DO_DINHEIRO, jogo)
    assert "dinheiro" in {p.arte for p in novas(jogo, ProjetilTematico)}


def test_agroboy_no_rodeio_laca_o_aluno_e_o_touro_arranca(jogo_limpo):
    jogo = jogo_limpo()
    agroboy = criar(jogo, "agroboy", distancia=300)
    na_segunda_fase(jogo, agroboy)
    assert agroboy.escolher_animacao() == "andar_touro"
    assert agroboy.velocidade_atual > agroboy.velocidade
    agroboy.ataques = 2
    agroboy.atacar(jogo)
    assert agroboy.laco.ativo and agroboy.escolher_animacao() == "laco"
    longe = jogo.jogador.posicao.distance_to(agroboy.posicao)
    for _ in range(90):
        agroboy.perseguir(1 / 30, jogo)
        if agroboy.arrancada.ativa:
            break
    assert agroboy.arrancada.ativa and jogo.jogador.posicao.distance_to(agroboy.posicao) < longe
    assert agroboy.escolher_animacao() == "andar_touro"


def test_no_touro_o_encostao_doi_mais(jogo_limpo):
    jogo = jogo_limpo()
    agroboy = criar(jogo, "agroboy")
    antes = agroboy.dano_de_contato
    na_segunda_fase(jogo, agroboy)
    assert agroboy.dano_de_contato == pytest.approx(antes * Agroboy.ENCOSTAO_NO_TOURO)


# ---- Grão-Mestre do Culto

from jogo.inimigos.mini_chefes import GraoMestreDoCulto  # noqa: E402
from jogo.projeteis.do_campus import ColunaDeFogo  # noqa: E402


def test_culto_faz_o_ritual_parado_quando_chama_os_cultistas(jogo_limpo):
    jogo = jogo_limpo()
    culto = criar(jogo, "grao_mestre_do_culto")
    culto.ataques = GraoMestreDoCulto.REFORCO_A_CADA - 1
    culto._espera_ataque = 0
    culto.mover(1 / 30, jogo)
    assert culto.escolher_animacao() == "ritual"
    cultista = FabricaDeInimigos.classe("cultista")
    assert novas(jogo, cultista)


def test_culto_ascende_com_mais_bracos_e_colunas_de_fogo_no_aluno(jogo_limpo):
    jogo = jogo_limpo()
    culto = criar(jogo, "grao_mestre_do_culto")
    culto.ataques = 1
    culto.atacar(jogo)
    tres = len(novas(jogo, ProjetilTematico))
    assert tres == GraoMestreDoCulto.BRACOS
    na_segunda_fase(jogo, culto)
    assert culto.escolher_animacao() == "andar_ascensao"
    for vez in range(1, GraoMestreDoCulto.COLUNA_A_CADA + 1):
        culto.ataques = vez
        culto.atacar(jogo)
    assert len(novas(jogo, ProjetilTematico)) - tres >= GraoMestreDoCulto.BRACOS_ASCENDIDO
    coluna, = novas(jogo, ColunaDeFogo)
    assert coluna.posicao == jogo.jogador.posicao


# ---- Gótica Trevosa

from jogo.inimigos.mini_chefes import GoticaTrevosa  # noqa: E402


def test_gotica_vira_morcegos_e_so_depois_aparece_perto_do_aluno(jogo_limpo):
    jogo = jogo_limpo()
    gotica = criar(jogo, "gotica_trevosa", distancia=600)
    gotica.ataques = 2
    gotica.atacar(jogo)
    assert gotica.escolher_animacao() == "sumir"
    assert gotica.posicao.distance_to(jogo.jogador.posicao) > 500
    gotica.cumprir_agenda(GoticaTrevosa.TEMPO_SUMINDO, jogo)
    perto = gotica.posicao.distance_to(jogo.jogador.posicao)
    assert perto == pytest.approx(GoticaTrevosa.DISTANCIA_DO_SUSTO, abs=40)


def test_vodu_da_gotica_acerta_onde_o_aluno_estiver_mas_quem_rola_escapa(jogo_limpo):
    jogo = jogo_limpo()
    gotica = criar(jogo, "gotica_trevosa", distancia=700)
    na_segunda_fase(jogo, gotica)
    gotica.ataques = 3
    gotica.atacar(jogo)
    assert gotica.escolher_animacao() == "vodu"
    assert any(m.arte == "caveira" and m.dono is jogo.jogador for m in novas(jogo, Marca))   # o aviso em cima dele
    vida = jogo.jogador.vida
    gotica.cumprir_agenda(GoticaTrevosa.AGULHADA, jogo)
    assert vida - jogo.jogador.vida == pytest.approx(GoticaTrevosa.DANO_DO_VODU)
    jogo.jogador.invencivel = 0
    gotica.ataques = 5
    gotica.atacar(jogo)
    jogo.jogador.direcao_movimento = pygame.Vector2(1, 0)
    jogo.jogador.rolar()
    vida = jogo.jogador.vida
    gotica.cumprir_agenda(GoticaTrevosa.AGULHADA, jogo)
    assert jogo.jogador.vida == vida


# ---- ET de Varginha

from jogo.inimigos.mini_chefes import ETDeVarginha  # noqa: E402
from jogo.projeteis.do_campus import FeixeDeAbducao  # noqa: E402


def test_et_faz_telepatia_ao_abrir_o_feixe(jogo_limpo):
    jogo = jogo_limpo()
    et = criar(jogo, "et_de_varginha")
    et.ataques = 1
    et.atacar(jogo)
    assert et.escolher_animacao() == "telepatia" and len(novas(jogo, FeixeDeAbducao)) == 1


def test_et_no_disco_abre_tres_feixes_e_o_raio_dele_puxa_o_aluno(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.vida_maxima = jogo.jogador.vida = 10 ** 6
    et = criar(jogo, "et_de_varginha", distancia=600)
    na_segunda_fase(jogo, et)
    assert et.escolher_animacao() == "andar_disco"
    et.ataques = 1
    et.atacar(jogo)
    et.atualizar(1 / 30, jogo)
    assert et.escolher_animacao() == "andar_disco" and et.animador.atual == "andar_disco"   # não desce do disco
    assert len(novas(jogo, FeixeDeAbducao)) == ETDeVarginha.FEIXES_NO_DISCO
    et.posicao = jogo.jogador.posicao + (ETDeVarginha.ALCANCE_DO_RAIO - 30, 0)
    longe = jogo.jogador.posicao.distance_to(et.posicao)
    for _ in range(20):
        et.puxar_com_o_raio(1 / 30, jogo)
        jogo.jogador.invencivel = 0
    assert jogo.jogador.posicao.distance_to(et.posicao) < longe
    assert jogo.jogador.vida < jogo.jogador.vida_maxima
    jogo.jogador.posicao = et.posicao + (ETDeVarginha.ALCANCE_DO_RAIO + 200, 0)
    antes = pygame.Vector2(jogo.jogador.posicao)
    et.puxar_com_o_raio(1 / 30, jogo)
    assert jogo.jogador.posicao == antes                       # fora do raio, nada


# ---- Professores (chefes das provas)

PROFESSORES = ("chefe_calculo", "chefe_arquitetura_ed", "chefe_td_poo")


@pytest.mark.parametrize("nome", PROFESSORES)
def test_professor_tem_animacao_de_ataque_com_os_pes_no_lugar(nome):
    animacoes = Recursos.animacoes(FabricaDeInimigos.classe(nome).PASTA_SPRITE)
    assert {"andar", "parado", "atacar"} <= set(animacoes)
    andar, atacar = animacoes["andar"].quadros[0], animacoes["atacar"].quadros[0]
    assert abs((pes(atacar) - atacar.get_height() / 2) - (pes(andar) - andar.get_height() / 2)) <= 3


@pytest.mark.parametrize("nome", PROFESSORES)
def test_professor_toca_o_ataque_do_comeco_ao_fim_antes_do_golpe(jogo_limpo, nome):
    """O preparo do golpe (Chefe.preparando) dura a tira inteira: todos os quadros aparecem antes de o ataque sair."""
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    chefe = criar(jogo, nome, distancia=200)
    chefe._espera_ataque = 0
    chefe.atualizar(1 / 30, jogo)
    assert chefe.escolher_animacao() == "atacar" and chefe._indice == 0
    vistos = set()
    for _ in range(round(chefe.duracao_do_preparo * 30) + 1):
        chefe.atualizar(1 / 30, jogo)
        if chefe.animador.atual == "atacar":
            vistos.add(chefe.animador.animacao.quadros.index(chefe.animador.quadro_atual))
    assert vistos == {0, 1, 2, 3} and chefe._indice == 1           # o golpe saiu no fim do preparo
    for _ in range(5):
        chefe.atualizar(1 / 30, jogo)
    assert chefe.escolher_animacao() != "atacar"
