"""Gera o mapa do Campus Jatobá (UFJ) a partir de satélite e OpenStreetMap.

Entradas (em arte_bruta/mapa/, fora do git):
  satelite_z17.jpg   mosaico Esri World Imagery, zoom 17, começando no tile (46704, 72169)
  osm.json           resposta do Overpass com prédios, vias, calçadas, piscina e quadra

Saídas:
  assets/cenario/mapa_ufj.png          chão em pixel art (metade da resolução da arena)
  assets/cenario/predios/<id>.png      um sprite 3/4 por prédio
  assets/cenario/mapa_ufj.json         arena, ponto inicial, prédios (colisão) e decorações

Uso: python ferramentas/gerar_mapa.py
"""
import json
import math
import os
import random
import re
import unicodedata
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import numpy as np  # noqa: E402
import pygame  # noqa: E402
from PIL import Image  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "arte_bruta" / "mapa"
SAIDA = RAIZ / "assets" / "cenario"
FONTE = RAIZ / "assets" / "fontes" / "pixelify-sans-latin-700-normal.woff2"

ESCALA_PIXEL = 2                 # o chão e os prédios são pixel art ampliada 2x no jogo
UNIDADES_POR_METRO = 5.0
ALTURA_ANDAR = 7                 # pixels nativos de parede por andar
INICIO_SATELITE = (745, 690)     # meio do gramado oval central, em pixels do satélite


class Classe(IntEnum):
    GRAMA = 0
    MATA = 1
    TERRA = 2
    CONCRETO = 3


def classificar(rgb):
    """Classe de chão de cada pixel do satélite (grama, mata, terra vermelha, concreto)."""
    rgb = rgb.astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    luz = 0.3 * r + 0.59 * g + 0.11 * b
    classe = np.full(r.shape, Classe.GRAMA, dtype=np.uint8)
    cinza = (abs(r - g) < 22) & (abs(g - b) < 28) & (luz > 125)
    classe[cinza] = Classe.CONCRETO
    classe[(luz < 80) & (g >= r)] = Classe.MATA
    classe[(r > g + 22) & (r > 110)] = Classe.TERRA
    return classe


