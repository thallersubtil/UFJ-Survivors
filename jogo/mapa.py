"""Mapas da partida: o chão, os obstáculos e as decorações da arena.

`Mapa` é abstrata; `MapaUFJ` é o Campus Jatobá gerado a partir de satélite e
OpenStreetMap (ferramentas/gerar_mapa.py), e `Cenario` (jogo/cenario.py) é o
pátio genérico usado quando o mapa da UFJ não está disponível.
"""
import json
import random
from collections import OrderedDict
from abc import ABC, abstractmethod

import pygame

from jogo.config import ESCALA_PIXEL, PASTA_ASSETS
from jogo.nucleo.animacao import Animador
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Decoracao(Entidade):
    """Enfeite (árvore, banco, poste, bandeira). Só existe para ser visto; pode ser animado."""

    grupo = "decoracao"
    camada = 1

    def __init__(self, posicao, imagem=None, altura=None, pasta=None):
        super().__init__(posicao, 0)
        self.imagem = imagem
        self.altura = altura
        self.animador = Animador(Recursos.animacoes_ou_imagem(pasta, imagem or "", altura or 48))

    def atualizar(self, dt, jogo):
        self.animador.atualizar(dt)

    def desenhar(self, tela, camera):
        imagem = self.animador.quadro_atual
        desenhar_sprite(tela, camera, imagem, self.posicao, sombra=imagem.get_width() < 200)


class FileiraDePlantacao(Entidade):
    """Uma fileira de pés de soja, milho ou trigo, em pé no talhão. É um objeto do mapa como as árvores:
    quem está atrás da fileira fica escondido por ela e quem está na frente passa por cima, o que dá
    volume à plantação. A posição é o meio da base da fileira."""

    grupo = "decoracao"
    camada = 1
    VARIACOES = 4
    APERTO = 0.62                # quanto de cada pé aparece antes do próximo (menor = fileira mais fechada)
    _tiras = {}                  # fileiras já montadas (cultura, largura, semente)

    def __init__(self, posicao, cultura, largura, semente):
        super().__init__(posicao, 0)
        self.cultura = cultura
        self.largura = largura
        self.semente = semente

    @property
    def imagem(self):
        chave = (self.cultura, self.largura, self.semente)
        if chave not in self._tiras:
            self._tiras[chave] = self._montar()
        return self._tiras[chave]

    def _montar(self):
        """Os pés lado a lado, com altura e ordem sorteadas (sempre iguais para a mesma fileira)."""
        sorteio = random.Random(self.semente)
        pes = [Recursos.imagem(f"cenario/plantas/{self.cultura}_{i}.png") for i in range(self.VARIACOES)]
        altura = max(pe.get_height() for pe in pes) + 6
        tira = pygame.Surface((self.largura, altura), pygame.SRCALPHA)
        pygame.draw.ellipse(tira, (20, 40, 20, 70), (4, altura - 12, self.largura - 8, 12))      # sombra no chão
        colocados, x = [], 0                                  # só entra o pé que cabe inteiro: nada cortado na ponta
        while True:
            pe = sorteio.choice(pes)
            if x + pe.get_width() > self.largura:
                break
            colocados.append((pe, x, altura - pe.get_height() - sorteio.randint(0, 5)))
            x += round(pe.get_width() * self.APERTO * sorteio.uniform(0.9, 1.15))
        sobra = (self.largura - max((px + pe.get_width() for pe, px, _ in colocados), default=0)) // 2
        for pe, px, py in colocados:                          # a fileira fica centrada no talhão
            tira.blit(pe, (px + sobra, py))
        return tira

    def atualizar(self, dt, jogo):
        pass

    def esta_visivel(self, camera):
        imagem = self.imagem
        area = pygame.Rect(self.posicao.x - self.largura / 2, self.posicao.y - imagem.get_height(), self.largura,
                           imagem.get_height())
        return camera.retangulo.colliderect(area)

    def desenhar(self, tela, camera):
        imagem = self.imagem
        base = camera.para_tela(self.posicao)
        tela.blit(imagem, (round(base.x - self.largura / 2), round(base.y - imagem.get_height())))


