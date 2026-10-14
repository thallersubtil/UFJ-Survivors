import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
import pixelizar  # noqa: E402


def folha_sintetica(n, cor=(30, 160, 60)):
    """n bonecos (corpo colorido, contorno escuro, olho branco) separados por espaço vazio."""
    folha = Image.new("RGBA", (n * 300, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(folha)
    for i in range(n):
        x = i * 300 + 60
        d.rectangle((x, 80 + i * 4, x + 160, 380), fill=(20, 15, 25, 255))
        d.rectangle((x + 12, 92 + i * 4, x + 148, 368), fill=(*cor, 255))
        d.rectangle((x + 90, 130, x + 130, 175), fill=(250, 250, 250, 255))
    return folha


def test_divide_em_n_quadros_mesmo_encostados():
    assert len(pixelizar.dividir(folha_sintetica(4), 4)) == 4
    colada = Image.new("RGBA", (400, 100), (200, 0, 0, 255))
    assert len(pixelizar.dividir(colada, 4)) == 4


def boneco_andando(perna):
    q = Image.new("RGBA", (200, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(q)
    d.ellipse((60, 10, 140, 90), fill=(230, 180, 140, 255))
    d.rectangle((70, 90, 130, 200), fill=(240, 120, 30, 255))
    d.rectangle((75, 200, 95, 290), fill=(40, 60, 160, 255))
    d.rectangle((105 + perna, 200, 125 + perna, 290), fill=(40, 60, 160, 255))
    return q


def test_reduz_com_transparencia_dura_e_paleta_limitada():
    quadros = pixelizar.reduzir(pixelizar.dividir(folha_sintetica(4), 4), altura=60, cores=8)
    assert len({q.size for q in quadros}) == 1 and quadros[0].height == 60
    tudo = np.concatenate([np.array(q).reshape(-1, 4) for q in quadros])
    assert set(np.unique(tudo[:, 3])) <= {0, 255}
    assert len({tuple(int(v) for v in c[:3]) for c in tudo if c[3] == 255}) <= 8


def test_alinha_pela_cabeca_e_tronco_e_nao_pela_largura():
    quadros = pixelizar.reduzir([boneco_andando(p) for p in (0, 30, 60)], altura=100, cores=8)
    centros = [np.nonzero(np.array(q)[..., 3][:25] > 0)[1].mean() for q in quadros]
    assert max(centros) - min(centros) <= 1.0


def test_reduzir_suave_mantem_bordas_macias_e_alinha_pelo_corpo():
    quadros = pixelizar.reduzir_suave([boneco_andando(p) for p in (0, 30, 60)], altura=60)
    assert len({q.size for q in quadros}) == 1 and quadros[0].height == 60
    alfas = set(np.unique(np.concatenate([np.array(q)[..., 3].ravel() for q in quadros])))
    assert len(alfas) > 3                      # borda suave, não binária
    assert min(a for a in alfas if a > 0) >= 24   # sem véu quase invisível em volta
    centros = [np.nonzero(np.array(q)[..., 3][:15] > 128)[1].mean() for q in quadros]
    assert max(centros) - min(centros) <= 1.0


def test_linhas_separa_folha_em_faixas_horizontais():
    folha = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(folha)
    d.rectangle((10, 10, 290, 80), fill=(200, 0, 0, 255))
    d.rectangle((10, 150, 290, 260), fill=(0, 200, 0, 255))
    faixas = pixelizar.linhas(folha, 2)
    assert len(faixas) == 2 and faixas[0].height < faixas[1].height


def test_alinhar_pela_esquerda_mantem_o_mastro_parado():
    quadros = []
    for largura in (60, 100, 80):
        q = Image.new("RGBA", (120, 100), (0, 0, 0, 0))
        ImageDraw.Draw(q).rectangle((5, 0, 10, 99), fill=(255, 255, 255, 255))
        ImageDraw.Draw(q).rectangle((10, 0, largura, 40), fill=(0, 150, 0, 255))
        quadros.append(q.crop(q.getbbox()))
    alinhados = pixelizar.reduzir_suave(quadros, 50, ancora="esquerda")
    mastros = [np.nonzero(np.array(q)[..., 3][-5:] > 128)[1].min() for q in alinhados]
    assert max(mastros) - min(mastros) <= 1
