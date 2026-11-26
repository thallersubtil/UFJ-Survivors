"""Monta a arte dos ataques dos chefes e mini-chefes (estilo liso, sem pixels).

Cada folha em nova_arte/_bruto/sem_pixel/ataques/<folha>.png (fora do git) traz 6 objetos numa grade de
3 colunas por 2 linhas, com fundo transparente. Cada objeto vira assets/ataques/<nome>.png, com o lado
maior em LADO pixels (o jogo reduz para a altura de cada projétil). Os pedaços soltos do desenho (vapor,
gotas, faíscas) vão para o objeto da casa da grade em que estão.

Também saem daqui a poça de sopa (a poça de ácido pintada de laranja) e as loirinhas (a tira da Loira da
Odontologia em tamanho de lacaio).

Uso: .venv/bin/python ferramentas/montar_ataques.py
"""
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "nova_arte" / "_bruto" / "sem_pixel" / "ataques"
DESTINO = RAIZ / "assets" / "ataques"
COLUNAS, LINHAS = 3, 2
LADO = 128
ALTURA_DA_LOIRINHA = 56

# folha: os seis nomes, na ordem de leitura (linha de cima da esquerda para a direita, depois a de baixo)
FOLHAS = {
    "cantina": ("bandeja", "prato_feito", "panelao", "concha", "colher_de_pau", "frigideira"),
    "odonto": ("escova", "pasta_de_dente", "dente", "espelhinho", "broca", "salto"),
    "gotica": ("coracao_preto", "rosa_negra", "morcego", "caveira", "vela_roxa", "nuvem_de_morcegos"),
    "agroboy": ("dinheiro", "chapeu", "milho", "bota", "fivela", "saco_de_soja"),
    "biblioteca": ("livro", "multa", "carimbo_da_biblioteca", "oculos", "livro_voador", "caderno_preto"),
    "et": ("laser", "plasma", "vaca", "anel_de_abducao", "feixe_de_luz", "cristal"),
    "lobo": ("garra", "lobeira", "osso", "pegada", "uivo", "poeira"),
    "tecnico": ("seringa", "erlenmeyer", "tubo_de_ensaio", "bequer", "poca_de_acido", "placa_de_petri"),
    "vigilante": ("batarangue", "lanterna", "apito", "cone", "cassetete", "distintivo"),
    "culto": ("adaga", "chama_dourada", "olho", "vela_preta", "livro_proibido", "selo"),
    "reitor": ("oficio", "portaria", "carimbo", "caneta", "pasta", "indeferido"),
    "calculo": ("lim", "dx", "integral", "pi", "giz", "esquadro"),
    "arquitetura": ("bit0", "bit1", "cpu", "clock", "ventoinha", "interrupcao"),
    "estrutura_de_dados": ("ponteiro", "null", "colchetes", "lista", "segfault", "pilha"),
    "transformacao_digital": ("email", "nuvem", "celular", "wifi", "reuniao", "grafico"),
    "poo": ("new", "chaves", "self", "engrenagem", "cadeado", "classe"),
}


def cortar(folha):
    """Uma imagem por casa da grade, com tudo o que tem o centro dentro dela."""
    largura, altura = folha.get_size()
    mascara = pygame.mask.from_surface(folha, 40)
    casas = [pygame.mask.Mask(folha.get_size()) for _ in range(COLUNAS * LINHAS)]
    for pedaco in mascara.connected_components(12):
        x, y = pedaco.centroid()
        casa = min(LINHAS - 1, y * LINHAS // altura) * COLUNAS + min(COLUNAS - 1, x * COLUNAS // largura)
        casas[casa].draw(pedaco, (0, 0))
    objetos = []
    for casa in casas:
        caixas = casa.get_bounding_rects()
        if not caixas:
            objetos.append(None)
            continue
        caixa = caixas[0].unionall(caixas[1:])
        objeto = folha.copy()
        apagar = casa.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))
        objeto.blit(apagar, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        objetos.append(objeto.subsurface(caixa).copy())
    return objetos


def no_lado(imagem, lado):
    fator = lado / max(imagem.get_size())
    return pygame.transform.smoothscale(imagem, (max(1, round(imagem.get_width() * fator)),
                                                 max(1, round(imagem.get_height() * fator))))


def repintar(imagem, matiz):
    """Cópia com as cores giradas para outro matiz (a poça de ácido vira poça de sopa)."""
    nova = imagem.copy()
    for x in range(nova.get_width()):
        for y in range(nova.get_height()):
            cor = nova.get_at((x, y))
            if cor.a == 0:
                continue
            h, s, v, a = cor.hsva
            if s > 25:                               # o contorno escuro e os brilhos brancos ficam como estão
                cor.hsva = (matiz, s, v, a)
                nova.set_at((x, y), cor)
    return nova


def montar():
    pygame.init()
    pygame.display.set_mode((1, 1))
    DESTINO.mkdir(parents=True, exist_ok=True)
    for folha, nomes in FOLHAS.items():
        origem = BRUTO / f"{folha}.png"
        if not origem.exists():
            print("falta a folha", folha)
            continue
        for nome, objeto in zip(nomes, cortar(pygame.image.load(str(origem)).convert_alpha())):
            if objeto is None:
                print("  casa vazia:", folha, nome)
                continue
            pygame.image.save(no_lado(objeto, LADO), str(DESTINO / f"{nome}.png"))
        print("ataques de", folha)
    acido = DESTINO / "poca_de_acido.png"
    if acido.exists():
        pygame.image.save(repintar(pygame.image.load(str(acido)).convert_alpha(), 24),
                          str(DESTINO / "poca_de_sopa.png"))
    loira = RAIZ / "assets" / "sprites" / "loira" / "andar-8.png"
    if loira.exists():
        tira = pygame.image.load(str(loira)).convert_alpha()
        quadro = round(tira.get_width() / 8 * ALTURA_DA_LOIRINHA / tira.get_height())
        pasta = RAIZ / "assets" / "sprites" / "loirinha"
        pasta.mkdir(parents=True, exist_ok=True)
        pygame.image.save(pygame.transform.smoothscale(tira, (quadro * 8, ALTURA_DA_LOIRINHA)),
                          str(pasta / "andar-8.png"))
        print("loirinhas")


if __name__ == "__main__":
    montar()
