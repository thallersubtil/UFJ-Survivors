import random

import pygame
import pytest

from jogo.cenario import Cenario
from jogo.fase import Fase
from jogo.inimigos.bug import Bug
from jogo.jogador.classes import Programador
from jogo.jogo import Jogo
from jogo.mapa import Mapa, MapaUFJ, Predio
from jogo.nucleo.colisao import Colisao

QUADRADO = [(100, 100), (200, 100), (200, 200), (100, 200)]


class FaseVazia(Fase):
    def criar_eventos(self):
        return []


def dados_de_teste():
    return {
        "largura": 1200, "altura": 1000, "chao": "cenario/nao_existe.png", "inicio": [600, 800],
        "predios": [{"id": "ru", "nome": "RU", "poligono": [[500, 300], [700, 300], [700, 500], [500, 500]],
                     "sprite": "cenario/predios/nao_existe.png", "canto": [500, 240]}],
        "decoracoes": [{"tipo": "palmeira", "x": 300, "y": 300}],
    }


def test_ponto_no_poligono():
    assert Colisao.ponto_no_poligono((150, 150), QUADRADO)
    assert not Colisao.ponto_no_poligono((250, 150), QUADRADO)


def test_circulo_encosta_no_poligono():
    assert Colisao.circulo_poligono((210, 150), 15, QUADRADO)
    assert not Colisao.circulo_poligono((230, 150), 15, QUADRADO)
    assert Colisao.circulo_poligono((150, 150), 5, QUADRADO)


def test_empurrar_para_fora_de_dentro_e_de_raspao():
    dentro = Colisao.empurrar_para_fora((190, 150), 10, QUADRADO)
    assert dentro.x == pytest.approx(210)
    raspando = Colisao.empurrar_para_fora((205, 150), 10, QUADRADO)
    assert raspando.x == pytest.approx(210)
    longe = Colisao.empurrar_para_fora((300, 150), 10, QUADRADO)
    assert longe is None


def test_empurrar_de_poligono_girado():
    losango = [(0, -100), (100, 0), (0, 100), (-100, 0)]
    novo = Colisao.empurrar_para_fora((40, 40), 10, losango)
    assert not Colisao.circulo_poligono(novo, 9.9, losango)


def test_mapa_e_abstrato_e_tem_duas_implementacoes():
    with pytest.raises(TypeError):
        Mapa()
    assert issubclass(MapaUFJ, Mapa) and issubclass(Cenario, Mapa)


def test_mapa_ufj_a_partir_dos_dados():
    mapa = MapaUFJ(dados_de_teste(), random.Random(1))
    assert mapa.arena.size == (1200, 1000)
    assert mapa.inicio == pygame.Vector2(600, 800)
    predios = [e for e in mapa.entidades() if isinstance(e, Predio)]
    assert len(predios) == 1 and predios[0].nome == "RU"
    assert mapa.bloqueado((600, 400), 10)
    assert not mapa.bloqueado((600, 800), 10)
    assert mapa.empurrar(pygame.Vector2(600, 495), 20).y == pytest.approx(520)


def test_heroi_e_inimigo_nao_atravessam_predio():
    mapa = MapaUFJ(dados_de_teste(), random.Random(1))
    jogo = Jogo(Programador, fase=FaseVazia(), semente=1, mapa=mapa)
    assert jogo.arena.size == (1200, 1000)
    assert jogo.jogador.posicao == pygame.Vector2(600, 800)
    for _ in range(200):
        jogo.entrada.direcao = pygame.Vector2(0, -1)
        jogo.atualizar(1 / 60)
    assert not mapa.bloqueado(jogo.jogador.posicao, jogo.jogador.raio - 1)
    assert jogo.jogador.posicao.y >= 500
    bug = Bug((600, 200))
    jogo.adicionar(bug)
    for _ in range(200):
        jogo.atualizar(1 / 60)
    assert not mapa.bloqueado(bug.posicao, bug.raio - 1)


def test_inimigo_nao_nasce_dentro_de_predio():
    dados = dados_de_teste()
    dados["predios"][0]["poligono"] = [[0, 0], [1200, 0], [1200, 900], [0, 900]]
    mapa = MapaUFJ(dados, random.Random(1))
    jogo = Jogo(Programador, fase=FaseVazia(), semente=2, mapa=mapa)
    for _ in range(40):
        assert not mapa.bloqueado(Fase.posicao_de_nascimento(jogo), 30)


def test_predio_visivel_e_desenha_mesmo_sem_arte():
    mapa = MapaUFJ(dados_de_teste(), random.Random(1))
    jogo = Jogo(Programador, fase=FaseVazia(), semente=1, mapa=mapa)
    jogo.desenhar(pygame.Surface((1280, 720)))
    predio = next(e for e in mapa.entidades() if isinstance(e, Predio))
    assert predio.esta_visivel(jogo.camera)


def test_jogo_sem_mapa_ufj_usa_patio_generico(monkeypatch):
    monkeypatch.setattr(MapaUFJ, "carregar", classmethod(lambda cls, rng: None))
    jogo = Jogo(Programador, fase=FaseVazia(), semente=1)
    assert isinstance(jogo.mapa, Cenario)


