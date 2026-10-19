# UFJ Survivors

Sobreviva às provas do semestre na UFJ. Jogo 2D em Pygame no estilo "survivors", feito para o trabalho prático de Programação Orientada a Objetos: três provas de 5 minutos no Campus Jatobá (mapa gerado de satélite e OpenStreetMap), personagens ilustrados e animados no estilo Disgaea, inimigos que são objetos das matérias do semestre e, no fim de cada prova, um professor possuído pela própria matéria como chefe.

| Prova | Chefe | Fases da luta |
|---|---|---|
| 1ª | Professor de Cálculo | Cálculo I |
| 2ª | Professor de Arquitetura e ED | Arquitetura de Computadores, depois Estrutura de Dados em C |
| 3ª | Professora de TD e POO | Transformação Digital, depois Programação Orientada a Objetos |

No chefe de duas matérias, quando a vida da primeira zera, a segunda (mais difícil) possui o professor e a luta continua com a vida cheia.

![Captura de tela](docs/entregas/captura_combate.png)

> **Vai trabalhar no projeto (você ou sua IA)?** Leia primeiro o [AGENTS.md](AGENTS.md) e a lista de [pendências](docs/PENDENCIAS.md).

## Como rodar

Requer Python 3.12.

macOS / Linux:
```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Windows:
```bat
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py
```

## Controles

| Tecla | Ação |
|---|---|
| WASD ou setas | Andar (as armas atacam sozinhas) |
| Mouse | Mirar as armas de disparo e o especial |
| Clique esquerdo | Alterna entre mira no mouse e mira automática (inimigo mais próximo) |
| Espaço | Especial |
| Esc | Pausar |
| 1, 2, 3 ou Enter | Escolher carta ao subir de nível |
| R / P | Sortear as cartas de novo / pular a escolha |

## Testes

```bash
.venv/bin/pytest
```

Para simular uma partida inteira sem janela (útil para balancear):
```bash
.venv/bin/python ferramentas/simular_partida.py --heroi 1 --imortal
```

## Ferramentas de arte

```bash
.venv/bin/python ferramentas/gerar_mapa.py        # mapa do Campus Jatobá (baixa satélite e OpenStreetMap se faltar)
.venv/bin/python ferramentas/montar_sprites.py    # folhas de animação -> pixel art (precisa das folhas em arte_bruta/)
.venv/bin/python ferramentas/gerar_sons.py        # efeitos sonoros
```

## Onde está cada requisito de POO

| Requisito | Arquivo | Classe / método |
|---|---|---|
| Classe abstrata com `atualizar()` e `desenhar()` | `jogo/nucleo/entidade.py` | `Entidade` |
| 3+ inimigos herdando de uma base | `jogo/inimigos/` | `Inimigo` e `Bug`, `CalculadoraBrava`, `MouseDeBolinha`, `Caixinha`, `PiCambaleante`, `Ponteiro`, `PilhaAA`, `PenteDeRAM`; chefes: `Chefe` > `ChefePossuido` > `ProfessorDeCalculo`, `ProfessorDeArquiteturaEED`, `ProfessoraDeTDEPOO`; matérias: `Materia` > `CalculoI`, `ArquiteturaDeComputadores`, `EstruturaDeDadosEmC`, `TransformacaoDigital`, `ProgramacaoOrientadaAObjetos` |
| Polimorfismo num único laço, sem `if` por tipo | `jogo/jogo.py` | `Jogo.atualizar()` |
| Encapsulamento com `@property` e validação | `jogo/nucleo/ser_vivo.py`, `jogo/placar.py`, `jogo/armas/arma.py` | `SerVivo.vida`, `Placar.pontos`, `ArmaDeDisparo.municao` |
| Composição | `jogo/jogo.py`, `jogo/jogador/jogador.py` | `Jogo` contém `Jogador`, `Fase` (a lista das três provas), `Placar`; `Jogador` contém `Arma`, `Item`, `Especial`; `ChefePossuido` contém suas `Materia` |
| Métodos especiais | `jogo/ranking.py` | `RegistroRanking.__lt__`, `__eq__`, `__str__` |
| `@classmethod` e `@staticmethod` | `jogo/inimigos/fabrica.py`, `jogo/nucleo/colisao.py` | `FabricaDeInimigos.criar()`, `Colisao.circulos_colidem()` |

Diagrama de classes: [docs/entregas/diagrama_classes.png](docs/entregas/diagrama_classes.png). Proposta completa: [docs/entregas/etapa1_proposta.md](docs/entregas/etapa1_proposta.md).

## Estrutura

```
main.py            ponto de entrada
jogo/
  nucleo/          Entidade, SerVivo, Colisao, Animacao/Animador, câmera, grade espacial, arte e som
  jogador/         Jogador, os dois alunos, especiais, bônus temporários
  inimigos/        Inimigo, fábrica, um arquivo por inimigo, Chefe, ChefePossuido e os três chefes
    materias/      Materia e uma matéria por arquivo (os ataques de cada chefe)
  armas/           Arma e suas famílias, uma arma por arquivo, colabs
  itens/           itens passivos
  projeteis/  ajudantes/  coletaveis/
  cenas/           telas (título, seleção, partida, nível, baú, pausa, fim, ranking) e HUD
  jogo.py fase.py placar.py ranking.py progressao.py efeitos.py
  mapa.py cenario.py  Mapa (abstrata), MapaUFJ, Predio, Decoracao e o pátio genérico
assets/            sprites, ícones, cenário, sons, fontes e a arte reaproveitada (legado/)
ferramentas/       preparo da arte, geração dos sons, simulador de partida
testes/            testes automáticos (pytest)
docs/              entregas, diagrama, registro de uso de IA, especificação e plano
```

## Como criar um inimigo novo

Basta um arquivo novo em `jogo/inimigos/`. Nenhuma classe existente muda:

```python
# jogo/inimigos/cafe_frio.py
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("cafe_frio")
class CafeFrio(Inimigo):
    NOME = "Café Frio"
    IMAGEM = "sprites/cafe.png"
    VIDA = 15
    VELOCIDADE = 60

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)
```

Para ele aparecer, acrescente `(tempo_em_segundos, "cafe_frio")` em `APRESENTACOES` de uma das provas (`ProvaDeCalculo`, `ProvaDeArquiteturaEED` ou `ProvaDeTDEPOO`, em `jogo/fase.py`).

## Como criar uma matéria (ou um chefe) novo

Uma matéria é uma classe que herda de `Materia` e diz quais ataques usa; os ataques prontos (`leque`, `anel`, `rajada`, `chamada`, `chefe.investir`) já existem:

```python
# jogo/inimigos/materias/banco_de_dados.py
from jogo.inimigos.materias.materia import Materia


class BancoDeDados(Materia):
    NOME = "Banco de Dados"
    COR = (255, 220, 90)
    SIMBOLO = "SQL"
    VIDA = 2500
    LACAIOS = ("caixinha", "bug")

    def ataques(self):
        return [self.select, self.join]

    def select(self, chefe, jogo):
        self.leque(chefe, jogo, 9)

    def join(self, chefe, jogo):
        self.anel(chefe, jogo, 12, simbolo="JOIN")
```

Para virar chefe, um arquivo em `jogo/inimigos/` com uma classe que herda de `ChefePossuido`, registrada na fábrica e com `MATERIAS = (BancoDeDados,)`. Nenhuma classe existente muda.

## Créditos

Veja [assets/CREDITOS.md](assets/CREDITOS.md). A arte em `assets/legado/` foi reaproveitada do jogo "Crônicas do Saber" (Fiuphis/Rpggame).
