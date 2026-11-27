"""O Leão do PROERD: o mascote da palestra, enorme e sério, com as cartilhas, a placa de DIGA NÃO, o rugido e os
malandros do fundão, que têm medo dele."""
import pygame
import pytest

from jogo.efeitos import TextoFlutuante
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.lacaios_do_campus import CaoFarejador, LacaioDoCampus, Malandro
from jogo.inimigos.mini_chefes import MINI_CHEFES, LeaoDoProerd, MiniChefe
from jogo.mapa import MapaUFJ
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.do_campus import PapelDoProerd, PlacaDigaNao, RugidoDoLeao
from jogo.projeteis.tematicos import GolpeNoChao, Marca, ProjetilTematico, arte_existe

ARTES = ("cartilha", "certificado", "placa_diga_nao", "diga_nao", "rugido", "medalha")


def novas(jogo, classe):
    return [e for e in jogo._novas + jogo.entidades if isinstance(e, classe) and e.ativo]


def invocar(jogo, distancia=300):
    leao = FabricaDeInimigos.criar("leao_do_proerd", jogo.jogador.posicao + (distancia, 0))
    jogo.adicionar(leao)
    return leao


def atacar(jogo, leao, vezes=1):
    for _ in range(vezes):
        leao.ataques += 1
        leao.atacar(jogo)


def test_leao_e_um_mini_chefe_registrado_na_fabrica_e_entra_no_sorteio():
    assert FabricaDeInimigos.classe("leao_do_proerd") is LeaoDoProerd
    assert issubclass(LeaoDoProerd, MiniChefe) and "leao_do_proerd" in MINI_CHEFES
    assert LeaoDoProerd.NOME == "Leão do PROERD" and LeaoDoProerd.ARTIGO == "Um" and LeaoDoProerd.GRITO


def test_leao_fica_no_auditorio_onde_da_a_palestra():
    mapa = MapaUFJ.carregar()
    if mapa is None:
        pytest.skip("sem o mapa da UFJ")
    assert LeaoDoProerd.LOCAL == "AUDITORIO" and mapa.local_de("AUDITORIO") is not None
    outros = [FabricaDeInimigos.classe(nome).LOCAL for nome in MINI_CHEFES if nome != "leao_do_proerd"]
    assert "AUDITORIO" not in outros                           # ninguém mais espera no mesmo lugar


@pytest.mark.parametrize("arte", ARTES)
def test_cada_ataque_do_leao_tem_o_proprio_desenho(arte):
    assert arte_existe(arte), arte


def test_leao_tem_folha_de_andar_rosto_ilustracao_e_malandro_desenhado():
    for caminho in ("sprites/leao_do_proerd/andar-8.png", "rostos/leao_do_proerd.png", "chefes/leao_do_proerd.png",
                    "sprites/malandro/andar-4.png"):
        assert (Recursos.pasta / caminho).is_file(), caminho


def test_leao_e_grande_e_musculoso(jogo_limpo):
    jogo = jogo_limpo()
    aluno = jogo.jogador.animador.quadro_atual.get_height()
    leao = invocar(jogo)
    assert leao.altura_sprite >= 1.8 * aluno and leao.raio > 2 * jogo.jogador.raio


def test_leao_chega_com_os_malandros_e_eles_sabem_de_quem_fugir(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo)
    leao.ao_chegar(jogo)
    malandros = novas(jogo, Malandro)
    assert len(malandros) == LeaoDoProerd.LACAIOS_NA_CHEGADA - LeaoDoProerd.CAES_NA_CHEGADA
    assert issubclass(Malandro, LacaioDoCampus)
    assert FabricaDeInimigos.classe("malandro") is Malandro
    assert all(m.temido is leao for m in malandros)


def test_malandro_sozinho_vem_para_cima_do_aluno(jogo_limpo):
    jogo = jogo_limpo()
    malandro = FabricaDeInimigos.criar("malandro", jogo.jogador.posicao + (300, 0))
    jogo.adicionar(malandro)
    antes = malandro.posicao.distance_to(jogo.jogador.posicao)
    for _ in range(20):
        jogo.atualizar(1 / 30)
    assert malandro.posicao.distance_to(jogo.jogador.posicao) < antes and not malandro.com_medo


