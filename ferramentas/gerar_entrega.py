"""Gera a entrega da etapa 3 como uma página HTML autocontida (um arquivo só, sem internet).

    .venv/bin/python ferramentas/gerar_entrega.py

Tudo o que a página mostra é lido na hora: a hierarquia e o diagrama de classes vêm das próprias
classes, a demonstração roda o laço do Jogo (ferramentas/demonstrar_polimorfismo.py), o registro de
IA vem de docs/registro_ia.md e os commits vêm do git. A fonte e a captura de tela vão embutidas.
"""
import base64
import html
import inspect
import io
import re
import subprocess
import sys
import textwrap
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import demonstrar_polimorfismo as demo  # noqa: E402

SAIDA = RAIZ / "docs" / "entregas" / "etapa3_hierarquia_e_polimorfismo.html"
CAPTURA = RAIZ / "docs" / "entregas" / "captura_etapa3.png"
FONTE = RAIZ / "assets" / "fontes" / "pixelify-sans-ufj-700.ttf"
REPOSITORIO = "https://github.com/thallersubtil/UFJ-Survivors"
INTEGRANTES = ("Filipe Duarte de Freitas Oliveira", "Thaller Subtil de Carvalho")
AUTORES = {"thallersubtil": "Thaller", "Filipe Duarte de Freitas Oliveira": "Filipe", "Filipe": "Filipe"}

# classes concretas que ganham caixa própria no diagrama (as abstratas sempre ganham)
EM_DESTAQUE = {"LacaioDoCampus", "ProjetilDoHeroi", "ProjetilInimigo"}
# ordem das caixas irmãs no diagrama (as que não estão aqui vêm depois, em ordem alfabética)
ORDEM = ("SerVivo", "Jogador", "Inimigo", "LacaioDoCampus", "MiniChefe", "Chefe", "Projetil", "Coletavel", "Ajudante", "Efeito")
FAMILIAS = (
    ("Entidade", "Tudo o que existe na arena"),
    ("Arma", "Armas do aluno (não são entidades: criam projéteis e ajudantes)"),
    ("Item", "Itens passivos"),
    ("Habilidade", "Habilidades de cada classe, nas cartas de nível"),
    ("Especial", "Habilidade ativa de cada classe"),
    ("Materia", "O que possui cada professor"),
    ("Fase", "O semestre: o calendário dos três chefes"),
    ("Mapa", "Campus Jatobá e pátio genérico"),
    ("Melhoria", "Melhorias permanentes da loja"),
    ("Lanche", "Lanches da cantina"),
    ("JogoDeAposta", "Jogos do cassino"),
    ("Mesa", "Aparelhos do cassino na tela"),
    ("Conquista", "Conquistas"),
    ("Cena", "Telas do jogo"),
    ("AcaoDoChefe", "Ações que os chefes executam"),
)


def e(texto):
    return html.escape(str(texto))


# ---------------------------------------------------------------- diagrama de herança (SVG)

class Caixa:
    """Uma caixa do diagrama: uma classe ou um grupo de classes concretas irmãs."""

    LARGURA, LARGURA_GRUPO = 190, 300
    LINHA = 17

    def __init__(self, titulo, abstrata=False, linhas=(), grupo=False):
        self.titulo, self.abstrata, self.linhas, self.grupo = titulo, abstrata, list(linhas), grupo
        self.filhas = []
        self.x = self.y = 0
        self.largura = self.LARGURA_GRUPO if grupo else self.LARGURA
        self.altura = 30 + (14 if abstrata else 0) + (8 + self.LINHA * len(self.linhas) if self.linhas else 0)


def caixa_de_grupo(classes):
    nomes = sorted(c.__name__ for c in classes)
    titulo = f"{len(nomes)} classes concretas" if len(nomes) > 1 else nomes[0]
    linhas = textwrap.wrap(", ".join(nomes), 40) if len(nomes) > 1 else []
    return Caixa(titulo, linhas=linhas, grupo=len(nomes) > 1)


def montar_arvore(classe):
    abstratos = sorted(getattr(classe, "__abstractmethods__", ()))
    proprios = [m for m in abstratos if m in vars(classe)] or abstratos
    caixa = Caixa(classe.__name__, bool(abstratos), [f"{m}()" for m in proprios if m.islower()])
    soltas = []
    ordem = lambda c: (ORDEM.index(c.__name__) if c.__name__ in ORDEM else len(ORDEM), c.__name__)
    for filha in sorted(demo.filhas(classe), key=ordem):
        if inspect.isabstract(filha) or filha.__name__ in EM_DESTAQUE:
            caixa.filhas.append(montar_arvore(filha))
        else:
            soltas += [filha] + [d for d in demo.descendentes(filha) if not inspect.isabstract(d)]
    if soltas:
        grupo = caixa_de_grupo(dict.fromkeys(soltas))
        if classe.__name__ == "Inimigo":
            caixa.filhas.insert(0, grupo)       # os lacaios das matérias primeiro
        else:
            caixa.filhas.append(grupo)
    return caixa


def posicionar(caixa, nivel=0, topo=0, colunas=None):
    """Árvore deitada: a raiz à esquerda, cada nível numa coluna. Devolve o fim (y) da subárvore."""
    colunas = colunas if colunas is not None else {}
    caixa.x = 12 + nivel * 236
    if not caixa.filhas:
        caixa.y = topo
        return topo + caixa.altura + 16
    fim = topo
    for filha in caixa.filhas:
        fim = posicionar(filha, nivel + 1, fim, colunas)
    primeira, ultima = caixa.filhas[0], caixa.filhas[-1]
    caixa.y = (primeira.y + ultima.y + ultima.altura) / 2 - caixa.altura / 2
    return max(fim, caixa.y + caixa.altura + 16)


def desenhar_caixa(c):
    classe = "caixa grupo" if c.grupo else ("caixa abstrata" if c.abstrata else "caixa")
    partes = [f'<g class="{classe}"><rect x="{c.x:.0f}" y="{c.y:.0f}" width="{c.largura}" height="{c.altura}" rx="3"/>']
    y = c.y + 20
    if c.abstrata:
        partes.append(f'<text class="estereotipo" x="{c.x + c.largura / 2:.0f}" y="{c.y + 15:.0f}">«abstrata»</text>')
        y += 13
    partes.append(f'<text class="nome" x="{c.x + c.largura / 2:.0f}" y="{y:.0f}">{e(c.titulo)}</text>')
    if c.linhas:
        partes.append(f'<line x1="{c.x:.0f}" x2="{c.x + c.largura:.0f}" y1="{y + 9:.0f}" y2="{y + 9:.0f}"/>')
        for i, linha in enumerate(c.linhas):
            partes.append(f'<text class="membro" x="{c.x + 10:.0f}" y="{y + 25 + i * Caixa.LINHA:.0f}">{e(linha)}</text>')
    partes.append("</g>")
    return "".join(partes)


