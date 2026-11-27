"""Ataques com a cara de cada chefe e mini-chefe: objetos desenhados, golpes no chão, poças e a turma da Loira."""
import pygame
import pytest

from jogo.inimigos.acoes_do_chefe import RaiosPelosOlhos
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.lacaios_do_campus import LacaioDoCampus
from jogo.inimigos.materias.arquitetura import ArquiteturaDeComputadores
from jogo.inimigos.materias.calculo import CalculoI, CalculoII
from jogo.inimigos.materias.estrutura_de_dados import EstruturaDeDadosEmC
from jogo.inimigos.materias.poo import ProgramacaoOrientadaAObjetos
from jogo.inimigos.materias.transformacao_digital import TransformacaoDigital
from jogo.inimigos.mini_chefes import MINI_CHEFES
from jogo.nucleo.camera import Camera
from jogo.projeteis.do_campus import FeixeDeAbducao, Multa
from jogo.projeteis.projeteis import ProjetilDaMateria
from jogo.projeteis.tematicos import (Bumerangue, Carimbada, FrascoDeAcido, GolpeNoChao, Marca, PanelaoDeSopa, Poca,
                                      ProjetilTematico, arte_existe)

MATERIAS = (CalculoI, CalculoII, ArquiteturaDeComputadores, EstruturaDeDadosEmC, TransformacaoDigital,
            ProgramacaoOrientadaAObjetos)


def novas(jogo, classe):
    return [e for e in jogo._novas + jogo.entidades if isinstance(e, classe) and e.ativo]


def invocar(jogo, nome, distancia=300):
    chefe = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + (distancia, 0))
    jogo.adicionar(chefe)
    return chefe


def atacar(jogo, chefe, vezes):
    """Ataca e deixa passar o tempo da animação: a bandeja sai da mão no quadro do arremesso."""
    for _ in range(vezes):
        chefe.ataques += 1
        chefe.atacar(jogo)
        chefe.cumprir_agenda(5.0, jogo)


def artes_lancadas(jogo):
    return {p.arte for p in novas(jogo, ProjetilTematico)}


def camera():
    return Camera(1280, 720, pygame.Rect(-5000, -5000, 10000, 10000))


def tela():
    return pygame.Surface((1280, 720), pygame.SRCALPHA)


# ---- o projétil desenhado

def test_projetil_tematico_usa_a_arte_e_sem_ela_volta_para_o_simbolo():
    com = ProjetilTematico((0, 0), (100, 0), 5, "o", (255, 150, 70), arte="bandeja")
    sem = ProjetilTematico((0, 0), (100, 0), 5, "dx", (255, 150, 70), arte="arte_que_nao_existe")
    assert com.arte == "bandeja" and sem.arte is None
    assert isinstance(com, ProjetilDaMateria) and com.grupo == "projetil_inimigo"
    visao = camera()
    desenho, simbolo = tela(), tela()
    com.desenhar(desenho, visao)
    sem.desenhar(simbolo, visao)
    assert desenho.get_bounding_rect().width > 0 and simbolo.get_bounding_rect().width > 0


def test_cada_arte_voa_do_seu_jeito():
    bandeja = ProjetilTematico((0, 0), (0, 100), 5, "o", (0, 0, 0), arte="bandeja")
    seringa = ProjetilTematico((0, 0), (0, 100), 5, "o", (0, 0, 0), arte="seringa")
    bandeja.tempo = seringa.tempo = 0.5
    assert bandeja.angulo_desenho() == pytest.approx(-0.5 * ProjetilTematico.GIRAM["bandeja"])      # gira
    assert seringa.angulo_desenho() == pytest.approx(-90)                                           # aponta