def test_malandro_foge_do_leao_quando_ele_chega_perto_e_grita_uma_vez(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo, distancia=2000)
    malandro = FabricaDeInimigos.criar("malandro", jogo.jogador.posicao + (300, 0))
    malandro.temido = leao
    leao.posicao = malandro.posicao + (-100, 0)                # o leão entre ele e o aluno
    jogo.adicionar(malandro)
    jogo._incorporar_novas()
    antes = malandro.posicao.distance_to(leao.posicao)
    for _ in range(3):
        malandro.mover(1 / 30, jogo)
    assert malandro.com_medo and malandro.posicao.distance_to(leao.posicao) > antes
    assert len(novas(jogo, TextoFlutuante)) == 1               # "SUJOU!" uma vez só, não a cada quadro
    leao.posicao = malandro.posicao + (-900, 0)                # sai e volta para perto: não grita de novo logo
    malandro.mover(1 / 30, jogo)
    leao.posicao = malandro.posicao + (-100, 0)
    malandro.mover(1 / 30, jogo)
    assert len(novas(jogo, TextoFlutuante)) == 1
    malandro.mover(Malandro.INTERVALO_DO_GRITO, jogo)
    assert len(novas(jogo, TextoFlutuante)) == 2


def test_primeiro_ataque_arremessa_cartilhas_e_certificados_que_giram(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo)
    atacar(jogo, leao)
    papeis = novas(jogo, PapelDoProerd)
    assert len(papeis) == LeaoDoProerd.PAPEIS and {p.arte for p in papeis} == {"cartilha", "certificado"}
    assert all(isinstance(p, ProjetilTematico) and p.velocidade.x < 0 for p in papeis)      # na direção do aluno
    papel = papeis[0]
    papel.tempo = 0.5
    assert papel.angulo_desenho() == pytest.approx(-0.5 * PapelDoProerd.GIRAM[papel.arte])
    assert "cartilha" not in ProjetilTematico.GIRAM            # a classe que já existia continua como estava


def test_segundo_ataque_desce_a_placa_de_diga_nao_em_cima_do_aluno(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo)
    atacar(jogo, leao, 2)
    placa, = novas(jogo, PlacaDigaNao)
    assert isinstance(placa, GolpeNoChao) and placa.posicao == jogo.jogador.posicao
    assert placa.raio == LeaoDoProerd.RAIO_DA_PLACA and placa.TEXTO == "DIGA NÃO!"
    assert {p.arte for p in novas(jogo, PapelDoProerd)} >= {"medalha"}


def test_placa_avisa_antes_fere_quem_ficou_embaixo_e_deixa_o_carimbo(jogo_limpo):
    jogo = jogo_limpo()
    placa = PlacaDigaNao(jogo.jogador.posicao, 100, 10)
    jogo.adicionar(placa)
    for _ in range(int(PlacaDigaNao.AVISO * 30) - 2):
        jogo.atualizar(1 / 30)
    assert jogo.jogador.vida == jogo.jogador.vida_maxima
    for _ in range(4):
        jogo.atualizar(1 / 30)
    assert jogo.jogador.vida == jogo.jogador.vida_maxima - 10
    assert placa.ARTE_DO_GOLPE == "placa_diga_nao" and placa.ARTE_DA_MARCA == "diga_nao"
    placa.desenhar(pygame.Surface((1280, 720), pygame.SRCALPHA), jogo.camera)


