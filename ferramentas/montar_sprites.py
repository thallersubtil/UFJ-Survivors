"""Monta todos os sprites animados do jogo a partir das folhas geradas em arte_bruta/.

Cada linha da RECEITA diz: folha, personagem (pasta em assets/sprites/), animação,
número de quadros na folha, altura na tela em pixels e, opcionalmente, a altura da
versão gigante (mini-chefe), quais quadros usar e se a folha tem vários objetos
diferentes lado a lado (cada um pixelizado sozinho).

Uso: python ferramentas/montar_sprites.py
"""
from pathlib import Path

from PIL import Image

from pixelizar import PASTA_SPRITES, dividir, gravar_tira, reduzir

BRUTA = Path(__file__).resolve().parent.parent / "arte_bruta"

# (folha, personagem, animação, quadros na folha, altura, extras)
# Nas folhas de andar de 6 quadros, os quadros 5 e 6 repetiam a passada aberta (o
# andar tropeçava); os 4 primeiros formam o ciclo largo-estreito-largo-estreito.
RECEITA = [
    ("teste_aluno1_parado.png", "aluno1", "parado", 4, 96, {}),
    ("teste_aluno1_olhos.png", "aluno1", "andar", 6, 96, {"usar": [0, 1, 2, 3]}),
    ("folhas/aluno2_parado.png", "aluno2", "parado", 4, 100, {}),
    ("folhas/aluno2_andar.png", "aluno2", "andar", 6, 100, {"usar": [0, 1, 2, 3]}),
    ("folhas/aluno2_ssj_parado.png", "aluno2_ssj", "parado", 4, 108, {}),
    ("folhas/aluno2_ssj_andar.png", "aluno2_ssj", "andar", 6, 108, {"usar": [0, 1, 2, 3]}),
    ("folhas/professor_parado.png", "professor", "parado", 4, 144, {"cores": 32}),
    ("folhas/professor_andar.png", "professor", "andar", 6, 144, {"cores": 32, "usar": [0, 1, 2, 3]}),
    ("teste_bug_lowres.png", "bug", "andar", 4, 36, {}),
    ("folhas/calculadora_andar.png", "calculadora", "andar", 4, 52, {"gigante": 156}),
    ("folhas/mouse_andar.png", "mouse", "andar", 4, 36, {}),
    ("folhas/mouse_andar.png", "mouse", "parado", 4, 36, {"usar": [0]}),
    ("folhas/caixinha_andar.png", "caixinha", "andar", 4, 48, {}),
    ("folhas/caixinha_andar.png", "caixinha_pequena", "andar", 4, 30, {}),
    ("folhas/pi_andar.png", "pi", "andar", 4, 48, {}),
    ("folhas/ponteiro_andar.png", "ponteiro", "andar", 4, 36, {"cores": 10}),
    ("folhas/pilha_andar.png", "pilha", "andar", 4, 52, {}),
    ("folhas/pente_ram_andar.png", "pente_ram", "andar", 4, 32, {"gigante": 96}),
    ("folhas/caramelo_mover.png", "caramelo", "mover", 6, 44, {}),
    ("folhas/chatgpt_mover.png", "chatgpt", "mover", 4, 40, {}),
    ("folhas/claude_mover.png", "claude", "mover", 4, 36, {}),
    ("folhas/fusca_mover.png", "fusca", "mover", 4, 60, {}),
    ("folhas/caramelo_no_fusca_mover.png", "caramelo_no_fusca", "mover", 4, 68, {}),
    ("folhas/cobra_mover.png", "cobra", "mover", 4, 24, {"cores": 12}),
    ("folhas/nota_mover.png", "nota", "mover", 4, 24, {"cores": 10}),
    ("folhas/bandeira_parado.png", "bandeira", "parado", 4, 120, {"cores": 12}),
    ("folhas/portal_ufj.png", "portal_ufj", "parado", 1, 192, {"cores": 24}),
    ("folhas/arvores.png", "palmeira", "parado", 3, 132, {"objeto": 0}),
    ("folhas/arvores.png", "ipe", "parado", 3, 120, {"objeto": 1}),
    ("folhas/arvores.png", "arvore_cerrado", "parado", 3, 108, {"objeto": 2}),
    ("folhas/poste_banco.png", "poste", "parado", 2, 116, {"objeto": 0, "cores": 10}),
    ("folhas/poste_banco.png", "banco", "parado", 2, 36, {"objeto": 1, "cores": 10}),
]


def montar(folha, personagem, animacao, n, altura, extras):
    brutos = dividir(Image.open(BRUTA / folha).convert("RGBA"), n)
    if "objeto" in extras:
        brutos = [brutos[extras["objeto"]]]
    if "usar" in extras:
        brutos = [brutos[i] for i in extras["usar"]]
    cores = max(48, extras.get("cores", 48))
    caminhos = [gravar_tira(reduzir(brutos, altura, cores), PASTA_SPRITES / personagem, animacao)]
    if "gigante" in extras:
        caminhos.append(gravar_tira(reduzir(brutos, extras["gigante"], cores + 16),
                                    PASTA_SPRITES / f"{personagem}_gigante", animacao))
    return caminhos


def main():
    for linha in RECEITA:
        for caminho in montar(*linha):
            print(caminho.relative_to(PASTA_SPRITES.parent.parent))


if __name__ == "__main__":
    main()
