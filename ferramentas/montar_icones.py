"""Corta uma folha de ícones em grade e grava cada um em nova_arte/icones/<nome>.png (64x64).

A folha tem fundo transparente e os ícones em grade regular (--linhas linhas), lidos da
esquerda para a direita e de cima para baixo, na ordem dos NOMES. Não toca em assets/.

Uso:
  python ferramentas/montar_icones.py FOLHA --linhas 2 apostila atletica bigorna ...
"""
import argparse
from pathlib import Path

from PIL import Image

from pixelizar import dividir, linhas

PREPARACAO = Path(__file__).resolve().parent.parent / "nova_arte"
LADO, MARGEM = 64, 2


def encaixar(icone):
    """Reduz o ícone para caber em LADO x LADO, centralizado, mantendo a proporção."""
    icone = icone.crop(icone.getbbox())
    fator = (LADO - 2 * MARGEM) / max(icone.size)
    r = icone.resize((max(1, round(icone.width * fator)), max(1, round(icone.height * fator))), Image.LANCZOS)
    tela = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    tela.paste(r, ((LADO - r.width) // 2, (LADO - r.height) // 2))
    return tela


def main():
    p = argparse.ArgumentParser()
    p.add_argument("folha")
    p.add_argument("nomes", nargs="+")
    p.add_argument("--linhas", type=int, default=1)
    a = p.parse_args()
    folha = Image.open(a.folha).convert("RGBA")
    por_linha = len(a.nomes) // a.linhas
    faixas = linhas(folha, a.linhas) if a.linhas > 1 else [folha]
    icones = [q for faixa in faixas for q in dividir(faixa, por_linha)]
    pasta = PREPARACAO / "icones"
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, icone in zip(a.nomes, icones):
        encaixar(icone).save(pasta / f"{nome}.png")
        print(pasta / f"{nome}.png")


if __name__ == "__main__":
    main()
