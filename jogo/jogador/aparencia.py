"""Aparência do aluno: tom de pele, cor do cabelo, do moletom e da calça.

A arte dos alunos não muda: as cores são trocadas na hora de carregar os sprites.
Cada pixel é classificado (pele, cabelo, moletom, calça, boné) pela cor original e
recebe o novo tom mantendo o sombreado (a claridade relativa do pixel).
"""
import numpy as np
import pygame

# (nome, cor) - "Original" (None) deixa como foi desenhado
TONS_DE_PELE = (
    ("Original", None),
    ("Muito clara", (255, 226, 204)),
    ("Clara", (240, 196, 160)),
    ("Média", (210, 154, 110)),
    ("Morena", (165, 108, 70)),
    ("Escura", (105, 66, 44)),
)
CORES_DE_CABELO = (
    ("Original", None),
    ("Preto", (52, 44, 50)),
    ("Castanho claro", (150, 100, 60)),
    ("Loiro", (236, 196, 100)),
    ("Ruivo", (200, 90, 40)),
    ("Grisalho", (180, 180, 186)),
    ("Azul", (70, 110, 220)),
    ("Rosa", (236, 110, 170)),
)
CORES_DE_MOLETOM = (
    ("Original", None),
    ("Verde", (50, 150, 80)),
    ("Laranja", (250, 140, 30)),
    ("Azul", (50, 100, 210)),
    ("Vermelho", (210, 40, 50)),
    ("Roxo", (130, 70, 200)),
    ("Preto", (52, 50, 60)),
    ("Branco", (236, 236, 240)),
    ("Amarelo", (245, 205, 50)),
)
CORES_DE_CALCA = (
    ("Original", None),
    ("Preta", (50, 50, 58)),
    ("Cinza", (130, 132, 140)),
    ("Cáqui", (190, 165, 115)),
    ("Verde-oliva", (100, 110, 60)),
    ("Vinho", (120, 40, 60)),
)

GENEROS = (("Masculino", None), ("Feminino", None))

CORES = ("pele", "cabelo", "moletom", "calca")    # as partes que trocam de cor

OPCOES = {
    "genero": GENEROS,
    "pele": TONS_DE_PELE,
    "cabelo": CORES_DE_CABELO,
    "moletom": CORES_DE_MOLETOM,
    "calca": CORES_DE_CALCA,
}