def test_terceiro_ataque_e_o_rugido_o_leao_para_e_treme(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo, distancia=600)
    assert not leao.rugindo
    atacar(jogo, leao, 3)
    rugido, = novas(jogo, RugidoDoLeao)
    assert leao.rugindo and rugido.posicao == leao.posicao and rugido.raio == LeaoDoProerd.RAIO_DO_RUGIDO
    assert sum(m.arte == "rugido" for m in novas(jogo, Marca)) == 2
    parado = pygame.Vector2(leao.posicao)
    for _ in range(int(LeaoDoProerd.TEMPO_DO_RUGIDO * 30) - 3):
        leao.perseguir(1 / 30, jogo)
    assert leao.posicao == parado
    for _ in range(10):
        leao.perseguir(1 / 30, jogo)
    assert not leao.rugindo and leao.posicao != parado          # acabou o rugido: volta a perseguir


def test_rugido_paralisa_de_medo_quem_ficou_perto(jogo_limpo):
    jogo = jogo_limpo()
    heroi = jogo.jogador
    normal = heroi.velocidade
    jogo.adicionar(RugidoDoLeao(heroi.posicao + (50, 0), 190, 8))
    for _ in range(int(RugidoDoLeao.AVISO * 30) + 2):
        jogo.atualizar(1 / 30)
    assert heroi.vida == heroi.vida_maxima - 8
    assert heroi.tem_bonus("medo_do_leao")
    assert heroi.velocidade == pytest.approx(normal * RugidoDoLeao.LENTIDAO)
    for _ in range(int(RugidoDoLeao.DURACAO_DO_MEDO * 30) + 3):
        jogo.atualizar(1 / 30)
    assert not heroi.tem_bonus("medo_do_leao") and heroi.velocidade == pytest.approx(normal)


def test_quem_se_afasta_do_rugido_nao_sente_nada(jogo_limpo):
    jogo = jogo_limpo()
    heroi = jogo.jogador
    jogo.adicionar(RugidoDoLeao(heroi.posicao + (400, 0), 190, 8))
    for _ in range(int(RugidoDoLeao.AVISO * 30) + 2):
        jogo.atualizar(1 / 30)
    assert heroi.vida == heroi.vida_maxima and not heroi.tem_bonus("medo_do_leao")


