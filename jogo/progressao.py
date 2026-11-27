"""Monta as cartas da tela de nível e o prêmio do baú."""
from dataclasses import dataclass
from typing import Callable

from jogo.armas.apostila import Apostila
from jogo.armas.caneta_bic import CanetaBic
from jogo.armas.caramelo import Caramelo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.cobra_python import CobraPython
from jogo.armas.colabs import Colab
from jogo.armas.controle import Controle
from jogo.armas.corrente_whatsapp import CorrenteDeWhatsApp
from jogo.armas.dado import DadoDeVinteLados
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.armas.pequi import PequiExplosivo
from jogo.armas.quadro_branco import QuadroBranco
from jogo.armas.regua import ReguaDeUmMetro
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
             Apostila, QuadroBranco, Controle, DadoDeVinteLados, ReguaDeUmMetro, CanetaBic, CorrenteDeWhatsApp)
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
        for habilidade in jogador.habilidades:
            if not habilidade.no_maximo:
                rotulo = "NÍVEL MÁXIMO!" if habilidade.nivel + 1 == habilidade.NIVEL_MAXIMO else f"nível {habilidade.nivel + 1}"
                opcoes.append(Opcao(habilidade.NOME, habilidade.descricao_proxima(), habilidade.ICONE, rotulo,
                                    "melhoria", lambda j, jogo, h=habilidade: j.subir_nivel_habilidade(h),
                                    peso=habilidade.PESO, origem=type(habilidade)))
        for habilidade in jogador.habilidades_da_classe:
            if habilidade not in jogador.habilidades:
                opcoes.append(Opcao(habilidade.NOME, habilidade.DESCRICAO, habilidade.ICONE, "HABILIDADE", "nova",
                                    lambda j, jogo, h=habilidade: j.adicionar_habilidade(h),
                                    peso=habilidade.PESO, origem=type(habilidade)))
        if len(jogador.itens) < jogador.MAX_ITENS:
            tem = {type(i) for i in jogador.itens}
            for classe in Progressao.ITENS:
                if classe not in tem and classe.liberada(jogador.desbloqueios):
                    opcoes.append(Opcao(classe.NOME, classe.DESCRICAO, classe.ICONE, "NOVO", "nova",
                                        lambda j, jogo, c=classe: j.adicionar_item(c()),
                                        classe.SO_AO_SUBIR_DE_NIVEL, Progressao._peso(classe), classe))
        return opcoes

    CURA_NO_MAXIMO = 0.30           # fração da vida máxima que a carta de vida recupera
    MOEDAS_NO_MAXIMO = 50           # moedas da outra carta, sem multiplicador nenhum

    @staticmethod
    def opcao_lanche():
        return Opcao("Lanche da Cantina", "Recupera 30% da vida máxima.", "legado/itens/potion_hp.png", "", "maximo",
                     lambda j, jogo: j.curar(j.vida_maxima * Progressao.CURA_NO_MAXIMO))

    @staticmethod
    def opcao_bolsa():
        return Opcao("Bolsa de Monitoria", f"Ganha {Progressao.MOEDAS_NO_MAXIMO} moedas.", "icones/moeda.png", "",
                     "maximo", lambda j, jogo: jogo.placar.adicionar_moedas(Progressao.MOEDAS_NO_MAXIMO))

    @staticmethod
    def opcoes_no_maximo():
        """Cartas de quem não tem mais o que melhorar (tudo no nível máximo ou banido): vida ou moedas."""
        return [Progressao.opcao_lanche(), Progressao.opcao_bolsa()]

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
        return escolhidas or Progressao.opcoes_no_maximo()

    @staticmethod
    def premio_bau(jogador, rng):
        candidatas = [o for o in Progressao.candidatas(jogador) if not o.so_nas_cartas]
        melhorias = [o for o in candidatas if o.tipo in ("melhoria", "colab")]
        if melhorias:
            return rng.choice(melhorias)
        if candidatas:
            return rng.choice(candidatas)
        return Progressao.opcao_lanche()
