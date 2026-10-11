# UFJ Survivors: plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** construir a primeira fase jogável de "UFJ Survivors" (sobrevivência por ondas, 15 minutos, chefe final) em Python com Pygame, cumprindo os requisitos de POO do trabalho, com arte gerada desde o protótipo.

**Architecture:** uma hierarquia de `Entidade` (abstrata) atualizada num único laço polimórfico dentro de `Jogo`; `Jogo` contém `Jogador`, `Fase`, `Placar`; armas, itens e especiais são objetos compostos no `Jogador`; inimigos nascem por uma fábrica com registro por decorador. Telas são `Cena`s empilhadas numa `Aplicacao`. Arte é gerada pela ferramenta de imagens e reduzida por um script; sons são sintetizados por script.

**Tech Stack:** Python 3.12, pygame-ce 2.5.8, pytest 9, Pillow 12 (só nas ferramentas de arte).

**Spec:** `docs/superpowers/specs/2026-10-10-ufj-survivors-design.md`

## Global Constraints

- Python 3.12 em `.venv` (criado com `~/.local/bin/python3.12 -m venv .venv`); comandos usam `.venv/bin/python` e `.venv/bin/pytest`.
- Biblioteca gráfica: `pygame-ce==2.5.8` (importada como `import pygame`).
- Janela 1280x720, 60 FPS, um jogador; arena 3200x1800; fase de 15 minutos (900 s); limite de 300 inimigos vivos.
- Nomes de classes, métodos, variáveis, comentários e textos do jogo em português; textos do jogo sem emojis.
- Requisitos de POO do enunciado (seção 2) obrigatórios e apontáveis no código: `Entidade` abstrata com `atualizar()`/`desenhar()`; 3+ inimigos herdando de `Inimigo`; laço único `for e in self.entidades: e.atualizar(dt, self)` sem `if` por tipo; `vida`, `pontos`, `municao` com `@property` e validação; `Jogo` contém `Jogador`, `Fase`, `Placar`; `Jogador` contém `Arma`; `__lt__`/`__eq__`/`__str__` em `RegistroRanking`; `@classmethod` na fábrica de inimigos e `@staticmethod` em `Colisao`.
- Todo caminho de arte é relativo a `assets/`; arte ausente nunca derruba o jogo (substituto desenhado).
- Testes rodam sem janela: `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy` (definidos em `testes/conftest.py`).
- Commits com a linha `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` no fim da mensagem.

## Review Focus

- `dados/ranking.json` ausente, vazio ou corrompido: o jogo abre e o ranking começa vazio (teste em Task 4).
- Arquivo de imagem ou som ausente: o jogo usa substituto e segue (teste em Task 3).
- Muita experiência de uma vez (baú, nota acumulada): sobe vários níveis e abre a tela de escolha uma vez por nível (teste em Task 8).
- Tudo no nível máximo ou sem espaço: a tela de nível ainda oferece uma opção ("Lanche da Cantina") (teste em Task 13).
- Muitas entidades ao mesmo tempo (300 inimigos, notas, projéteis): o quadro continua rápido; notas se acumulam em vez de multiplicar (teste em Task 14).

---

## Mapa de arquivos

```
main.py                         ponto de entrada (Task 10; aponta para o título na Task 17)
requirements.txt  pytest.ini    (Task 1)
jogo/
  config.py                     constantes e cores (Task 1)
  aplicacao.py                  Aplicacao: janela e pilha de cenas (Task 10)
  jogo.py                       Jogo: a partida (Task 9)
  fase.py                       EventoDaFase, Fase, SemanaDeProvas (Task 9; linha do tempo completa na Task 15)
  placar.py  ranking.py         Placar, RegistroRanking, Ranking (Task 4)
  progressao.py                 Opcao, Progressao (Task 14)
  cenario.py                    Decoracao, Cenario (Task 9)
  efeitos.py                    Efeito, TextoFlutuante, FaiscaExplosao (Task 6); AuraSSJ, RaioZoltraak (Task 8);
                                GolpeClaude (Task 13); RaioDebate (Task 14)
  nucleo/  entidade.py ser_vivo.py colisao.py grade.py camera.py (Task 2); recursos.py desenho.py (Task 3)
  jogador/ especial.py bonus.py (Task 5); jogador.py alunos.py especiais.py (Task 8)
  inimigos/ __init__.py fabrica.py inimigo.py bug.py (Task 6); os outros lacaios, chefe.py, professor.py (Task 12)
  armas/   arma.py (Task 5); cobra_python.py caramelo.py (Task 7); chatgpt.py claude.py gemini.py fusca.py (Task 13);
           colabs.py (Task 14)
  projeteis/ projeteis.py       (Task 7; acréscimos nas Tasks 12, 13 e 14)
  ajudantes/ ajudantes.py       (Task 7; acréscimos nas Tasks 13 e 14)
  coletaveis/ coletaveis.py     (Task 6)
  itens/   item.py (Task 5); itens.py (Task 14)
  cenas/   cena.py widgets.py hud.py partida.py (Task 10); titulo.py selecao.py nivel.py bau.py pausa.py fim.py
           ranking.py (Task 17)
assets/  sprites/ icones/ cenario/ (Tasks 11 e 16); sons/ (Task 3); fontes/ (Task 1); legado/
ferramentas/ preparar_arte.py gerar_sons.py (Task 3); simular_partida.py (Task 19)
testes/  conftest.py e um test_*.py por assunto
docs/    diagrama_classes.mmd, entregas/, registro_ia.md (Task 18)
```

Cada pacote em `jogo/` tem um `__init__.py` vazio, exceto `jogo/inimigos/__init__.py` (Task 6).

---

### Task 1: Estrutura do projeto

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `jogo/__init__.py`, `jogo/config.py`, `testes/conftest.py`, `testes/test_config.py`
- Move: `assets/legado/fontes/*.woff2` → `assets/fontes/`

**Interfaces:**
- Produces: `jogo.config` com `RAIZ`, `PASTA_ASSETS`, `PASTA_DADOS`, `ARQUIVO_RANKING`, `TITULO`, `LARGURA`, `ALTURA`, `FPS`, `ARENA_LARGURA`, `ARENA_ALTURA`, `DURACAO_FASE`, `MAX_INIMIGOS`, `DISTANCIA_REPOSICIONAR`, `INVENCIBILIDADE_APOS_DANO`, `COMBO_ESPECIAL`, `BONUS_67_VELOCIDADE`, `BONUS_67_DURACAO`, `SORTEIOS_POR_PARTIDA`, `CURA_AO_PULAR`, `LIMITE_COLETAVEIS`, `LIMITE_EFEITOS`, `FONTE`, `FONTE_MEDIA`, classe `Cor`.

- [ ] **Step 1: Arquivos de configuração do projeto**

`requirements.txt`:
```
pygame-ce==2.5.8
pytest==9.1.1
pillow==12.3.0
```

`pytest.ini`:
```ini
[pytest]
testpaths = testes
pythonpath = .
```

`jogo/__init__.py`: vazio.

Mover a fonte: `mkdir -p assets/fontes && git mv assets/legado/fontes/*.woff2 assets/fontes/ && rmdir assets/legado/fontes`

- [ ] **Step 2: Teste que falha**

`testes/conftest.py`:
```python
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def pygame_iniciado():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()
```

`testes/test_config.py`:
```python
from jogo import config


def test_tamanhos_da_janela_e_da_arena():
    assert (config.LARGURA, config.ALTURA) == (1280, 720)
    assert config.ARENA_LARGURA > config.LARGURA
    assert config.ARENA_ALTURA > config.ALTURA
    assert config.DURACAO_FASE == 900


def test_fonte_existe():
    assert (config.PASTA_ASSETS / config.FONTE).exists()
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_config.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.config'`

- [ ] **Step 4: Implementar `jogo/config.py`**

```python
"""Configurações gerais e números de balanceamento do jogo."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_ASSETS = RAIZ / "assets"
PASTA_DADOS = RAIZ / "dados"
ARQUIVO_RANKING = PASTA_DADOS / "ranking.json"

TITULO = "UFJ Survivors"
LARGURA, ALTURA = 1280, 720
FPS = 60

ARENA_LARGURA, ARENA_ALTURA = 3200, 1800
DURACAO_FASE = 15 * 60
MAX_INIMIGOS = 300
DISTANCIA_REPOSICIONAR = 1400   # inimigo mais longe que isso do herói renasce perto dele
INVENCIBILIDADE_APOS_DANO = 0.5
COMBO_ESPECIAL = 67
BONUS_67_VELOCIDADE = 1.5
BONUS_67_DURACAO = 6.0
SORTEIOS_POR_PARTIDA = 3
CURA_AO_PULAR = 20
LIMITE_COLETAVEIS = 400
LIMITE_EFEITOS = 150

FONTE = "fontes/pixelify-sans-latin-700-normal.woff2"
FONTE_MEDIA = "fontes/pixelify-sans-latin-500-normal.woff2"


class Cor:
    FUNDO = (24, 20, 37)
    PAINEL = (34, 30, 52)
    BORDA = (214, 168, 74)
    BORDA_ESCURA = (16, 12, 24)
    TEXTO = (245, 236, 214)
    TEXTO_FRACO = (168, 160, 190)
    VIDA = (226, 64, 74)
    EXPERIENCIA = (96, 196, 255)
    CAFE = (176, 112, 64)
    DESTAQUE = (255, 214, 92)
    DANO = (255, 255, 255)
    DANO_FORTE = (255, 214, 92)
    DANO_HEROI = (255, 90, 90)
    CURA = (120, 230, 120)
    APROVADO = (120, 230, 120)
    REPROVADO = (240, 80, 80)
    GRAMA_FORA = (36, 58, 40)
```

- [ ] **Step 5: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Estrutura do projeto e configuração

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Núcleo (Entidade, SerVivo, Colisao, GradeEspacial, Camera)

**Files:**
- Create: `jogo/nucleo/__init__.py` (vazio), `jogo/nucleo/entidade.py`, `jogo/nucleo/ser_vivo.py`, `jogo/nucleo/colisao.py`, `jogo/nucleo/grade.py`, `jogo/nucleo/camera.py`
- Test: `testes/test_nucleo.py`

**Interfaces:**
- Produces:
  - `Entidade(posicao, raio)`: atributos `posicao: Vector2`, `raio`, `ativo`; atributos de classe `grupo: str = "geral"`, `camada: int = 1`; abstratos `atualizar(dt, jogo)`, `desenhar(tela, camera)`; `remover()`, `distancia_ate(outra)`.
  - `SerVivo(posicao, raio, vida_maxima)`: propriedades `vida`, `vida_maxima`, `esta_vivo`; `receber_dano(q) -> bool` (True se morreu neste golpe), `curar(q)`; atributo `piscar` (segundos de flash branco).
  - `Colisao.circulos_colidem(a, b)`, `Colisao.ponto_no_circulo(ponto, centro, raio)`, `Colisao.segmento_acerta_circulo(inicio, fim, largura, centro, raio)` (todos `@staticmethod`, retornam bool).
  - `GradeEspacial(tamanho_celula=96)`: `reconstruir(entidades)`, `proximos(posicao, raio) -> list` (candidatos; quem chama faz o teste fino).
  - `Camera(largura, altura, arena: Rect)`: `seguir(posicao)`, `para_tela(pos) -> Vector2`, `para_mundo(pos_tela) -> Vector2`, propriedade `retangulo -> Rect`, `visivel(posicao, margem=64) -> bool`.

- [ ] **Step 1: Testes que falham**

`testes/test_nucleo.py`:
```python
import pygame
import pytest

from jogo.nucleo.camera import Camera
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.grade import GradeEspacial
from jogo.nucleo.ser_vivo import SerVivo


class Boneco(SerVivo):
    def atualizar(self, dt, jogo):
        pass

    def desenhar(self, tela, camera):
        pass


def test_entidade_e_abstrata():
    with pytest.raises(TypeError):
        Entidade((0, 0), 5)


def test_vida_comeca_cheia_e_nao_passa_dos_limites():
    b = Boneco((0, 0), 10, 50)
    assert b.vida == 50
    b.vida = 999
    assert b.vida == 50
    b.vida = -10
    assert b.vida == 0
    assert not b.esta_vivo


def test_vida_rejeita_valor_que_nao_e_numero():
    b = Boneco((0, 0), 10, 50)
    with pytest.raises(TypeError):
        b.vida = "muita"
    with pytest.raises(TypeError):
        b.vida = True


def test_vida_maxima_deve_ser_positiva_e_corta_vida_atual():
    b = Boneco((0, 0), 10, 50)
    with pytest.raises(ValueError):
        b.vida_maxima = 0
    b.vida_maxima = 30
    assert b.vida == 30


def test_receber_dano_avisa_so_no_golpe_que_mata():
    b = Boneco((0, 0), 10, 20)
    assert b.receber_dano(5) is False
    assert b.vida == 15
    assert b.piscar > 0
    assert b.receber_dano(100) is True
    assert b.receber_dano(1) is False


def test_dano_e_cura_negativos_sao_recusados():
    b = Boneco((0, 0), 10, 20)
    with pytest.raises(ValueError):
        b.receber_dano(-1)
    with pytest.raises(ValueError):
        b.curar(-1)


def test_curar_nao_passa_do_maximo():
    b = Boneco((0, 0), 10, 20)
    b.receber_dano(15)
    b.curar(100)
    assert b.vida == 20


def test_colisao_de_circulos():
    a = Boneco((0, 0), 10, 1)
    b = Boneco((19, 0), 10, 1)
    c = Boneco((21, 0), 10, 1)
    assert Colisao.circulos_colidem(a, b)
    assert not Colisao.circulos_colidem(a, c)


def test_ponto_no_circulo():
    assert Colisao.ponto_no_circulo((3, 4), (0, 0), 5)
    assert not Colisao.ponto_no_circulo((4, 4), (0, 0), 5)


def test_segmento_acerta_circulo():
    assert Colisao.segmento_acerta_circulo((0, 0), (100, 0), 10, (50, 12), 8)
    assert not Colisao.segmento_acerta_circulo((0, 0), (100, 0), 10, (50, 30), 8)
    assert not Colisao.segmento_acerta_circulo((0, 0), (100, 0), 10, (130, 0), 8)
    assert Colisao.segmento_acerta_circulo((0, 0), (0, 0), 10, (3, 0), 1)


def test_grade_acha_vizinhos_e_ignora_distantes():
    grade = GradeEspacial(100)
    perto = Boneco((150, 150), 10, 1)
    longe = Boneco((900, 900), 10, 1)
    grade.reconstruir([perto, longe])
    achados = grade.proximos((120, 120), 50)
    assert perto in achados
    assert longe not in achados


def test_camera_segue_e_respeita_bordas_da_arena():
    arena = pygame.Rect(0, 0, 3000, 2000)
    cam = Camera(1000, 500, arena)
    cam.seguir((1500, 1000))
    assert cam.para_tela((1500, 1000)) == pygame.Vector2(500, 250)
    cam.seguir((10, 10))
    assert cam.retangulo.topleft == (0, 0)
    cam.seguir((2990, 1990))
    assert cam.retangulo.bottomright == (3000, 2000)
    assert cam.para_mundo(cam.para_tela((2500, 1800))) == pygame.Vector2(2500, 1800)


def test_camera_visivel():
    cam = Camera(1000, 500, pygame.Rect(0, 0, 3000, 2000))
    cam.seguir((500, 250))
    assert cam.visivel((990, 490))
    assert cam.visivel((1050, 250), margem=64)
    assert not cam.visivel((1200, 250), margem=64)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_nucleo.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.nucleo'`

- [ ] **Step 3: Implementar**

`jogo/nucleo/entidade.py`:
```python
"""Classe abstrata base de tudo que existe na arena."""
from abc import ABC, abstractmethod

import pygame


class Entidade(ABC):
    """Algo com posição na arena que se atualiza e se desenha a cada quadro.

    `grupo` diz em qual lista do Jogo a entidade também entra (por exemplo
    "inimigo"), para buscas rápidas. `camada` define a ordem de desenho:
    camadas menores são desenhadas primeiro.
    """

    grupo = "geral"
    camada = 1

    def __init__(self, posicao, raio):
        self.posicao = pygame.Vector2(posicao)
        self.raio = raio
        self.ativo = True

    @abstractmethod
    def atualizar(self, dt, jogo):
        """Avança a entidade `dt` segundos dentro do `jogo`."""

    @abstractmethod
    def desenhar(self, tela, camera):
        """Desenha a entidade na tela, convertendo a posição pela câmera."""

    def remover(self):
        """Marca a entidade para sair do jogo no fim do quadro."""
        self.ativo = False

    def distancia_ate(self, outra):
        return self.posicao.distance_to(outra.posicao)
```

`jogo/nucleo/ser_vivo.py`:
```python
"""Entidades com vida."""
from abc import ABC
from numbers import Real

from jogo.nucleo.entidade import Entidade


def exigir_numero(valor, nome):
    """Recusa o que não for número (bool também é recusado)."""
    if isinstance(valor, bool) or not isinstance(valor, Real):
        raise TypeError(f"{nome} deve ser um número, recebeu {valor!r}")


class SerVivo(Entidade, ABC):
    """Entidade com vida. A vida nunca fica abaixo de 0 nem acima do máximo."""

    DURACAO_PISCAR = 0.12

    def __init__(self, posicao, raio, vida_maxima):
        super().__init__(posicao, raio)
        self._vida = None
        self.vida_maxima = vida_maxima
        self._vida = self._vida_maxima
        self.piscar = 0.0

    @property
    def vida_maxima(self):
        return self._vida_maxima

    @vida_maxima.setter
    def vida_maxima(self, valor):
        exigir_numero(valor, "vida_maxima")
        if valor <= 0:
            raise ValueError("vida_maxima deve ser positiva")
        self._vida_maxima = valor
        if self._vida is not None:
            self._vida = min(self._vida, valor)

    @property
    def vida(self):
        return self._vida

    @vida.setter
    def vida(self, valor):
        exigir_numero(valor, "vida")
        self._vida = max(0, min(valor, self._vida_maxima))

    @property
    def esta_vivo(self):
        return self._vida > 0

    def receber_dano(self, quantidade):
        """Tira vida. Retorna True só no golpe que matou."""
        exigir_numero(quantidade, "dano")
        if quantidade < 0:
            raise ValueError("dano não pode ser negativo")
        estava_vivo = self.esta_vivo
        self.vida = self._vida - quantidade
        self.piscar = self.DURACAO_PISCAR
        return estava_vivo and not self.esta_vivo

    def curar(self, quantidade):
        exigir_numero(quantidade, "cura")
        if quantidade < 0:
            raise ValueError("cura não pode ser negativa")
        self.vida = self._vida + quantidade
```

`jogo/nucleo/colisao.py`:
```python
"""Utilitário de colisão. Todas as entidades colidem como círculos."""
import pygame


class Colisao:
    @staticmethod
    def circulos_colidem(a, b):
        soma = a.raio + b.raio
        return a.posicao.distance_squared_to(b.posicao) <= soma * soma

    @staticmethod
    def ponto_no_circulo(ponto, centro, raio):
        return pygame.Vector2(ponto).distance_squared_to(centro) <= raio * raio

    @staticmethod
    def segmento_acerta_circulo(inicio, fim, largura, centro, raio):
        """True se o círculo encosta na faixa de `largura` que vai de inicio a fim."""
        inicio = pygame.Vector2(inicio)
        trecho = pygame.Vector2(fim) - inicio
        centro = pygame.Vector2(centro)
        comprimento2 = trecho.length_squared()
        t = 0.0 if comprimento2 == 0 else max(0.0, min(1.0, (centro - inicio).dot(trecho) / comprimento2))
        mais_proximo = inicio + trecho * t
        limite = raio + largura / 2
        return mais_proximo.distance_squared_to(centro) <= limite * limite
```

`jogo/nucleo/grade.py`:
```python
"""Grade espacial para achar entidades próximas sem testar todas contra todas."""
from collections import defaultdict


class GradeEspacial:
    def __init__(self, tamanho_celula=96):
        self.tamanho = tamanho_celula
        self._celulas = defaultdict(list)

    def _chave(self, x, y):
        return int(x // self.tamanho), int(y // self.tamanho)

    def reconstruir(self, entidades):
        self._celulas.clear()
        for e in entidades:
            self._celulas[self._chave(e.posicao.x, e.posicao.y)].append(e)

    def proximos(self, posicao, raio):
        """Entidades das células que tocam o quadrado em volta do círculo."""
        x0, y0 = self._chave(posicao[0] - raio, posicao[1] - raio)
        x1, y1 = self._chave(posicao[0] + raio, posicao[1] + raio)
        resultado = []
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                resultado.extend(self._celulas.get((cx, cy), ()))
        return resultado
```

`jogo/nucleo/camera.py`:
```python
"""Câmera que segue o herói sem mostrar fora da arena."""
import pygame


class Camera:
    def __init__(self, largura, altura, arena):
        self.largura = largura
        self.altura = altura
        self.arena = arena
        self.deslocamento = pygame.Vector2(0, 0)

    def seguir(self, posicao):
        x = posicao[0] - self.largura / 2
        y = posicao[1] - self.altura / 2
        x = max(self.arena.left, min(x, self.arena.right - self.largura))
        y = max(self.arena.top, min(y, self.arena.bottom - self.altura))
        self.deslocamento.update(x, y)

    def para_tela(self, posicao):
        return pygame.Vector2(posicao) - self.deslocamento

    def para_mundo(self, posicao_tela):
        return pygame.Vector2(posicao_tela) + self.deslocamento

    @property
    def retangulo(self):
        return pygame.Rect(round(self.deslocamento.x), round(self.deslocamento.y), self.largura, self.altura)

    def visivel(self, posicao, margem=64):
        return self.retangulo.inflate(margem * 2, margem * 2).collidepoint(posicao)
```

`jogo/nucleo/__init__.py`: vazio.

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Núcleo: Entidade, SerVivo, Colisao, grade espacial e câmera

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Recursos, desenho e ferramentas de arte e som

**Files:**
- Create: `jogo/nucleo/recursos.py`, `jogo/nucleo/desenho.py`, `ferramentas/preparar_arte.py`, `ferramentas/gerar_sons.py`
- Modify: `.gitignore` (acrescentar `arte_bruta/`)
- Test: `testes/test_recursos.py`

**Interfaces:**
- Consumes: `jogo.config.PASTA_ASSETS`, `FONTE`.
- Produces:
  - `Recursos.imagem(caminho, altura=None) -> Surface` (cache; substituto se faltar), `Recursos.icone(caminho, tamanho) -> Surface` (cabe num quadrado), `Recursos.silhueta_branca(img)`, `Recursos.espelhada(img)`, `Recursos.rotacionada(img, angulo)`, `Recursos.substituto(nome, altura)` (`@staticmethod`), `Recursos.fonte(tamanho, arquivo=FONTE)`, `Recursos.som(nome)`, `Recursos.tocar(nome, volume=0.5)`, `Recursos.limpar()`; atributo de classe `pasta` (trocável em teste).
  - `SomMudo` com `play()` e `set_volume()` que não fazem nada.
  - `desenhar_sprite(tela, camera, imagem, posicao, *, espelhar=False, piscar=False, escala=(1.0, 1.0), angulo=0.0, deslocamento_y=0.0, sombra=True, alfa=255)`; `desenhar_sombra(tela, centro_tela, largura)`.
  - `ferramentas/preparar_arte.py ENTRADA SAIDA [--altura N] [--ladrilho N] [--tela LxA]`.
  - `ferramentas/gerar_sons.py` grava `assets/sons/{acerto,coleta,nivel,bau,buzina,dano,disparo,especial,claude,vitoria,derrota,67}.wav`.

- [ ] **Step 1: Testes que falham**

`testes/test_recursos.py`:
```python
import pygame

from jogo.nucleo.recursos import Recursos, SomMudo


def test_imagem_existente_carrega_e_vem_do_cache():
    a = Recursos.imagem("legado/itens/potion_hp.png")
    b = Recursos.imagem("legado/itens/potion_hp.png")
    assert a is b
    assert a.get_size() == (46, 68)


def test_imagem_redimensionada_pela_altura():
    img = Recursos.imagem("legado/itens/potion_hp.png", 34)
    assert img.get_height() == 34
    assert img.get_width() == 23


def test_imagem_ausente_vira_substituto_sem_erro():
    img = Recursos.imagem("sprites/nao_existe.png", 40)
    assert img.get_size() == (40, 40)


def test_icone_cabe_no_quadrado():
    img = Recursos.icone("legado/itens/potion_hp.png", 32)
    assert max(img.get_size()) == 32


def test_silhueta_branca_preserva_transparencia():
    sup = pygame.Surface((4, 4), pygame.SRCALPHA)
    sup.fill((10, 20, 30, 255), pygame.Rect(0, 0, 2, 2))
    branca = Recursos.silhueta_branca(sup)
    assert branca.get_at((0, 0)) == pygame.Color(255, 255, 255, 255)
    assert branca.get_at((3, 3)).a == 0


def test_som_ausente_vira_som_mudo():
    som = Recursos.som("som_que_nao_existe")
    assert isinstance(som, SomMudo)
    Recursos.tocar("som_que_nao_existe")


def test_fonte_carrega():
    fonte = Recursos.fonte(20)
    assert fonte.render("Olá", True, (255, 255, 255)).get_width() > 0
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_recursos.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.nucleo.recursos'`

- [ ] **Step 3: Implementar `jogo/nucleo/recursos.py`**

```python
"""Carrega imagens, fontes e sons uma vez só, com substitutos quando falta arquivo."""
import zlib
from pathlib import Path

import pygame

from jogo.config import FONTE, PASTA_ASSETS


class SomMudo:
    """Som que não toca nada. Usado quando o arquivo ou o áudio não existem."""

    def play(self, *args, **kwargs):
        pass

    def set_volume(self, *args):
        pass


class Recursos:
    pasta = PASTA_ASSETS
    _imagens = {}
    _derivadas = {}
    _fontes = {}
    _sons = {}
    _ultimo_toque = {}
    INTERVALO_MINIMO_SOM_MS = 45

    @classmethod
    def imagem(cls, caminho, altura=None):
        chave = (caminho, altura)
        if chave not in cls._imagens:
            arquivo = cls.pasta / caminho
            if arquivo.exists():
                img = pygame.image.load(str(arquivo))
                if pygame.display.get_surface() is not None:
                    img = img.convert_alpha()
            else:
                img = cls.substituto(Path(caminho).stem, altura or 48)
            if altura and img.get_height() != altura:
                largura = max(1, round(img.get_width() * altura / img.get_height()))
                img = cls._redimensionar(img, (largura, int(altura)))
            cls._imagens[chave] = img
        return cls._imagens[chave]

    @classmethod
    def icone(cls, caminho, tamanho):
        """Imagem reduzida para caber num quadrado de `tamanho` pixels."""
        chave = ("icone", caminho, tamanho)
        if chave not in cls._derivadas:
            img = cls.imagem(caminho)
            fator = tamanho / max(img.get_size())
            novo = (max(1, round(img.get_width() * fator)), max(1, round(img.get_height() * fator)))
            cls._derivadas[chave] = cls._redimensionar(img, novo)
        return cls._derivadas[chave]

    @staticmethod
    def _redimensionar(img, tamanho):
        try:
            return pygame.transform.smoothscale(img, tamanho)
        except ValueError:
            return pygame.transform.scale(img, tamanho)

    @classmethod
    def silhueta_branca(cls, imagem):
        chave = ("branca", id(imagem))
        if chave not in cls._derivadas:
            branca = imagem.copy()
            branca.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            cls._derivadas[chave] = branca
        return cls._derivadas[chave]

    @classmethod
    def espelhada(cls, imagem):
        chave = ("espelho", id(imagem))
        if chave not in cls._derivadas:
            cls._derivadas[chave] = pygame.transform.flip(imagem, True, False)
        return cls._derivadas[chave]

    @classmethod
    def rotacionada(cls, imagem, angulo):
        passo = int(round(angulo / 6.0)) * 6 % 360
        chave = ("giro", id(imagem), passo)
        if chave not in cls._derivadas:
            cls._derivadas[chave] = pygame.transform.rotate(imagem, passo)
        return cls._derivadas[chave]

    @staticmethod
    def substituto(nome, altura):
        """Círculo colorido com a inicial do nome, para quando falta a arte."""
        tamanho = max(8, int(altura))
        sup = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        cor = pygame.Color(0)
        cor.hsva = (zlib.crc32(nome.encode()) % 360, 60, 90, 100)
        centro = (tamanho // 2, tamanho // 2)
        pygame.draw.circle(sup, cor, centro, tamanho // 2)
        pygame.draw.circle(sup, (20, 20, 30), centro, tamanho // 2, max(1, tamanho // 16))
        if pygame.font.get_init():
            letra = pygame.font.Font(None, int(tamanho * 0.7)).render(nome[:1].upper(), True, (20, 20, 30))
            sup.blit(letra, letra.get_rect(center=centro))
        return sup

    @classmethod
    def fonte(cls, tamanho, arquivo=FONTE):
        chave = (arquivo, tamanho)
        if chave not in cls._fontes:
            caminho = cls.pasta / arquivo
            cls._fontes[chave] = pygame.font.Font(str(caminho) if caminho.exists() else None, tamanho)
        return cls._fontes[chave]

    @classmethod
    def som(cls, nome):
        if nome not in cls._sons:
            arquivo = cls.pasta / "sons" / f"{nome}.wav"
            som = SomMudo()
            if pygame.mixer.get_init() and arquivo.exists():
                try:
                    som = pygame.mixer.Sound(str(arquivo))
                except pygame.error:
                    som = SomMudo()
            cls._sons[nome] = som
        return cls._sons[nome]

    @classmethod
    def tocar(cls, nome, volume=0.5):
        """Toca um som, ignorando repetições muito próximas do mesmo som."""
        agora = pygame.time.get_ticks()
        if agora - cls._ultimo_toque.get(nome, -10_000) < cls.INTERVALO_MINIMO_SOM_MS:
            return
        cls._ultimo_toque[nome] = agora
        som = cls.som(nome)
        som.set_volume(volume)
        som.play()

    @classmethod
    def limpar(cls):
        for cache in (cls._imagens, cls._derivadas, cls._fontes, cls._sons, cls._ultimo_toque):
            cache.clear()
```

`jogo/nucleo/desenho.py`:
```python
"""Funções de desenho de sprites com animação simples feita por código."""
import pygame

from jogo.nucleo.recursos import Recursos

_sombras = {}


def desenhar_sombra(tela, centro_tela, largura):
    largura = max(6, int(largura))
    if largura not in _sombras:
        altura = max(3, largura // 3)
        sombra = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 70), sombra.get_rect())
        _sombras[largura] = sombra
    sombra = _sombras[largura]
    tela.blit(sombra, sombra.get_rect(center=(round(centro_tela[0]), round(centro_tela[1]))))


def desenhar_sprite(tela, camera, imagem, posicao, *, espelhar=False, piscar=False,
                    escala=(1.0, 1.0), angulo=0.0, deslocamento_y=0.0, sombra=True, alfa=255):
    """Desenha a imagem centrada na posição, com os pés na base do sprite.

    `deslocamento_y` levanta o sprite (pulo/balanço) sem mover a sombra.
    """
    centro = camera.para_tela(posicao)
    base_y = centro.y + imagem.get_height() / 2
    if sombra:
        desenhar_sombra(tela, (centro.x, base_y), imagem.get_width() * 0.75)
    img = imagem
    if piscar:
        img = Recursos.silhueta_branca(img)
    if espelhar:
        img = Recursos.espelhada(img)
    if escala != (1.0, 1.0):
        img = pygame.transform.scale(img, (max(1, int(img.get_width() * escala[0])),
                                           max(1, int(img.get_height() * escala[1]))))
    if angulo:
        img = Recursos.rotacionada(img, angulo)
        retangulo = img.get_rect(center=(round(centro.x), round(centro.y - deslocamento_y)))
    else:
        retangulo = img.get_rect(midbottom=(round(centro.x), round(base_y - deslocamento_y)))
    if alfa < 255:
        img = img.copy()
        img.set_alpha(alfa)
    tela.blit(img, retangulo)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 5: Ferramenta de preparo de arte**

`ferramentas/preparar_arte.py`:
```python
"""Prepara imagens geradas para o jogo.

Uso:
  python ferramentas/preparar_arte.py ENTRADA SAIDA --altura 64      sprite: recorta o vazio e reduz
  python ferramentas/preparar_arte.py ENTRADA SAIDA --ladrilho 256   chão: quadrado que se repete sem emenda
  python ferramentas/preparar_arte.py ENTRADA SAIDA --tela 1280x720  fundo: cobre a tela inteira
"""
import argparse
from pathlib import Path

from PIL import Image, ImageChops


def recortar_vazio(img):
    alfa = img.getchannel("A").point(lambda a: 255 if a > 8 else 0)
    caixa = alfa.getbbox()
    return img.crop(caixa) if caixa else img


def reduzir_para_altura(img, altura):
    largura = max(1, round(img.width * altura / img.height))
    return img.resize((largura, altura), Image.LANCZOS)


