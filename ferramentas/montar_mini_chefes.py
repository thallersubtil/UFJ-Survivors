"""Monta a arte dos mini-chefes do mapa e dos lacaios deles a partir das folhas brutas (nova_arte/_bruto/).

Mini-chefes: folha de 8 quadros andando (viram a tira assets/sprites/<pasta>/andar-8.png) e o rosto
para o mini-mapa (assets/rostos/<pasta>.png), recortado do primeiro quadro. Lacaios: folhas 4x3 com um
bicho por linha. A arte vem olhando para a esquerda e o jogo espera a direita, então tudo é espelhado.

Uso: python ferramentas/montar_mini_chefes.py
"""
from pathlib import Path

from PIL import Image, ImageOps

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
    "reitor": ("mc2_reitor_andar_8q.png", 1, 250, 0.20),
    "lobo_guara": ("mc2_lobo_guara_andar_8q.png", 2, 112, 0.55),
    "loira": ("mc2_loira_v2_andar_8q.png", 2, 98, 0.58),
    "culto": ("mc2_culto_andar_8q.png", 2, 100, 0.60),
    "gotica": ("mc2_gotica_andar_8q.png", 2, 94, 0.60),
    "et": ("mc2_et_andar_8q.png", 2, 84, 0.62),
    "agroboy": ("mc2_agroboy_andar_8q.png", 2, 100, 0.60),
}
# folha 4 colunas x 3 linhas: (pasta, altura na tela) de cada linha
LACAIOS = {
    "mc2_lacaios_a.png": (("coxinha", 36), ("morcego", 34), ("livro_atrasado", 40)),
    "mc2_lacaios_b.png": (("cobaia", 32), ("carimbo", 42), ("lobinho", 36)),
    "mc2_lacaios_c.png": (("dente", 40), ("cultista", 46), ("mini_ovni", 40)),
    "mc2_lacaios_d.png": (("boi", 56), ("hb20", 58), ("caminhonete", 92)),
}
GATO = ("mc2_gato_alienigena_8q.png", "gato_alienigena", 38)
LADO_DO_ROSTO = 64


def espelhados(quadros):
    return [ImageOps.mirror(q) for q in quadros]


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


def main():
    ROSTOS.mkdir(parents=True, exist_ok=True)
    for pasta, (folha, n_linhas, altura, cabeca) in MINI_CHEFES.items():
        imagem = Image.open(BRUTO / folha).convert("RGBA")
        faixas = linhas(imagem, n_linhas) if n_linhas > 1 else [imagem]
        quadros = [q for faixa in faixas for q in dividir(faixa, 8 // n_linhas)]
        for antiga in (SPRITES / pasta).glob("andar-*.png"):
            antiga.unlink()
        caminho = gravar_tira(reduzir_suave(espelhados(quadros), altura), SPRITES / pasta, "andar")
        rosto(Image.open(caminho).convert("RGBA"), 8, cabeca).save(ROSTOS / f"{pasta}.png")
        print(caminho)
    for folha, bichos in LACAIOS.items():
        faixas = linhas(Image.open(BRUTO / folha).convert("RGBA"), len(bichos))
        for faixa, (pasta, altura) in zip(faixas, bichos):
            print(gravar_tira(reduzir_suave(espelhados(dividir(faixa, 4)), altura), SPRITES / pasta, "andar"))
    folha, pasta, altura = GATO
    faixas = linhas(Image.open(BRUTO / folha).convert("RGBA"), 2)
    quadros = [q for faixa in faixas for q in dividir(faixa, 4)]
    print(gravar_tira(reduzir_suave(espelhados(quadros), altura), SPRITES / pasta, "andar"))


if __name__ == "__main__":
    main()