def test_projetil_tematico_fere_o_aluno_como_qualquer_projetil_inimigo(jogo_limpo):
    jogo = jogo_limpo()
    jogo.adicionar(ProjetilTematico(jogo.jogador.posicao, (0, 0), 7, "o", (255, 150, 70), arte="bandeja"))
    jogo.atualizar(1 / 30)
    assert jogo.jogador.vida == jogo.jogador.vida_maxima - 7


def test_bumerangue_vai_e_volta():
    volta = Bumerangue((0, 0), (400, 0), 5, "<", (250, 220, 80), arte="batarangue")
    mais_longe = 0
    for _ in range(int(Bumerangue.IDA * 2 * 60)):
        volta.tempo += 1 / 60
        volta.mover(1 / 60)
        mais_longe = max(mais_longe, volta.posicao.x)
    assert mais_longe > 150 and abs(volta.posicao.x) < 20


# ---- as matérias dos professores

@pytest.mark.parametrize("materia", MATERIAS)
def test_toda_materia_desenha_os_proprios_simbolos(materia):
    assert materia.SIMBOLO in materia.ARTES
    assert all(arte_existe(arte) for arte in materia.ARTES.values())
    assert arte_existe(materia.ARTE_DA_CHAMADA)
    projetil = materia().criar_projetil((0, 0), (10, 0), 5, materia.SIMBOLO)
    assert isinstance(projetil, ProjetilTematico) and projetil.arte == materia.ARTES[materia.SIMBOLO]
    assert projetil.cor == materia.COR


def test_materia_sem_desenho_para_o_simbolo_usa_a_bolinha():
    projetil = CalculoI().criar_projetil((0, 0), (10, 0), 5, "símbolo novo")
    assert projetil.arte is None and projetil.simbolo == "símbolo novo"


def test_poo_mostra_o_cadeado_enquanto_esta_encapsulada(jogo_limpo):
    jogo = jogo_limpo()
    chefe = invocar(jogo, "chefe_td_poo")
    poo = chefe.materias[1]
    poo.encapsulamento(chefe, jogo)
    cadeado = [m for m in novas(jogo, Marca) if m.arte == "cadeado"]
    assert len(cadeado) == 1 and cadeado[0].dono is chefe and cadeado[0].duracao == poo.DURACAO_ESCUDO


def test_chamada_marca_cada_lacaio_com_o_desenho_da_materia(jogo_limpo):
    jogo = jogo_limpo()
    chefe = invocar(jogo, "chefe_calculo")
    chefe.materia.chamada(chefe, jogo, 5)
    assert sum(m.arte == CalculoI.ARTE_DA_CHAMADA for m in novas(jogo, Marca)) == 5


# ---- os mini-chefes

@pytest.mark.parametrize("nome", MINI_CHEFES)
def test_nenhum_mini_chefe_ataca_com_bolinha_generica(jogo_limpo, nome):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    chefe = invocar(jogo, nome)
    atacar(jogo, chefe, 6)
    projeteis = novas(jogo, ProjetilDaMateria)
    assert all(isinstance(p, ProjetilTematico) and p.arte for p in projeteis)
    quadro = tela()
    for entidade in jogo._novas:                               # tudo o que ele lançou sabe se desenhar
        entidade.desenhar(quadro, jogo.camera)


def test_tia_da_cantina_arremessa_bandeja_comida_e_o_panelao(jogo_limpo):
    jogo = jogo_limpo()
    tia = invocar(jogo, "tia_da_cantina")
    atacar(jogo, tia, 3)
    assert {"bandeja", "prato_feito", "frigideira", "concha", "colher_de_pau"} <= artes_lancadas(jogo)
    paneloes = novas(jogo, PanelaoDeSopa)
    assert len(paneloes) == 1 and paneloes[0].posicao == jogo.jogador.posicao


