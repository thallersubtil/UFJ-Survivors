"""Teste de fumaça do executável: roda empacotado (PyInstaller) e sem janela.

Monta o aluno, escolhe cada classe clicando na carteirinha, joga 20 s de partida
com cada uma e abre o Centro Acadêmico e o Treino. Imprime "SMOKE OK" no fim;
qualquer exceção imprime o erro e "SMOKE FALHOU" (código de saída 1).

Existe porque o executável pode abrir e mesmo assim quebrar dentro da partida:
os inimigos são carregados por pkgutil.iter_modules e o PyInstaller só empacota
o que encontra em import direto. Quem gera o executável é
ferramentas/gerar_executavel.py, que roda este teste antes de atualizar a pasta.
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame  # noqa: E402


def _tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def main():
    from jogo.aplicacao import Aplicacao
    from jogo.cenas.centro_academico import CenaCentroAcademico
    from jogo.cenas.personalizacao import CenaPersonalizacao
    from jogo.cenas.selecao import CLASSES
    from jogo.cenas.treino import CenaTreino
    from jogo.loja.progresso import Progresso
    from jogo.ranking import Ranking

    pygame.display.set_mode((1, 1))
    app = Aplicacao(pygame.Surface((1280, 720)))
    pasta = Path(tempfile.mkdtemp())                       # não mexe nos saves de verdade
    app.ranking, app.progresso = Ranking(pasta / "r.json"), Progresso(pasta / "p.json")
    for indice, classe in enumerate(CLASSES):
        app.trocar(CenaPersonalizacao(app))
        app.passo(1 / 60, [_tecla(pygame.K_RETURN)])        # tira a foto
        for _ in range(120):
            app.passo(1 / 60, [])
        selecao = app.cena_atual
        selecao.escolher(indice)
        for _ in range(30):
            app.passo(1 / 60, [])
        clique = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=selecao.cartoes[0].center, button=1)
        app.passo(1 / 60, [clique])
        for _ in range(20 * 60):
            app.passo(1 / 60, [])
            if type(app.cena_atual).__name__ in ("CenaNivel", "CenaBau"):
                app.passo(1 / 60, [_tecla(pygame.K_1)])
        print("ok", classe.__name__, type(app.cena_atual).__name__)
    for cena in (CenaCentroAcademico, CenaTreino):
        app.trocar(cena(app))
        for _ in range(60):
            app.passo(1 / 60, [])
        print("ok", cena.__name__)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("SMOKE FALHOU")
        sys.exit(1)
    print("SMOKE OK")
