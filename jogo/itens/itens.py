"""Itens passivos. Cada um soma seu efeito em Jogador.recalcular_atributos()."""
from jogo.itens.item import Item


class CadernoDeResumos(Item):
    NOME = "Caderno de Resumos"
    DESCRICAO = "+10% de dano por nível."
    ICONE = "icones/caderno.png"
    MELHORIAS = ("+10% de dano.", "+10% de dano.")

    def aplicar(self, jogador):
        jogador.mult_dano += 0.10 * self.nivel


class Energetico(Item):
    NOME = "Energético"
    DESCRICAO = "+10% de velocidade por nível."
    ICONE = "icones/energetico.png"
    MELHORIAS = ("+10% de velocidade.", "+10% de velocidade.")

    def aplicar(self, jogador):
        jogador.mult_velocidade += 0.10 * self.nivel


class MarmitaDoRU(Item):
    NOME = "Marmita do RU"
    DESCRICAO = "Recupera vida aos pouquinhos."
    ICONE = "icones/marmita.png"
    MELHORIAS = ("Recupera vida mais rápido.", "Recupera 1 de vida por segundo.")
    REGENERACAO = (1 / 3, 1 / 2, 1.0)

    def aplicar(self, jogador):
        jogador.regeneracao += self.REGENERACAO[self.nivel - 1]


class MochilaPesada(Item):
    NOME = "Mochila Pesada"
    DESCRICAO = "+20 de vida máxima por nível."
    ICONE = "icones/mochila.png"
    MELHORIAS = ("+20 de vida máxima.", "+20 de vida máxima.")

    def aplicar(self, jogador):
        jogador.vida_maxima_extra += 20 * self.nivel


class FoneDeOuvido(Item):
    NOME = "Fone de Ouvido"
    DESCRICAO = "Puxa as notas de mais longe (+30% por nível)."
    ICONE = "icones/fone.png"
    MELHORIAS = ("+30% de alcance de coleta.", "+30% de alcance de coleta.")

    def aplicar(self, jogador):
        jogador.alcance_coleta *= 1 + 0.30 * self.nivel


class RelogioDePulso(Item):
    NOME = "Relógio de Pulso"
    DESCRICAO = "Armas e especial recarregam 8% mais rápido por nível."
    ICONE = "legado/itens/item_watch_l.png"
    MELHORIAS = ("-8% de recarga.", "-8% de recarga.")

    def aplicar(self, jogador):
        jogador.mult_recarga *= 1 - 0.08 * self.nivel


class GarrafaTermica(Item):
    NOME = "Garrafa Térmica"
    DESCRICAO = "+25% de café máximo e de recarga de café por nível."
    ICONE = "icones/garrafa.png"
    MELHORIAS = ("+25% de café.", "+25% de café.")

    def aplicar(self, jogador):
        jogador.mult_cafe *= 1 + 0.25 * self.nivel


ITENS = (CadernoDeResumos, Energetico, MarmitaDoRU, MochilaPesada, FoneDeOuvido, RelogioDePulso, GarrafaTermica)
