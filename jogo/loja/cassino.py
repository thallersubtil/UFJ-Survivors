"""Cassino do Centro Acadêmico: jogos de aposta com as moedas do jogo (nunca dinheiro de verdade).

Cada jogo herda de JogoDeAposta e diz duas coisas: quais são os sorteios possíveis (`sorteios`, todos com a
mesma chance) e quanto cada um paga (`avaliar`). O sorteio de verdade (`jogar`) e a tabela de chances mostrada
na tela (`tabela`) saem dessas mesmas duas respostas, então a porcentagem exibida nunca diverge do jogo.

A casa sempre ganha um pouquinho no longo prazo: o retorno esperado de cada jogo fica abaixo de 100%
(`retorno_esperado`), e o prêmio é sempre arredondado para baixo.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import product


def _com_virgula(numero, casas=2):
    """1.5 -> '1,5'; 30.0 -> '30'; 0.4630 -> '0,46'."""
    return f"{numero:.{casas}f}".rstrip("0").rstrip(".").replace(".", ",")


@dataclass(frozen=True)
class ResultadoDaAposta:
    aposta: int
    premio: int
    mensagem: str
    simbolos: tuple = ()
    rotulo: str = ""            # nome da linha da tabela de prêmios em que o sorteio caiu

    @property
    def ganhou(self):
        return self.premio > self.aposta

    @property
    def multiplicador(self):
        return self.premio / self.aposta if self.aposta else 0.0


@dataclass(frozen=True)
class Desfecho:
    """O que um sorteio vale: em que linha da tabela ele cai, quanto paga e o que aparece na tela."""
    rotulo: str
    multiplicador: float
    mensagem: str
    simbolos: tuple


@dataclass(frozen=True)
class LinhaDePremio:
    """Uma linha da tabela de prêmios: a chance de acontecer e quanto paga."""
    rotulo: str
    chance: float               # de 0 a 1
    multiplicador: float        # prêmio dividido pela aposta (0: perde tudo)

    @property
    def chance_formatada(self):
        return f"{_com_virgula(self.chance * 100)}%"

    @property
    def multiplicador_formatado(self):
        return f"{_com_virgula(self.multiplicador)}x" if self.multiplicador else "perde"


class JogoDeAposta(ABC):
    NOME = "Jogo"
    DESCRICAO = ""
    APOSTAS = (10, 25, 50, 100, 250)
    ESCOLHAS = (None,)          # o que o jogador escolhe antes de jogar (None: nada)

    @abstractmethod
    def sorteios(self):
        """Todos os sorteios possíveis, cada um com a mesma chance de sair (uma sequência)."""

    @abstractmethod
    def avaliar(self, sorteio, escolha):
        """Devolve o Desfecho de um sorteio para o palpite dado."""

    def sortear(self, rng):
        """Tira um dos sorteios possíveis. Os jogos sobrescrevem só para girar peça por peça."""
        return rng.choice(self.sorteios())

    def validar(self, escolha):
        if escolha not in self.ESCOLHAS:
            raise ValueError(f"escolha inválida: {escolha!r}")

    @staticmethod
    def premio_de(aposta, multiplicador):
        """Prêmio inteiro, arredondado para baixo (a conta é feita em centésimos para não errar por décimos)."""
        return round(aposta * multiplicador * 100) // 100

    def jogar(self, aposta, escolha, rng):
        """Joga uma rodada e devolve um ResultadoDaAposta (o prêmio já inclui a aposta de volta)."""
        self.validar(escolha)
        desfecho = self.avaliar(self.sortear(rng), escolha)
        return ResultadoDaAposta(aposta, self.premio_de(aposta, desfecho.multiplicador), desfecho.mensagem,
                                 desfecho.simbolos, desfecho.rotulo)

    def tabela(self, escolha=None):
        """Linhas de prêmio com a chance de cada uma, contadas nos mesmos sorteios que `jogar` usa.
        Vem do maior multiplicador para o menor."""
        self.validar(escolha)
        sorteios = self.sorteios()
        contagem = {}
        for sorteio in sorteios:
            desfecho = self.avaliar(sorteio, escolha)
            chave = (desfecho.rotulo, desfecho.multiplicador)
            contagem[chave] = contagem.get(chave, 0) + 1
        linhas = [LinhaDePremio(rotulo, vezes / len(sorteios), multiplicador)
                  for (rotulo, multiplicador), vezes in contagem.items()]
        return sorted(linhas, key=lambda linha: (-linha.multiplicador, linha.chance))

    def retorno_esperado(self, escolha=None):
        """Quanto volta, em média, de cada moeda apostada. Abaixo de 1: a casa ganha."""
        return sum(linha.chance * linha.multiplicador for linha in self.tabela(escolha))


class MaquinaDeSalgadinho(JogoDeAposta):
    """Caça-níquel: três rolos. Três iguais pagam a tabela; dois iguais devolvem um pouco a mais."""

    NOME = "Máquina de Salgadinho"
    DESCRICAO = "Três iguais pagam a tabela; dois iguais pagam 1,5x. 67-67-67 paga 30x."
    SIMBOLOS = ("Pequi", "Café", "Pão de Queijo", "Nota 10", "Caramelo", "67")
    TRIO = {"Pequi": 5, "Café": 5, "Pão de Queijo": 8, "Nota 10": 10, "Caramelo": 15, "67": 30}
    PAR = 1.5
    ROLOS = 3

    def sorteios(self):
        return tuple(product(self.SIMBOLOS, repeat=self.ROLOS))

    def sortear(self, rng):
        return tuple(rng.choice(self.SIMBOLOS) for _ in range(self.ROLOS))

    def avaliar(self, sorteio, escolha):
        diferentes = len(set(sorteio))
        if diferentes == 1:
            return Desfecho(f"Três {sorteio[0]}", self.TRIO[sorteio[0]], f"Três {sorteio[0]}!", sorteio)
        if diferentes == 2:
            return Desfecho("Dois iguais", self.PAR, "Dois iguais.", sorteio)
        return Desfecho("Nada", 0, "Nada desta vez.", sorteio)


class DadoDoMestre(JogoDeAposta):
    """O d20 do Mestre de RPG: aposte se sai acima ou abaixo de 10,5. 20 natural paga mais; 1 natural perde."""

    NOME = "Dado do Mestre"
    DESCRICAO = "Acima (11-20) ou abaixo (2-10) pagam 1,9x. 20 natural paga 2,5x; 1 natural sempre perde."
    ESCOLHAS = ("acima", "abaixo")
    LADOS = 20
    PAGAMENTO = 1.9
    CRITICO = 2.5

    def sorteios(self):
        return tuple(range(1, self.LADOS + 1))

    def sortear(self, rng):
        return rng.randint(1, self.LADOS)

    def avaliar(self, sorteio, escolha):
        simbolos = (str(sorteio),)
        if sorteio == self.LADOS:
            return Desfecho(f"{self.LADOS} natural", self.CRITICO, f"{self.LADOS} natural! Acerto crítico!", simbolos)
        if sorteio == 1:
            return Desfecho("1 natural", 0, "1 natural... falha crítica.", simbolos)
        if (sorteio > self.LADOS / 2) == (escolha == "acima"):
            return Desfecho("Acertou o lado", self.PAGAMENTO, f"Saiu {sorteio}. Acertou!", simbolos)
        return Desfecho("Errou o lado", 0, f"Saiu {sorteio}. Errou.", simbolos)


class RoletaDoBandejao(JogoDeAposta):
    """Roleta do RU: o aluno pede um prato e a roda decide o que a tia serve. Se sair o prato pedido, ganha;
    quanto menos casas o prato tem na roda, mais ele paga."""

    NOME = "Roleta do Bandejão"
    DESCRICAO = "Peça um prato e gire: se a roda parar nele, você ganha. Prato mais raro na roda paga mais."
    # a roda, casa por casa: 5 de arroz, 4 de frango, 2 de bife e 1 de strogonoff
    SETORES = ("Arroz", "Frango", "Arroz", "Bife", "Frango", "Arroz", "Strogonoff", "Frango", "Arroz", "Bife",
               "Frango", "Arroz")
    PAGAMENTO = {"Arroz": 2.2, "Frango": 2.8, "Bife": 5.5, "Strogonoff": 11.0}
    ESCOLHAS = tuple(PAGAMENTO)

    def sorteios(self):
        """As casas da roda (o número da casa, não o prato: pratos repetidos têm mais chance)."""
        return tuple(range(len(self.SETORES)))

    def avaliar(self, sorteio, escolha):
        prato = self.SETORES[sorteio]
        simbolos = (prato, str(sorteio))
        if prato == escolha:
            return Desfecho(f"Sai {escolha}", self.PAGAMENTO[prato], f"{prato}! Era o seu pedido.", simbolos)
        return Desfecho("Sai outro prato", 0, f"Saiu {prato}. Você pediu {escolha}.", simbolos)


JOGOS_DE_APOSTA = (MaquinaDeSalgadinho, DadoDoMestre, RoletaDoBandejao)


class SegredosDoCassino:
    """Item da loja (aba Desbloqueios): libera a consulta da tabela de prêmios e chances dentro do cassino.
    Sem ele, o aluno aposta no escuro."""

    NOME = "Segredos do Cassino do CA"
    DESCRICAO = "O caderninho do tesoureiro: mostra, no cassino, a chance e o valor de cada prêmio."
    ICONE = "icones/segredos_cassino.png"
    TIPO = "CASSINO"
    PRECO_DESBLOQUEIO = 300


class Cassino:
    @staticmethod
    def aposta_maxima(progresso):
        """O all in: tudo o que o aluno tem. Nenhuma aposta pode passar disso."""
        return progresso.moedas

    @staticmethod
    def apostar(progresso, jogo, aposta, escolha, rng):
        """Desconta a aposta, joga e paga o prêmio. Sem moedas suficientes, não joga."""
        if aposta <= 0:
            raise ValueError("a aposta precisa ser positiva")
        jogo.validar(escolha)
        progresso.gastar(aposta)
        resultado = jogo.jogar(aposta, escolha, rng)
        if resultado.premio:
            progresso.ganhar(resultado.premio)
        return resultado

    @staticmethod
    def apostar_tudo(progresso, jogo, escolha, rng):
        """All in: aposta o saldo inteiro de uma vez."""
        return Cassino.apostar(progresso, jogo, Cassino.aposta_maxima(progresso), escolha, rng)
