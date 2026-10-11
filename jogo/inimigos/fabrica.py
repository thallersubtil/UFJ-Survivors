"""Fábrica de inimigos: cria qualquer inimigo pelo nome registrado."""


class FabricaDeInimigos:
    _registro = {}

    @classmethod
    def registrar(cls, nome):
        """Decorador que registra uma classe de inimigo com um nome."""
        def decorador(classe):
            if nome in cls._registro:
                raise ValueError(f"já existe um inimigo registrado como '{nome}'")
            cls._registro[nome] = classe
            classe.CHAVE = nome
            return classe
        return decorador

    @classmethod
    def classe(cls, nome):
        try:
            return cls._registro[nome]
        except KeyError:
            raise ValueError(f"inimigo desconhecido: '{nome}'") from None

    @classmethod
    def criar(cls, nome, posicao, escala=1.0):
        return cls.classe(nome)(posicao, escala)

    @classmethod
    def criar_gigante(cls, nome, posicao, escala=1.0):
        inimigo = cls.criar(nome, posicao, escala)
        inimigo.tornar_gigante()
        return inimigo

    @classmethod
    def nomes(cls):
        return sorted(cls._registro)
