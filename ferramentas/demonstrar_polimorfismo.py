"""Etapa 3: mostra, com o código de verdade, a hierarquia de classes e o polimorfismo funcionando.

    .venv/bin/python ferramentas/demonstrar_polimorfismo.py              # as três partes
    .venv/bin/python ferramentas/demonstrar_polimorfismo.py --arvore     # só a hierarquia

Nada aqui é escrito à mão: a árvore sai das próprias classes (`__subclasses__`) e a demonstração
cria um inimigo de cada tipo registrado na fábrica e avança a partida só com `jogo.atualizar(dt)`,
o mesmo laço único que o jogo usa. Não abre janela.
"""
import argparse
import importlib
import inspect
import os
import pkgutil
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

import jogo as pacote  # noqa: E402

RAIZES = ("Entidade", "Arma", "Item", "Fase", "Mapa", "Materia", "Habilidade", "Especial", "Melhoria",
          "JogoDeAposta", "Lanche", "Conquista", "Cena", "Mesa", "AcaoDoChefe")
GANCHOS = ("mover", "ao_morrer", "desenhar_corpo", "atacar")
TOTAL = 0          # classes do pacote jogo, contadas em carregar_classes


def carregar_classes():
    """Importa todos os módulos do jogo e devolve {nome: classe}."""
    for modulo in pkgutil.walk_packages(pacote.__path__, "jogo."):
        importlib.import_module(modulo.name)
    classes = {}
    for nome, modulo in list(sys.modules.items()):
        if nome.startswith("jogo"):
            for _, classe in inspect.getmembers(modulo, inspect.isclass):
                if classe.__module__.startswith("jogo"):
                    classes.setdefault(classe.__name__, set()).add(classe)
    global TOTAL
    TOTAL = sum(len(homonimas) for homonimas in classes.values())
    return {nome: next(iter(homonimas)) for nome, homonimas in classes.items()}


def filhas(classe):
    return sorted(classe.__subclasses__(), key=lambda c: c.__name__)


def descendentes(classe):
    todas = []
    for filha in filhas(classe):
        todas += [filha] + descendentes(filha)
    return list(dict.fromkeys(todas))


def concretas(classe):
    return [c for c in descendentes(classe) if not inspect.isabstract(c)]


def linhas_da_arvore(classe, nivel=0):
    abstratos = sorted(getattr(classe, "__abstractmethods__", ()))
    marca = f"  (abstrata: {', '.join(abstratos)})" if abstratos else ""
    linhas = ["    " * nivel + classe.__name__ + marca]
    for filha in filhas(classe):
        linhas += linhas_da_arvore(filha, nivel + 1)
    return linhas


def mostrar_arvore(classes):
    print("1. HIERARQUIA DE CLASSES (lida do código)\n")
    for nome in RAIZES:
        raiz = classes[nome]
        print("\n".join(linhas_da_arvore(raiz)))
        print(f"    -> {len(concretas(raiz))} classes concretas\n")
    print(f"Total de classes no pacote jogo: {TOTAL}\n")


def total_de_classes():
    return TOTAL


def criar_partida(classes):
    from jogo.jogo import Jogo

    class FaseVazia(classes["Fase"]):
        """Fase sem eventos, para nada além do que a demonstração criar entrar na arena."""
        NOME = "Demonstração"

        def criar_eventos(self):
            return []

    pygame.init()
    pygame.display.set_mode((1, 1))
    partida = Jogo(classes["Programador"], fase=FaseVazia(), semente=3)
    partida.jogador.imortal = True      # como no modo treino: a demonstração não acaba em REPROVADO
    return partida


