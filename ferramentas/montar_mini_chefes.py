"""Monta a arte dos mini-chefes do mapa e dos lacaios deles a partir das folhas brutas (nova_arte/_bruto/).

Mini-chefes: folha de 8 quadros andando (viram a tira assets/sprites/<pasta>/andar-8.png) e o rosto
para o mini-mapa (assets/rostos/<pasta>.png), recortado do primeiro quadro. Lacaios: folhas 4x3 com um
bicho por linha. A arte vem olhando para a esquerda e o jogo espera a direita, então tudo é espelhado.

Quem tem animações especiais (EXTRAS: golpe, arremesso, segunda fase) tem todas as tiras postas na mesma tela,
alinhadas pelo corpo e com os pés na base, para não pular de lugar ao trocar de animação.

A ilustração da apresentação de quem está em ILUSTRACOES sai de nova_arte/_bruto/ilustracoes/<pasta>.png
para assets/chefes/<pasta>.png.

Uso: python ferramentas/montar_mini_chefes.py [pasta ...]
Sem nomes, monta tudo; com nomes (ex.: leao_do_proerd malandro), só as pastas pedidas.
"""
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

from pixelizar import dividir, gravar_tira, linhas, reduzir_suave

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "nova_arte" / "_bruto"
SPRITES = RAIZ / "assets" / "sprites"
ROSTOS = RAIZ / "assets" / "rostos"

