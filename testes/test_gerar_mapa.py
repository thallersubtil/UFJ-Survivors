import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
import gerar_mapa  # noqa: E402
import pintar_predios  # noqa: E402


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


def test_estilo_do_predio_e_fixo_por_nome_ou_por_identificador():
    assert pintar_predios.estilo_do_predio("predio_1", "BIBLIOTECA") == "metal"
    assert pintar_predios.estilo_do_predio("predio_1", "RU") == "ceramica"
    sorteado = pintar_predios.estilo_do_predio("predio_42", "PREDIO")
    assert sorteado in pintar_predios.ESTILOS and sorteado == pintar_predios.estilo_do_predio("predio_42", "PREDIO")


@pytest.mark.parametrize("estilo", sorted(pintar_predios.ESTILOS))
def test_sprite_de_predio_tem_parede_telhado_e_contorno(estilo):
    poligono = [(100, 300), (400, 300), (400, 500), (100, 500)]
    altura_parede = 2 * gerar_mapa.ALTURA_ANDAR
    sprite, canto = pintar_predios.pintar_predio(poligono, altura_parede, estilo, nome="RU")
    assert sprite.height > 200 + altura_parede - 1
    assert canto == (100 - pintar_predios.MARGEM, 300 - altura_parede - pintar_predios.MARGEM)
    assert sprite.getpixel((0, 0))[3] == 0                       # fora do prédio é transparente
    telhado = sprite.getpixel((150, 100))
    parede = sprite.getpixel((36, 420 - canto[1]))               # entre duas janelas, na parede da frente
    assert telhado[3] == 255 and parede[3] == 255 and telhado != parede
    assert sprite.getpixel((250, 500 - canto[1] + pintar_predios.SOMBRA[1] + 4))[3] in range(1, 255)   # sombra no chão


def test_paredes_visiveis_sao_as_viradas_para_baixo_nos_dois_sentidos():
    horario = [(0, 0), (10, 0), (10, 10), (0, 10)]
    for base in (horario, horario[::-1]):
        faces = pintar_predios._faces_visiveis(base)
        assert [(a[1], b[1]) for _, a, b in faces] == [(10, 10)]