@dataclass
class Recorte:
    """Liga coordenadas geográficas, pixels do satélite e unidades do jogo."""

    tile_x0: int
    tile_y0: int
    zoom: int
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def metros_por_pixel(self):
        lat_meio = self.latlon_satelite((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)[0]
        return 156543.03392 * math.cos(math.radians(lat_meio)) / 2 ** self.zoom

    @property
    def mundo_por_pixel(self):
        return self.metros_por_pixel * UNIDADES_POR_METRO

    @property
    def largura_mundo(self):
        return int((self.x1 - self.x0) * self.mundo_por_pixel)

    @property
    def altura_mundo(self):
        return int((self.y1 - self.y0) * self.mundo_por_pixel)

    def satelite(self, lat, lon):
        n = 2 ** self.zoom
        x = (lon + 180) / 360 * n
        y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
        return (x - self.tile_x0) * 256, (y - self.tile_y0) * 256

    def latlon_satelite(self, sx, sy):
        n = 2 ** self.zoom
        x = sx / 256 + self.tile_x0
        y = sy / 256 + self.tile_y0
        lon = x / n * 360 - 180
        lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
        return lat, lon

    def mundo(self, lat, lon):
        sx, sy = self.satelite(lat, lon)
        return (sx - self.x0) * self.mundo_por_pixel, (sy - self.y0) * self.mundo_por_pixel

    def latlon(self, x, y):
        return self.latlon_satelite(x / self.mundo_por_pixel + self.x0, y / self.mundo_por_pixel + self.y0)


RECORTE = Recorte(tile_x0=46704, tile_y0=72169, zoom=17, x0=430, y0=160, x1=1060, y1=1150)

NOMES_CURTOS = {
    "restaurante universitario": "RU",
    "biblioteca": "BIBLIOTECA",
    "reitoria": "REITORIA",
    "centro de convivencia": "CONVIVENCIA",
    "cantina": "CANTINA",
    "auditorio": "AUDITORIO",
    "faculdade de medicina": "MEDICINA",
    "faculdade de direito": "DIREITO",
    "hospital veterinario": "HOSPITAL VET.",
    "laboratorios de ciencias exatas": "LAB. EXATAS",
    "laboratorios de ciencias da saude": "LAB. SAUDE",
    "pos-graduacao": "POS-GRADUACAO",
    "biomedicina e enfermagem": "BIOMED. E ENF.",
    "engenharia florestal": "ENG. FLORESTAL",
    "ciencias humanas": "HUMANAS",
}


def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def nome_curto(nome):
    """Nome que cabe na plaquinha do prédio."""
    if not nome:
        return ""
    simples = _sem_acento(nome).lower()
    for chave, curto in NOMES_CURTOS.items():
        if chave in simples:
            return curto
    limpo = re.sub(r"\s+(UFJ|do Campus Jatoba)$", "", _sem_acento(nome)).upper()
    return limpo[:18]


TELHADOS = {
    "branco": (226, 226, 220),
    "cinza": (172, 176, 182),
    "escuro": (92, 96, 106),
    "ceramica": (180, 92, 60),
    "metal": (150, 172, 192),
}
# cores conferidas nas fotos (Wikimedia Commons): Biblioteca clara, Medicina cinza-escura
TELHADO_CONHECIDO = {"BIBLIOTECA": "cinza", "MEDICINA": "escuro", "REITORIA": "branco", "RU": "branco"}
PAREDES = {"branco": (236, 234, 226), "cinza": (214, 214, 208), "escuro": (126, 130, 140),
           "ceramica": (232, 214, 182), "metal": (220, 224, 228)}


def cor_de_telhado(media):
    """Cor da paleta de telhados mais próxima da média vista no satélite."""
    return min(TELHADOS.values(), key=lambda c: sum((a - b) ** 2 for a, b in zip(c, media)))


def _tom(cor, delta):
    return tuple(max(0, min(255, v + delta)) for v in cor)


def desenhar_predio(poligono, telhado, andares=2, nome=""):
    """Sprite 3/4 de um prédio em resolução nativa. Devolve (superfície, canto superior esquerdo)."""
    altura_parede = max(1, andares) * ALTURA_ANDAR
    xs = [p[0] for p in poligono]
    ys = [p[1] for p in poligono]
    esquerda, topo = int(min(xs)) - 2, int(min(ys)) - altura_parede - 2
    largura = int(max(xs)) - esquerda + 3
    altura = int(max(ys)) - topo + 3
    local = [(x - esquerda, y - topo) for x, y in poligono]
    nome_parede = next(k for k, v in TELHADOS.items() if v == telhado)
    parede = PAREDES[nome_parede]

    base = pygame.Surface((largura, altura), pygame.SRCALPHA)
    for t in range(altura_parede + 1):
        pygame.draw.polygon(base, (*_tom(parede, -18 if t < 2 else 0), 255), [(x, y - t) for x, y in local])
    telhado_pts = [(x, y - altura_parede) for x, y in local]
    sprite = base.copy()
    # janelas na faixa de parede que fica visível (abaixo do telhado)
    mascara_telhado = pygame.Surface((largura, altura), pygame.SRCALPHA)
    pygame.draw.polygon(mascara_telhado, (255, 255, 255, 255), telhado_pts)
    vidro = (66, 92, 124) if nome_parede != "escuro" else (150, 186, 214)
    for y in range(altura):
        for x in range(largura):
            if sprite.get_at((x, y)).a == 0 or mascara_telhado.get_at((x, y)).a:
                continue
            if x % 6 in (1, 2, 3) and (y + 2) % ALTURA_ANDAR in (2, 3, 4):
                sprite.set_at((x, y), (*vidro, 255))
    pygame.draw.polygon(sprite, (*telhado, 255), telhado_pts)
    pygame.draw.polygon(sprite, (*_tom(telhado, -40), 255), telhado_pts, 1)
    for i in range(len(telhado_pts)):   # beiral mais claro nas arestas de cima
        a, b = telhado_pts[i], telhado_pts[(i + 1) % len(telhado_pts)]
        if a[1] + b[1] < 2 * (sum(p[1] for p in telhado_pts) / len(telhado_pts)):
            pygame.draw.line(sprite, (*_tom(telhado, 28), 255), a, b)
    if nome:
        fonte = pygame.font.Font(str(FONTE), 9) if FONTE.exists() else pygame.font.Font(None, 11)
        texto = fonte.render(nome, False, (250, 246, 230))
        centro = (sum(p[0] for p in telhado_pts) / len(telhado_pts), sum(p[1] for p in telhado_pts) / len(telhado_pts))
        placa = pygame.Rect(0, 0, texto.get_width() + 4, texto.get_height() + 1)
        placa.center = (round(centro[0]), round(centro[1]))
        pygame.draw.rect(sprite, (40, 34, 48, 255), placa)
        pygame.draw.rect(sprite, (214, 168, 74, 255), placa, 1)
        sprite.blit(texto, (placa.x + 2, placa.y))
    contorno = pygame.mask.from_surface(sprite).outline()
    if len(contorno) > 2:
        pygame.draw.lines(sprite, (28, 24, 34, 255), True, contorno, 1)
    return sprite, (esquerda, topo)


def _textura(classe_mapa, rng):
    """Pinta cada classe com uma textura de pixel art: manchas grandes + pontinhos."""
    h, w = classe_mapa.shape
    manchas = rng.random((h // 4 + 2, w // 4 + 2))
    manchas = np.kron(manchas, np.ones((4, 4)))[:h, :w]
    pontos = rng.random((h, w))
    paletas = {
        Classe.GRAMA: [(86, 142, 56), (98, 156, 62), (110, 168, 70)],
        Classe.MATA: [(38, 80, 40), (48, 96, 46), (60, 112, 52)],
        Classe.TERRA: [(156, 72, 46), (172, 84, 52), (186, 100, 62)],
        Classe.CONCRETO: [(176, 172, 162), (190, 186, 176), (202, 198, 188)],
    }
    rgb = np.zeros((h, w, 3), np.uint8)
    for classe, paleta in paletas.items():
        mascara = classe_mapa == classe
        indice = np.clip((manchas * 2.2 + (pontos > 0.93) * 1.0 - (pontos < 0.05) * 1.0).astype(int), 0, 2)
        for i, cor in enumerate(paleta):
            rgb[mascara & (indice == i)] = cor
    flores = (classe_mapa == Classe.GRAMA) & (pontos > 0.998)
    rgb[flores] = (236, 214, 90)
    return rgb


def _moda_3x3(classes):
    contagens = []
    for c in range(len(Classe)):
        m = (classes == c).astype(np.int16)
        soma = sum(np.roll(np.roll(m, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1))
        contagens.append(soma)
    return np.argmax(np.stack(contagens), axis=0).astype(np.uint8)


def gerar():
    pygame.init()
    pygame.display.set_mode((1, 1))
    rng = np.random.default_rng(67)
    aleatorio = random.Random(67)
    rec = RECORTE
    satelite = np.array(Image.open(ENTRADA / "satelite_z17.jpg").convert("RGB"))
    osm = json.loads((ENTRADA / "osm.json").read_text(encoding="utf-8"))["elements"]
    W, H = rec.largura_mundo, rec.altura_mundo
    w, h = W // ESCALA_PIXEL, H // ESCALA_PIXEL

    # 1. chão pelo satélite
    ys = (np.arange(h) * ESCALA_PIXEL / rec.mundo_por_pixel + rec.y0).astype(int).clip(0, satelite.shape[0] - 1)
    xs = (np.arange(w) * ESCALA_PIXEL / rec.mundo_por_pixel + rec.x0).astype(int).clip(0, satelite.shape[1] - 1)
    amostra = satelite[ys][:, xs]
    classes = _moda_3x3(_moda_3x3(_moda_3x3(classificar(amostra))))
    chao = pygame.surfarray.make_surface(_textura(classes, rng).swapaxes(0, 1))

    def nativo(lat, lon):
        x, y = rec.mundo(lat, lon)
        return x / ESCALA_PIXEL, y / ESCALA_PIXEL

    def pontos(elemento):
        return [nativo(g["lat"], g["lon"]) for g in elemento.get("geometry", [])]

    # 2. áreas especiais e vias
    for e in osm:
        t = e["tags"]
        p = pontos(e)
        if len(p) < 3:
            continue
        if t.get("amenity") == "parking":
            pygame.draw.polygon(chao, (82, 82, 88), p)
            for x in range(int(min(q[0] for q in p)), int(max(q[0] for q in p)), 5):
                pygame.draw.line(chao, (220, 220, 210), (x, min(q[1] for q in p) + 1), (x, min(q[1] for q in p) + 4))
        elif t.get("leisure") == "swimming_pool":
            pygame.draw.polygon(chao, (232, 232, 226), p)
            pygame.draw.polygon(chao, (64, 150, 222), p, 0)
            pygame.draw.polygon(chao, (232, 232, 226), p, 2)
        elif t.get("leisure") == "pitch":
            pygame.draw.polygon(chao, (58, 132, 96), p)
            pygame.draw.polygon(chao, (236, 236, 230), p, 1)
    larguras = {"motorway": 20, "motorway_link": 12, "service": 12, "residential": 10, "unclassified": 10,
                "footway": 4}
    for camada in ("borda", "miolo"):
        for e in osm:
            via = e["tags"].get("highway")
            if via not in larguras or "building" in e["tags"]:
                continue
            p = pontos(e)
            if len(p) < 2:
                continue
            largura = larguras[via] + (2 if camada == "borda" else 0)
            if via == "footway":
                cor = (150, 140, 120) if camada == "borda" else (212, 198, 166)
            else:
                cor = (150, 150, 150) if camada == "borda" else (74, 74, 80)
            pygame.draw.lines(chao, cor, False, p, largura)
            for q in p:
                pygame.draw.circle(chao, cor, q, largura / 2)

    # 3. prédios
    (SAIDA / "predios").mkdir(parents=True, exist_ok=True)
    for antigo in (SAIDA / "predios").glob("*.png"):
        antigo.unlink()
    predios = []
    for e in osm:
        t = e["tags"]
        if "building" not in t:
            continue
        p = pontos(e)
        if len(p) < 3 or max(q[0] for q in p) < 0 or min(q[0] for q in p) > w or max(q[1] for q in p) < 0 \
                or min(q[1] for q in p) > h:
            continue
        sx = [rec.satelite(g["lat"], g["lon"]) for g in e["geometry"]]
        mascara = Image.new("L", (satelite.shape[1], satelite.shape[0]), 0)
        from PIL import ImageDraw
        ImageDraw.Draw(mascara).polygon(sx, fill=255)
        dentro = satelite[np.array(mascara) > 0]
        media = dentro.mean(axis=0) if len(dentro) else (200, 200, 200)
        andares = int(re.sub(r"\D", "", t.get("building:levels", "2")) or 2)
        nome = nome_curto(t.get("name"))
        telhado = TELHADOS[TELHADO_CONHECIDO[nome]] if nome in TELHADO_CONHECIDO else cor_de_telhado(media)
        sprite, (esquerda, topo) = desenhar_predio(p, telhado, andares, nome)
        ident = f"predio_{e['id']}"
        pygame.image.save(sprite, str(SAIDA / "predios" / f"{ident}.png"))
        predios.append({"id": ident, "nome": nome or "PREDIO",
                        "poligono": [[round(x * ESCALA_PIXEL), round(y * ESCALA_PIXEL)] for x, y in p],
                        "sprite": f"cenario/predios/{ident}.png",
                        "canto": [esquerda * ESCALA_PIXEL, topo * ESCALA_PIXEL]})
    pygame.image.save(chao, str(SAIDA / "mapa_ufj.png"))

    # 4. decorações
    poligonos = [[tuple(q) for q in pr["poligono"]] for pr in predios]

    def livre(x, y, folga=30):
        if not (60 < x < W - 60 and 60 < y < H - 60):
            return False
        from jogo.nucleo.colisao import Colisao
        return not any(Colisao.circulo_poligono((x, y), folga, pol) for pol in poligonos)

    decoracoes = []
    mata = np.argwhere(classes == Classe.MATA)
    aleatorio.shuffle(mata := [tuple(v) for v in mata])
    usados = []
    for ny, nx in mata:
        x, y = int(nx) * ESCALA_PIXEL, int(ny) * ESCALA_PIXEL
        if len(usados) >= 200:
            break
        if all((x - ux) ** 2 + (y - uy) ** 2 > 160 ** 2 for ux, uy in usados) and livre(x, y):
            usados.append((x, y))
            decoracoes.append({"tipo": "ipe" if aleatorio.random() < 0.15 else "arvore", "x": x, "y": y})
    for e in osm:
        via = e["tags"].get("highway")
        p = [(x * ESCALA_PIXEL, y * ESCALA_PIXEL) for x, y in pontos(e)]
        if via not in ("service", "footway") or len(p) < 2:
            continue
        passo, tipo, afastamento = (300, "palmeira", 44) if via == "service" else (300, "poste", 16)
        andado, lado = 0.0, 1
        for a, b in zip(p, p[1:]):
            trecho = pygame.Vector2(b) - pygame.Vector2(a)
            comprimento = trecho.length()
            if comprimento == 0:
                continue
            normal = pygame.Vector2(-trecho.y, trecho.x).normalize()
            d = (passo - andado % passo) % passo
            while d < comprimento:
                q = pygame.Vector2(a) + trecho * (d / comprimento) + normal * afastamento * lado
                if livre(q.x, q.y, 20):
                    decoracoes.append({"tipo": tipo, "x": round(q.x), "y": round(q.y)})
                lado = -lado
                d += passo
            andado += comprimento
    for pr in predios:
        if pr["nome"] in ("RU", "BIBLIOTECA", "CANTINA", "CONVIVENCIA", "CENTRO DE AULAS I", "CENTRO DE AULAS II"):
            base = max(pr["poligono"], key=lambda q: q[1])
            if livre(base[0], base[1] + 40, 16):
                decoracoes.append({"tipo": "banco", "x": base[0], "y": base[1] + 40})
    acesso = next((e for e in osm if e["tags"].get("name") == "Acesso UFJ - Campus Jatobá"), None)
    if acesso:
        p = [(x * ESCALA_PIXEL, y * ESCALA_PIXEL) for x, y in pontos(acesso)]
        dentro = [q for q in p if 0 < q[0] < W and 0 < q[1] < H]
        if dentro:
            px, py = min(dentro, key=lambda q: (q[0] - W / 2) ** 2 + (q[1] - H / 2) ** 2)
            decoracoes.append({"tipo": "portal", "x": round(px), "y": round(py)})
            decoracoes.append({"tipo": "bandeira", "x": round(px) - 110, "y": round(py) + 40})

    inicio = [round((INICIO_SATELITE[0] - rec.x0) * rec.mundo_por_pixel),
              round((INICIO_SATELITE[1] - rec.y0) * rec.mundo_por_pixel)]
    dados = {"largura": W, "altura": H, "chao": "cenario/mapa_ufj.png", "inicio": inicio,
             "predios": predios, "decoracoes": decoracoes,
             "fonte": "Esri World Imagery (satélite) e OpenStreetMap (ODbL), Campus Jatobá da UFJ"}
    (SAIDA / "mapa_ufj.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    print(f"arena {W}x{H}, chão {w}x{h}, {len(predios)} prédios, {len(decoracoes)} decorações, início {inicio}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(RAIZ))
    gerar()
