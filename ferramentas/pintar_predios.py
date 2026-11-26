"""Pinta os prédios do mapa no estilo do resto do jogo: telhado texturizado, paredes com janelas e sombra.

Cada prédio é um sprite 3/4 em resolução de tela: a base é o contorno real (o mesmo polígono da
colisão), as paredes viradas para baixo sobem a altura dos andares e o telhado é o contorno
deslocado para cima. O canto do sprite continua o mesmo de antes, então o mapa (colisão e
posição) não muda; só a pintura.

Texturas em ferramentas/texturas/: telhado_ceramica.png, telhado_metal.png, telhado_laje.png e
telhado_objetos_8.png (caixa d'água, ar-condicionado, placas solares...).

Uso: python ferramentas/pintar_predios.py     (repinta assets/cenario/predios/ a partir de mapa_ufj.json)
"""
import json
import math
import random
import zlib
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
TEXTURAS = Path(__file__).resolve().parent / "texturas"
CENARIO = RAIZ / "assets" / "cenario"
FONTE = RAIZ / "assets" / "fontes" / "pixelify-sans-ufj-700.ttf"

CONTORNO = (26, 22, 34, 255)
MARGEM = 6                      # folga em volta do contorno (igual à do sprite antigo: o canto não muda)
SOMBRA = (22, 12)               # deslocamento da sombra no chão
ALTURA_ANDAR = 64
LADO_TEXTURA = 448
MODULO_JANELA = 58              # distância entre janelas na parede

# estilo: textura do telhado, cor da parede, cor do beiral, se tem cumeeira, quantos objetos no teto
ESTILOS = {
    "ceramica": ("telhado_ceramica.png", (238, 222, 190), (120, 58, 40), True, 0),
    "metal": ("telhado_metal.png", (224, 228, 232), (92, 104, 122), True, 2),
    "laje": ("telhado_laje.png", (232, 226, 214), (150, 146, 138), False, 5),
}
ESTILO_CONHECIDO = {"BIBLIOTECA": "metal", "REITORIA": "laje", "RU": "ceramica", "CANTINA": "ceramica"}
SORTEIO_DE_ESTILO = ("ceramica", "ceramica", "ceramica", "metal", "metal", "laje", "laje")
OBJETOS = ("ar_condicionado", "caixa_dagua", "placa_solar", "claraboia", "exaustor", "antena", "alcapao",
           "aquecedor_solar")
ALTURA_OBJETO = {"ar_condicionado": 40, "caixa_dagua": 52, "placa_solar": 50, "claraboia": 40, "exaustor": 40,
                 "antena": 46, "alcapao": 46, "aquecedor_solar": 46}


def estilo_do_predio(ident, nome):
    """Estilo fixo por prédio: os conhecidos pelo nome, os outros sorteados sempre do mesmo jeito."""
    return ESTILO_CONHECIDO.get(nome) or SORTEIO_DE_ESTILO[zlib.crc32(ident.encode()) % len(SORTEIO_DE_ESTILO)]


def _tom(cor, fator):
    return tuple(max(0, min(255, round(v * fator))) for v in cor[:3])