def medir_laco(classes, segundos=2.0):
    """Cria um inimigo de cada tipo da fábrica, avança a partida só com `jogo.atualizar` e mede cada um.

    Devolve (quantas entidades, quantas classes diferentes, linhas), com uma linha por inimigo:
    (nome na fábrica, classe, classe de onde vem o `mover`, quanto andou, quanto chegou perto do aluno).
    """
    from jogo.inimigos.fabrica import FabricaDeInimigos

    partida = criar_partida(classes)
    centro = pygame.Vector2(partida.jogador.posicao)
    nomes = FabricaDeInimigos.nomes()
    inimigos = []
    for i, nome in enumerate(nomes):
        direcao = pygame.Vector2(1, 0).rotate(360 * i / len(nomes))
        inimigo = FabricaDeInimigos.criar(nome, centro + direcao * 420)
        partida.adicionar(inimigo)
        inimigos.append((nome, inimigo, pygame.Vector2(inimigo.posicao)))

    dt = 1 / 60
    for _ in range(int(segundos / dt)):
        partida.atualizar(dt)          # a única chamada: o Jogo não sabe o tipo de ninguém

    linhas = []
    for nome, inimigo, origem in inimigos:
        dona = next(c.__name__ for c in type(inimigo).__mro__ if "mover" in vars(c))
        andou = inimigo.posicao.distance_to(origem)
        aproximou = origem.distance_to(centro) - inimigo.posicao.distance_to(partida.jogador.posicao)
        linhas.append((nome, type(inimigo).__name__, dona, andou, aproximou))
    tipos = {type(e).__name__ for e in partida.entidades}
    return len(partida.entidades), len(tipos), linhas


def demonstrar_laco(classes, segundos=2.0):
    print("2. POLIMORFISMO FUNCIONANDO (um inimigo de cada tipo, o mesmo laço para todos)\n")
    entidades, tipos, linhas = medir_laco(classes, segundos)
    print(f"Depois de {segundos:.0f} s de partida, {entidades} entidades de {tipos} classes diferentes")
    print("passaram pelo laço `for e in self.entidades: e.atualizar(dt, self)`.\n")
    print(f"{'nome na fábrica':<24}{'classe':<26}{'mover() vem de':<22}{'andou':>7}{'chegou perto':>14}")
    for nome, classe, dona, andou, aproximou in linhas:
        print(f"{nome:<24}{classe:<26}{dona:<22}{andou:>6.0f}px{aproximou:>12.0f}px")
    print("\nMesma chamada, comportamentos diferentes: cada classe responde do seu jeito a `atualizar`.\n")


def conferencias(classes):
    """As conferências da etapa 3, como lista de (texto, passou)."""
    from jogo.jogo import Jogo

    fonte = inspect.getsource(Jogo.atualizar) + inspect.getsource(Jogo.desenhar)
    sem_if_por_tipo = "isinstance" not in fonte and "type(" not in fonte and "__class__" not in fonte
    entidade, inimigo = classes["Entidade"], classes["Inimigo"]
    incompletas = [c.__name__ for c in concretas(entidade)
                   if not (callable(getattr(c, "atualizar", None)) and callable(getattr(c, "desenhar", None)))]
    return [
        ("Entidade é abstrata, com atualizar() e desenhar()",
         {"atualizar", "desenhar"} <= set(entidade.__abstractmethods__)),
        (f"{len(concretas(entidade))} classes concretas de Entidade implementam os dois métodos", not incompletas),
        (f"{len(concretas(inimigo))} inimigos concretos herdam de Inimigo (mínimo exigido: 3)",
         len(concretas(inimigo)) >= 3),
        ("Jogo.atualizar() e Jogo.desenhar() não usam isinstance nem type()", sem_if_por_tipo),
    ]


def sobrescritas(classes):
    """Para cada método que os inimigos sobrescrevem, as classes que têm a própria versão."""
    inimigo = classes["Inimigo"]
    return {gancho: [c.__name__ for c in descendentes(inimigo) if gancho in vars(c)] for gancho in GANCHOS}


def verificar(classes):
    print("3. CONFERÊNCIAS\n")
    resultado = conferencias(classes)
    for texto, certo in resultado:
        print(f"[{'ok' if certo else 'FALHOU'}] {texto}")
    print("\nMétodos sobrescritos pelos inimigos (quantas classes têm a própria versão):")
    for gancho, donas in sobrescritas(classes).items():
        print(f"  {gancho + '()':<18}{len(donas):>3}  {', '.join(donas[:8])}{'...' if len(donas) > 8 else ''}")
    return all(certo for _, certo in resultado)


def principal():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--arvore", action="store_true", help="mostra só a hierarquia de classes")
    opcoes = argumentos.parse_args()
    classes = carregar_classes()
    mostrar_arvore(classes)
    if opcoes.arvore:
        return 0
    demonstrar_laco(classes)
    return 0 if verificar(classes) else 1


if __name__ == "__main__":
    sys.exit(principal())
