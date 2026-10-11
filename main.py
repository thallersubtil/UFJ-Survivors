"""UFJ Survivors. Rode com: python main.py"""
from jogo.aplicacao import Aplicacao
from jogo.cenas.titulo import CenaTitulo


def main():
    app = Aplicacao()
    app.executar(CenaTitulo(app))


if __name__ == "__main__":
    main()