class Predio(Entidade):
    """Prédio da UFJ: obstáculo com o contorno real e desenho em pixel art 3/4.

    A posição é o meio da base (o ponto mais ao sul), para quem passa atrás do
    prédio ser desenhado antes dele e ficar escondido.
    """

    grupo = "predio"
    camada = 1

    def __init__(self, nome, poligono, sprite, canto, escala=ESCALA_PIXEL):
        pontos = [pygame.Vector2(p) for p in poligono]
        base_y = max(p.y for p in pontos)
        meio_x = sum(p.x for p in pontos) / len(pontos)
        super().__init__((meio_x, base_y), 0)
        self.nome = nome
        self.poligono = [tuple(p) for p in pontos]
        self.sprite = sprite
        self.canto = pygame.Vector2(canto)
        self.escala = escala
        xs = [p.x for p in pontos]
        ys = [p.y for p in pontos]
        self.contorno = pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)

    @property
    def imagem(self):
        return Recursos.imagem_pixel(self.sprite, self.escala)

    def atualizar(self, dt, jogo):
        pass

    def esta_visivel(self, camera):
        area = pygame.Rect(self.canto, self.imagem.get_size()).union(self.contorno)
        return camera.retangulo.inflate(64, 64).colliderect(area)

    def desenhar(self, tela, camera):
        tela.blit(self.imagem, camera.para_tela(self.canto))

    def empurrar(self, centro, raio):
        return Colisao.empurrar_para_fora(centro, raio, self.poligono)


class Mapa(ABC):
    """O que um mapa oferece ao Jogo: tamanho, ponto inicial, entidades, chão e obstáculos."""

    def __init__(self, arena, inicio):
        self.arena = arena
        self.inicio = pygame.Vector2(inicio)

    @abstractmethod
    def entidades(self):
        """Entidades fixas do mapa (prédios, decorações) para entrarem no Jogo."""

    @abstractmethod
    def desenhar_chao(self, tela, camera):
        """Desenha o chão visível pela câmera."""

    def obstaculos_perto(self, posicao, raio):
        return []

    def fator_de_velocidade(self, posicao):
        """Quanto o chão deixa andar ali (1 = normal). Mato alto e plantação seguram o passo do aluno."""
        return 1.0

    def local_de(self, nome):
        """Um ponto livre em frente ao prédio chamado `nome`, ou None se o mapa não tem esse prédio."""
        return None

    def miniatura(self, altura):
        """Desenho do mapa inteiro com `altura` pixels (para o mini-mapa)."""
        largura = max(1, round(altura * self.arena.width / self.arena.height))
        imagem = pygame.Surface((largura, altura))
        imagem.fill((52, 92, 52))
        return imagem

    def empurrar(self, posicao, raio):
        """Posição corrigida para não ficar dentro de nenhum obstáculo."""
        posicao = pygame.Vector2(posicao)
        for obstaculo in self.obstaculos_perto(posicao, raio):
            nova = obstaculo.empurrar(posicao, raio)
            if nova is not None:
                posicao = nova
        return posicao

    def bloqueado(self, posicao, raio):
        return any(Colisao.circulo_poligono(posicao, raio, o.poligono) for o in self.obstaculos_perto(posicao, raio))


