"""Animação por quadros: Animacao (uma sequência) e Animador (o conjunto de um personagem)."""


class Animacao:
    """Sequência de quadros tocada a um certo número de quadros por segundo."""

    def __init__(self, quadros, fps=8, repetir=True):
        if not quadros:
            raise ValueError("uma animação precisa de pelo menos um quadro")
        self.quadros = list(quadros)
        self.fps = fps
        self.repetir = repetir

    @property
    def duracao(self):
        return len(self.quadros) / self.fps

    def quadro(self, tempo):
        indice = int(tempo * self.fps)
        if self.repetir:
            indice %= len(self.quadros)
        else:
            indice = min(indice, len(self.quadros) - 1)
        return self.quadros[indice]

    def terminou(self, tempo):
        return not self.repetir and tempo >= self.duracao


class Animador:
    """Guarda as animações de um personagem e qual está tocando agora.

    Personagens contêm um Animador (composição) e só dizem qual animação querem
    com `tocar("andar")`; o Animador cuida do tempo e do quadro.
    """

    def __init__(self, animacoes, inicial=None):
        self.animacoes = dict(animacoes)
        self.atual = inicial if inicial in self.animacoes else next(iter(self.animacoes))
        self.tempo = 0.0

    def tocar(self, nome):
        if nome in self.animacoes and nome != self.atual:
            self.atual = nome
            self.tempo = 0.0

    def atualizar(self, dt):
        self.tempo += dt

    def trocar_conjunto(self, animacoes):
        """Troca as imagens (ex.: Super Saiyajin) sem perder o passo da animação atual."""
        self.animacoes = dict(animacoes)
        if self.atual not in self.animacoes:
            self.atual = next(iter(self.animacoes))

    @property
    def animacao(self):
        return self.animacoes[self.atual]

    @property
    def quadro_atual(self):
        return self.animacao.quadro(self.tempo)

    @property
    def terminou(self):
        return self.animacao.terminou(self.tempo)
