"""UFJ Survivors. Rode com: python main.py"""
from jogo.aplicacao import Aplicacao
from jogo.cenas.partida import CenaPartida
from jogo.jogador.alunos import AlunoAgil


def main():
    app = Aplicacao()
    app.executar(CenaPartida(app, AlunoAgil))


if __name__ == "__main__":
    main()