class Aparencia:
    """Escolhas do aluno: gênero e cores. Cada atributo só aceita uma das opções da sua lista."""

    PARTES = tuple(OPCOES)

    def __init__(self, pele="Original", cabelo="Original", moletom="Original", calca="Original",
                 genero="Masculino"):
        self._escolhas = {}
        self.genero = genero
        self.pele = pele
        self.cabelo = cabelo
        self.moletom = moletom
        self.calca = calca

    def _definir(self, parte, nome):
        nomes = [n for n, _ in OPCOES[parte]]
        if nome not in nomes:
            raise ValueError(f"{parte} inválido: {nome!r} (opções: {', '.join(nomes)})")
        self._escolhas[parte] = nome

    @property
    def genero(self):
        return self._escolhas["genero"]

    @genero.setter
    def genero(self, nome):
        self._definir("genero", nome)

    @property
    def feminino(self):
        return self._escolhas["genero"] == "Feminino"

    @property
    def pele(self):
        return self._escolhas["pele"]

    @pele.setter
    def pele(self, nome):
        self._definir("pele", nome)

    @property
    def cabelo(self):
        return self._escolhas["cabelo"]

    @cabelo.setter
    def cabelo(self, nome):
        self._definir("cabelo", nome)

    @property
    def moletom(self):
        return self._escolhas["moletom"]

    @moletom.setter
    def moletom(self, nome):
        self._definir("moletom", nome)

    @property
    def calca(self):
        return self._escolhas["calca"]

    @calca.setter
    def calca(self, nome):
        self._definir("calca", nome)

    def escolha(self, parte):
        return self._escolhas[parte]

    def cor(self, parte):
        """Cor alvo da parte, ou None se ficar como o original."""
        return dict(OPCOES[parte])[self._escolhas[parte]]

    def trocar(self, parte, passo):
        """Vai para a opção anterior (-1) ou seguinte (+1) da parte, dando a volta na lista."""
        nomes = [n for n, _ in OPCOES[parte]]
        indice = (nomes.index(self._escolhas[parte]) + passo) % len(nomes)
        self._definir(parte, nomes[indice])

    @property
    def original(self):
        """Todas as cores como no desenho (o gênero não conta: não é cor)."""
        return all(self.cor(parte) is None for parte in CORES)

    def restaurar_cores(self):
        for parte in CORES:
            self._definir(parte, "Original")

    def chave(self):
        """As escolhas na ordem do construtor: Aparencia(*a.chave()) == a."""
        return tuple(self._escolhas[parte] for parte in (*CORES, "genero"))

    def __eq__(self, outra):
        return isinstance(outra, Aparencia) and self.chave() == outra.chave()

    def __hash__(self):
        return hash(self.chave())

    def __str__(self):
        return ", ".join(f"{parte}: {self._escolhas[parte]}" for parte in self.PARTES)

    # Recoloração

    def recolorir(self, imagem, moletom_original="verde", cabelo_natural=True):
        """Cópia da imagem com as cores trocadas. `moletom_original` diz como achar o moletom
        na arte ("verde" ou "laranja"); `cabelo_natural=False` não mexe no cabelo (Super Saiyajin)."""
        if self.original:
            return imagem
        rgb = pygame.surfarray.array3d(imagem).astype(np.float32) / 255
        alfa = pygame.surfarray.array_alpha(imagem)
        mascaras = classificar(rgb, alfa, moletom_original, cabelo_natural)
        alvos = {"pele": self.cor("pele"), "cabelo": self.cor("cabelo"), "moletom": self.cor("moletom"),
                 "bone": self.cor("moletom"), "calca": self.cor("calca")}
        h, s, v = rgb_para_hsv(rgb)
        for parte, cor in alvos.items():
            mascara = mascaras[parte]
            if cor is None or not mascara.any():
                continue
            ref_s = max(float(np.median(s[mascara])), 1e-3)
            ref_v = max(float(np.median(v[mascara])), 1e-3)
            alvo_h, alvo_s, alvo_v = (float(x.item()) for x in rgb_para_hsv(np.array(cor, np.float32) / 255))
            h[mascara] = alvo_h
            s[mascara] = np.clip(s[mascara] / ref_s * alvo_s, 0, 1)
            v[mascara] = np.clip(v[mascara] / ref_v * alvo_v, 0, 1)
        nova = imagem.copy()
        pygame.surfarray.blit_array(nova, (hsv_para_rgb(h, s, v) * 255).round().astype(np.uint8))
        canal_alfa = pygame.surfarray.pixels_alpha(nova)
        canal_alfa[:] = alfa
        del canal_alfa   # libera a trava da superfície
        return nova


_vestidas = {}


def vestir_animacoes(animacoes, aparencia, moletom_original="verde", cabelo_natural=True):
    """Conjunto de animações com as cores da aparência (guardado em cache)."""
    if aparencia is None or aparencia.original:
        return animacoes
    from jogo.nucleo.animacao import Animacao
    chave = (id(animacoes), aparencia.chave(), moletom_original, cabelo_natural)
    if chave not in _vestidas:
        _vestidas[chave] = (animacoes, {
            nome: Animacao([aparencia.recolorir(q, moletom_original, cabelo_natural) for q in animacao.quadros],
                           animacao.fps, animacao.repetir)
            for nome, animacao in animacoes.items()})
    return _vestidas[chave][1]