# pasta: (folha, linhas da folha, altura na tela, fração da altura que é a cabeça)
MINI_CHEFES = {
    "tia_da_cantina": ("mc2_tia_da_cantina_andar_8q.png", 2, 190, 0.50),
    "vigilante": ("mc2_vigilante_andar_8q.png", 2, 96, 0.60),
    "bibliotecaria": ("mc2_bibliotecaria_v2_andar_8q.png", 2, 98, 0.60),
    "tecnico": ("mc2_tecnico_andar_8q.png", 2, 150, 0.45),
    "reitor": ("mc2_reitor_v3_andar_8q.png", 2, 375, 0.14),     # o Reitor de verdade, bem alto (foto de referência)
    "lobo_guara": ("mc2_lobo_guara_andar_8q.png", 2, 112, 0.55),
    "loira": ("mc2_loira_v2_andar_8q.png", 2, 98, 0.58),
    "culto": ("mc2_culto_andar_8q.png", 2, 100, 0.60),
    "gotica": ("mc2_gotica_andar_8q.png", 2, 94, 0.60),
    "et": ("mc2_et_andar_8q.png", 2, 84, 0.62),
    "agroboy": ("mc2_agroboy_andar_8q.png", 2, 100, 0.60),
    "leao_do_proerd": ("mc2_leao_do_proerd_v3_andar_8q.png", 2, 150, 0.52),
}
# animações a mais de um mini-chefe: pasta -> lista de animações. Cada uma diz:
#   folha, nome, linhas e quadros da folha;
#   corte: "celulas" (grade de células iguais) ou "pecas" (cada pedaço do desenho vai para a célula onde fica o
#          centro dele: a corda presa na mão fica no quadro da mão, mesmo passando do meio do vão);
#   ancora: o que fica parado entre os quadros: "camiseta" (a massa preta da camiseta), "massa" (o miolo do
#          corpo, sem as partes finas como bastão e corda) ou "chao" (o que está no chão: buraco, monte de terra);
#   escala: "altura_maxima" (altura do quadro mais alto), "referencia" (índice do quadro, altura que ele deve ter)
#          ou "fator_de" (usa a mesma escala de outra animação do personagem: folhas geradas do mesmo jeito saem
#          com o personagem do mesmo tamanho).
EXTRAS = {
    "leao_do_proerd": (
        dict(folha="mc2_leao_do_proerd_bastao_andar_8q.png", nome="andar_bastao", linhas=2, quadros=8,
             corte="celulas", ancora="camiseta", altura_maxima=154),
        dict(folha="mc2_leao_do_proerd_golpe_6q.png", nome="golpe", linhas=2, quadros=6, corte="celulas",
             ancora="camiseta", altura_maxima=158),
        dict(folha="mc2_leao_do_proerd_comer_4q.png", nome="comer", linhas=1, quadros=4, corte="celulas",
             ancora="camiseta", altura_maxima=167),
    ),
    "tia_da_cantina": (
        dict(folha="mc2_tia_da_cantina_arremessar_4q.png", nome="arremessar", linhas=1, quadros=4, corte="pecas",
             ancora="massa", referencia=(3, 176)),
        dict(folha="mc2_tia_da_cantina_panelao_6q.png", nome="panelao", linhas=2, quadros=6, corte="pecas",
             ancora="massa", referencia=(5, 176)),
        dict(folha="mc2_tia_da_cantina_girar_4q.png", nome="girar", linhas=1, quadros=4, corte="pecas",
             ancora="massa", fator_de="arremessar"),
        dict(folha="mc2_tia_da_cantina_concha_andar_8q.png", nome="andar_concha", linhas=2, quadros=8,
             corte="pecas", ancora="massa", fator_de="andar"),
    ),
    "lobo_guara": (
        dict(folha="mc2_lobo_guara_uivar_4q.png", nome="uivar", linhas=1, quadros=4, corte="pecas",
             ancora="massa", referencia=(0, 112)),
        dict(folha="mc2_lobo_guara_bote_4q.png", nome="bote", linhas=1, quadros=4, corte="pecas", ancora="massa",
             referencia=(0, 68)),                  # agachado: nesta folha o lobo saiu menor que na do uivo
        dict(folha="mc2_lobo_guara_cavar_4q.png", nome="cavar", linhas=1, quadros=4, corte="pecas", ancora="chao",
             fator_de="uivar"),
        dict(folha="mc2_lobo_guara_emergir_4q.png", nome="emergir", linhas=1, quadros=4, corte="pecas",
             ancora="chao", referencia=(3, 112)),
    ),
    "vigilante": (
        dict(folha="mc2_vigilante_lanterna_4q.png", nome="lanterna", linhas=1, quadros=4, corte="pecas",
             ancora="massa", referencia=(0, 96)),
        dict(folha="mc2_vigilante_arrancada_4q.png", nome="arrancada", linhas=1, quadros=4, corte="pecas",
             ancora="massa", fator_de="lanterna"),
        dict(folha="mc2_vigilante_gancho_4q.png", nome="gancho", linhas=1, quadros=4, corte="pecas",
             ancora="massa", fator_de="lanterna"),
        dict(folha="mc2_vigilante_voadora_4q.png", nome="voadora", linhas=1, quadros=4, corte="pecas",
             ancora="massa", fator_de="lanterna"),
    ),
    "bibliotecaria": (
        dict(folha="mc2_bibliotecaria_anotar_4q.png", nome="anotar", linhas=1, quadros=4, corte="pecas",
             ancora="massa", referencia=(0, 100)),
        dict(folha="mc2_bibliotecaria_arremessar_4q.png", nome="arremessar", linhas=1, quadros=4, corte="pecas",
             ancora="massa", referencia=(0, 100)),
        dict(folha="mc2_bibliotecaria_shhh_4q.png", nome="shhh", linhas=1, quadros=4, corte="pecas",
             ancora="massa", referencia=(0, 100)),
    ),
    "tecnico": (
        dict(folha="mc2_tecnico_arremessar_4q.png", nome="arremessar", linhas=1, quadros=4, corte="pecas",
             ancora="massa", referencia=(0, 150)),
        dict(folha="mc2_tecnico_socar_chao_4q.png", nome="socar_chao", linhas=1, quadros=4, corte="pecas",
             ancora="massa", fator_de="arremessar"),
        dict(folha="mc2_tecnico_furia_andar_8q.png", nome="andar_furia", linhas=2, quadros=8, corte="pecas",
             ancora="massa", referencia=(0, 160)),       # o vapor da cabeça deixa o quadro um pouco mais alto
    ),
    "reitor": (
        dict(folha="mc2_reitor_carimbar_4q.png", nome="carimbar", linhas=1, quadros=4, corte="pecas",
             ancora="massa", referencia=(0, 375)),
        dict(folha="mc2_reitor_apresentar_4q.png", nome="apresentar", linhas=1, quadros=4, corte="pecas",
             ancora="massa", referencia=(0, 375)),
    ),
    "loira": (
        dict(folha="mc2_loira_chamar_4q.png", nome="chamar", linhas=1, quadros=4, corte="pecas", ancora="massa",
             referencia=(0, 98)),
        dict(folha="mc2_loira_chave_4q.png", nome="chave", linhas=1, quadros=4, corte="pecas", ancora="massa",
             referencia=(0, 98)),
        dict(folha="mc2_loira_broca_4q.png", nome="broca", linhas=1, quadros=4, corte="pecas", ancora="massa",
             referencia=(0, 84)),                         # agachada, apontando a broca
    ),
    "agroboy": (
        dict(folha="mc2_agroboy_dinheiro_4q.png", nome="dinheiro", linhas=1, quadros=4, corte="pecas",
             ancora="massa", referencia=(0, 100)),
        dict(folha="mc2_agroboy_laco_4q.png", nome="laco", linhas=1, quadros=4, corte="pecas", ancora="massa",
             referencia=(0, 100)),
        dict(folha="mc2_agroboy_touro_andar_8q.png", nome="andar_touro", linhas=2, quadros=8, corte="pecas",
             ancora="massa", referencia=(0, 140)),        # montado no touro: maior que a pé
    ),
    "culto": (
        dict(folha="mc2_culto_ritual_4q.png", nome="ritual", linhas=1, quadros=4, corte="pecas", ancora="massa",
             referencia=(0, 104)),
        dict(folha="mc2_culto_ascensao_limpo_andar_8q.png", nome="andar_ascensao", linhas=2, quadros=8, corte="pecas",
             ancora="massa", referencia=(0, 116)),
    ),
    "gotica": (
        dict(folha="mc2_gotica_sumir_4q.png", nome="sumir", linhas=1, quadros=4, corte="pecas", ancora="massa",
             referencia=(0, 94)),
        dict(folha="mc2_gotica_vodu_4q.png", nome="vodu", linhas=1, quadros=4, corte="pecas", ancora="massa",
             referencia=(0, 94)),
    ),
    "et": (
        dict(folha="mc2_et_telepatia_4q.png", nome="telepatia", linhas=1, quadros=4, corte="celulas",
             ancora="massa", referencia=(0, 84)),
        dict(folha="mc2_et_disco_andar_8q.png", nome="andar_disco", linhas=2, quadros=8, corte="pecas",
             ancora="massa", referencia=(0, 96)),
    ),
}
# animação de ataque dos professores (chefes das provas): pasta -> (folha em _bruto/, quadros, corte). As tiras de andar e
# parado deles vêm de outras ferramentas e não mudam aqui: a de ataque é medida pela de andar que já existe (mesma
# altura do corpo e os pés na mesma linha).
PROFESSORES = {
    "professor": ("professor_calculo_atacar_4q.png", 4, "pecas"),        # (a folha bruta teve o vão aberto à mão)
    "professor_computacao": ("sem_pixel/sprites/professor_computacao_atacar_4q.png", 4, "pecas"),
    "professora": ("sem_pixel/sprites/professora_atacar_4q.png", 4, "pecas"),
}
# o que fica parado no andar de quem tem EXTRAS (o padrão é o miolo do corpo)
ANCORA_DO_ANDAR = {"leao_do_proerd": "camiseta"}
# folha 4 colunas x 3 linhas: (pasta, altura na tela) de cada linha
LACAIOS = {
    "mc2_lacaios_a.png": (("coxinha", 36), ("morcego", 34), ("livro_atrasado", 40)),
    "mc2_lacaios_b.png": (("cobaia", 32), ("carimbo", 42), ("lobinho", 36)),
    "mc2_lacaios_c.png": (("dente", 40), ("cultista", 46), ("mini_ovni", 40)),
    "mc2_lacaios_d.png": (("boi", 56), ("hb20", 58), ("caminhonete", 92)),
}
GATO = ("mc2_gato_alienigena_8q.png", "gato_alienigena", 38)
# lacaios com folha própria, de uma linha só: folha -> (pasta, quadros, altura na tela)
SOLTOS = {"mc2_malandro_andar_4q.png": ("malandro", 4, 48),
          "mc2_cao_farejador_andar_4q.png": ("cao_farejador", 4, 44)}
