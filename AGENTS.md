# Instruções para agentes de IA (Claude Code, Codex, Cursor e afins)

Leia este arquivo inteiro antes de mexer no projeto. Ele vale para qualquer pessoa do grupo e para a IA que ela usar.

## O que é este projeto

**UFJ Survivors** é o trabalho prático de Programação Orientada a Objetos da UFJ (Profª Emília Alves Nogueira). É um jogo 2D em Pygame no estilo "survivors" (Vampire Survivors, HoloCure): o herói anda pela arena, as armas atacam sozinhas, as ondas de inimigos crescem e o Professor aparece aos 15 minutos como chefe final. Os inimigos são objetos das matérias do semestre que ganharam vida; as armas misturam memes, IAs e anime.

- O enunciado do trabalho está resumido em `docs/superpowers/specs/2026-10-10-ufj-survivors-design.md` (seções 1 e 12). **A especificação é a referência**: se algo aqui ou no código contradizer a especificação, siga a especificação ou converse com o grupo.
- O plano de implementação que gerou o código está em `docs/superpowers/plans/2026-10-10-ufj-survivors.md`.
- O que ainda falta fazer está em `docs/PENDENCIAS.md`. **Comece por lá.**

## Como rodar e testar

```bash
python3.12 -m venv .venv                 # Windows: py -3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py                 # abre o jogo
.venv/bin/pytest -q                      # testes (todos devem passar antes de qualquer commit)
.venv/bin/python ferramentas/simular_partida.py --heroi 1 --imortal   # partida inteira sem janela, para balancear
```

Os testes rodam sem janela (`testes/conftest.py` define `SDL_VIDEODRIVER=dummy`). Para scripts próprios que importam pygame sem abrir janela, use as mesmas variáveis.

## Requisitos de POO que NÃO podem quebrar

A nota depende de estes pontos continuarem verdadeiros e fáceis de mostrar na defesa oral. Toda mudança precisa preservá-los:

| Requisito | Onde está |
|---|---|
| Classe abstrata `Entidade` com `atualizar()` e `desenhar()` | `jogo/nucleo/entidade.py` |
| 3+ inimigos herdando de `Inimigo` | `jogo/inimigos/` (8 lacaios + Professor) |
| **Um único laço** `for e in self.entidades: e.atualizar(dt, self)` **sem `if`/`isinstance` por tipo** | `Jogo.atualizar()` em `jogo/jogo.py` |
| `vida`, `pontos`, `municao` com `@property` e validação | `SerVivo`, `Placar`, `ArmaDeDisparo` |
| `Jogo` contém `Jogador`, `Fase`, `Placar`; `Jogador` contém `Arma` | `jogo/jogo.py`, `jogo/jogador/jogador.py` |
| `__str__`, `__eq__`, `__lt__` | `RegistroRanking` em `jogo/ranking.py` |
| `@classmethod` (fábrica) e `@staticmethod` (colisão) | `FabricaDeInimigos`, `Colisao` |

Regras que decorrem disso:
- Comportamento específico de um tipo vai num **método sobrescrito** (`mover`, `ao_morrer`, `desenhar_corpo`, `ao_acertar`, `ao_coletar`, `aplicar`...), nunca num `if type(...)`/`isinstance` dentro dos laços do `Jogo`.
- Não troque `@property` por atributo público nem remova a validação.
- Ao criar uma classe nova, encaixe-a na hierarquia existente (veja o diagrama em `docs/entregas/diagrama_classes.png`) e atualize `docs/diagrama_classes.mmd` se ela for importante para a defesa.

## Mapa do código

```
main.py                ponto de entrada (abre a CenaTitulo)
jogo/config.py         tamanhos, cores e números gerais
jogo/jogo.py           Jogo: a partida; o laço polimórfico; regras de dano, morte, combo 67, notas
jogo/fase.py           Fase (abstrata) e SemanaDeProvas: linha do tempo dos 15 minutos
jogo/nucleo/           Entidade, SerVivo, Colisao, Camera, GradeEspacial, Recursos (arte/som com substitutos), desenho
jogo/jogador/          Jogador (abstrata), AlunoAgil, AlunoResistente, especiais, BonusTemporario
jogo/inimigos/         Inimigo (abstrata), FabricaDeInimigos, um arquivo por lacaio, Chefe, Professor
jogo/armas/            Arma, ArmaDeDisparo (usa café), ArmaDeContato (não usa café), uma arma por arquivo, colabs.py
jogo/itens/            Item (abstrata) e os 7 itens passivos
jogo/projeteis/  jogo/ajudantes/  jogo/coletaveis/  jogo/efeitos.py   o que as armas e inimigos colocam na arena
jogo/progressao.py     cartas de nível e prêmio do baú
jogo/cenas/            telas (Cena abstrata) e o HUD
assets/                sprites/, icones/, cenario/, sons/, fontes/, legado/ (arte reaproveitada de outro jogo)
ferramentas/           preparar_arte.py, gerar_sons.py, simular_partida.py
testes/                pytest, um arquivo por assunto; fixture `jogo_limpo` em conftest.py
docs/                  entregas, diagrama, registro de uso de IA, especificação, plano, pendências
```