class MapaUFJ(Mapa):
    """Campus Jatobá da UFJ, lido de assets/cenario/mapa_ufj.json."""

    ARQUIVO = "cenario/mapa_ufj.json"
    CELULA = 128
    DECORACOES = {
        "palmeira": "palmeira", "ipe": "ipe", "arvore": "arvore_cerrado", "poste": "poste",
        "banco": "banco", "portal": "portal_ufj", "bandeira": "bandeira",
    }

    def __init__(self, dados, rng=None):
        super().__init__(pygame.Rect(0, 0, dados["largura"], dados["altura"]), dados["inicio"])
        self.chao = dados["chao"]
        self.escala = dados.get("escala", ESCALA_PIXEL)
        escala_predios = dados.get("escala_predios", self.escala)
        self.predios = [Predio(p["nome"], p["poligono"], p["sprite"], p["canto"], escala_predios)
                        for p in dados["predios"]]
        self._blocos = OrderedDict()
        self._miniaturas = {}
        self._recortes_dos_talhoes = {}
        self.fileiras = self._plantar_fileiras()
        self.faixas = dados.get("faixas", [])        # travessias de pedestre (ferramentas/faixas_de_pedestre.py)
        self.decoracoes = [Decoracao((d["x"], d["y"]), pasta=self.DECORACOES.get(d["tipo"], d["tipo"]))
                           for d in dados["decoracoes"] if not self.na_lavoura(d["x"], d["y"], -40)]   # sem árvore na plantação
        self._celulas = {}
        for predio in self.predios:
            r = predio.contorno
            for cx in range(r.left // self.CELULA, r.right // self.CELULA + 1):
                for cy in range(r.top // self.CELULA, r.bottom // self.CELULA + 1):
                    self._celulas.setdefault((cx, cy), []).append(predio)
        Recursos.imagem(self.chao)       # o chão é consultado já no 1º quadro (passo na mata): lê agora, não no meio do jogo

    @classmethod
    def carregar(cls, rng=None):
        """Lê o mapa gerado; devolve None se ele não existir."""
        arquivo = PASTA_ASSETS / cls.ARQUIVO
        if not arquivo.is_file():
            return None
        return cls(json.loads(arquivo.read_text(encoding="utf-8")), rng)

    def entidades(self):
        return self.predios + self.decoracoes + self.fileiras

    # Quanto cada chão segura o passo do aluno (1 = normal): ele atravessa a plantação, mas com esforço.
    PASSO_NA_CULTURA = {"soja": 0.8, "trigo": 0.72, "milho": 0.6}
    PASSO_NA_MATA = 0.88
    ESPACO_ENTRE_FILEIRAS = {"soja": 42, "trigo": 38, "milho": 54}
    MARGEM_DA_FILEIRA = 22

    def fator_de_velocidade(self, posicao):
        x, y = posicao
        for talhao in self.LAVOURAS:
            if talhao.collidepoint(x, y):
                return self.PASSO_NA_CULTURA[self.cultura_de(talhao)]
        return self.PASSO_NA_MATA if self._tem_a_cor(x, y, self.VERDE_ESCURO) else 1.0

    def _plantar_fileiras(self):
        """As fileiras em pé de cada talhão (só se a arte dos pés existir)."""
        fileiras = []
        for indice, talhao in enumerate(self.LAVOURAS):
            cultura = self.cultura_de(talhao)
            if not self._existe(f"cenario/plantas/{cultura}_0.png"):
                continue
            passo = self.ESPACO_ENTRE_FILEIRAS[cultura]
            largura = talhao.width - 2 * self.MARGEM_DA_FILEIRA
            for n, y in enumerate(range(talhao.top + passo, talhao.bottom - 6, passo)):
                fileiras.append(FileiraDePlantacao((talhao.centerx, y), cultura, largura, indice * 100 + n % 7))
        return fileiras

    FRENTE_DO_PREDIO = 150       # distância da base do prédio até o ponto de referência

    def local_de(self, nome):
        """Ponto livre em frente ao prédio; se a frente está tomada por outro prédio, o livre mais próximo."""
        for predio in self.predios:
            if predio.nome == nome:
                frente = pygame.Vector2(predio.posicao.x, predio.contorno.bottom + self.FRENTE_DO_PREDIO)
                candidatos = [frente] + [frente + pygame.Vector2(passo, 0).rotate(angulo)
                                         for passo in range(120, 1201, 120) for angulo in range(0, 360, 30)]
                for ponto in candidatos:
                    if self.arena.inflate(-240, -240).collidepoint(ponto) and not self.bloqueado(ponto, 110):
                        return ponto
                return self.empurrar(frente, 100)
        return None

    def miniatura(self, altura):
        """O chão reduzido com os prédios pintados por cima (guardada: só é montada uma vez por altura)."""
        if altura not in self._miniaturas:
            fator = altura / self.arena.height
            chao = Recursos.imagem(self.chao)
            imagem = pygame.transform.smoothscale(chao, (max(1, round(self.arena.width * fator)), altura))
            for predio in self.predios:
                pontos = [(x * fator, y * fator) for x, y in predio.poligono]
                pygame.draw.polygon(imagem, (196, 150, 110), pontos)
                pygame.draw.polygon(imagem, (70, 44, 40), pontos, 1)
            for talhao in self.LAVOURAS:                         # os talhões de lavoura também aparecem
                area = pygame.Rect(talhao.x * fator, talhao.y * fator, talhao.w * fator, talhao.h * fator)
                pygame.draw.rect(imagem, self.CORES_DAS_CULTURAS[self.cultura_de(talhao)], area)
                pygame.draw.rect(imagem, (150, 84, 50), area, 1)
            self._miniaturas[altura] = imagem
        return self._miniaturas[altura]

    def obstaculos_perto(self, posicao, raio):
        x0, y0 = int((posicao[0] - raio) // self.CELULA), int((posicao[1] - raio) // self.CELULA)
        x1, y1 = int((posicao[0] + raio) // self.CELULA), int((posicao[1] + raio) // self.CELULA)
        achados = []
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                for predio in self._celulas.get((cx, cy), ()):
                    if predio not in achados:
                        achados.append(predio)
        return achados

    BLOCO = 128            # lado do bloco do chão, em pixels da imagem reduzida
    MAX_BLOCOS = 80

    def _bloco(self, bx, by):
        """Bloco do chão já ampliado (com suavização), guardado nos mais usados recentemente."""
        chave = (bx, by)
        if chave in self._blocos:
            self._blocos.move_to_end(chave)
            return self._blocos[chave]
        chao = Recursos.imagem(self.chao)
        area = pygame.Rect(bx * self.BLOCO, by * self.BLOCO, self.BLOCO + 1, self.BLOCO + 1).clip(chao.get_rect())
        if area.width <= 0 or area.height <= 0:
            return None
        pedaco = chao.subsurface(area)
        tamanho = (area.width * self.escala, area.height * self.escala)
        try:
            ampliado = pygame.transform.smoothscale(pedaco, tamanho)
        except ValueError:
            ampliado = pygame.transform.scale(pedaco, tamanho)
        self._plantar(ampliado, bx, by)
        asfalto = pygame.mask.from_threshold(ampliado, self.ASFALTO[0], (*self.ASFALTO[1], 255))
        self._detalhar(ampliado, bx, by)
        self._sinalizar(ampliado, bx, by, asfalto)
        self._enfeitar(ampliado, bx, by)
        self._blocos[chave] = ampliado
        if len(self._blocos) > self.MAX_BLOCOS:
            self._blocos.popitem(last=False)
        return ampliado

    # Detalhe do chão: o chão ampliado fica borrado, então uma textura em resolução de tela (folhas, grão do
    # asfalto, pedrinhas, fileiras da lavoura) é somada e subtraída só onde o bloco tem a cor daquele piso
    # (ferramentas/montar_grama.py e montar_chao.py). Cada piso: textura e as cores (com tolerância) que o marcam.
    GRAMA = ((109, 173, 68), (30, 30, 22))
    VERDE_ESCURO = ((50, 106, 50), (26, 30, 18))        # mata fechada e sombra de árvore
    TERRA = ((184, 98, 56), (30, 30, 24))               # terra batida
    PISOS = (
        ("grama", (GRAMA, VERDE_ESCURO)),               # a mata usa a folhagem da grama
        ("terra", (TERRA,)),
        ("asfalto", (((76, 76, 88), (20, 20, 22)), ((218, 206, 172), (22, 22, 24)),     # ruas, calçadas
                     ((190, 188, 176), (16, 16, 16)))),                                 # e concreto
    )

    # Lavoura: a plantação fica em talhões retangulares, em lugares escolhidos (as áreas agrícolas a oeste,
    # a leste e ao sul do campus), com corredores de terra entre eles. Dentro do talhão o chão é pintado
    # inteiro de fileiras; fora deles não existe plantação.
    CORREDOR = 64

    @staticmethod
    def _talhoes(area, colunas, linhas, corredor=CORREDOR):
        """Divide a área agrícola em colunas x linhas de talhões iguais, separados por corredores."""
        x, y, largura, altura = area
        lado_x = (largura - corredor * (colunas - 1)) // colunas
        lado_y = (altura - corredor * (linhas - 1)) // linhas
        return tuple(pygame.Rect(x + c * (lado_x + corredor), y + l * (lado_y + corredor), lado_x, lado_y)
                     for l in range(linhas) for c in range(colunas))

    LAVOURAS = (_talhoes((360, 6560, 820, 1640), 2, 2) + _talhoes((4310, 6000, 790, 780), 2, 1)
                + _talhoes((4050, 6880, 800, 900), 2, 1) + _talhoes((2550, 9300, 1150, 600), 3, 1))
    CULTURAS = ("soja", "milho", "trigo")       # o que se planta na UFJ; os talhões alternam entre elas
    CORES_DAS_CULTURAS = {"soja": (48, 120, 44), "milho": (40, 104, 40), "trigo": (206, 168, 52)}

    def cultura_de(self, talhao):
        """O que está plantado no talhão."""
        return self.CULTURAS[self.LAVOURAS.index(talhao) % len(self.CULTURAS)]
    AREA_51 = pygame.Rect(5050, 2050, 1086, 1250)       # o descampado do Centro de Aulas Secreto 51

    # Biomas: cada pedaço do campus tem a própria decoração de chão. (nome, quantos por bloco, enfeites;
    # os repetidos saem mais). O teste de cada bioma é o método _e_<nome>.
    BIOMAS = (
        ("grama", 6, ("capim_alto", "capim_baixo", "capim_baixo", "capim_alto", "trevos", "flores_amarelas",
                      "margaridas", "flores_rosas", "flores_vermelhas", "petalas_ipe", "pedras", "arbusto",
                      "arbusto_florido", "cogumelos")),
        ("mata", 5, ("arbusto", "arbusto", "arbusto_florido", "cogumelos", "cogumelos", "capim_alto", "pedras")),
        ("lavoura", 2, ("corvo", "corvo", "fardo_de_feno", "fardo_de_feno", "espantalho", "carrinho_de_mao",
                        "irrigador", "irrigador")),             # soja, milho e trigo: nada de abóbora nem legumes
        ("terra", 2, ("pedras", "pedras", "capim_baixo")),
        ("area_51", 1, ("marca_de_pouso", "pegadas_alienigenas", "pegadas_alienigenas", "placa_alienigena",
                        "circulo_alienigena", "pedras")),
    )

    @staticmethod
    def _existe(caminho):
        return (Recursos.pasta / caminho).is_file()

    def _detalhar(self, bloco, bx, by):
        """Dá textura nítida a cada piso do bloco (grama, lavoura, terra, asfalto), sem mudar o desenho do mapa."""
        lado = self.BLOCO * self.escala
        for nome, cores in self.PISOS:
            luz, sombra = f"cenario/{nome}_luz.png", f"cenario/{nome}_sombra.png"
            if not (self._existe(luz) and self._existe(sombra)):
                continue
            piso = pygame.mask.Mask(bloco.get_size())
            for cor, tolerancia in cores:
                piso.draw(pygame.mask.from_threshold(bloco, cor, (*tolerancia, 255)), (0, 0))
            if piso.count() == 0:
                continue
            detalhado = bloco.convert_alpha()
            for caminho, modo in ((luz, pygame.BLEND_RGB_ADD), (sombra, pygame.BLEND_RGB_SUB)):
                ladrilho = Recursos.imagem(caminho)
                largura, altura = ladrilho.get_size()
                for y in range(-((by * lado) % altura), bloco.get_height(), altura):
                    for x in range(-((bx * lado) % largura), bloco.get_width(), largura):
                        detalhado.blit(ladrilho, (x, y), special_flags=modo)
            recorte = piso.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))
            detalhado.blit(recorte, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            bloco.blit(detalhado, (0, 0))

    LISTRA = 8                       # largura de cada listra da faixa de pedestre e do vão entre elas
    COR_DA_FAIXA = (226, 224, 212, 120)       # tinta gasta: meio transparente, o grão do asfalto aparece por baixo
    SOBRA_DA_FAIXA = 12              # a faixa é desenhada mais comprida e recortada pelo asfalto: vai de meio-fio a meio-fio
    ASFALTO = ((76, 76, 88), (20, 20, 22))

    def _sinalizar(self, bloco, bx, by, asfalto):
        """Pinta as faixas de pedestre do bloco, só em cima do asfalto (`asfalto` é a máscara dele no bloco)."""
        lado = self.BLOCO * self.escala
        canto = pygame.Vector2(bx * lado, by * lado)
        area = pygame.Rect(canto, bloco.get_size()).inflate(240, 240)
        perto = [f for f in self.faixas if area.collidepoint(f["x"], f["y"])]
        if not perto:
            return
        tinta = pygame.Surface(bloco.get_size(), pygame.SRCALPHA)
        for faixa in perto:
            centro = pygame.Vector2(faixa["x"], faixa["y"]) - canto
            andar = pygame.Vector2(faixa["dx"], faixa["dy"])
            atravessado = pygame.Vector2(-andar.y, andar.x) * faixa["largura"] / 2
            listras = int((faixa["comprimento"] + self.SOBRA_DA_FAIXA) // (2 * self.LISTRA))
            for i in range(listras):
                meio = centro + andar * (i - (listras - 1) / 2) * 2 * self.LISTRA
                meia = andar * self.LISTRA / 2
                pygame.draw.polygon(tinta, self.COR_DA_FAIXA, [meio - meia - atravessado, meio + meia - atravessado,
                                                               meio + meia + atravessado, meio - meia + atravessado])
        recorte = asfalto.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))
        tinta.blit(recorte, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        bloco.blit(tinta, (0, 0))

    FOLGA_DA_TRANSICAO = 72          # quanto em volta do bloco entra na conta, para a borda não emendar torta
    RECORTES_POR_LADO = 0.045        # mordidas e saliências por pixel de borda do talhão

    def _recortes(self, talhao):
        """Saliências e mordidas na borda do talhão (sempre as mesmas): tiram a linha reta da plantação."""
        chave = tuple(talhao)
        if chave not in self._recortes_dos_talhoes:
            sorteio = random.Random(hash(chave))
            recortes = []
            for inicio, fim in ((talhao.topleft, talhao.topright), (talhao.bottomleft, talhao.bottomright),
                                (talhao.topleft, talhao.bottomleft), (talhao.topright, talhao.bottomright)):
                lado = pygame.Vector2(fim) - pygame.Vector2(inicio)
                for _ in range(int(lado.length() * self.RECORTES_POR_LADO)):
                    ponto = pygame.Vector2(inicio) + lado * sorteio.random()
                    recortes.append((ponto, sorteio.randint(10, 26), sorteio.random() < 0.5))
            self._recortes_dos_talhoes[chave] = recortes
        return self._recortes_dos_talhoes[chave]

    def _mancha(self, talhao, area, crescimento, desfoque, mordidas=True):
        """Máscara (branco = dentro) do talhão na área dada, com a borda irregular e esfumada."""
        mascara = pygame.Surface(area.size)
        pygame.draw.rect(mascara, (255, 255, 255), talhao.inflate(crescimento * 2, crescimento * 2).move(-area.x, -area.y),
                         border_radius=18)
        for ponto, raio, para_fora in self._recortes(talhao):
            if not (para_fora or mordidas):
                continue
            centro = (ponto.x - area.x, ponto.y - area.y)
            if -40 < centro[0] < area.width + 40 and -40 < centro[1] < area.height + 40:
                pygame.draw.circle(mascara, (255, 255, 255) if para_fora else (0, 0, 0), centro, raio + crescimento // 2)
        pequena = pygame.transform.smoothscale(mascara, (max(1, area.width // desfoque), max(1, area.height // desfoque)))
        return pygame.transform.smoothscale(pequena, area.size)

    def _plantar(self, bloco, bx, by):
        """Pinta de terra batida os talhões de lavoura que passam pelo bloco, com a borda irregular se
        misturando no chão em volta. É a mesma terra dos caminhos (a textura dela entra depois, em _detalhar);
        as plantas são as fileiras em pé (FileiraDePlantacao)."""
        lado = self.BLOCO * self.escala
        folga = self.FOLGA_DA_TRANSICAO
        area = pygame.Rect(bx * lado - folga, by * lado - folga, bloco.get_width() + 2 * folga,
                           bloco.get_height() + 2 * folga)
        for talhao in self.LAVOURAS:                          # o talhão inteiro, com beirada e corredores
            if not talhao.inflate(120, 120).colliderect(area):
                continue
            solo = pygame.Surface(area.size, pygame.SRCALPHA)
            solo.fill(self.TERRA[0])
            self._recortar(solo, self._mancha(talhao, area, 38, 8, mordidas=False), 1.0)
            bloco.blit(solo, (-folga, -folga))

    @staticmethod
    def _recortar(camada, mancha, forca):
        """Usa a mancha (tons de cinza) como transparência da camada."""
        pixels = pygame.surfarray.pixels_alpha(camada)
        pixels[:] = (pygame.surfarray.array_red(mancha) * forca).astype("uint8")
        del pixels

    def na_lavoura(self, x, y, folga=0):
        """Diz se o ponto do mundo cai dentro de algum talhão (com `folga` pixels para dentro da borda)."""
        return any(talhao.inflate(-2 * folga, -2 * folga).collidepoint(x, y) for talhao in self.LAVOURAS)

    def _e_grama(self, x, y):
        """Gramado aberto: nem mata, rua, calçada, terra ou plantação."""
        return not self.na_lavoura(x, y, -30) and self._tem_a_cor(x, y, self.GRAMA)

    def _e_mata(self, x, y):
        return not self.na_lavoura(x, y, -30) and self._tem_a_cor(x, y, self.VERDE_ESCURO)

    def _e_lavoura(self, x, y):
        return self.na_lavoura(x, y, 50)

    def _e_terra(self, x, y):
        return (not self.na_lavoura(x, y, -30) and not self.AREA_51.collidepoint(x, y)
                and self._tem_a_cor(x, y, self.TERRA))

    def _e_area_51(self, x, y):
        return self.AREA_51.collidepoint(x, y) and self._tem_a_cor(x, y, self.TERRA) and not self.bloqueado((x, y), 170)

    def _tem_a_cor(self, x, y, piso):
        chao = Recursos.imagem(self.chao)
        px, py = int(x // self.escala), int(y // self.escala)
        if not chao.get_rect().collidepoint(px, py):
            return False
        cor, tolerancia = piso
        return all(abs(a - b) <= t for a, b, t in zip(chao.get_at((px, py))[:3], cor, tolerancia))

    def _enfeites_do_bloco(self, bx, by):
        """Enfeites (imagem e ponto de apoio no mundo) do bloco; sempre os mesmos para o mesmo bloco."""
        sorteio = random.Random(bx * 73856093 ^ by * 19349663)
        lado = self.BLOCO * self.escala
        achados = []
        for bioma, quantos, enfeites in self.BIOMAS:
            pertence = getattr(self, f"_e_{bioma}")
            for _ in range(quantos):
                nome = sorteio.choice(enfeites)
                x, y = (bx + sorteio.random()) * lado, (by + sorteio.random()) * lado
                caminho = f"cenario/enfeites/{nome}.png"
                if pertence(x, y) and self._existe(caminho):
                    achados.append((Recursos.imagem(caminho), x, y))
        return achados

    def _enfeitar(self, bloco, bx, by):
        """Desenha flores, capim e pedras no gramado; os vizinhos entram para nada ficar cortado na emenda."""
        lado = self.BLOCO * self.escala
        enfeites = [e for vy in (by - 1, by, by + 1) for vx in (bx - 1, bx, bx + 1)
                    for e in self._enfeites_do_bloco(vx, vy)]
        for imagem, x, y in sorted(enfeites, key=lambda e: e[2]):
            bloco.blit(imagem, (round(x - bx * lado - imagem.get_width() / 2), round(y - by * lado - imagem.get_height())))

    def desenhar_chao(self, tela, camera):
        """O chão fica guardado em resolução reduzida e é desenhado em blocos ampliados com suavização."""
        tela.fill((40, 70, 40))
        visivel = camera.retangulo.clip(self.arena)
        if visivel.width <= 0 or visivel.height <= 0:
            return
        lado = self.BLOCO * self.escala
        for by in range(visivel.top // lado, (visivel.bottom - 1) // lado + 1):
            for bx in range(visivel.left // lado, (visivel.right - 1) // lado + 1):
                bloco = self._bloco(bx, by)
                if bloco is not None:
                    tela.blit(bloco, camera.para_tela((bx * lado, by * lado)))