def test_panelao_cai_fere_quem_ficou_embaixo_e_deixa_poca_de_sopa(jogo_limpo):
    jogo = jogo_limpo()
    jogo.adicionar(PanelaoDeSopa(jogo.jogador.posicao, 100, 10))
    for _ in range(int(PanelaoDeSopa.AVISO * 30) - 2):
        jogo.atualizar(1 / 30)
    assert jogo.jogador.vida == jogo.jogador.vida_maxima and not novas(jogo, Poca)       # ainda é só o aviso
    for _ in range(6):
        jogo.atualizar(1 / 30)
    assert jogo.jogador.vida < jogo.jogador.vida_maxima
    poca, = novas(jogo, Poca)
    assert poca.arte == "poca_de_sopa" and arte_existe(poca.arte)


def test_poca_queima_quem_pisa_de_tempos_em_tempos_e_seca(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.vida_maxima = jogo.jogador.vida = 10 ** 6
    longe = Poca(jogo.jogador.posicao + (500, 0), 80, 1000, "poca_de_acido", (120, 235, 70), duracao=1.0)
    perto = Poca(jogo.jogador.posicao, 80, 3, "poca_de_sopa", (255, 140, 40), duracao=1.0)
    jogo.adicionar(longe)
    jogo.adicionar(perto)
    jogo.atualizar(1 / 30)
    assert jogo.jogador.vida == 10 ** 6 - 3
    jogo.atualizar(1 / 30)
    assert jogo.jogador.vida == 10 ** 6 - 3                    # não queima a cada quadro
    for _ in range(40):
        jogo.atualizar(1 / 30)
    assert not perto.ativo and not longe.ativo


def test_loira_da_odontologia_invoca_varias_loirinhas_ate_o_limite(jogo_limpo):
    jogo = jogo_limpo()
    loira = invocar(jogo, "loira_da_odontologia")
    loira.ao_chegar(jogo)
    loirinhas = novas(jogo, FabricaDeInimigos.classe("loirinha"))
    assert len(loirinhas) == loira.LACAIOS_NA_CHEGADA >= 6
    assert all(isinstance(l, LacaioDoCampus) and len(l.animador.animacao.quadros) == 8 for l in loirinhas)
    assert loirinhas[0].animador.quadro_atual.get_height() < loira.animador.quadro_atual.get_height()   # miniaturas
    atacar(jogo, loira, 9)
    assert len(novas(jogo, FabricaDeInimigos.classe("loirinha"))) == loira.TURMA_MAXIMA
    assert {"escova", "pasta_de_dente", "espelhinho"} <= artes_lancadas(jogo)
    for loirinha in loira.turma[:5]:                           # derrotadas abrem vaga na turma
        loirinha.remover()
    atacar(jogo, loira, 2)                                     # um ataque de HB20 e uma chamada de quatro
    assert len(novas(jogo, FabricaDeInimigos.classe("loirinha"))) == loira.TURMA_MAXIMA - 1


def test_vigilante_solta_batarangues_que_voltam(jogo_limpo):
    jogo = jogo_limpo()
    vigilante = invocar(jogo, "vigilante")
    atacar(jogo, vigilante, 2)
    batarangues = novas(jogo, Bumerangue)
    assert len(batarangues) == 3 and all(b.arte == "batarangue" for b in batarangues)
    assert vigilante.arrancada.ativa


def test_agroboy_joga_dinheiro_e_o_chapeu_volta(jogo_limpo):
    jogo = jogo_limpo()
    agroboy = invocar(jogo, "agroboy")
    atacar(jogo, agroboy, 2)
    assert {"dinheiro", "milho", "chapeu"} <= artes_lancadas(jogo)
    assert [b.arte for b in novas(jogo, Bumerangue)] == ["chapeu"]


def test_reitor_carimba_indeferido_onde_o_aluno_esta(jogo_limpo):
    jogo = jogo_limpo()
    reitor = invocar(jogo, "reitor")
    atacar(jogo, reitor, 2)
    assert {"oficio", "portaria", "logo_ufj"} <= artes_lancadas(jogo)
    carimbada, = novas(jogo, Carimbada)
    assert carimbada.posicao == jogo.jogador.posicao and arte_existe(Carimbada.ARTE_DA_MARCA)
    vida = jogo.jogador.vida
    for _ in range(40):
        carimbada.atualizar(1 / 30, jogo)
    assert jogo.jogador.vida < vida and not carimbada.ativo


def test_tecnico_arremessa_seringas_e_frasco_de_acido(jogo_limpo):
    jogo = jogo_limpo()
    tecnico = invocar(jogo, "tecnico_do_laboratorio")
    atacar(jogo, tecnico, 3)
    assert artes_lancadas(jogo) == {"seringa"}
    frasco, = novas(jogo, FrascoDeAcido)
    frasco.ao_cair(jogo)
    assert novas(jogo, Poca)[0].arte == "poca_de_acido"


def test_lobo_guara_deixa_rastro_de_garras_no_bote(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    lobo = invocar(jogo, "lobo_guara")
    atacar(jogo, lobo, 1)
    for _ in range(40):
        lobo.perseguir(1 / 60, jogo)
    marcas = [m.arte for m in novas(jogo, Marca)]
    assert marcas.count("garra") >= 3 and "poeira" in marcas


def test_gotica_some_e_aparece_em_nuvens_de_morcegos(jogo_limpo):
    jogo = jogo_limpo()
    gotica = invocar(jogo, "gotica_trevosa")
    atacar(jogo, gotica, 2)
    assert [m.arte for m in novas(jogo, Marca)].count("nuvem_de_morcegos") == 2
    assert artes_lancadas(jogo) == {"coracao_preto", "rosa_negra"}


def test_culto_e_bibliotecaria_lancam_os_proprios_objetos(jogo_limpo):
    jogo = jogo_limpo()
    atacar(jogo, invocar(jogo, "grao_mestre_do_culto"), 4)
    assert artes_lancadas(jogo) == {"chama_dourada", "adaga"}
    jogo = jogo_limpo()
    atacar(jogo, invocar(jogo, "bibliotecaria"), 3)
    assert artes_lancadas(jogo) == {"multa", "livro"}
    assert all(m.arte == "multa" for m in novas(jogo, Multa))


def test_feixe_de_abducao_e_um_golpe_no_chao_com_arte_propria(jogo_limpo):
    jogo = jogo_limpo()
    feixe = FeixeDeAbducao(jogo.jogador.posicao, 95, 10)
    assert isinstance(feixe, GolpeNoChao)
    assert all(arte_existe(a) for a in (feixe.ARTE_DO_ANEL, feixe.ARTE_DO_FEIXE, feixe.ARTE_DO_ABDUZIDO))
    visao = jogo.camera
    antes, depois = tela(), tela()
    feixe.desenhar(antes, visao)
    feixe.tempo, feixe.disparou = feixe.AVISO + 0.1, True
    feixe.desenhar(depois, visao)
    assert depois.get_bounding_rect().height > antes.get_bounding_rect().height      # a coluna de luz subiu


def test_mini_ovni_atira_laser(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    ovni = FabricaDeInimigos.criar("mini_ovni", jogo.jogador.posicao + (260, 0))
    for _ in range(100):
        ovni.mover(1 / 30, jogo)
    assert artes_lancadas(jogo) == {"laser"}


def test_marca_acompanha_o_dono_e_some(jogo_limpo):
    jogo = jogo_limpo()
    dono = invocar(jogo, "reitor")
    marca = Marca(dono.posicao - (0, 50), "cadeado", 50, duracao=0.3, dono=dono)
    jogo.adicionar(marca)
    dono.posicao += (100, 0)
    marca.atualizar(0.1, jogo)
    assert marca.posicao == dono.posicao - (0, 50) and marca.ativo
    marca.atualizar(0.3, jogo)
    assert not marca.ativo


# ---- raios pelos olhos do professor de ED

def chefe_de_ed(jogo):
    chefe = invocar(jogo, "chefe_arquitetura_ed")
    chefe.vida = 1
    chefe.receber_dano(10)                                     # Arquitetura cai, ED assume
    chefe.troca = 0
    return chefe


def test_ed_tem_raios_pelos_olhos_que_saem_da_altura_dos_olhos(jogo_limpo):
    jogo = jogo_limpo()
    chefe = chefe_de_ed(jogo)
    assert chefe.materia.visao_de_raio_laser in chefe.materia.ataques()
    chefe.materia.visao_de_raio_laser(chefe, jogo)
    raios = chefe.acao_atual
    assert isinstance(raios, RaiosPelosOlhos) and len(raios.feixes()) == 2
    topo = chefe.posicao.y - chefe.altura_sprite / 2
    for olho in chefe.olhos():
        assert topo < olho.y < topo + chefe.altura_sprite * 0.2      # na cabeça
    chefe.olhando_esquerda = False
    direita = [o.x for o in chefe.olhos()]
    chefe.olhando_esquerda = True
    assert [o.x - chefe.posicao.x for o in chefe.olhos()] == [chefe.posicao.x - x for x in direita]


def test_raios_nascem_exatamente_nos_olhos_em_qualquer_quadro(jogo_limpo):
    """O olho é medido no desenho de cada quadro: fica no rosto, colado na frente dele, e é dali que o feixe sai."""
    jogo = jogo_limpo()
    chefe = chefe_de_ed(jogo)
    chefe.olhando_esquerda = False
    for animacao in chefe.animador.animacoes.values():
        for quadro in animacao.quadros:
            x, y = chefe.olho_no_quadro(quadro)
            px, py = round(x + quadro.get_width() / 2), round(y + quadro.get_height() / 2)
            assert quadro.get_at((px, py)).a > 128                           # em cima do rosto, não no ar
            assert py - quadro.get_bounding_rect().top == chefe.ALTURA_DO_OLHO
            assert all(quadro.get_at((fx, py)).a <= 128 for fx in range(px + 5, quadro.get_width()))   # na frente
    chefe.materia.visao_de_raio_laser(chefe, jogo)
    assert [origem for origem, _ in chefe.acao_atual.feixes()] == chefe.olhos()


def test_raios_pelos_olhos_avisam_antes_e_ferem_quem_ficou_na_mira(jogo_limpo):
    jogo = jogo_limpo()
    chefe = chefe_de_ed(jogo)
    raios = RaiosPelosOlhos(chefe, 20)
    while not raios.disparando:
        assert jogo.jogador.vida == jogo.jogador.vida_maxima    # mirando e travando ninguém se machuca
        raios(1 / 60, jogo)
    assert raios(1 / 60, jogo) is False
    assert jogo.jogador.vida == jogo.jogador.vida_maxima - 20
    for _ in range(60):                                         # o mesmo disparo não fere duas vezes
        if raios(1 / 60, jogo):
            break
    assert jogo.jogador.vida == jogo.jogador.vida_maxima - 20


def test_quem_sai_da_linha_depois_da_trava_escapa_dos_raios(jogo_limpo):
    jogo = jogo_limpo()
    chefe = chefe_de_ed(jogo)
    raios = RaiosPelosOlhos(chefe, 20)
    while not raios.travado:
        raios(1 / 60, jogo)
    travada = pygame.Vector2(raios.direcao)
    jogo.jogador.posicao += travada.rotate(90) * 200           # desviou para o lado
    terminou = False
    for _ in range(120):
        terminou = raios(1 / 60, jogo)
        if terminou:
            break
    assert terminou and raios.direcao == travada
    assert jogo.jogador.vida == jogo.jogador.vida_maxima
    raios.tempo = raios.MIRA + raios.TRAVA                      # e o desenho dos feixes não quebra
    raios.desenhar_aviso(tela(), jogo.camera)
