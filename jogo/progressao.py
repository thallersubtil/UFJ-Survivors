"""Monta as cartas da tela de nível e o prêmio do baú."""
from dataclasses import dataclass
from typing import Callable

from jogo.armas.caramelo import Caramelo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.cobra_python import CobraPython
from jogo.armas.colabs import Colab
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.itens.itens import ITENS


@dataclass
class Opcao:
    titulo: str
    descricao: str
    icone: str
    rotulo: str
    tipo: str
    acao: Callable

    def aplicar(self, jogador, jogo):
        self.acao(jogador, jogo)


class Progressao:
    ARMAS = (CobraPython, Caramelo, MascoteChatGPT, MascoteClaude, Gemini, FuscaAzul)
    ITENS = ITENS

    @staticmethod
    def candidatas(jogador):
        opcoes = []
        for receita in Colab.colabs_disponiveis(jogador.armas):
            opcoes.append(Opcao(receita.NOME, receita.DESCRICAO, receita.ICONE, "COLAB!", "colab",
                                lambda j, jogo, r=receita: j.aplicar_colab(r, jogo)))
        for arma in jogador.armas:
            if not arma.no_maximo:
                opcoes.append(Opcao(arma.NOME, arma.descricao_proxima(), arma.ICONE, f"nível {arma.nivel + 1}",
                                    "melhoria", lambda j, jogo, a=arma: a.subir_nivel()))
        if len(jogador.armas) < jogador.MAX_ARMAS:
            tem = {type(a) for a in jogador.armas} | jogador.armas_em_colab
            for classe in Progressao.ARMAS:
                if classe not in tem:
                    opcoes.append(Opcao(classe.NOME, classe.DESCRICAO, classe.ICONE, "NOVA", "nova",
                                        lambda j, jogo, c=classe: j.adicionar_arma(c())))
        for item in jogador.itens:
            if not item.no_maximo:
                opcoes.append(Opcao(item.NOME, item.descricao_proxima(), item.ICONE, f"nível {item.nivel + 1}",
                                    "melhoria", lambda j, jogo, i=item: j.subir_nivel_item(i)))
        if len(jogador.itens) < jogador.MAX_ITENS:
            tem = {type(i) for i in jogador.itens}
            for classe in Progressao.ITENS:
                if classe not in tem:
                    opcoes.append(Opcao(classe.NOME, classe.DESCRICAO, classe.ICONE, "NOVO", "nova",
                                        lambda j, jogo, c=classe: j.adicionar_item(c())))
        return opcoes

    @staticmethod
    def opcao_lanche():
        return Opcao("Lanche da Cantina", "Recupera 30 de vida.", "legado/itens/potion_hp.png", "", "lanche",
                     lambda j, jogo: j.curar(30))

    @staticmethod
    def gerar_opcoes(jogador, rng, quantidade=3):
        candidatas = Progressao.candidatas(jogador)
        colabs = [o for o in candidatas if o.tipo == "colab"][:quantidade]
        outras = [o for o in candidatas if o.tipo != "colab"]
        escolhidas = colabs + rng.sample(outras, min(len(outras), quantidade - len(colabs)))
        return escolhidas or [Progressao.opcao_lanche()]

    @staticmethod
    def premio_bau(jogador, rng):
        candidatas = Progressao.candidatas(jogador)
        melhorias = [o for o in candidatas if o.tipo in ("melhoria", "colab")]
        if melhorias:
            return rng.choice(melhorias)
        if candidatas:
            return rng.choice(candidatas)
        return Progressao.opcao_lanche()
