"""Melhorias permanentes da loja do Centro Acadêmico.

Como os itens, cada melhoria soma o seu efeito em Jogador.recalcular_atributos()
(polimorfismo: o Jogador chama `aplicar` sem saber qual melhoria é).
"""
from abc import ABC, abstractmethod


class Melhoria(ABC):
    CHAVE = ""                 # nome guardado no arquivo de progresso; não mude depois de lançar
    NOME = "Melhoria"
    DESCRICAO = ""
    ICONE = ""
    NIVEL_MAXIMO = 5
    CUSTO_BASE = 80
    CRESCIMENTO = 1.6          # cada nível custa 60% a mais que o anterior

    def __init__(self, nivel=1):
        self.nivel = nivel

    @property
    def nivel(self):
        return self._nivel

    @nivel.setter
    def nivel(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("o nível deve ser um número inteiro")
        if not 1 <= valor <= self.NIVEL_MAXIMO:
            raise ValueError(f"o nível de {self.NOME} vai de 1 a {self.NIVEL_MAXIMO}")
        self._nivel = valor

    @classmethod
    def custo(cls, nivel_atual):
        """Preço para ir de `nivel_atual` ao nível seguinte (arredondado de 10 em 10)."""
        return int(round(cls.CUSTO_BASE * cls.CRESCIMENTO ** nivel_atual / 10) * 10)

    @abstractmethod
    def aplicar(self, jogador):
        """Soma o efeito desta melhoria (no nível comprado) aos atributos do jogador."""

    def __str__(self):
        return f"{self.NOME} (nível {self._nivel})"


class PlanoDeSaude(Melhoria):
    CHAVE = "vida"
    NOME = "Plano de Saúde Estudantil"
    DESCRICAO = "+8 de vida máxima por nível."
    ICONE = "icones/loja_vida.png"
    CUSTO_BASE = 60

    def aplicar(self, jogador):
        jogador.vida_maxima_extra += 8 * self.nivel


class AulasDeReforco(Melhoria):
    CHAVE = "dano"
    NOME = "Aulas de Reforço"
    DESCRICAO = "+5% de dano por nível."
    ICONE = "icones/caderno.png"
    CUSTO_BASE = 90

    def aplicar(self, jogador):
        jogador.mult_dano += 0.05 * self.nivel


class TreinoNoGinasio(Melhoria):
    CHAVE = "velocidade"
    NOME = "Treino no Ginásio"
    DESCRICAO = "+3% de velocidade por nível."
    ICONE = "icones/tenis.png"
    CUSTO_BASE = 80
    POR_NIVEL = 0.03

    def aplicar(self, jogador):
        jogador.mult_velocidade += self.POR_NIVEL * self.nivel


class AgendaOrganizada(Melhoria):
    CHAVE = "recarga"
    NOME = "Agenda Organizada"
    DESCRICAO = "Armas e especial recarregam 3% mais rápido por nível."
    ICONE = "legado/itens/item_watch_s.png"
    CUSTO_BASE = 100

    def aplicar(self, jogador):
        jogador.mult_recarga *= 1 - 0.03 * self.nivel


class AulaDeParkour(Melhoria):
    CHAVE = "rolamento"
    NOME = "Aula de Parkour"
    DESCRICAO = "O rolamento recarrega 10% mais rápido por nível."
    ICONE = "icones/rolamento.png"
    NIVEL_MAXIMO = 3
    CUSTO_BASE = 90

    def aplicar(self, jogador):
        jogador.mult_rolamento *= 1 - 0.10 * self.nivel


class SorteDeCalouro(Melhoria):
    CHAVE = "critico"
    NOME = "Sorte de Calouro"
    DESCRICAO = "+2% de chance de acerto crítico por nível."
    ICONE = "legado/itens/item_dice.png"
    CUSTO_BASE = 90

    def aplicar(self, jogador):
        jogador.chance_critico += 0.02 * self.nivel


class ImaDaRepublica(Melhoria):
    CHAVE = "coleta"
    NOME = "Ímã da República"
    DESCRICAO = "+10% de alcance de coleta por nível."
    ICONE = "icones/fone.png"
    NIVEL_MAXIMO = 3
    CUSTO_BASE = 50

    def aplicar(self, jogador):
        jogador.alcance_coleta *= 1 + 0.10 * self.nivel


class Monitoria(Melhoria):
    CHAVE = "experiencia"
    NOME = "Monitoria"
    DESCRICAO = "+5% de experiência das notas por nível."
    ICONE = "sprites/nota.png"
    CUSTO_BASE = 110

    def aplicar(self, jogador):
        jogador.mult_experiencia += 0.05 * self.nivel


class BolsaPermanencia(Melhoria):
    CHAVE = "moedas"
    NOME = "Bolsa Permanência"
    DESCRICAO = "+10% de moedas por nível."
    ICONE = "icones/moeda.png"
    CUSTO_BASE = 100

    def aplicar(self, jogador):
        jogador.mult_moedas += 0.10 * self.nivel


MELHORIAS = (PlanoDeSaude, AulasDeReforco, TreinoNoGinasio, AgendaOrganizada, AulaDeParkour, SorteDeCalouro,
             ImaDaRepublica, Monitoria, BolsaPermanencia)
