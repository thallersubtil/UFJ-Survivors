"""Bônus que multiplicam um atributo por um tempo (Super Saiyajin, combo 67)."""


class BonusTemporario:
    def __init__(self, nome, atributo, multiplicador, duracao):
        self.nome = nome
        self.atributo = atributo
        self.multiplicador = multiplicador
        self.duracao = duracao
        self.restante = duracao

    def atualizar(self, dt):
        self.restante -= dt

    @property
    def ativo(self):
        return self.restante > 0
