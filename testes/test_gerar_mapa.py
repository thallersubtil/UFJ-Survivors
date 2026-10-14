import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
import gerar_mapa  # noqa: E402


def test_classifica_cores_do_satelite():
    c = gerar_mapa.Classe
    cores = np.array([[[176, 84, 52], [40, 80, 40], [205, 205, 200], [110, 160, 70]]], dtype=np.uint8)
    assert list(gerar_mapa.classificar(cores)[0]) == [c.TERRA, c.MATA, c.CONCRETO, c.GRAMA]


def test_projecao_ida_e_volta():
    recorte = gerar_mapa.Recorte(tile_x0=46704, tile_y0=72169, zoom=17, x0=430, y0=160, x1=1060, y1=1150)
    x, y = recorte.mundo(-17.9267, -51.7175)
    assert 0 < x < recorte.largura_mundo and 0 < y < recorte.altura_mundo
    lat, lon = recorte.latlon(x, y)
    assert lat == pytest.approx(-17.9267, abs=1e-6) and lon == pytest.approx(-51.7175, abs=1e-6)


def test_nome_curto_dos_predios():
    assert gerar_mapa.nome_curto("Restaurante Universitário UFJ") == "RU"
    assert gerar_mapa.nome_curto('Biblioteca do Câmpus Jatobá - "Flor do Cerrado"') == "BIBLIOTECA"
    assert gerar_mapa.nome_curto("Centro de Aulas I") == "CENTRO DE AULAS I"
    assert gerar_mapa.nome_curto(None) == ""


def test_cor_do_telhado_vai_para_a_paleta():
    assert gerar_mapa.cor_de_telhado((180, 95, 62)) == gerar_mapa.TELHADOS["ceramica"]
    assert gerar_mapa.cor_de_telhado((230, 230, 228)) == gerar_mapa.TELHADOS["branco"]
    assert gerar_mapa.cor_de_telhado((85, 88, 96)) == gerar_mapa.TELHADOS["escuro"]


def test_sprite_de_predio_tem_parede_telhado_e_contorno():
    poligono = [(10, 30), (50, 30), (50, 50), (10, 50)]
    sprite, canto = gerar_mapa.desenhar_predio(poligono, gerar_mapa.TELHADOS["branco"], andares=2, nome="RU")
    assert sprite.get_height() > 20 + 2 * gerar_mapa.ALTURA_ANDAR - 1
    assert canto[1] < 30
    assert sprite.get_at((0, 0)).a == 0
