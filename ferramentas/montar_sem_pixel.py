"""Monta a arte no estilo liso (sem pixels) a partir das folhas em nova_arte/_bruto/sem_pixel/ (fora do git).

- chefes/<nome>_v<n>.png -> assets/chefes/<nome>.png (ilustração da apresentação, 720x900)
- crupies/<nome>.png    -> assets/crupies/<nome>/<expressão>.png (folha de 4 poses da cintura para cima, separada
                           pelos pedaços ligados do desenho; todas na mesma altura)
- sprites/<pasta>_<animação>_<n>q.png -> assets/sprites/<pasta>/<animação>-<n>.png (tira da partida: os quadros
                           são lidos linha por linha, espelhados para olhar para a direita e postos na mesma
                           altura e na mesma linha de chão)

Uso: .venv/bin/python ferramentas/montar_sem_pixel.py
"""
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "nova_arte" / "_bruto" / "sem_pixel"
CHEFES = ("calculo", "arquitetura_ed", "td_poo")
CRUPIES = ("gamer", "mestre_de_rpg", "monitor")
EXPRESSOES = ("espera", "torcida", "riso", "choro")      # a ordem das poses na folha
ALTURA_CHEFE, ALTURA_CRUPIE = 900, 360
# folha, pasta, animação, quadros, linhas da folha, altura na tela
TIRAS = (
    ("professor_computacao_v4_parado_4q.png", "professor_computacao", "parado", 4, 1, 168),
    ("professor_computacao_v4_andar_8q.png", "professor_computacao", "andar", 8, 2, 168),
    ("professora_v7_parado_4q.png", "professora", "parado", 4, 1, 162),
    ("professora_v7_andar_8q.png", "professora", "andar", 8, 2, 162),
)


def na_altura(img, altura):
    largura = round(img.get_width() * altura / img.get_height())
    return pygame.transform.smoothscale(img, (largura, altura))


def cortar_poses(folha, quantidade, linhas=1):
    """Separa as poses pelos pedaços ligados do desenho: os maiores são os corpos; lágrimas, gotas e riscos
    soltos vão para o corpo mais próximo. Devolve, da esquerda para a direita, uma imagem por pose."""
    mascara = pygame.mask.from_surface(folha, 40)
    pedacos = sorted(mascara.connected_components(30), key=lambda m: m.count(), reverse=True)
    faixa = folha.get_height() / linhas
    corpos = sorted(pedacos[:quantidade], key=lambda m: (int(m.centroid()[1] // faixa), m.centroid()[0]))
    grupos = [[corpo] for corpo in corpos]
    for solto in pedacos[quantidade:]:
        x, y = solto.centroid()
        mais_perto = min(range(len(corpos)), key=lambda i: (corpos[i].centroid()[0] - x) ** 2
                         + (corpos[i].centroid()[1] - y) ** 2)
        grupos[mais_perto].append(solto)
    poses = []
    for grupo in grupos:
        junto = pygame.mask.Mask(folha.get_size())
        for pedaco in grupo:
            junto.draw(pedaco, (0, 0))
        pose = folha.copy()
        apagar = junto.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))
        pose.blit(apagar, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        poses.append(pose)
    return poses


def montar():
    pygame.init()
    pygame.display.set_mode((1, 1))
    for nome in CHEFES:
        versoes = sorted((BRUTO / "chefes").glob(f"{nome}_v*.png"))       # a versão mais nova vale
        origem = versoes[-1] if versoes else BRUTO / "chefes" / f"{nome}_v2.png"
        if origem.exists():
            pygame.image.save(na_altura(pygame.image.load(str(origem)).convert_alpha(), ALTURA_CHEFE),
                              str(RAIZ / "assets" / "chefes" / f"{nome}.png"))
            print("chefe", nome)
    for nome in CRUPIES:
        origem = BRUTO / "crupies" / f"{nome}.png"
        if not origem.exists():
            continue
        folha = pygame.image.load(str(origem)).convert_alpha()
        base = folha.get_bounding_rect().bottom              # todas as poses assentam na mesma linha
        topo = folha.get_bounding_rect().top
        destino = RAIZ / "assets" / "crupies" / nome
        destino.mkdir(parents=True, exist_ok=True)
        for expressao, pose in zip(EXPRESSOES, cortar_poses(folha, len(EXPRESSOES))):
            caixa = pose.get_bounding_rect()
            recorte = pose.subsurface((caixa.x, topo, caixa.w, base - topo)).copy()
            pygame.image.save(na_altura(recorte, ALTURA_CRUPIE), str(destino / f"{expressao}.png"))
        print("crupiê", nome)
    for folha, pasta, animacao, quadros, linhas, altura in TIRAS:
        origem = BRUTO / "sprites" / folha
        if origem.exists():
            montar_tira(pygame.image.load(str(origem)).convert_alpha(), pasta, animacao, quadros, linhas, altura)
            print("tira", pasta, animacao)


def montar_tira(folha, pasta, animacao, quadros, linhas, altura):
    """Recorta os quadros, vira para a direita e grava a tira com células iguais e os pés na mesma linha."""
    recortes = []
    for pose in cortar_poses(folha, quadros, linhas):
        recortes.append(pygame.transform.flip(pose.subsurface(pose.get_bounding_rect()).copy(), True, False))
    fator = altura / max(r.get_height() for r in recortes)
    recortes = [pygame.transform.smoothscale(r, (max(1, round(r.get_width() * fator)), max(1, round(r.get_height() * fator))))
                for r in recortes]
    largura = max(r.get_width() for r in recortes) + 2
    tira = pygame.Surface((largura * quadros, altura), pygame.SRCALPHA)
    for i, r in enumerate(recortes):
        tira.blit(r, (i * largura + (largura - r.get_width()) // 2, altura - r.get_height()))
    destino = RAIZ / "assets" / "sprites" / pasta
    destino.mkdir(parents=True, exist_ok=True)
    for antiga in destino.glob(f"{animacao}-*.png"):          # a tira antiga, com outro número de quadros
        antiga.unlink()
    pygame.image.save(tira, str(destino / f"{animacao}-{quadros}.png"))


if __name__ == "__main__":
    montar()