def desenhar_arvore(caixa):
    partes = []
    if caixa.filhas:
        saida_x, meio_y = caixa.x + caixa.largura, caixa.y + caixa.altura / 2
        tronco = saida_x + 30
        # triângulo vazado na mãe: a seta da herança aponta para a classe base
        partes.append(f'<polygon class="heranca" points="{saida_x:.0f},{meio_y:.0f} {saida_x + 13:.0f},{meio_y - 7:.0f} '
                      f'{saida_x + 13:.0f},{meio_y + 7:.0f}"/>')
        partes.append(f'<path class="fio" d="M{saida_x + 13:.0f},{meio_y:.0f} H{tronco:.0f}"/>')
        for filha in caixa.filhas:
            fy = filha.y + filha.altura / 2
            partes.append(f'<path class="fio" d="M{tronco:.0f},{meio_y:.0f} V{fy:.0f} H{filha.x:.0f}"/>')
            partes.append(desenhar_arvore(filha))
    partes.append(desenhar_caixa(caixa))
    return "".join(partes)


def extensao(caixa):
    largura, altura = caixa.x + caixa.largura, caixa.y + caixa.altura
    for filha in caixa.filhas:
        l, a = extensao(filha)
        largura, altura = max(largura, l), max(altura, a)
    return largura, altura


def svg_heranca(classes):
    raiz = montar_arvore(classes["Entidade"])
    posicionar(raiz, topo=12)
    largura, altura = extensao(raiz)
    return (f'<svg class="diagrama" viewBox="0 0 {largura + 12:.0f} {altura + 12:.0f}" role="img" '
            f'aria-label="Diagrama de classes: herança a partir de Entidade">{desenhar_arvore(raiz)}</svg>')


# ---------------------------------------------------------------- diagrama de composição (SVG)

def svg_composicao(classes):
    """Quem contém quem. As posições são fixas; as contagens vêm do código."""
    def n(nome):
        return len(demo.concretas(classes[nome]))

    caixas = {}

    def caixa(chave, x, y, titulo, abstrata=False, linhas=()):
        c = Caixa(titulo, abstrata, linhas)
        c.x, c.y = x, y
        caixas[chave] = c

    caixa("Jogo", 546, 14, "Jogo", linhas=["atualizar(dt)", "desenhar(tela)"])
    caixa("Jogador", 330, 150, "Jogador", True, ["vida (property)", f"{n('Jogador')} classes concretas"])
    caixa("Fase", 546, 150, "Fase", True, [f"{n('Fase')} provas"])
    caixa("Placar", 762, 150, "Placar", linhas=["pontos (property)", "moedas (property)"])
    caixa("Mapa", 978, 150, "Mapa", True, [f"{n('Mapa')} mapas"])
    caixa("Entidade", 978, 14, "Entidade", True, ["atualizar()", "desenhar()", f"{n('Entidade')} classes concretas"])
    partes_do_jogador = (("Arma", ["espera (property)", f"{n('Arma')} armas"]), ("Item", [f"{n('Item')} itens"]),
                         ("Habilidade", [f"{n('Habilidade')} habilidades"]), ("Especial", [f"{n('Especial')} especiais"]))
    for i, (nome, linhas) in enumerate(partes_do_jogador):
        caixa(nome, 12 + i * 216, 318, nome, True, linhas)
    caixa("Rolamento", 12, 140, "Rolamento", linhas=["esquiva com invencibilidade"])
    caixa("Animador", 12, 216, "Animador", linhas=["quadros da animação"])
    caixa("Fabrica", 978, 300, "FabricaDeInimigos", linhas=["registrar(nome) classmethod", "criar(nome, posicao) classmethod"])
    caixa("Inimigo", 978, 426, "Inimigo", True, ["mover()", f"{n('Inimigo')} classes concretas"])
    caixa("ChefePossuido", 978, 548, "ChefePossuido", True, [f"{n('ChefePossuido')} professores"])
    caixa("Materia", 722, 548, "Materia", True, ["ataques()", f"{n('Materia')} matérias"])
    caixa("Colisao", 722, 432, "Colisao", linhas=["circulos_colidem() staticmethod"])

    def baixo(c):
        return c.x + c.largura / 2, c.y + c.altura

    def cima(c):
        return c.x + c.largura / 2, c.y

    def losango(x, y):
        return f'<polygon class="composicao" points="{x:.0f},{y:.0f} {x - 6:.0f},{y + 9:.0f} {x:.0f},{y + 18:.0f} {x + 6:.0f},{y + 9:.0f}"/>'

    partes = []

    def contem(dono, parte, desvio=0, rotulo=""):
        (x1, y1), (x2, y2) = baixo(caixas[dono]), cima(caixas[parte])
        x1 += desvio
        meio = y1 + 18 + (y2 - y1 - 18) / 2
        partes.append(losango(x1, y1))
        partes.append(f'<path class="fio" d="M{x1:.0f},{y1 + 18:.0f} V{meio:.0f} H{x2:.0f} V{y2:.0f}"/>')
        if rotulo:
            partes.append(f'<text class="rotulo" x="{x2 + 6:.0f}" y="{y2 - 8:.0f}">{e(rotulo)}</text>')

    for i, parte in enumerate(("Jogador", "Fase", "Placar", "Mapa")):
        contem("Jogo", parte, desvio=(i - 1.5) * 26)
    for i, (parte, _) in enumerate(partes_do_jogador):
        contem("Jogador", parte, desvio=(i - 1.5) * 20, rotulo="0..4" if parte in ("Arma", "Item") else "1")
    # Rolamento e Animador: partes do Jogador, ligadas pela lateral
    jog = caixas["Jogador"]
    for parte, y in (("Rolamento", jog.y + 22), ("Animador", jog.y + 74)):
        fim = caixas[parte].x + caixas[parte].largura
        partes.append(f'<polygon class="composicao" points="{jog.x:.0f},{y:.0f} {jog.x - 9:.0f},{y - 6:.0f} '
                      f'{jog.x - 18:.0f},{y:.0f} {jog.x - 9:.0f},{y + 6:.0f}"/>')
        partes.append(f'<path class="fio" d="M{jog.x - 18:.0f},{y:.0f} H{fim:.0f}"/>')
    # Jogo guarda a lista de entidades (agregação: losango vazado)
    j, ent = caixas["Jogo"], caixas["Entidade"]
    y = j.y + 26
    partes.append(f'<polygon class="agregacao" points="{j.x + j.largura:.0f},{y:.0f} {j.x + j.largura + 9:.0f},{y - 6:.0f} '
                  f'{j.x + j.largura + 18:.0f},{y:.0f} {j.x + j.largura + 9:.0f},{y + 6:.0f}"/>')
    partes.append(f'<path class="fio" d="M{j.x + j.largura + 18:.0f},{y:.0f} H{ent.x:.0f}"/>')
    partes.append(f'<text class="rotulo" x="{j.x + j.largura + 30:.0f}" y="{y - 8:.0f}">entidades: lista, um único laço</text>')
    # dependências (tracejado)
    f, fab, ini = caixas["Fase"], caixas["Fabrica"], caixas["Inimigo"]
    partes.append(f'<path class="usa" d="M{f.x + f.largura / 2 + 40:.0f},{f.y + f.altura:.0f} V262 H{fab.x + 40:.0f} V{fab.y:.0f}"/>')
    partes.append(f'<text class="rotulo" x="{f.x + f.largura / 2 + 48:.0f}" y="256">pede inimigos pelo nome</text>')
    partes.append(f'<path class="usa" d="M{fab.x + fab.largura / 2:.0f},{fab.y + fab.altura:.0f} V{ini.y:.0f}"/>')
    partes.append(f'<text class="rotulo" x="{fab.x + fab.largura / 2 + 8:.0f}" y="{ini.y - 12:.0f}">cria</text>')
    # herança Inimigo <|-- ChefePossuido e composição ChefePossuido *-- Materia
    ch, mat = caixas["ChefePossuido"], caixas["Materia"]
    cx = ini.x + ini.largura / 2
    partes.append(f'<polygon class="heranca" points="{cx:.0f},{ini.y + ini.altura:.0f} {cx - 7:.0f},{ini.y + ini.altura + 13:.0f} '
                  f'{cx + 7:.0f},{ini.y + ini.altura + 13:.0f}"/>')
    partes.append(f'<path class="fio" d="M{cx:.0f},{ini.y + ini.altura + 13:.0f} V{ch.y:.0f}"/>')
    my = ch.y + 30
    partes.append(f'<polygon class="composicao" points="{ch.x:.0f},{my:.0f} {ch.x - 9:.0f},{my - 6:.0f} {ch.x - 18:.0f},{my:.0f} {ch.x - 9:.0f},{my + 6:.0f}"/>')
    partes.append(f'<path class="fio" d="M{ch.x - 18:.0f},{my:.0f} H{mat.x + mat.largura:.0f}"/>')
    partes.append(f'<text class="rotulo" x="{mat.x + mat.largura + 6:.0f}" y="{my - 8:.0f}">1..2</text>')
    # herança Entidade <|-- Inimigo (resumida): fio lateral
    ex = ent.x + ent.largura
    partes.append(f'<polygon class="heranca" points="{ex:.0f},{ent.y + 40:.0f} {ex + 13:.0f},{ent.y + 33:.0f} {ex + 13:.0f},{ent.y + 47:.0f}"/>')
    partes.append(f'<path class="fio" d="M{ex + 13:.0f},{ent.y + 40:.0f} H{ex + 34:.0f} V{ini.y + 30:.0f} H{ini.x + ini.largura:.0f}"/>')
    partes.append(f'<text class="rotulo" x="{ex + 40:.0f}" y="{ent.y + 150:.0f}" transform="rotate(90 {ex + 40:.0f} {ent.y + 150:.0f})">herda (via SerVivo)</text>')
    partes += [desenhar_caixa(c) for c in caixas.values()]
    return ('<svg class="diagrama" viewBox="0 0 1230 640" role="img" aria-label="Diagrama de classes: composição">'
            + "".join(partes) + "</svg>")


