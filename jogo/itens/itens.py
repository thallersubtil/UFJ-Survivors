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


class TenisDeCorrida(Item):
    NOME = "Tênis de Corrida"
    DESCRICAO = "O rolamento recarrega 15% mais rápido por nível."
    ICONE = "icones/tenis.png"
    MELHORIAS = ("-15% de recarga do rolamento.", "-15% de recarga do rolamento.")
    PRECO_DESBLOQUEIO = 250

    def aplicar(self, jogador):
        jogador.mult_rolamento *= 1 - 0.15 * self.nivel


class OculosDeGrau(Item):
    NOME = "Óculos de Grau"
    DESCRICAO = "Enxerga o ponto fraco: +5% de chance de crítico por nível."
    ICONE = "icones/oculos.png"
    MELHORIAS = ("+5% de crítico.", "+5% de crítico.")
    PRECO_DESBLOQUEIO = 300

    def aplicar(self, jogador):
        jogador.chance_critico += 0.05 * self.nivel


class Cola(Item):
    """Notas mais rápido colando, com vida máxima menor e risco de ser pego.

    Pego colando, a cola é confiscada por alguns níveis: sem o bônus e sem o custo, e as notas
    rendem só metade até a punição acabar. Só aparece nas cartas de nível, nunca no baú.
    """
    NOME = "Cola"
    DESCRICAO = "1,5x de experiência, -15% de vida máxima. Cuidado para não ser pego!"
    ICONE = "sprites/nota.png"
    NIVEL_MAXIMO = 2
    MELHORIAS = ("2x de experiência, -20% de vida máxima.",)
    SO_AO_SUBIR_DE_NIVEL = True
    EXPERIENCIA = (1.5, 2.0)
    CUSTO_VIDA = (0.15, 0.20)
    CHANCE_FLAGRA = (0.02, 0.03)        # por nível que o herói sobe
    EXPERIENCIA_PUNIDO = 0.5
    NIVEIS_DE_PUNICAO = 2
    REDUCAO_POR_OCULOS = 0.25           # cada nível do Óculos de Grau esconde melhor a cola

    def __init__(self):
        super().__init__()
        self._castigo = 0

    @property
    def punido(self):
        return self._castigo > 0

    def aplicar(self, jogador):
        if self.punido:
            jogador.fator_experiencia *= self.EXPERIENCIA_PUNIDO
            return
        jogador.fator_experiencia *= self.EXPERIENCIA[self.nivel - 1]
        jogador.mult_vida_maxima *= 1 - self.CUSTO_VIDA[self.nivel - 1]

    def chance_de_flagra(self, jogador, jogo):
        chance = self.CHANCE_FLAGRA[self.nivel - 1]
        if jogo.chefe is not None and jogo.chefe.ativo:
            chance *= 2                  # o professor está olhando
        for item in jogador.itens:
            if isinstance(item, OculosDeGrau):
                chance *= max(0.0, 1 - self.REDUCAO_POR_OCULOS * item.nivel)
        return chance

    def ao_subir_de_nivel(self, jogador, jogo):
        if self.punido:
            self._castigo -= 1
            if not self.punido:
                jogo.anunciar("Cola devolvida")
                jogador.recalcular_atributos()
        elif jogo.rng.random() < self.chance_de_flagra(jogador, jogo):
            self._castigo = self.NIVEIS_DE_PUNICAO
            jogo.anunciar("PEGO COLANDO!", 3)
            jogador.recalcular_atributos()


ITENS = (CadernoDeResumos, Energetico, MarmitaDoRU, MochilaPesada, FoneDeOuvido, RelogioDePulso, GarrafaTermica,
         TenisDeCorrida, OculosDeGrau, Cola)
