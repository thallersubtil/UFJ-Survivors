"""Aparência do aluno: gênero, penteado, olhos, roupas, acessório e cores.

Só guarda as escolhas (com validação). Quem desenha é o Boneco, que monta as partes
(jogo/jogador/partes.py) a partir destas escolhas.
"""
from jogo.jogador import partes

# (nome, cor)
TONS_DE_PELE = (
    ("Muito clara", (255, 226, 204)),
    ("Clara", (240, 196, 160)),
    ("Média", (210, 154, 110)),
    ("Morena", (165, 108, 70)),
    ("Escura", (105, 66, 44)),
)
CORES_DE_CABELO = (
    ("Preto", (52, 44, 50)),
    ("Castanho", (110, 66, 40)),
    ("Castanho claro", (160, 110, 64)),
    ("Loiro", (236, 196, 100)),
    ("Ruivo", (200, 90, 40)),
    ("Grisalho", (180, 180, 186)),
    ("Azul", (70, 110, 220)),
    ("Rosa", (236, 110, 170)),
    ("Verde", (70, 170, 110)),
)
CORES_DE_ROUPA = (
    ("Verde", (50, 150, 80)),
    ("Laranja", (250, 140, 30)),
    ("Azul", (50, 100, 210)),
    ("Vermelho", (210, 40, 50)),
    ("Roxo", (130, 70, 200)),
    ("Rosa", (235, 110, 160)),
    ("Preto", (52, 50, 60)),
    ("Branco", (236, 236, 240)),
    ("Amarelo", (245, 205, 50)),
)
CORES_DE_BAIXO = (
    ("Jeans", (60, 90, 160)),
    ("Preta", (50, 50, 58)),
    ("Cinza", (130, 132, 140)),
    ("Cáqui", (190, 165, 115)),
    ("Verde-oliva", (100, 110, 60)),
    ("Vinho", (120, 40, 60)),
    ("Xadrez vermelho", (180, 50, 60)),
)

# Partes cujo valor escolhe um formato (uma classe de partes.py)
ESTILOS = {
    "genero": tuple(partes.CORPOS),
    "penteado": tuple(partes.PENTEADOS),
    "olhos": tuple(partes.OLHOS),
    "cima": tuple(partes.ROUPAS_DE_CIMA),
    "baixo": tuple(partes.ROUPAS_DE_BAIXO),
    "acessorio": tuple(partes.ACESSORIOS),
}
# Partes cujo valor escolhe uma cor
CORES = {
    "pele": TONS_DE_PELE,
    "cabelo": CORES_DE_CABELO,
    "cor_cima": CORES_DE_ROUPA,
    "cor_baixo": CORES_DE_BAIXO,
}
OPCOES = {**{parte: nomes for parte, nomes in ESTILOS.items()},
          **{parte: tuple(nome for nome, _ in cores) for parte, cores in CORES.items()}}

PADRAO = {
    "genero": "Masculino", "penteado": "Curto", "olhos": "Normais", "cima": "Moletom", "baixo": "Calça",
    "acessorio": "Nenhum", "pele": "Clara", "cabelo": "Castanho", "cor_cima": "Verde", "cor_baixo": "Jeans",
}
PADRAO_FEMININO = {**PADRAO, "genero": "Feminino", "penteado": "Longo", "baixo": "Saia", "cor_baixo": "Preta"}


def _parte(nome):
    """Cria a @property de uma parte: lê a escolha e, ao atribuir, valida contra as opções."""
    def ler(self):
        return self._escolhas[nome]

    def escrever(self, valor):
        self._definir(nome, valor)

    return property(ler, escrever, doc=f"Escolha de {nome} (só aceita uma das OPCOES).")


class Aparencia:
    """Escolhas do aluno. Cada atributo só aceita uma das opções da sua lista."""

    PARTES = ("genero", "penteado", "cabelo", "olhos", "pele", "cima", "cor_cima", "baixo", "cor_baixo",
              "acessorio")

    genero = _parte("genero")
    penteado = _parte("penteado")
    cabelo = _parte("cabelo")
    olhos = _parte("olhos")
    pele = _parte("pele")
    cima = _parte("cima")
    cor_cima = _parte("cor_cima")
    baixo = _parte("baixo")
    cor_baixo = _parte("cor_baixo")
    acessorio = _parte("acessorio")

    def __init__(self, **escolhas):
        desconhecidas = set(escolhas) - set(self.PARTES)
        if desconhecidas:
            raise ValueError(f"parte desconhecida: {', '.join(sorted(desconhecidas))}")
        base = PADRAO_FEMININO if escolhas.get("genero") == "Feminino" else PADRAO
        self._escolhas = {}
        for parte in self.PARTES:
            self._definir(parte, escolhas.get(parte, base[parte]))

    def _definir(self, parte, nome):
        if nome not in OPCOES[parte]:
            raise ValueError(f"{parte} inválido: {nome!r} (opções: {', '.join(OPCOES[parte])})")
        self._escolhas[parte] = nome

    def escolha(self, parte):
        return self._escolhas[parte]

    def cor(self, parte):
        """Cor RGB de uma parte de cor (pele, cabelo, cor_cima, cor_baixo); None para partes de formato."""
        if parte not in CORES:
            return None
        return dict(CORES[parte])[self._escolhas[parte]]

    def trocar(self, parte, passo):
        """Vai para a opção anterior (-1) ou seguinte (+1) da parte, dando a volta na lista."""
        nomes = OPCOES[parte]
        indice = (nomes.index(self._escolhas[parte]) + passo) % len(nomes)
        self._definir(parte, nomes[indice])

    def sortear(self, rng):
        for parte in self.PARTES:
            self._definir(parte, rng.choice(OPCOES[parte]))

    def copia(self):
        return Aparencia(**self._escolhas)

    def chave(self):
        return tuple(self._escolhas[parte] for parte in self.PARTES)

    def __eq__(self, outra):
        return isinstance(outra, Aparencia) and self.chave() == outra.chave()

    def __hash__(self):
        return hash(self.chave())

    def __str__(self):
        return ", ".join(f"{parte}: {self._escolhas[parte]}" for parte in self.PARTES)