@lru_cache(maxsize=None)
def textura(arquivo):
    """Textura do telhado, repetível (mistura com ela mesma deslocada meia volta para sumir com a emenda)."""
    lado = LADO_TEXTURA
    a = np.asarray(Image.open(TEXTURAS / arquivo).convert("RGB").resize((lado, lado), Image.LANCZOS), np.float32)
    b = np.roll(a, (lado // 2, lado // 2), axis=(0, 1))
    rampa = 1 - np.abs(np.linspace(-1, 1, lado))
    peso = np.clip(np.minimum.outer(rampa, rampa) * 4, 0, 1)[..., None]
    return Image.fromarray((a * peso + b * (1 - peso)).astype(np.uint8))


@lru_cache(maxsize=None)
def objetos_de_telhado():
    folha = Image.open(TEXTURAS / "telhado_objetos_8.png").convert("RGBA")
    largura, altura = folha.width // 4, folha.height // 2
    achados = {}
    for i, nome in enumerate(OBJETOS):
        celula = folha.crop(((i % 4) * largura, (i // 4) * altura, (i % 4 + 1) * largura, (i // 4 + 1) * altura))
        desenho = celula.crop(celula.getbbox())
        alvo = ALTURA_OBJETO[nome]
        achados[nome] = desenho.resize((max(1, round(desenho.width * alvo / desenho.height)), alvo), Image.LANCZOS)
    return achados


def _parede(comprimento, altura, cor, andares, com_porta, sorteio):
    """Parede vista de frente (antes de inclinar): reboco, rodapé, sombra do beiral, janelas e porta."""
    largura = max(4, round(comprimento))
    img = Image.new("RGBA", (largura, altura), (*cor, 255))
    d = ImageDraw.Draw(img)
    for _ in range(largura * altura // 220):                       # manchinhas do reboco
        x, y = sorteio.randrange(largura), sorteio.randrange(altura)
        d.rectangle((x, y, x + sorteio.randrange(2, 7), y + 1), fill=(*_tom(cor, sorteio.choice((0.95, 1.04))), 255))
    for i in range(16):                                            # sombra do beiral
        d.line((0, i, largura, i), fill=(*_tom(cor, 0.62 + 0.38 * i / 16), 255))
    for andar in range(1, andares):                                # friso entre os andares
        y = altura - andar * ALTURA_ANDAR
        d.rectangle((0, y - 2, largura, y + 1), fill=(*_tom(cor, 0.8), 255))
    d.rectangle((0, altura - 10, largura, altura), fill=(*_tom(cor, 0.58), 255))    # rodapé
    d.line((0, altura - 11, largura, altura - 11), fill=(*_tom(cor, 0.45), 255))

    colunas = int((largura - 16) // MODULO_JANELA)
    folga = (largura - colunas * MODULO_JANELA) / 2
    porta = colunas // 2 if com_porta and colunas >= 1 else None
    vidro, vidro_claro, moldura = (70, 124, 178), (150, 204, 236), (248, 246, 238)
    for c in range(colunas):
        meio = folga + (c + 0.5) * MODULO_JANELA
        for andar in range(andares):
            base = altura - andar * ALTURA_ANDAR
            if andar == 0 and c == porta:
                x0, x1, y0, y1 = meio - 17, meio + 17, base - 50, base - 1
                d.rectangle((x0 - 3, y0 - 3, x1 + 3, y1), fill=CONTORNO)
                d.rectangle((x0, y0, x1, y1), fill=(96, 62, 44, 255))
                d.rectangle((x0 + 3, y0 + 4, meio - 2, y1 - 18), fill=(*vidro, 255))
                d.rectangle((meio + 2, y0 + 4, x1 - 3, y1 - 18), fill=(*vidro, 255))
                d.line((meio, y0, meio, y1), fill=CONTORNO)
                d.rectangle((x0 - 8, y0 - 10, x1 + 8, y0 - 4), fill=(*_tom(cor, 0.5), 255))     # marquise
                continue
            x0, x1, y0, y1 = meio - 16, meio + 16, base - 48, base - 20
            d.rectangle((x0 - 3, y0 - 3, x1 + 3, y1 + 3), fill=CONTORNO)
            d.rectangle((x0 - 1, y0 - 1, x1 + 1, y1 + 1), fill=(*moldura, 255))
            d.rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), fill=(*vidro, 255))
            d.polygon(((x0 + 1, y1 - 1), (x0 + 1, y1 - 12), (x0 + 12, y0 + 1), (x0 + 22, y0 + 1)), fill=(*vidro_claro, 255))
            d.line((meio, y0, meio, y1), fill=(*moldura, 255), width=2)
            d.rectangle((x0 - 5, y1 + 3, x1 + 5, y1 + 6), fill=(*_tom(cor, 0.7), 255))          # peitoril
    return img


def _faces_visiveis(base):
    """Arestas da base viradas para baixo (as paredes que a câmera vê), das de trás para as da frente."""
    n = len(base)
    sentido = sum(base[i][0] * base[(i + 1) % n][1] - base[(i + 1) % n][0] * base[i][1] for i in range(n))
    faces = []
    for i in range(n):
        a, b = base[i], base[(i + 1) % n]
        dx = b[0] - a[0]
        if (dx if sentido > 0 else -dx) < 0:      # y cresce para baixo: no sentido horário, a face sul anda para a esquerda
            faces.append((max(a[1], b[1]), *((a, b) if a[0] <= b[0] else (b, a))))
    return sorted(faces)


def pintar_predio(poligono, altura_parede, estilo, nome="", semente=0, canto=None):
    """Sprite do prédio (imagem RGBA) e o canto superior esquerdo dele no mundo.

    `canto` mantém o canto de um sprite que já existe (o mapa gravado arredonda o contorno).
    """
    arquivo, cor_parede, cor_beiral, cumeeira, n_objetos = ESTILOS[estilo]
    sorteio = random.Random(semente)
    xs, ys = [p[0] for p in poligono], [p[1] for p in poligono]
    esquerda, topo = canto or (int(min(xs)) - MARGEM, int(min(ys)) - altura_parede - MARGEM)
    largura = int(max(xs)) - esquerda + MARGEM + 1 + SOMBRA[0]
    altura = int(max(ys)) - topo + MARGEM + 1 + SOMBRA[1]
    base = [(x - esquerda, y - topo) for x, y in poligono]
    teto = [(x, y - altura_parede) for x, y in base]
    andares = max(1, round(altura_parede / ALTURA_ANDAR))
    sprite = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))

    # sombra no chão
    mancha = Image.new("L", (largura, altura), 0)
    ImageDraw.Draw(mancha).polygon([(x + SOMBRA[0], y + SOMBRA[1]) for x, y in base], fill=95)
    sprite.paste((14, 24, 20, 255), mask=mancha.filter(ImageFilter.GaussianBlur(3)))

    # paredes
    faces = _faces_visiveis(base)
    maior = max(faces, key=lambda f: abs(f[2][0] - f[1][0]), default=None)
    for face in faces:
        _, a, b = face
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dx < 3:
            continue
        comprimento = math.hypot(dx, dy)
        luz = 1.0 - 0.3 * abs(dy) / comprimento - (0.08 if dy < 0 else 0)       # faces inclinadas ficam mais escuras
        frente = _parede(comprimento, altura_parede, _tom(cor_parede, luz), andares, face is maior, sorteio)
        k = comprimento / dx
        inclinada = frente.transform((largura, altura), Image.AFFINE,
                                     (k, 0, -a[0] * k, -dy / dx, 1, -a[1] + a[0] * dy / dx + altura_parede),
                                     Image.BICUBIC)
        quina = [a, b, (b[0], b[1] - altura_parede), (a[0], a[1] - altura_parede)]
        recorte = Image.new("L", (largura, altura), 0)
        ImageDraw.Draw(recorte).polygon(quina, fill=255)
        sprite.paste(inclinada, mask=ImageChops.multiply(recorte, inclinada.getchannel("A")))
        ImageDraw.Draw(sprite).line(quina + [quina[0]], fill=CONTORNO, width=3)

    # telhado: textura alinhada com o lado mais comprido do prédio
    n = len(teto)
    lados = [(math.hypot(teto[(i + 1) % n][0] - teto[i][0], teto[(i + 1) % n][1] - teto[i][1]), i) for i in range(n)]
    i = max(lados)[1]
    angulo = math.degrees(math.atan2(teto[(i + 1) % n][1] - teto[i][1], teto[(i + 1) % n][0] - teto[i][0]))
    diagonal = int(math.hypot(largura, altura)) + LADO_TEXTURA
    ladrilho = textura(arquivo)
    tapete = Image.new("RGB", (diagonal, diagonal))
    for y in range(0, diagonal, LADO_TEXTURA):
        for x in range(0, diagonal, LADO_TEXTURA):
            tapete.paste(ladrilho, (x, y))
    tapete = tapete.rotate(-angulo, Image.BICUBIC)
    sobra = ((diagonal - largura) // 2, (diagonal - altura) // 2)
    tapete = tapete.crop((sobra[0], sobra[1], sobra[0] + largura, sobra[1] + altura)).convert("RGBA")
    recorte = Image.new("L", (largura, altura), 0)
    ImageDraw.Draw(recorte).polygon(teto, fill=255)
    meio = (sum(q[0] for q in teto) / n, sum(q[1] for q in teto) / n)
    if cumeeira:                                   # duas águas: um lado do eixo fica na sombra
        rad = math.radians(angulo)
        yy, xx = np.mgrid[0:altura, 0:largura]
        lado_escuro = ((xx - meio[0]) * -math.sin(rad) + (yy - meio[1]) * math.cos(rad)) > 0
        escuro = Image.fromarray((lado_escuro * 255).astype(np.uint8))
        tapete.paste(Image.blend(tapete, Image.new("RGBA", tapete.size, (20, 14, 30, 255)), 0.24), mask=escuro)
    miolo = recorte.filter(ImageFilter.MinFilter(15))
    beiral = ImageChops.subtract(recorte, miolo)
    tapete.paste(Image.blend(tapete, Image.new("RGBA", tapete.size, (*cor_beiral, 255)), 0.72), mask=beiral)
    sprite.paste(tapete, mask=recorte)
    d = ImageDraw.Draw(sprite)
    d.line(teto + [teto[0]], fill=CONTORNO, width=4)
    for q in teto:
        d.ellipse((q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2), fill=CONTORNO)

    # objetos no teto, longe da borda e da placa
    livre = np.array(recorte.filter(ImageFilter.MinFilter(61))) > 0
    candidatos = np.argwhere(livre)
    postos = []
    tentativas = 0
    while len(candidatos) and len(postos) < n_objetos and tentativas < 200:
        tentativas += 1
        y, x = candidatos[sorteio.randrange(len(candidatos))]
        if abs(x - meio[0]) < 110 and abs(y - meio[1]) < 50:
            continue
        if any(math.hypot(x - px, y - py) < 78 for px, py in postos):
            continue
        postos.append((x, y))
    for x, y in sorted(postos, key=lambda p: p[1]):
        objeto = objetos_de_telhado()[sorteio.choice(OBJETOS)]
        sombra = Image.new("RGBA", objeto.size, (10, 8, 20, 90))
        sprite.paste(sombra, (int(x - objeto.width / 2 + 6), int(y - objeto.height / 2 + 5)), objeto.getchannel("A").point(lambda v: v * 90 // 255))
        sprite.alpha_composite(objeto, (int(x - objeto.width / 2), int(y - objeto.height / 2)))

    if nome:
        fonte = ImageFont.truetype(str(FONTE), 24)
        d = ImageDraw.Draw(sprite)
        caixa = d.textbbox((0, 0), nome, font=fonte)
        w, h = caixa[2] - caixa[0] + 20, caixa[3] - caixa[1] + 12
        x0, y0 = round(meio[0] - w / 2), round(meio[1] - h / 2)
        d.rounded_rectangle((x0 - 3, y0 - 3, x0 + w + 3, y0 + h + 3), 8, fill=CONTORNO)
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 6, fill=(64, 52, 92, 255), outline=(240, 196, 90, 255), width=2)
        d.text((x0 + 10 - caixa[0], y0 + 6 - caixa[1]), nome, font=fonte, fill=(255, 248, 230, 255))
    return sprite, (esquerda, topo)


def main():
    arquivo = CENARIO / "mapa_ufj.json"
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    for predio in dados["predios"]:
        poligono = [tuple(p) for p in predio["poligono"]]
        altura_parede = int(min(p[1] for p in poligono)) - MARGEM - predio["canto"][1]
        estilo = estilo_do_predio(predio["id"], predio["nome"])
        nome = "" if predio["nome"] == "PREDIO" else predio["nome"]
        sprite, _ = pintar_predio(poligono, altura_parede, estilo, nome, zlib.crc32(predio["id"].encode()),
                                  tuple(predio["canto"]))
        sprite.save(RAIZ / "assets" / predio["sprite"])
        print(predio["id"], predio["nome"], estilo, sprite.size, altura_parede)


if __name__ == "__main__":
    main()
