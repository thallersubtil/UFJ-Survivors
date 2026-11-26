"""O que sai de um baú: a raridade (comum, épico ou lendário), os prêmios e as moedas.

A raridade é o "crítico" do baú: quase todos são comuns, mas a sorte do aluno aumenta a chance de
sair um épico ou um lendário. As moedas têm o seu próprio crítico, sorteado à parte.
"""
from dataclasses import dataclass

from jogo.progressao import Progressao


@dataclass(frozen=True)
class Raridade:
    chave: str
    nome: str
    itens: int                 # quantos prêmios (armas, itens ou melhorias) o baú dá
    moedas: tuple              # (mínimo, máximo) de moedas
    chance: float              # chance base de o baú sair assim (a sorte multiplica)
    cor: tuple
    abertura: float            # segundos da animação até a tampa abrir
    quadros: tuple             # imagens da tampa abrindo


def _quadros(prefixo):
    return tuple(f"legado/itens/{prefixo}_f{i}.png" for i in range(4))


COMUM = Raridade("comum", "BAÚ COMUM", 1, (8, 16), 1.0, (214, 168, 74), 1.0, _quadros("chest"))
EPICO = Raridade("epico", "BAÚ ÉPICO!", 3, (45, 75), 0.12, (190, 110, 255), 1.7, _quadros("bau_epico"))
LENDARIO = Raridade("lendario", "BAÚ LENDÁRIO!!!", 5, (160, 260), 0.02, (255, 222, 90), 2.8, _quadros("bau_lendario"))
RARIDADES = (COMUM, EPICO, LENDARIO)


class Tesouro:
    """Um baú já sorteado. `abrir` entrega os prêmios e as moedas ao aluno."""

    CHANCE_DE_MOEDAS_CRITICAS = 0.15
    MULT_MOEDAS_CRITICAS = 3
    CHANCE_MAXIMA = 0.75           # nem com muita sorte todo baú é épico ou toda moeda crita

    def __init__(self, raridade, moedas, moedas_criticas=False):
        self.raridade = raridade
        self.moedas = moedas
        self.moedas_criticas = moedas_criticas
        self.premios = []          # preenchido ao abrir
        self.moedas_ganhas = 0     # já com os bônus de moedas do aluno e da prova

    @classmethod
    def chances(cls, jogador):
        """Chance de cada raridade para este aluno, na ordem de RARIDADES (soma 1)."""
        lendario = min(cls.CHANCE_MAXIMA, jogador.chance(LENDARIO.chance))
        epico = min(cls.CHANCE_MAXIMA - lendario, jogador.chance(EPICO.chance))
        return (1 - epico - lendario, epico, lendario)

    @classmethod
    def sortear(cls, jogador, rng):
        raridade = rng.choices(RARIDADES, weights=cls.chances(jogador))[0]
        moedas = rng.randint(*raridade.moedas)
        critico = rng.random() < min(cls.CHANCE_MAXIMA, jogador.chance(cls.CHANCE_DE_MOEDAS_CRITICAS))
        if critico:
            moedas *= cls.MULT_MOEDAS_CRITICAS
        return cls(raridade, moedas, critico)

    @property
    def critico(self):
        """Baú acima do comum: foi o crítico do baú."""
        return self.raridade is not COMUM

    def abrir(self, jogo):
        """Entrega um prêmio por vez (cada um já conta com o anterior) e depois as moedas."""
        for _ in range(self.raridade.itens):
            premio = Progressao.premio_bau(jogo.jogador, jogo.rng)
            premio.aplicar(jogo.jogador, jogo)
            self.premios.append(premio)
        antes = jogo.placar.moedas
        jogo.ganhar_moedas(self.moedas)
        self.moedas_ganhas = jogo.placar.moedas - antes
        if self.raridade is LENDARIO:
            jogo.marcos.add("bau_lendario")
        return self.premios
