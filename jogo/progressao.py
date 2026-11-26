"""Monta as cartas da tela de nível e o prêmio do baú."""
from dataclasses import dataclass
from typing import Callable

from jogo.armas.apostila import Apostila
from jogo.armas.caramelo import Caramelo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.cobra_python import CobraPython
from jogo.armas.colabs import Colab
from jogo.armas.controle import Controle
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.armas.pequi import PequiExplosivo
from jogo.armas.quadro_branco import QuadroBranco
from jogo.armas.wifi import WifiEduroam
from jogo.itens.itens import ITENS


@dataclass
class Opcao:
    titulo: str
    descricao: str
    icone: str
    rotulo: str
    tipo: str
    acao: Callable
    so_nas_cartas: bool = False     # não sai no baú (ex.: Cola)
    peso: float = 1.0               # chance relativa no sorteio das cartas
    origem: object = None           # classe da arma ou do item (para banir)

    def aplicar(self, jogador, jogo):
        self.acao(jogador, jogo)


class Progressao:
    ARMAS = (CobraPython, Caramelo, MascoteChatGPT, MascoteClaude, Gemini, FuscaAzul, PequiExplosivo, WifiEduroam,
             Apostila, QuadroBranco, Controle)
    ITENS = ITENS

    PESO_DESBLOQUEADO = 0.7         # o que foi comprado na loja começa um pouco mais raro

    @staticmethod
    def _peso(classe):
        return classe.PESO * (Progressao.PESO_DESBLOQUEADO if classe.PRECO_DESBLOQUEIO > 0 else 1.0)

    @staticmethod
    def candidatas(jogador):
        opcoes = Progressao._candidatas_sem_filtro(jogador)
        return [o for o in opcoes if o.origem is None or o.origem not in jogador.banidos]

    @staticmethod
    def _candidatas_sem_filtro(jogador):
        opcoes = []
        for receita in Colab.colabs_disponiveis(jogador.armas):
            opcoes.append(Opcao(receita.NOME, receita.DESCRICAO, receita.ICONE, "COLAB SECRETA!", "colab",
                                lambda j, jogo, r=receita: j.aplicar_colab(r, jogo)))
        for arma in jogador.armas:
            if not arma.no_maximo:
                rotulo = "NÍVEL MÁXIMO!" if arma.nivel + 1 == arma.NIVEL_MAXIMO else f"nível {arma.nivel + 1}"
                opcoes.append(Opcao(arma.NOME, arma.descricao_proxima(), arma.ICONE, rotulo,
                                    "melhoria", lambda j, jogo, a=arma: a.subir_nivel(),
                                    peso=Progressao._peso(type(arma)), origem=type(arma)))
        if len(jogador.armas) < jogador.MAX_ARMAS:
            tem = {type(a) for a in jogador.armas} | jogador.armas_em_colab
            for classe in Progressao.ARMAS:
                if classe not in tem and classe.liberada(jogador.desbloqueios):
                    opcoes.append(Opcao(classe.NOME, classe.DESCRICAO, classe.ICONE, "NOVA", "nova",
                                        lambda j, jogo, c=classe: j.adicionar_arma(c()),
                                        peso=Progressao._peso(classe), origem=classe))
        for item in jogador.itens:
            if not item.no_maximo:
                opcoes.append(Opcao(item.NOME, item.descricao_proxima(), item.ICONE, f"nível {item.nivel + 1}",
                                    "melhoria", lambda j, jogo, i=item: j.subir_nivel_item(i),
                                    item.SO_AO_SUBIR_DE_NIVEL, Progressao._peso(type(item)), type(item)))
        if len(jogador.itens) < jogador.MAX_ITENS:
            tem = {type(i) for i in jogador.itens}
            for classe in Progressao.ITENS:
                if classe not in tem and classe.liberada(jogador.desbloqueios):
                    opcoes.append(Opcao(classe.NOME, classe.DESCRICAO, classe.ICONE, "NOVO", "nova",
                                        lambda j, jogo, c=classe: j.adicionar_item(c()),
                                        classe.SO_AO_SUBIR_DE_NIVEL, Progressao._peso(classe), classe))
        return opcoes

    @staticmethod
    def opcao_lanche():
        return Opcao("Lanche da Cantina", "Recupera 30 de vida.", "legado/itens/potion_hp.png", "", "atributo",
                     lambda j, jogo: j.curar(30))

    @staticmethod
    def opcoes_de_atributo():
        """Cartas para quando não sobra arma nem item para oferecer (todas as vagas no máximo ou banidas)."""
        return [
            Opcao("Estudo Extra", "+5% de dano pelo resto da partida.", "icones/caderno.png", "", "atributo",
                  lambda j, jogo: j.ganhar_atributo("dano", 0.05)),
            Opcao("Café Reforçado", "Armas recarregam 5% mais rápido pelo resto da partida.", "icones/garrafa.png",
                  "", "atributo", lambda j, jogo: j.ganhar_atributo("recarga", 0.05)),
            Opcao("Fôlego", "+10 de vida máxima pelo resto da partida.", "icones/mochila.png", "", "atributo",
                  lambda j, jogo: j.ganhar_atributo("vida", 10)),
            Progressao.opcao_lanche(),
        ]

    @staticmethod
    def sortear_com_peso(opcoes, quantidade, rng):
        """Sorteia sem repetir, respeitando o peso de cada opção."""
        restantes, escolhidas = list(opcoes), []
        while restantes and len(escolhidas) < quantidade:
            escolhida = rng.choices(restantes, weights=[o.peso for o in restantes])[0]
            restantes.remove(escolhida)
            escolhidas.append(escolhida)
        return escolhidas

    @staticmethod
    def gerar_opcoes(jogador, rng, quantidade=3):
        candidatas = Progressao.candidatas(jogador)
        colabs = [o for o in candidatas if o.tipo == "colab"][:quantidade]
        outras = [o for o in candidatas if o.tipo != "colab"]
        escolhidas = colabs + Progressao.sortear_com_peso(outras, quantidade - len(colabs), rng)
        return escolhidas or Progressao.sortear_com_peso(Progressao.opcoes_de_atributo(), quantidade, rng)

    @staticmethod
    def premio_bau(jogador, rng):
        candidatas = [o for o in Progressao.candidatas(jogador) if not o.so_nas_cartas]
        melhorias = [o for o in candidatas if o.tipo in ("melhoria", "colab")]
        if melhorias:
            return rng.choice(melhorias)
        if candidatas:
            return rng.choice(candidatas)
        return Progressao.opcao_lanche()