## Receitas

**Inimigo novo** (é o "requisito surpresa" mais provável na apresentação): um arquivo novo em `jogo/inimigos/` com uma classe que herda de `Inimigo`, decorada com `@FabricaDeInimigos.registrar("nome")` e implementando `mover()`. O pacote importa todos os arquivos da pasta sozinho; **nenhuma classe existente muda**. Para aparecer na fase, acrescente `(segundos, "nome")` em `SemanaDeProvas.APRESENTACOES`. Exemplo completo no `README.md`.

**Arma nova**: herde de `ArmaDeDisparo` (implemente `disparar()`, que retorna `False` se não havia alvo) ou de `ArmaDeContato` (implemente `atualizar()`). Defina `NOME`, `DESCRICAO`, `ICONE`, `ATRIBUTOS` (uma tupla de 7 valores por atributo, um por nível) e `MELHORIAS` (6 textos). Acrescente a classe em `Progressao.ARMAS` para ela aparecer nas cartas.

**Item novo**: herde de `Item`, implemente `aplicar(jogador)` somando ao modificador do jogador conforme `self.nivel`, e acrescente em `ITENS` (`jogo/itens/itens.py`).

**Arte nova**: gere a imagem (o grupo usou a ferramenta de imagens do ChatGPT com o estilo "cute chibi pixel art, 16-bit SNES style, three-quarter top-down view like Stardew Valley, thick dark outline, saturated colors, simple cel shading, transparent background"), salve a original em `arte_bruta/` (ignorada pelo git) e reduza com:
```bash
.venv/bin/python ferramentas/preparar_arte.py arte_bruta/x.png assets/sprites/x.png --altura 46
```
Se um arquivo de arte faltar, o jogo desenha um círculo colorido no lugar; nada quebra.

**Trocar a arte provisória dos alunos e do professor pelas caricaturas do grupo**: basta substituir `assets/sprites/aluno1.png`, `aluno2.png`, `aluno2_ssj.png` e `professor.png` (mantendo fundo transparente e o personagem virado para a direita) e os nomes `NOME` em `jogo/jogador/alunos.py` e `jogo/inimigos/professor.py`.

## Convenções

- **Tudo em português**: nomes de classes, métodos, variáveis, comentários, textos do jogo e mensagens de commit. Textos do jogo sem emojis.
- Siga o estilo do código vizinho: docstrings curtas, constantes de classe em MAIÚSCULAS, um arquivo por inimigo/arma.
- **Teste primeiro**: para comportamento novo ou correção de defeito, escreva o teste em `testes/`, veja falhar, implemente, veja passar, rode a suíte inteira.
- Não versione `arte_bruta/`, `.venv/` nem `dados/ranking.json` (já estão no `.gitignore`).

## Processo do trabalho (vale nota)

- **Commits distribuídos entre os integrantes valem 10% da nota.** Cada pessoa commita o próprio trabalho, no próprio nome (`git config user.name` / `user.email` da pessoa). Commits pequenos, um assunto por commit, mensagem em português dizendo o que mudou.
- **Registro de uso de IA vale 5%.** A cada sessão com IA, acrescente uma linha na tabela da etapa atual em `docs/registro_ia.md`: onde a IA foi usada e o que precisou ser corrigido ou entendido. Escreva com as próprias palavras.
- Antes de dar push: `git pull`, rode `.venv/bin/pytest -q`, depois `git push`. Trabalhem direto no `main` ou em branches curtos; não reescrevam o histórico de quem já fez push.

## Prazos

| Etapa | Data | Entrega |
|---|---|---|
| 1 | 22/10 | Proposta e diagrama de classes (`docs/entregas/etapa1_proposta.md`, `diagrama_classes.png`) |
| 2 | 05/11 | Protótipo (tag `etapa-2-prototipo`) |
| 3 | 26/11 | Hierarquia completa e polimorfismo funcionando |
| Mostra | 03/12 | A turma joga os jogos e vota em "mais criativo" e "melhor arquitetura" |
| 4 | 10/12 ou 14/12 | Versão final, defesa oral individual e requisito surpresa (ex.: "crie um inimigo novo em 10 minutos sem alterar as classes existentes") |