def rgb_para_hsv(rgb):
    """Matiz em graus (0-360), saturação e valor (0-1), para um array (..., 3)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maximo = rgb.max(-1)
    minimo = rgb.min(-1)
    delta = np.maximum(maximo - minimo, 1e-6)
    matiz = np.where(maximo == r, ((g - b) / delta) % 6,
                     np.where(maximo == g, (b - r) / delta + 2, (r - g) / delta + 4)) * 60
    saturacao = np.where(maximo > 0, (maximo - minimo) / np.maximum(maximo, 1e-6), 0)
    return matiz, saturacao, maximo


def hsv_para_rgb(h, s, v):
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    m = v - c
    setor = (h // 60).astype(int) % 6
    zeros = np.zeros_like(c)
    tabela = [(c, x, zeros), (x, c, zeros), (zeros, c, x), (zeros, x, c), (x, zeros, c), (c, zeros, x)]
    rgb = np.zeros(h.shape + (3,), np.float32)
    for i, (r, g, b) in enumerate(tabela):
        sel = setor == i
        rgb[sel] = np.stack([r[sel], g[sel], b[sel]], -1)
    return rgb + m[..., None]


def crescer(semente, permitido):
    """Região conectada (vizinhança de 4) a partir da semente, andando só por pixels permitidos."""
    regiao = semente & permitido
    while True:
        vizinhos = regiao.copy()
        vizinhos[1:, :] |= regiao[:-1, :]
        vizinhos[:-1, :] |= regiao[1:, :]
        vizinhos[:, 1:] |= regiao[:, :-1]
        vizinhos[:, :-1] |= regiao[:, 1:]
        vizinhos &= permitido
        if (vizinhos == regiao).all():
            return regiao
        regiao = vizinhos


def preencher_buracos(mascara):
    """Inclui os pixels cercados pela máscara (ex.: os reflexos claros no meio do cabelo)."""
    fora = np.zeros_like(mascara)
    fora[0, :] = fora[-1, :] = True
    fora[:, 0] = fora[:, -1] = True
    fora = crescer(fora, ~mascara)
    return mascara | ~fora


def classificar(rgb, alfa, moletom_original="verde", cabelo_natural=True):
    """Máscaras booleanas de cada parte do aluno.

    A cor sozinha confunde partes parecidas (olhos e sobrancelhas têm o tom do cabelo; bochecha e
    sombra da pele têm o tom do moletom laranja). Por isso cada parte é a REGIÃO CONECTADA de pixels
    da sua cor que nasce no lugar certo do corpo: o cabelo a partir do topo da cabeça, o moletom a
    partir do tronco, a calça a partir das pernas. O rosto fica separado pelo contorno e pela pele.

    Os arrays vêm de pygame.surfarray, então o primeiro eixo é x e o segundo é y.
    """
    h, s, v = rgb_para_hsv(rgb)
    visivel = alfa > 128
    altura = rgb.shape[1]
    y = np.broadcast_to(np.arange(altura)[None, :] / altura, alfa.shape)
    contorno = v < 0.08
    base = visivel & ~contorno
    topo = visivel.any(0).argmax() / altura          # primeira linha com pixel visível

    tom_de_pele = (h >= 5) & (h < 40) & (s >= 0.2) & (s < 0.8) & (v > 0.55)
    cor_de_bone = base & ((h < 12) | (h >= 330)) & (s >= 0.55) & (v > 0.2) & (y < 0.45)
    bone = crescer(cor_de_bone & (y < topo + 0.1), cor_de_bone)   # só o boné, não a boca nem a bochecha
    if bone.any():
        # Parte de trás do boné: o vermelho que aparece entre as mechas e a sombra puxada para o marrom,
        # bem mais saturada que o cabelo (vizinhança de 8, porque a sombra encosta no boné pela diagonal).
        alto = y < topo + 0.17
        bone |= cor_de_bone & alto
        aba_de_tras = base & alto & ((h < 30) | (h >= 330)) & (s >= 0.78) & (v >= 0.45) & (v < 0.78)
        aba_de_tras |= base & (y < 0.35) & ((h < 20) | (h >= 330)) & (s >= 0.75)   # sombra sob a aba
        aba_de_tras |= base & (y < topo + 0.1) & (h < 30) & (s >= 0.5) & (v >= 0.78)   # brilho no alto do boné
        while True:
            novos = _vizinhos8(bone) & aba_de_tras & ~bone
            if not novos.any():
                break
            bone |= novos
        # contorno vermelho-escuro do boné (bem escuro e saturado; o cabelo é mais claro)
        contorno_do_bone = visivel & ((h < 15) | (h >= 330)) & (s >= 0.7) & (v < 0.25) & (y < 0.3)
        perto = _vizinhos(bone)
        bone |= perto & contorno_do_bone

    calca_cor = base & (h >= 190) & (h < 250) & (s > 0.2)
    calca = crescer(calca_cor & (y > 0.7), calca_cor & (y > 0.5))

    if moletom_original == "verde":
        moletom_cor = base & (h >= 90) & (h < 180) & (s > 0.2)
        sombra_do_moletom = moletom_cor
    else:   # laranja: bem mais saturado que a pele
        moletom_cor = base & (h >= 5) & (h < 45) & (s >= 0.85) & (v > 0.4)
        sombra_do_moletom = base & (h >= 5) & (h < 50) & (s >= 0.6) & (v > 0.3) & ~(tom_de_pele & (s < 0.78))
    tronco = (y > 0.5) & (y < 0.65)
    capuz = (y > 0.35) & (y < 0.5) & (s >= 0.95)    # o capuz fica atrás da alça da mochila, separado do tronco
    # Super Saiyajin: o cabelo dourado tem matiz vizinha à do moletom laranja e à da pele. Ele não troca de
    # cor, então só precisa ficar fora das outras partes: a região dourada que nasce no alto da cabeça.
    dourado = np.zeros_like(base)
    if not cabelo_natural:
        borda = ~visivel
        for _ in range(2):
            borda |= _vizinhos(borda)
        amarelo = base & (h >= 33) & (h < 68) & (s >= 0.3) & (v >= 0.35)
        sombra_dourada = base & (h >= 22) & (h < 33) & (s >= 0.6) & (v >= 0.35) & (y < 0.36)   # pele é menos saturada
        cor_dourada = amarelo | sombra_dourada
        dourado = crescer(cor_dourada & ((y < topo + 0.08) | (borda & (y < 0.45))), cor_dourada)
        dourado = preencher_buracos(dourado) & base & (y < 0.8)
    moletom = crescer(moletom_cor & (tronco | capuz) & ~dourado,
                      (moletom_cor | sombra_do_moletom) & (y > 0.22) & ~dourado)   # inclui o capuz

    # Olhos: o escuro em volta do branco do olho, na altura do rosto. A íris tem tom de cabelo e às
    # vezes encosta na franja; sem isso o cabelo "escorre" para dentro do olho.
    faixa_do_rosto = (y > topo + 0.2) & (y < 0.45)
    branco_do_olho = visivel & (s < 0.2) & (v > 0.8) & (y > topo + 0.2) & (y < 0.38)   # acima da gola
    perto_do_bone = bone.copy()
    for _ in range(2):   # o forro claro da aba do boné não é olho
        perto_do_bone |= _vizinhos(perto_do_bone)
    branco_do_olho &= ~perto_do_bone
    olhos = branco_do_olho.copy()
    for _ in range(3):
        olhos |= _vizinhos(olhos)
    olhos &= faixa_do_rosto & (v < 0.6)

    cabelo = np.zeros_like(base)
    if cabelo_natural:
        cor_de_cabelo = ~olhos & base & ~bone & ((h >= 270) | (h < 55)) & (s >= 0.1) & (v < 0.45) & (y < 0.5) \
            & ~tom_de_pele
        # Sementes: o topo da cabeça e a borda da silhueta (as mechas do lado). A fita do boné pode
        # separar o cabelo do topo do resto; olhos e sobrancelhas nunca encostam na borda.
        borda = ~visivel
        for _ in range(2):
            borda |= _vizinhos(borda)
        sementes = cor_de_cabelo & ((y < topo + 0.08) | (borda & (y < 0.42)))
        cabelo = crescer(sementes, cor_de_cabelo)
        cabelo = preencher_buracos(cabelo) & base & ~bone & (y < 0.5)
        if bone.any():   # a fita clara da regulagem do boné não é cabelo
            cabelo &= ~((s < 0.25) & (v > 0.6) & (y < topo + 0.17))
        cabelo &= ~moletom
        # pele da testa que aparece entre as mechas da franja (inclusive a sombra da franja sobre ela)
        # Matiz típica deste cabelo (no topo da cabeça, onde só há cabelo).
        topo_do_cabelo = cabelo & (y < topo + 0.12)
        matiz_cabelo = _matiz_media(h[topo_do_cabelo]) if topo_do_cabelo.any() else 0.0
        longe_do_cabelo = _distancia_matiz(h, matiz_cabelo) > 15
        # Pele da testa e a sombra da franja sobre ela: tom de pele (mesmo escuro) e matiz diferente da do
        # cabelo. Sem isso a sombra na testa e no rosto pegava a cor do cabelo e não a da pele.
        sombra_de_pele = (h >= 8) & (h < 40) & (s >= 0.35) & longe_do_cabelo
        cor_de_testa = (tom_de_pele & (v > 0.7)) | ((h >= 14) & (h < 40) & (s >= 0.35) & (v > 0.38)) | sombra_de_pele
        testa = cor_de_testa & _faixa_da_testa(branco_do_olho, tom_de_pele, y, topo, v)
        cabelo &= ~testa

    livre = base & tom_de_pele & ~moletom & ~cabelo & ~bone & ~calca & ~dourado
    # Rosto e pescoço até a gola; mãos a partir de baixo. Os cordões do capuz têm tom de pele e
    # encostam no pescoço, então a pele não desce da gola para o peito.
    rosto = crescer(livre & (y > topo + 0.2) & (y < 0.45), livre & (y < 0.45))
    maos = np.zeros_like(livre)
    sobra = livre & (y > 0.45) & (y < 0.8)
    while sobra.any():   # cada pedaço separado: a mão começa embaixo; o cordão desce do peito
        x0, y0 = np.argwhere(sobra)[0]
        pedaco = crescer(np.zeros_like(sobra) | (np.arange(sobra.shape[0])[:, None] == x0)
                         & (np.arange(sobra.shape[1])[None, :] == y0), sobra)
        sobra &= ~pedaco
        if y[pedaco].min() >= 0.555:
            maos |= pedaco
    pele = rosto | maos
    if cabelo_natural:   # pontas claras do cabelo, encostadas nele e longe do rosto
        pontas = base & ~pele & ~moletom & ~bone & ~calca & ((h < 60) | (h >= 300)) & (y < topo + 0.2)
        cabelo = crescer(cabelo, cabelo | pontas)
    pele &= ~cabelo
    if cabelo_natural:
        pele |= testa & base & ~moletom & ~bone
    # Sobras na cabeça (blush, transição entre mecha e testa): ficam com a parte vizinha.
    quente = (h < 45) | (h >= 330)
    resto = base & quente & (y < 0.43) & ~(pele | cabelo | moletom | bone | calca | dourado)   # até o pescoço
    for _ in range(4):
        perto_da_pele = _vizinhos(pele) & resto
        perto_do_cabelo = _vizinhos(cabelo) & resto & ~perto_da_pele & (y < 0.38) if cabelo_natural \
            else perto_da_pele & False
        if not (perto_da_pele.any() or perto_do_cabelo.any()):
            break
        pele |= perto_da_pele
        cabelo |= perto_do_cabelo
        resto &= ~(perto_da_pele | perto_do_cabelo)
    cabelo &= ~olhos & ~pele      # cílios, íris e pele nunca levam a cor do cabelo
    if bone.any():   # contorno escuro entre o boné e o fundo: é do boné, não do cabelo
        claro = cabelo & (v >= 0.25)
        contorno_do_bone = cabelo & (v < 0.25) & _vizinhos8(bone) & ~_vizinhos8(claro)
        cabelo &= ~contorno_do_bone
        bone = bone | contorno_do_bone
    return {"pele": pele, "cabelo": cabelo, "moletom": moletom, "calca": calca, "bone": bone}


def _faixa_da_testa(branco_do_olho, tom_de_pele, y, topo, v):
    """Onde fica a testa: logo acima dos olhos, na largura do rosto.

    Os reflexos do cabelo têm a mesma cor da pele; o que os separa da testa é o lugar. A largura do
    rosto vem da pele na altura dos olhos. Com os olhos fechados (piscando), a altura dos olhos é a
    primeira linha do rosto com bastante pele clara.
    """
    altura = branco_do_olho.shape[1]
    if branco_do_olho.any():
        olho_topo = np.nonzero(branco_do_olho)[1].min()
    else:
        pele_clara = (tom_de_pele & (v > 0.7) & (y > topo + 0.15) & (y < 0.4)).sum(0)
        linhas = np.nonzero(pele_clara >= 6)[0]
        if not len(linhas):
            return np.zeros_like(tom_de_pele)
        olho_topo = linhas[0] + 1
    linhas_dos_olhos = slice(olho_topo, olho_topo + max(3, altura // 20))
    colunas_com_pele = np.nonzero(tom_de_pele[:, linhas_dos_olhos].any(1))[0]
    colunas = np.zeros(branco_do_olho.shape[0], bool)
    if len(colunas_com_pele):
        colunas[colunas_com_pele.min(): colunas_com_pele.max() + 1] = True
    return colunas[:, None] & (y >= olho_topo / altura - 0.075) & (y <= olho_topo / altura + 0.02)


def _distancia_matiz(h, referencia):
    """Distância angular entre matizes (0 a 180 graus)."""
    d = np.abs(h - referencia) % 360
    return np.minimum(d, 360 - d)


def _matiz_media(matizes):
    """Média circular das matizes em graus (350 e 10 dão 0, não 180)."""
    rad = np.radians(matizes)
    return float(np.degrees(np.arctan2(np.sin(rad).mean(), np.cos(rad).mean())) % 360)


def _vizinhos8(mascara):
    """Pixels com algum vizinho (8, contando as diagonais) dentro da máscara."""
    v = _vizinhos(mascara)
    v[1:, 1:] |= mascara[:-1, :-1]
    v[:-1, :-1] |= mascara[1:, 1:]
    v[1:, :-1] |= mascara[:-1, 1:]
    v[:-1, 1:] |= mascara[1:, :-1]
    return v


def _vizinhos(mascara):
    """Pixels com algum vizinho (4) dentro da máscara."""
    v = np.zeros_like(mascara)
    v[1:, :] |= mascara[:-1, :]
    v[:-1, :] |= mascara[1:, :]
    v[:, 1:] |= mascara[:, :-1]
    v[:, :-1] |= mascara[:, 1:]
    return v