def test_escala_do_mapa_vem_do_arquivo():
    dados = dados_de_teste()
    dados["escala"] = 3
    mapa = MapaUFJ(dados, random.Random(1))
    assert mapa.escala == 3
    predio = next(e for e in mapa.entidades() if isinstance(e, Predio))
    assert predio.escala == 3
    jogo = Jogo(Programador, fase=FaseVazia(), semente=1, mapa=mapa)
    jogo.desenhar(pygame.Surface((1280, 720)))


def test_chao_suave_desenha_por_blocos_em_cache(tmp_path, monkeypatch):
    from jogo.nucleo.recursos import Recursos
    (tmp_path / "cenario").mkdir()
    chao = pygame.Surface((400, 400))
    chao.fill((10, 200, 10))
    pygame.image.save(chao, str(tmp_path / "cenario" / "chao.png"))
    monkeypatch.setattr(Recursos, "pasta", tmp_path)
    Recursos.limpar()
    dados = dados_de_teste()
    dados.update({"largura": 1200, "altura": 1200, "chao": "cenario/chao.png", "escala": 3, "escala_predios": 1})
    mapa = MapaUFJ(dados, random.Random(1))
    assert all(p.escala == 1 for p in mapa.entidades() if isinstance(p, Predio))
    jogo = Jogo(Programador, fase=FaseVazia(), semente=1, mapa=mapa)
    tela = pygame.Surface((1280, 720))
    mapa.desenhar_chao(tela, jogo.camera)
    assert tela.get_at((640, 360))[:3] == (10, 200, 10)
    blocos = len(mapa._blocos)
    mapa.desenhar_chao(tela, jogo.camera)
    assert len(mapa._blocos) == blocos > 0
    Recursos.limpar()


# ---------------------------------------------------------------- biomas e lavoura
def _mapa_ufj():
    import pytest
    from jogo.mapa import MapaUFJ
    mapa = MapaUFJ.carregar()
    if mapa is None:
        pytest.skip("sem o mapa da UFJ")
    return mapa


def test_lavoura_fica_em_talhoes_separados_sem_predio_nem_arvore():
    mapa = _mapa_ufj()
    talhoes = mapa.LAVOURAS
    assert len(talhoes) >= 8
    for i, talhao in enumerate(talhoes):
        assert mapa.arena.contains(talhao)
        assert all(not talhao.colliderect(outro) for outro in talhoes[i + 1:])        # há corredor entre eles
        assert all(not talhao.colliderect(predio.contorno) for predio in mapa.predios)
    assert all(not mapa.na_lavoura(d.posicao.x, d.posicao.y) for d in mapa.decoracoes)  # nenhuma árvore na plantação


def test_cada_bioma_tem_a_propria_decoracao():
    mapa = _mapa_ufj()
    nomes = [nome for nome, _, _ in mapa.BIOMAS]
    assert nomes == ["grama", "mata", "lavoura", "terra", "area_51"]
    enfeites = {nome: set(lista) for nome, _, lista in mapa.BIOMAS}
    assert "espantalho" in enfeites["lavoura"] and "aboboras" not in enfeites["lavoura"]
    assert {mapa.cultura_de(t) for t in mapa.LAVOURAS} == {"soja", "milho", "trigo"}
    assert "espantalho" in enfeites["lavoura"] and "espantalho" not in enfeites["grama"] | enfeites["mata"]
    assert "marca_de_pouso" in enfeites["area_51"] and not enfeites["lavoura"] & {"arbusto", "cogumelos"}
    dentro = mapa.LAVOURAS[0].center
    assert mapa._e_lavoura(*dentro) and not mapa._e_grama(*dentro) and not mapa._e_mata(*dentro)
    perto_do_ru = mapa.local_de("RU")
    assert not mapa._e_lavoura(*perto_do_ru)                                           # nada de plantação no RU
    for nome, _, lista in mapa.BIOMAS:
        for enfeite in lista:
            assert mapa._existe(f"cenario/enfeites/{enfeite}.png"), enfeite


def test_plantacao_tem_fileiras_em_pe_e_segura_o_passo_do_aluno(jogo_limpo):
    from jogo.mapa import FileiraDePlantacao
    mapa = _mapa_ufj()
    assert mapa.fileiras and all(isinstance(f, FileiraDePlantacao) for f in mapa.fileiras)
    assert all(mapa.na_lavoura(f.posicao.x, f.posicao.y) for f in mapa.fileiras)
    assert {f.cultura for f in mapa.fileiras} == {"soja", "milho", "trigo"}
    milho = next(f for f in mapa.fileiras if f.cultura == "milho")
    soja = next(f for f in mapa.fileiras if f.cultura == "soja")
    assert milho.imagem.get_height() > soja.imagem.get_height() * 2          # o milho é bem mais alto

    assert mapa.fator_de_velocidade(mapa.inicio) == 1.0
    talhao = next(t for t in mapa.LAVOURAS if mapa.cultura_de(t) == "milho")
    assert mapa.fator_de_velocidade(talhao.center) == mapa.PASSO_NA_CULTURA["milho"] < 1

    def andado(inicio):
        jogo = jogo_limpo()
        jogo.jogador.imortal = True
        jogo.jogador.posicao = pygame.Vector2(inicio)
        jogo.entrada.direcao = pygame.Vector2(1, 0)
        for _ in range(15):
            jogo.atualizar(1 / 30)
        return jogo.jogador.posicao.x - inicio[0]

    livre = pygame.Vector2(mapa.inicio)
    assert andado(talhao.midleft + pygame.Vector2(40, 0)) < andado(livre) * 0.7
