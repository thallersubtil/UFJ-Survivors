"""Monta todos os sprites animados do jogo a partir das folhas geradas em arte_bruta/.

Cada linha da RECEITA diz: folha, personagem (pasta em assets/sprites/), animação,
número de quadros na folha, altura nativa em pixels e, opcionalmente, a altura da
versão gigante (mini-chefe), quais quadros usar e se a folha tem vários objetos
diferentes lado a lado (cada um pixelizado sozinho).

Uso: python ferramentas/montar_sprites.py
"""
from pathlib import Path

from PIL import Image

from pixelizar import PASTA_SPRITES, dividir, gravar_tira, pixelizar

BRUTA = Path(__file__).resolve().parent.parent / "arte_bruta"

# (folha, personagem, animação, quadros na folha, altura, extras)
RECEITA = [
    ("teste_aluno1_parado.png", "aluno1", "parado", 4, 48, {}),
    ("teste_aluno1_olhos.png", "aluno1", "andar", 6, 48, {}),
    ("folhas/aluno2_parado.png", "aluno2", "parado", 4, 50, {}),
    ("folhas/aluno2_andar.png", "aluno2", "andar", 6, 50, {}),
    ("folhas/aluno2_ssj_parado.png", "aluno2_ssj", "parado", 4, 54, {}),
    ("folhas/aluno2_ssj_andar.png", "aluno2_ssj", "andar", 6, 54, {}),
    ("folhas/professor_parado.png", "professor", "parado", 4, 72, {"cores": 32}),
    ("folhas/professor_andar.png", "professor", "andar", 6, 72, {"cores": 32}),
    ("teste_bug_lowres.png", "bug", "andar", 4, 18, {}),
    ("folhas/calculadora_andar.png", "calculadora", "andar", 4, 26, {"gigante": 78}),
    ("folhas/mouse_andar.png", "mouse", "andar", 4, 18, {}),
    ("folhas/mouse_andar.png", "mouse", "parado", 4, 18, {"usar": [0]}),
    ("folhas/caixinha_andar.png", "caixinha", "andar", 4, 24, {}),
    ("folhas/caixinha_andar.png", "caixinha_pequena", "andar", 4, 15, {}),
    ("folhas/pi_andar.png", "pi", "andar", 4, 24, {}),
    ("folhas/ponteiro_andar.png", "ponteiro", "andar", 4, 18, {"cores": 10}),
    ("folhas/pilha_andar.png", "pilha", "andar", 4, 26, {}),
    ("folhas/pente_ram_andar.png", "pente_ram", "andar", 4, 16, {"gigante": 48}),
    ("folhas/caramelo_mover.png", "caramelo", "mover", 6, 22, {}),
    ("folhas/chatgpt_mover.png", "chatgpt", "mover", 4, 20, {}),
    ("folhas/claude_mover.png", "claude", "mover", 4, 18, {}),
    ("folhas/fusca_mover.png", "fusca", "mover", 4, 30, {}),
    ("folhas/caramelo_no_fusca_mover.png", "caramelo_no_fusca", "mover", 4, 34, {}),
    ("folhas/cobra_mover.png", "cobra", "mover", 4, 12, {"cores": 12}),
    ("folhas/nota_mover.png", "nota", "mover", 4, 12, {"cores": 10}),
    ("folhas/bandeira_parado.png", "bandeira", "parado", 4, 60, {"cores": 12}),
    ("folhas/portal_ufj.png", "portal_ufj", "parado", 1, 96, {"cores": 24}),
    ("folhas/arvores.png", "palmeira", "parado", 3, 66, {"objeto": 0}),
    ("folhas/arvores.png", "ipe", "parado", 3, 60, {"objeto": 1}),
    ("folhas/arvores.png", "arvore_cerrado", "parado", 3, 54, {"objeto": 2}),
    ("folhas/poste_banco.png", "poste", "parado", 2, 58, {"objeto": 0, "cores": 10}),
    ("folhas/poste_banco.png", "banco", "parado", 2, 18, {"objeto": 1, "cores": 10}),
]


def montar(folha, personagem, animacao, n, altura, extras):
    brutos = dividir(Image.open(BRUTA / folha).convert("RGBA"), n)
    if "objeto" in extras:
        brutos = [brutos[extras["objeto"]]]
    if "usar" in extras:
        brutos = [brutos[i] for i in extras["usar"]]
    cores = extras.get("cores", 24)
    caminhos = [gravar_tira(pixelizar(brutos, altura, cores), PASTA_SPRITES / personagem, animacao)]
    if "gigante" in extras:
        caminhos.append(gravar_tira(pixelizar(brutos, extras["gigante"], cores + 8),
                                    PASTA_SPRITES / f"{personagem}_gigante", animacao))
    return caminhos


def main():
    for linha in RECEITA:
        for caminho in montar(*linha):
            print(caminho.relative_to(PASTA_SPRITES.parent.parent))


if __name__ == "__main__":
    main()
