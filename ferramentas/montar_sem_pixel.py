"""Monta a arte no estilo liso (sem pixels) a partir das folhas em nova_arte/_bruto/sem_pixel/ (fora do git).

- chefes/<nome>_v<n>.png -> assets/chefes/<nome>.png (ilustração da apresentação, 720x900)
- crupies/<nome>.png    -> assets/crupies/<nome>/<expressão>.png (folha de 4 poses da cintura para cima, separada
                           pelos pedaços ligados do desenho; todas na mesma altura)
- sprites/<pasta>_<animação>_<n>q.png -> assets/sprites/<pasta>/<animação>-<n>.png (tira da partida: os quadros
                           são lidos linha por linha, espelhados para olhar para a direita e postos na mesma
                           altura e na mesma linha de chão)
- <classe>.png           -> assets/retratos/<classe>.png (arte principal do aluno, na matrícula),
                           assets/rostos/<classe>.png (o rosto do HUD, um quadrado em volta da cabeça) e
                           assets/fotos/<classe>.png (a foto 3x4 da carteirinha, de pé, com a cabeça enchendo o quadro)
- chibis/<classe>_andar_8q.png, _parado_4q.png e dano_a_4.png / dano_b_4.png -> os bonecos dos alunos na
                           partida (assets/sprites/<classe>/andar-8, parado-4 e dano-1), chibis sem pixels

Uso: .venv/bin/python ferramentas/montar_sem_pixel.py
"""
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import numpy  # noqa: E402
import pygame  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "nova_arte" / "_bruto" / "sem_pixel"
# o de Cálculo não entra aqui: a ilustração aprovada dele vem de nova_arte/_bruto/ilustracoes/calculo_flavio_v2.png
CHEFES = ("arquitetura_ed", "td_poo")
CRUPIES = ("gamer", "mestre_de_rpg", "monitor")
ALUNOS = ("otaku", "programador", "mestre_de_rpg", "monitor", "gamer", "calouro", "cara_da_carona")
ALTURA_RETRATO, LADO_DO_ROSTO = 900, 160
FOTO = (176, 232)                # a foto 3x4 da carteirinha (o dobro do tamanho em que aparece)
# quanto da altura do desenho é a cabeça (com o cabelo): quem tem pouco cabelo tem a cabeça menor no desenho,
# e a foto precisa chegar mais perto para ele não sair pequeno
CABECA = {"otaku": 0.19, "programador": 0.20, "mestre_de_rpg": 0.19, "monitor": 0.18, "gamer": 0.20,
          "calouro": 0.16, "cara_da_carona": 0.19}
# quanto o meio da cabeça fica para a direita do meio medido, em frações da cabeça (o dado que o Mestre segura
# ao lado do rosto puxa a medida para a esquerda)
DESVIO_DA_CABECA = {"mestre_de_rpg": 0.42}
# boneco da partida: pasta -> altura na tela (a careta de dano é um pouco mais alta, por causa das estrelinhas)
CHIBIS = {"otaku": 72, "programador": 72, "mestre_de_rpg": 72, "monitor": 72, "gamer": 72, "calouro": 72,
          "cara_da_carona": 72, "otaku_ssj": 82}
# folhas de dano: quatro bonecos diferentes por folha, da esquerda para a direita
DANOS = {"dano_a_4.png": ("otaku", "programador", "mestre_de_rpg", "monitor"),
         "dano_b_4.png": ("gamer", "calouro", "cara_da_carona", "otaku_ssj")}
