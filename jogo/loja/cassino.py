"""Cassino do Centro Acadêmico: jogos de aposta com as moedas do jogo (nunca dinheiro de verdade).

Cada jogo herda de JogoDeAposta e implementa `jogar`. A casa sempre ganha um
pouquinho no longo prazo (o retorno esperado de cada jogo fica abaixo de 100%).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoDaAposta:
    aposta: int
    premio: int
    mensagem: str
    simbolos: tuple = ()

    @property
    def ganhou(self):
        return self.premio > self.aposta


class JogoDeAposta(ABC):
    NOME = "Jogo"
    DESCRICAO = ""
    APOSTAS = (10, 25, 50, 100, 250)
    ESCOLHAS = (None,)          # o que o jogador escolhe antes de jogar (None: nada)

    @abstractmethod
    def jogar(self, aposta, escolha, rng):
        """Joga uma rodada e devolve um ResultadoDaAposta (o prêmio já inclui a aposta de volta)."""


class MaquinaDeSalgadinho(JogoDeAposta):
    """Caça-níquel: três rolos. Três iguais pagam a tabela; dois iguais devolvem um pouco a mais."""

    NOME = "Máquina de Salgadinho"
    DESCRICAO = "Três iguais pagam a tabela; dois iguais pagam 1,5x. 67-67-67 paga 30x."
    SIMBOLOS = ("Pequi", "Café", "Pão de Queijo", "Nota 10", "Caramelo", "67")
    TRIO = {"Pequi": 5, "Café": 5, "Pão de Queijo": 8, "Nota 10": 10, "Caramelo": 15, "67": 30}
    PAR = 1.5

    def jogar(self, aposta, escolha, rng):
        simbolos = tuple(rng.choice(self.SIMBOLOS) for _ in range(3))
        diferentes = len(set(simbolos))
        if diferentes == 1:
            premio, mensagem = aposta * self.TRIO[simbolos[0]], f"Três {simbolos[0]}!"
        elif diferentes == 2:
            premio, mensagem = round(aposta * self.PAR), "Dois iguais."
        else:
            premio, mensagem = 0, "Nada desta vez."
        return ResultadoDaAposta(aposta, premio, mensagem, simbolos)


class DadoDoMestre(JogoDeAposta):
    """O d20 do Mestre de RPG: aposte se sai acima ou abaixo de 10,5. 20 natural paga mais; 1 natural perde."""

    NOME = "Dado do Mestre"
    DESCRICAO = "Acima (11-20) ou abaixo (2-10) pagam 1,9x. 20 natural paga 2,5x; 1 natural sempre perde."
    ESCOLHAS = ("acima", "abaixo")
    LADOS = 20
    PAGAMENTO = 1.9
    CRITICO = 2.5

    def jogar(self, aposta, escolha, rng):
        if escolha not in self.ESCOLHAS:
            raise ValueError("escolha 'acima' ou 'abaixo'")
        valor = rng.randint(1, self.LADOS)
        if valor == self.LADOS:
            premio, mensagem = round(aposta * self.CRITICO), "20 natural! Acerto crítico!"
        elif valor == 1:
            premio, mensagem = 0, "1 natural... falha crítica."
        elif (valor > self.LADOS / 2) == (escolha == "acima"):
            premio, mensagem = round(aposta * self.PAGAMENTO), f"Saiu {valor}. Acertou!"
        else:
            premio, mensagem = 0, f"Saiu {valor}. Errou."
        return ResultadoDaAposta(aposta, premio, mensagem, (str(valor),))


JOGOS_DE_APOSTA = (MaquinaDeSalgadinho, DadoDoMestre)


class Cassino:
    @staticmethod
    def apostar(progresso, jogo, aposta, escolha, rng):
        """Desconta a aposta, joga e paga o prêmio. Sem moedas suficientes, não joga."""
        if aposta <= 0:
            raise ValueError("a aposta precisa ser positiva")
        progresso.gastar(aposta)
        resultado = jogo.jogar(aposta, escolha, rng)
        if resultado.premio:
            progresso.ganhar(resultado.premio)
        return resultado
