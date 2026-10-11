import pygame
import pytest

from jogo.nucleo.camera import Camera
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.grade import GradeEspacial
from jogo.nucleo.ser_vivo import SerVivo


class Boneco(SerVivo):
    def atualizar(self, dt, jogo):
        pass

    def desenhar(self, tela, camera):
        pass


def test_entidade_e_abstrata():
    with pytest.raises(TypeError):
        Entidade((0, 0), 5)


def test_vida_comeca_cheia_e_nao_passa_dos_limites():
    b = Boneco((0, 0), 10, 50)
    assert b.vida == 50
    b.vida = 999
    assert b.vida == 50
    b.vida = -10
    assert b.vida == 0
    assert not b.esta_vivo


def test_vida_rejeita_valor_que_nao_e_numero():
    b = Boneco((0, 0), 10, 50)
    with pytest.raises(TypeError):
        b.vida = "muita"
    with pytest.raises(TypeError):
        b.vida = True


def test_vida_maxima_deve_ser_positiva_e_corta_vida_atual():
    b = Boneco((0, 0), 10, 50)
    with pytest.raises(ValueError):
        b.vida_maxima = 0
    b.vida_maxima = 30
    assert b.vida == 30


def test_receber_dano_avisa_so_no_golpe_que_mata():
    b = Boneco((0, 0), 10, 20)
    assert b.receber_dano(5) is False
    assert b.vida == 15
    assert b.piscar > 0
    assert b.receber_dano(100) is True
    assert b.receber_dano(1) is False


def test_dano_e_cura_negativos_sao_recusados():
    b = Boneco((0, 0), 10, 20)
    with pytest.raises(ValueError):
        b.receber_dano(-1)
    with pytest.raises(ValueError):
        b.curar(-1)


def test_curar_nao_passa_do_maximo():
    b = Boneco((0, 0), 10, 20)
    b.receber_dano(15)
    b.curar(100)
    assert b.vida == 20


def test_colisao_de_circulos():
    a = Boneco((0, 0), 10, 1)
    b = Boneco((19, 0), 10, 1)
    c = Boneco((21, 0), 10, 1)
    assert Colisao.circulos_colidem(a, b)
    assert not Colisao.circulos_colidem(a, c)


def test_ponto_no_circulo():
    assert Colisao.ponto_no_circulo((3, 4), (0, 0), 5)
    assert not Colisao.ponto_no_circulo((4, 4), (0, 0), 5)


def test_segmento_acerta_circulo():
    assert Colisao.segmento_acerta_circulo((0, 0), (100, 0), 10, (50, 12), 8)
    assert not Colisao.segmento_acerta_circulo((0, 0), (100, 0), 10, (50, 30), 8)
    assert not Colisao.segmento_acerta_circulo((0, 0), (100, 0), 10, (130, 0), 8)
    assert Colisao.segmento_acerta_circulo((0, 0), (0, 0), 10, (3, 0), 1)


def test_grade_acha_vizinhos_e_ignora_distantes():
    grade = GradeEspacial(100)
    perto = Boneco((150, 150), 10, 1)
    longe = Boneco((900, 900), 10, 1)
    grade.reconstruir([perto, longe])
    achados = grade.proximos((120, 120), 50)
    assert perto in achados
    assert longe not in achados


def test_camera_segue_e_respeita_bordas_da_arena():
    arena = pygame.Rect(0, 0, 3000, 2000)
    cam = Camera(1000, 500, arena)
    cam.seguir((1500, 1000))
    assert cam.para_tela((1500, 1000)) == pygame.Vector2(500, 250)
    cam.seguir((10, 10))
    assert cam.retangulo.topleft == (0, 0)
    cam.seguir((2990, 1990))
    assert cam.retangulo.bottomright == (3000, 2000)
    assert cam.para_mundo(cam.para_tela((2500, 1800))) == pygame.Vector2(2500, 1800)


def test_camera_visivel():
    cam = Camera(1000, 500, pygame.Rect(0, 0, 3000, 2000))
    cam.seguir((500, 250))
    assert cam.visivel((990, 490))
    assert cam.visivel((1050, 250), margem=64)
    assert not cam.visivel((1200, 250), margem=64)