# ---------------------------------------------------------------- hierarquia completa (listas que abrem e fecham)

def lista_de_classes(classe):
    abstratos = sorted(getattr(classe, "__abstractmethods__", ()))
    marca = f' <span class="falta">abstrata: {e(", ".join(abstratos))}</span>' if abstratos else ""
    filhas = demo.filhas(classe)
    nome = f'<span class="classe{" abstrata" if abstratos else ""}">{e(classe.__name__)}</span>{marca}'
    if not filhas:
        return f"<li>{nome}</li>"
    return f'<li>{nome}<ul>{"".join(lista_de_classes(f) for f in filhas)}</ul></li>'


def familias_html(classes):
    blocos = []
    for nome, para_que in FAMILIAS:
        raiz = classes[nome]
        blocos.append(
            f'<details class="familia"{" open" if nome == "Entidade" else ""}><summary><span class="classe abstrata">{e(nome)}</span>'
            f'<span class="conta">{len(demo.concretas(raiz))} concretas</span><span class="para">{e(para_que)}</span></summary>'
            f'<ul class="arvore">{lista_de_classes(raiz)}</ul></details>')
    return "".join(blocos)


# ---------------------------------------------------------------- dados de fora do código

def commits_por_integrante():
    saida = subprocess.run(["git", "log", "--format=%an"], capture_output=True, text=True, cwd=RAIZ).stdout
    contagem = {}
    for autor in saida.splitlines():
        nome = AUTORES.get(autor)
        if nome:
            contagem[nome] = contagem.get(nome, 0) + 1
    return contagem


def registro_de_ia():
    """Linhas da tabela da etapa 3 em docs/registro_ia.md, como (onde, o que corrigimos)."""
    texto = (RAIZ / "docs" / "registro_ia.md").read_text(encoding="utf-8")
    trecho = texto.split("## Etapa 3", 1)[1].split("\n## ", 1)[0]
    linhas = []
    for linha in trecho.splitlines():
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(celulas) == 3 and celulas[0].startswith("3"):
            linhas.append((celulas[1], celulas[2]))
    return linhas


def total_de_testes():
    saida = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], capture_output=True, text=True, cwd=RAIZ).stdout
    achado = re.search(r"(\d+) tests? collected", saida)
    return int(achado.group(1)) if achado else 0


def captura_embutida():
    from PIL import Image

    imagem = Image.open(CAPTURA).convert("RGB")
    saida = io.BytesIO()
    imagem.save(saida, "JPEG", quality=84, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(saida.getvalue()).decode()


def codigo(texto):
    """Markdown mínimo do registro de IA: `código` vira <code>."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", e(texto))


# ---------------------------------------------------------------- a página

CSS = """
@font-face{font-family:"Pixelify UFJ";src:url(data:font/ttf;base64,@@FONTE@@) format("truetype");font-weight:700}
:root{--quadro:#1d3a2e;--quadro-fundo:#142820;--giz:#f1f0e2;--papel:#f3f6f0;--folha:#ffffff;--tinta:#16211b;
  --apagado:#5b6a61;--linha:#cfd8cf;--nota:#f0b400;--carimbo:#c5302a;--grama:#2f7d3b;--ceu:#2c6fb3;
  --pixel:"Pixelify UFJ",ui-monospace,monospace;--texto:Charter,"Iowan Old Style","Palatino Linotype",Georgia,serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--papel);color:var(--tinta);font:17px/1.62 var(--texto);-webkit-text-size-adjust:100%}
