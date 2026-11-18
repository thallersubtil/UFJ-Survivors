"""Progresso que fica entre as partidas: moedas, melhorias compradas e desbloqueios, salvo em JSON."""
import json


class Progresso:
    """Carteira e compras do aluno. Sem o arquivo (ou com ele estragado), começa do zero."""

    def __init__(self, caminho):
        self.caminho = caminho
        self._moedas = 0
        self._niveis = {}            # CHAVE da melhoria -> nível comprado
        self._desbloqueios = set()   # nomes das classes de armas e itens liberados
        self._lanche = None          # CHAVE do lanche guardado para a próxima partida
        self._conquistas = set()     # CHAVEs das conquistas já alcançadas
        self._classes_jogadas = set()
        self._carregar()

    @property
    def moedas(self):
        return self._moedas

    @moedas.setter
    def moedas(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("moedas devem ser um número inteiro")
        if valor < 0:
            raise ValueError("moedas não podem ser negativas")
        self._moedas = valor

    def ganhar(self, quantidade):
        if quantidade < 0:
            raise ValueError("não dá para ganhar moedas negativas")
        self.moedas = self._moedas + int(quantidade)
        self.salvar()

    def pode_pagar(self, preco):
        return 0 <= preco <= self._moedas

    def gastar(self, preco):
        if not self.pode_pagar(preco):
            raise ValueError("moedas insuficientes")
        self.moedas = self._moedas - int(preco)
        self.salvar()

    # Melhorias permanentes

    def nivel_de(self, melhoria):
        return self._niveis.get(melhoria.CHAVE, 0)

    def preco_da_proxima(self, melhoria):
        """Preço do próximo nível, ou None se já está no máximo."""
        nivel = self.nivel_de(melhoria)
        return None if nivel >= melhoria.NIVEL_MAXIMO else melhoria.custo(nivel)

    def comprar_melhoria(self, melhoria):
        preco = self.preco_da_proxima(melhoria)
        if preco is None or not self.pode_pagar(preco):
            return False
        self._niveis[melhoria.CHAVE] = self.nivel_de(melhoria) + 1
        self.gastar(preco)
        return True

    def melhorias_compradas(self):
        """Uma instância de cada melhoria comprada, no nível comprado, para o Jogador aplicar."""
        from jogo.loja.melhorias import MELHORIAS
        return [classe(self.nivel_de(classe)) for classe in MELHORIAS if self.nivel_de(classe) > 0]

    # Desbloqueios (armas e itens que só aparecem nas cartas depois de comprados)

    def desbloqueado(self, classe):
        return classe.PRECO_DESBLOQUEIO <= 0 or classe.__name__ in self._desbloqueios

    def desbloquear(self, classe):
        if self.desbloqueado(classe) or not self.pode_pagar(classe.PRECO_DESBLOQUEIO):
            return False
        self._desbloqueios.add(classe.__name__)
        self.gastar(classe.PRECO_DESBLOQUEIO)
        return True

    @property
    def desbloqueios(self):
        return frozenset(self._desbloqueios)

    # Lanche da Cantina (um por vez, vale só na próxima partida)

    @property
    def lanche_reservado(self):
        from jogo.loja.lanches import LANCHES
        return next((c for c in LANCHES if c.CHAVE == self._lanche), None)

    def comprar_lanche(self, classe):
        if self._lanche is not None or not self.pode_pagar(classe.PRECO):
            return False
        self._lanche = classe.CHAVE
        self.gastar(classe.PRECO)
        return True

    def consumir_lanche(self):
        """Tira o lanche guardado (a partida começou) e devolve a classe dele, ou None."""
        classe = self.lanche_reservado
        self._lanche = None
        self.salvar()
        return classe

    # Conquistas

    @property
    def conquistas(self):
        return frozenset(self._conquistas)

    @property
    def classes_jogadas(self):
        return frozenset(self._classes_jogadas)

    def registrar_conquista(self, chave):
        self._conquistas.add(chave)
        self.salvar()

    def registrar_classe(self, nome):
        self._classes_jogadas.add(nome)
        self.salvar()

    # Arquivo

    def _carregar(self):
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(dados, dict):
            return
        moedas = dados.get("moedas", 0)
        if isinstance(moedas, int) and not isinstance(moedas, bool) and moedas >= 0:
            self._moedas = moedas
        from jogo.loja.melhorias import MELHORIAS
        maximos = {m.CHAVE: m.NIVEL_MAXIMO for m in MELHORIAS}
        niveis = dados.get("melhorias", {})
        if isinstance(niveis, dict):
            for chave, nivel in niveis.items():
                if chave in maximos and isinstance(nivel, int) and 0 < nivel <= maximos[chave]:
                    self._niveis[chave] = nivel
        desbloqueios = dados.get("desbloqueios", [])
        if isinstance(desbloqueios, list):
            self._desbloqueios = {d for d in desbloqueios if isinstance(d, str)}
        lanche = dados.get("lanche")
        from jogo.loja.lanches import LANCHES
        if lanche in {c.CHAVE for c in LANCHES}:
            self._lanche = lanche
        for campo, destino in (("conquistas", self._conquistas), ("classes_jogadas", self._classes_jogadas)):
            valores = dados.get(campo, [])
            if isinstance(valores, list):
                destino.update(v for v in valores if isinstance(v, str))

    def salvar(self):
        """Grava o progresso. Sem permissão de escrita, vale só até fechar o jogo."""
        dados = {"moedas": self._moedas, "melhorias": self._niveis, "desbloqueios": sorted(self._desbloqueios),
                 "lanche": self._lanche, "conquistas": sorted(self._conquistas),
                 "classes_jogadas": sorted(self._classes_jogadas)}
        try:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            self.caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass
