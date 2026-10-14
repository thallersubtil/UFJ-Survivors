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


def test_quadros_tem_altura_nativa_mesma_largura_e_transparencia_dura():
    quadros = pixelizar.pixelizar(pixelizar.dividir(folha_sintetica(4), 4), altura=24, cores=8)
    assert len({q.size for q in quadros}) == 1
    assert quadros[0].height == 24
    alfas = {a for q in quadros for a in np.array(q.getchannel("A")).ravel()}
    assert alfas <= {0, 255}


def test_preserva_o_brilho_do_olho_e_poe_contorno():
    q = pixelizar.pixelizar(pixelizar.dividir(folha_sintetica(1), 1), altura=24, cores=8)[0]
    cores = {c[:3] for c in map(tuple, np.array(q).reshape(-1, 4)) if c[3] == 255}
    assert any(sum(c) > 700 for c in cores)
    assert any(sum(c) < 100 for c in cores)


def test_gravar_tira_com_numero_de_quadros_no_nome(tmp_path):
    quadros = pixelizar.pixelizar(pixelizar.dividir(folha_sintetica(3), 3), altura=20, cores=8)
    caminho = pixelizar.gravar_tira(quadros, tmp_path / "heroi", "andar")
    assert caminho.name == "andar-3.png"
    tira = Image.open(caminho)
    assert tira.size == (quadros[0].width * 3, 20)
