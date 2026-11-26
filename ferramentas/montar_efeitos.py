"""Monta tiras de efeitos e projéteis (explosões, tiros, folhas) a partir de folhas de quadros.

Diferente dos personagens, um efeito não tem "corpo" para alinhar: todos os quadros são
recortados pela mesma caixa (a união do que aparece em todos) e reduzidos na mesma escala,
então o centro do efeito não pula de um quadro para o outro.

Grava em nova_arte/sprites/<pasta>/<animacao>-<n>.png e copia para assets/sprites/.
Uso: python ferramentas/montar_efeitos.py
"""
import shutil
from pathlib import Path

from PIL import Image

from montar_itens import celulas
from pixelizar import gravar_tira, reduzir_suave

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "nova_arte" / "_bruto"
PREPARACAO = RAIZ / "nova_arte" / "sprites"
ASSETS = RAIZ / "assets" / "sprites"

# folha, linhas, colunas, quadros usados, pasta, animação, altura em pixels de tela
EFEITOS = (
    ("golpe_claude_6q.png", 2, 3, range(6), "golpe_claude", "explodir", 150),
    ("tiro_chatgpt_8q.png", 2, 4, range(0, 4), "tiro_chatgpt", "mover", 22),
    ("tiro_chatgpt_8q.png", 2, 4, range(4, 8), "tiro_chatgpt_alucinado", "mover", 22),
    ("folha_e_pequi_8q.png", 2, 4, range(0, 4), "folha_apostila", "mover", 36),
    ("folha_e_pequi_8q.png", 2, 4, range(4, 8), "estouro_pequi", "explodir", 150),
)
CARAMELO = ("caramelo_correr_8q.png", 2, 4, "caramelo", "mover", 38)


def mesma_caixa(quadros, altura):
    """Recorta todos os quadros pela união das caixas e reduz na mesma escala."""
    caixas = [q.getbbox() for q in quadros if q.getbbox()]
    uniao = (min(c[0] for c in caixas), min(c[1] for c in caixas), max(c[2] for c in caixas), max(c[3] for c in caixas))
    escala = altura / (uniao[3] - uniao[1])
    tamanho = (max(1, round((uniao[2] - uniao[0]) * escala)), altura)
    return [q.crop(uniao).resize(tamanho, Image.LANCZOS) for q in quadros]


def publicar(pasta, animacao, tira):
    destino = ASSETS / pasta
    destino.mkdir(parents=True, exist_ok=True)
    for antiga in destino.glob(f"{animacao}-*.png"):
        antiga.unlink()
    shutil.copy(tira, destino / Path(tira).name)
    print(destino / Path(tira).name)


def main():
    for folha, n_linhas, colunas, usados, pasta, animacao, altura in EFEITOS:
        partes = celulas(Image.open(BRUTO / folha).convert("RGBA"), n_linhas, colunas, borda=0.01)
        publicar(pasta, animacao, gravar_tira(mesma_caixa([partes[i] for i in usados], altura), PREPARACAO / pasta, animacao))
    folha, n_linhas, colunas, pasta, animacao, altura = CARAMELO
    partes = celulas(Image.open(BRUTO / folha).convert("RGBA"), n_linhas, colunas, borda=0.01)
    tira = gravar_tira(reduzir_suave(partes, altura), PREPARACAO / pasta, animacao)
    publicar(pasta, animacao, tira)
    primeiro = Image.open(tira)
    primeiro.crop((0, 0, primeiro.width // len(partes), primeiro.height)).save(ASSETS / f"{pasta}.png")


if __name__ == "__main__":
    main()
