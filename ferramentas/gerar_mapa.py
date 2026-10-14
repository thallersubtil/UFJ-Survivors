"""Gera o mapa do Campus Jatobá (UFJ) a partir de satélite e OpenStreetMap.

Entradas (em arte_bruta/mapa/, fora do git):
  satelite_z17.jpg   mosaico Esri World Imagery, zoom 17, começando no tile (46704, 72169)
  osm.json           resposta do Overpass com prédios, vias, calçadas, piscina e quadra

Saídas:
  assets/cenario/mapa_ufj.png          chão em pixel art (metade da resolução da arena)
  assets/cenario/predios/<id>.png      um sprite 3/4 por prédio
  assets/cenario/mapa_ufj.json         arena, ponto inicial, prédios (colisão) e decorações

Uso: python ferramentas/gerar_mapa.py [--baixar]   (baixa as fontes se ainda não existirem)
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
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "arte_bruta" / "mapa"
SAIDA = RAIZ / "assets" / "cenario"
FONTE = RAIZ / "assets" / "fontes" / "pixelify-sans-latin-700-normal.woff2"

ESCALA_CHAO = 3                  # o chão é guardado em 1/3 da resolução; o jogo amplia suavizando
UNIDADES_POR_METRO = 10.0         # herói de ~76 px; prédios bem maiores que ele
ALTURA_ANDAR = 64                # pixels de parede por andar
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


RECORTE = Recorte(tile_x0=46704, tile_y0=72169, zoom=17, x0=470, y0=240, x1=1010, y1=1140)

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


CONTORNO = (26, 22, 34)
GROSSURA = 4                      # contorno grosso, como o dos personagens


def _poligono_grosso(sup, cor, pontos, largura):
    pygame.draw.polygon(sup, cor, pontos, 0)
    pygame.draw.lines(sup, CONTORNO, True, pontos, largura)
    for q in pontos:
        pygame.draw.circle(sup, CONTORNO, q, largura / 2)


def desenhar_predio(poligono, telhado, andares=2, nome=""):
    """Sprite 3/4 de um prédio em resolução cheia, no estilo ilustrado. Devolve (superfície, canto)."""
    altura_parede = max(1, andares) * ALTURA_ANDAR
    xs = [p[0] for p in poligono]
    ys = [p[1] for p in poligono]
    m = GROSSURA + 2
    esquerda, topo = int(min(xs)) - m, int(min(ys)) - altura_parede - m
    largura = int(max(xs)) - esquerda + m + 1
    altura = int(max(ys)) - topo + m + 1
    base = [(x - esquerda, y - topo) for x, y in poligono]
    nome_parede = next(k for k, v in TELHADOS.items() if v == telhado)
    parede = PAREDES[nome_parede]
    sombra_parede = _tom(parede, -46)
    vidro = (64, 112, 168) if nome_parede != "escuro" else (150, 196, 230)
    brilho_vidro = _tom(vidro, 70)
    sprite = pygame.Surface((largura, altura), pygame.SRCALPHA)
    teto = [(x, y - altura_parede) for x, y in base]

    # paredes: cada aresta virada para baixo (visível) vira uma face com janelas
    n = len(base)
    sentido = sum(base[i][0] * base[(i + 1) % n][1] - base[(i + 1) % n][0] * base[i][1] for i in range(n))
    faces = []
    for i in range(n):
        a, b = base[i], base[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        normal_y = dx if sentido > 0 else -dx
        if normal_y > 0:
            faces.append((max(a[1], b[1]), a, b, dx, dy))
    for _, a, b, dx, dy in sorted(faces):
        face = [a, b, (b[0], b[1] - altura_parede), (a[0], a[1] - altura_parede)]
        clara = abs(dx) > abs(dy)
        cor = parede if clara else sombra_parede
        _poligono_grosso(sprite, cor, face, GROSSURA)
        comprimento = (dx * dx + dy * dy) ** 0.5
        colunas = int(comprimento // 34)
        for c in range(colunas):
            f0 = (c + 0.25) / max(colunas, 1)
            f1 = (c + 0.75) / max(colunas, 1)
            for andar in range(max(1, andares)):
                y0 = altura_parede - andar * ALTURA_ANDAR - ALTURA_ANDAR * 0.78
                y1 = altura_parede - andar * ALTURA_ANDAR - ALTURA_ANDAR * 0.3
                q = [(a[0] + dx * f0, a[1] + dy * f0 - y1 + 0), (a[0] + dx * f1, a[1] + dy * f1 - y1),
                     (a[0] + dx * f1, a[1] + dy * f1 - y0), (a[0] + dx * f0, a[1] + dy * f0 - y0)]
                q = [(x, y) for x, y in q]
                pygame.draw.polygon(sprite, vidro if clara else _tom(vidro, -30), q)
                pygame.draw.line(sprite, brilho_vidro, q[3], (q[3][0] + (q[2][0] - q[3][0]) * 0.5, q[3][1] + (q[2][1] - q[3][1]) * 0.5), 3)
                pygame.draw.polygon(sprite, CONTORNO, q, 2)
        pygame.draw.line(sprite, _tom(cor, -70), a, b, 6)   # rodapé
    # telhado
    _poligono_grosso(sprite, telhado, teto, GROSSURA)
    meio = (sum(q[0] for q in teto) / n, sum(q[1] for q in teto) / n)
    interno = [(meio[0] + (x - meio[0]) * 0.86, meio[1] + (y - meio[1]) * 0.86) for x, y in teto]
    pygame.draw.polygon(sprite, _tom(telhado, 22), interno, 0)
    pygame.draw.lines(sprite, _tom(telhado, -30), True, interno, 2)
    if nome:
        fonte = pygame.font.Font(None, 30)   # fonte comum em negrito: legível na placa
        fonte.set_bold(True)
        texto = fonte.render(nome, True, (255, 248, 230))
        placa = pygame.Rect(0, 0, texto.get_width() + 18, texto.get_height() + 6)
        placa.center = (round(meio[0]), round(meio[1]))
        pygame.draw.rect(sprite, CONTORNO, placa.inflate(6, 6), border_radius=8)
        pygame.draw.rect(sprite, (64, 52, 92), placa, border_radius=6)
        pygame.draw.rect(sprite, (240, 196, 90), placa, 2, border_radius=6)
        sprite.blit(texto, texto.get_rect(center=placa.center))
    return sprite, (esquerda, topo)


def _ruido_suave(rng, h, w, passo):
    """Ruído macio: valores aleatórios numa grade grossa, interpolados (bilinear)."""
    gy, gx = h // passo + 2, w // passo + 2
    grade = rng.random((gy, gx)).astype(np.float32)
    img = Image.fromarray((grade * 255).astype(np.uint8)).resize((gx * passo, gy * passo), Image.BICUBIC)
    return np.array(img)[:h, :w].astype(np.float32) / 255


def _textura(classe_mapa, rng):
    """Pinta cada classe com tons macios (estilo ilustrado) e bordas suaves entre elas."""
    h, w = classe_mapa.shape
    ruido = 0.6 * _ruido_suave(rng, h, w, 24) + 0.4 * _ruido_suave(rng, h, w, 6)
    paletas = {
        Classe.GRAMA: ((92, 156, 60), (126, 190, 76)),
        Classe.MATA: ((40, 92, 46), (66, 128, 58)),
        Classe.TERRA: ((168, 82, 50), (204, 120, 70)),
        Classe.CONCRETO: ((182, 178, 168), (214, 210, 200)),
    }
    rgb = np.zeros((h, w, 3), np.float32)
    for classe, (escura, clara) in paletas.items():
        m = classe_mapa == classe
        e, c = np.array(escura, np.float32), np.array(clara, np.float32)
        rgb[m] = e + (c - e) * ruido[m][:, None]
    imagem = Image.fromarray(rgb.clip(0, 255).astype(np.uint8))
    from PIL import ImageFilter
    imagem = imagem.filter(ImageFilter.GaussianBlur(1.2))
    rgb = np.array(imagem)
    flores = (classe_mapa == Classe.GRAMA) & (rng.random((h, w)) > 0.9993)
    rgb[flores] = (246, 222, 96)
    return rgb


def _suavizar_classes(classes, raio=3):
    """Desfoca cada classe e escolhe a mais forte: tira a escadinha herdada dos pixels do satélite."""
    pesos = [np.array(Image.fromarray(((classes == c) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(raio)))
             for c in range(len(Classe))]
    return np.argmax(np.stack(pesos), axis=0).astype(np.uint8)


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
    E = ESCALA_CHAO
    w, h = W // E, H // E

    # 1. chão pelo satélite (resolução reduzida; o jogo amplia com suavização)
    ys = (np.arange(h) * E / rec.mundo_por_pixel + rec.y0).astype(int).clip(0, satelite.shape[0] - 1)
    xs = (np.arange(w) * E / rec.mundo_por_pixel + rec.x0).astype(int).clip(0, satelite.shape[1] - 1)
    classes = classificar(satelite[ys][:, xs])
    for _ in range(2):
        classes = _moda_3x3(classes)
    classes = _suavizar_classes(classes)
    textura = _textura(classes, rng)

    def pontos(elemento, escala=1.0):
        return [(x / escala, y / escala) for x, y in (rec.mundo(g["lat"], g["lon"]) for g in elemento.get("geometry", []))]

    # 2. áreas especiais e vias, desenhadas numa camada com o dobro da resolução e reduzidas (bordas lisas)
    S = 2
    camada = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    for e in osm:
        tg = e["tags"]
        q = [(x * S, y * S) for x, y in pontos(e, E)]
        if len(q) < 3:
            continue
        if tg.get("amenity") == "parking":
            d.polygon(q, fill=(88, 88, 96, 255), outline=(226, 226, 216, 255), width=3)
        elif tg.get("leisure") == "swimming_pool":
            d.polygon(q, fill=(236, 236, 228, 255))
            cx, cy = sum(v[0] for v in q) / len(q), sum(v[1] for v in q) / len(q)
            d.polygon([(cx + (x - cx) * 0.8, cy + (y - cy) * 0.8) for x, y in q], fill=(70, 160, 228, 255))
        elif tg.get("leisure") == "pitch":
            d.polygon(q, fill=(60, 140, 100, 255), outline=(240, 240, 232, 255), width=3)
    larguras = {"motorway": 90, "motorway_link": 60, "service": 64, "residential": 52, "unclassified": 52,
                "footway": 22}
    for etapa in ("borda", "miolo", "faixa"):
        for e in osm:
            via = e["tags"].get("highway")
            if via not in larguras or "building" in e["tags"]:
                continue
            q = [(x * S, y * S) for x, y in pontos(e, E)]
            if len(q) < 2:
                continue
            largura = larguras[via] / E * S
            if etapa == "borda":
                cor, largura = ((150, 136, 112) if via == "footway" else (196, 192, 184)), largura + 6
            elif etapa == "miolo":
                cor = (222, 208, 176) if via == "footway" else (78, 80, 90)
            else:
                if via == "footway":
                    continue
                cor, largura = (236, 220, 120), 2
            d.line(q, fill=(*cor, 255), width=max(1, round(largura)), joint="curve")
            if etapa != "faixa":
                r = largura / 2
                for x, y in (q[0], q[-1]):
                    d.ellipse((x - r, y - r, x + r, y + r), fill=(*cor, 255))
    base = Image.fromarray(textura).convert("RGBA")
    base.alpha_composite(camada.resize((w, h), Image.LANCZOS))
    chao = pygame.image.frombytes(base.convert("RGB").tobytes(), (w, h), "RGB")

    # 3. prédios em resolução cheia
    (SAIDA / "predios").mkdir(parents=True, exist_ok=True)
    for antigo in (SAIDA / "predios").glob("*.png"):
        antigo.unlink()
    predios = []
    for e in osm:
        tg = e["tags"]
        if "building" not in tg:
            continue
        p = pontos(e)
        if len(p) < 3 or max(q[0] for q in p) < 0 or min(q[0] for q in p) > W or max(q[1] for q in p) < 0 \
                or min(q[1] for q in p) > H:
            continue
        sx = [rec.satelite(g["lat"], g["lon"]) for g in e["geometry"]]
        mascara = Image.new("L", (satelite.shape[1], satelite.shape[0]), 0)
        ImageDraw.Draw(mascara).polygon(sx, fill=255)
        dentro = satelite[np.array(mascara) > 0]
        media = dentro.mean(axis=0) if len(dentro) else (200, 200, 200)
        andares = int(re.sub(r"\D", "", tg.get("building:levels", "2")) or 2)
        nome = nome_curto(tg.get("name"))
        telhado = TELHADOS[TELHADO_CONHECIDO[nome]] if nome in TELHADO_CONHECIDO else cor_de_telhado(media)
        sprite, (esquerda, topo) = desenhar_predio(p, telhado, andares, nome)
        ident = f"predio_{e['id']}"
        pygame.image.save(sprite, str(SAIDA / "predios" / f"{ident}.png"))
        predios.append({"id": ident, "nome": nome or "PREDIO",
                        "poligono": [[round(x), round(y)] for x, y in p],
                        "sprite": f"cenario/predios/{ident}.png", "canto": [esquerda, topo]})
    pygame.image.save(chao, str(SAIDA / "mapa_ufj.png"))

    # 4. decorações
    poligonos = [[tuple(q) for q in pr["poligono"]] for pr in predios]
    from jogo.nucleo.colisao import Colisao

    def livre(x, y, folga=60):
        if not (100 < x < W - 100 and 100 < y < H - 100):
            return False
        return not any(Colisao.circulo_poligono((x, y), folga, pol) for pol in poligonos)

    decoracoes = []
    mata = [tuple(v) for v in np.argwhere(classes == Classe.MATA)]
    aleatorio.shuffle(mata)
    usados = []
    for ny, nx in mata:
        x, y = int(nx) * E, int(ny) * E
        if len(usados) >= 320:
            break
        if all((x - ux) ** 2 + (y - uy) ** 2 > 230 ** 2 for ux, uy in usados) and livre(x, y):
            usados.append((x, y))
            decoracoes.append({"tipo": "ipe" if aleatorio.random() < 0.18 else "arvore", "x": x, "y": y})
    for e in osm:
        via = e["tags"].get("highway")
        p = pontos(e)
        if via not in ("service", "footway") or len(p) < 2:
            continue
        passo, tipo, afastamento = (520, "palmeira", 70) if via == "service" else (560, "poste", 26)
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
                if livre(q.x, q.y, 40):
                    decoracoes.append({"tipo": tipo, "x": round(q.x), "y": round(q.y)})
                lado = -lado
                d += passo
            andado += comprimento
    for pr in predios:
        if pr["nome"] in ("RU", "BIBLIOTECA", "CANTINA", "CONVIVENCIA", "CENTRO DE AULAS I", "CENTRO DE AULAS II"):
            base = max(pr["poligono"], key=lambda q: q[1])
            for desvio in (-90, 90):
                if livre(base[0] + desvio, base[1] + 80, 30):
                    decoracoes.append({"tipo": "banco", "x": base[0] + desvio, "y": base[1] + 80})
    acesso = next((e for e in osm if e["tags"].get("name") == "Acesso UFJ - Campus Jatobá"), None)
    if acesso:
        p = pontos(acesso)
        dentro = [q for q in p if 200 < q[0] < W - 200 and 200 < q[1] < H - 200]
        if dentro:
            px, py = min(dentro, key=lambda q: q[1])
            decoracoes.append({"tipo": "portal", "x": round(px), "y": round(py)})
            decoracoes.append({"tipo": "bandeira", "x": round(px) - 230, "y": round(py) + 80})

    inicio = [round((INICIO_SATELITE[0] - rec.x0) * rec.mundo_por_pixel),
              round((INICIO_SATELITE[1] - rec.y0) * rec.mundo_por_pixel)]
    dados = {"largura": W, "altura": H, "chao": "cenario/mapa_ufj.png", "escala": E, "escala_predios": 1,
             "inicio": inicio, "predios": predios, "decoracoes": decoracoes,
             "fonte": "Esri World Imagery (satélite) e OpenStreetMap (ODbL), Campus Jatobá da UFJ"}
    (SAIDA / "mapa_ufj.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    print(f"arena {W}x{H}, chão {w}x{h}, {len(predios)} prédios, {len(decoracoes)} decorações, início {inicio}")


def baixar_fontes():
    """Baixa o mosaico de satélite (Esri World Imagery) e os dados do OpenStreetMap (Overpass).

    O satélite serve só de referência para pintar o chão e não vai para o repositório.
    """
    import io
    import urllib.parse
    import urllib.request
    ENTRADA.mkdir(parents=True, exist_ok=True)
    cabecalho = {"User-Agent": "ufj-survivors-trabalho-poo/1.0"}
    rec = RECORTE
    colunas, linhas = 5, 6
    mosaico = Image.new("RGB", (colunas * 256, linhas * 256))
    for dx in range(colunas):
        for dy in range(linhas):
            url = ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/"
                   f"{rec.zoom}/{rec.tile_y0 + dy}/{rec.tile_x0 + dx}")
            dados = urllib.request.urlopen(urllib.request.Request(url, headers=cabecalho), timeout=30).read()
            mosaico.paste(Image.open(io.BytesIO(dados)), (dx * 256, dy * 256))
    mosaico.save(ENTRADA / "satelite_z17.jpg", quality=92)
    caixa = "-17.9330,-51.7230,-17.9200,-51.7100"
    consulta = (f'[out:json][timeout:60];(way["building"]({caixa});way["highway"]({caixa});'
                f'way["leisure"]({caixa});way["landuse"]({caixa});way["amenity"]({caixa}););out geom tags;')
    pedido = urllib.request.Request("https://overpass-api.de/api/interpreter",
                                    data=urllib.parse.urlencode({"data": consulta}).encode(), headers=cabecalho)
    (ENTRADA / "osm.json").write_bytes(urllib.request.urlopen(pedido, timeout=90).read())
    print(f"fontes gravadas em {ENTRADA}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(RAIZ))
    if "--baixar" in sys.argv or not (ENTRADA / "osm.json").exists():
        baixar_fontes()
    gerar()