def tornar_ladrilhavel(img, lado):
    img = img.convert("RGB").resize((lado, lado), Image.LANCZOS)
    rolada = ImageChops.offset(img, lado // 2, lado // 2)
    mascara = Image.new("L", (lado, lado))
    metade = lado / 2
    pixels = mascara.load()
    for y in range(lado):
        for x in range(lado):
            perto_da_borda = max(abs(x - metade), abs(y - metade)) / metade
            pixels[x, y] = int(255 * max(0.0, min(1.0, (perto_da_borda - 0.55) / 0.4)))
    return Image.composite(rolada, img, mascara)


def cobrir_tela(img, largura, altura):
    img = img.convert("RGB")
    fator = max(largura / img.width, altura / img.height)
    img = img.resize((round(img.width * fator), round(img.height * fator)), Image.LANCZOS)
    esquerda = (img.width - largura) // 2
    topo = (img.height - altura) // 2
    return img.crop((esquerda, topo, esquerda + largura, topo + altura))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("entrada")
    p.add_argument("saida")
    p.add_argument("--altura", type=int)
    p.add_argument("--ladrilho", type=int)
    p.add_argument("--tela")
    a = p.parse_args()
    img = Image.open(a.entrada)
    if a.ladrilho:
        img = tornar_ladrilhavel(img, a.ladrilho)
    elif a.tela:
        largura, altura = (int(v) for v in a.tela.lower().split("x"))
        img = cobrir_tela(img, largura, altura)
    else:
        img = recortar_vazio(img.convert("RGBA"))
        if a.altura:
            img = reduzir_para_altura(img, a.altura)
    Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
    img.save(a.saida)
    print(f"{a.saida}: {img.width}x{img.height}")


if __name__ == "__main__":
    main()
```

Acrescentar `arte_bruta/` ao `.gitignore` (as imagens originais geradas ficam fora do repositório).

- [ ] **Step 6: Ferramenta de sons**

`ferramentas/gerar_sons.py`:
```python
"""Sintetiza os efeitos sonoros do jogo em assets/sons/*.wav.

O áudio do 67 usa a voz do sistema (comando `say` do macOS) quando existe;
o grupo pode substituir assets/sons/67.wav pelo áudio que quiser.
"""
import math
import random
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

TAXA = 22050
PASTA = Path(__file__).resolve().parent.parent / "assets" / "sons"


def tom(freq_ini, freq_fim, duracao, forma="quadrada", volume=0.5, ruido=0.0):
    amostras = []
    fase = 0.0
    total = int(TAXA * duracao)
    for i in range(total):
        t = i / total
        freq = freq_ini + (freq_fim - freq_ini) * t
        fase += 2 * math.pi * freq / TAXA
        if forma == "quadrada":
            v = 1.0 if math.sin(fase) >= 0 else -1.0
        elif forma == "triangular":
            v = 2 / math.pi * math.asin(math.sin(fase))
        else:
            v = math.sin(fase)
        v = v * (1 - ruido) + random.uniform(-1, 1) * ruido
        envelope = min(1.0, i / (TAXA * 0.004)) * (1 - t) ** 1.5
        amostras.append(v * envelope * volume)
    return amostras


def silencio(duracao):
    return [0.0] * int(TAXA * duracao)


def gravar(nome, amostras):
    PASTA.mkdir(parents=True, exist_ok=True)
    with wave.open(str(PASTA / f"{nome}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, a)) * 32000)) for a in amostras))


def arpejo(notas, duracao_nota, forma="quadrada", volume=0.4):
    resultado = []
    for n in notas:
        resultado += tom(n, n, duracao_nota, forma, volume)
    return resultado


def gerar_67():
    destino = PASTA / "67.wav"
    if shutil.which("say") and shutil.which("afconvert"):
        with tempfile.TemporaryDirectory() as pasta:
            aiff = Path(pasta) / "67.aiff"
            subprocess.run(["say", "-v", "Samantha", "-r", "170", "-o", str(aiff), "six seven"], check=True)
            subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@22050", "-c", "1", str(aiff), str(destino)], check=True)
            return
    gravar("67", arpejo([523, 659], 0.25, "triangular", 0.6))


def main():
    random.seed(67)
    gravar("acerto", tom(220, 90, 0.05, "quadrada", 0.25, ruido=0.6))
    gravar("disparo", tom(900, 500, 0.04, "quadrada", 0.18))
    gravar("coleta", tom(880, 1320, 0.06, "triangular", 0.35))
    gravar("nivel", arpejo([523, 659, 784, 1046], 0.08, "quadrada", 0.3))
    gravar("bau", arpejo([392, 523, 659, 784, 1046, 1318], 0.07, "triangular", 0.45))
    gravar("buzina", tom(420, 400, 0.16, "quadrada", 0.35) + silencio(0.05) + tom(420, 400, 0.22, "quadrada", 0.35))
    gravar("dano", tom(220, 70, 0.15, "quadrada", 0.4, ruido=0.3))
    gravar("especial", tom(250, 1200, 0.6, "triangular", 0.5))
    gravar("claude", tom(1400, 300, 0.18, "senoidal", 0.5, ruido=0.2))
    gravar("vitoria", arpejo([523, 523, 784, 1046], 0.16, "quadrada", 0.35) + tom(1046, 1046, 0.5, "triangular", 0.4))
    gravar("derrota", arpejo([392, 370, 349], 0.22, "quadrada", 0.35) + tom(330, 160, 0.7, "triangular", 0.4))
    gerar_67()
    print(f"sons gravados em {PASTA}")


if __name__ == "__main__":
    main()
```

Run: `.venv/bin/python ferramentas/gerar_sons.py`
Expected: `sons gravados em .../assets/sons` e 12 arquivos `.wav` em `assets/sons/` (conferir com `ls assets/sons`). Ouvir `afplay assets/sons/67.wav` e `afplay assets/sons/buzina.wav`.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "Recursos com substitutos, desenho de sprites e ferramentas de arte e som

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Placar e ranking

**Files:**
- Create: `jogo/placar.py`, `jogo/ranking.py`
- Test: `testes/test_placar_ranking.py`

**Interfaces:**
- Consumes: `jogo.config.COMBO_ESPECIAL`.
- Produces:
  - `Placar()`: propriedade `pontos` (int ≥ 0; `TypeError`/`ValueError`), `eliminacoes`, `tempo` (float, segundos), `combo`, `combos_67`; `adicionar_pontos(q)`, `registrar_eliminacao(pontos) -> bool` (True quando o combo chega a um múltiplo de 67), `zerar_combo()`, `pontuacao_final(venceu) -> int`, propriedade `tempo_formatado -> "mm:ss"`, `__str__`.
  - `RegistroRanking(nome, heroi, pontos, tempo, venceu=False)`: `__lt__`, `__eq__`, `__str__`, `para_dict()`, `RegistroRanking.de_dict(d)` (`@classmethod`). Nome vazio vira "Anônimo"; nome cortado em 12 caracteres.
  - `Ranking(caminho)`: `registros` (lista do melhor para o pior), `adicionar(registro) -> int | None` (posição 1..10 ou None), `salvar()`; `LIMITE = 10`.

- [ ] **Step 1: Testes que falham**

`testes/test_placar_ranking.py`:
```python
import json

import pytest

from jogo.placar import Placar
from jogo.ranking import Ranking, RegistroRanking


def test_pontos_validos():
    p = Placar()
    p.adicionar_pontos(10)
    assert p.pontos == 10
    with pytest.raises(ValueError):
        p.pontos = -1
    with pytest.raises(TypeError):
        p.pontos = 2.5
    with pytest.raises(ValueError):
        p.adicionar_pontos(-5)


def test_combo_67_dispara_a_cada_67_eliminacoes_seguidas():
    p = Placar()
    disparos = [p.registrar_eliminacao(1) for _ in range(134)]
    assert disparos.count(True) == 2
    assert disparos[66] is True and disparos[133] is True
    assert p.combos_67 == 2
    assert p.eliminacoes == 134


def test_levar_dano_zera_o_combo():
    p = Placar()
    for _ in range(60):
        p.registrar_eliminacao(1)
    p.zerar_combo()
    assert p.combo == 0
    assert not any(p.registrar_eliminacao(1) for _ in range(66))


def test_tempo_formatado_e_str():
    p = Placar()
    p.tempo = 125.7
    assert p.tempo_formatado == "02:05"
    assert "02:05" in str(p)


def test_pontuacao_final_premia_tempo_e_vitoria():
    p = Placar()
    p.adicionar_pontos(100)
    p.tempo = 60
    assert p.pontuacao_final(False) == 100 + 120
    assert p.pontuacao_final(True) == 100 + 120 + 5000


def test_registro_compara_por_pontos_e_desempata_pelo_tempo():
    a = RegistroRanking("Ana", "Aluno 1", 500, 300)
    b = RegistroRanking("Bia", "Aluno 2", 800, 300)
    c = RegistroRanking("Caio", "Aluno 1", 800, 200)
    assert a < b
    assert b < c
    assert sorted([c, a, b], reverse=True) == [c, b, a]


def test_registro_igualdade_e_texto():
    a = RegistroRanking("Ana", "Aluno 1", 500, 65)
    assert a == RegistroRanking("Ana", "Aluno 1", 500, 65)
    assert a != RegistroRanking("Ana", "Aluno 1", 501, 65)
    assert str(a) == "Ana (Aluno 1) - 500 pontos em 01:05"


def test_registro_nome_vazio_e_longo():
    assert RegistroRanking("   ", "Aluno 1", 1, 1).nome == "Anônimo"
    assert RegistroRanking("NomeMuitoGrandeDemais", "Aluno 1", 1, 1).nome == "NomeMuitoGra"


def test_ranking_guarda_os_10_melhores_e_persiste(tmp_path):
    arquivo = tmp_path / "ranking.json"
    r = Ranking(arquivo)
    for i in range(12):
        r.adicionar(RegistroRanking(f"J{i}", "Aluno 1", i * 10, 100))
    assert len(r.registros) == 10
    assert r.registros[0].pontos == 110
    assert r.adicionar(RegistroRanking("Ruim", "Aluno 1", 0, 100)) is None
    assert r.adicionar(RegistroRanking("Top", "Aluno 2", 999, 50)) == 1
    recarregado = Ranking(arquivo)
    assert [x.nome for x in recarregado.registros] == [x.nome for x in r.registros]


@pytest.mark.parametrize("conteudo", ["", "{quebrado", '{"a": 1}', '[{"nome": "x"}]'])
def test_ranking_corrompido_comeca_vazio(tmp_path, conteudo):
    arquivo = tmp_path / "ranking.json"
    arquivo.write_text(conteudo, encoding="utf-8")
    assert Ranking(arquivo).registros == []


def test_ranking_cria_pasta_ao_salvar(tmp_path):
    arquivo = tmp_path / "nova" / "ranking.json"
    r = Ranking(arquivo)
    r.adicionar(RegistroRanking("Ana", "Aluno 1", 10, 10))
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    assert dados[0]["nome"] == "Ana"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_placar_ranking.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.placar'`

- [ ] **Step 3: Implementar**

`jogo/placar.py`:
```python
"""Pontuação, eliminações, tempo de jogo e o combo 67."""
from jogo.config import COMBO_ESPECIAL


class Placar:
    PONTOS_POR_SEGUNDO = 2
    BONUS_VITORIA = 5000

    def __init__(self):
        self._pontos = 0
        self.eliminacoes = 0
        self.tempo = 0.0
        self.combo = 0
        self.combos_67 = 0

    @property
    def pontos(self):
        return self._pontos

    @pontos.setter
    def pontos(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("pontos devem ser um número inteiro")
        if valor < 0:
            raise ValueError("pontos não podem ser negativos")
        self._pontos = valor

    def adicionar_pontos(self, quantidade):
        if quantidade < 0:
            raise ValueError("não dá para ganhar pontos negativos")
        self.pontos = self._pontos + quantidade

    def registrar_eliminacao(self, pontos):
        """Conta uma eliminação. Retorna True quando o combo completa 67."""
        self.eliminacoes += 1
        self.adicionar_pontos(pontos)
        self.combo += 1
        if self.combo % COMBO_ESPECIAL == 0:
            self.combos_67 += 1
            return True
        return False

    def zerar_combo(self):
        self.combo = 0

    def pontuacao_final(self, venceu):
        total = self._pontos + int(self.tempo) * self.PONTOS_POR_SEGUNDO
        return total + (self.BONUS_VITORIA if venceu else 0)

    @property
    def tempo_formatado(self):
        minutos, segundos = divmod(int(self.tempo), 60)
        return f"{minutos:02d}:{segundos:02d}"

    def __str__(self):
        return f"{self._pontos} pontos | {self.eliminacoes} eliminações | {self.tempo_formatado}"
```

`jogo/ranking.py`:
```python
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
        except (OSError, ValueError, KeyError, TypeError):
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
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(json.dumps([r.para_dict() for r in self.registros], ensure_ascii=False, indent=2),
                                encoding="utf-8")
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Placar com combo 67 e ranking local

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Bases de armas, itens, especiais e bônus

**Files:**
- Create: `jogo/armas/__init__.py` (vazio), `jogo/armas/arma.py`, `jogo/itens/__init__.py` (vazio), `jogo/itens/item.py`, `jogo/jogador/__init__.py` (vazio), `jogo/jogador/especial.py`, `jogo/jogador/bonus.py`
- Test: `testes/test_bases.py`

**Interfaces:**
- Produces:
  - `Arma` (abstrata): atributos de classe `NOME`, `DESCRICAO`, `ICONE`, `NIVEL_MAXIMO = 7`, `ATRIBUTOS: dict[str, tuple]` (um valor por nível), `MELHORIAS: tuple[str]` (texto para subir do nível n para n+1, tamanho `NIVEL_MAXIMO - 1`); propriedade `nivel` (int de 1 a `NIVEL_MAXIMO`, senão `ValueError`/`TypeError`), `no_maximo`; `subir_nivel()`, `ao_subir_nivel()`, `valor(atributo)`, `descricao_proxima()`, abstrato `atualizar(dt, jogo, dono)`, `ao_remover(jogo)`, `encher()` (não faz nada), propriedade `fracao_cafe -> None`, `__str__`.
  - `ArmaDeDisparo(Arma)` (abstrata): `MUNICAO_BASE = 12`, `RECARGA_CAFE = 0.4` (por segundo), `PENALIDADE_SEM_CAFE = 3.0`; propriedades `municao` (≥ 0, corta no máximo), `municao_maxima`, `tem_cafe`, `fracao_cafe`; `encher()`; `atualizar(dt, jogo, dono)` concreto que chama o abstrato `disparar(jogo, dono) -> bool`.
  - `ArmaDeContato(Arma)` (abstrata, sem munição).
  - `Item` (abstrata): `NOME`, `DESCRICAO`, `ICONE`, `NIVEL_MAXIMO = 3`, `MELHORIAS` (tamanho 2); `nivel`, `no_maximo`, `subir_nivel()`, `descricao_proxima()`, abstrato `aplicar(jogador)`, `__str__`.
  - `Especial` (abstrata): `NOME`, `DESCRICAO`, `ICONE`, `RECARGA = 60.0`; `restante`, propriedades `pronto`, `progresso`; `atualizar(dt, mult_recarga=1.0)`, `usar(dono, jogo) -> bool`, abstrato `ativar(dono, jogo)`.
  - `BonusTemporario(nome, atributo, multiplicador, duracao)`: `restante`, `atualizar(dt)`, propriedade `ativo`.
- O `dono` das armas é um `Jogador` (Task 8) com `mult_cafe`, `mult_recarga`, `multiplicador_dano`, `posicao`, `direcao_mira`.

- [ ] **Step 1: Testes que falham**

`testes/test_bases.py`:
```python
from types import SimpleNamespace

import pytest

from jogo.armas.arma import Arma, ArmaDeContato, ArmaDeDisparo
from jogo.itens.item import Item
from jogo.jogador.bonus import BonusTemporario
from jogo.jogador.especial import Especial


class Estilingue(ArmaDeDisparo):
    NOME = "Estilingue"
    ATRIBUTOS = {"recarga": (1.0,) * 7}
    MELHORIAS = ("+",) * 6

    def __init__(self):
        super().__init__()
        self.disparos = 0

    def disparar(self, jogo, dono):
        self.disparos += 1
        return True


class Soco(ArmaDeContato):
    NOME = "Soco"
    MELHORIAS = ("a", "b", "c", "d", "e", "f")

    def atualizar(self, dt, jogo, dono):
        pass


class Amuleto(Item):
    NOME = "Amuleto"
    MELHORIAS = ("x", "y")

    def aplicar(self, jogador):
        jogador.sorte += self.nivel


class Grito(Especial):
    NOME = "Grito"
    RECARGA = 10.0

    def ativar(self, dono, jogo):
        dono.gritou = True


def dono_falso():
    return SimpleNamespace(mult_cafe=1.0, mult_recarga=1.0, multiplicador_dano=1.0)


def test_arma_e_abstrata():
    with pytest.raises(TypeError):
        Arma()
    with pytest.raises(TypeError):
        ArmaDeDisparo()


def test_nivel_da_arma_validado():
    s = Soco()
    assert s.nivel == 1
    with pytest.raises(ValueError):
        s.nivel = 0
    with pytest.raises(ValueError):
        s.nivel = 8
    with pytest.raises(TypeError):
        s.nivel = 2.0
    for _ in range(6):
        s.subir_nivel()
    assert s.no_maximo
    with pytest.raises(ValueError):
        s.subir_nivel()


def test_descricao_do_proximo_nivel_e_str():
    s = Soco()
    assert s.descricao_proxima() == "a"
    s.subir_nivel()
    assert s.descricao_proxima() == "b"
    assert str(s) == "Soco (nível 2)"
    assert s.fracao_cafe is None


def test_municao_validada():
    e = Estilingue()
    assert e.municao == e.municao_maxima == 12
    with pytest.raises(ValueError):
        e.municao = -1
    e.municao = 500
    assert e.municao == 12
    e.municao = 0
    assert not e.tem_cafe
    e.encher()
    assert e.municao == 12


def test_disparo_gasta_cafe_e_sem_cafe_atira_mais_devagar():
    e = Estilingue()
    dono = dono_falso()
    e.atualizar(0.0, None, dono)
    assert e.disparos == 1
    assert e.municao == 11
    e.municao = 0
    e.atualizar(1.0, None, dono)
    assert e.disparos == 2
    e.atualizar(1.5, None, dono)
    assert e.disparos == 2
    assert e.fracao_cafe == pytest.approx(e.municao / 12)


def test_item_nivel_ate_3_e_aplicar():
    a = Amuleto()
    jogador = SimpleNamespace(sorte=0)
    a.subir_nivel()
    a.subir_nivel()
    assert a.no_maximo
    with pytest.raises(ValueError):
        a.subir_nivel()
    a.aplicar(jogador)
    assert jogador.sorte == 3


def test_especial_recarga():
    g = Grito()
    dono = SimpleNamespace(gritou=False)
    assert g.pronto
    assert g.usar(dono, None) is True
    assert dono.gritou
    assert not g.pronto
    assert g.usar(dono, None) is False
    g.atualizar(5.0)
    assert g.progresso == pytest.approx(0.5)
    g.atualizar(2.5, mult_recarga=0.5)
    assert g.pronto


def test_bonus_temporario_expira():
    b = BonusTemporario("ssj", "dano", 2.0, 1.0)
    assert b.ativo
    b.atualizar(1.0)
    assert not b.ativo
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_bases.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.armas'`

- [ ] **Step 3: Implementar**

`jogo/armas/arma.py`:
```python
"""Bases das armas. O Jogador contém uma lista de Armas (composição)."""
from abc import ABC, abstractmethod
from numbers import Real


class Arma(ABC):
    NOME = "Arma"
    DESCRICAO = ""
    ICONE = ""
    NIVEL_MAXIMO = 7
    ATRIBUTOS = {}
    MELHORIAS = ()

    def __init__(self):
        self._nivel = 1

    @property
    def nivel(self):
        return self._nivel

    @nivel.setter
    def nivel(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("o nível deve ser um número inteiro")
        if not 1 <= valor <= self.NIVEL_MAXIMO:
            raise ValueError(f"o nível de {self.NOME} vai de 1 a {self.NIVEL_MAXIMO}")
        self._nivel = valor

    @property
    def no_maximo(self):
        return self._nivel >= self.NIVEL_MAXIMO

    def subir_nivel(self):
        self.nivel = self._nivel + 1
        self.ao_subir_nivel()

    def ao_subir_nivel(self):
        """Gancho para armas que precisam reagir à melhoria."""

    def valor(self, atributo):
        return self.ATRIBUTOS[atributo][self._nivel - 1]

    def descricao_proxima(self):
        return "" if self.no_maximo else self.MELHORIAS[self._nivel - 1]

    @abstractmethod
    def atualizar(self, dt, jogo, dono):
        """Avança a arma; é aqui que ela ataca."""

    def ao_remover(self, jogo):
        """Chamado quando a arma sai do jogador (por exemplo, virou colab)."""

    def encher(self):
        """Recarrega a munição. Armas sem munição não fazem nada."""

    @property
    def fracao_cafe(self):
        """Fração de café (0 a 1) para o HUD, ou None se a arma não usa café."""
        return None

    def __str__(self):
        return f"{self.NOME} (nível {self._nivel})"


class ArmaDeDisparo(Arma, ABC):
    """Arma que gasta café (munição) a cada disparo. O café recarrega sozinho."""

    MUNICAO_BASE = 12
    RECARGA_CAFE = 0.4
    PENALIDADE_SEM_CAFE = 3.0

    def __init__(self):
        super().__init__()
        self._mult_cafe = 1.0
        self._municao = float(self.MUNICAO_BASE)
        self._espera = 0.0

    @property
    def municao_maxima(self):
        return self.MUNICAO_BASE * self._mult_cafe

    @property
    def municao(self):
        return self._municao

    @municao.setter
    def municao(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, Real):
            raise TypeError("a munição deve ser um número")
        if valor < 0:
            raise ValueError("a munição não pode ser negativa")
        self._municao = min(float(valor), self.municao_maxima)

    @property
    def tem_cafe(self):
        return self._municao >= 1

    @property
    def fracao_cafe(self):
        return self._municao / self.municao_maxima

    def encher(self):
        self._municao = self.municao_maxima

    def atualizar(self, dt, jogo, dono):
        self._mult_cafe = dono.mult_cafe
        self.municao = min(self.municao_maxima, self._municao + self.RECARGA_CAFE * dono.mult_cafe * dt)
        self._espera -= dt
        if self._espera > 0:
            return
        com_cafe = self.tem_cafe
        if self.disparar(jogo, dono):
            if com_cafe:
                self.municao = self._municao - 1
            fator = 1.0 if com_cafe else self.PENALIDADE_SEM_CAFE
            self._espera = self.valor("recarga") * dono.mult_recarga * fator
        else:
            self._espera = 0.1

    @abstractmethod
    def disparar(self, jogo, dono):
        """Cria os projéteis. Retorna False se não havia em que atirar."""


class ArmaDeContato(Arma, ABC):
    """Arma que machuca encostando (ajudantes, veículos, golpes). Não usa café."""
```

`jogo/itens/item.py`:
```python
"""Base dos itens passivos."""
from abc import ABC, abstractmethod


class Item(ABC):
    NOME = "Item"
    DESCRICAO = ""
    ICONE = ""
    NIVEL_MAXIMO = 3
    MELHORIAS = ()

    def __init__(self):
        self._nivel = 1

    @property
    def nivel(self):
        return self._nivel

    @nivel.setter
    def nivel(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("o nível deve ser um número inteiro")
        if not 1 <= valor <= self.NIVEL_MAXIMO:
            raise ValueError(f"o nível de {self.NOME} vai de 1 a {self.NIVEL_MAXIMO}")
        self._nivel = valor

    @property
    def no_maximo(self):
        return self._nivel >= self.NIVEL_MAXIMO

    def subir_nivel(self):
        self.nivel = self._nivel + 1

    def descricao_proxima(self):
        return "" if self.no_maximo else self.MELHORIAS[self._nivel - 1]

    @abstractmethod
    def aplicar(self, jogador):
        """Soma o efeito deste item (no nível atual) aos atributos do jogador."""

    def __str__(self):
        return f"{self.NOME} (nível {self._nivel})"
```

`jogo/jogador/especial.py`:
```python
"""Base dos ataques especiais (tecla Espaço)."""
from abc import ABC, abstractmethod


class Especial(ABC):
    NOME = "Especial"
    DESCRICAO = ""
    ICONE = ""
    RECARGA = 60.0

    def __init__(self):
        self.restante = 0.0

    @property
    def pronto(self):
        return self.restante <= 0

    @property
    def progresso(self):
        return max(0.0, min(1.0, 1 - self.restante / self.RECARGA))

    def atualizar(self, dt, mult_recarga=1.0):
        self.restante = max(0.0, self.restante - dt / mult_recarga)

    def usar(self, dono, jogo):
        if not self.pronto:
            return False
        self.ativar(dono, jogo)
        self.restante = self.RECARGA
        return True

    @abstractmethod
    def ativar(self, dono, jogo):
        """Efeito do especial."""
```

`jogo/jogador/bonus.py`:
```python
"""Bônus que multiplicam um atributo por um tempo (Super Saiyajin, combo 67)."""


class BonusTemporario:
    def __init__(self, nome, atributo, multiplicador, duracao):
        self.nome = nome
        self.atributo = atributo
        self.multiplicador = multiplicador
        self.duracao = duracao
        self.restante = duracao

    def atualizar(self, dt):
        self.restante -= dt

    @property
    def ativo(self):
        return self.restante > 0
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Bases de armas (com munição de café), itens, especiais e bônus

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Efeitos, coletáveis, inimigo base, fábrica e Bug

**Files:**
- Create: `jogo/efeitos.py`, `jogo/coletaveis/__init__.py` (vazio), `jogo/coletaveis/coletaveis.py`, `jogo/inimigos/__init__.py`, `jogo/inimigos/fabrica.py`, `jogo/inimigos/inimigo.py`, `jogo/inimigos/bug.py`
- Test: `testes/test_inimigos_base.py`

**Interfaces:**
- Consumes: `Entidade`, `SerVivo`, `Colisao`, `Recursos`, `desenhar_sprite`, `Cor`, `DISTANCIA_REPOSICIONAR`.
- Produces:
  - `Efeito(posicao, duracao, raio=0)` (abstrata; `grupo = "efeito"`, `camada = 3`): `tempo`, `duracao`, propriedade `fracao`, gancho `ao_atualizar(dt, jogo)`; remove-se sozinho ao fim.
  - `TextoFlutuante(texto, posicao, cor=Cor.DANO, tamanho=16, duracao=0.7, subida=36)`, `FaiscaExplosao(posicao, raio=70, dano=10)` (fere o herói uma vez se ele estiver dentro).
  - `Coletavel(posicao, raio=12)` (abstrata; `grupo = "coletavel"`, `camada = 0`, `IMAGEM`, `ALTURA`, `MAGNETICO`): abstrato `ao_coletar(jogo)`. Concretos: `Nota(posicao, valor=1)` (atributo `valor`), `CopoDeCafe(posicao)`, `PocaoDeVida(posicao)` (cura 30), `Bau(posicao)`.
  - `FabricaDeInimigos`: `registrar(nome)` (decorador; nome repetido gera `ValueError`; grava `CHAVE` na classe), `classe(nome)`, `criar(nome, posicao, escala=1.0)`, `criar_gigante(nome, posicao, escala=1.0)`, `nomes()`; todos `@classmethod`; nome desconhecido gera `ValueError`.
  - `Inimigo(posicao, escala=1.0)` (abstrata; `grupo = "inimigo"`): atributos de classe `NOME, IMAGEM, ALTURA, RAIO, VIDA, VELOCIDADE, DANO, PONTOS, EXPERIENCIA, TAMANHO_GRUPO, CHANCE_CAFE, CHANCE_POCAO`; atributos `velocidade, tempo, possuido, olhando_esquerda, gigante, solta_bau, reposiciona, altura_sprite, empurrao`; abstrato `mover(dt, jogo)`; `desenhar_corpo(tela, camera)` (sobrescrevível); `ir_em_direcao(alvo, dt, velocidade=None)`, `tocar_jogador(jogo)`, `possuir(duracao)`, `empurrar(direcao, forca=180)`, `tornar_gigante()`, `ao_morrer(jogo)`, `balanco()`, propriedades `valor_em_pontos`, `valor_em_experiencia`.
  - `Bug` registrado como `"bug"`.
- O `jogo` usado aqui (Task 9) oferece: `jogador`, `fase.posicao_de_nascimento(jogo)`, `grade.proximos(pos, raio)`, `arena`, `rng`, `adicionar(e)`, `ferir_jogador(dano)`, `causar_dano(inimigo, dano, direcao=None, forte=False)`, `inimigo_mais_proximo(pos, raio_max, excluir=None)`, `soltar_nota(pos, valor)`, `dar_experiencia(q)`, `pedir_bau()`.

- [ ] **Step 1: Testes que falham**

`testes/test_inimigos_base.py`:
```python
from types import SimpleNamespace

import pygame
import pytest

from jogo.inimigos.bug import Bug
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


def test_inimigo_e_abstrato():
    with pytest.raises(TypeError):
        Inimigo((0, 0))


def test_fabrica_cria_bug_pelo_nome():
    bug = FabricaDeInimigos.criar("bug", (10, 20))
    assert isinstance(bug, Bug)
    assert bug.posicao == pygame.Vector2(10, 20)
    assert Bug.CHAVE == "bug"
    assert "bug" in FabricaDeInimigos.nomes()


def test_fabrica_recusa_nome_desconhecido():
    with pytest.raises(ValueError):
        FabricaDeInimigos.criar("dragao", (0, 0))


def test_registrar_inimigo_novo_sem_mexer_nas_classes(monkeypatch):
    monkeypatch.setattr(FabricaDeInimigos, "_registro", dict(FabricaDeInimigos._registro))

    @FabricaDeInimigos.registrar("bug_de_teste")
    class BugDeTeste(Bug):
        VIDA = 1

    assert isinstance(FabricaDeInimigos.criar("bug_de_teste", (0, 0)), BugDeTeste)
    with pytest.raises(ValueError):
        FabricaDeInimigos.registrar("bug_de_teste")(BugDeTeste)


def test_escala_aumenta_vida_e_um_pouco_a_velocidade():
    normal = Bug((0, 0))
    forte = Bug((0, 0), escala=3.0)
    assert forte.vida == pytest.approx(normal.vida * 3)
    assert forte.velocidade > normal.velocidade


def test_gigante_e_maior_mais_forte_e_solta_bau():
    g = FabricaDeInimigos.criar_gigante("bug", (0, 0))
    assert g.gigante and g.solta_bau and not g.reposiciona
    assert g.raio == Bug.RAIO * 3
    assert g.vida == Bug.VIDA * 30
    assert g.valor_em_pontos == Bug.PONTOS * 20


def test_bug_anda_em_direcao_ao_heroi():
    bug = Bug((0, 0))
    jogo = SimpleNamespace(jogador=SimpleNamespace(posicao=pygame.Vector2(100, 0)))
    bug.mover(0.1, jogo)
    assert bug.posicao.x == pytest.approx(Bug.VELOCIDADE * 0.1)
    assert bug.posicao.y == pytest.approx(0)
    assert not bug.olhando_esquerda
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_inimigos_base.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.inimigos'`

- [ ] **Step 3: Implementar os efeitos**

`jogo/efeitos.py`:
```python
"""Efeitos visuais de curta duração: números de dano, explosões, raios."""
import math
from abc import ABC

import pygame

from jogo.config import Cor
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Efeito(Entidade, ABC):
    grupo = "efeito"
    camada = 3

    def __init__(self, posicao, duracao, raio=0):
        super().__init__(posicao, raio)
        self.duracao = duracao
        self.tempo = 0.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.ao_atualizar(dt, jogo)
        if self.tempo >= self.duracao:
            self.remover()

    def ao_atualizar(self, dt, jogo):
        """Gancho para efeitos que interagem com o jogo enquanto duram."""

    @property
    def fracao(self):
        return min(1.0, self.tempo / self.duracao) if self.duracao > 0 else 1.0


class TextoFlutuante(Efeito):
    def __init__(self, texto, posicao, cor=Cor.DANO, tamanho=16, duracao=0.7, subida=36):
        super().__init__(posicao, duracao)
        self.subida = subida
        fonte = Recursos.fonte(tamanho)
        frente = fonte.render(texto, True, cor)
        contorno = fonte.render(texto, True, Cor.BORDA_ESCURA)
        self.imagem = pygame.Surface((frente.get_width() + 2, frente.get_height() + 2), pygame.SRCALPHA)
        for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
            self.imagem.blit(contorno, (dx, dy))
        self.imagem.blit(frente, (1, 1))

    def desenhar(self, tela, camera):
        p = camera.para_tela(self.posicao)
        p.y -= self.subida * self.fracao
        alfa = 255 if self.fracao < 0.6 else int(255 * (1 - self.fracao) / 0.4)
        self.imagem.set_alpha(alfa)
        tela.blit(self.imagem, self.imagem.get_rect(center=(round(p.x), round(p.y))))


class FaiscaExplosao(Efeito):
    """Explosão da Pilha AA: fere o herói uma vez se ele estiver perto."""

    def __init__(self, posicao, raio=70, dano=10):
        super().__init__(posicao, 0.35, raio)
        self.dano = dano
        self._feriu = False

    def ao_atualizar(self, dt, jogo):
        if not self._feriu:
            self._feriu = True
            if Colisao.circulos_colidem(self, jogo.jogador):
                jogo.ferir_jogador(self.dano)

    def desenhar(self, tela, camera):
        lado = int(self.raio * 2.4)
        sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
        centro = pygame.Vector2(lado / 2, lado / 2)
        r = self.raio * (0.4 + 0.6 * self.fracao)
        alfa = int(255 * (1 - self.fracao))
        pygame.draw.circle(sup, (255, 220, 80, alfa // 2), centro, int(r))
        pygame.draw.circle(sup, (255, 255, 200, alfa), centro, int(r), 3)
        for i in range(8):
            direcao = pygame.Vector2(1, 0).rotate(i * 45 + self.fracao * 60)
            pygame.draw.line(sup, (255, 240, 120, alfa), centro + direcao * r * 0.5, centro + direcao * r * 1.15, 3)
        c = camera.para_tela(self.posicao)
        tela.blit(sup, sup.get_rect(center=(round(c.x), round(c.y))))
```

- [ ] **Step 4: Implementar os coletáveis**

`jogo/coletaveis/coletaveis.py`:
```python
"""Coisas que o herói pega no chão: notas (experiência), café, poção e baú."""
import math
from abc import ABC, abstractmethod

from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Coletavel(Entidade, ABC):
    grupo = "coletavel"
    camada = 0
    IMAGEM = ""
    ALTURA = 24
    MAGNETICO = True
    VELOCIDADE_ATRACAO = 520

    def __init__(self, posicao, raio=12):
        super().__init__(posicao, raio)
        self.tempo = 0.0
        self.atraido = False

    def atualizar(self, dt, jogo):
        self.tempo += dt
        jogador = jogo.jogador
        if self.MAGNETICO and not self.atraido and \
                self.posicao.distance_to(jogador.posicao) <= jogador.alcance_coleta:
            self.atraido = True
        if self.atraido:
            falta = jogador.posicao - self.posicao
            if falta.length_squared() > 0:
                self.posicao += falta.normalize() * min(falta.length(), self.VELOCIDADE_ATRACAO * dt)
        if Colisao.circulos_colidem(self, jogador):
            self.ao_coletar(jogo)
            self.remover()

    @abstractmethod
    def ao_coletar(self, jogo):
        """Efeito de pegar o coletável."""

    def altura_desenho(self):
        return self.ALTURA

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.IMAGEM, self.altura_desenho())
        desenhar_sprite(tela, camera, imagem, self.posicao, deslocamento_y=3 + math.sin(self.tempo * 4) * 2)


class Nota(Coletavel):
    IMAGEM = "sprites/nota.png"
    ALTURA = 20

    def __init__(self, posicao, valor=1):
        super().__init__(posicao)
        self.valor = valor

    def ao_coletar(self, jogo):
        jogo.dar_experiencia(self.valor)
        Recursos.tocar("coleta", 0.2)

    def altura_desenho(self):
        return 26 if self.valor >= 5 else self.ALTURA


class CopoDeCafe(Coletavel):
    IMAGEM = "sprites/cafe.png"
    ALTURA = 30

    def ao_coletar(self, jogo):
        jogo.jogador.encher_cafe()
        jogo.adicionar(TextoFlutuante("CAFÉ!", self.posicao, Cor.CAFE, 18))
        Recursos.tocar("coleta", 0.4)


class PocaoDeVida(Coletavel):
    IMAGEM = "legado/itens/potion_hp_s.png"
    ALTURA = 30
    CURA = 30

    def ao_coletar(self, jogo):
        jogo.jogador.curar(self.CURA)
        jogo.adicionar(TextoFlutuante(f"+{self.CURA}", self.posicao, Cor.CURA, 18))
        Recursos.tocar("coleta", 0.4)


class Bau(Coletavel):
    IMAGEM = "legado/itens/chest_f0.png"
    ALTURA = 52
    MAGNETICO = False

    def __init__(self, posicao):
        super().__init__(posicao, raio=22)

    def ao_coletar(self, jogo):
        jogo.pedir_bau()
```

- [ ] **Step 5: Implementar a fábrica, o inimigo base e o Bug**

`jogo/inimigos/__init__.py`:
```python
"""Inimigos do jogo.

Todo módulo desta pasta é importado aqui, e cada inimigo se registra na
FabricaDeInimigos com o decorador @FabricaDeInimigos.registrar. Para criar
um inimigo novo basta um arquivo novo nesta pasta: nenhuma classe existente muda.
"""
import importlib
import pkgutil

for _modulo in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_modulo.name}")
```

`jogo/inimigos/fabrica.py`:
```python
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
```

`jogo/inimigos/inimigo.py`:
```python
"""Classe base abstrata dos inimigos."""
import math
from abc import ABC, abstractmethod

import pygame

from jogo.coletaveis.coletaveis import Bau, CopoDeCafe, PocaoDeVida
from jogo.config import DISTANCIA_REPOSICIONAR, Cor
from jogo.efeitos import TextoFlutuante
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.recursos import Recursos
from jogo.nucleo.ser_vivo import SerVivo


class Inimigo(SerVivo, ABC):
    grupo = "inimigo"
    camada = 1

    NOME = "Inimigo"
    IMAGEM = ""
    ALTURA = 40
    RAIO = 16
    VIDA = 10
    VELOCIDADE = 80
    DANO = 5
    PONTOS = 10
    EXPERIENCIA = 1
    TAMANHO_GRUPO = 1
    CHANCE_CAFE = 0.03
    CHANCE_POCAO = 0.006

    ESCALA_GIGANTE = 3
    VIDA_GIGANTE = 30
    PONTOS_GIGANTE = 20
    EXPERIENCIA_GIGANTE = 15

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, self.RAIO, self.VIDA * escala)
        self.escala = escala
        self.velocidade = self.VELOCIDADE * (1 + (escala - 1) * 0.08)
        self.tempo = 0.0
        self.possuido = 0.0
        self._espera_soco = 0.0
        self.empurrao = pygame.Vector2()
        self.olhando_esquerda = False
        self.gigante = False
        self.solta_bau = False
        self.reposiciona = True
        self.altura_sprite = self.ALTURA

    def tornar_gigante(self):
        self.gigante = True
        self.solta_bau = True
        self.reposiciona = False
        self.raio = self.RAIO * self.ESCALA_GIGANTE
        self.altura_sprite = self.ALTURA * self.ESCALA_GIGANTE
        self.vida_maxima = self.vida_maxima * self.VIDA_GIGANTE
        self.vida = self.vida_maxima

    @property
    def valor_em_pontos(self):
        return self.PONTOS * (self.PONTOS_GIGANTE if self.gigante else 1)

    @property
    def valor_em_experiencia(self):
        return self.EXPERIENCIA * (self.EXPERIENCIA_GIGANTE if self.gigante else 1)

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.piscar = max(0.0, self.piscar - dt)
        if self.reposiciona and \
                self.posicao.distance_squared_to(jogo.jogador.posicao) > DISTANCIA_REPOSICIONAR ** 2:
            self.posicao = jogo.fase.posicao_de_nascimento(jogo)
        if self.possuido > 0:
            self.possuido -= dt
            self._agir_possuido(dt, jogo)
        else:
            self.mover(dt, jogo)
            self.tocar_jogador(jogo)
        if self.empurrao.length_squared() > 1:
            self.posicao += self.empurrao * dt
            self.empurrao *= max(0.0, 1 - 8 * dt)
        self._separar(jogo)
        self.posicao.x = max(jogo.arena.left + self.raio, min(self.posicao.x, jogo.arena.right - self.raio))
        self.posicao.y = max(jogo.arena.top + self.raio, min(self.posicao.y, jogo.arena.bottom - self.raio))

    @abstractmethod
    def mover(self, dt, jogo):
        """Como este inimigo se desloca. Cada tipo tem o seu jeito."""

    def ir_em_direcao(self, alvo, dt, velocidade=None):
        falta = pygame.Vector2(alvo) - self.posicao
        if falta.length_squared() > 1:
            falta.normalize_ip()
            self.posicao += falta * (velocidade or self.velocidade) * dt
            if abs(falta.x) > 0.1:
                self.olhando_esquerda = falta.x < 0

    def tocar_jogador(self, jogo):
        if Colisao.circulos_colidem(self, jogo.jogador):
            jogo.ferir_jogador(self.DANO)

    def possuir(self, duracao):
        """Efeito do Fusca Azul: por um tempo, ataca outros inimigos."""
        self.possuido = max(self.possuido, duracao)

    def _agir_possuido(self, dt, jogo):
        self._espera_soco -= dt
        alvo = jogo.inimigo_mais_proximo(self.posicao, 400, excluir=self)
        if alvo is None:
            return
        self.ir_em_direcao(alvo.posicao, dt, self.velocidade * 1.4)
        if self._espera_soco <= 0 and Colisao.circulos_colidem(self, alvo):
            self._espera_soco = 0.5
            jogo.causar_dano(alvo, max(5, self.DANO * 2), alvo.posicao - self.posicao)
            jogo.adicionar(TextoFlutuante("POW!", alvo.posicao, Cor.DESTAQUE, 16))

    def empurrar(self, direcao, forca=180):
        direcao = pygame.Vector2(direcao)
        if direcao.length_squared() > 0:
            self.empurrao += direcao.normalize() * forca * (0.25 if self.gigante else 1)

    def _separar(self, jogo):
        for outro in jogo.grade.proximos(self.posicao, self.raio * 2)[:8]:
            if outro is self:
                continue
            afastar = self.posicao - outro.posicao
            soma = self.raio + outro.raio
            distancia2 = afastar.length_squared()
            if 0 < distancia2 < soma * soma:
                distancia = math.sqrt(distancia2)
                self.posicao += afastar / distancia * (soma - distancia) * 0.25

    def ao_morrer(self, jogo):
        """O que acontece quando morre. Por padrão solta nota e, às vezes, café ou poção."""
        jogo.soltar_nota(self.posicao, self.valor_em_experiencia)
        sorte = jogo.rng.random()
        if sorte < self.CHANCE_POCAO:
            jogo.adicionar(PocaoDeVida(self.posicao + (10, 0)))
        elif sorte < self.CHANCE_POCAO + self.CHANCE_CAFE:
            jogo.adicionar(CopoDeCafe(self.posicao + (10, 0)))
        if self.solta_bau:
            jogo.adicionar(Bau(self.posicao))

    def balanco(self):
        return abs(math.sin(self.tempo * 9)) * 3

    def desenhar(self, tela, camera):
        self.desenhar_corpo(tela, camera)
        if self.possuido > 0:
            self._desenhar_possessao(tela, camera)

    def desenhar_corpo(self, tela, camera):
        """Desenha o sprite. Inimigos com visual especial sobrescrevem só isto."""
        imagem = Recursos.imagem(self.IMAGEM, int(self.altura_sprite))
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda,
                        piscar=self.piscar > 0, deslocamento_y=self.balanco())

    def _desenhar_possessao(self, tela, camera):
        p = camera.para_tela(self.posicao)
        topo = (round(p.x), round(p.y - self.altura_sprite / 2 - 14))
        pygame.draw.circle(tela, (40, 110, 230), topo, 9)
        marca = Recursos.fonte(14).render("!", True, Cor.TEXTO)
        tela.blit(marca, marca.get_rect(center=topo))
```

`jogo/inimigos/bug.py`:
```python
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("bug")
class Bug(Inimigo):
    """Besourinho verde de olhos esbugalhados. Rápido, fraco, vem em bando."""

    NOME = "Bug"
    IMAGEM = "sprites/bug.png"
    ALTURA = 30
    RAIO = 12
    VIDA = 6
    VELOCIDADE = 125
    DANO = 4
    PONTOS = 5
    TAMANHO_GRUPO = 6

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)
```

- [ ] **Step 6: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "Efeitos, coletáveis, inimigo base, fábrica de inimigos e Bug

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Projéteis, ajudantes, Cobra Python e Caramelo

**Files:**
- Create: `jogo/projeteis/__init__.py` (vazio), `jogo/projeteis/projeteis.py`, `jogo/ajudantes/__init__.py` (vazio), `jogo/ajudantes/ajudantes.py`, `jogo/armas/cobra_python.py`, `jogo/armas/caramelo.py`
- Test: `testes/test_armas_iniciais.py`

**Interfaces:**
- Consumes: `ArmaDeDisparo`, `ArmaDeContato`, `Entidade`, `Colisao`, `Recursos`, `desenhar_sprite`.
- Produces:
  - `Projetil(posicao, velocidade, dano, raio=10)` (abstrata; `grupo = "projetil"`, `camada = 2`, `IMAGEM`, `ALTURA`, `DURACAO = 2.0`): `velocidade: Vector2`, `dano`, `tempo`; `mover(dt)`, abstrato `verificar_colisao(jogo)`, `angulo_desenho()`.
  - `ProjetilDoHeroi(posicao, velocidade, dano, perfuracao=1, raio=10, atingidos=None)`: acerta inimigos via `jogo.inimigos_proximos` e `jogo.causar_dano`; gancho `ao_acertar(inimigo, jogo)`; atributos `perfuracao`, `atingidos: set[int]` (ids).
  - `ProjetilDivisivel(..., geracoes=1, ...)`: ao acertar, cria duas cópias do próprio tipo, desviadas ±35°, com 70% do dano e `geracoes - 1`.
  - `ProjetilInimigo(posicao, velocidade, dano, raio=10)`: fere o herói com `jogo.ferir_jogador`.
  - `MovimentoSerpente` (mixin com `mover(dt)` ondulado), `CobraProjetil(MovimentoSerpente, ProjetilDoHeroi)`.
  - `Ajudante` (abstrata; `grupo = "ajudante"`, `camada = 2`); `CachorroCaramelo(dono, angulo, arma)`.
  - `CobraPython(ArmaDeDisparo)`, `Caramelo(ArmaDeContato)` com `cachorros` (lista).

- [ ] **Step 1: Testes que falham**

`testes/test_armas_iniciais.py`:
```python
from types import SimpleNamespace

import pygame
import pytest

from jogo.armas.caramelo import Caramelo
from jogo.armas.cobra_python import CobraPython
from jogo.projeteis.projeteis import CobraProjetil, ProjetilDivisivel


class JogoFalso:
    def __init__(self):
        self.adicionados = []

    def adicionar(self, entidade):
        self.adicionados.append(entidade)


def dono_falso():
    return SimpleNamespace(posicao=pygame.Vector2(100, 100), direcao_mira=pygame.Vector2(1, 0),
                           multiplicador_dano=1.0, mult_cafe=1.0, mult_recarga=1.0)


@pytest.mark.parametrize("classe", [CobraPython, Caramelo])
def test_tabelas_de_atributos_tem_um_valor_por_nivel(classe):
    for valores in classe.ATRIBUTOS.values():
        assert len(valores) == classe.NIVEL_MAXIMO
    assert len(classe.MELHORIAS) == classe.NIVEL_MAXIMO - 1


def test_cobra_dispara_mais_cobras_nos_niveis_altos():
    jogo, dono = JogoFalso(), dono_falso()
    arma = CobraPython()
    assert arma.disparar(jogo, dono)
    assert len(jogo.adicionados) == 1
    for _ in range(2):
        arma.subir_nivel()
    jogo.adicionados.clear()
    arma.disparar(jogo, dono)
    assert len(jogo.adicionados) == 2
    assert all(isinstance(c, CobraProjetil) for c in jogo.adicionados)
    assert jogo.adicionados[0].dano == arma.valor("dano")


def test_cobra_avanca_ondulando():
    cobra = CobraProjetil((0, 0), (400, 0), 10)
    ys = []
    for _ in range(20):
        cobra.tempo += 0.02
        cobra.mover(0.02)
        ys.append(cobra.posicao.y)
    assert cobra.posicao.x == pytest.approx(160, abs=1)
    assert max(ys) > 5 and min(ys) < -5


def test_projetil_divisivel_cria_duas_metades():
    class Estrelinha(ProjetilDivisivel):
        pass

    jogo = JogoFalso()
    p = Estrelinha((0, 0), (300, 0), 10, geracoes=1)
    p.ao_acertar(None, jogo)
    assert len(jogo.adicionados) == 2
    assert all(f.geracoes == 0 and f.dano == pytest.approx(7) for f in jogo.adicionados)
    jogo.adicionados.clear()
    jogo.adicionados[:] = []
    filho = Estrelinha((0, 0), (300, 0), 10, geracoes=0)
    filho.ao_acertar(None, jogo)
    assert jogo.adicionados == []


def test_caramelo_cria_e_recria_cachorros_conforme_o_nivel():
    jogo, dono = JogoFalso(), dono_falso()
    arma = Caramelo()
    arma.atualizar(0.016, jogo, dono)
    assert len(arma.cachorros) == 1
    arma.subir_nivel()
    arma.atualizar(0.016, jogo, dono)
    assert len(arma.cachorros) == 2
    assert sum(c.ativo for c in jogo.adicionados) == 2
    arma.ao_remover(jogo)
    assert not any(c.ativo for c in jogo.adicionados)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_armas_iniciais.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.armas.caramelo'`

- [ ] **Step 3: Implementar os projéteis**

`jogo/projeteis/projeteis.py`:
```python
"""Projéteis do herói e dos inimigos."""
import math
from abc import ABC, abstractmethod

import pygame

from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Projetil(Entidade, ABC):
    grupo = "projetil"
    camada = 2
    IMAGEM = ""
    ALTURA = 24
    DURACAO = 2.0

    def __init__(self, posicao, velocidade, dano, raio=10):
        super().__init__(posicao, raio)
        self.velocidade = pygame.Vector2(velocidade)
        self.dano = dano
        self.tempo = 0.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.tempo >= self.DURACAO or not jogo.arena.collidepoint(self.posicao):
            self.remover()
            return
        self.mover(dt)
        self.verificar_colisao(jogo)

    def mover(self, dt):
        self.posicao += self.velocidade * dt

    @abstractmethod
    def verificar_colisao(self, jogo):
        """Testa se acertou alguém e aplica o dano."""

    def angulo_desenho(self):
        return -math.degrees(math.atan2(self.velocidade.y, self.velocidade.x))

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.IMAGEM, self.ALTURA)
        desenhar_sprite(tela, camera, imagem, self.posicao, angulo=self.angulo_desenho(), sombra=False)


class ProjetilDoHeroi(Projetil):
    def __init__(self, posicao, velocidade, dano, perfuracao=1, raio=10, atingidos=None):
        super().__init__(posicao, velocidade, dano, raio)
        self.perfuracao = perfuracao
        self.atingidos = set(atingidos or ())

    def verificar_colisao(self, jogo):
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if id(inimigo) in self.atingidos:
                continue
            self.atingidos.add(id(inimigo))
            jogo.causar_dano(inimigo, self.dano, self.velocidade)
            self.ao_acertar(inimigo, jogo)
            self.perfuracao -= 1
            if self.perfuracao <= 0:
                self.remover()
                return

    def ao_acertar(self, inimigo, jogo):
        """Gancho para projéteis com efeito extra ao acertar."""


class ProjetilDivisivel(ProjetilDoHeroi):
    """Ao acertar, se divide em duas cópias de si mesmo (Gemini, Cobras Gêmeas)."""

    DESVIO = 35
    FATOR_DANO = 0.7

    def __init__(self, posicao, velocidade, dano, geracoes=1, perfuracao=1, raio=10, atingidos=None):
        super().__init__(posicao, velocidade, dano, perfuracao, raio, atingidos)
        self.geracoes = geracoes

    def ao_acertar(self, inimigo, jogo):
        if self.geracoes <= 0:
            return
        for desvio in (-self.DESVIO, self.DESVIO):
            jogo.adicionar(type(self)(self.posicao, self.velocidade.rotate(desvio), self.dano * self.FATOR_DANO,
                                      geracoes=self.geracoes - 1, raio=self.raio, atingidos=self.atingidos))


class ProjetilInimigo(Projetil):
    def verificar_colisao(self, jogo):
        if Colisao.circulos_colidem(self, jogo.jogador):
            jogo.ferir_jogador(self.dano)
            self.remover()


class MovimentoSerpente:
    """Mixin: avança ondulando para os lados, como uma cobra."""

    AMPLITUDE = 14
    FREQUENCIA = 12

    def mover(self, dt):
        if not hasattr(self, "_base"):
            self._base = pygame.Vector2(self.posicao)
        self._base += self.velocidade * dt
        lado = pygame.Vector2(-self.velocidade.y, self.velocidade.x)
        if lado.length_squared() > 0:
            lado.scale_to_length(math.sin(self.tempo * self.FREQUENCIA) * self.AMPLITUDE)
        self.posicao = self._base + lado


class CobraProjetil(MovimentoSerpente, ProjetilDoHeroi):
    IMAGEM = "sprites/cobra.png"
    ALTURA = 22
    DURACAO = 1.6
```

Nota: `scale_to_length(0)` é permitido; o `if` só evita vetor nulo.

- [ ] **Step 4: Implementar ajudantes e as duas armas**

`jogo/ajudantes/ajudantes.py`:
```python
"""Ajudantes: coisas que as armas colocam na arena (cachorro, fusca, mascotes)."""
import math
from abc import ABC

import pygame

from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Ajudante(Entidade, ABC):
    grupo = "ajudante"
    camada = 2


class CachorroCaramelo(Ajudante):
    """Vira-lata caramelo que corre em volta do herói e morde quem encosta."""

    IMAGEM = "sprites/caramelo.png"
    ALTURA = 40
    ESPERA_MORDIDA = 0.5

    def __init__(self, dono, angulo, arma):
        super().__init__(dono.posicao, 18)
        self.dono = dono
        self.angulo = angulo
        self.arma = arma
        self.tempo = 0.0
        self.olhando_esquerda = False
        self._mordidos = {}

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.angulo += self.arma.valor("velocidade") * dt
        raio = self.arma.valor("raio")
        nova = self.dono.posicao + pygame.Vector2(math.cos(self.angulo), math.sin(self.angulo)) * raio
        if abs(nova.x - self.posicao.x) > 0.5:
            self.olhando_esquerda = nova.x < self.posicao.x
        self.posicao = nova
        for chave in list(self._mordidos):
            self._mordidos[chave] -= dt
            if self._mordidos[chave] <= 0:
                del self._mordidos[chave]
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if id(inimigo) in self._mordidos:
                continue
            self._mordidos[id(inimigo)] = self.ESPERA_MORDIDA
            jogo.causar_dano(inimigo, self.arma.valor("dano") * self.dono.multiplicador_dano,
                             inimigo.posicao - self.dono.posicao)

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.IMAGEM, self.ALTURA)
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda,
                        deslocamento_y=abs(math.sin(self.tempo * 14)) * 4)
```

`jogo/armas/cobra_python.py`:
```python
from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import CobraProjetil


class CobraPython(ArmaDeDisparo):
    NOME = "Cobra Python"
    ICONE = "sprites/cobra.png"
    DESCRICAO = "Dispara cobrinhas que avançam serpenteando na direção da mira."
    ATRIBUTOS = {
        "dano": (10, 12, 14, 14, 17, 17, 22),
        "quantidade": (1, 1, 2, 2, 3, 3, 4),
        "perfuracao": (1, 2, 2, 3, 3, 4, 5),
        "recarga": (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.65),
    }
    MELHORIAS = (
        "Atravessa mais 1 inimigo.",
        "Mais 1 cobra por disparo.",
        "Atravessa mais 1 inimigo.",
        "Mais 1 cobra e mais dano.",
        "Atravessa mais 1 inimigo.",
        "Mais 1 cobra, mais dano e recarga menor.",
    )
    VELOCIDADE = 430
    ABERTURA = 12

    def disparar(self, jogo, dono):
        quantidade = self.valor("quantidade")
        dano = self.valor("dano") * dono.multiplicador_dano
        for i in range(quantidade):
            direcao = dono.direcao_mira.rotate((i - (quantidade - 1) / 2) * self.ABERTURA)
            jogo.adicionar(CobraProjetil(dono.posicao, direcao * self.VELOCIDADE, dano,
                                         perfuracao=self.valor("perfuracao")))
        Recursos.tocar("disparo", 0.15)
        return True
```

`jogo/armas/caramelo.py`:
```python
import math

from jogo.ajudantes.ajudantes import CachorroCaramelo
from jogo.armas.arma import ArmaDeContato


class Caramelo(ArmaDeContato):
    NOME = "Caramelo"
    ICONE = "sprites/caramelo.png"
    DESCRICAO = "Um vira-lata caramelo corre em volta de você e morde quem chega perto."
    ATRIBUTOS = {
        "quantidade": (1, 2, 2, 3, 3, 4, 4),
        "dano": (7, 8, 9, 10, 12, 13, 16),
        "raio": (70, 75, 80, 90, 95, 100, 115),
        "velocidade": (3.0, 3.0, 3.4, 3.4, 3.8, 3.8, 4.3),
    }
    MELHORIAS = (
        "Mais 1 caramelo.",
        "Voltas mais rápidas e mais dano.",
        "Mais 1 caramelo.",
        "Voltas mais rápidas e maiores.",
        "Mais 1 caramelo.",
        "Mais dano, voltas maiores e mais rápidas.",
    )

    def __init__(self):
        super().__init__()
        self.cachorros = []

    def atualizar(self, dt, jogo, dono):
        if len(self.cachorros) != self.valor("quantidade"):
            self._recriar(jogo, dono)

    def _recriar(self, jogo, dono):
        self.ao_remover(jogo)
        quantidade = self.valor("quantidade")
        self.cachorros = [CachorroCaramelo(dono, 2 * math.pi * i / quantidade, self) for i in range(quantidade)]
        for cachorro in self.cachorros:
            jogo.adicionar(cachorro)

    def ao_remover(self, jogo):
        for cachorro in self.cachorros:
            cachorro.remover()
        self.cachorros = []
```

- [ ] **Step 5: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Projéteis, ajudantes e as armas iniciais Cobra Python e Caramelo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Jogador, alunos e especiais

**Files:**
- Create: `jogo/jogador/jogador.py`, `jogo/jogador/alunos.py`, `jogo/jogador/especiais.py`
- Modify: `jogo/efeitos.py` (acrescentar `AuraSSJ` e `RaioZoltraak` no fim)
- Test: `testes/test_jogador.py`

**Interfaces:**
- Consumes: `SerVivo`, `Arma`, `Especial`, `BonusTemporario`, `CobraPython`, `Caramelo`, `Recursos`, `desenhar_sprite`, `INVENCIBILIDADE_APOS_DANO`.
- Produces:
  - `Jogador(posicao)` (abstrata; `grupo = "jogador"`): atributos de classe `NOME, DESCRICAO, VIDA, VELOCIDADE, IMAGEM, IMAGEM_TRANSFORMADO, ALTURA, RAIO, MAX_ARMAS = 6, MAX_ITENS = 6, ALCANCE_COLETA_BASE = 90`; atributos `armas, itens, bonus, especial, direcao_mira, movendo, olhando_esquerda, invencivel, nivel, experiencia, armas_em_colab (set de classes)`, modificadores `mult_dano, mult_velocidade, mult_recarga, mult_cafe, regeneracao, alcance_coleta, vida_maxima_extra`; abstratos `criar_arma_inicial()`, `criar_especial()`; `recalcular_atributos()`, `multiplicador(atributo)`, propriedades `velocidade`, `multiplicador_dano`, `experiencia_necessaria`, `pode_levar_dano`; `tem_bonus(nome)`, `adicionar_bonus(b)`, `adicionar_arma(a)`, `remover_arma(a, jogo)`, `adicionar_item(i)`, `subir_nivel_item(i)`, `encher_cafe()`, `ganhar_experiencia(q) -> int` (níveis ganhos), `usar_especial(jogo) -> bool`.
  - `AlunoAgil`, `AlunoResistente`, `HEROIS = (AlunoAgil, AlunoResistente)`.
  - `Zoltraak`, `SuperSaiyajin` (especiais).
  - `AuraSSJ(dono, duracao)`, `RaioZoltraak(dono, dano, duracao=1.5)` (efeitos).
- O `jogo` usado em `Jogador.atualizar` oferece `entrada.direcao: Vector2`, `entrada.mira: Vector2 | None` (posição no mundo) e `arena`.

- [ ] **Step 1: Testes que falham**

`testes/test_jogador.py`:
```python
from types import SimpleNamespace

import pygame
import pytest

from jogo.armas.caramelo import Caramelo
from jogo.armas.cobra_python import CobraPython
from jogo.itens.item import Item
from jogo.jogador.alunos import HEROIS, AlunoAgil, AlunoResistente
from jogo.jogador.bonus import BonusTemporario
from jogo.jogador.especiais import SuperSaiyajin, Zoltraak
from jogo.jogador.jogador import Jogador


class Turbo(Item):
    NOME = "Turbo"
    MELHORIAS = ("a", "b")

    def aplicar(self, jogador):
        jogador.mult_velocidade += 0.5 * self.nivel
        jogador.vida_maxima_extra += 10 * self.nivel


class JogoFalso:
    def __init__(self, direcao=(0, 0), mira=None):
        self.entrada = SimpleNamespace(direcao=pygame.Vector2(direcao), mira=mira)
        self.arena = pygame.Rect(0, 0, 3200, 1800)
        self.adicionados = []

    def adicionar(self, e):
        self.adicionados.append(e)


def test_jogador_e_abstrato():
    with pytest.raises(TypeError):
        Jogador((0, 0))


def test_herois_comecam_com_arma_e_especial_proprios():
    agil, forte = AlunoAgil((0, 0)), AlunoResistente((0, 0))
    assert isinstance(agil.armas[0], CobraPython) and isinstance(agil.especial, Zoltraak)
    assert isinstance(forte.armas[0], Caramelo) and isinstance(forte.especial, SuperSaiyajin)
    assert agil.vida == 80 and forte.vida == 130
    assert agil.velocidade > forte.velocidade
    assert HEROIS == (AlunoAgil, AlunoResistente)


def test_movimento_normalizado_e_preso_na_arena():
    j = AlunoAgil((100, 100))
    j.atualizar(0.1, JogoFalso(direcao=(1, 1)))
    andou = j.posicao - pygame.Vector2(100, 100)
    assert andou.length() == pytest.approx(j.velocidade * 0.1)
    j.posicao.update(5, 5)
    j.atualizar(0.1, JogoFalso(direcao=(-1, -1)))
    assert j.posicao.x >= j.raio and j.posicao.y >= j.raio


def test_mira_segue_movimento_ou_mouse():
    j = AlunoAgil((100, 100))
    j.atualizar(0.01, JogoFalso(direcao=(0, -1)))
    assert j.direcao_mira == pygame.Vector2(0, -1)
    j.atualizar(0.01, JogoFalso(mira=pygame.Vector2(100, 300)))
    assert j.direcao_mira.y == pytest.approx(1)


def test_experiencia_sobe_varios_niveis_de_uma_vez():
    j = AlunoAgil((0, 0))
    necessario = j.experiencia_necessaria
    assert j.ganhar_experiencia(necessario - 1) == 0
    ganhos = j.ganhar_experiencia(500)
    assert ganhos > 1
    assert j.nivel == 1 + ganhos
    assert 0 <= j.experiencia < j.experiencia_necessaria
    with pytest.raises(ValueError):
        j.ganhar_experiencia(-1)


def test_invencibilidade_depois_de_dano():
    j = AlunoAgil((0, 0))
    j.receber_dano(10)
    assert not j.pode_levar_dano
    j.atualizar(0.6, JogoFalso())
    assert j.pode_levar_dano


def test_bonus_multiplicam_e_expiram():
    j = AlunoAgil((0, 0))
    base = j.velocidade
    j.adicionar_bonus(BonusTemporario("combo67", "velocidade", 1.5, 1.0))
    j.adicionar_bonus(BonusTemporario("combo67", "velocidade", 1.5, 1.0))
    assert j.velocidade == pytest.approx(base * 1.5)
    j.atualizar(1.1, JogoFalso())
    assert j.velocidade == pytest.approx(base)


def test_itens_recalculam_atributos_e_curam_a_vida_ganha():
    j = AlunoAgil((0, 0))
    base = j.velocidade
    item = Turbo()
    j.adicionar_item(item)
    assert j.velocidade == pytest.approx(base * 1.5)
    assert j.vida_maxima == 90 and j.vida == 90
    j.subir_nivel_item(item)
    assert j.velocidade == pytest.approx(base * 2.0)
    assert j.vida_maxima == 100


def test_limites_de_armas_e_itens():
    j = AlunoAgil((0, 0))
    for _ in range(5):
        j.adicionar_arma(Caramelo())
    with pytest.raises(ValueError):
        j.adicionar_arma(Caramelo())
    for _ in range(6):
        j.adicionar_item(Turbo())
    with pytest.raises(ValueError):
        j.adicionar_item(Turbo())


def test_super_saiyajin_dobra_o_dano_e_cria_aura():
    j = AlunoResistente((0, 0))
    jogo = JogoFalso()
    assert j.usar_especial(jogo)
    assert j.tem_bonus("ssj")
    assert j.multiplicador_dano == pytest.approx(2.0)
    assert len(jogo.adicionados) == 1
    assert not j.usar_especial(jogo)


def test_zoltraak_cria_raio():
    j = AlunoAgil((0, 0))
    jogo = JogoFalso()
    assert j.usar_especial(jogo)
    assert type(jogo.adicionados[0]).__name__ == "RaioZoltraak"


def test_encher_cafe_so_afeta_armas_de_disparo():
    j = AlunoAgil((0, 0))
    j.adicionar_arma(Caramelo())
    j.armas[0].municao = 0
    j.encher_cafe()
    assert j.armas[0].municao == j.armas[0].municao_maxima
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_jogador.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.jogador.alunos'`

- [ ] **Step 3: Acrescentar os efeitos dos especiais ao fim de `jogo/efeitos.py`**

```python
class AuraSSJ(Efeito):
    """Aura dourada do Super Saiyajin, desenhada logo atrás do herói."""

    camada = 1

    def __init__(self, dono, duracao):
        super().__init__(dono.posicao, duracao)
        self.dono = dono

    def ao_atualizar(self, dt, jogo):
        self.posicao = self.dono.posicao - pygame.Vector2(0, 0.5)

    def desenhar(self, tela, camera):
        c = camera.para_tela(self.dono.posicao)
        largura, altura = 70, 96
        sup = pygame.Surface((largura + 20, altura + 30), pygame.SRCALPHA)
        base = pygame.Vector2(sup.get_width() / 2, sup.get_height() - 6)
        brilho = 0.85 + 0.15 * math.sin(self.tempo * 25)
        pygame.draw.ellipse(sup, (255, 210, 60, int(70 * brilho)), (10, 20, largura, altura))
        for i in range(7):
            x = 14 + i * (largura - 8) / 6
            topo = 8 + 10 * (1 + math.sin(self.tempo * 18 + i * 1.7))
            pygame.draw.polygon(sup, (255, 236, 120, int(110 * brilho)),
                                [(x - 7, base.y - 20), (x, topo), (x + 7, base.y - 20)])
        tela.blit(sup, sup.get_rect(midbottom=(round(c.x), round(c.y + 34))))


class RaioZoltraak(Efeito):
    """Raio mágico que sai do herói na direção da mira e atravessa tudo."""

    COMPRIMENTO = 950
    LARGURA = 70
    INTERVALO = 0.1

    def __init__(self, dono, dano, duracao=1.5):
        super().__init__(dono.posicao, duracao)
        self.dono = dono
        self.dano = dano
        self.direcao = pygame.Vector2(dono.direcao_mira)
        self._espera = 0.0

    def ao_atualizar(self, dt, jogo):
        self.posicao = pygame.Vector2(self.dono.posicao)
        self.direcao = pygame.Vector2(self.dono.direcao_mira)
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.INTERVALO
        fim = self.posicao + self.direcao * self.COMPRIMENTO
        meio = (self.posicao + fim) / 2
        for inimigo in jogo.inimigos_proximos(meio, self.COMPRIMENTO / 2 + self.LARGURA):
            if Colisao.segmento_acerta_circulo(self.posicao, fim, self.LARGURA, inimigo.posicao, inimigo.raio):
                jogo.causar_dano(inimigo, self.dano, self.direcao)

    def desenhar(self, tela, camera):
        inicio = camera.para_tela(self.posicao)
        fim = inicio + self.direcao * self.COMPRIMENTO
        sumindo = 1.0 if self.fracao < 0.85 else (1 - self.fracao) / 0.15
        largura = self.LARGURA * (1 + 0.12 * math.sin(self.tempo * 40)) * sumindo
        for cor, fator in (((140, 80, 255), 1.0), ((210, 190, 255), 0.55), ((255, 255, 255), 0.25)):
            espessura = max(1, int(largura * fator))
            pygame.draw.line(tela, cor, inicio, fim, espessura)
            pygame.draw.circle(tela, cor, inicio, espessura // 2 + 4)
```

- [ ] **Step 4: Implementar especiais, jogador e alunos**

`jogo/jogador/especiais.py`:
```python
from jogo.efeitos import AuraSSJ, RaioZoltraak
from jogo.jogador.bonus import BonusTemporario
from jogo.jogador.especial import Especial
from jogo.nucleo.recursos import Recursos


class Zoltraak(Especial):
    NOME = "Zoltraak"
    DESCRICAO = "Um raio mágico enorme na direção da mira, que atravessa tudo."
    ICONE = "icones/zoltraak.png"
    DANO_POR_TOQUE = 18

    def ativar(self, dono, jogo):
        jogo.adicionar(RaioZoltraak(dono, self.DANO_POR_TOQUE * dono.multiplicador_dano))
        Recursos.tocar("especial", 0.6)


class SuperSaiyajin(Especial):
    NOME = "Super Saiyajin"
    DESCRICAO = "Cabelo dourado por 10 s: dano em dobro e mais velocidade."
    ICONE = "icones/ssj.png"
    DURACAO = 10.0

    def ativar(self, dono, jogo):
        dono.adicionar_bonus(BonusTemporario("ssj", "dano", 2.0, self.DURACAO))
        dono.adicionar_bonus(BonusTemporario("ssj_velocidade", "velocidade", 1.4, self.DURACAO))
        jogo.adicionar(AuraSSJ(dono, self.DURACAO))
        Recursos.tocar("especial", 0.6)
```

`jogo/jogador/jogador.py`:
```python
"""O herói controlado pelo jogador."""
import math
from abc import ABC, abstractmethod

import pygame

from jogo.config import INVENCIBILIDADE_APOS_DANO
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.recursos import Recursos
from jogo.nucleo.ser_vivo import SerVivo


class Jogador(SerVivo, ABC):
    grupo = "jogador"
    camada = 1

    NOME = "Jogador"
    DESCRICAO = ""
    VIDA = 100
    VELOCIDADE = 200
    IMAGEM = ""
    IMAGEM_TRANSFORMADO = None
    ALTURA = 64
    RAIO = 18
    MAX_ARMAS = 6
    MAX_ITENS = 6
    ALCANCE_COLETA_BASE = 90

    def __init__(self, posicao):
        super().__init__(posicao, self.RAIO, self.VIDA)
        self.armas = []
        self.itens = []
        self.bonus = []
        self.armas_em_colab = set()
        self.direcao_mira = pygame.Vector2(1, 0)
        self.movendo = False
        self.olhando_esquerda = False
        self.invencivel = 0.0
        self.tempo = 0.0
        self.nivel = 1
        self.experiencia = 0
        self._redefinir_atributos()
        self.especial = self.criar_especial()
        self.adicionar_arma(self.criar_arma_inicial())

    @abstractmethod
    def criar_arma_inicial(self):
        """Arma com que este herói começa."""

    @abstractmethod
    def criar_especial(self):
        """Especial (tecla Espaço) deste herói."""

    def _redefinir_atributos(self):
        self.mult_dano = 1.0
        self.mult_velocidade = 1.0
        self.mult_recarga = 1.0
        self.mult_cafe = 1.0
        self.regeneracao = 0.0
        self.alcance_coleta = self.ALCANCE_COLETA_BASE
        self.vida_maxima_extra = 0

    def recalcular_atributos(self):
        """Zera os modificadores e deixa cada item aplicar o seu (polimorfismo)."""
        maxima_antes = self.vida_maxima
        self._redefinir_atributos()
        for item in self.itens:
            item.aplicar(self)
        self.vida_maxima = self.VIDA + self.vida_maxima_extra
        if self.vida_maxima > maxima_antes:
            self.curar(self.vida_maxima - maxima_antes)

    def multiplicador(self, atributo):
        resultado = 1.0
        for b in self.bonus:
            if b.atributo == atributo:
                resultado *= b.multiplicador
        return resultado

    @property
    def velocidade(self):
        return self.VELOCIDADE * self.mult_velocidade * self.multiplicador("velocidade")

    @property
    def multiplicador_dano(self):
        return self.mult_dano * self.multiplicador("dano")

    def tem_bonus(self, nome):
        return any(b.nome == nome for b in self.bonus)

    def adicionar_bonus(self, bonus):
        self.bonus = [b for b in self.bonus if b.nome != bonus.nome] + [bonus]

    def adicionar_arma(self, arma):
        if len(self.armas) >= self.MAX_ARMAS:
            raise ValueError("o herói já carrega o máximo de armas")
        self.armas.append(arma)

    def remover_arma(self, arma, jogo):
        arma.ao_remover(jogo)
        self.armas.remove(arma)

    def adicionar_item(self, item):
        if len(self.itens) >= self.MAX_ITENS:
            raise ValueError("o herói já carrega o máximo de itens")
        self.itens.append(item)
        self.recalcular_atributos()

    def subir_nivel_item(self, item):
        item.subir_nivel()
        self.recalcular_atributos()

    def encher_cafe(self):
        for arma in self.armas:
            arma.encher()

    @property
    def experiencia_necessaria(self):
        return 8 + (self.nivel - 1) * 5

    def ganhar_experiencia(self, quantidade):
        """Soma experiência e retorna quantos níveis o herói subiu."""
        if quantidade < 0:
            raise ValueError("experiência não pode ser negativa")
        self.experiencia += quantidade
        ganhos = 0
        while self.experiencia >= self.experiencia_necessaria:
            self.experiencia -= self.experiencia_necessaria
            self.nivel += 1
            ganhos += 1
        return ganhos

    @property
    def pode_levar_dano(self):
        return self.invencivel <= 0 and self.esta_vivo

    def receber_dano(self, quantidade):
        morreu = super().receber_dano(quantidade)
        self.invencivel = INVENCIBILIDADE_APOS_DANO
        return morreu

    def usar_especial(self, jogo):
        return self.especial.usar(self, jogo)

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.piscar = max(0.0, self.piscar - dt)
        self.invencivel = max(0.0, self.invencivel - dt)
        direcao = pygame.Vector2(jogo.entrada.direcao)
        self.movendo = direcao.length_squared() > 0
        if self.movendo:
            direcao.normalize_ip()
            self.posicao += direcao * self.velocidade * dt
            self.direcao_mira = pygame.Vector2(direcao)
            if abs(direcao.x) > 0.01:
                self.olhando_esquerda = direcao.x < 0
        arena = jogo.arena
        self.posicao.x = max(arena.left + self.raio, min(self.posicao.x, arena.right - self.raio))
        self.posicao.y = max(arena.top + self.raio, min(self.posicao.y, arena.bottom - self.raio))
        if jogo.entrada.mira is not None:
            mira = pygame.Vector2(jogo.entrada.mira) - self.posicao
            if mira.length_squared() > 1:
                self.direcao_mira = mira.normalize()
                self.olhando_esquerda = mira.x < 0
        if self.regeneracao:
            self.curar(self.regeneracao * dt)
        for b in self.bonus:
            b.atualizar(dt)
        self.bonus = [b for b in self.bonus if b.ativo]
        self.especial.atualizar(dt, self.mult_recarga)
        for arma in list(self.armas):
            arma.atualizar(dt, jogo, self)

    def desenhar(self, tela, camera):
        caminho = self.IMAGEM_TRANSFORMADO if self.IMAGEM_TRANSFORMADO and self.tem_bonus("ssj") else self.IMAGEM
        imagem = Recursos.imagem(caminho, self.ALTURA)
        pulo = abs(math.sin(self.tempo * 10)) * 4 if self.movendo else (1 + math.sin(self.tempo * 2)) * 0.8
        alfa = 130 if self.invencivel > 0 and int(self.invencivel * 20) % 2 else 255
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda,
                        piscar=self.piscar > 0, deslocamento_y=pulo, alfa=alfa)
```

`jogo/jogador/alunos.py`:
```python
"""Os dois heróis jogáveis (arte provisória de aluno genérico)."""
from jogo.armas.caramelo import Caramelo
from jogo.armas.cobra_python import CobraPython
from jogo.jogador.especiais import SuperSaiyajin, Zoltraak
from jogo.jogador.jogador import Jogador


class AlunoAgil(Jogador):
    NOME = "Aluno 1"
    DESCRICAO = "Ágil e frágil. Ataca de longe."
    VIDA = 80
    VELOCIDADE = 230
    IMAGEM = "sprites/aluno1.png"

    def criar_arma_inicial(self):
        return CobraPython()

    def criar_especial(self):
        return Zoltraak()


class AlunoResistente(Jogador):
    NOME = "Aluno 2"
    DESCRICAO = "Resistente e mais lento. Ataca de perto."
    VIDA = 130
    VELOCIDADE = 180
    IMAGEM = "sprites/aluno2.png"
    IMAGEM_TRANSFORMADO = "sprites/aluno2_ssj.png"

    def criar_arma_inicial(self):
        return Caramelo()

    def criar_especial(self):
        return SuperSaiyajin()


HEROIS = (AlunoAgil, AlunoResistente)
```

- [ ] **Step 5: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Jogador, os dois alunos e os especiais Zoltraak e Super Saiyajin

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Fase, cenário e Jogo (a partida)

**Files:**
- Create: `jogo/fase.py`, `jogo/cenario.py`, `jogo/jogo.py`
- Test: `testes/test_jogo.py`

**Interfaces:**
- Consumes: tudo das Tasks 2 a 8.
- Produces:
  - `EventoDaFase(tempo, acao, descricao="")` (dataclass; `executado`).
  - `Fase` (abstrata): `NOME`, `DURACAO`, `APRESENTACOES: tuple[(segundos, nome_inimigo)]`, `INTERVALO_NASCIMENTO = 0.5`; atributos `tempo`, `ativos: list[str]`, `eventos`, `chefe_apareceu`; abstrato `criar_eventos() -> list[EventoDaFase]`; `atualizar(dt, jogo)`, propriedade `escala_dificuldade`, `alvo_de_inimigos() -> int`, `nascer(jogo, nome, quantidade=None)`, `posicao_de_nascimento(jogo)` (`@staticmethod`), `formacao_circulo(jogo, nome, quantidade, raio=560)`, `formacao_parede(jogo, nome, quantidade)`, `chamar_mini_chefe(jogo, nome)`, `chamar_chefe(jogo, nome)`.
  - `SemanaDeProvas(Fase)`: nesta task, só o Bug e nenhum evento (completada na Task 14).
  - `Decoracao(posicao, imagem, altura)` (Entidade que não faz nada ao atualizar), `Cenario(arena)` com `gerar_decoracoes(arena, rng, quantidade=70)` (`@staticmethod`) e `desenhar_chao(tela, camera)`.
  - `Entrada` (dataclass: `direcao: Vector2`, `mira: Vector2 | None`).
  - `Jogo(classe_jogador, fase=None, semente=None)`: atributos `rng, arena, jogador, fase, placar, camera, entrada, grade, cenario, entidades, grupos (defaultdict[str, list]), niveis_pendentes, baus_pendentes, sorteios_restantes, chefe, terminou, venceu, anuncios (list[[texto, restante]])`; propriedade `inimigos`; `adicionar(e)`, `atualizar(dt)`, `desenhar(tela)`, `inimigos_proximos(pos, raio)`, `inimigo_mais_proximo(pos, raio_max, excluir=None)`, `inimigo_com_mais_vida(pos, raio_max)`, `causar_dano(inimigo, dano, direcao=None, forte=False) -> bool`, `ferir_jogador(dano) -> bool`, `dar_experiencia(q)`, `soltar_nota(pos, valor)`, `pedir_bau()`, `iniciar_chefe(chefe)`, `anunciar(texto, duracao=2.5)`, `terminar(venceu)`, `resultado(nome) -> RegistroRanking`.

- [ ] **Step 1: Testes que falham**

`testes/test_jogo.py`:
```python
import pygame
import pytest

from jogo.coletaveis.coletaveis import Nota
from jogo.config import COMBO_ESPECIAL, LIMITE_COLETAVEIS
from jogo.inimigos.bug import Bug
from jogo.jogador.alunos import AlunoAgil, AlunoResistente
from jogo.jogo import Jogo
from jogo.nucleo.entidade import Entidade


class Espiao(Entidade):
    def __init__(self):
        super().__init__((0, 0), 1)
        self.chamadas = 0

    def atualizar(self, dt, jogo):
        self.chamadas += 1

    def desenhar(self, tela, camera):
        pass


def jogo_sem_decoracao(classe=AlunoAgil):
    jogo = Jogo(classe, semente=1)
    for e in jogo.entidades:
        if e.grupo == "decoracao":
            e.remover()
    jogo._limpar()
    return jogo


def test_jogo_contem_jogador_fase_e_placar():
    jogo = Jogo(AlunoAgil, semente=1)
    assert jogo.jogador in jogo.entidades
    assert jogo.fase is not None and jogo.placar is not None
    assert jogo.jogador.posicao == pygame.Vector2(jogo.arena.center)


def test_laco_unico_atualiza_qualquer_entidade():
    jogo = jogo_sem_decoracao()
    espiao = Espiao()
    jogo.adicionar(espiao)
    jogo.atualizar(1 / 60)
    jogo.atualizar(1 / 60)
    assert espiao.chamadas == 2


def test_entidade_removida_sai_das_listas():
    jogo = jogo_sem_decoracao()
    bug = Bug(jogo.jogador.posicao + (300, 0))
    jogo.adicionar(bug)
    jogo.atualizar(0.001)
    assert bug in jogo.inimigos
    bug.remover()
    jogo.atualizar(0.001)
    assert bug not in jogo.inimigos and bug not in jogo.entidades


def test_causar_dano_mata_pontua_e_solta_nota():
    jogo = jogo_sem_decoracao()
    bug = Bug(jogo.jogador.posicao + (300, 0))
    jogo.adicionar(bug)
    jogo.atualizar(0.001)
    assert jogo.causar_dano(bug, 1000) is True
    assert not bug.ativo
    assert jogo.placar.eliminacoes == 1
    assert jogo.placar.pontos == Bug.PONTOS
    assert jogo.causar_dano(bug, 1000) is False
    jogo.atualizar(0.001)
    assert any(isinstance(e, Nota) for e in jogo.entidades)


def test_combo_67_toca_bonus_de_velocidade():
    jogo = jogo_sem_decoracao()
    base = jogo.jogador.velocidade
    for _ in range(COMBO_ESPECIAL):
        bug = Bug(jogo.jogador.posicao + (500, 0))
        jogo.adicionar(bug)
        jogo._incorporar_novas()
        jogo.causar_dano(bug, 1000)
    assert jogo.jogador.tem_bonus("combo67")
    assert jogo.jogador.velocidade == pytest.approx(base * 1.5)
    assert any(texto == "67!" for texto, _ in jogo.anuncios)


def test_ferir_jogador_respeita_invencibilidade_e_zera_combo():
    jogo = jogo_sem_decoracao()
    jogo.placar.combo = 10
    assert jogo.ferir_jogador(5) is True
    assert jogo.placar.combo == 0
    assert jogo.ferir_jogador(5) is False
    assert jogo.jogador.vida == jogo.jogador.vida_maxima - 5


def test_bug_encosta_e_fere_o_heroi():
    jogo = jogo_sem_decoracao()
    jogo.adicionar(Bug(jogo.jogador.posicao + (5, 0)))
    jogo.atualizar(1 / 60)
    assert jogo.jogador.vida < jogo.jogador.vida_maxima


def test_cobra_acerta_bug_na_frente():
    jogo = jogo_sem_decoracao()
    bug = Bug(jogo.jogador.posicao + (120, 0))
    bug.VELOCIDADE = 0
    bug.velocidade = 0
    jogo.adicionar(bug)
    for _ in range(40):
        jogo.atualizar(1 / 60)
    assert not bug.ativo or bug.vida < bug.vida_maxima


def test_caramelo_morde_bug_por_perto():
    jogo = jogo_sem_decoracao(AlunoResistente)
    bug = Bug(jogo.jogador.posicao + (70, 0), escala=50)
    bug.velocidade = 0
    jogo.adicionar(bug)
    for _ in range(90):
        jogo.atualizar(1 / 60)
    assert bug.vida < bug.vida_maxima


def test_notas_viram_experiencia_e_niveis_pendentes():
    jogo = jogo_sem_decoracao()
    jogo.adicionar(Nota(jogo.jogador.posicao, 500))
    jogo.atualizar(1 / 60)
    assert jogo.niveis_pendentes > 1


def test_notas_se_acumulam_quando_passa_do_limite():
    jogo = jogo_sem_decoracao()
    longe = jogo.jogador.posicao + (1000, 0)
    for _ in range(LIMITE_COLETAVEIS + 50):
        jogo.soltar_nota(longe, 1)
        jogo._incorporar_novas()
    notas = [e for e in jogo.entidades if isinstance(e, Nota)]
    assert len(notas) == LIMITE_COLETAVEIS
    assert sum(n.valor for n in notas) == LIMITE_COLETAVEIS + 50


def test_morte_do_heroi_termina_a_partida():
    jogo = jogo_sem_decoracao()
    jogo.jogador.vida = 0
    jogo.atualizar(1 / 60)
    assert jogo.terminou and not jogo.venceu


def test_partida_de_um_minuto_com_jogador_automatico():
    jogo = Jogo(AlunoAgil, semente=7)
    jogo.jogador.vida_maxima = 10 ** 9
    jogo.jogador.vida = 10 ** 9
    tela = pygame.Surface((1280, 720))
    passos = 60 * 60
    for i in range(passos):
        jogo.entrada.direcao = pygame.Vector2(1, 0).rotate(i * 0.5)
        jogo.atualizar(1 / 60)
        if i % 60 == 0:
            jogo.desenhar(tela)
    assert jogo.placar.tempo == pytest.approx(60, abs=0.1)
    assert len(jogo.inimigos) > 10
    assert jogo.placar.eliminacoes > 0


def test_resultado_vira_registro_de_ranking():
    jogo = jogo_sem_decoracao()
    jogo.placar.adicionar_pontos(100)
    jogo.placar.tempo = 10
    jogo.terminar(True)
    r = jogo.resultado("Ana")
    assert r.nome == "Ana" and r.heroi == "Aluno 1" and r.venceu
    assert r.pontos == 100 + 20 + 5000
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_jogo.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.jogo'`

- [ ] **Step 3: Implementar a fase**

`jogo/fase.py`:
```python
"""Fases: linha do tempo de inimigos, mini-chefes e chefe."""
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

import pygame

from jogo.config import ALTURA, LARGURA, MAX_INIMIGOS
from jogo.inimigos.fabrica import FabricaDeInimigos


@dataclass
class EventoDaFase:
    tempo: float
    acao: Callable
    descricao: str = ""
    executado: bool = field(default=False)


class Fase(ABC):
    NOME = "Fase"
    DURACAO = 900
    APRESENTACOES = ()
    INTERVALO_NASCIMENTO = 0.5

    def __init__(self):
        self.tempo = 0.0
        self.ativos = []
        self._apresentados = 0
        self._espera = 0.0
        self.chefe_apareceu = False
        self.eventos = sorted(self.criar_eventos(), key=lambda e: e.tempo)

    @abstractmethod
    def criar_eventos(self):
        """Lista de EventoDaFase (mini-chefes, formações, chefe)."""

    @property
    def escala_dificuldade(self):
        return 1 + self.tempo / 300

    def alvo_de_inimigos(self):
        alvo = 18 + self.tempo * 0.26
        if self.chefe_apareceu:
            alvo *= 0.5
        return min(MAX_INIMIGOS, int(alvo))

    def atualizar(self, dt, jogo):
        self.tempo += dt
        while self._apresentados < len(self.APRESENTACOES) and \
                self.APRESENTACOES[self._apresentados][0] <= self.tempo:
            self.ativos.append(self.APRESENTACOES[self._apresentados][1])
            self._apresentados += 1
        for evento in self.eventos:
            if not evento.executado and evento.tempo <= self.tempo:
                evento.executado = True
                evento.acao(jogo)
        self._espera -= dt
        if self._espera <= 0 and self.ativos:
            self._espera = self.INTERVALO_NASCIMENTO
            if len(jogo.inimigos) < self.alvo_de_inimigos():
                self.nascer(jogo, jogo.rng.choice(self.ativos))

    def nascer(self, jogo, nome, quantidade=None):
        classe = FabricaDeInimigos.classe(nome)
        quantidade = quantidade or classe.TAMANHO_GRUPO
        centro = self.posicao_de_nascimento(jogo)
        for _ in range(quantidade):
            espalhar = pygame.Vector2(jogo.rng.uniform(-40, 40), jogo.rng.uniform(-40, 40))
            jogo.adicionar(FabricaDeInimigos.criar(nome, centro + espalhar, self.escala_dificuldade))

    @staticmethod
    def posicao_de_nascimento(jogo):
        """Um ponto logo fora da tela, em volta do herói, dentro da arena."""
        angulo = jogo.rng.uniform(0, 2 * math.pi)
        distancia = math.hypot(LARGURA, ALTURA) / 2 + 80
        p = jogo.jogador.posicao + pygame.Vector2(math.cos(angulo), math.sin(angulo)) * distancia
        p.x = max(jogo.arena.left + 30, min(p.x, jogo.arena.right - 30))
        p.y = max(jogo.arena.top + 30, min(p.y, jogo.arena.bottom - 30))
        return p

    def formacao_circulo(self, jogo, nome, quantidade, raio=560):
        for i in range(quantidade):
            direcao = pygame.Vector2(1, 0).rotate(360 * i / quantidade)
            jogo.adicionar(FabricaDeInimigos.criar(nome, jogo.jogador.posicao + direcao * raio,
                                                   self.escala_dificuldade))
        jogo.anunciar("Cercado!", 1.5)

    def formacao_parede(self, jogo, nome, quantidade):
        lado = jogo.rng.choice((-1, 1))
        x = jogo.jogador.posicao.x + lado * (LARGURA / 2 + 60)
        for i in range(quantidade):
            y = jogo.jogador.posicao.y + (i - (quantidade - 1) / 2) * 36
            jogo.adicionar(FabricaDeInimigos.criar(nome, (x, y), self.escala_dificuldade))
        jogo.anunciar("Lá vem a turma!", 1.5)

    def chamar_mini_chefe(self, jogo, nome):
        gigante = FabricaDeInimigos.criar_gigante(nome, self.posicao_de_nascimento(jogo), self.escala_dificuldade)
        jogo.adicionar(gigante)
        jogo.anunciar(f"Mini-chefe: {gigante.NOME} Gigante!", 3)

    def chamar_chefe(self, jogo, nome):
        self.chefe_apareceu = True
        jogo.iniciar_chefe(FabricaDeInimigos.criar(nome, self.posicao_de_nascimento(jogo)))


class SemanaDeProvas(Fase):
    NOME = "Semana de Provas"
    DURACAO = 900
    APRESENTACOES = ((0, "bug"),)

    def criar_eventos(self):
        return []
```

- [ ] **Step 4: Implementar o cenário**

`jogo/cenario.py`:
```python
"""Chão do pátio e decorações da arena."""
import pygame

from jogo.config import Cor
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class Decoracao(Entidade):
    """Enfeite parado (árvore, banco, poste). Só existe para ser visto."""

    grupo = "decoracao"
    camada = 1

    def __init__(self, posicao, imagem, altura):
        super().__init__(posicao, 0)
        self.imagem = imagem
        self.altura = altura

    def atualizar(self, dt, jogo):
        pass

    def desenhar(self, tela, camera):
        desenhar_sprite(tela, camera, Recursos.imagem(self.imagem, self.altura), self.posicao)


class Cenario:
    TIPOS = (
        ("cenario/arvore.png", 140, 0.35),
        ("cenario/banco.png", 46, 0.25),
        ("cenario/poste.png", 100, 0.2),
        ("cenario/canteiro.png", 52, 0.2),
    )
    CHAO = "cenario/chao.png"

    def __init__(self, arena):
        self.arena = arena

    @staticmethod
    def gerar_decoracoes(arena, rng, quantidade=70):
        imagens = [t[0] for t in Cenario.TIPOS]
        alturas = {t[0]: t[1] for t in Cenario.TIPOS}
        pesos = [t[2] for t in Cenario.TIPOS]
        centro = pygame.Vector2(arena.center)
        decoracoes = []
        while len(decoracoes) < quantidade:
            p = pygame.Vector2(rng.uniform(arena.left + 80, arena.right - 80),
                               rng.uniform(arena.top + 80, arena.bottom - 80))
            if p.distance_to(centro) < 300:
                continue
            imagem = rng.choices(imagens, pesos)[0]
            decoracoes.append(Decoracao(p, imagem, alturas[imagem]))
        return decoracoes

    def desenhar_chao(self, tela, camera):
        tela.fill(Cor.GRAMA_FORA)
        chao = Recursos.imagem(self.CHAO)
        largura, altura = chao.get_size()
        visivel = camera.retangulo.clip(self.arena)
        x0 = visivel.left - (visivel.left - self.arena.left) % largura
        y0 = visivel.top - (visivel.top - self.arena.top) % altura
        for y in range(int(y0), visivel.bottom, altura):
            for x in range(int(x0), visivel.right, largura):
                tela.blit(chao, camera.para_tela((x, y)))
        borda = self.arena.move(-camera.deslocamento.x, -camera.deslocamento.y)
        pygame.draw.rect(tela, Cor.BORDA_ESCURA, borda, 6)
```

- [ ] **Step 5: Implementar o Jogo**

`jogo/jogo.py`:
```python
"""A partida: contém o Jogador, a Fase, o Placar e todas as entidades."""
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import pygame

from jogo.cenario import Cenario
from jogo.coletaveis.coletaveis import Nota
from jogo.config import (ALTURA, ARENA_ALTURA, ARENA_LARGURA, BONUS_67_DURACAO, BONUS_67_VELOCIDADE, LARGURA,
                         LIMITE_COLETAVEIS, LIMITE_EFEITOS, SORTEIOS_POR_PARTIDA, Cor)
from jogo.efeitos import TextoFlutuante
from jogo.fase import SemanaDeProvas
from jogo.jogador.bonus import BonusTemporario
from jogo.nucleo.camera import Camera
from jogo.nucleo.grade import GradeEspacial
from jogo.nucleo.recursos import Recursos
from jogo.placar import Placar
from jogo.ranking import RegistroRanking

import jogo.inimigos  # noqa: F401  (registra todos os inimigos na fábrica)


@dataclass
class Entrada:
    direcao: pygame.Vector2 = field(default_factory=pygame.Vector2)
    mira: Optional[pygame.Vector2] = None


class Jogo:
    MARGEM_BUSCA = 64

    def __init__(self, classe_jogador, fase=None, semente=None):
        self.rng = random.Random(semente)
        self.arena = pygame.Rect(0, 0, ARENA_LARGURA, ARENA_ALTURA)
        self.jogador = classe_jogador(self.arena.center)
        self.fase = fase if fase is not None else SemanaDeProvas()
        self.placar = Placar()
        self.camera = Camera(LARGURA, ALTURA, self.arena)
        self.entrada = Entrada()
        self.grade = GradeEspacial(96)
        self.cenario = Cenario(self.arena)
        self.entidades = []
        self.grupos = defaultdict(list)
        self._novas = []
        self.niveis_pendentes = 0
        self.baus_pendentes = 0
        self.sorteios_restantes = SORTEIOS_POR_PARTIDA
        self.chefe = None
        self.terminou = False
        self.venceu = False
        self.anuncios = []
        self._ultima_nota = None
        self.adicionar(self.jogador)
        for decoracao in Cenario.gerar_decoracoes(self.arena, self.rng):
            self.adicionar(decoracao)
        self._incorporar_novas()
        self.camera.seguir(self.jogador.posicao)

    @property
    def inimigos(self):
        return self.grupos["inimigo"]

    def adicionar(self, entidade):
        self._novas.append(entidade)

    def _incorporar_novas(self):
        while self._novas:
            novas, self._novas = self._novas, []
            for e in novas:
                self.entidades.append(e)
                self.grupos[e.grupo].append(e)

    def _limpar(self):
        self.entidades = [e for e in self.entidades if e.ativo]
        for nome in list(self.grupos):
            self.grupos[nome] = [e for e in self.grupos[nome] if e.ativo]

    def atualizar(self, dt):
        if self.terminou:
            return
        self.placar.tempo += dt
        self.fase.atualizar(dt, self)
        self._incorporar_novas()
        self.grade.reconstruir(self.inimigos)
        for e in self.entidades:          # polimorfismo: um único laço, sem if por tipo
            if e.ativo:
                e.atualizar(dt, self)
        self._incorporar_novas()
        self._limpar()
        for anuncio in self.anuncios:
            anuncio[1] -= dt
        self.anuncios = [a for a in self.anuncios if a[1] > 0]
        self.camera.seguir(self.jogador.posicao)
        if not self.jogador.esta_vivo:
            self.terminar(False)

    def desenhar(self, tela):
        self.cenario.desenhar_chao(tela, self.camera)
        visiveis = [e for e in self.entidades if self.camera.visivel(e.posicao, 160)]
        visiveis.sort(key=lambda e: (e.camada, e.posicao.y))
        for e in visiveis:
            e.desenhar(tela, self.camera)

    # Buscas

    def inimigos_proximos(self, posicao, raio):
        """Inimigos ativos cujo círculo encosta no círculo (posicao, raio)."""
        resultado = []
        for e in self.grade.proximos(posicao, raio + self.MARGEM_BUSCA):
            if e.ativo:
                limite = raio + e.raio
                if e.posicao.distance_squared_to(posicao) <= limite * limite:
                    resultado.append(e)
        return resultado

    def inimigo_mais_proximo(self, posicao, raio_max, excluir=None):
        melhor, melhor_distancia = None, raio_max * raio_max
        for e in self.grade.proximos(posicao, raio_max):
            if e is excluir or not e.ativo:
                continue
            distancia = e.posicao.distance_squared_to(posicao)
            if distancia <= melhor_distancia:
                melhor, melhor_distancia = e, distancia
        return melhor

    def inimigo_com_mais_vida(self, posicao, raio_max):
        candidatos = [e for e in self.grade.proximos(posicao, raio_max)
                      if e.ativo and e.posicao.distance_squared_to(posicao) <= raio_max * raio_max]
        return max(candidatos, key=lambda e: e.vida, default=None)

    # Regras

    def causar_dano(self, inimigo, dano, direcao=None, forte=False):
        """Fere um inimigo. Retorna True se ele morreu com este golpe."""
        if not inimigo.ativo or not inimigo.esta_vivo:
            return False
        dano = max(1, round(dano))
        morreu = inimigo.receber_dano(dano)
        if direcao is not None:
            inimigo.empurrar(direcao)
        if len(self.grupos["efeito"]) < LIMITE_EFEITOS:
            deslocamento = pygame.Vector2(self.rng.uniform(-8, 8), -inimigo.raio)
            self.adicionar(TextoFlutuante(str(dano), inimigo.posicao + deslocamento,
                                          Cor.DANO_FORTE if forte else Cor.DANO, 22 if forte else 16))
        Recursos.tocar("acerto", 0.12)
        if morreu:
            self._registrar_morte(inimigo)
        return morreu

    def _registrar_morte(self, inimigo):
        inimigo.remover()
        if self.placar.registrar_eliminacao(inimigo.valor_em_pontos):
            self._combo_67()
        inimigo.ao_morrer(self)

    def _combo_67(self):
        self.jogador.adicionar_bonus(BonusTemporario("combo67", "velocidade", BONUS_67_VELOCIDADE, BONUS_67_DURACAO))
        self.anunciar("67!", 2.0)
        Recursos.tocar("67", 0.9)

    def ferir_jogador(self, dano):
        if not self.jogador.pode_levar_dano:
            return False
        self.jogador.receber_dano(dano)
        self.placar.zerar_combo()
        self.adicionar(TextoFlutuante(f"-{round(dano)}", self.jogador.posicao - (0, 30), Cor.DANO_HEROI, 18))
        Recursos.tocar("dano", 0.4)
        return True

    def dar_experiencia(self, quantidade):
        niveis = self.jogador.ganhar_experiencia(quantidade)
        self.niveis_pendentes += niveis

    def soltar_nota(self, posicao, valor):
        """Solta uma nota; acima do limite, soma o valor na última nota solta."""
        if len(self.grupos["coletavel"]) + len(self._novas) >= LIMITE_COLETAVEIS and \
                self._ultima_nota is not None and self._ultima_nota.ativo:
            self._ultima_nota.valor += valor
            return
        self._ultima_nota = Nota(posicao, valor)
        self.adicionar(self._ultima_nota)

    def pedir_bau(self):
        self.baus_pendentes += 1
        Recursos.tocar("bau", 0.6)

    def iniciar_chefe(self, chefe):
        self.chefe = chefe
        self.adicionar(chefe)
        self.anunciar(f"{chefe.NOME} chegou!", 3)

    def anunciar(self, texto, duracao=2.5):
        self.anuncios.append([texto, duracao])

    def terminar(self, venceu):
        if self.terminou:
            return
        self.terminou = True
        self.venceu = venceu
        Recursos.tocar("vitoria" if venceu else "derrota", 0.7)

    def resultado(self, nome):
        return RegistroRanking(nome, self.jogador.NOME, self.placar.pontuacao_final(self.venceu),
                               self.placar.tempo, self.venceu)
```

Atenção ao `soltar_nota`: o teste conta notas já incorporadas; por isso a soma usa `len(self.grupos["coletavel"]) + len(self._novas)`.

- [ ] **Step 6: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam. Se `test_partida_de_um_minuto_com_jogador_automatico` demorar mais de 20 s, investigar desempenho antes de seguir.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "Fase, cenário e Jogo com o laço polimórfico das entidades

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Janela, cenas básicas, HUD e protótipo jogável

**Files:**
- Create: `jogo/aplicacao.py`, `jogo/cenas/__init__.py` (vazio), `jogo/cenas/cena.py`, `jogo/cenas/widgets.py`, `jogo/cenas/hud.py`, `jogo/cenas/partida.py`, `main.py`
- Test: `testes/test_cenas.py`

**Interfaces:**
- Consumes: `Jogo`, `Recursos`, `Cor`, `HEROIS`.
- Produces:
  - `Aplicacao(tela=None)`: `tela`, `ranking`, `mira_mouse: bool`, `cenas` (pilha); `empilhar(c)`, `desempilhar()`, `trocar(c)`, propriedade `cena_atual`, `passo(dt, eventos)` (um quadro: eventos, atualizar, desenhar), `executar(cena_inicial)`, `sair()`.
  - `Cena(app)` (abstrata): `tratar_evento(evento)`, `atualizar(dt)`, `desenhar(tela)`.
  - `widgets`: `desenhar_texto(tela, texto, tamanho, cor, *, centro=None, topo_esquerda=None, topo_direita=None, sombra=True) -> Rect`, `quebrar_linhas(texto, fonte, largura) -> list[str]`, `desenhar_painel(tela, rect, cor_fundo=Cor.PAINEL, cor_borda=Cor.BORDA, alfa=235)`, `desenhar_barra(tela, rect, fracao, cor, cor_fundo=(40, 30, 50))`, `escurecer(tela, alfa=160)`, `Botao(texto, centro, acao, largura=320, altura=64)`, `MenuDeBotoes(botoes)` com `tratar_evento`, `desenhar`.
  - `Hud().desenhar(tela, jogo)`.
  - `CenaPartida(app, classe_jogador)` com atributo `jogo`.

- [ ] **Step 1: Testes que falham**

`testes/test_cenas.py`:
```python
import pygame

from jogo.aplicacao import Aplicacao
from jogo.cenas.partida import CenaPartida
from jogo.jogador.alunos import AlunoAgil


def tecla(k, tipo=pygame.KEYDOWN):
    return pygame.event.Event(tipo, key=k, mod=0, unicode="", scancode=0)


def test_partida_roda_alguns_quadros_e_desenha_o_hud():
    app = Aplicacao(pygame.Surface((1280, 720)))
    app.trocar(CenaPartida(app, AlunoAgil))
    for _ in range(30):
        app.passo(1 / 60, [])
    assert app.cena_atual.jogo.placar.tempo > 0.4


def test_espaco_usa_o_especial():
    app = Aplicacao(pygame.Surface((1280, 720)))
    cena = CenaPartida(app, AlunoAgil)
    app.trocar(cena)
    app.passo(1 / 60, [tecla(pygame.K_SPACE)])
    assert not cena.jogo.jogador.especial.pronto
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_cenas.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.aplicacao'`

- [ ] **Step 3: Implementar aplicação e cena base**

`jogo/aplicacao.py`:
```python
"""Janela do jogo e pilha de cenas."""
import pygame

from jogo.config import ALTURA, ARQUIVO_RANKING, FPS, LARGURA, TITULO
from jogo.ranking import Ranking


class Aplicacao:
    def __init__(self, tela=None):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        if tela is None:
            tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.SCALED | pygame.RESIZABLE)
            pygame.display.set_caption(TITULO)
        self.tela = tela
        self.relogio = pygame.time.Clock()
        self.ranking = Ranking(ARQUIVO_RANKING)
        self.mira_mouse = False
        self.cenas = []
        self.rodando = True

    @property
    def cena_atual(self):
        return self.cenas[-1]

    def empilhar(self, cena):
        self.cenas.append(cena)

    def desempilhar(self):
        self.cenas.pop()

    def trocar(self, cena):
        self.cenas = [cena]

    def sair(self):
        self.rodando = False

    def passo(self, dt, eventos):
        """Um quadro: entrega eventos, atualiza a cena do topo e desenha a pilha."""
        for evento in eventos:
            if evento.type == pygame.QUIT:
                self.sair()
                return
            self.cena_atual.tratar_evento(evento)
        self.cena_atual.atualizar(dt)
        for cena in list(self.cenas):
            cena.desenhar(self.tela)

    def executar(self, cena_inicial):
        self.trocar(cena_inicial)
        while self.rodando and self.cenas:
            dt = min(self.relogio.tick(FPS) / 1000, 1 / 20)
            self.passo(dt, pygame.event.get())
            pygame.display.flip()
        pygame.quit()
```

`jogo/cenas/cena.py`:
```python
from abc import ABC, abstractmethod


class Cena(ABC):
    """Uma tela do jogo (título, partida, pausa...)."""

    def __init__(self, app):
        self.app = app

    @abstractmethod
    def tratar_evento(self, evento):
        """Recebe um evento do Pygame (tecla, mouse)."""

    @abstractmethod
    def atualizar(self, dt):
        """Avança a cena."""

    @abstractmethod
    def desenhar(self, tela):
        """Desenha a cena."""
```

- [ ] **Step 4: Implementar os widgets**

`jogo/cenas/widgets.py`:
```python
"""Peças de interface reaproveitadas pelas cenas."""
import pygame

from jogo.config import Cor
from jogo.nucleo.recursos import Recursos

TECLAS_CONFIRMAR = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


def desenhar_texto(tela, texto, tamanho, cor, *, centro=None, topo_esquerda=None, topo_direita=None, sombra=True):
    fonte = Recursos.fonte(tamanho)
    imagem = fonte.render(texto, True, cor)
    if centro is not None:
        retangulo = imagem.get_rect(center=centro)
    elif topo_direita is not None:
        retangulo = imagem.get_rect(topright=topo_direita)
    else:
        retangulo = imagem.get_rect(topleft=topo_esquerda or (0, 0))
    if sombra:
        tela.blit(fonte.render(texto, True, Cor.BORDA_ESCURA), retangulo.move(2, 2))
    tela.blit(imagem, retangulo)
    return retangulo


def quebrar_linhas(texto, fonte, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if fonte.size(tentativa)[0] <= largura or not atual:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def desenhar_painel(tela, retangulo, cor_fundo=Cor.PAINEL, cor_borda=Cor.BORDA, alfa=235):
    painel = pygame.Surface(retangulo.size, pygame.SRCALPHA)
    pygame.draw.rect(painel, (*cor_fundo, alfa), painel.get_rect(), border_radius=6)
    pygame.draw.rect(painel, Cor.BORDA_ESCURA, painel.get_rect(), 4, border_radius=6)
    pygame.draw.rect(painel, cor_borda, painel.get_rect().inflate(-6, -6), 2, border_radius=4)
    tela.blit(painel, retangulo)


def desenhar_barra(tela, retangulo, fracao, cor, cor_fundo=(40, 30, 50)):
    pygame.draw.rect(tela, Cor.BORDA_ESCURA, retangulo.inflate(4, 4), border_radius=4)
    pygame.draw.rect(tela, cor_fundo, retangulo, border_radius=3)
    cheio = retangulo.copy()
    cheio.width = round(retangulo.width * max(0.0, min(1.0, fracao)))
    if cheio.width > 0:
        pygame.draw.rect(tela, cor, cheio, border_radius=3)


def escurecer(tela, alfa=160):
    veu = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    veu.fill((10, 8, 18, alfa))
    tela.blit(veu, (0, 0))


class Botao:
    IMAGEM = "legado/ui/btn_wood.png"
    IMAGEM_FOCO = "legado/ui/btn_gold.png"

    def __init__(self, texto, centro, acao, largura=320, altura=64):
        self.texto = texto
        self.acao = acao
        self.retangulo = pygame.Rect(0, 0, largura, altura)
        self.retangulo.center = centro

    def desenhar(self, tela, focado):
        imagem = Recursos.imagem(self.IMAGEM_FOCO if focado else self.IMAGEM)
        tela.blit(pygame.transform.scale(imagem, self.retangulo.size), self.retangulo)
        desenhar_texto(tela, self.texto, 28, Cor.BORDA_ESCURA if focado else Cor.TEXTO,
                       centro=self.retangulo.center, sombra=not focado)


class MenuDeBotoes:
    """Lista de botões navegável por teclado (setas/WS + Enter) e mouse."""

    def __init__(self, botoes):
        self.botoes = botoes
        self.indice = 0

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_w):
                self.indice = (self.indice - 1) % len(self.botoes)
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.indice = (self.indice + 1) % len(self.botoes)
            elif evento.key in TECLAS_CONFIRMAR:
                self.botoes[self.indice].acao()
        elif evento.type == pygame.MOUSEMOTION:
            for i, botao in enumerate(self.botoes):
                if botao.retangulo.collidepoint(evento.pos):
                    self.indice = i
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for botao in self.botoes:
                if botao.retangulo.collidepoint(evento.pos):
                    botao.acao()
                    return

    def desenhar(self, tela):
        for i, botao in enumerate(self.botoes):
            botao.desenhar(tela, i == self.indice)
```

- [ ] **Step 5: Implementar o HUD**

`jogo/cenas/hud.py`:
```python
"""Informações da partida desenhadas por cima do jogo."""
import pygame

from jogo.config import LARGURA, Cor
from jogo.cenas.widgets import desenhar_barra, desenhar_painel, desenhar_texto
from jogo.nucleo.recursos import Recursos


class Hud:
    def desenhar(self, tela, jogo):
        self._experiencia(tela, jogo)
        self._heroi(tela, jogo)
        self._armas_e_itens(tela, jogo)
        self._tempo_e_placar(tela, jogo)
        self._chefe(tela, jogo)
        self._anuncios(tela, jogo)

    def _experiencia(self, tela, jogo):
        j = jogo.jogador
        desenhar_barra(tela, pygame.Rect(4, 4, LARGURA - 8, 12), j.experiencia / j.experiencia_necessaria,
                       Cor.EXPERIENCIA)
        desenhar_texto(tela, f"NV {j.nivel}", 16, Cor.TEXTO, topo_direita=(LARGURA - 10, 18))

    def _heroi(self, tela, jogo):
        j = jogo.jogador
        desenhar_painel(tela, pygame.Rect(10, 24, 300, 70))
        retrato = Recursos.icone(j.IMAGEM, 52)
        tela.blit(retrato, retrato.get_rect(center=(44, 59)))
        desenhar_texto(tela, j.NOME, 18, Cor.TEXTO, topo_esquerda=(78, 32))
        desenhar_barra(tela, pygame.Rect(78, 58, 160, 16), j.vida / j.vida_maxima, Cor.VIDA)
        desenhar_texto(tela, f"{round(j.vida)}/{round(j.vida_maxima)}", 14, Cor.TEXTO, centro=(158, 66))
        especial = j.especial
        centro = pygame.Vector2(274, 59)
        icone = Recursos.icone(especial.ICONE, 40)
        tela.blit(icone, icone.get_rect(center=centro))
        if not especial.pronto:
            veu = pygame.Surface((44, 44), pygame.SRCALPHA)
            altura = round(44 * (1 - especial.progresso))
            veu.fill((10, 8, 18, 170), pygame.Rect(0, 0, 44, altura))
            tela.blit(veu, veu.get_rect(center=centro))
        else:
            desenhar_texto(tela, "ESPAÇO", 11, Cor.DESTAQUE, centro=(centro.x, centro.y + 26))

    def _armas_e_itens(self, tela, jogo):
        j = jogo.jogador
        for i, arma in enumerate(j.armas):
            caixa = pygame.Rect(12 + i * 46, 102, 42, 42)
            desenhar_painel(tela, caixa, alfa=210)
            icone = Recursos.icone(arma.ICONE, 30)
            tela.blit(icone, icone.get_rect(center=caixa.center))
            desenhar_texto(tela, str(arma.nivel), 12, Cor.DESTAQUE, topo_direita=(caixa.right - 4, caixa.bottom - 16))
            if arma.fracao_cafe is not None:
                desenhar_barra(tela, pygame.Rect(caixa.left + 3, caixa.bottom + 3, caixa.width - 6, 4),
                               arma.fracao_cafe, Cor.CAFE)
        for i, item in enumerate(j.itens):
            caixa = pygame.Rect(12 + i * 38, 156, 34, 34)
            desenhar_painel(tela, caixa, alfa=210)
            icone = Recursos.icone(item.ICONE, 24)
            tela.blit(icone, icone.get_rect(center=caixa.center))
            desenhar_texto(tela, str(item.nivel), 11, Cor.DESTAQUE, topo_direita=(caixa.right - 3, caixa.bottom - 14))

    def _tempo_e_placar(self, tela, jogo):
        desenhar_texto(tela, jogo.placar.tempo_formatado, 34, Cor.TEXTO, centro=(LARGURA // 2, 42))
        desenhar_texto(tela, jogo.fase.NOME, 14, Cor.TEXTO_FRACO, centro=(LARGURA // 2, 66))
        desenhar_texto(tela, f"{jogo.placar.pontos} pts", 20, Cor.DESTAQUE, topo_direita=(LARGURA - 14, 38))
        desenhar_texto(tela, f"{jogo.placar.eliminacoes} eliminações", 14, Cor.TEXTO, topo_direita=(LARGURA - 14, 62))
        combo = jogo.placar.combo % 67
        desenhar_texto(tela, f"COMBO {combo}/67", 14, Cor.DESTAQUE if combo > 50 else Cor.TEXTO_FRACO,
                       topo_direita=(LARGURA - 14, 80))

    def _chefe(self, tela, jogo):
        chefe = jogo.chefe
        if chefe is None or not chefe.ativo:
            return
        retangulo = pygame.Rect(0, 0, 640, 18)
        retangulo.midbottom = (LARGURA // 2, tela.get_height() - 24)
        desenhar_barra(tela, retangulo, chefe.vida / chefe.vida_maxima, Cor.VIDA)
        desenhar_texto(tela, chefe.NOME.upper(), 18, Cor.TEXTO, centro=(LARGURA // 2, retangulo.top - 14))

    def _anuncios(self, tela, jogo):
        for i, (texto, restante) in enumerate(jogo.anuncios[-3:]):
            tamanho = 96 if texto == "67!" else 40
            imagem_y = tela.get_height() // 3 + i * 56
            desenhar_texto(tela, texto, tamanho, Cor.DESTAQUE, centro=(LARGURA // 2, imagem_y))
```

- [ ] **Step 6: Implementar a cena da partida e o `main.py`**

`jogo/cenas/partida.py`:
```python
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.hud import Hud
from jogo.jogo import Jogo


class CenaPartida(Cena):
    ESPERA_FIM = 1.5

    def __init__(self, app, classe_jogador):
        super().__init__(app)
        self.jogo = Jogo(classe_jogador)
        self.hud = Hud()
        self._espera_fim = self.ESPERA_FIM

    def tratar_evento(self, evento):
        if evento.type != pygame.KEYDOWN:
            return
        if evento.key == pygame.K_ESCAPE:
            self._pausar()
        elif evento.key == pygame.K_SPACE:
            self.jogo.jogador.usar_especial(self.jogo)

    def _pausar(self):
        from jogo.cenas.pausa import CenaPausa
        self.app.empilhar(CenaPausa(self.app, self))

    def _ler_entrada(self):
        teclas = pygame.key.get_pressed()
        x = (teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT])
        y = (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP])
        self.jogo.entrada.direcao = pygame.Vector2(x, y)
        self.jogo.entrada.mira = self.jogo.camera.para_mundo(pygame.mouse.get_pos()) if self.app.mira_mouse else None

    def atualizar(self, dt):
        if self.jogo.terminou:
            self._espera_fim -= dt
            if self._espera_fim <= 0:
                self._encerrar()
            return
        self._ler_entrada()
        self.jogo.atualizar(dt)
        if self.jogo.niveis_pendentes > 0:
            self._abrir("jogo.cenas.nivel", "CenaNivel")
        elif self.jogo.baus_pendentes > 0:
            self._abrir("jogo.cenas.bau", "CenaBau")

    def _abrir(self, modulo, nome):
        import importlib
        try:
            classe = getattr(importlib.import_module(modulo), nome)
        except (ImportError, AttributeError):
            self.jogo.niveis_pendentes = 0
            self.jogo.baus_pendentes = 0
            return
        self.app.empilhar(classe(self.app, self.jogo))

    def _encerrar(self):
        try:
            from jogo.cenas.fim import CenaFimDeJogo
        except ImportError:
            self.app.sair()
            return
        self.app.trocar(CenaFimDeJogo(self.app, self.jogo))

    def desenhar(self, tela):
        self.jogo.desenhar(tela)
        self.hud.desenhar(tela, self.jogo)
```

Nota: os `import` tardios com fallback deixam o protótipo rodar antes de existirem as cenas de nível, baú, pausa e fim (Task 17). Na Task 17 eles são trocados por imports normais no topo do arquivo, e `_abrir`/`_encerrar` viram chamadas diretas (código completo na Task 17). Até lá, `Esc` falha: `_pausar` só funciona depois da Task 17; no protótipo, feche a janela para sair.

`main.py`:
```python
"""UFJ Survivors. Rode com: python main.py"""
from jogo.aplicacao import Aplicacao
from jogo.cenas.partida import CenaPartida
from jogo.jogador.alunos import AlunoAgil


def main():
    app = Aplicacao()
    app.executar(CenaPartida(app, AlunoAgil))


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 8: Conferir na tela**

Run: `.venv/bin/python main.py` (fechar a janela depois de ~20 s).
Expected: janela abre; herói (substituto colorido) anda com WASD; bugs (substitutos) aparecem e perseguem; cobras saem do herói; números de dano; HUD com vida, experiência, tempo. Sem arte ainda: substitutos e chão verde são esperados.

- [ ] **Step 9: Commit**

```bash
git add -A && git commit -m "Janela, HUD e partida jogável (protótipo sem arte)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Arte do protótipo (etapa 2)

**Files:**
- Create: `arte_bruta/*.png` (ignorado pelo git), `assets/sprites/{aluno1,aluno2,aluno2_ssj,bug,cobra,caramelo,nota,cafe}.png`, `assets/cenario/{chao,arvore,banco,poste,canteiro}.png`, `assets/icones/{zoltraak,ssj}.png`, `assets/CREDITOS.md`

**Interfaces:**
- Produces: arquivos de arte nos caminhos usados pelas classes (`IMAGEM`, `ICONE`, `Cenario.TIPOS`, `Cenario.CHAO`).

Ferramenta: `mcp__imagegen__generate_image` (e `mcp__imagegen__edit_image` para variações). Toda imagem de sprite usa `background="transparent"` e `output_path="arte_bruta/<nome>.png"`. Prompt-base, colocado no começo de todo prompt de sprite:

> Game sprite for a 2D top-down survivors game. Cute chibi pixel art, 16-bit SNES style, three-quarter top-down view like Stardew Valley, thick dark outline, saturated colors, simple cel shading, single subject centered, full body visible, facing right, transparent background, no text, no ground shadow, no frame.

- [ ] **Step 1: Gerar os sprites do protótipo** (uma chamada por arquivo; conferir a prévia; se ficar ruim, gerar de novo com o prompt ajustado)

| Arquivo bruto | Prompt (depois do prompt-base) | Ferramenta |
|---|---|---|
| `aluno1.png` | Subject: a generic university student hero, young man with messy dark hair, green hoodie, blue jeans, sneakers, a backpack, determined smile. | generate |
| `aluno2.png` | Image 1: same character, same pose, same style and proportions; change only the hoodie to orange and add a red cap. | edit (entrada: `arte_bruta/aluno1.png`) |
| `aluno2_ssj.png` | Image 1: same character, same pose; change the hair into tall spiky glowing golden Super Saiyan hair with a few golden sparkles around; keep clothes. | edit (entrada: `arte_bruta/aluno2.png`) |
| `bug.png` | Subject: a goofy lime-green beetle bug monster with huge googly eyes, two antennae, six tiny legs. | generate |
| `cobra.png` | Subject: a small cute snake in Python-logo colors (blue head half, yellow tail half), side view, slithering horizontally, facing right. | generate |
| `caramelo.png` | Subject: a Brazilian caramel-colored mutt dog (vira-lata caramelo), happy, tongue out, running, side view facing right. | generate |
| `nota.png` | Subject: a small round golden token coin with the number "10" embossed on it, shiny. | generate |
| `cafe.png` | Subject: a small paper coffee cup with a brown sleeve and steam rising. | generate |
| `icone_zoltraak.png` | Subject: game skill icon, a powerful purple and white magic beam spell blasting diagonally from a glowing magic circle, square composition. | generate |
| `icone_ssj.png` | Subject: game skill icon, golden spiky Super Saiyan hair silhouette surrounded by a golden flame aura, square composition. | generate |
| `arvore.png` | Subject: a Brazilian ipê tree with bright yellow flowers, full tree. Facing direction does not apply. | generate |
| `banco.png` | Subject: a wooden park bench with iron legs. | generate |
| `poste.png` | Subject: a tall classic street lamp post, lit. | generate |
| `canteiro.png` | Subject: a small round flower bed with green bush and colorful flowers. | generate |

Chão (sem o prompt-base, `background="opaque"`, `aspect_ratio="1:1"`, `output_path="arte_bruta/chao.png"`):

> Seamless tileable top-down texture for a 2D pixel art game: university campus courtyard, light gray stone pavement tiles with thin grass between some tiles, a few tiny leaves, 16-bit SNES style, flat even lighting, no objects, no shadows, no perspective, fills the whole image.

- [ ] **Step 2: Reduzir para o tamanho do jogo**

```bash
P=".venv/bin/python ferramentas/preparar_arte.py"
$P arte_bruta/aluno1.png assets/sprites/aluno1.png --altura 64
$P arte_bruta/aluno2.png assets/sprites/aluno2.png --altura 64
$P arte_bruta/aluno2_ssj.png assets/sprites/aluno2_ssj.png --altura 64
$P arte_bruta/bug.png assets/sprites/bug.png --altura 30
$P arte_bruta/cobra.png assets/sprites/cobra.png --altura 22
$P arte_bruta/caramelo.png assets/sprites/caramelo.png --altura 40
$P arte_bruta/nota.png assets/sprites/nota.png --altura 26
$P arte_bruta/cafe.png assets/sprites/cafe.png --altura 30
$P arte_bruta/icone_zoltraak.png assets/icones/zoltraak.png --altura 64
$P arte_bruta/icone_ssj.png assets/icones/ssj.png --altura 64
$P arte_bruta/arvore.png assets/cenario/arvore.png --altura 140
$P arte_bruta/banco.png assets/cenario/banco.png --altura 46
$P arte_bruta/poste.png assets/cenario/poste.png --altura 100
$P arte_bruta/canteiro.png assets/cenario/canteiro.png --altura 52
$P arte_bruta/chao.png assets/cenario/chao.png --ladrilho 256
```

Expected: cada linha imprime o caminho e o tamanho final.

- [ ] **Step 3: Créditos da arte**

`assets/CREDITOS.md`:
```markdown
# Créditos da arte e do som

- `assets/sprites/`, `assets/icones/`, `assets/cenario/`: gerados com a ferramenta de imagens do ChatGPT para este trabalho (uso acadêmico, sem fins lucrativos). Mascotes, logos e memes citados pertencem aos seus donos.
- `assets/legado/` e `assets/fontes/`: reaproveitados do jogo "Crônicas do Saber" (Fiuphis/Rpggame). Fonte Pixelify Sans (licença OFL).
- `assets/sons/`: sintetizados por `ferramentas/gerar_sons.py`; o 67 usa a voz do sistema macOS.
```

- [ ] **Step 4: Conferir no jogo com uma captura de tela**

Run:
```bash
SDL_VIDEODRIVER=dummy .venv/bin/python -c "
import pygame
from jogo.aplicacao import Aplicacao
from jogo.cenas.partida import CenaPartida
from jogo.jogador.alunos import AlunoAgil
app = Aplicacao(pygame.display.set_mode((1280, 720)))
cena = CenaPartida(app, AlunoAgil); app.trocar(cena)
for i in range(60 * 25):
    cena.jogo.entrada.direcao = pygame.Vector2(1, 0).rotate(i * 0.4)
    cena.jogo.niveis_pendentes = 0
    cena.jogo.atualizar(1 / 60)
cena.desenhar(app.tela)
pygame.image.save(app.tela, 'arte_bruta/captura_prototipo.png')
"
```
Abrir `arte_bruta/captura_prototipo.png` (ferramenta Read) e verificar: herói, bugs, cobras, notas, chão sem emendas fortes e decorações combinam entre si. Ajustar alturas no Step 2 se algo estiver grande ou pequeno demais.

- [ ] **Step 5: Commit (marco da etapa 2)**

```bash
git add -A && git commit -m "Arte do protótipo: alunos, bug, cobra, caramelo, notas e cenário

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git tag etapa-2-prototipo
```

---

### Task 12: Os outros sete lacaios, o Chefe e o Professor

**Files:**
- Create: `jogo/inimigos/calculadora.py`, `jogo/inimigos/mouse_de_bolinha.py`, `jogo/inimigos/caixinha.py`, `jogo/inimigos/pi_cambaleante.py`, `jogo/inimigos/ponteiro.py`, `jogo/inimigos/pilha_aa.py`, `jogo/inimigos/pente_de_ram.py`, `jogo/inimigos/chefe.py`, `jogo/inimigos/professor.py`
- Modify: `jogo/projeteis/projeteis.py` (acrescentar `FolhaDeProva`), `testes/conftest.py` (fixture `jogo_limpo`)
- Test: `testes/test_lacaios.py`

**Interfaces:**
- Consumes: `Inimigo` (com `desenhar_corpo`, Task 6), `FabricaDeInimigos`, `ProjetilInimigo`, `FaiscaExplosao`, `TextoFlutuante`, `desenhar_sombra`.
- Produces: inimigos registrados `"calculadora"`, `"mouse"`, `"caixinha"`, `"caixinha_pequena"`, `"pi"`, `"ponteiro"`, `"pilha"`, `"pente_ram"`, `"professor"`; `Chefe` (abstrata, com `ataques() -> list`, `furioso`, `acao_atual`); `FolhaDeProva(ProjetilInimigo)`; fixture `jogo_limpo(classe=AlunoAgil)` que devolve um `Jogo` sem decorações e com uma fase sem nascimentos (`FaseVazia`).

- [ ] **Step 1: Fixture e testes que falham**

Acrescentar ao fim de `testes/conftest.py`:
```python
@pytest.fixture
def jogo_limpo():
    from jogo.fase import Fase
    from jogo.jogador.alunos import AlunoAgil
    from jogo.jogo import Jogo

    class FaseVazia(Fase):
        NOME = "Fase de teste"

        def criar_eventos(self):
            return []

    def criar(classe=AlunoAgil):
        jogo = Jogo(classe, fase=FaseVazia(), semente=3)
        for e in jogo.entidades:
            if e.grupo == "decoracao":
                e.remover()
        jogo._limpar()
        return jogo

    return criar
```

`testes/test_lacaios.py`:
```python
import pygame
import pytest

from jogo.efeitos import FaiscaExplosao, TextoFlutuante
from jogo.inimigos.caixinha import Caixinha, CaixinhaPequena
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.inimigos.mouse_de_bolinha import MouseDeBolinha
from jogo.inimigos.professor import Professor
from jogo.projeteis.projeteis import FolhaDeProva

LACAIOS = ["bug", "calculadora", "mouse", "caixinha", "pi", "ponteiro", "pilha", "pente_ram"]


def novos(jogo):
    jogo._incorporar_novas()
    return jogo.entidades


def test_todos_os_lacaios_estao_registrados_e_herdam_de_inimigo():
    for nome in LACAIOS + ["professor"]:
        assert issubclass(FabricaDeInimigos.classe(nome), Inimigo)


@pytest.mark.parametrize("nome", LACAIOS + ["professor"])
def test_cada_inimigo_anda_e_desenha_sem_erro(jogo_limpo, nome):
    jogo = jogo_limpo()
    inimigo = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + (250, 120))
    jogo.adicionar(inimigo)
    tela = pygame.Surface((1280, 720))
    inicio = pygame.Vector2(inimigo.posicao)
    for _ in range(90):
        jogo.atualizar(1 / 60)
    jogo.desenhar(tela)
    assert inimigo.posicao != inicio


def test_mouse_fica_parado_e_depois_dispara(jogo_limpo):
    jogo = jogo_limpo()
    mouse = MouseDeBolinha(jogo.jogador.posicao + (400, 0))
    jogo.adicionar(mouse)
    jogo.atualizar(0.2)
    assert mouse.posicao.x == pytest.approx(jogo.jogador.posicao.x + 400, abs=1)
    for _ in range(20):
        jogo.atualizar(1 / 60)
    assert mouse.correndo
    assert mouse.posicao.x < jogo.jogador.posicao.x + 400 - 20


def test_caixinha_se_divide_em_duas_que_nao_se_dividem(jogo_limpo):
    jogo = jogo_limpo()
    caixa = Caixinha(jogo.jogador.posicao + (300, 0))
    jogo.adicionar(caixa)
    jogo._incorporar_novas()
    jogo.causar_dano(caixa, 1000)
    pequenas = [e for e in novos(jogo) if isinstance(e, CaixinhaPequena)]
    assert len(pequenas) == 2
    jogo.causar_dano(pequenas[0], 1000)
    assert len([e for e in novos(jogo) if isinstance(e, CaixinhaPequena) and e.ativo]) == 1


def test_pi_mostra_3_14_ao_morrer(jogo_limpo):
    jogo = jogo_limpo()
    pi = FabricaDeInimigos.criar("pi", jogo.jogador.posicao + (300, 0))
    jogo.adicionar(pi)
    jogo._incorporar_novas()
    jogo.causar_dano(pi, 1000)
    assert any(isinstance(e, TextoFlutuante) for e in novos(jogo))


def test_pilha_explode_e_fere_quem_estiver_perto(jogo_limpo):
    jogo = jogo_limpo()
    pilha = FabricaDeInimigos.criar("pilha", jogo.jogador.posicao + (40, 0))
    jogo.adicionar(pilha)
    jogo._incorporar_novas()
    jogo.causar_dano(pilha, 1000)
    assert any(isinstance(e, FaiscaExplosao) for e in novos(jogo))
    jogo.atualizar(1 / 60)
    assert jogo.jogador.vida < jogo.jogador.vida_maxima


def test_ponteiro_mergulha_em_linha_reta(jogo_limpo):
    jogo = jogo_limpo()
    ponteiro = FabricaDeInimigos.criar("ponteiro", jogo.jogador.posicao + (500, 0))
    jogo.adicionar(ponteiro)
    jogo.atualizar(1 / 60)
    direcao = pygame.Vector2(ponteiro.direcao)
    jogo.jogador.posicao.y += 200
    jogo.atualizar(1 / 60)
    assert ponteiro.direcao == direcao


def test_professor_joga_folhas_chama_lacaios_e_investe(jogo_limpo):
    jogo = jogo_limpo()
    prof = Professor(jogo.jogador.posicao + (300, 0))
    jogo.iniciar_chefe(prof)
    jogo._incorporar_novas()
    prof.atacar_folhas(jogo)
    assert sum(isinstance(e, FolhaDeProva) for e in novos(jogo)) == 7
    antes = len(jogo.inimigos)
    prof.atacar_chamada(jogo)
    novos(jogo)
    assert len(jogo.grupos["inimigo"]) > antes
    prof.atacar_investida(jogo)
    inicio = pygame.Vector2(prof.posicao)
    for _ in range(90):
        jogo.atualizar(1 / 60)
    assert prof.posicao.distance_to(inicio) > 150


def test_professor_furioso_joga_mais_folhas(jogo_limpo):
    jogo = jogo_limpo()
    prof = Professor(jogo.jogador.posicao + (300, 0))
    jogo.adicionar(prof)
    prof.vida = prof.vida_maxima * 0.4
    assert prof.furioso
    prof.atacar_folhas(jogo)
    assert sum(isinstance(e, FolhaDeProva) for e in novos(jogo)) == 11


def test_professor_nao_e_possuido_e_derrota_vence_o_jogo(jogo_limpo):
    jogo = jogo_limpo()
    prof = Professor(jogo.jogador.posicao + (300, 0))
    jogo.iniciar_chefe(prof)
    jogo._incorporar_novas()
    prof.possuir(5)
    assert prof.possuido == 0
    jogo.causar_dano(prof, 10 ** 7)
    assert jogo.terminou and jogo.venceu
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_lacaios.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.inimigos.caixinha'`

- [ ] **Step 3: Implementar os lacaios**

`jogo/inimigos/calculadora.py`:
```python
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("calculadora")
class CalculadoraBrava(Inimigo):
    """Calculadora científica emburrada com ERROR no visor. Persegue sem parar."""

    NOME = "Calculadora Brava"
    IMAGEM = "sprites/calculadora.png"
    ALTURA = 46
    RAIO = 17
    VIDA = 20
    VELOCIDADE = 85
    DANO = 8
    PONTOS = 12
    EXPERIENCIA = 2

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)
```

`jogo/inimigos/mouse_de_bolinha.py`:
```python
import math

import pygame

from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("mouse")
class MouseDeBolinha(Inimigo):
    """Mouse bege antigo que corre como rato: para, mira e dispara em linha reta."""

    NOME = "Mouse de Bolinha"
    IMAGEM = "sprites/mouse.png"
    ALTURA = 34
    RAIO = 15
    VIDA = 12
    VELOCIDADE = 320
    DANO = 7
    PONTOS = 10
    TEMPO_PARADO = 0.7
    TEMPO_CORRENDO = 0.9

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.correndo = False
        self._timer = 0.4
        self._direcao = pygame.Vector2(1, 0)

    def mover(self, dt, jogo):
        self._timer -= dt
        if self.correndo:
            self.posicao += self._direcao * self.velocidade * dt
            if self._timer <= 0:
                self.correndo = False
                self._timer = self.TEMPO_PARADO
        elif self._timer <= 0:
            falta = jogo.jogador.posicao - self.posicao
            if falta.length_squared() > 0:
                self._direcao = falta.normalize()
                self.olhando_esquerda = self._direcao.x < 0
            self.correndo = True
            self._timer = self.TEMPO_CORRENDO

    def balanco(self):
        return abs(math.sin(self.tempo * 22)) * 2 if self.correndo else 0
```

`jogo/inimigos/caixinha.py`:
```python
import math

import pygame

from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("caixinha")
class Caixinha(Inimigo):
    """Caixa de papelão com etiqueta "class". Anda aos pulos; ao morrer solta duas menores."""

    NOME = "Caixinha"
    IMAGEM = "sprites/caixinha.png"
    ALTURA = 42
    RAIO = 17
    VIDA = 22
    VELOCIDADE = 230
    DANO = 7
    PONTOS = 12
    EXPERIENCIA = 2
    CICLO = 1.0
    PULO = 0.35

    def _no_ar(self):
        return self.tempo % self.CICLO < self.PULO

    def mover(self, dt, jogo):
        if self._no_ar():
            self.ir_em_direcao(jogo.jogador.posicao, dt)

    def balanco(self):
        fase = self.tempo % self.CICLO
        return math.sin(math.pi * fase / self.PULO) * 14 if fase < self.PULO else 0

    def ao_morrer(self, jogo):
        super().ao_morrer(jogo)
        for lado in (-1, 1):
            jogo.adicionar(CaixinhaPequena(self.posicao + pygame.Vector2(lado * 16, 0), self.escala))


@FabricaDeInimigos.registrar("caixinha_pequena")
class CaixinhaPequena(Caixinha):
    """A caixinha que sai de dentro da Caixinha. Esta não se divide."""

    ALTURA = 26
    RAIO = 11
    VIDA = 8
    PONTOS = 4
    EXPERIENCIA = 1
    CHANCE_CAFE = 0.0

    def ao_morrer(self, jogo):
        Inimigo.ao_morrer(self, jogo)
```

`jogo/inimigos/pi_cambaleante.py`:
```python
import math

from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("pi")
class PiCambaleante(Inimigo):
    """A letra π gorducha, de chapeuzinho de festa, andando em zigue-zague."""

    NOME = "Pi Cambaleante"
    IMAGEM = "sprites/pi.png"
    ALTURA = 46
    RAIO = 16
    VIDA = 16
    VELOCIDADE = 95
    DANO = 6
    PONTOS = 10
    EXPERIENCIA = 2

    def mover(self, dt, jogo):
        falta = jogo.jogador.posicao - self.posicao
        if falta.length_squared() < 1:
            return
        frente = falta.normalize()
        lado = frente.rotate(90) * math.sin(self.tempo * 4) * 0.9
        self.ir_em_direcao(self.posicao + (frente + lado) * 100, dt)

    def ao_morrer(self, jogo):
        super().ao_morrer(jogo)
        jogo.adicionar(TextoFlutuante("3,14...", self.posicao - (0, 20), Cor.DESTAQUE, 16, duracao=1.0))
```

`jogo/inimigos/ponteiro.py`:
```python
import math

import pygame

from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.nucleo.desenho import desenhar_sprite
from jogo.nucleo.recursos import Recursos


@FabricaDeInimigos.registrar("ponteiro")
class Ponteiro(Inimigo):
    """A setinha do mouse: mergulha em linha reta, passa do ponto e mira de novo."""

    NOME = "Ponteiro"
    IMAGEM = "sprites/ponteiro.png"
    ALTURA = 34
    RAIO = 13
    VIDA = 9
    VELOCIDADE = 380
    DANO = 6
    PONTOS = 10
    TEMPO_MERGULHO = 1.8
    ANGULO_DA_PONTA = 135   # a ponta do cursor aponta para cima e para a esquerda

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self.direcao = pygame.Vector2(1, 0)
        self._timer = 0.0

    def mover(self, dt, jogo):
        self._timer -= dt
        if self._timer <= 0:
            falta = jogo.jogador.posicao - self.posicao
            if falta.length_squared() > 0:
                self.direcao = falta.normalize()
            self._timer = self.TEMPO_MERGULHO
        self.posicao += self.direcao * self.velocidade * dt

    def desenhar_corpo(self, tela, camera):
        imagem = Recursos.imagem(self.IMAGEM, int(self.altura_sprite))
        angulo = math.degrees(math.atan2(-self.direcao.y, self.direcao.x)) - self.ANGULO_DA_PONTA
        desenhar_sprite(tela, camera, imagem, self.posicao, piscar=self.piscar > 0, angulo=angulo or 0.01)
```

`jogo/inimigos/pilha_aa.py`:
```python
import math

from jogo.efeitos import FaiscaExplosao
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo


@FabricaDeInimigos.registrar("pilha")
class PilhaAA(Inimigo):
    """Pilha AA brava que anda aos saltos e solta faíscas ao morrer."""

    NOME = "Pilha AA"
    IMAGEM = "sprites/pilha.png"
    ALTURA = 44
    RAIO = 15
    VIDA = 20
    VELOCIDADE = 75
    DANO = 9
    PONTOS = 12
    EXPERIENCIA = 2
    RAIO_EXPLOSAO = 70
    DANO_EXPLOSAO = 10

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)

    def balanco(self):
        return abs(math.sin(self.tempo * 6)) * 8

    def ao_morrer(self, jogo):
        super().ao_morrer(jogo)
        jogo.adicionar(FaiscaExplosao(self.posicao, self.RAIO_EXPLOSAO, self.DANO_EXPLOSAO))
```

`jogo/inimigos/pente_de_ram.py`:
```python
import math

import pygame

from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.inimigos.inimigo import Inimigo
from jogo.nucleo.desenho import desenhar_sombra
from jogo.nucleo.recursos import Recursos


@FabricaDeInimigos.registrar("pente_ram")
class PenteDeRAM(Inimigo):
    """Pente de memória que anda como centopeia: lento e resistente."""

    NOME = "Pente de RAM"
    IMAGEM = "sprites/pente_ram.png"
    ALTURA = 30
    RAIO = 22
    VIDA = 60
    VELOCIDADE = 55
    DANO = 10
    PONTOS = 25
    EXPERIENCIA = 4
    FATIAS = 5

    def mover(self, dt, jogo):
        self.ir_em_direcao(jogo.jogador.posicao, dt)

    def desenhar_corpo(self, tela, camera):
        """Desenha o pente em fatias que ondulam, como as patas de uma centopeia."""
        imagem = Recursos.imagem(self.IMAGEM, int(self.altura_sprite))
        if self.piscar > 0:
            imagem = Recursos.silhueta_branca(imagem)
        if self.olhando_esquerda:
            imagem = Recursos.espelhada(imagem)
        centro = camera.para_tela(self.posicao)
        largura, altura = imagem.get_size()
        desenhar_sombra(tela, (centro.x, centro.y + altura / 2), largura * 0.9)
        fatia = math.ceil(largura / self.FATIAS)
        for i in range(self.FATIAS):
            area = pygame.Rect(i * fatia, 0, min(fatia, largura - i * fatia), altura)
            onda = math.sin(self.tempo * 8 + i * 0.9) * altura * 0.12
            tela.blit(imagem, (round(centro.x - largura / 2 + i * fatia), round(centro.y - altura / 2 - onda - 2)), area)
```

- [ ] **Step 4: Implementar a folha de prova, o Chefe e o Professor**

Acrescentar ao fim de `jogo/projeteis/projeteis.py`:
```python
class FolhaDeProva(ProjetilInimigo):
    IMAGEM = "sprites/folha_prova.png"
    ALTURA = 26
    DURACAO = 4.0

    def angulo_desenho(self):
        return self.tempo * 360
```

`jogo/inimigos/chefe.py`:
```python
"""Base dos chefes: alternam ataques e ficam furiosos com pouca vida."""
from abc import ABC, abstractmethod

from jogo.inimigos.inimigo import Inimigo


class Chefe(Inimigo, ABC):
    CHANCE_CAFE = 0.0
    CHANCE_POCAO = 0.0
    INTERVALO_ATAQUE = 2.6
    INTERVALO_FURIOSO = 1.6
    DISTANCIA_PREFERIDA = 260

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, 1.0)
        self.reposiciona = False
        self._espera_ataque = 2.0
        self._indice = 0
        self.acao_atual = None

    @property
    def furioso(self):
        return self.vida < self.vida_maxima / 2

    @abstractmethod
    def ataques(self):
        """Lista de ataques (métodos que recebem o jogo), usados em sequência."""

    def mover(self, dt, jogo):
        if self.acao_atual is not None:
            if self.acao_atual(dt, jogo):
                self.acao_atual = None
            return
        if self.posicao.distance_to(jogo.jogador.posicao) > self.DISTANCIA_PREFERIDA:
            self.ir_em_direcao(jogo.jogador.posicao, dt)
        self._espera_ataque -= dt
        if self._espera_ataque <= 0:
            lista = self.ataques()
            lista[self._indice % len(lista)](jogo)
            self._indice += 1
            self._espera_ataque = self.INTERVALO_FURIOSO if self.furioso else self.INTERVALO_ATAQUE

    def possuir(self, duracao):
        """Chefes não são possuídos pelo Fusca."""

    def empurrar(self, direcao, forca=180):
        super().empurrar(direcao, forca * 0.1)
```

`jogo/inimigos/professor.py`:
```python
"""O Professor: chefe final da Semana de Provas (arte genérica provisória)."""
import pygame

from jogo.config import Cor
from jogo.efeitos import TextoFlutuante
from jogo.inimigos.chefe import Chefe
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.projeteis.projeteis import FolhaDeProva


@FabricaDeInimigos.registrar("professor")
class Professor(Chefe):
    NOME = "Professor"
    IMAGEM = "sprites/professor.png"
    ALTURA = 112
    RAIO = 40
    VIDA = 9000
    VELOCIDADE = 75
    DANO = 18
    PONTOS = 5000
    EXPERIENCIA = 0
    LACAIOS_CHAMADA = ("bug", "calculadora", "caixinha", "pi", "pilha")
    TEMPO_CARGA = 0.8
    TEMPO_INVESTIDA = 0.6
    VELOCIDADE_INVESTIDA = 720

    def __init__(self, posicao, escala=1.0):
        super().__init__(posicao, escala)
        self._carga = 0.0
        self._investida = 0.0
        self._direcao = pygame.Vector2(1, 0)

    def ataques(self):
        return [self.atacar_folhas, self.atacar_investida, self.atacar_folhas, self.atacar_chamada]

    def _mirar(self, jogo):
        falta = jogo.jogador.posicao - self.posicao
        return falta.normalize() if falta.length_squared() > 0 else pygame.Vector2(1, 0)

    def atacar_folhas(self, jogo):
        quantidade = 11 if self.furioso else 7
        base = self._mirar(jogo)
        for i in range(quantidade):
            direcao = base.rotate((i - (quantidade - 1) / 2) * 12)
            jogo.adicionar(FolhaDeProva(self.posicao, direcao * 300, 12))

    def atacar_investida(self, jogo):
        self._carga = self.TEMPO_CARGA
        self._investida = self.TEMPO_INVESTIDA
        self._direcao = self._mirar(jogo)
        self.acao_atual = self._investindo

    def _investindo(self, dt, jogo):
        if self._carga > 0:
            self._carga -= dt
            self._direcao = self._mirar(jogo)
            return False
        self._investida -= dt
        self.posicao += self._direcao * self.VELOCIDADE_INVESTIDA * dt
        return self._investida <= 0

    def atacar_chamada(self, jogo):
        quantidade = 8 if self.furioso else 6
        for i in range(quantidade):
            posicao = self.posicao + pygame.Vector2(140, 0).rotate(360 * i / quantidade)
            nome = jogo.rng.choice(self.LACAIOS_CHAMADA)
            jogo.adicionar(FabricaDeInimigos.criar(nome, posicao, jogo.fase.escala_dificuldade))
        jogo.adicionar(TextoFlutuante("CHAMADA!", self.posicao - (0, 80), Cor.DESTAQUE, 22, duracao=1.2))

    def ao_morrer(self, jogo):
        jogo.terminar(venceu=True)

    def desenhar_corpo(self, tela, camera):
        if self.acao_atual is not None and self._carga > 0:
            inicio = camera.para_tela(self.posicao)
            fim = inicio + self._direcao * self.VELOCIDADE_INVESTIDA * self.TEMPO_INVESTIDA
            pygame.draw.line(tela, (230, 60, 60), inicio, fim, 6)
        super().desenhar_corpo(tela, camera)
```

- [ ] **Step 5: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Sete lacaios, chefe e Professor com folhas, investida e chamada

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: Armas ChatGPT, Claude, Gemini e Fusca Azul

**Files:**
- Create: `jogo/armas/chatgpt.py`, `jogo/armas/claude.py`, `jogo/armas/gemini.py`, `jogo/armas/fusca.py`
- Modify: `jogo/projeteis/projeteis.py` (acrescentar `TiroChatGPT`, `EstrelaGemini`), `jogo/ajudantes/ajudantes.py` (acrescentar `MascoteFlutuante`, `FuscaVeiculo`), `jogo/efeitos.py` (acrescentar `GolpeClaude`)
- Test: `testes/test_armas.py`

**Interfaces:**
- Consumes: `ArmaDeDisparo`, `ArmaDeContato`, `ProjetilDoHeroi`, `ProjetilDivisivel`, `Ajudante`, `Jogo` (buscas e `causar_dano`), fixture `jogo_limpo`.
- Produces: `MascoteChatGPT` (`CHANCE_ALUCINAR = 0.15`, `ALCANCE = 520`), `MascoteClaude` (`progresso` 0..1, `ALCANCE = 600`), `Gemini`, `FuscaAzul`; `TiroChatGPT(posicao, velocidade, dano, alucinado=False)`, `EstrelaGemini(ProjetilDivisivel)`; `MascoteFlutuante(dono, imagem, altura, deslocamento, barra=None)` (atributo `deslocamento` mutável; `barra` é função que devolve 0..1 ou None), `FuscaVeiculo(posicao, sentido, possessao, dano)` (sentido +1 vai para a direita); `GolpeClaude(posicao, raio)`.

- [ ] **Step 1: Testes que falham**

`testes/test_armas.py`:
```python
import pygame
import pytest

from jogo.ajudantes.ajudantes import FuscaVeiculo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.inimigos.bug import Bug
from jogo.projeteis.projeteis import EstrelaGemini, TiroChatGPT

NOVAS = [MascoteChatGPT, MascoteClaude, Gemini, FuscaAzul]


def parado(bug):
    bug.velocidade = 0
    return bug


@pytest.mark.parametrize("classe", NOVAS)
def test_tabelas_de_atributos(classe):
    for valores in classe.ATRIBUTOS.values():
        assert len(valores) == classe.NIVEL_MAXIMO
    assert len(classe.MELHORIAS) == classe.NIVEL_MAXIMO - 1
    assert classe.NOME and classe.DESCRICAO and classe.ICONE


def test_chatgpt_atira_no_mais_proximo_e_nao_atira_sem_alvo(jogo_limpo, monkeypatch):
    monkeypatch.setattr(MascoteChatGPT, "CHANCE_ALUCINAR", 0.0)
    jogo = jogo_limpo()
    arma = MascoteChatGPT()
    arma.atualizar(0.0, jogo, jogo.jogador)
    jogo._incorporar_novas()
    assert not any(isinstance(e, TiroChatGPT) for e in jogo.entidades)
    jogo.adicionar(parado(Bug(jogo.jogador.posicao + (200, 0))))
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    assert arma.disparar(jogo, jogo.jogador)
    jogo._incorporar_novas()
    tiros = [e for e in jogo.entidades if isinstance(e, TiroChatGPT)]
    assert len(tiros) == 1 and tiros[0].velocidade.x > 0


def test_chatgpt_alucinado_da_dano_dobrado(jogo_limpo, monkeypatch):
    jogo = jogo_limpo()
    monkeypatch.setattr(MascoteChatGPT, "CHANCE_ALUCINAR", 1.0)
    arma = MascoteChatGPT()
    arma.atualizar(0.0, jogo, jogo.jogador)
    jogo.adicionar(parado(Bug(jogo.jogador.posicao + (200, 0))))
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    arma.disparar(jogo, jogo.jogador)
    jogo._incorporar_novas()
    tiro = [e for e in jogo.entidades if isinstance(e, TiroChatGPT)][0]
    assert tiro.alucinado and tiro.dano == pytest.approx(arma.valor("dano") * 2)


def test_claude_pensa_e_golpeia_o_inimigo_com_mais_vida(jogo_limpo):
    jogo = jogo_limpo()
    fraco = parado(Bug(jogo.jogador.posicao + (200, 0)))
    forte = parado(Bug(jogo.jogador.posicao + (-200, 0), escala=40))
    jogo.adicionar(fraco)
    jogo.adicionar(forte)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    arma = MascoteClaude()
    arma.atualizar(1.0, jogo, jogo.jogador)
    assert 0 < arma.progresso < 1
    arma.atualizar(5.0, jogo, jogo.jogador)
    assert arma.progresso == 0
    assert forte.vida < forte.vida_maxima
    assert fraco.vida == fraco.vida_maxima


def test_estrela_gemini_se_divide_ao_acertar(jogo_limpo):
    jogo = jogo_limpo()
    jogo.adicionar(parado(Bug(jogo.jogador.posicao + (100, 0), escala=20)))
    jogo.adicionar(EstrelaGemini(jogo.jogador.posicao + (60, 0), (380, 0), 10, geracoes=1))
    for _ in range(10):
        jogo.atualizar(1 / 60)
    assert sum(isinstance(e, EstrelaGemini) for e in jogo.entidades) == 2


def test_gemini_dispara_estrela_com_geracoes_do_nivel(jogo_limpo):
    jogo = jogo_limpo()
    arma = Gemini()
    assert arma.disparar(jogo, jogo.jogador)
    jogo._incorporar_novas()
    estrela = [e for e in jogo.entidades if isinstance(e, EstrelaGemini)][0]
    assert estrela.geracoes == arma.valor("geracoes")


def test_fusca_atravessa_a_tela_e_possui_inimigos(jogo_limpo):
    jogo = jogo_limpo()
    bug = parado(Bug(jogo.jogador.posicao + (0, 150), escala=50))
    jogo.adicionar(bug)
    tela = jogo.camera.retangulo
    jogo.adicionar(FuscaVeiculo((tela.left - 100, bug.posicao.y), 1, possessao=3.0, dano=8))
    for _ in range(200):
        jogo.atualizar(1 / 60)
    assert bug.possuido > 0
    assert not any(isinstance(e, FuscaVeiculo) for e in jogo.entidades)


def test_arma_fusca_solta_fuscas_de_tempos_em_tempos(jogo_limpo):
    jogo = jogo_limpo()
    arma = FuscaAzul()
    arma.atualizar(10.0, jogo, jogo.jogador)
    jogo._incorporar_novas()
    assert sum(isinstance(e, FuscaVeiculo) for e in jogo.entidades) == arma.valor("quantidade")


def test_possuido_soca_outro_inimigo(jogo_limpo):
    jogo = jogo_limpo()
    possuido = Bug(jogo.jogador.posicao + (300, 0))
    vitima = parado(Bug(jogo.jogador.posicao + (330, 0), escala=10))
    jogo.adicionar(possuido)
    jogo.adicionar(vitima)
    possuido.possuir(3)
    for _ in range(60):
        jogo.atualizar(1 / 60)
    assert vitima.vida < vitima.vida_maxima
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_armas.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.armas.chatgpt'`

- [ ] **Step 3: Acrescentar projéteis, ajudantes e efeito**

Ao fim de `jogo/projeteis/projeteis.py`:
```python
class TiroChatGPT(ProjetilDoHeroi):
    """Bolinha de energia do mascote. Quando alucinado, é rosa e com '?'."""

    DURACAO = 1.4

    def __init__(self, posicao, velocidade, dano, alucinado=False):
        super().__init__(posicao, velocidade, dano, raio=8)
        self.alucinado = alucinado

    def desenhar(self, tela, camera):
        c = camera.para_tela(self.posicao)
        cor = (255, 110, 200) if self.alucinado else (120, 240, 200)
        pygame.draw.circle(tela, (*cor, 255), (round(c.x), round(c.y)), 8)
        pygame.draw.circle(tela, (255, 255, 255), (round(c.x), round(c.y)), 4)
        if self.alucinado:
            marca = Recursos.fonte(14).render("?", True, (255, 255, 255))
            tela.blit(marca, marca.get_rect(center=(round(c.x), round(c.y - 14))))


class EstrelaGemini(ProjetilDivisivel):
    IMAGEM = "sprites/estrela_gemini.png"
    ALTURA = 26
    DURACAO = 1.8

    def angulo_desenho(self):
        return self.tempo * 540
```

Ao fim de `jogo/ajudantes/ajudantes.py`:
```python
class MascoteFlutuante(Ajudante):
    """Mascote que flutua perto do herói (ChatGPT, Claude). Pode mostrar uma barrinha."""

    camada = 2

    def __init__(self, dono, imagem, altura, deslocamento, barra=None):
        super().__init__(dono.posicao + deslocamento, 14)
        self.dono = dono
        self.imagem = imagem
        self.altura = altura
        self.deslocamento = pygame.Vector2(deslocamento)
        self.barra = barra
        self.tempo = 0.0

    def atualizar(self, dt, jogo):
        self.tempo += dt
        alvo = self.dono.posicao + self.deslocamento + pygame.Vector2(0, math.sin(self.tempo * 3) * 6)
        self.posicao += (alvo - self.posicao) * min(1.0, dt * 8)

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.imagem, self.altura)
        desenhar_sprite(tela, camera, imagem, self.posicao, sombra=False)
        if self.barra is not None:
            c = camera.para_tela(self.posicao)
            fundo = pygame.Rect(0, 0, 34, 5)
            fundo.midtop = (round(c.x), round(c.y - self.altura / 2 - 10))
            pygame.draw.rect(tela, (20, 16, 30), fundo.inflate(2, 2))
            cheio = fundo.copy()
            cheio.width = round(fundo.width * self.barra())
            pygame.draw.rect(tela, (240, 140, 70), cheio)


class FuscaVeiculo(Ajudante):
    """Fusca azul que atravessa a tela buzinando e possui quem atropela."""

    IMAGEM = "sprites/fusca.png"
    ALTURA = 56
    VELOCIDADE = 650

    def __init__(self, posicao, sentido, possessao, dano):
        super().__init__(posicao, 34)
        self.sentido = sentido
        self.possessao = possessao
        self.dano = dano
        self.tempo = 0.0
        self._atingidos = set()

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.posicao.x += self.sentido * self.VELOCIDADE * dt
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if id(inimigo) in self._atingidos:
                continue
            self._atingidos.add(id(inimigo))
            inimigo.possuir(self.possessao)
            jogo.causar_dano(inimigo, self.dano, pygame.Vector2(self.sentido, -0.3))
        if self.tempo > 0.5 and not jogo.camera.visivel(self.posicao, 300):
            self.remover()

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.IMAGEM, self.ALTURA)
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.sentido < 0,
                        deslocamento_y=abs(math.sin(self.tempo * 30)) * 2)
```

Ao fim de `jogo/efeitos.py`:
```python
class GolpeClaude(Efeito):
    """Estrela laranja que explode onde o Claude bateu."""

    def __init__(self, posicao, raio):
        super().__init__(posicao, 0.35, raio)

    def desenhar(self, tela, camera):
        c = camera.para_tela(self.posicao)
        r = self.raio * (0.5 + 0.7 * self.fracao)
        alfa = int(255 * (1 - self.fracao))
        lado = int(self.raio * 3)
        sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
        meio = pygame.Vector2(lado / 2, lado / 2)
        pontas = []
        for i in range(8):
            distancia = r if i % 2 == 0 else r * 0.35
            pontas.append(meio + pygame.Vector2(distancia, 0).rotate(i * 45 + 22.5))
        pygame.draw.polygon(sup, (240, 130, 60, alfa), pontas)
        pygame.draw.circle(sup, (255, 230, 200, alfa), meio, int(r * 0.25))
        tela.blit(sup, sup.get_rect(center=(round(c.x), round(c.y))))
```

- [ ] **Step 4: Implementar as quatro armas**

`jogo/armas/chatgpt.py`:
```python
import pygame

from jogo.ajudantes.ajudantes import MascoteFlutuante
from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import TiroChatGPT


class MascoteChatGPT(ArmaDeDisparo):
    NOME = "Mascote do ChatGPT"
    ICONE = "sprites/chatgpt.png"
    DESCRICAO = "Atira no inimigo mais próximo. Às vezes alucina e atira para qualquer lado, com dano dobrado."
    ATRIBUTOS = {
        "dano": (9, 11, 13, 15, 17, 20, 24),
        "quantidade": (1, 1, 2, 2, 2, 3, 3),
        "recarga": (0.9, 0.85, 0.85, 0.75, 0.7, 0.65, 0.55),
    }
    MELHORIAS = (
        "Mais dano.",
        "Mais 1 disparo.",
        "Mais dano e recarga menor.",
        "Mais dano.",
        "Mais 1 disparo.",
        "Mais dano e recarga menor.",
    )
    CHANCE_ALUCINAR = 0.15
    ALCANCE = 520
    VELOCIDADE = 560
    DESLOCAMENTO = (-38, -46)

    def __init__(self):
        super().__init__()
        self.mascote = None

    def atualizar(self, dt, jogo, dono):
        if self.mascote is None:
            self.mascote = MascoteFlutuante(dono, self.ICONE, 34, self.DESLOCAMENTO)
            jogo.adicionar(self.mascote)
        super().atualizar(dt, jogo, dono)

    def disparar(self, jogo, dono):
        origem = self.mascote.posicao if self.mascote else dono.posicao
        alvo = jogo.inimigo_mais_proximo(origem, self.ALCANCE)
        if alvo is None:
            return False
        rumo = alvo.posicao - origem
        rumo = rumo.normalize() if rumo.length_squared() > 0 else pygame.Vector2(1, 0)
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            alucinou = jogo.rng.random() < self.CHANCE_ALUCINAR
            if alucinou:
                direcao = pygame.Vector2(1, 0).rotate(jogo.rng.uniform(0, 360))
            else:
                direcao = rumo.rotate((i - (quantidade - 1) / 2) * 8)
            dano = self.valor("dano") * dono.multiplicador_dano * (2 if alucinou else 1)
            jogo.adicionar(TiroChatGPT(origem, direcao * self.VELOCIDADE, dano, alucinado=alucinou))
        Recursos.tocar("disparo", 0.12)
        return True

    def ao_remover(self, jogo):
        if self.mascote is not None:
            self.mascote.remover()
            self.mascote = None
```

`jogo/armas/claude.py`:
```python
from jogo.ajudantes.ajudantes import MascoteFlutuante
from jogo.armas.arma import ArmaDeContato
from jogo.efeitos import GolpeClaude
from jogo.nucleo.recursos import Recursos


class MascoteClaude(ArmaDeContato):
    NOME = "Mascote do Claude"
    ICONE = "sprites/claude.png"
    DESCRICAO = "Pensa por um instante e acerta um golpe forte no inimigo com mais vida."
    ATRIBUTOS = {
        "pensar": (3.0, 2.7, 2.4, 2.1, 1.8, 1.6, 1.3),
        "dano": (45, 55, 65, 80, 95, 115, 150),
        "area": (0, 0, 0, 70, 80, 95, 120),
    }
    MELHORIAS = (
        "Pensa mais rápido e bate mais forte.",
        "Pensa mais rápido e bate mais forte.",
        "O golpe passa a causar dano em área.",
        "Pensa mais rápido e área maior.",
        "Pensa mais rápido e área maior.",
        "Pensa bem mais rápido, área e dano maiores.",
    )
    ALCANCE = 600
    DESLOCAMENTO = (38, -46)

    def __init__(self):
        super().__init__()
        self.progresso = 0.0
        self.mascote = None

    def atualizar(self, dt, jogo, dono):
        if self.mascote is None:
            self.mascote = MascoteFlutuante(dono, self.ICONE, 34, self.DESLOCAMENTO, barra=lambda: self.progresso)
            jogo.adicionar(self.mascote)
        self.progresso = min(1.0, self.progresso + dt / (self.valor("pensar") * dono.mult_recarga))
        if self.progresso < 1.0:
            return
        alvo = jogo.inimigo_com_mais_vida(dono.posicao, self.ALCANCE)
        if alvo is not None:
            self._golpear(jogo, dono, alvo)
            self.progresso = 0.0

    def _golpear(self, jogo, dono, alvo):
        dano = self.valor("dano") * dono.multiplicador_dano
        area = self.valor("area")
        centro = alvo.posicao.copy()
        jogo.causar_dano(alvo, dano, forte=True)
        jogo.adicionar(GolpeClaude(centro, max(area, 40)))
        if area:
            for outro in jogo.inimigos_proximos(centro, area):
                if outro is not alvo:
                    jogo.causar_dano(outro, dano * 0.5, outro.posicao - centro)
        Recursos.tocar("claude", 0.4)

    def ao_remover(self, jogo):
        if self.mascote is not None:
            self.mascote.remover()
            self.mascote = None
```

`jogo/armas/gemini.py`:
```python
import pygame

from jogo.armas.arma import ArmaDeDisparo
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import EstrelaGemini


class Gemini(ArmaDeDisparo):
    NOME = "Gemini"
    ICONE = "sprites/estrela_gemini.png"
    DESCRICAO = "Atira uma estrela que se divide em duas ao acertar. Gêmeos, entendeu?"
    ATRIBUTOS = {
        "dano": (12, 14, 16, 18, 20, 23, 27),
        "quantidade": (1, 1, 1, 2, 2, 2, 3),
        "geracoes": (1, 1, 2, 2, 2, 3, 3),
        "recarga": (1.3, 1.2, 1.2, 1.1, 1.0, 1.0, 0.9),
    }
    MELHORIAS = (
        "Mais dano e recarga menor.",
        "As estrelas se dividem mais uma vez.",
        "Mais 1 estrela.",
        "Mais dano e recarga menor.",
        "As estrelas se dividem mais uma vez.",
        "Mais 1 estrela e mais dano.",
    )
    VELOCIDADE = 380
    ALCANCE = 600

    def disparar(self, jogo, dono):
        alvo = jogo.inimigo_mais_proximo(dono.posicao, self.ALCANCE)
        rumo = (alvo.posicao - dono.posicao) if alvo is not None else pygame.Vector2(dono.direcao_mira)
        rumo = rumo.normalize() if rumo.length_squared() > 0 else pygame.Vector2(1, 0)
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            direcao = rumo.rotate((i - (quantidade - 1) / 2) * 20)
            jogo.adicionar(EstrelaGemini(dono.posicao, direcao * self.VELOCIDADE,
                                         self.valor("dano") * dono.multiplicador_dano, geracoes=self.valor("geracoes")))
        Recursos.tocar("disparo", 0.12)
        return True
```

`jogo/armas/fusca.py`:
```python
from jogo.ajudantes.ajudantes import FuscaVeiculo
from jogo.armas.arma import ArmaDeContato
from jogo.nucleo.recursos import Recursos


class FuscaAzul(ArmaDeContato):
    NOME = "Fusca Azul"
    ICONE = "sprites/fusca.png"
    DESCRICAO = "Um fusca azul atravessa a tela. Quem é atropelado sai socando os outros inimigos."
    ATRIBUTOS = {
        "recarga": (7.0, 6.5, 6.0, 5.5, 5.0, 4.5, 3.5),
        "quantidade": (1, 1, 2, 2, 2, 3, 3),
        "possessao": (3.0, 3.5, 3.5, 4.0, 4.5, 5.0, 6.0),
        "dano": (8, 10, 12, 14, 16, 18, 22),
    }
    MELHORIAS = (
        "Possessão mais longa e recarga menor.",
        "Mais 1 fusca.",
        "Possessão mais longa e recarga menor.",
        "Possessão mais longa e recarga menor.",
        "Mais 1 fusca e possessão mais longa.",
        "Possessão bem mais longa e recarga menor.",
    )

    def __init__(self):
        super().__init__()
        self._espera = 2.0

    def atualizar(self, dt, jogo, dono):
        self._espera -= dt
        if self._espera <= 0:
            self._soltar(jogo, dono)
            self._espera = self.valor("recarga") * dono.mult_recarga

    def _soltar(self, jogo, dono):
        tela = jogo.camera.retangulo
        for _ in range(self.valor("quantidade")):
            da_esquerda = jogo.rng.random() < 0.5
            y = jogo.rng.uniform(tela.top + 60, tela.bottom - 40)
            x = tela.left - 120 if da_esquerda else tela.right + 120
            jogo.adicionar(FuscaVeiculo((x, y), 1 if da_esquerda else -1, self.valor("possessao"),
                                        self.valor("dano") * dono.multiplicador_dano))
        Recursos.tocar("buzina", 0.5)
```

- [ ] **Step 5: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Armas Mascote do ChatGPT, Mascote do Claude, Gemini e Fusca Azul

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 14: Itens, colabs e progressão (cartas de nível e baú)

**Files:**
- Create: `jogo/itens/itens.py`, `jogo/armas/colabs.py`, `jogo/progressao.py`
- Modify: `jogo/jogador/jogador.py` (método `aplicar_colab`), `jogo/projeteis/projeteis.py` (acrescentar `CobraGemea`), `jogo/ajudantes/ajudantes.py` (acrescentar `FuscaCircular`), `jogo/efeitos.py` (acrescentar `RaioDebate`)
- Test: `testes/test_progressao.py`

**Interfaces:**
- Consumes: `Item`, `Arma`, `ArmaDeDisparo`, `ArmaDeContato`, armas das Tasks 7 e 13, `MascoteFlutuante`, `Colisao`.
- Produces:
  - Itens: `CadernoDeResumos`, `Energetico`, `MarmitaDoRU`, `MochilaPesada`, `FoneDeOuvido`, `RelogioDePulso`, `GarrafaTermica`; `ITENS` (tupla das classes).
  - `Colab(Arma)` (abstrata; `NIVEL_MAXIMO = 1`, `INGREDIENTES`, `RECEITAS`), `Colab.colabs_disponiveis(armas) -> list[type]`, `Colab.ingredientes_em(receita, armas) -> list[Arma]` (ambos `@staticmethod`); `CarameloNoFusca`, `CobrasGemeas`, `DebateDasIAs`.
  - `Jogador.aplicar_colab(receita, jogo)`.
  - `Opcao(titulo, descricao, icone, rotulo, tipo, acao)` (dataclass; `tipo` em `"colab" | "melhoria" | "nova" | "lanche"`; `aplicar(jogador, jogo)`); `Progressao.ARMAS`, `Progressao.ITENS`, `Progressao.candidatas(jogador)`, `Progressao.gerar_opcoes(jogador, rng, quantidade=3)`, `Progressao.premio_bau(jogador, rng)`, `Progressao.opcao_lanche()` (todos `@staticmethod`).

- [ ] **Step 1: Testes que falham**

`testes/test_progressao.py`:
```python
import random

import pytest

from jogo.armas.caramelo import Caramelo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.cobra_python import CobraPython
from jogo.armas.colabs import CarameloNoFusca, Colab, CobrasGemeas, DebateDasIAs
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.itens.itens import ITENS, FoneDeOuvido, GarrafaTermica, MarmitaDoRU, MochilaPesada, RelogioDePulso
from jogo.jogador.alunos import AlunoAgil, AlunoResistente
from jogo.progressao import Progressao


def no_maximo(arma):
    while not arma.no_maximo:
        arma.subir_nivel()
    return arma


def test_tabelas_dos_itens():
    assert len(ITENS) == 7
    for classe in ITENS:
        assert len(classe.MELHORIAS) == classe.NIVEL_MAXIMO - 1
        assert classe.NOME and classe.DESCRICAO and classe.ICONE


def test_efeitos_dos_itens():
    j = AlunoAgil((0, 0))
    for classe in (FoneDeOuvido, RelogioDePulso, GarrafaTermica, MarmitaDoRU, MochilaPesada):
        j.adicionar_item(classe())
    assert j.alcance_coleta == pytest.approx(90 * 1.3)
    assert j.mult_recarga == pytest.approx(0.92)
    assert j.mult_cafe == pytest.approx(1.25)
    assert j.regeneracao == pytest.approx(1 / 3)
    assert j.vida_maxima == 100


def test_colab_so_aparece_com_as_duas_armas_no_maximo():
    armas = [Caramelo(), FuscaAzul()]
    assert Colab.colabs_disponiveis(armas) == []
    no_maximo(armas[0])
    assert Colab.colabs_disponiveis(armas) == []
    no_maximo(armas[1])
    assert Colab.colabs_disponiveis(armas) == [CarameloNoFusca]


def test_receitas_das_tres_colabs():
    assert set(CarameloNoFusca.INGREDIENTES) == {Caramelo, FuscaAzul}
    assert set(CobrasGemeas.INGREDIENTES) == {CobraPython, Gemini}
    assert set(DebateDasIAs.INGREDIENTES) == {MascoteChatGPT, MascoteClaude}


def test_aplicar_colab_troca_as_duas_armas_pela_colab(jogo_limpo):
    jogo = jogo_limpo(AlunoResistente)
    j = jogo.jogador
    no_maximo(j.armas[0])
    j.adicionar_arma(no_maximo(FuscaAzul()))
    j.aplicar_colab(CarameloNoFusca, jogo)
    assert [type(a) for a in j.armas] == [CarameloNoFusca]
    assert {Caramelo, FuscaAzul} <= j.armas_em_colab
    for _ in range(30):
        jogo.atualizar(1 / 60)


@pytest.mark.parametrize("receita", [CarameloNoFusca, CobrasGemeas, DebateDasIAs])
def test_cada_colab_funciona_na_partida(jogo_limpo, receita):
    jogo = jogo_limpo()
    jogo.jogador.armas = [receita()]
    from jogo.inimigos.bug import Bug
    for i in range(10):
        bug = Bug(jogo.jogador.posicao + (150 + i * 20, 40), escala=30)
        bug.velocidade = 0
        jogo.adicionar(bug)
    for _ in range(240):
        jogo.atualizar(1 / 60)
    assert any(b.vida < b.vida_maxima for b in jogo.inimigos)


def test_opcoes_de_nivel_sao_tres_e_validas():
    j = AlunoAgil((0, 0))
    opcoes = Progressao.gerar_opcoes(j, random.Random(1))
    assert len(opcoes) == 3
    assert len({o.titulo for o in opcoes}) == 3


def test_colab_disponivel_sempre_aparece_primeiro():
    j = AlunoAgil((0, 0))
    no_maximo(j.armas[0])
    j.adicionar_arma(no_maximo(Gemini()))
    opcoes = Progressao.gerar_opcoes(j, random.Random(5))
    assert opcoes[0].tipo == "colab"


def test_aplicar_opcoes_de_melhoria_e_de_arma_nova(jogo_limpo):
    jogo = jogo_limpo()
    j = jogo.jogador
    candidatas = Progressao.candidatas(j)
    melhoria = next(o for o in candidatas if o.tipo == "melhoria")
    melhoria.aplicar(j, jogo)
    assert j.armas[0].nivel == 2
    nova = next(o for o in candidatas if o.tipo == "nova" and o.titulo == "Gemini")
    nova.aplicar(j, jogo)
    assert isinstance(j.armas[-1], Gemini)


def test_sem_nada_para_oferecer_aparece_o_lanche(jogo_limpo):
    jogo = jogo_limpo()
    j = jogo.jogador
    j.armas = [CarameloNoFusca(), CobrasGemeas(), DebateDasIAs(), CarameloNoFusca(), CobrasGemeas(), DebateDasIAs()]
    j.itens = []
    for classe in ITENS[:6]:
        item = classe()
        item.nivel = item.NIVEL_MAXIMO
        j.itens.append(item)
    opcoes = Progressao.gerar_opcoes(j, random.Random(2))
    assert [o.tipo for o in opcoes] == ["lanche"]
    j.vida = 10
    opcoes[0].aplicar(j, jogo)
    assert j.vida == 40


def test_premio_do_bau_prefere_melhorar(jogo_limpo):
    jogo = jogo_limpo()
    premio = Progressao.premio_bau(jogo.jogador, random.Random(3))
    assert premio.tipo == "melhoria"
    premio.aplicar(jogo.jogador, jogo)
    assert jogo.jogador.armas[0].nivel == 2


def test_arma_que_virou_colab_nao_volta_como_nova():
    j = AlunoResistente((0, 0))
    j.armas_em_colab = {Caramelo, FuscaAzul}
    j.armas = []
    titulos = {o.titulo for o in Progressao.candidatas(j)}
    assert "Caramelo" not in titulos and "Fusca Azul" not in titulos
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_progressao.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.armas.colabs'`

- [ ] **Step 3: Implementar os itens**

`jogo/itens/itens.py`:
```python
"""Itens passivos. Cada um soma seu efeito em Jogador.recalcular_atributos()."""
from jogo.itens.item import Item


class CadernoDeResumos(Item):
    NOME = "Caderno de Resumos"
    DESCRICAO = "+10% de dano por nível."
    ICONE = "icones/caderno.png"
    MELHORIAS = ("+10% de dano.", "+10% de dano.")

    def aplicar(self, jogador):
        jogador.mult_dano += 0.10 * self.nivel


class Energetico(Item):
    NOME = "Energético"
    DESCRICAO = "+10% de velocidade por nível."
    ICONE = "icones/energetico.png"
    MELHORIAS = ("+10% de velocidade.", "+10% de velocidade.")

    def aplicar(self, jogador):
        jogador.mult_velocidade += 0.10 * self.nivel


class MarmitaDoRU(Item):
    NOME = "Marmita do RU"
    DESCRICAO = "Recupera vida aos pouquinhos."
    ICONE = "icones/marmita.png"
    MELHORIAS = ("Recupera vida mais rápido.", "Recupera 1 de vida por segundo.")
    REGENERACAO = (1 / 3, 1 / 2, 1.0)

    def aplicar(self, jogador):
        jogador.regeneracao += self.REGENERACAO[self.nivel - 1]


class MochilaPesada(Item):
    NOME = "Mochila Pesada"
    DESCRICAO = "+20 de vida máxima por nível."
    ICONE = "icones/mochila.png"
    MELHORIAS = ("+20 de vida máxima.", "+20 de vida máxima.")

    def aplicar(self, jogador):
        jogador.vida_maxima_extra += 20 * self.nivel


class FoneDeOuvido(Item):
    NOME = "Fone de Ouvido"
    DESCRICAO = "Puxa as notas de mais longe (+30% por nível)."
    ICONE = "icones/fone.png"
    MELHORIAS = ("+30% de alcance de coleta.", "+30% de alcance de coleta.")

    def aplicar(self, jogador):
        jogador.alcance_coleta *= 1 + 0.30 * self.nivel


class RelogioDePulso(Item):
    NOME = "Relógio de Pulso"
    DESCRICAO = "Armas e especial recarregam 8% mais rápido por nível."
    ICONE = "legado/itens/item_watch_l.png"
    MELHORIAS = ("-8% de recarga.", "-8% de recarga.")

    def aplicar(self, jogador):
        jogador.mult_recarga *= 1 - 0.08 * self.nivel


class GarrafaTermica(Item):
    NOME = "Garrafa Térmica"
    DESCRICAO = "+25% de café máximo e de recarga de café por nível."
    ICONE = "icones/garrafa.png"
    MELHORIAS = ("+25% de café.", "+25% de café.")

    def aplicar(self, jogador):
        jogador.mult_cafe *= 1 + 0.25 * self.nivel


ITENS = (CadernoDeResumos, Energetico, MarmitaDoRU, MochilaPesada, FoneDeOuvido, RelogioDePulso, GarrafaTermica)
```

- [ ] **Step 4: Acrescentar `CobraGemea`, `FuscaCircular` e `RaioDebate`**

Ao fim de `jogo/projeteis/projeteis.py`:
```python
class CobraGemea(MovimentoSerpente, ProjetilDivisivel):
    IMAGEM = "sprites/cobra.png"
    ALTURA = 22
    DURACAO = 1.6
```

Ao fim de `jogo/ajudantes/ajudantes.py`:
```python
class FuscaCircular(Ajudante):
    """O Caramelo dirigindo o fusca em volta do herói, atropelando e possuindo inimigos."""

    IMAGEM = "sprites/caramelo_no_fusca.png"
    ALTURA = 64
    RAIO_VOLTA = 230
    VELOCIDADE_ANGULAR = 1.8
    ESPERA_ATROPELO = 1.0

    def __init__(self, dono, arma):
        super().__init__(dono.posicao, 36)
        self.dono = dono
        self.arma = arma
        self.angulo = 0.0
        self.tempo = 0.0
        self.olhando_esquerda = False
        self._atropelados = {}

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.angulo += self.VELOCIDADE_ANGULAR * dt
        nova = self.dono.posicao + pygame.Vector2(math.cos(self.angulo), math.sin(self.angulo)) * self.RAIO_VOLTA
        self.olhando_esquerda = nova.x < self.posicao.x
        self.posicao = nova
        for chave in list(self._atropelados):
            self._atropelados[chave] -= dt
            if self._atropelados[chave] <= 0:
                del self._atropelados[chave]
        for inimigo in jogo.inimigos_proximos(self.posicao, self.raio):
            if id(inimigo) in self._atropelados:
                continue
            self._atropelados[id(inimigo)] = self.ESPERA_ATROPELO
            inimigo.possuir(self.arma.valor("possessao"))
            jogo.causar_dano(inimigo, self.arma.valor("dano") * self.dono.multiplicador_dano,
                             inimigo.posicao - self.dono.posicao)

    def desenhar(self, tela, camera):
        imagem = Recursos.imagem(self.IMAGEM, self.ALTURA)
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda,
                        deslocamento_y=abs(math.sin(self.tempo * 30)) * 2)
```

Ao fim de `jogo/efeitos.py`:
```python
class RaioDebate(Efeito):
    """Raio entre os dois mascotes do Debate das IAs. Dura enquanto a colab existir."""

    camada = 2

    def __init__(self, mascote_a, mascote_b):
        super().__init__(mascote_a.posicao, float("inf"))
        self.a = mascote_a
        self.b = mascote_b

    def ao_atualizar(self, dt, jogo):
        self.posicao = (self.a.posicao + self.b.posicao) / 2

    def desenhar(self, tela, camera):
        inicio = camera.para_tela(self.a.posicao)
        fim = camera.para_tela(self.b.posicao)
        tremor = 2 + 2 * math.sin(self.tempo * 50)
        pygame.draw.line(tela, (240, 130, 60), inicio, fim, int(8 + tremor))
        pygame.draw.line(tela, (120, 240, 200), inicio, fim, 4)
        pygame.draw.line(tela, (255, 255, 255), inicio, fim, 2)
```

- [ ] **Step 5: Implementar as colabs e o método do jogador**

`jogo/armas/colabs.py`:
```python
"""Colabs: duas armas no nível máximo se juntam numa arma nova."""
from abc import ABC

import pygame

from jogo.ajudantes.ajudantes import FuscaCircular, MascoteFlutuante
from jogo.armas.arma import Arma, ArmaDeContato, ArmaDeDisparo
from jogo.armas.caramelo import Caramelo
from jogo.armas.chatgpt import MascoteChatGPT
from jogo.armas.claude import MascoteClaude
from jogo.armas.cobra_python import CobraPython
from jogo.armas.fusca import FuscaAzul
from jogo.armas.gemini import Gemini
from jogo.efeitos import RaioDebate
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.projeteis import CobraGemea


class Colab(Arma, ABC):
    NIVEL_MAXIMO = 1
    MELHORIAS = ()
    INGREDIENTES = ()
    RECEITAS = []

    @staticmethod
    def colabs_disponiveis(armas):
        """Receitas cujas duas armas estão no nível máximo."""
        disponiveis = []
        for receita in Colab.RECEITAS:
            if all(any(type(a) is ingrediente and a.no_maximo for a in armas) for ingrediente in receita.INGREDIENTES):
                disponiveis.append(receita)
        return disponiveis

    @staticmethod
    def ingredientes_em(receita, armas):
        return [a for a in armas if type(a) in receita.INGREDIENTES]


class CarameloNoFusca(ArmaDeContato, Colab):
    NOME = "Caramelo no Fusca"
    ICONE = "sprites/caramelo_no_fusca.png"
    DESCRICAO = "O Caramelo assume o volante e dá voltas na arena atropelando e possuindo inimigos."
    INGREDIENTES = (Caramelo, FuscaAzul)
    ATRIBUTOS = {"dano": (30,), "possessao": (5.0,)}

    def __init__(self):
        super().__init__()
        self.fusca = None

    def atualizar(self, dt, jogo, dono):
        if self.fusca is None:
            self.fusca = FuscaCircular(dono, self)
            jogo.adicionar(self.fusca)

    def ao_remover(self, jogo):
        if self.fusca is not None:
            self.fusca.remover()
            self.fusca = None


class CobrasGemeas(ArmaDeDisparo, Colab):
    NOME = "Cobras Gêmeas"
    ICONE = "icones/cobras_gemeas.png"
    DESCRICAO = "Quatro cobras por disparo, e cada uma se divide em duas ao acertar."
    INGREDIENTES = (CobraPython, Gemini)
    ATRIBUTOS = {"dano": (24,), "quantidade": (4,), "geracoes": (2,), "recarga": (0.7,)}
    MUNICAO_BASE = 16
    VELOCIDADE = 430

    def disparar(self, jogo, dono):
        quantidade = self.valor("quantidade")
        for i in range(quantidade):
            direcao = dono.direcao_mira.rotate((i - (quantidade - 1) / 2) * 14)
            jogo.adicionar(CobraGemea(dono.posicao, direcao * self.VELOCIDADE,
                                      self.valor("dano") * dono.multiplicador_dano, geracoes=self.valor("geracoes")))
        Recursos.tocar("disparo", 0.15)
        return True


class DebateDasIAs(ArmaDeContato, Colab):
    NOME = "Debate das IAs"
    ICONE = "icones/debate.png"
    DESCRICAO = "ChatGPT e Claude discutem em volta de você, e o raio entre eles acerta tudo no meio."
    INGREDIENTES = (MascoteChatGPT, MascoteClaude)
    ATRIBUTOS = {"dano": (14,), "raio": (150,), "velocidade": (1.6,)}
    INTERVALO = 0.15

    def __init__(self):
        super().__init__()
        self.mascotes = None
        self.raio_visual = None
        self.angulo = 0.0
        self._espera = 0.0

    def atualizar(self, dt, jogo, dono):
        if self.mascotes is None:
            self.mascotes = (MascoteFlutuante(dono, MascoteChatGPT.ICONE, 34, (0, 0)),
                             MascoteFlutuante(dono, MascoteClaude.ICONE, 34, (0, 0)))
            self.raio_visual = RaioDebate(*self.mascotes)
            for e in (*self.mascotes, self.raio_visual):
                jogo.adicionar(e)
        self.angulo += self.valor("velocidade") * dt
        braco = pygame.Vector2(self.valor("raio"), 0).rotate_rad(self.angulo)
        self.mascotes[0].deslocamento = braco
        self.mascotes[1].deslocamento = -braco
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.INTERVALO
        inicio, fim = self.mascotes[0].posicao, self.mascotes[1].posicao
        for inimigo in jogo.inimigos_proximos(dono.posicao, self.valor("raio") + 20):
            if Colisao.segmento_acerta_circulo(inicio, fim, 16, inimigo.posicao, inimigo.raio):
                jogo.causar_dano(inimigo, self.valor("dano") * dono.multiplicador_dano)

    def ao_remover(self, jogo):
        if self.mascotes is not None:
            for e in (*self.mascotes, self.raio_visual):
                e.remover()
            self.mascotes = None


Colab.RECEITAS = [CarameloNoFusca, CobrasGemeas, DebateDasIAs]
```

Acrescentar a `Jogador` (em `jogo/jogador/jogador.py`, depois de `remover_arma`):
```python
    def aplicar_colab(self, receita, jogo):
        """Troca as duas armas da receita pela colab."""
        from jogo.armas.colabs import Colab
        for arma in Colab.ingredientes_em(receita, self.armas):
            self.armas_em_colab.add(type(arma))
            self.remover_arma(arma, jogo)
        self.armas.append(receita())
```

- [ ] **Step 6: Implementar a progressão**

`jogo/progressao.py`:
```python
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
```

- [ ] **Step 7: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "Itens passivos, colabs e cartas de nível

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 15: Linha do tempo completa da fase e desempenho

**Files:**
- Modify: `jogo/fase.py` (substituir a classe `SemanaDeProvas`)
- Test: `testes/test_fase.py`

**Interfaces:**
- Consumes: `Fase`, `EventoDaFase`, inimigos registrados.
- Produces: `SemanaDeProvas` com as 8 apresentações, mini-chefes aos 300 s e 600 s, formações a cada 120 s e o Professor aos 900 s.

- [ ] **Step 1: Testes que falham**

`testes/test_fase.py`:
```python
import time

import pygame

from jogo.coletaveis.coletaveis import Nota
from jogo.fase import SemanaDeProvas
from jogo.inimigos.bug import Bug
from jogo.inimigos.professor import Professor
from jogo.jogador.alunos import AlunoAgil
from jogo.jogo import Jogo


def jogo_imortal():
    jogo = Jogo(AlunoAgil, semente=11)
    jogo.jogador.vida_maxima = 10 ** 9
    jogo.jogador.vida = 10 ** 9
    return jogo


def pular_para(jogo, segundos):
    jogo.fase.tempo = segundos - 0.01
    jogo.atualizar(0.02)


def test_lacaios_sao_apresentados_na_ordem():
    fase = SemanaDeProvas()
    nomes = [nome for _, nome in fase.APRESENTACOES]
    assert nomes == ["bug", "calculadora", "mouse", "caixinha", "pi", "ponteiro", "pilha", "pente_ram"]
    jogo = jogo_imortal()
    pular_para(jogo, 280)
    assert jogo.fase.ativos == ["bug", "calculadora", "mouse", "caixinha"]


def test_mini_chefes_aos_5_e_aos_10_minutos():
    jogo = jogo_imortal()
    pular_para(jogo, 300)
    jogo._incorporar_novas()
    gigantes = [e for e in jogo.inimigos if e.gigante]
    assert len(gigantes) == 1 and gigantes[0].CHAVE == "calculadora"
    pular_para(jogo, 600)
    gigantes = [e for e in jogo.inimigos if e.gigante]
    assert {g.CHAVE for g in gigantes} == {"calculadora", "pente_ram"}


def test_formacao_aos_2_minutos():
    jogo = jogo_imortal()
    antes = len(jogo.inimigos)
    pular_para(jogo, 120)
    assert len(jogo.inimigos) >= antes + 20


def test_professor_aos_15_minutos():
    jogo = jogo_imortal()
    pular_para(jogo, 900)
    assert isinstance(jogo.chefe, Professor)
    assert jogo.fase.chefe_apareceu
    assert any("Professor" in texto for texto, _ in jogo.anuncios)


def test_quadro_continua_rapido_com_muitas_entidades():
    jogo = jogo_imortal()
    for i in range(300):
        jogo.adicionar(Bug(jogo.jogador.posicao + pygame.Vector2(200 + (i % 30) * 25, 0).rotate(i * 7)))
    for i in range(400):
        jogo.adicionar(Nota(jogo.jogador.posicao + pygame.Vector2(600, 0).rotate(i), 1))
    jogo._incorporar_novas()
    tela = pygame.Surface((1280, 720))
    inicio = time.perf_counter()
    for _ in range(30):
        jogo.atualizar(1 / 60)
        jogo.desenhar(tela)
    media_ms = (time.perf_counter() - inicio) / 30 * 1000
    assert media_ms < 33, f"quadro médio de {media_ms:.1f} ms"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_fase.py -v`
Expected: FAIL nos testes de apresentação, mini-chefe, formação e Professor (a `SemanaDeProvas` provisória só tem o Bug). Se o teste de desempenho falhar, otimizar antes de seguir (ver Step 4).

- [ ] **Step 3: Substituir `SemanaDeProvas` em `jogo/fase.py`**

```python
class SemanaDeProvas(Fase):
    NOME = "Semana de Provas"
    DURACAO = 900
    APRESENTACOES = (
        (0, "bug"),
        (90, "calculadora"),
        (180, "mouse"),
        (270, "caixinha"),
        (360, "pi"),
        (450, "ponteiro"),
        (540, "pilha"),
        (630, "pente_ram"),
    )
    FORMACOES = ("bug", "calculadora", "mouse", "caixinha", "ponteiro", "pi", "bug")

    def criar_eventos(self):
        eventos = [
            EventoDaFase(300, lambda jogo: self.chamar_mini_chefe(jogo, "calculadora"), "Calculadora Gigante"),
            EventoDaFase(600, lambda jogo: self.chamar_mini_chefe(jogo, "pente_ram"), "Pente de RAM Gigante"),
            EventoDaFase(900, lambda jogo: self.chamar_chefe(jogo, "professor"), "Professor"),
        ]
        for i, nome in enumerate(self.FORMACOES):
            if i % 2 == 0:
                acao = lambda jogo, n=nome: self.formacao_circulo(jogo, n, 24)
            else:
                acao = lambda jogo, n=nome: self.formacao_parede(jogo, n, 20)
            eventos.append(EventoDaFase(120 * (i + 1), acao, f"Formação de {nome}"))
        return eventos
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam. Se `test_quadro_continua_rapido_com_muitas_entidades` passar de 33 ms: medir com `python -m cProfile -s cumtime` num script com o mesmo cenário e atacar o maior custo (candidatos de `_separar`, `TextoFlutuante` por acerto, ordenação em `desenhar`).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Linha do tempo completa da Semana de Provas

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 16: Arte restante (inimigos, professor, armas, ícones, título)

**Files:**
- Create: `assets/sprites/{calculadora,mouse,caixinha,pi,ponteiro,pilha,pente_ram,professor,chatgpt,claude,estrela_gemini,fusca,caramelo_no_fusca,folha_prova,logo}.png`, `assets/icones/{caderno,energetico,marmita,mochila,fone,garrafa,cobras_gemeas,debate}.png`, `assets/cenario/titulo_fundo.png`

**Interfaces:**
- Produces: arquivos nos caminhos já usados pelas classes das Tasks 12 a 14 e pelas cenas da Task 17.

Mesmo procedimento da Task 11 (prompt-base no começo de todo sprite, `background="transparent"`, `output_path="arte_bruta/<nome>.png"`, conferir cada prévia).

- [ ] **Step 1: Gerar os sprites dos inimigos e do professor**

| Arquivo bruto | Prompt (depois do prompt-base) |
|---|---|
| `calculadora.png` | Subject: an angry gray scientific calculator creature with little arms and legs, grumpy face drawn on its green LCD display, buttons on its body. |
| `mouse.png` | Subject: an old beige ball computer mouse running like a rat, its gray cable curling behind as a tail, small beady eyes, tiny pink feet. |
| `caixinha.png` | Subject: a cardboard box mimic creature with two curious eyes peeking from under the lid, small legs, a white label sticker on the front. |
| `pi.png` | Subject: the greek letter pi as a chubby yellow character, walking on the two legs of the letter, tiny striped party hat, dizzy happy face. |
| `ponteiro.png` | Subject: a white computer mouse pointer arrow cursor with a thick black outline, pointing up-left exactly like a standard arrow cursor, two small angry eyes. Do not face right. |
| `pilha.png` | Subject: an AA battery character standing upright, orange top and black body, angry face, small arms and legs, tiny yellow electric sparks. |
| `pente_ram.png` | Subject: a long green RAM memory stick lying horizontally, golden contacts along the bottom edge acting as many little legs like a centipede, a cute face at the right end. Side view. |
| `professor.png` | Subject: a generic university professor boss character, tall, round glasses, gray beard, tweed jacket with elbow patches, holding a stack of exam papers in one hand and a piece of chalk in the other, smug villain smile. Larger and more detailed than regular enemies. |

- [ ] **Step 2: Gerar armas, projéteis e ícones**

| Arquivo bruto | Prompt (depois do prompt-base) | Ferramenta |
|---|---|---|
| `chatgpt.png` | Subject: a small floating robot mascot inspired by the ChatGPT logo: a round black badge with the white interlocking hexagonal knot symbol as its face, two tiny glowing eyes, little hover sparkles. | generate |
| `claude.png` | Subject: a small cute orange blocky pixel creature mascot inspired by the Claude Code mascot: chunky terracotta-orange body, two simple black eyes, four short legs. | generate |
| `estrela_gemini.png` | Subject: a glowing four-pointed sparkle star with a blue to purple to pink gradient, inspired by the Gemini AI logo. | generate |
| `fusca.png` | Subject: a classic blue Volkswagen Beetle (fusca) car, side view facing right, cartoonish and bouncy, shiny chrome bumpers. | generate |
| `caramelo_no_fusca.png` | Image 1 is a blue beetle car, Image 2 is a caramel dog. Draw the same blue beetle car, same style, with the same caramel dog driving it, head and paws out of the driver window, happy tongue out. Side view facing right, transparent background. | edit (entradas: `arte_bruta/fusca.png`, `arte_bruta/caramelo.png`) |
| `folha_prova.png` | Subject: a single sheet of exam paper, slightly crumpled, with a big red circled zero grade and red marks. Flat top view. | generate |
| `icone_caderno.png` | Subject: game item icon, a spiral notebook with colorful sticky notes, square composition. | generate |
| `icone_energetico.png` | Subject: game item icon, an energy drink can with a lightning bolt, square composition. | generate |
| `icone_marmita.png` | Subject: game item icon, an aluminum lunch box (Brazilian marmita) with rice and beans, steaming, square composition. | generate |
| `icone_mochila.png` | Subject: game item icon, an overstuffed heavy school backpack with books sticking out, square composition. | generate |
| `icone_fone.png` | Subject: game item icon, over-ear headphones with musical notes, square composition. | generate |
| `icone_garrafa.png` | Subject: game item icon, a metal thermos bottle with coffee steam, square composition. | generate |
| `icone_cobras_gemeas.png` | Subject: game skill icon, two small Python-colored snakes (blue and yellow) intertwined around a four-pointed blue-purple sparkle star, square composition. | generate |
| `icone_debate.png` | Image 1 and Image 2 are two small mascots. Draw both mascots, same style, facing each other and arguing, with an electric beam crackling between them, square game icon, transparent background. | edit (entradas: `arte_bruta/chatgpt.png`, `arte_bruta/claude.png`) |

- [ ] **Step 3: Gerar fundo e logo do título**

Fundo (sem o prompt-base; `background="opaque"`, `aspect_ratio="16:9"`, `output_path="arte_bruta/titulo_fundo.png"`):

> 16-bit pixel art illustration, wide landscape, a Brazilian university campus courtyard at golden-hour sunset, modern low buildings, yellow ipê trees, students' backpacks on benches; in the distance a comical horde of cute monsters approaching: green beetle bugs, angry calculators, flying arrow cursors, an AA battery; warm saturated colors, lots of empty sky at the top for a title, no text.

Logo (`background="transparent"`, `output_path="arte_bruta/logo.png"`):

> Game title logo, the exact text "UFJ SURVIVORS" in big chunky pixel-art letters, golden yellow with thick dark brown outline and a small drop shadow, a tiny caramel dog peeking over the letters and a small blue-and-yellow snake curling around the last letter, transparent background, nothing else.

Se o texto do logo sair com letras erradas, gerar de novo (até 3 vezes); se continuar errado, não criar `logo.png` (a cena de título desenha o nome com a fonte do jogo).

- [ ] **Step 4: Reduzir para o tamanho do jogo**

```bash
P=".venv/bin/python ferramentas/preparar_arte.py"
for par in calculadora:46 mouse:34 caixinha:42 pi:46 ponteiro:34 pilha:44 pente_ram:30 professor:112 \
           chatgpt:34 claude:34 estrela_gemini:26 fusca:56 caramelo_no_fusca:64 folha_prova:26 logo:220; do
  nome=${par%%:*}; altura=${par##*:}
  [ -f arte_bruta/$nome.png ] && $P arte_bruta/$nome.png assets/sprites/$nome.png --altura $altura
done
for nome in caderno energetico marmita mochila fone garrafa cobras_gemeas debate; do
  $P arte_bruta/icone_$nome.png assets/icones/$nome.png --altura 64
done
$P arte_bruta/titulo_fundo.png assets/cenario/titulo_fundo.png --tela 1280x720
```

- [ ] **Step 5: Conferir no jogo**

Rodar a captura da Task 11 Step 4 com `cena.jogo.fase.tempo = 640` antes do laço (para aparecerem todos os lacaios) e com `cena.jogo.jogador.armas` incluindo `MascoteChatGPT()`, `MascoteClaude()`, `Gemini()`, `FuscaAzul()`; salvar em `arte_bruta/captura_completa.png` e abrir com Read. Verificar: cada inimigo reconhecível, tamanhos coerentes entre si, o Ponteiro aponta para onde voa. Ajustar alturas e regerar o que destoar.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Arte dos inimigos, do professor, das armas, dos ícones e do título

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 17: Telas de título, seleção, nível, baú, pausa, fim e ranking

**Files:**
- Create: `jogo/cenas/titulo.py`, `jogo/cenas/selecao.py`, `jogo/cenas/nivel.py`, `jogo/cenas/bau.py`, `jogo/cenas/pausa.py`, `jogo/cenas/fim.py`, `jogo/cenas/ranking.py`
- Modify: `jogo/cenas/widgets.py` (acrescentar `desenhar_fundo`), `jogo/cenas/partida.py` (imports diretos), `main.py` (começar no título)
- Test: `testes/test_telas.py`

**Interfaces:**
- Consumes: `Aplicacao`, `Cena`, widgets, `Progressao`, `HEROIS`, `Ranking`, `RegistroRanking`, `CURA_AO_PULAR`.
- Produces: `CenaTitulo(app)`, `CenaSelecao(app)`, `CenaNivel(app, jogo)`, `CenaBau(app, jogo)`, `CenaPausa(app, partida)`, `CenaFimDeJogo(app, jogo)`, `CenaRanking(app, destaque=None)`; `desenhar_fundo(tela, caminho, escuro=0)`.

- [ ] **Step 1: Testes que falham**

`testes/test_telas.py`:
```python
import pygame
import pytest

from jogo.aplicacao import Aplicacao
from jogo.cenas.bau import CenaBau
from jogo.cenas.fim import CenaFimDeJogo
from jogo.cenas.nivel import CenaNivel
from jogo.cenas.partida import CenaPartida
from jogo.cenas.pausa import CenaPausa
from jogo.cenas.ranking import CenaRanking
from jogo.cenas.selecao import CenaSelecao
from jogo.cenas.titulo import CenaTitulo
from jogo.jogador.alunos import AlunoAgil, AlunoResistente
from jogo.ranking import Ranking


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def texto(t):
    return pygame.event.Event(pygame.TEXTINPUT, text=t)


@pytest.fixture
def app(tmp_path):
    a = Aplicacao(pygame.Surface((1280, 720)))
    a.ranking = Ranking(tmp_path / "ranking.json")
    return a


def test_titulo_jogar_leva_a_selecao(app):
    app.trocar(CenaTitulo(app))
    app.passo(1 / 60, [])
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaSelecao)


def test_titulo_ranking_e_sair(app):
    app.trocar(CenaTitulo(app))
    app.passo(1 / 60, [tecla(pygame.K_DOWN), tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaRanking)
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert isinstance(app.cena_atual, CenaTitulo)
    app.passo(1 / 60, [tecla(pygame.K_UP), tecla(pygame.K_RETURN)])
    assert not app.rodando


def test_selecao_escolhe_o_segundo_aluno(app):
    app.trocar(CenaSelecao(app))
    app.passo(1 / 60, [tecla(pygame.K_RIGHT), tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaPartida)
    assert isinstance(app.cena_atual.jogo.jogador, AlunoResistente)


def test_selecao_esc_volta_ao_titulo(app):
    app.trocar(CenaSelecao(app))
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert isinstance(app.cena_atual, CenaTitulo)


def test_subir_de_nivel_abre_cartas_e_tecla_1_escolhe(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    partida.jogo.niveis_pendentes = 2
    app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaNivel)
    app.passo(1 / 60, [tecla(pygame.K_1)])
    assert partida.jogo.niveis_pendentes == 1
    app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaNivel)


def test_sortear_de_novo_e_pular(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    partida.jogo.niveis_pendentes = 1
    app.passo(1 / 60, [])
    app.passo(1 / 60, [tecla(pygame.K_r)])
    assert partida.jogo.sorteios_restantes == 2
    partida.jogo.jogador.vida = 10
    app.passo(1 / 60, [tecla(pygame.K_p)])
    assert partida.jogo.jogador.vida == 30
    assert app.cena_atual is partida


def test_bau_abre_aplica_premio_e_fecha(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    partida.jogo.baus_pendentes = 1
    app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaBau)
    for _ in range(80):
        app.passo(1 / 60, [])
    assert partida.jogo.jogador.armas[0].nivel == 2
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    assert app.cena_atual is partida and partida.jogo.baus_pendentes == 0


def test_pausa_alterna_mira_e_volta(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert isinstance(app.cena_atual, CenaPausa)
    tempo = partida.jogo.placar.tempo
    app.passo(1 / 60, [tecla(pygame.K_DOWN), tecla(pygame.K_RETURN)])
    assert app.mira_mouse
    assert partida.jogo.placar.tempo == tempo
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert app.cena_atual is partida


def test_fim_de_jogo_grava_nome_no_ranking(app):
    partida = CenaPartida(app, AlunoAgil)
    app.trocar(partida)
    partida.jogo.placar.adicionar_pontos(321)
    partida.jogo.terminar(False)
    for _ in range(100):
        app.passo(1 / 60, [])
    assert isinstance(app.cena_atual, CenaFimDeJogo)
    app.passo(1 / 60, [texto("A"), texto("n"), texto("a"), tecla(pygame.K_RETURN)])
    assert isinstance(app.cena_atual, CenaRanking)
    assert app.ranking.registros[0].nome == "Ana"
    assert Ranking(app.ranking.caminho).registros[0].nome == "Ana"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/bin/pytest testes/test_telas.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'jogo.cenas.bau'`

- [ ] **Step 3: `desenhar_fundo` e a partida com imports diretos**

Acrescentar ao fim de `jogo/cenas/widgets.py`:
```python
def desenhar_fundo(tela, caminho, escuro=0):
    """Fundo de tela cheia; sem o arquivo, pinta a cor de fundo do jogo."""
    if (Recursos.pasta / caminho).exists():
        fundo = Recursos.imagem(caminho)
        if fundo.get_size() != tela.get_size():
            fundo = pygame.transform.smoothscale(fundo, tela.get_size())
        tela.blit(fundo, (0, 0))
    else:
        tela.fill(Cor.FUNDO)
    if escuro:
        escurecer(tela, escuro)
```

Substituir `jogo/cenas/partida.py` inteiro por:
```python
import pygame

from jogo.cenas.bau import CenaBau
from jogo.cenas.cena import Cena
from jogo.cenas.fim import CenaFimDeJogo
from jogo.cenas.hud import Hud
from jogo.cenas.nivel import CenaNivel
from jogo.cenas.pausa import CenaPausa
from jogo.jogo import Jogo


class CenaPartida(Cena):
    ESPERA_FIM = 1.5

    def __init__(self, app, classe_jogador):
        super().__init__(app)
        self.jogo = Jogo(classe_jogador)
        self.hud = Hud()
        self._espera_fim = self.ESPERA_FIM

    def tratar_evento(self, evento):
        if evento.type != pygame.KEYDOWN:
            return
        if evento.key == pygame.K_ESCAPE:
            self.app.empilhar(CenaPausa(self.app, self))
        elif evento.key == pygame.K_SPACE:
            self.jogo.jogador.usar_especial(self.jogo)

    def _ler_entrada(self):
        teclas = pygame.key.get_pressed()
        x = (teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT])
        y = (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP])
        self.jogo.entrada.direcao = pygame.Vector2(x, y)
        self.jogo.entrada.mira = self.jogo.camera.para_mundo(pygame.mouse.get_pos()) if self.app.mira_mouse else None

    def atualizar(self, dt):
        if self.jogo.terminou:
            self._espera_fim -= dt
            if self._espera_fim <= 0:
                self.app.trocar(CenaFimDeJogo(self.app, self.jogo))
            return
        self._ler_entrada()
        self.jogo.atualizar(dt)
        if self.jogo.niveis_pendentes > 0:
            self.app.empilhar(CenaNivel(self.app, self.jogo))
        elif self.jogo.baus_pendentes > 0:
            self.app.empilhar(CenaBau(self.app, self.jogo))

    def desenhar(self, tela):
        self.jogo.desenhar(tela)
        self.hud.desenhar(tela, self.jogo)
```

`main.py`:
```python
"""UFJ Survivors. Rode com: python main.py"""
from jogo.aplicacao import Aplicacao
from jogo.cenas.titulo import CenaTitulo


def main():
    app = Aplicacao()
    app.executar(CenaTitulo(app))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Título, seleção e ranking**

`jogo/cenas/titulo.py`:
```python
import math

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import Botao, MenuDeBotoes, desenhar_fundo, desenhar_texto
from jogo.config import ALTURA, LARGURA, TITULO, Cor
from jogo.nucleo.recursos import Recursos


class CenaTitulo(Cena):
    LOGO = "sprites/logo.png"

    def __init__(self, app):
        super().__init__(app)
        self.tempo = 0.0
        meio = LARGURA // 2
        self.menu = MenuDeBotoes([
            Botao("JOGAR", (meio, 440), self._jogar),
            Botao("RANKING", (meio, 520), self._ranking),
            Botao("SAIR", (meio, 600), app.sair),
        ])

    def _jogar(self):
        from jogo.cenas.selecao import CenaSelecao
        self.app.trocar(CenaSelecao(self.app))

    def _ranking(self):
        from jogo.cenas.ranking import CenaRanking
        self.app.trocar(CenaRanking(self.app))

    def tratar_evento(self, evento):
        self.menu.tratar_evento(evento)

    def atualizar(self, dt):
        self.tempo += dt

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=60)
        y = 200 + math.sin(self.tempo * 2) * 6
        if (Recursos.pasta / self.LOGO).exists():
            logo = Recursos.imagem(self.LOGO, 220)
            tela.blit(logo, logo.get_rect(center=(LARGURA // 2, y)))
        else:
            desenhar_texto(tela, TITULO.upper(), 96, Cor.DESTAQUE, centro=(LARGURA // 2, y))
        self.menu.desenhar(tela)
        desenhar_texto(tela, "Trabalho de Programação Orientada a Objetos - UFJ", 14, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 20))
```

`jogo/cenas/selecao.py`:
```python
import math

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import (TECLAS_CONFIRMAR, desenhar_barra, desenhar_fundo, desenhar_painel, desenhar_texto,
                                quebrar_linhas)
from jogo.config import ALTURA, LARGURA, Cor
from jogo.jogador.alunos import HEROIS
from jogo.nucleo.recursos import Recursos


class CenaSelecao(Cena):
    def __init__(self, app):
        super().__init__(app)
        self.indice = 0
        self.tempo = 0.0
        self.exemplos = [classe((0, 0)) for classe in HEROIS]
        self.cartoes = []
        for i in range(len(HEROIS)):
            r = pygame.Rect(0, 0, 420, 500)
            r.center = (LARGURA // 2 + (i - (len(HEROIS) - 1) / 2) * 460, 390)
            self.cartoes.append(r)

    def _comecar(self):
        from jogo.cenas.partida import CenaPartida
        self.app.trocar(CenaPartida(self.app, HEROIS[self.indice]))

    def _voltar(self):
        from jogo.cenas.titulo import CenaTitulo
        self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_LEFT, pygame.K_a):
                self.indice = (self.indice - 1) % len(HEROIS)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.indice = (self.indice + 1) % len(HEROIS)
            elif evento.key in TECLAS_CONFIRMAR:
                self._comecar()
            elif evento.key == pygame.K_ESCAPE:
                self._voltar()
        elif evento.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.cartoes):
                if r.collidepoint(evento.pos):
                    self.indice = i
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, r in enumerate(self.cartoes):
                if r.collidepoint(evento.pos):
                    self.indice = i
                    self._comecar()

    def atualizar(self, dt):
        self.tempo += dt

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=170)
        desenhar_texto(tela, "ESCOLHA SEU ALUNO", 44, Cor.DESTAQUE, centro=(LARGURA // 2, 70))
        for i, (heroi, r) in enumerate(zip(self.exemplos, self.cartoes)):
            self._cartao(tela, heroi, r, i == self.indice)
        desenhar_texto(tela, "[<- ->] escolher    [Enter] começar    [Esc] voltar", 16, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 24))

    def _cartao(self, tela, heroi, r, focado):
        desenhar_painel(tela, r, cor_borda=Cor.DESTAQUE if focado else Cor.BORDA_ESCURA)
        pulo = abs(math.sin(self.tempo * 6)) * 8 if focado else 0
        sprite = Recursos.imagem(heroi.IMAGEM, 150)
        tela.blit(sprite, sprite.get_rect(midbottom=(r.centerx, r.top + 190 - pulo)))
        desenhar_texto(tela, heroi.NOME, 30, Cor.TEXTO, centro=(r.centerx, r.top + 215))
        desenhar_texto(tela, heroi.DESCRICAO, 16, Cor.TEXTO_FRACO, centro=(r.centerx, r.top + 245))
        x = r.left + 30
        desenhar_texto(tela, "Vida", 16, Cor.TEXTO, topo_esquerda=(x, r.top + 270))
        desenhar_barra(tela, pygame.Rect(x + 120, r.top + 274, 230, 12), heroi.VIDA / 130, Cor.VIDA)
        desenhar_texto(tela, "Velocidade", 16, Cor.TEXTO, topo_esquerda=(x, r.top + 296))
        desenhar_barra(tela, pygame.Rect(x + 120, r.top + 300, 230, 12), heroi.VELOCIDADE / 230, Cor.EXPERIENCIA)
        arma = heroi.armas[0]
        icone = Recursos.icone(arma.ICONE, 40)
        tela.blit(icone, icone.get_rect(center=(x + 20, r.top + 350)))
        desenhar_texto(tela, f"Arma: {arma.NOME}", 18, Cor.TEXTO, topo_esquerda=(x + 50, r.top + 340))
        especial = heroi.especial
        icone = Recursos.icone(especial.ICONE, 40)
        tela.blit(icone, icone.get_rect(center=(x + 20, r.top + 405)))
        desenhar_texto(tela, f"Especial: {especial.NOME}", 18, Cor.DESTAQUE, topo_esquerda=(x + 50, r.top + 395))
        fonte = Recursos.fonte(15)
        for n, linha in enumerate(quebrar_linhas(especial.DESCRICAO, fonte, r.width - 110)):
            desenhar_texto(tela, linha, 15, Cor.TEXTO_FRACO, topo_esquerda=(x + 50, r.top + 420 + n * 18))
```

`jogo/cenas/ranking.py`:
```python
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR, desenhar_fundo, desenhar_painel, desenhar_texto
from jogo.config import ALTURA, LARGURA, Cor


class CenaRanking(Cena):
    def __init__(self, app, destaque=None):
        super().__init__(app)
        self.destaque = destaque

    def _voltar(self):
        from jogo.cenas.titulo import CenaTitulo
        self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and (evento.key == pygame.K_ESCAPE or evento.key in TECLAS_CONFIRMAR):
            self._voltar()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._voltar()

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=170)
        desenhar_texto(tela, "RANKING", 48, Cor.DESTAQUE, centro=(LARGURA // 2, 70))
        painel = pygame.Rect(0, 0, 820, 520)
        painel.center = (LARGURA // 2, 390)
        desenhar_painel(tela, painel)
        registros = self.app.ranking.registros
        if not registros:
            desenhar_texto(tela, "Ninguém jogou ainda. Seja o primeiro!", 24, Cor.TEXTO, centro=painel.center)
        for i, r in enumerate(registros):
            y = painel.top + 30 + i * 46
            cor = Cor.DESTAQUE if self.destaque is not None and r == self.destaque else Cor.TEXTO
            minutos, segundos = divmod(int(r.tempo), 60)
            desenhar_texto(tela, f"{i + 1}.", 24, cor, topo_esquerda=(painel.left + 30, y))
            desenhar_texto(tela, r.nome, 24, cor, topo_esquerda=(painel.left + 90, y))
            desenhar_texto(tela, r.heroi, 18, Cor.TEXTO_FRACO, topo_esquerda=(painel.left + 330, y + 4))
            desenhar_texto(tela, f"{minutos:02d}:{segundos:02d}", 20, cor, topo_esquerda=(painel.left + 460, y + 2))
            desenhar_texto(tela, f"{r.pontos}", 24, cor, topo_direita=(painel.right - 140, y))
            if r.venceu:
                desenhar_texto(tela, "APROVADO", 14, Cor.APROVADO, topo_esquerda=(painel.right - 120, y + 6))
        desenhar_texto(tela, "[Enter] voltar", 16, Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 24))
```

- [ ] **Step 5: Nível, baú, pausa e fim de jogo**

`jogo/cenas/nivel.py`:
```python
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR, desenhar_painel, desenhar_texto, escurecer, quebrar_linhas
from jogo.config import ALTURA, CURA_AO_PULAR, LARGURA, Cor
from jogo.nucleo.recursos import Recursos
from jogo.progressao import Progressao

CORES_ROTULO = {"colab": Cor.DESTAQUE, "nova": Cor.APROVADO, "melhoria": Cor.EXPERIENCIA, "lanche": Cor.CURA}


class CenaNivel(Cena):
    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.indice = 0
        self._sortear()
        Recursos.tocar("nivel", 0.5)

    def _sortear(self):
        self.opcoes = Progressao.gerar_opcoes(self.jogo.jogador, self.jogo.rng)
        self.indice = 0
        self.cartoes = []
        for i in range(len(self.opcoes)):
            r = pygame.Rect(0, 0, 310, 380)
            r.center = (LARGURA // 2 + (i - (len(self.opcoes) - 1) / 2) * 340, 380)
            self.cartoes.append(r)

    def escolher(self, i):
        self.opcoes[i].aplicar(self.jogo.jogador, self.jogo)
        self._fechar()

    def sortear_de_novo(self):
        if self.jogo.sorteios_restantes > 0:
            self.jogo.sorteios_restantes -= 1
            self._sortear()

    def pular(self):
        self.jogo.jogador.curar(CURA_AO_PULAR)
        self._fechar()

    def _fechar(self):
        self.jogo.niveis_pendentes = max(0, self.jogo.niveis_pendentes - 1)
        self.app.desempilhar()

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            numeros = (pygame.K_1, pygame.K_2, pygame.K_3)
            if evento.key in numeros and numeros.index(evento.key) < len(self.opcoes):
                self.escolher(numeros.index(evento.key))
            elif evento.key in (pygame.K_LEFT, pygame.K_a):
                self.indice = (self.indice - 1) % len(self.opcoes)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.indice = (self.indice + 1) % len(self.opcoes)
            elif evento.key in TECLAS_CONFIRMAR:
                self.escolher(self.indice)
            elif evento.key == pygame.K_r:
                self.sortear_de_novo()
            elif evento.key == pygame.K_p:
                self.pular()
        elif evento.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.cartoes):
                if r.collidepoint(evento.pos):
                    self.indice = i
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, r in enumerate(self.cartoes):
                if r.collidepoint(evento.pos):
                    self.escolher(i)
                    return

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        escurecer(tela, 170)
        desenhar_texto(tela, "SUBIU DE NÍVEL!", 48, Cor.DESTAQUE, centro=(LARGURA // 2, 110))
        fonte_titulo, fonte_texto = Recursos.fonte(22), Recursos.fonte(16)
        for i, (opcao, r) in enumerate(zip(self.opcoes, self.cartoes)):
            focado = i == self.indice
            desenhar_painel(tela, r, cor_borda=Cor.DESTAQUE if focado else Cor.BORDA)
            desenhar_texto(tela, str(i + 1), 18, Cor.TEXTO_FRACO, topo_esquerda=(r.left + 14, r.top + 10))
            icone = Recursos.icone(opcao.icone, 80)
            tela.blit(icone, icone.get_rect(center=(r.centerx, r.top + 75)))
            if opcao.rotulo:
                desenhar_texto(tela, opcao.rotulo, 16, CORES_ROTULO[opcao.tipo], centro=(r.centerx, r.top + 135))
            y = r.top + 160
            for linha in quebrar_linhas(opcao.titulo, fonte_titulo, r.width - 30):
                desenhar_texto(tela, linha, 22, Cor.TEXTO, centro=(r.centerx, y))
                y += 26
            y += 10
            for linha in quebrar_linhas(opcao.descricao, fonte_texto, r.width - 36):
                desenhar_texto(tela, linha, 16, Cor.TEXTO_FRACO, centro=(r.centerx, y))
                y += 20
        rodape = (f"[1] [2] [3] ou Enter: escolher    [R] sortear de novo ({self.jogo.sorteios_restantes})    "
                  f"[P] pular (+{CURA_AO_PULAR} de vida)")
        desenhar_texto(tela, rodape, 16, Cor.TEXTO, centro=(LARGURA // 2, ALTURA - 60))
```

`jogo/cenas/bau.py`:
```python
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR, desenhar_texto, escurecer
from jogo.config import ALTURA, LARGURA, Cor
from jogo.nucleo.recursos import Recursos
from jogo.progressao import Progressao


class CenaBau(Cena):
    QUADROS = tuple(f"legado/itens/chest_f{i}.png" for i in range(4))
    DURACAO_ABERTURA = 1.0

    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.tempo = 0.0
        self.premio = Progressao.premio_bau(jogo.jogador, jogo.rng)
        self.aberto = False

    def tratar_evento(self, evento):
        if not self.aberto:
            return
        confirmou = evento.type == pygame.KEYDOWN and evento.key in TECLAS_CONFIRMAR
        clicou = evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
        if confirmou or clicou:
            self.jogo.baus_pendentes = max(0, self.jogo.baus_pendentes - 1)
            self.app.desempilhar()

    def atualizar(self, dt):
        self.tempo += dt
        if not self.aberto and self.tempo >= self.DURACAO_ABERTURA:
            self.premio.aplicar(self.jogo.jogador, self.jogo)
            self.aberto = True
            Recursos.tocar("bau", 0.6)

    def desenhar(self, tela):
        escurecer(tela, 170)
        desenhar_texto(tela, "BAÚ!", 56, Cor.DESTAQUE, centro=(LARGURA // 2, 110))
        quadro = min(len(self.QUADROS) - 1, int(self.tempo / self.DURACAO_ABERTURA * len(self.QUADROS)))
        tremor = 0 if self.aberto else round(4 * ((self.tempo * 30) % 2 - 1))
        bau = Recursos.imagem(self.QUADROS[quadro], 210)
        tela.blit(bau, bau.get_rect(center=(LARGURA // 2 + tremor, 300)))
        if self.aberto:
            icone = Recursos.icone(self.premio.icone, 72)
            tela.blit(icone, icone.get_rect(center=(LARGURA // 2, 470)))
            desenhar_texto(tela, f"Você ganhou: {self.premio.titulo}", 28, Cor.TEXTO, centro=(LARGURA // 2, 540))
            if self.premio.rotulo:
                desenhar_texto(tela, self.premio.rotulo, 18, Cor.DESTAQUE, centro=(LARGURA // 2, 572))
            desenhar_texto(tela, "[Enter] continuar", 16, Cor.TEXTO_FRACO, centro=(LARGURA // 2, ALTURA - 40))
```

`jogo/cenas/pausa.py`:
```python
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import Botao, MenuDeBotoes, desenhar_texto, escurecer
from jogo.config import ALTURA, LARGURA, Cor


class CenaPausa(Cena):
    def __init__(self, app, partida):
        super().__init__(app)
        self.partida = partida
        meio = LARGURA // 2
        self.menu = MenuDeBotoes([
            Botao("CONTINUAR", (meio, 300), self._continuar, largura=380),
            Botao(self._texto_mira(), (meio, 380), self._alternar_mira, largura=380),
            Botao("SAIR PARA O TÍTULO", (meio, 460), self._sair, largura=380),
        ])

    def _texto_mira(self):
        return "MIRA: MOUSE" if self.app.mira_mouse else "MIRA: TECLADO"

    def _alternar_mira(self):
        self.app.mira_mouse = not self.app.mira_mouse
        self.menu.botoes[1].texto = self._texto_mira()

    def _continuar(self):
        self.app.desempilhar()

    def _sair(self):
        from jogo.cenas.titulo import CenaTitulo
        self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self._continuar()
        else:
            self.menu.tratar_evento(evento)

    def atualizar(self, dt):
        pass

    def desenhar(self, tela):
        escurecer(tela, 160)
        desenhar_texto(tela, "PAUSADO", 56, Cor.DESTAQUE, centro=(LARGURA // 2, 180))
        self.menu.desenhar(tela)
        desenhar_texto(tela, "WASD ou setas: andar    Espaço: especial    Esc: pausar", 16, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 40))
```

`jogo/cenas/fim.py`:
```python
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.ranking import CenaRanking
from jogo.cenas.widgets import desenhar_fundo, desenhar_painel, desenhar_texto
from jogo.config import ALTURA, LARGURA, Cor
from jogo.ranking import RegistroRanking


class CenaFimDeJogo(Cena):
    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.nome = ""
        self.tempo = 0.0
        pygame.key.start_text_input()

    def _salvar(self):
        registro = self.jogo.resultado(self.nome)
        self.app.ranking.adicionar(registro)
        pygame.key.stop_text_input()
        self.app.trocar(CenaRanking(self.app, destaque=registro))

    def _sair(self):
        from jogo.cenas.titulo import CenaTitulo
        pygame.key.stop_text_input()
        self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.TEXTINPUT:
            for letra in evento.text:
                if letra.isprintable() and len(self.nome) < RegistroRanking.TAMANHO_NOME:
                    self.nome += letra
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_BACKSPACE:
                self.nome = self.nome[:-1]
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._salvar()
            elif evento.key == pygame.K_ESCAPE:
                self._sair()

    def atualizar(self, dt):
        self.tempo += dt

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=190)
        venceu = self.jogo.venceu
        titulo = "APROVADO!" if venceu else "REPROVADO!"
        frase = "Você derrotou o Professor!" if venceu else "A Semana de Provas venceu desta vez."
        desenhar_texto(tela, titulo, 72, Cor.APROVADO if venceu else Cor.REPROVADO, centro=(LARGURA // 2, 110))
        desenhar_texto(tela, frase, 22, Cor.TEXTO, centro=(LARGURA // 2, 170))
        painel = pygame.Rect(0, 0, 560, 250)
        painel.center = (LARGURA // 2, 340)
        desenhar_painel(tela, painel)
        placar = self.jogo.placar
        linhas = (
            ("Pontuação final", str(placar.pontuacao_final(venceu))),
            ("Tempo", placar.tempo_formatado),
            ("Eliminações", str(placar.eliminacoes)),
            ("Nível", str(self.jogo.jogador.nivel)),
            ("Combos 67", str(placar.combos_67)),
        )
        for i, (rotulo, valor) in enumerate(linhas):
            y = painel.top + 26 + i * 42
            desenhar_texto(tela, rotulo, 22, Cor.TEXTO_FRACO, topo_esquerda=(painel.left + 30, y))
            desenhar_texto(tela, valor, 24, Cor.DESTAQUE, topo_direita=(painel.right - 30, y))
        cursor = "_" if int(self.tempo * 2) % 2 == 0 else " "
        caixa = pygame.Rect(0, 0, 460, 56)
        caixa.center = (LARGURA // 2, 540)
        desenhar_painel(tela, caixa, alfa=255)
        desenhar_texto(tela, f"Seu nome: {self.nome}{cursor}", 26, Cor.TEXTO, topo_esquerda=(caixa.left + 20, caixa.top + 12))
        desenhar_texto(tela, "[Enter] salvar no ranking    [Esc] sair sem salvar", 16, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 40))
```

- [ ] **Step 6: Rodar e ver passar**

Run: `.venv/bin/pytest -v`
Expected: todos passam (os testes da Task 10 continuam válidos).

- [ ] **Step 7: Capturas de todas as telas**

Script descartável (não versionar) em `arte_bruta/capturas.py`, rodado com `SDL_VIDEODRIVER=dummy .venv/bin/python arte_bruta/capturas.py`: cria a `Aplicacao` com `pygame.display.set_mode((1280, 720))`, e para cada cena (Título, Seleção, Partida aos 30 s, Nível com `niveis_pendentes = 1`, Baú depois de 1,2 s, Pausa, Fim com vitória, Ranking com 3 registros num arquivo temporário) chama `app.passo(1/60, [])` e salva `arte_bruta/tela_<nome>.png`. Abrir cada imagem com Read e conferir: nada cortado, textos legíveis, nada sobreposto.

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "Telas de título, seleção, nível, baú, pausa, fim de jogo e ranking

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 18: Documentos das entregas (diagrama, proposta, registro de IA, README)

**Files:**
- Create: `docs/diagrama_classes.mmd`, `docs/entregas/diagrama_classes.png`, `docs/entregas/etapa1_proposta.md`, `docs/registro_ia.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: as classes como implementadas (conferir nomes no código antes de escrever).

- [ ] **Step 1: Diagrama de classes em Mermaid**

`docs/diagrama_classes.mmd`:
```
classDiagram
    direction TB
    class Entidade {
        <<abstract>>
        +posicao: Vector2
        +raio: float
        +ativo: bool
        +atualizar(dt, jogo)*
        +desenhar(tela, camera)*
        +remover()
    }
    class SerVivo {
        <<abstract>>
        -_vida: float
        +vida: float «property»
        +vida_maxima: float «property»
        +receber_dano(q) bool
        +curar(q)
    }
    class Jogador {
        <<abstract>>
        +armas: list~Arma~
        +itens: list~Item~
        +especial: Especial
        +criar_arma_inicial()* Arma
        +criar_especial()* Especial
        +ganhar_experiencia(q) int
        +aplicar_colab(receita, jogo)
    }
    class AlunoAgil
    class AlunoResistente
    class Inimigo {
        <<abstract>>
        +mover(dt, jogo)*
        +ao_morrer(jogo)
        +possuir(duracao)
        +tornar_gigante()
    }
    class Bug
    class CalculadoraBrava
    class MouseDeBolinha
    class Caixinha
    class CaixinhaPequena
    class PiCambaleante
    class Ponteiro
    class PilhaAA
    class PenteDeRAM
    class Chefe {
        <<abstract>>
        +ataques()* list
    }
    class Professor
    class Projetil {
        <<abstract>>
        +verificar_colisao(jogo)*
    }
    class ProjetilDoHeroi
    class ProjetilInimigo
    class Ajudante {
        <<abstract>>
    }
    class Coletavel {
        <<abstract>>
        +ao_coletar(jogo)*
    }
    class Efeito {
        <<abstract>>
    }
    class Arma {
        <<abstract>>
        -_nivel: int
        +nivel: int «property»
        +atualizar(dt, jogo, dono)*
        +__str__()
    }
    class ArmaDeDisparo {
        <<abstract>>
        -_municao: float
        +municao: float «property»
        +disparar(jogo, dono)* bool
    }
    class ArmaDeContato {
        <<abstract>>
    }
    class Colab {
        <<abstract>>
        +colabs_disponiveis(armas)$ list
    }
    class Item {
        <<abstract>>
        +aplicar(jogador)*
    }
    class Especial {
        <<abstract>>
        +ativar(dono, jogo)*
    }
    class Jogo {
        +entidades: list~Entidade~
        +atualizar(dt)
        +causar_dano(inimigo, dano)
    }
    class Fase {
        <<abstract>>
        +criar_eventos()* list
        +posicao_de_nascimento(jogo)$
    }
    class SemanaDeProvas
    class Placar {
        -_pontos: int
        +pontos: int «property»
        +registrar_eliminacao(p) bool
        +__str__()
    }
    class RegistroRanking {
        +__lt__(outro)
        +__eq__(outro)
        +__str__()
    }
    class FabricaDeInimigos {
        +registrar(nome)$
        +criar(nome, posicao, escala)$ Inimigo
    }
    class Colisao {
        +circulos_colidem(a, b)$ bool
        +segmento_acerta_circulo(...)$ bool
    }

    Entidade <|-- SerVivo
    Entidade <|-- Projetil
    Entidade <|-- Ajudante
    Entidade <|-- Coletavel
    Entidade <|-- Efeito
    SerVivo <|-- Jogador
    SerVivo <|-- Inimigo
    Jogador <|-- AlunoAgil
    Jogador <|-- AlunoResistente
    Inimigo <|-- Bug
    Inimigo <|-- CalculadoraBrava
    Inimigo <|-- MouseDeBolinha
    Inimigo <|-- Caixinha
    Caixinha <|-- CaixinhaPequena
    Inimigo <|-- PiCambaleante
    Inimigo <|-- Ponteiro
    Inimigo <|-- PilhaAA
    Inimigo <|-- PenteDeRAM
    Inimigo <|-- Chefe
    Chefe <|-- Professor
    Projetil <|-- ProjetilDoHeroi
    Projetil <|-- ProjetilInimigo
    Arma <|-- ArmaDeDisparo
    Arma <|-- ArmaDeContato
    Arma <|-- Colab
    Fase <|-- SemanaDeProvas

    Jogo *-- Jogador
    Jogo *-- Fase
    Jogo *-- Placar
    Jogo o-- Entidade
    Jogador *-- Arma
    Jogador *-- Item
    Jogador *-- Especial
    Fase ..> FabricaDeInimigos : usa
    FabricaDeInimigos ..> Inimigo : cria
    Jogo ..> Colisao : usa
    Placar ..> RegistroRanking : vira
```

Notas para quem ler: os armamentos concretos (CobraPython, Caramelo, MascoteChatGPT, MascoteClaude, Gemini, FuscaAzul, CarameloNoFusca, CobrasGemeas, DebateDasIAs), os 7 itens e os projéteis/ajudantes concretos ficam fora do diagrama principal para ele caber numa página; listá-los em texto na proposta.

- [ ] **Step 2: Gerar a imagem do diagrama**

Run: `npx -y @mermaid-js/mermaid-cli@11.4.2 -i docs/diagrama_classes.mmd -o docs/entregas/diagrama_classes.png -w 2400 -b white`
Expected: `docs/entregas/diagrama_classes.png` criado. Abrir com Read e conferir legibilidade. Se o `npx` falhar (rede ou Chromium), registrar o erro e orientar o grupo a colar o `.mmd` em https://mermaid.live e exportar o PNG.

- [ ] **Step 3: Proposta da etapa 1**

`docs/entregas/etapa1_proposta.md` com estas seções (texto completo, em português, sem placeholders):
1. **Identificação**: disciplina, professora, integrantes (deixar os nomes para o grupo preencher numa linha `Integrantes:` — é o único campo que o grupo preenche).
2. **O jogo**: um parágrafo do conceito (survivors na UFJ, lacaios das matérias, professor chefe, poderes de memes/IA/anime) e as regras (15 min, ondas, notas, níveis, cartas, café, combo 67, colabs, vitória/derrota).
3. **Controles**.
4. **Inimigos**: tabela da seção 4 da especificação.
5. **Armas, itens e especiais**: listas curtas.
6. **Diagrama de classes**: a imagem `diagrama_classes.png` e a explicação de cada relação principal (herança de `Entidade`, composição de `Jogo` e `Jogador`, fábrica, colisão).
7. **Como cada requisito de POO é cumprido**: a tabela "Mapeamento dos requisitos" da especificação, com o caminho do arquivo de cada um.
8. **Cronograma das etapas**: tabela da seção 12 da especificação.

- [ ] **Step 4: Registro de uso de IA**

`docs/registro_ia.md`: título, uma frase explicando que segue o formato do enunciado (uma tabela por etapa) e a tabela da Etapa 1 preenchida com o que de fato aconteceu nesta sessão, por exemplo:

| Etapa | Onde usamos IA | O que precisamos corrigir ou entender |
|---|---|---|
| 1 | Brainstorm do tema, dos inimigos e das armas com o Claude Code | Recusamos duas listas de inimigos que não eram visuais nem engraçadas; pedimos que o visual viesse antes da mecânica |
| 1 | Especificação, plano de implementação e diagrama de classes | Conferir que cada requisito da seção 2 aparece no diagrama e no código |
| 2 | Geração da arte com a ferramenta de imagens do ChatGPT | (preencher: sprites refeitos, ajustes de tamanho) |
| 2 e 3 | Código do jogo escrito com o Claude Code a partir do plano | (preencher: o que o grupo revisou, testou e mudou) |

Tabelas vazias para as etapas 3 e 4. Avisar no topo que o grupo deve revisar e completar com as próprias palavras.

- [ ] **Step 5: README**

Substituir `README.md` por: título e frase do jogo; captura de tela (`docs/entregas/captura.png`, copiada de `arte_bruta/tela_partida.png`); **Como rodar** (`python3.12 -m venv .venv`, `.venv/bin/pip install -r requirements.txt`, `.venv/bin/python main.py`; no Windows `py -3.12 -m venv .venv` e `.venv\Scripts\python main.py`); **Controles**; **Testes** (`.venv/bin/pytest`); **Onde está cada requisito de POO** (tabela com arquivo e classe); **Estrutura de pastas**; **Como criar um inimigo novo** (exemplo de 10 linhas: arquivo novo em `jogo/inimigos/`, classe herdando de `Inimigo` com `@FabricaDeInimigos.registrar`, e nome acrescentado em `SemanaDeProvas.APRESENTACOES`); **Créditos** (link para `assets/CREDITOS.md`).

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Diagrama de classes, proposta da etapa 1, registro de IA e README

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 19: Simulação completa, balanceamento e verificação final

**Files:**
- Create: `ferramentas/simular_partida.py`
- Modify (se a simulação pedir): números de balanceamento em `jogo/config.py`, `jogo/fase.py`, `jogo/jogador/jogador.py`, `jogo/inimigos/professor.py`

- [ ] **Step 1: Simulador de partida sem janela**

`ferramentas/simular_partida.py`:
```python
"""Joga uma partida inteira sem janela, com um jogador automático, e mostra um resumo.

Uso: python ferramentas/simular_partida.py [--heroi 1|2] [--imortal] [--semente N]
"""
import argparse
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from jogo.jogador.alunos import HEROIS  # noqa: E402
from jogo.jogo import Jogo  # noqa: E402
from jogo.progressao import Progressao  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--heroi", type=int, default=1)
    p.add_argument("--imortal", action="store_true")
    p.add_argument("--semente", type=int, default=1)
    a = p.parse_args()
    pygame.init()
    pygame.display.set_mode((1, 1))
    jogo = Jogo(HEROIS[a.heroi - 1], semente=a.semente)
    if a.imortal:
        jogo.jogador.vida_maxima = 10 ** 9
        jogo.jogador.vida = 10 ** 9
    dt = 1 / 30
    inicio = time.perf_counter()
    quadro = 0
    while not jogo.terminou and jogo.placar.tempo < 20 * 60:
        fuga = pygame.Vector2()
        for inimigo in jogo.inimigos_proximos(jogo.jogador.posicao, 220):
            fuga += jogo.jogador.posicao - inimigo.posicao
        circulo = pygame.Vector2(1, 0).rotate(quadro * 0.3)
        jogo.entrada.direcao = fuga.normalize() if fuga.length_squared() > 0 else circulo
        if jogo.jogador.especial.pronto:
            jogo.jogador.usar_especial(jogo)
        jogo.atualizar(dt)
        while jogo.niveis_pendentes > 0:
            Progressao.gerar_opcoes(jogo.jogador, jogo.rng)[0].aplicar(jogo.jogador, jogo)
            jogo.niveis_pendentes -= 1
        while jogo.baus_pendentes > 0:
            Progressao.premio_bau(jogo.jogador, jogo.rng).aplicar(jogo.jogador, jogo)
            jogo.baus_pendentes -= 1
        quadro += 1
        if quadro % (30 * 60) == 0:
            print(f"{jogo.placar.tempo_formatado}  nível {jogo.jogador.nivel:>2}  vida {jogo.jogador.vida:>7.0f}  "
                  f"inimigos {len(jogo.inimigos):>3}  eliminações {jogo.placar.eliminacoes}")
    print("---")
    print(f"resultado: {'VITÓRIA' if jogo.venceu else 'DERROTA' if jogo.terminou else 'SEM FIM'} em {jogo.placar.tempo_formatado}")
    print(f"nível {jogo.jogador.nivel}; armas: {', '.join(str(x) for x in jogo.jogador.armas)}")
    print(f"itens: {', '.join(str(x) for x in jogo.jogador.itens)}")
    print(f"placar: {jogo.placar}; combos 67: {jogo.placar.combos_67}")
    print(f"tempo real da simulação: {time.perf_counter() - inicio:.0f} s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar e calibrar**

Run: `.venv/bin/python ferramentas/simular_partida.py --heroi 1 --imortal` e o mesmo com `--heroi 2`.
Critérios (com jogador imortal): o Professor aparece aos 15:00 e é derrotado antes de 17:00; nível final entre 30 e 60; pelo menos 5 armas; pelo menos um combo 67 na partida.
Run: `.venv/bin/python ferramentas/simular_partida.py --heroi 1` e `--heroi 2` (mortal, sementes 1, 2 e 3).
Critério: o jogador automático burro sobrevive pelo menos 4 minutos e morre antes de 15:00 na maioria das sementes (um humano deve se sair melhor que ele).
Se algum critério falhar, ajustar um número por vez (vida do Professor, `Fase.alvo_de_inimigos`, `Fase.escala_dificuldade`, `Jogador.experiencia_necessaria`, `Inimigo.DANO` dos lacaios) e rodar de novo. Registrar os números finais na mensagem do commit.

- [ ] **Step 3: Testes e jogo de verdade**

Run: `.venv/bin/pytest -v` → todos passam.
Run: `.venv/bin/python main.py` e pedir ao usuário para jogar uma partida com cada aluno, conferindo: menus com teclado e mouse, combo 67 com áudio, Fusca possuindo inimigos, colabs, baú, pausa com mira por mouse, fim de jogo e ranking.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "Simulador de partida e balanceamento

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

- [ ] **Step 5: Limpeza do projeto antigo (com confirmação do usuário)**

Perguntar ao usuário antes de cada ação: apagar o fork `thallersubtil/Rpggame` no GitHub (`gh repo delete thallersubtil/Rpggame --yes`, que exige `gh auth refresh -h github.com -s delete_repo` feito por ele) e apagar a pasta `~/Desktop/Workspace/Rpggame` (fora desta sessão, que roda dentro dela).
