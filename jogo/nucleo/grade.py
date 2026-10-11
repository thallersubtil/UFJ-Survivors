"""Grade espacial para achar entidades próximas sem testar todas contra todas."""
from collections import defaultdict


class GradeEspacial:
    def __init__(self, tamanho_celula=96):
        self.tamanho = tamanho_celula
        self._celulas = defaultdict(list)

    def _chave(self, x, y):
        return int(x // self.tamanho), int(y // self.tamanho)

    def reconstruir(self, entidades):
        self._celulas.clear()
        for e in entidades:
            self._celulas[self._chave(e.posicao.x, e.posicao.y)].append(e)

    def proximos(self, posicao, raio):
        """Entidades das células que tocam o quadrado em volta do círculo."""
        x0, y0 = self._chave(posicao[0] - raio, posicao[1] - raio)
        x1, y1 = self._chave(posicao[0] + raio, posicao[1] + raio)
        resultado = []
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                resultado.extend(self._celulas.get((cx, cy), ()))
        return resultado