ALTURA_NO_MENU = 108           # o boneco de 72 px aparece com 108 nas telas (matrícula, ranking, título)
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
    for nome in ALUNOS:
        versoes = sorted(BRUTO.glob(f"{nome}_v[0-9]*.png"))             # o retrato retocado vale
        origem = versoes[-1] if versoes else BRUTO / f"{nome}.png"
        if origem.exists():
            montar_aluno(pygame.image.load(str(origem)).convert_alpha(), nome)
            print("aluno", nome)
    for pasta, altura in CHIBIS.items():
        folhas = {}
        for animacao, quadros, linhas in (("parado", 4, 1), ("andar", 8, 2)):
            origem = BRUTO / "chibis" / "v2" / f"{pasta}_{animacao}_{quadros}q.png"     # a versão retocada vale
            if not origem.exists():
                origem = BRUTO / "chibis" / f"{pasta}_{animacao}_{quadros}q.png"
            if origem.exists():
                folhas[animacao] = (pygame.image.load(str(origem)).convert_alpha(), quadros, linhas)
        montar_boneco(folhas, altura, RAIZ / "assets" / "sprites" / pasta)
        montar_boneco(folhas, round(altura * ALTURA_NO_MENU / 72), RAIZ / "assets" / "retratos" / "chibis" / pasta)
        parado = RAIZ / "assets" / "sprites" / pasta / "parado-4.png"            # a imagem solta da classe
        if parado.exists():
            tira = pygame.image.load(str(parado)).convert_alpha()
            quadro = tira.subsurface((0, 0, tira.get_width() // 4, tira.get_height()))
            pygame.image.save(quadro.subsurface(quadro.get_bounding_rect()), str(RAIZ / "assets" / "sprites" / f"{pasta}.png"))
        print("chibi", pasta)
    for folha, pastas in DANOS.items():
        origem = BRUTO / "chibis" / folha
        if origem.exists():
            poses = cortar_poses(sem_nevoa(pygame.image.load(str(origem)).convert_alpha()), len(pastas))
            for pasta, pose in zip(pastas, poses):
                recorte = pygame.transform.flip(pose.subsurface(pose.get_bounding_rect()).copy(), True, False)
                pygame.image.save(na_altura(recorte, CHIBIS[pasta] + 4), str(RAIZ / "assets" / "sprites" / pasta / "dano-1.png"))
    for folha, pasta, animacao, quadros, linhas, altura in TIRAS:
        origem = BRUTO / "sprites" / folha
        if origem.exists():
            montar_tira(pygame.image.load(str(origem)).convert_alpha(), pasta, animacao, quadros, linhas, altura)
            print("tira", pasta, animacao)


def montar_aluno(arte, nome):
    """Grava o retrato (o desenho inteiro, sem as margens vazias) e o rosto (um quadrado em volta da cabeça)."""
    figura = arte.subsurface(arte.get_bounding_rect()).copy()
    pygame.image.save(na_altura(figura, ALTURA_RETRATO), str(RAIZ / "assets" / "retratos" / f"{nome}.png"))
    # busto: a cabeça inteira com folga em cima e dos lados, até os ombros (a cabeça ocupa perto de um sexto da
    # altura do desenho; o quadrado pega um terço), centrado no meio do cabelo e não no do corpo
    lado = round(figura.get_height() * 0.30)
    topo_da_cabeca = pygame.mask.from_surface(figura.subsurface((0, 0, figura.get_width(), lado // 3)), 40)
    centro_x = round(topo_da_cabeca.centroid()[0] + DESVIO_DA_CABECA.get(nome, 0) * figura.get_height() * CABECA[nome])
    rosto = pygame.Surface((lado, lado), pygame.SRCALPHA)
    rosto.blit(figura, (lado // 2 - centro_x, round(lado * 0.08)))
    pygame.image.save(pygame.transform.smoothscale(rosto, (LADO_DO_ROSTO, LADO_DO_ROSTO)),
                      str(RAIZ / "assets" / "rostos" / f"{nome}.png"))
    # foto 3x4: a cabeça ocupa dois terços da largura, com uma folga em cima; o resto são os ombros
    cabeca = figura.get_height() * CABECA[nome]
    largura = round(cabeca / 0.66)
    altura = round(largura * FOTO[1] / FOTO[0])
    foto = pygame.Surface((largura, altura), pygame.SRCALPHA)
    foto.blit(figura, (largura // 2 - centro_x, round(altura * 0.07)))
    (RAIZ / "assets" / "fotos").mkdir(exist_ok=True)
    pygame.image.save(pygame.transform.smoothscale(foto, FOTO), str(RAIZ / "assets" / "fotos" / f"{nome}.png"))


def sem_nevoa(folha, limiar=110):
    """Apaga o que é quase transparente em volta do desenho (brilhos e névoas, que grudam um quadro no outro e
    alargam a célula) e, ao contrário, fecha o que é quase transparente por dentro dele: a folha às vezes vem
    com o branco dos olhos ou a lente dos óculos meio transparente, e isso viraria um buraco no boneco."""
    w, h = folha.get_size()
    firme = pygame.mask.from_surface(folha, limiar)
    vazio = firme.copy()
    vazio.invert()
    fora = pygame.mask.Mask((w, h))                         # o vazio ligado à borda da folha: o lado de fora
    for pedaco in vazio.connected_components():
        caixa = pedaco.get_bounding_rects()[0]
        if caixa.left == 0 or caixa.top == 0 or caixa.right == w or caixa.bottom == h:
            fora.draw(pedaco, (0, 0))
    limpa = folha.copy()
    alfa = pygame.surfarray.pixels_alpha(limpa)
    de_fora = pygame.surfarray.array_alpha(fora.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))) > 0
    original = alfa.copy()
    alfa[de_fora] = 0                                       # névoa do lado de fora some
    alfa[~de_fora & (original > 0)] = 255                   # por dentro, o que tinha cor fica opaco
    del alfa
    return limpa


def medir_boneco(pose):
    """O corpo (o maior pedaço ligado, sem gotas e brilhos soltos) e o meio da cabeça dele: o centro de massa da
    metade de cima, que não muda quando uma mecha de cabelo sai um pouco diferente de um quadro para outro."""
    corpo = max(pygame.mask.from_surface(pose, 110).connected_components(200), key=lambda m: m.count())
    caixa = corpo.get_bounding_rects()[0]
    cabeca = pygame.mask.Mask((caixa.w, int(caixa.h * 0.45)))
    cabeca.draw(corpo, (-caixa.left, -caixa.top))
    return caixa, caixa.left + cabeca.centroid()[0]


PESCOCO, EMENDA = (0.45, 0.60), 0.015      # faixa da altura do corpo onde procurar o pescoço, e a meia faixa de emenda


def altura_do_pescoco(pose, caixa):
    """Em que linha o pescoço está: a mais estreita do corpo entre o queixo e os ombros. É ali que a cabeça é
    emendada no corpo; mais acima, a emenda cai no queixo e ele fica mexendo de um quadro para o outro."""
    corpo = max(pygame.mask.from_surface(pose, 110).connected_components(200), key=lambda m: m.count())
    linhas = range(caixa.top + int(caixa.h * PESCOCO[0]), caixa.top + int(caixa.h * PESCOCO[1]))
    return min(linhas, key=lambda y: sum(corpo.get_at((x, y)) for x in range(caixa.left, caixa.right)))


def _matriz(sup):
    """A imagem como matriz (largura, altura, 4) de 0 a 1, com a cor já multiplicada pela transparência."""
    alfa = pygame.surfarray.array_alpha(sup).astype("float32")[..., None] / 255
    return numpy.concatenate([pygame.surfarray.array3d(sup).astype("float32") / 255 * alfa, alfa], axis=2)


def _imagem(matriz):
    alfa = matriz[..., 3:4]
    cor = numpy.where(alfa > 0, matriz[..., :3] / numpy.maximum(alfa, 1e-6), 0)
    sup = pygame.Surface(matriz.shape[:2], pygame.SRCALPHA)
    pygame.surfarray.pixels3d(sup)[:] = (cor * 255).clip(0, 255).astype("uint8")
    pygame.surfarray.pixels_alpha(sup)[:] = (alfa[..., 0] * 255).clip(0, 255).astype("uint8")
    return sup


def mesma_cabeca(quadros):
    """No andar a cabeça não muda, só balança; mas a folha vem com o cabelo e o rosto redesenhados de um jeito
    um pouco diferente em cada quadro, e a animação treme. Aqui a cabeça do primeiro quadro (com o que flutua em
    volta dela) é posta em todos os outros, no lugar onde a cabeça de cada um está, com uma emenda suave na
    linha do pescoço (medida no primeiro quadro: a cabeça é rígida, então a distância do topo até o pescoço é a
    mesma em todos). O corpo e as pernas de cada quadro ficam como vieram."""
    pose0, caixa0, meio0 = quadros[0]
    cabeca = _matriz(pose0)
    pescoco = altura_do_pescoco(pose0, caixa0) - caixa0.top
    saida = [quadros[0]]
    for pose, caixa, meio in quadros[1:]:
        dx, dy = round(meio - meio0), caixa.top - caixa0.top
        deslocada = numpy.roll(cabeca, (dx, dy), axis=(0, 1))
        corte = caixa.top + pescoco
        y = numpy.arange(pose.get_height(), dtype="float32")
        peso = numpy.clip((corte + caixa.h * EMENDA - y) / (2 * caixa.h * EMENDA), 0, 1)[None, :, None]
        junta = _imagem(deslocada * peso + _matriz(pose) * (1 - peso))
        saida.append((junta, *medir_boneco(junta)))
    return saida


def montar_boneco(folhas, altura, destino):
    """Monta todas as tiras de um boneco juntas, para ele não tremer nem mudar de tamanho ao trocar de quadro ou
    de animação. Cada quadro é recortado numa janela do mesmo tamanho presa à cabeça (o meio dela na horizontal,
    o topo dela na vertical): assim a cabeça cai exatamente no mesmo ponto em todos e quem se mexe são as pernas.
    Alinhar pelo contorno ou pelos pés faz a cabeça pular, porque cabos, gotas e a altura do pé mudam a cada
    passo. A cabeça fica no meio da célula, e a escala e a largura da célula valem para todas as animações."""
    if not folhas:
        return
    janelas, maior = {}, 0
    for animacao, (folha, n, linhas) in folhas.items():
        poses = [pygame.transform.flip(pose, True, False) for pose in cortar_poses(sem_nevoa(folha), n, linhas)]
        medidos = [(pose, *medir_boneco(pose)) for pose in poses]
        if animacao == "andar":
            medidos = mesma_cabeca(medidos)
        alturas = sorted(caixa.h for _, caixa, _ in medidos)
        escala = 1 / alturas[len(alturas) // 2]    # cada folha vem num tamanho: o corpo passa a ter a mesma altura
        totais = [pose.get_bounding_rect() for pose, _, _ in medidos]
        ancoras = [(round(meio), caixa.top) for _, caixa, meio in medidos]
        lado = max(max(x - total.left, total.right - x) for (x, _), total in zip(ancoras, totais))
        acima = max(y - total.top for (_, y), total in zip(ancoras, totais))          # gotas e faíscas de cima
        abaixo = max(caixa.bottom - y for (_, y), (_, caixa, _) in zip(ancoras, medidos))
        janelas[animacao] = (medidos, ancoras, lado, acima, abaixo, escala)
        maior = max(maior, (acima + abaixo) * escala)
    metade = max(lado * escala * altura / maior for _, _, lado, _, _, escala in janelas.values())
    largura = 2 * (int(metade) + 2)
    destino.mkdir(parents=True, exist_ok=True)
    for animacao, (medidos, ancoras, lado, acima, abaixo, escala) in janelas.items():
        k = escala * altura / maior
        tamanho = (max(1, round(2 * lado * k)), max(1, round((acima + abaixo) * k)))
        tira = pygame.Surface((largura * len(medidos), altura), pygame.SRCALPHA)
        for i, ((pose, _, _), (x, y)) in enumerate(zip(medidos, ancoras)):
            janela = pygame.Surface((2 * lado, acima + abaixo), pygame.SRCALPHA)
            janela.blit(pose, (lado - x, acima - y))
            img = pygame.transform.smoothscale(janela, tamanho)
            tira.blit(img, (i * largura + (largura - tamanho[0]) // 2, altura - tamanho[1]))
        for antiga in destino.glob(f"{animacao}-*.png"):
            antiga.unlink()
        pygame.image.save(tira, str(destino / f"{animacao}-{len(medidos)}.png"))


def montar_tira(folha, pasta, animacao, quadros, linhas, altura):
    """Recorta os quadros, vira para a direita e grava a tira com células iguais e os pés na mesma linha."""
    folha = sem_nevoa(folha)
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
