"""Ranking local dos 10 melhores resultados, salvo em JSON."""
import json


class RegistroRanking:
    """Um resultado de partida. A ordem natural vai do pior para o melhor."""

    TAMANHO_NOME = 12

    def __init__(self, nome, heroi, pontos, tempo, venceu=False):
        self.nome = str(nome or "").strip()[: self.TAMANHO_NOME] or "Anônimo"
        self.heroi = str(heroi)
        self.pontos = int(pontos)
        self.tempo = float(tempo)
        self.venceu = bool(venceu)

    def _chave(self):
        return self.pontos, -self.tempo

    def __lt__(self, outro):
        if not isinstance(outro, RegistroRanking):
            return NotImplemented
        return self._chave() < outro._chave()

    def __eq__(self, outro):
        if not isinstance(outro, RegistroRanking):
            return NotImplemented
        return (self.nome, self.heroi, self.pontos, round(self.tempo, 2), self.venceu) == \
               (outro.nome, outro.heroi, outro.pontos, round(outro.tempo, 2), outro.venceu)

    __hash__ = None

    def __str__(self):
        minutos, segundos = divmod(int(self.tempo), 60)
        return f"{self.nome} ({self.heroi}) - {self.pontos} pontos em {minutos:02d}:{segundos:02d}"

    def para_dict(self):
        return {"nome": self.nome, "heroi": self.heroi, "pontos": self.pontos,
                "tempo": self.tempo, "venceu": self.venceu}

    @classmethod
    def de_dict(cls, dados):
        return cls(dados["nome"], dados["heroi"], dados["pontos"], dados["tempo"], dados.get("venceu", False))


class Ranking:
    LIMITE = 10

    def __init__(self, caminho):
        self.caminho = caminho
        self.registros = self._carregar()

    def _carregar(self):
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            if not isinstance(dados, list):
                return []
            registros = [RegistroRanking.de_dict(d) for d in dados]
        except (OSError, ValueError, KeyError, TypeError, OverflowError):
            return []
        return sorted(registros, reverse=True)[: self.LIMITE]

    def adicionar(self, registro):
        """Insere o resultado. Retorna a posição (1 a 10) ou None se não entrou."""
        self.registros = sorted(self.registros + [registro], reverse=True)[: self.LIMITE]
        self.salvar()
        for posicao, r in enumerate(self.registros, start=1):
            if r is registro:
                return posicao
        return None

    def salvar(self):
        """Grava o ranking. Sem permissão de escrita, o ranking vale só até fechar o jogo."""
        try:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            self.caminho.write_text(json.dumps([r.para_dict() for r in self.registros], ensure_ascii=False, indent=2),
                                    encoding="utf-8")
        except OSError:
            pass