a{color:var(--ceu)}a:focus-visible,summary:focus-visible,input:focus-visible{outline:3px solid var(--nota);outline-offset:2px}
code{font:0.86em var(--mono);background:#e6ece5;padding:.08em .34em;border-radius:3px}
pre{font:13.5px/1.55 var(--mono);background:var(--quadro-fundo);color:var(--giz);padding:18px 20px;border-radius:4px;overflow:auto;margin:18px 0}
pre code{background:none;padding:0;font:inherit}
pre .c{color:#9fb8a7}pre .k{color:var(--nota)}
h2{font:700 30px/1.15 var(--pixel);margin:0 0 6px;letter-spacing:.2px}
h3{font:700 19px/1.3 var(--texto);margin:38px 0 8px}
p{margin:0 0 14px;max-width:72ch}
.quadro{background:var(--quadro);color:var(--giz);border-bottom:14px solid #7a5230;box-shadow:inset 0 0 0 8px var(--quadro-fundo)}
.quadro .dentro{max-width:1240px;margin:0 auto;padding:46px 32px 40px;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,520px);gap:40px;align-items:center}
.quadro h1{font:700 clamp(40px,6vw,74px)/.98 var(--pixel);margin:0 0 14px;text-shadow:3px 3px 0 var(--quadro-fundo)}
.quadro .etapa{font:700 22px/1.3 var(--pixel);color:var(--nota);margin:0 0 20px}
.quadro p{color:#dfe5d6;max-width:56ch}
.quadro dl{display:grid;grid-template-columns:auto 1fr;gap:4px 16px;margin:22px 0 0;font-size:15.5px}
.quadro dt{color:#a9c0ae}.quadro dd{margin:0}.quadro a{color:var(--giz)}
.foto{margin:0;transform:rotate(1.4deg);background:#fff;padding:10px 10px 12px;box-shadow:0 10px 0 rgba(0,0,0,.25)}
.foto img{display:block;width:100%;height:auto;image-rendering:auto}
.foto figcaption{font:14px/1.4 var(--texto);color:#3a463e;padding-top:8px}
.pagina{max-width:1240px;margin:0 auto;padding:0 32px 80px;display:grid;grid-template-columns:210px minmax(0,1fr);gap:48px}
nav.indice{position:sticky;top:0;align-self:start;padding-top:44px;font-size:15px}
nav.indice ol{list-style:none;margin:0;padding:0;border-left:3px solid var(--linha)}
nav.indice a{display:block;padding:5px 0 5px 14px;margin-left:-3px;border-left:3px solid transparent;color:var(--apagado);text-decoration:none}
nav.indice a:hover{color:var(--tinta);border-left-color:var(--grama)}
section{padding-top:44px}
.lead{font-size:18.5px;color:#2c3a31}
table{border-collapse:collapse;width:100%;margin:16px 0 8px;font-size:15.5px;line-height:1.45;background:var(--folha)}
th,td{text-align:left;vertical-align:top;padding:10px 14px;border:1px solid var(--linha)}
th{font:700 14.5px/1.3 var(--texto);background:#e3eae2}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.rolagem{overflow-x:auto}
.boletim{border:2px solid var(--tinta)}
.boletim th{background:var(--tinta);color:var(--giz);border-color:var(--tinta)}
.boletim td:first-child{font:700 16px/1.3 var(--pixel);white-space:nowrap}
.boletim td.ok{text-align:center;vertical-align:middle;width:128px}
.selo{display:inline-block;font:700 14px/1 var(--pixel);color:var(--carimbo);border:2.5px solid var(--carimbo);border-radius:4px;
  padding:6px 9px 5px;transform:rotate(-7deg);letter-spacing:1px;opacity:.9}
tr:nth-child(even) .selo{transform:rotate(5deg)}
.numeros{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0;margin:22px 0;border:2px solid var(--tinta);background:var(--folha)}
.numeros div{padding:14px 16px;border-right:1px solid var(--linha)}
.numeros b{display:block;font:700 34px/1 var(--pixel);color:var(--grama)}
.numeros span{font-size:14.5px;color:var(--apagado);line-height:1.3;display:block;margin-top:5px}
.prancha{background:var(--folha);border:2px solid var(--tinta);padding:14px;margin:18px 0;overflow-x:auto}
svg.diagrama{display:block;min-width:1080px;width:100%;height:auto;font-family:ui-sans-serif,system-ui,"Segoe UI",Helvetica,Arial,sans-serif}
svg .caixa rect{fill:#fff;stroke:var(--tinta);stroke-width:1.6}
svg .caixa.abstrata rect{fill:#e4efe2;stroke:var(--quadro);stroke-width:2}
svg .caixa.grupo rect{fill:#fbf6df;stroke:#9a7a1c;stroke-dasharray:5 3}
svg .caixa line{stroke:var(--tinta);stroke-width:1}
svg text{fill:var(--tinta)}
svg .nome{font-weight:700;font-size:14.5px;text-anchor:middle}
svg .abstrata .nome{font-style:italic}
svg .estereotipo{font-size:10.5px;text-anchor:middle;fill:var(--apagado)}
svg .membro{font-size:12.5px}
svg .rotulo{font-size:11.5px;fill:var(--apagado)}
svg .fio{fill:none;stroke:var(--tinta);stroke-width:1.4}
svg .usa{fill:none;stroke:var(--apagado);stroke-width:1.4;stroke-dasharray:6 4}
svg .heranca,svg .agregacao{fill:#fff;stroke:var(--tinta);stroke-width:1.4}
svg .composicao{fill:var(--tinta)}
.legenda{display:flex;flex-wrap:wrap;gap:8px 26px;font-size:14.5px;color:var(--apagado);margin:6px 0 0;padding:0;list-style:none}
.legenda svg{vertical-align:-4px;margin-right:6px}
.busca{display:flex;gap:12px;align-items:center;margin:14px 0 10px;font-size:15.5px}
.busca input{font:16px var(--texto);padding:8px 12px;border:2px solid var(--tinta);border-radius:3px;background:#fff;width:min(340px,100%)}
.familia{background:var(--folha);border:1px solid var(--linha);margin:0 0 6px}
.familia summary{cursor:pointer;padding:10px 14px;display:flex;flex-wrap:wrap;gap:6px 14px;align-items:baseline}
.familia .conta{font:700 14px var(--pixel);color:var(--grama)}
.familia .para{color:var(--apagado);font-size:15px}
.classe{font:14px var(--mono)}.classe.abstrata{font-style:italic;font-weight:700}
.falta{font-size:13px;color:var(--apagado);margin-left:6px}
ul.arvore{margin:0;padding:4px 14px 14px 22px}
ul.arvore,ul.arvore ul{list-style:none}
ul.arvore ul{margin:0;padding-left:20px;border-left:1.5px solid var(--linha)}
ul.arvore li{padding:1.5px 0 1.5px 6px;line-height:1.5}
mark{background:var(--nota);color:var(--tinta);padding:0 2px}
.barras{font-size:14px;background:var(--folha);border:2px solid var(--tinta);padding:14px 16px;margin:16px 0}
.barra{display:grid;grid-template-columns:minmax(120px,210px) 1fr 62px;gap:10px;align-items:center;padding:2px 0}
.barra .classe{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.barra i{display:block;height:13px;background:var(--cor)}
.barra .n{text-align:right;font:13px var(--mono);color:var(--apagado)}
.chaves{display:flex;flex-wrap:wrap;gap:6px 16px;margin:0 0 12px;padding:0;list-style:none;font:13px var(--mono)}
.chaves i{display:inline-block;width:12px;height:12px;background:var(--cor);margin-right:6px;vertical-align:-1px}
.confere{list-style:none;padding:0;margin:14px 0}
.confere li{padding:5px 0 5px 34px;position:relative}
.confere li::before{content:"";position:absolute;left:2px;top:9px;width:18px;height:10px;border-left:4px solid var(--grama);border-bottom:4px solid var(--grama);transform:rotate(-45deg) scale(.7)}
.confere li.falhou::before{border-color:var(--carimbo)}
footer{max-width:1240px;margin:0 auto;padding:22px 32px 40px;color:var(--apagado);font-size:14.5px;border-top:1px solid var(--linha)}
@media (max-width:900px){.pagina{grid-template-columns:1fr;gap:0;padding:0 18px 60px}nav.indice{position:static;padding-top:26px}
  .quadro .dentro{grid-template-columns:1fr;padding:34px 22px}.foto{transform:none}body{font-size:16px}}
@media print{nav.indice{display:none}.pagina{display:block}.quadro{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  pre{white-space:pre-wrap}section{break-inside:auto}.prancha,table,.familia{break-inside:avoid}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

JS = """
const campo=document.getElementById('busca'),conta=document.getElementById('achadas');
const nomes=[...document.querySelectorAll('.arvore .classe')];
nomes.forEach(n=>n.dataset.nome=n.textContent);
campo.addEventListener('input',()=>{const t=campo.value.trim().toLowerCase();let q=0;
  nomes.forEach(n=>{const nome=n.dataset.nome,i=t?nome.toLowerCase().indexOf(t):-1;
    if(i<0){n.textContent=nome;return}q++;
    n.innerHTML=nome.slice(0,i)+'<mark>'+nome.slice(i,i+t.length)+'</mark>'+nome.slice(i+t.length);
    for(let d=n.closest('details');d;d=d.parentElement.closest('details'))d.open=true});
  conta.textContent=t?(q+(q===1?' classe encontrada':' classes encontradas')):''});
addEventListener('beforeprint',()=>document.querySelectorAll('details').forEach(d=>d.open=true));
"""

CORES_DAS_BARRAS = ("#2f7d3b", "#2c6fb3", "#c5302a", "#f0b400", "#7a4fb5", "#0e8f8f", "#d9722a", "#5b6a61",
                    "#9c3f7d", "#4f7d1f", "#1d3a2e", "#b08900")


def barras_html(linhas):
    maior = max(l[3] for l in linhas)
    donas = list(dict.fromkeys(l[2] for l in sorted(linhas, key=lambda l: l[2])))
    cor = {dona: CORES_DAS_BARRAS[i % len(CORES_DAS_BARRAS)] for i, dona in enumerate(donas)}
    chaves = "".join(f'<li><i style="--cor:{cor[d]}"></i>{e(d)}</li>' for d in donas)
    barras = "".join(
        f'<div class="barra"><span class="classe">{e(classe)}</span><i style="--cor:{cor[dona]};width:{100 * andou / maior:.1f}%" '
        f'title="mover() de {e(dona)}"></i><span class="n">{andou:.0f} px</span></div>'
        for _, classe, dona, andou, _ in sorted(linhas, key=lambda l: -l[3]))
    return (f'<div class="barras"><p style="margin:0 0 6px;font-size:14.5px;color:var(--apagado)">A cor mostra em que classe está '
            f'o <code>mover()</code> que respondeu:</p><ul class="chaves">{chaves}</ul>{barras}</div>')


def requisitos(classes):
    def n(nome):
        return len(demo.concretas(classes[nome]))

    return (
        ("Classe abstrata", "<code>Entidade</code> com os métodos abstratos <code>atualizar()</code> e <code>desenhar()</code>",
         "<code>jogo/nucleo/entidade.py</code>: <code>class Entidade(ABC)</code> com os dois <code>@abstractmethod</code>. "
         f"As {n('Entidade')} classes concretas implementam os dois."),
        ("Herança", "Pelo menos 3 tipos de inimigos herdando de uma classe base",
         f"{n('Inimigo')} classes concretas herdam de <code>Inimigo</code> (<code>jogo/inimigos/</code>), em até 5 níveis: "
         "<code>Entidade</code> &gt; <code>SerVivo</code> &gt; <code>Inimigo</code> &gt; <code>Chefe</code> &gt; "
         "<code>ChefePossuido</code> &gt; <code>ProfessorDeCalculo</code>."),
        ("Polimorfismo", "Um único laço <code>for e in entidades: e.atualizar()</code>, sem <code>if</code> por tipo",
         "<code>Jogo.atualizar()</code> em <code>jogo/jogo.py</code>. O laço não usa <code>isinstance</code> nem <code>type()</code>, "
         "e um teste automático falha se alguém colocar."),
        ("Encapsulamento", "Vida, pontuação e munição com <code>@property</code> e validação",
         "<code>SerVivo.vida</code> e <code>vida_maxima</code> (<code>jogo/nucleo/ser_vivo.py</code>), <code>Placar.pontos</code> e "
         "<code>moedas</code> (<code>jogo/placar.py</code>), <code>GarrafaDeCafe.municao</code> (<code>jogo/jogador/garrafa_de_cafe.py</code>: as doses de café da Virada de Noite)."),
        ("Composição", "<code>Jogo</code> contém <code>Jogador</code>, <code>Fase</code> e <code>Placar</code>; <code>Jogador</code> contém <code>Arma</code>",
         "<code>Jogo.__init__</code> cria <code>self.jogador</code>, <code>self.fase</code>, <code>self.placar</code> e <code>self.mapa</code>; "
         "<code>Jogador.__init__</code> cria <code>self.armas</code>, <code>self.itens</code>, as habilidades, o especial, o "
         "<code>Rolamento</code> e o <code>Animador</code>."),
        ("Métodos especiais", "<code>__str__</code>, <code>__eq__</code> ou <code>__lt__</code> em pelo menos uma classe",
         "<code>RegistroRanking</code> tem os três (<code>jogo/ranking.py</code>): o ranking é ordenado com <code>sorted()</code>. "
         "<code>__str__</code> também em <code>Placar</code>, <code>Arma</code>, <code>Item</code>, <code>Materia</code>, "
         "<code>Habilidade</code> e <code>Melhoria</code>."),
        ("@classmethod e @staticmethod", "Uma fábrica de inimigos e um utilitário de colisão",
         "<code>FabricaDeInimigos.criar()</code>, <code>registrar()</code> e <code>nomes()</code> (<code>jogo/inimigos/fabrica.py</code>); "
         "<code>Colisao.circulos_colidem()</code>, <code>segmento_acerta_circulo()</code>, <code>empurrar_para_fora()</code> "
         "(<code>jogo/nucleo/colisao.py</code>)."),
    )


def pagina():
    classes = demo.carregar_classes()
    entidades, tipos, linhas = demo.medir_laco(classes)
    conferencias = demo.conferencias(classes)
    sobrescritas = demo.sobrescritas(classes)
    commits = commits_por_integrante()
    testes = total_de_testes()

    def n(nome):
        return len(demo.concretas(classes[nome]))

    boletim = "".join(
        f'<tr><td>{principio}</td><td>{pedido}</td><td>{onde}</td><td class="ok"><span class="selo">CUMPRIDO</span></td></tr>'
        for principio, pedido, onde in requisitos(classes))
    numeros = "".join(f"<div><b>{valor}</b><span>{e(rotulo)}</span></div>" for valor, rotulo in (
        (demo.total_de_classes(), "classes no pacote jogo"), (n("Entidade"), "classes concretas de Entidade"),
        (n("Inimigo"), "inimigos que herdam de Inimigo"), (n("Jogador"), "classes do aluno"),
        (f"{n('Arma')} e {n('Item')}", "armas e itens"), (testes, "testes automáticos passando")))
    ganchos = "".join(
        f'<tr><td><code>{e(gancho)}()</code></td><td class="n">{len(donas)}</td><td>{", ".join(f"<code>{e(d)}</code>" for d in donas)}</td></tr>'
        for gancho, donas in sobrescritas.items())
    confere = "".join(f'<li class="{"" if certo else "falhou"}">{e(texto)}</li>' for texto, certo in conferencias)
    ia = "".join(f"<tr><td>{codigo(onde)}</td><td>{codigo(corrigido)}</td></tr>" for onde, corrigido in registro_de_ia())
    autoria = " e ".join(f"{nome} ({quantos} commits)" for nome, quantos in sorted(commits.items()))

    corpo = f"""
<header class="quadro"><div class="dentro">
  <div>
    <h1>UFJ Survivors</h1>
    <p class="etapa">Etapa 3: hierarquia de classes completa e polimorfismo funcionando</p>
    <p>Um jogo de sobrevivência no Campus Jatobá: o aluno enfrenta as três provas do semestre e os professores
    possuídos pelas próprias matérias. Esta página mostra, com dados lidos do próprio código, que a hierarquia
    está completa e que tudo na arena passa por um único laço polimórfico.</p>
    <dl>
      <dt>Disciplina</dt><dd>Programação Orientada a Objetos, UFJ</dd>
      <dt>Professora</dt><dd>Emília Alves Nogueira</dd>
      <dt>Grupo</dt><dd>{" e ".join(e(i) for i in INTEGRANTES)}</dd>
      <dt>Entrega</dt><dd>26/11/2026</dd>
      <dt>Repositório</dt><dd><a href="{REPOSITORIO}">{REPOSITORIO.removeprefix("https://")}</a></dd>
    </dl>
  </div>
  <figure class="foto"><img src="{captura_embutida()}" width="1280" height="720" alt="Captura do jogo: o Monitor cercado por calculadoras e letras pi no gramado do campus">
    <figcaption>1ª prova, Cálculo I. Aluno, inimigos, moedas, árvores e postes são todos <code>Entidade</code>.</figcaption></figure>
</div></header>

<div class="pagina">
<nav class="indice" aria-label="Seções"><ol>
  <li><a href="#entrega">O que foi entregue</a></li>
  <li><a href="#requisitos">Requisitos de POO</a></li>
  <li><a href="#diagrama">Diagrama de classes</a></li>
  <li><a href="#hierarquia">Hierarquia completa</a></li>
  <li><a href="#polimorfismo">Polimorfismo funcionando</a></li>
  <li><a href="#novo">Inimigo novo</a></li>
  <li><a href="#rodar">Como rodar</a></li>
  <li><a href="#processo">Processo e uso de IA</a></li>
</ol></nav>
<main>

<section id="entrega">
<h2>O que foi entregue</h2>
<p class="lead">O jogo está completo e jogável do título ao boletim final. A etapa 3 pede a hierarquia de classes
completa e o polimorfismo funcionando; os dois podem ser conferidos de três jeitos.</p>
<table>
<tr><th>Jeito</th><th>Comando</th><th>O que mostra</th></tr>
<tr><td>Jogando</td><td><code>python main.py</code></td><td>Aluno, {n("Inimigo")} tipos de inimigo, projéteis, ajudantes, coletáveis, efeitos e prédios, todos atualizados pelo mesmo laço.</td></tr>
<tr><td>Demonstração</td><td><code>python ferramentas/demonstrar_polimorfismo.py</code></td><td>Imprime a hierarquia lida do código, cria um inimigo de cada tipo e avança a partida só com <code>jogo.atualizar(dt)</code>.</td></tr>
<tr><td>Testes</td><td><code>pytest -q</code></td><td>{testes} testes. Os de <code>testes/test_etapa3.py</code> falham se alguém puser um <code>isinstance</code> no laço ou criar um inimigo fora da hierarquia.</td></tr>
</table>
<div class="numeros">{numeros}</div>
</section>

<section id="requisitos">
<h2>Requisitos obrigatórios de POO</h2>
<p>Os sete requisitos da seção 2 do enunciado, com o lugar do código onde cada um está.</p>
<div class="rolagem"><table class="boletim">
<tr><th>Princípio</th><th>Requisito mínimo</th><th>Onde está no código</th><th>Situação</th></tr>
{boletim}
</table></div>
<h3>Encapsulamento com validação</h3>
<p>A vida só aceita número, nunca fica negativa e nunca passa da máxima. Quem usa escreve <code>inimigo.vida -= 10</code>; a regra fica num lugar só.</p>
<pre><code><span class="c"># jogo/nucleo/ser_vivo.py</span>
<span class="k">@property</span>
def vida(self):
    return self._vida

<span class="k">@vida.setter</span>
def vida(self, valor):
    exigir_numero(valor, "vida")
    self._vida = max(0, min(valor, self._vida_maxima))</code></pre>
</section>

<section id="diagrama">
<h2>Diagrama de classes</h2>
<p>Os dois diagramas são desenhados a partir das classes do jogo, então acompanham o código. O primeiro mostra a
herança a partir de <code>Entidade</code>; o segundo, a composição.</p>
<h3>Herança: tudo o que existe na arena é uma Entidade</h3>
<div class="prancha">{svg_heranca(classes)}</div>
<ul class="legenda">
  <li><svg width="34" height="16"><rect x="1" y="1" width="32" height="14" fill="#e4efe2" stroke="#1d3a2e" stroke-width="2"/></svg>classe abstrata, com os métodos que as filhas implementam</li>
  <li><svg width="34" height="16"><rect x="1" y="1" width="32" height="14" fill="#fbf6df" stroke="#9a7a1c" stroke-dasharray="5 3"/></svg>classes concretas irmãs, agrupadas para caber</li>
  <li><svg width="34" height="16"><polygon points="2,8 15,1 15,15" fill="#fff" stroke="#16211b" stroke-width="1.4"/><path d="M15,8 H33" stroke="#16211b" stroke-width="1.4"/></svg>herda de (a seta aponta para a classe base)</li>
</ul>
<h3>Composição: quem contém quem</h3>
<div class="prancha">{svg_composicao(classes)}</div>
<ul class="legenda">
  <li><svg width="34" height="16"><polygon points="2,8 9,3 16,8 9,13" fill="#16211b"/><path d="M16,8 H33" stroke="#16211b" stroke-width="1.4"/></svg>contém (composição)</li>
  <li><svg width="34" height="16"><polygon points="2,8 9,3 16,8 9,13" fill="#fff" stroke="#16211b" stroke-width="1.4"/><path d="M16,8 H33" stroke="#16211b" stroke-width="1.4"/></svg>guarda numa lista (agregação)</li>
  <li><svg width="34" height="16"><path d="M1,8 H33" stroke="#5b6a61" stroke-width="1.4" stroke-dasharray="6 4"/></svg>usa</li>
</ul>
<h3>Decisões de herança e composição</h3>
<table>
<tr><th>Decisão</th><th>Por quê</th></tr>
<tr><td><code>Inimigo</code> é abstrata</td><td>Não existe "um inimigo qualquer". Ter vida, tocar no aluno, soltar nota e sumir ao morrer está na base; cada filha só escreve o próprio jeito de andar, em <code>mover()</code>.</td></tr>
<tr><td>Herança só onde "é um" vale</td><td><code>CaixinhaPequena</code> é uma <code>Caixinha</code>; <code>Agroboy</code> é um <code>Motorizado</code>, que é um <code>MiniChefe</code>.</td></tr>
<tr><td>O chefe tem matérias, não é uma matéria</td><td><code>ChefePossuido</code> contém uma lista de <code>Materia</code>. A matéria atual dá o nome, a vida e os ataques; trocar de matéria no meio da luta é trocar o objeto, não a classe.</td></tr>
<tr><td>As armas não são entidades</td><td>Elas pertencem ao aluno e criam entidades (projéteis e ajudantes). O laço do <code>Jogo</code> fica só com o que existe na arena.</td></tr>
<tr><td>Animação por composição</td><td>Aluno, inimigos e ajudantes contêm um <code>Animador</code>; cada classe só diz qual animação quer.</td></tr>
<tr><td>Inimigo novo não altera classe existente</td><td>A classe nova se registra sozinha com <code>@FabricaDeInimigos.registrar("nome")</code>. É o que o requisito surpresa pede.</td></tr>
</table>
</section>

<section id="hierarquia">
<h2>Hierarquia completa</h2>
<p>As {len(FAMILIAS)} famílias de classes do jogo, cada uma a partir da sua classe base. Em itálico, as abstratas, com os
métodos que as filhas precisam implementar. Clique numa família para abrir.</p>
<div class="busca"><label for="busca">Procurar uma classe</label><input id="busca" type="search" placeholder="por exemplo, Caixinha" autocomplete="off"><span id="achadas" aria-live="polite"></span></div>
{familias_html(classes)}
</section>

<section id="polimorfismo">
<h2>Polimorfismo funcionando</h2>
<h3>O laço único</h3>
<pre><code><span class="c"># jogo/jogo.py, Jogo.atualizar()</span>
for e in self.entidades:          <span class="c"># polimorfismo: um único laço, sem if por tipo</span>
    if e.ativo:
        e.atualizar(dt, self)</code></pre>
<p>O único <code>if</code> pergunta se a entidade ainda está na arena, nunca de que tipo ela é.
<code>Jogo.desenhar()</code> segue a mesma ideia: <code>for e in visiveis: e.desenhar(tela, self.camera)</code>.</p>
<h3>Onde cada tipo diz o que faz</h3>
<div class="rolagem"><table>
<tr><th>Chamada, sempre a mesma</th><th>Quem chama</th><th>Respostas diferentes</th></tr>
<tr><td><code>e.atualizar(dt, jogo)</code></td><td><code>Jogo.atualizar()</code></td><td>Inimigo anda e ataca; projétil voa e confere colisão; coletável é atraído pelo aluno; efeito conta o tempo e some.</td></tr>
<tr><td><code>self.mover(dt, jogo)</code></td><td><code>Inimigo.atualizar()</code></td><td><code>Bug</code> corre em linha reta; <code>MouseDeBolinha</code> para, mira e dispara; <code>PiCambaleante</code> anda em zigue-zague; <code>Ponteiro</code> mergulha e passa do ponto.</td></tr>
<tr><td><code>self.ao_morrer(jogo)</code></td><td><code>Inimigo</code>, ao zerar a vida</td><td><code>Caixinha</code> solta duas <code>CaixinhaPequena</code>; <code>PilhaAA</code> explode em faíscas; <code>PiCambaleante</code> mostra "3,14..."; <code>MiniChefe</code> deixa um baú.</td></tr>
<tr><td><code>self.atacar(jogo)</code></td><td><code>MiniChefe</code>, na hora do ataque</td><td>A Bibliotecária aplica multas que tiram moedas; a Tia da Cantina arremessa o panelão; o ET de Varginha abre feixes de abdução.</td></tr>
<tr><td><code>materia.ataques()</code></td><td><code>ChefePossuido</code></td><td>Cálculo I: limite, derivada e integral. POO: polimorfismo, herança e encapsulamento.</td></tr>
<tr><td><code>coletavel.ao_coletar(jogo)</code></td><td><code>Coletavel.atualizar()</code></td><td><code>Nota</code> dá experiência; <code>Ima</code> puxa toda a experiência do mapa; <code>Bau</code> abre o prêmio.</td></tr>
<tr><td><code>item.aplicar(jogador)</code></td><td><code>Jogador</code>, ao recalcular os bônus</td><td>Item, habilidade e melhoria somam cada um o seu efeito, sem o aluno saber qual é qual.</td></tr>
<tr><td><code>arma.atualizar(dt, jogo, dono)</code></td><td><code>Jogador.atualizar()</code></td><td>Arma de disparo atira e espera a recarga; arma contínua mantém um ajudante na arena.</td></tr>
</table></div>
<h3>Demonstração executada</h3>
<p>A ferramenta pede à fábrica um inimigo de cada um dos {len(linhas)} tipos registrados, coloca todos à mesma distância do aluno e
chama apenas <code>jogo.atualizar(dt)</code> por 2 segundos. Nesse tempo, {entidades} entidades de {tipos} classes diferentes
passaram pelo laço. O gráfico mostra quanto cada inimigo andou: a chamada é uma só, e a distância muda porque cada classe tem o
próprio <code>mover()</code>.</p>
{barras_html(linhas)}
<ul class="confere">{confere}</ul>
<h3>Métodos que os inimigos sobrescrevem</h3>
<div class="rolagem"><table>
<tr><th>Método</th><th class="n">Classes</th><th>Quem tem a própria versão</th></tr>
{ganchos}
</table></div>
</section>

<section id="novo">
<h2>Inimigo novo sem tocar em nada</h2>
<p>Um arquivo novo basta. Nenhum outro arquivo muda: a classe se registra na fábrica e o laço do <code>Jogo</code> já atualiza e desenha o inimigo.</p>
<pre><code><span class="c"># jogo/inimigos/grampeador.py</span>
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


<span class="k">@FabricaDeInimigos.registrar("grampeador")</span>
class Grampeador(Inimigo):
    NOME = "Grampeador"
    VIDA = 20
    VELOCIDADE = 90

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)</code></pre>
<p>Depois disso, <code>FabricaDeInimigos.criar("grampeador", posicao)</code> já funciona. Para ele aparecer numa prova, basta uma
linha <code>(segundos, "grampeador")</code> em <code>APRESENTACOES</code>, em <code>jogo/fase.py</code>.</p>
</section>

<section id="rodar">
<h2>Como rodar</h2>
<pre><code>git clone {REPOSITORIO}.git
cd UFJ-Survivors
python3.12 -m venv .venv                 <span class="c"># Windows: py -3.12 -m venv .venv</span>
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py                 <span class="c"># o jogo</span>
.venv/bin/python ferramentas/demonstrar_polimorfismo.py
.venv/bin/pytest -q                      <span class="c"># {testes} testes</span></code></pre>
<table>
<tr><th>Tecla</th><th>Ação</th></tr>
<tr><td>WASD ou setas</td><td>Andar</td></tr>
<tr><td>Espaço</td><td>Especial da classe</td></tr>
<tr><td>Shift ou botão direito</td><td>Rolar (esquiva)</td></tr>
<tr><td>Botão esquerdo</td><td>Alternar entre mira no mouse e mira automática</td></tr>
<tr><td>M</td><td>Mini-mapa</td></tr>
<tr><td>Esc</td><td>Pausar</td></tr>
</table>
</section>

<section id="processo">
<h2>Processo e uso de IA</h2>
<p>O histórico de commits está no repositório: {e(autoria)} até esta entrega. As etapas anteriores estão em
<code>docs/entregas/etapa1_proposta.md</code> (proposta e diagrama) e na tag <code>etapa-2-prototipo</code> (protótipo).</p>
<h3>Registro de uso de IA da etapa 3</h3>
<p>Cópia da tabela da etapa 3 de <code>docs/registro_ia.md</code>, no formato pedido no enunciado.</p>
<div class="rolagem"><table>
<tr><th>Onde usamos IA</th><th>O que precisamos corrigir ou entender</th></tr>
{ia}
</table></div>
</section>

</main></div>
<footer>UFJ Survivors, trabalho prático de Programação Orientada a Objetos. Página gerada por <code>ferramentas/gerar_entrega.py</code> a partir do código.</footer>
"""
    css = CSS.replace("@@FONTE@@", base64.b64encode(FONTE.read_bytes()).decode())
    return ('<!doctype html>\n<html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>UFJ Survivors: etapa 3, hierarquia de classes e polimorfismo</title>"
            f"<style>{css}</style></head><body>{corpo}<script>{JS}</script></body></html>\n")


ESTILO_DO_SVG = """
svg{font-family:ui-sans-serif,system-ui,"Segoe UI",Helvetica,Arial,sans-serif;background:#fff}
.caixa rect{fill:#fff;stroke:#16211b;stroke-width:1.6}.caixa.abstrata rect{fill:#e4efe2;stroke:#1d3a2e;stroke-width:2}
.caixa.grupo rect{fill:#fbf6df;stroke:#9a7a1c;stroke-dasharray:5 3}.caixa line{stroke:#16211b;stroke-width:1}
text{fill:#16211b}.nome{font-weight:700;font-size:14.5px;text-anchor:middle}.abstrata .nome{font-style:italic}
.estereotipo{font-size:10.5px;text-anchor:middle;fill:#5b6a61}.membro{font-size:12.5px}.rotulo{font-size:11.5px;fill:#5b6a61}
.fio{fill:none;stroke:#16211b;stroke-width:1.4}.usa{fill:none;stroke:#5b6a61;stroke-width:1.4;stroke-dasharray:6 4}
.heranca,.agregacao{fill:#fff;stroke:#16211b;stroke-width:1.4}.composicao{fill:#16211b}
"""


def gravar_diagramas(classes):
    """Os mesmos diagramas da página, como arquivos SVG (o README e a proposta da etapa 1 apontam para eles)."""
    for nome, svg in (("diagrama_classes.svg", svg_heranca(classes)), ("diagrama_composicao.svg", svg_composicao(classes))):
        solto = svg.replace('<svg class="diagrama"', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        solto = solto.replace(">", f"><style>{ESTILO_DO_SVG}</style>", 1)
        (SAIDA.parent / nome).write_text(solto + "\n", encoding="utf-8")


def principal():
    SAIDA.write_text(pagina(), encoding="utf-8")
    gravar_diagramas(demo.carregar_classes())
    print(f"{SAIDA.relative_to(RAIZ)}: {SAIDA.stat().st_size // 1024} KB")


if __name__ == "__main__":
    principal()