def test_leao_e_os_malandros_lutam_e_se_desenham(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    leao = invocar(jogo)
    leao.ao_chegar(jogo)
    tela = pygame.Surface((1280, 720))
    for _ in range(240):
        jogo.atualizar(1 / 30)
        jogo.desenhar(tela)
    assert leao.ataques >= 3


# ---- os cães farejadores

def test_cao_farejador_e_um_lacaio_registrado_e_desenhado():
    assert FabricaDeInimigos.classe("cao_farejador") is CaoFarejador and issubclass(CaoFarejador, LacaioDoCampus)
    assert (Recursos.pasta / "sprites/cao_farejador/andar-4.png").is_file()


def test_leao_chega_com_malandros_e_caes(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo)
    leao.ao_chegar(jogo)
    caes, malandros = novas(jogo, CaoFarejador), novas(jogo, Malandro)
    assert len(caes) == LeaoDoProerd.CAES_NA_CHEGADA >= 2
    assert len(caes) + len(malandros) == LeaoDoProerd.LACAIOS_NA_CHEGADA
    assert leao.matilha == caes


def test_rugido_chama_mais_caes_ate_o_tamanho_da_matilha(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo)
    leao.ao_chegar(jogo)
    atacar(jogo, leao, 3)
    assert len(novas(jogo, CaoFarejador)) == LeaoDoProerd.CAES_NA_CHEGADA + LeaoDoProerd.CAES_POR_RUGIDO
    atacar(jogo, leao, 30)
    assert len(novas(jogo, CaoFarejador)) == LeaoDoProerd.MATILHA_MAXIMA
    for cao in leao.matilha[:2]:
        cao.remover()
    atacar(jogo, leao, 3)                                      # morreu cão: o próximo rugido repõe
    assert len(novas(jogo, CaoFarejador)) == LeaoDoProerd.MATILHA_MAXIMA


def test_cao_segue_o_rastro_do_aluno_e_nao_onde_ele_esta(jogo_limpo):
    jogo = jogo_limpo()
    cao = FabricaDeInimigos.criar("cao_farejador", jogo.jogador.posicao + (400, 0))
    jogo.adicionar(cao)
    jogo._incorporar_novas()
    antigo = pygame.Vector2(jogo.jogador.posicao)
    for _ in range(10):
        cao.atualizar(1 / 30, jogo)
    jogo.jogador.posicao = antigo + (0, 600)                   # o aluno se mexe: o cão ainda fareja o rastro velho
    for _ in range(5):
        cao.atualizar(1 / 30, jogo)
    assert cao.alvo == antigo
    for _ in range(int(CaoFarejador.ATRASO * 30) + 2):
        cao.atualizar(1 / 30, jogo)
    assert cao.alvo == jogo.jogador.posicao                    # passado o atraso, pega o cheiro novo
    perto = cao.posicao.distance_to(jogo.jogador.posicao)
    for _ in range(10):
        cao.atualizar(1 / 30, jogo)
    assert cao.posicao.distance_to(jogo.jogador.posicao) < perto


# ---- segunda fase: o bastão e a fome

def entrar_na_segunda_fase(jogo, leao):
    leao.vida = leao.vida_maxima * LeaoDoProerd.SEGUNDA_FASE_ABAIXO_DE
    leao.mover(1 / 30, jogo)


def test_leao_tem_as_animacoes_da_segunda_fase():
    animacoes = Recursos.animacoes("leao_do_proerd")
    assert {"andar", "andar_bastao", "golpe", "comer"} <= set(animacoes)
    assert len(animacoes["golpe"].quadros) == 6 and len(animacoes["comer"].quadros) == 4


def test_com_metade_da_vida_ele_tira_o_bastao_e_nao_guarda_mais(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo)
    leao.mover(1 / 30, jogo)
    assert not leao.segunda_fase and leao.escolher_animacao() == "andar"
    entrar_na_segunda_fase(jogo, leao)
    assert leao.segunda_fase and leao.escolher_animacao() == "andar_bastao"
    assert any(t for t in novas(jogo, TextoFlutuante))         # avisa que mudou
    leao.vida = leao.vida_maxima
    leao.mover(1 / 30, jogo)
    assert leao.segunda_fase                                   # curar não faz ele guardar o bastão
    assert leao.intervalo_de_ataque < LeaoDoProerd.INTERVALO_ATAQUE


def test_na_segunda_fase_ele_alterna_bastao_fome_e_rugido(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo)
    entrar_na_segunda_fase(jogo, leao)
    vistos = []
    for _ in range(4):
        leao.ataques += 1
        leao.atacar(jogo)
        vistos.append("golpe" if leao.golpe.ativo else "comer" if leao.comendo else "rugido" if leao.rugindo
                      else "?")
        leao.golpe.parar()
        leao._comendo = leao._rugido = 0.0
    assert sorted(vistos) == ["comer", "golpe", "golpe", "rugido"]


def golpear_parado(jogo, leao, distancia):
    """O aluno a `distancia` na frente do leão; devolve a vida que sobrou depois do golpe inteiro."""
    jogo.jogador.posicao = leao.posicao + (distancia, 0)
    leao.golpe.comecar(leao, jogo)
    quadros = []
    for _ in range(int(leao.golpe.duracao * 30) + 3):
        leao.perseguir(1 / 30, jogo)
        quadros.append(leao.golpe.quadro if leao.golpe.ativo else None)
    return quadros


def test_golpe_de_bastao_mira_avanca_e_acerta_com_forca(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo)
    entrar_na_segunda_fase(jogo, leao)
    inicio = pygame.Vector2(leao.posicao)
    jogo.jogador.posicao = leao.posicao + (220, 0)
    leao.golpe.comecar(leao, jogo)
    for _ in range(int(leao.golpe.carga * 30) - 2):            # mirando: não anda nem acerta ainda
        leao.perseguir(1 / 30, jogo)
    assert leao.posicao == inicio and jogo.jogador.vida == jogo.jogador.vida_maxima
    assert leao.escolher_animacao() == "golpe" and leao.golpe.quadro in (0, 1)
    for _ in range(int((leao.golpe.duracao - leao.golpe.carga) * 30) + 3):
        leao.perseguir(1 / 30, jogo)
    assert leao.posicao.x > inicio.x + 60                      # avançou na direção do aluno
    assert jogo.jogador.vida == pytest.approx(jogo.jogador.vida_maxima - LeaoDoProerd.DANO_DO_BASTAO * LeaoDoProerd.FRACAO_DO_DANO)
    assert not leao.golpe.ativo


def test_golpe_passa_pelos_seis_quadros_em_ordem(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    leao = invocar(jogo)
    entrar_na_segunda_fase(jogo, leao)
    quadros = [q for q in golpear_parado(jogo, leao, 200) if q is not None]
    assert quadros == sorted(quadros) and set(quadros) == set(range(6))


def test_golpe_nao_acerta_quem_esta_atras_ou_longe(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo)
    entrar_na_segunda_fase(jogo, leao)
    jogo.jogador.posicao = leao.posicao + (220, 0)
    leao.golpe.comecar(leao, jogo)
    jogo.jogador.posicao = leao.posicao - (400, 0)             # depois de mirar, o aluno foge para trás dele
    for _ in range(int(leao.golpe.duracao * 30) + 3):
        leao.perseguir(1 / 30, jogo)
    assert jogo.jogador.vida == jogo.jogador.vida_maxima


def test_golpe_nao_acerta_quem_esta_colado_nas_costas_dele(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo)
    entrar_na_segunda_fase(jogo, leao)
    jogo.jogador.posicao = leao.posicao + (220, 0)
    leao.golpe.comecar(leao, jogo)
    for _ in range(int((leao.golpe.carga + leao.golpe.avanco) * 30) - 1):
        leao.perseguir(1 / 30, jogo)
        jogo.jogador.posicao = leao.posicao - (90, 0)          # dentro do alcance, mas atrás
    for _ in range(4):
        leao.perseguir(1 / 30, jogo)
    assert jogo.jogador.vida == jogo.jogador.vida_maxima


def test_leao_come_o_malandro_mais_perto_e_recupera_vida(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo, distancia=800)
    entrar_na_segunda_fase(jogo, leao)
    perto = FabricaDeInimigos.criar("malandro", leao.posicao + (150, 0))
    longe = FabricaDeInimigos.criar("malandro", leao.posicao + (900, 0))
    for malandro in (perto, longe):
        leao.receber_lacaio(jogo, malandro)
    jogo._incorporar_novas()
    leao.vida = leao.vida_maxima * 0.3
    leao.comer(jogo)
    assert not perto.ativo and longe.ativo and leao.comendo
    assert leao.escolher_animacao() == "comer"
    parado, vida = pygame.Vector2(leao.posicao), leao.vida
    vistos = []
    for _ in range(int(LeaoDoProerd.TEMPO_COMENDO * 30) + 3):
        if not leao.comendo:
            break
        vistos.append(leao.indice_do_quadro_comendo)
        leao.perseguir(1 / 30, jogo)
    assert leao.posicao == parado and not leao.comendo         # come parado
    assert vistos == sorted(vistos) and set(vistos) == set(range(4))
    assert leao.vida == pytest.approx(vida + leao.vida_maxima * LeaoDoProerd.CURA_POR_MALANDRO)


def test_sem_malandro_por_perto_ele_chama_um_e_come(jogo_limpo):
    jogo = jogo_limpo()
    leao = invocar(jogo, distancia=800)
    entrar_na_segunda_fase(jogo, leao)
    leao.comer(jogo)
    assert leao.comendo
    assert [m for m in novas(jogo, Malandro)] == []            # o chamado já foi para a boca


def test_segunda_fase_inteira_roda_e_desenha(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    leao = invocar(jogo)
    leao.ao_chegar(jogo)
    entrar_na_segunda_fase(jogo, leao)
    tela = pygame.Surface((1280, 720))
    for _ in range(300):
        jogo.atualizar(1 / 30)
        jogo.desenhar(tela)
    assert leao.ataques >= 4