# quem tem a ilustração da apresentação montada aqui: pasta em assets/chefes/ -> arquivo em _bruto/ilustracoes/
ILUSTRACOES = {"leao_do_proerd": "leao_do_proerd_v6.png", "reitor": "reitor_v2.png"}
# quem tem o rosto do mini-mapa recortado da ilustração (mais nítido que o do boneco da partida):
# pasta -> (centro x, centro y, lado), em frações da ilustração; o recorte sai redondo
ROSTOS_DA_ILUSTRACAO = {"reitor": (0.485, 0.072, 0.14)}
ALTURA_DA_ILUSTRACAO = 900
LADO_DO_ROSTO = 64


def espelhados(quadros):
    return [ImageOps.mirror(q) for q in quadros]


def recortado(imagem):
    """A imagem cortada no que é visível de verdade (ignora o quase transparente que o gerador deixa)."""
    visivel = imagem.getchannel("A").point(lambda a: 255 if a > 40 else 0)
    caixa = visivel.getbbox()
    return imagem.crop(caixa) if caixa else imagem


def quadros_da_folha(folha, n_linhas, n_quadros, corte=None):
    """Os quadros da folha, linha por linha. Sem `corte`, separa pelos vãos vazios; "celulas" corta numa grade
    de células iguais; "pecas" manda cada pedaço do desenho para a célula onde fica o centro dele."""
    imagem = Image.open(BRUTO / folha).convert("RGBA")
    if corte is None:
        faixas = linhas(imagem, n_linhas) if n_linhas > 1 else [imagem]
        return [q for faixa in faixas for q in dividir(faixa, n_quadros // n_linhas)]
    colunas = n_quadros // n_linhas
    largura, altura = imagem.width / colunas, imagem.height / n_linhas
    if corte == "celulas":
        return [recortado(sem_lascas(imagem.crop((round(c * largura), round(l * altura), round((c + 1) * largura),
                                                  round((l + 1) * altura)))))
                for l in range(n_linhas) for c in range(colunas)]
    alfa = np.array(imagem.getchannel("A"))
    superficie = pygame.Surface(imagem.size, pygame.SRCALPHA)
    pygame.surfarray.pixels_alpha(superficie)[:] = alfa.T
    pedacos = pygame.mask.from_surface(superficie, 40).connected_components(12)
    casas = [np.zeros(alfa.shape, bool) for _ in range(n_quadros)]
    caixas = [[] for _ in range(n_quadros)]

    def casa_do_centro(pedaco):
        x, y = pedaco.centroid()
        return min(n_linhas - 1, int(y // altura)) * colunas + min(colunas - 1, int(x // largura))

    grandes = [p for p in pedacos if p.count() >= PEDACO_PEQUENO]
    for pedaco in grandes:                       # os corpos (e o que está preso neles) vão pela célula
        casa = casa_do_centro(pedaco)
        casas[casa] |= _mascara_em_array(pedaco)
        caixas[casa] += pedaco.get_bounding_rects()
    for pedaco in pedacos:                       # riscos, gotas e torrões vão para o corpo mais perto, a não ser
        #                                          que o quadro deles não tenha corpo nenhum
        if pedaco.count() >= PEDACO_PEQUENO:
            continue
        caixa = pedaco.get_bounding_rects()[0]
        casa = casa_do_centro(pedaco)
        if caixas[casa]:                         # o quadro tem corpo: vai para o corpo mais perto (pode ser o vizinho)
            candidatas = [i for i in range(n_quadros) if caixas[i]]
            casa = min(candidatas, key=lambda i: min(_distancia(caixa, c) for c in caixas[i]))
        casas[casa] |= _mascara_em_array(pedaco)  # quadro só de pedaços (a nuvem de morcegos): fica com eles
    quadros = []
    for casa in casas:
        pixels = np.array(imagem)
        pixels[~casa] = 0
        quadros.append(recortado(Image.fromarray(pixels, "RGBA")))
    return quadros


PEDACO_PEQUENO = 6000           # pixels: abaixo disso é risco, gota ou torrão solto, não um corpo


def _distancia(a, b):
    """Distância entre dois retângulos (0 se encostam)."""
    dx = max(0, a.left - b.right, b.left - a.right)
    dy = max(0, a.top - b.bottom, b.top - a.bottom)
    return (dx * dx + dy * dy) ** 0.5


def sem_lascas(celula):
    """Apaga da célula os pedaços pequenos encostados na borda da esquerda ou da direita: são pontas do desenho
    do quadro vizinho (uma onda, uma aura) que passaram do meio do vão."""
    superficie = pygame.Surface(celula.size, pygame.SRCALPHA)
    pygame.surfarray.pixels_alpha(superficie)[:] = np.array(celula.getchannel("A")).T
    pixels = np.array(celula)
    for pedaco in pygame.mask.from_surface(superficie, 40).connected_components(1):
        caixa = pedaco.get_bounding_rects()[0]
        if pedaco.count() < PEDACO_PEQUENO and (caixa.left <= 1 or caixa.right >= celula.width - 1):
            pixels[_mascara_em_array(pedaco)] = 0
    return Image.fromarray(pixels, "RGBA")


def _mascara_em_array(mascara):
    superficie = mascara.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 255))
    return pygame.surfarray.array_red(superficie).T > 0


def _miolo(opaco, raio):
    """Só o que tem pixels marcados `raio` pixels para cada lado (some com o que é fino: contorno, bastão, corda)."""
    miolo = opaco.copy()
    for d in range(1, raio + 1):
        miolo[d:, :] &= opaco[:-d, :]
        miolo[:-d, :] &= opaco[d:, :]
        miolo[:, d:] &= opaco[:, :-d]
        miolo[:, :-d] &= opaco[:, d:]
    return miolo


def centro_da_camiseta(quadro):
    """Coluna do meio da massa escura do quadro (a camiseta preta), sem o contorno fino nem o bastão."""
    a = np.array(quadro).astype(int)
    xs = np.nonzero(_miolo((a[..., 3] > 0) & (a[..., :3].max(axis=2) < 70), 3))[1]
    return xs.mean() if len(xs) else quadro.width / 2


def centro_da_massa(quadro):
    """Coluna mediana do miolo do corpo, entre 15% e 55% da altura: cabeça e tronco, que quase não mexem (sem
    bastão, corda e rastro, que são finos, e sem as pernas, que abrem no passo)."""
    opaco = np.array(quadro)[..., 3] > 40
    linhas_cheias = np.nonzero(opaco.any(axis=1))[0]
    if len(linhas_cheias) == 0:
        return quadro.width / 2
    topo, base = linhas_cheias[0], linhas_cheias[-1]
    faixa = np.zeros_like(opaco)
    faixa[int(topo + 0.15 * (base - topo)):int(topo + 0.55 * (base - topo)) + 1] = True
    xs = np.nonzero(_miolo(opaco, 4) & faixa)[1]
    return float(np.median(xs)) if len(xs) else quadro.width / 2


def centro_do_chao(quadro):
    """Meio do que está nos 15% de baixo do quadro (o buraco, o monte de terra)."""
    opaco = np.array(quadro)[..., 3] > 40
    linhas_cheias = np.nonzero(opaco.any(axis=1))[0]
    if len(linhas_cheias) == 0:
        return quadro.width / 2
    topo, base = linhas_cheias[0], linhas_cheias[-1]
    xs = np.nonzero(opaco[int(base - 0.15 * (base - topo)):])[1]
    return (xs.min() + xs.max()) / 2


ANCORAS = {"camiseta": centro_da_camiseta, "massa": centro_da_massa, "chao": centro_do_chao}


def reduzidos(quadros, extra, fatores):
    """Os quadros já na escala da tela, conforme o que a animação pede (veja EXTRAS)."""
    if "altura_maxima" in extra:
        fator = extra["altura_maxima"] / max(q.height for q in quadros)
    elif "referencia" in extra:
        indice, altura = extra["referencia"]
        fator = altura / quadros[indice].height
    else:
        fator = fatores[extra["fator_de"]]
    fatores[extra["nome"]] = fator
    saida = []
    for q in quadros:
        r = q.resize((max(1, round(q.width * fator)), max(1, round(q.height * fator))), Image.LANCZOS)
        a = np.array(r)
        a[a[..., 3] < 24] = 0
        saida.append(Image.fromarray(a, "RGBA"))
    return saida


def mesma_tela(tiras, ancoras_por_tira):
    """Acerta as tiras de um personagem para ele não pular de lugar ao trocar de animação.

    O jogo desenha cada quadro centrado na posição, então: a âncora (camiseta, corpo ou chão) fica no meio da
    largura, e os pés ficam sempre à mesma distância abaixo do meio, a do andar. Quem tem algo acima da cabeça
    (o panelão erguido) ganha uma tela mais alta só naquela animação, com o meio no mesmo lugar."""
    altura_do_andar = tiras["andar"][0].height
    saida = {}
    for nome, quadros in tiras.items():
        ancoras = [ANCORAS[ancoras_por_tira[nome]](q) for q in quadros]
        meia = int(max(max(a, q.width - a) for q, a in zip(quadros, ancoras))) + 2
        altura = max(altura_do_andar, 2 * max(q.height for q in quadros) - altura_do_andar)
        pes = (altura + altura_do_andar) // 2
        novos = []
        for q, ancora in zip(quadros, ancoras):
            tela = Image.new("RGBA", (meia * 2, altura), (0, 0, 0, 0))
            tela.paste(q, (round(meia - ancora), pes - q.height))
            novos.append(tela)
        saida[nome] = novos
    return saida


def montar_ataque_de_professor(pasta, folha, n_quadros, corte):
    """A tira atacar-<n> do professor, do tamanho do andar dele: o primeiro quadro (de pé) com a altura do corpo
    no andar, o corpo no meio e os pés à mesma distância do meio que no andar."""
    andar = Image.open(SPRITES / pasta / "andar-8.png").convert("RGBA")
    quadro_do_andar = andar.crop((0, 0, andar.width // 8, andar.height))
    caixa = quadro_do_andar.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    altura_do_corpo, pes_do_andar = caixa[3] - caixa[1], caixa[3]
    quadros = espelhados(quadros_da_folha(folha, 1, n_quadros, corte))
    quadros = reduzidos(quadros, dict(nome="atacar", referencia=(0, altura_do_corpo)), {})
    ancoras = [centro_da_massa(q) for q in quadros]
    meia = int(max(max(a, q.width - a) for q, a in zip(quadros, ancoras))) + 2
    distancia = pes_do_andar - andar.height / 2                # dos pés até o meio do quadro, no andar
    altura = int(max(andar.height, 2 * max(q.height - distancia for q in quadros) + 2))
    pes = round(altura / 2 + distancia)
    saida = []
    for q, ancora in zip(quadros, ancoras):
        tela = Image.new("RGBA", (meia * 2, altura), (0, 0, 0, 0))
        tela.paste(q, (round(meia - ancora), pes - q.height))
        saida.append(tela)
    return gravar_tira(saida, SPRITES / pasta, "atacar")


def rosto(tira, quadros, fracao):
    """Recorta a cabeça do primeiro quadro num quadrado (o que sobra dos lados fica transparente)."""
    largura = tira.width // quadros
    quadro = tira.crop((0, 0, largura, tira.height))
    quadro = quadro.crop(quadro.getbbox())
    lado = max(1, round(quadro.height * fracao))
    cabeca = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    cabeca.alpha_composite(quadro.crop((0, 0, quadro.width, lado)), ((lado - quadro.width) // 2, 0)) \
        if quadro.width <= lado else cabeca.alpha_composite(
            quadro.crop(((quadro.width - lado) // 2, 0, (quadro.width + lado) // 2, lado)))
    return cabeca.resize((LADO_DO_ROSTO, LADO_DO_ROSTO), Image.LANCZOS)


def rosto_da_ilustracao(arte, enquadramento, destino):
    """Recorta a cabeça da ilustração num círculo (o fundo da ilustração não aparece em volta)."""
    cx, cy, lado = enquadramento
    meio = lado * arte.height / 2
    caixa = (round(cx * arte.width - meio), round(cy * arte.height - meio),
             round(cx * arte.width + meio), round(cy * arte.height + meio))
    cabeca = arte.crop(caixa).resize((LADO_DO_ROSTO, LADO_DO_ROSTO), Image.LANCZOS)
    mascara = Image.new("L", (LADO_DO_ROSTO * 4, LADO_DO_ROSTO * 4), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, LADO_DO_ROSTO * 4 - 1, LADO_DO_ROSTO * 4 - 1), fill=255)
    cabeca.putalpha(mascara.resize((LADO_DO_ROSTO, LADO_DO_ROSTO), Image.LANCZOS))
    cabeca.save(destino)
    return destino


def main(pedidas=()):
    pygame.init()

    def pedida(pasta):
        return not pedidas or pasta in pedidas

    ROSTOS.mkdir(parents=True, exist_ok=True)
    for pasta, (folha, n_linhas, altura, cabeca) in MINI_CHEFES.items():
        if not pedida(pasta):
            continue
        brutos = quadros_da_folha(folha, n_linhas, 8)
        tiras = {"andar": reduzir_suave(espelhados(brutos), altura)}
        ancoras = {"andar": ANCORA_DO_ANDAR.get(pasta, "massa")}
        fatores = {"andar": altura / max(q.height for q in brutos)}
        for extra in EXTRAS.get(pasta, ()):
            quadros = quadros_da_folha(extra["folha"], extra["linhas"], extra["quadros"], extra["corte"])
            tiras[extra["nome"]] = reduzidos(espelhados(quadros), extra, fatores)
            ancoras[extra["nome"]] = extra["ancora"]
        if len(tiras) > 1:
            tiras = mesma_tela(tiras, ancoras)
        for nome, quadros in tiras.items():
            caminho = gravar_tira(quadros, SPRITES / pasta, nome)
            print(caminho)
        rosto(Image.open(SPRITES / pasta / "andar-8.png").convert("RGBA"), 8, cabeca).save(ROSTOS / f"{pasta}.png")
    for folha, bichos in LACAIOS.items():
        faixas = linhas(Image.open(BRUTO / folha).convert("RGBA"), len(bichos))
        for faixa, (pasta, altura) in zip(faixas, bichos):
            if not pedida(pasta):
                continue
            print(gravar_tira(reduzir_suave(espelhados(dividir(faixa, 4)), altura), SPRITES / pasta, "andar"))
    folha, pasta, altura = GATO
    if pedida(pasta):
        faixas = linhas(Image.open(BRUTO / folha).convert("RGBA"), 2)
        quadros = [q for faixa in faixas for q in dividir(faixa, 4)]
        print(gravar_tira(reduzir_suave(espelhados(quadros), altura), SPRITES / pasta, "andar"))
    for folha, (pasta, n_quadros, altura) in SOLTOS.items():
        if pedida(pasta):
            quadros = dividir(Image.open(BRUTO / folha).convert("RGBA"), n_quadros)
            print(gravar_tira(reduzir_suave(espelhados(quadros), altura), SPRITES / pasta, "andar"))
    for pasta, (folha, n_quadros, corte) in PROFESSORES.items():
        if pedida(pasta):
            print(montar_ataque_de_professor(pasta, folha, n_quadros, corte))
    for pasta, arquivo in ILUSTRACOES.items():
        if pedida(pasta):
            arte = Image.open(BRUTO / "ilustracoes" / arquivo).convert("RGBA")
            largura = round(arte.width * ALTURA_DA_ILUSTRACAO / arte.height)
            destino = RAIZ / "assets" / "chefes" / f"{pasta}.png"
            arte.resize((largura, ALTURA_DA_ILUSTRACAO), Image.LANCZOS).save(destino)
            print(destino)
            if pasta in ROSTOS_DA_ILUSTRACAO:
                print(rosto_da_ilustracao(arte, ROSTOS_DA_ILUSTRACAO[pasta], ROSTOS / f"{pasta}.png"))


if __name__ == "__main__":
    main(tuple(sys.argv[1:]))
