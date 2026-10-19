# Instruções para agentes de IA (Claude Code, Codex, Cursor e afins)

Leia este arquivo inteiro antes de mexer no projeto. Ele vale para qualquer pessoa do grupo e para a IA que ela usar.

## O que é este projeto

**UFJ Survivors** é o trabalho prático de Programação Orientada a Objetos da UFJ (Profª Emília Alves Nogueira). É um jogo 2D em Pygame no estilo "survivors" (Vampire Survivors, HoloCure): o herói anda pelo Campus Jatobá da UFJ (mapa gerado a partir de satélite e OpenStreetMap), as armas atacam sozinhas, as ondas de inimigos crescem e o Professor aparece aos 8 minutos como chefe final. A arte é ilustrada e animada, no estilo Disgaea (contorno grosso, cores saturadas). Os inimigos são objetos das matérias do semestre que ganharam vida; as armas misturam memes, IAs e anime.

- O enunciado do trabalho está resumido em `docs/superpowers/specs/2026-10-10-ufj-survivors-design.md` (seções 1 e 12). **A especificação é a referência**: se algo aqui ou no código contradizer a especificação, siga a especificação ou converse com o grupo.
- O plano de implementação que gerou o código está em `docs/superpowers/plans/2026-10-10-ufj-survivors.md`.
- Animação, pixel art e mapa da UFJ (a partida de 8 minutos descrita ali foi trocada pelas três provas de 5 minutos, veja abaixo): `docs/superpowers/specs/2026-10-14-animacao-mapa-ufj-design.md` (vale sobre a especificação original onde divergirem).
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
| 3+ inimigos herdando de `Inimigo` | `jogo/inimigos/` (8 lacaios + 3 chefes possuídos) |
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
jogo/fase.py           Fase (abstrata), Prova e as três provas (Cálculo I; Arquitetura e ED; TD e POO), 5 min cada
jogo/mapa.py           Mapa (abstrata), MapaUFJ, Predio (obstáculo), Decoracao; jogo/cenario.py: pátio genérico
jogo/nucleo/animacao.py  Animacao e Animador (composição: personagens contêm um Animador)
jogo/nucleo/           Entidade, SerVivo, Colisao, Camera, GradeEspacial, Recursos (arte/som com substitutos), desenho
jogo/jogador/          Jogador (abstrata), AlunoAgil, AlunoResistente, especiais, BonusTemporario
jogo/inimigos/         Inimigo (abstrata), FabricaDeInimigos, um arquivo por lacaio, Chefe, ChefePossuido e os três chefes
jogo/inimigos/materias/  Materia (abstrata) e as cinco matérias: os ataques de cada chefe
jogo/armas/            Arma, ArmaDeDisparo (usa café), ArmaDeContato (não usa café), uma arma por arquivo, colabs.py
jogo/itens/            Item (abstrata) e os 7 itens passivos
jogo/projeteis/  jogo/ajudantes/  jogo/coletaveis/  jogo/efeitos.py   o que as armas e inimigos colocam na arena
jogo/progressao.py     cartas de nível e prêmio do baú
jogo/cenas/            telas (Cena abstrata) e o HUD
assets/                sprites/, icones/, cenario/, sons/, fontes/, legado/ (arte reaproveitada de outro jogo)
ferramentas/           pixelizar.py e montar_sprites.py (folhas de animação), gerar_mapa.py (mapa da UFJ),
                       gerar_sons.py, simular_partida.py, preparar_arte.py (imagens soltas, ex.: título)
testes/                pytest, um arquivo por assunto; fixture `jogo_limpo` em conftest.py
docs/                  entregas, diagrama, registro de uso de IA, especificação, plano, pendências
```

## Receitas

**Inimigo novo** (é o "requisito surpresa" mais provável na apresentação): um arquivo novo em `jogo/inimigos/` com uma classe que herda de `Inimigo`, decorada com `@FabricaDeInimigos.registrar("nome")` e implementando `mover()`. O pacote importa todos os arquivos da pasta sozinho; **nenhuma classe existente muda**. Para aparecer, acrescente `(segundos, "nome")` em `APRESENTACOES` de uma das provas em `jogo/fase.py`. Exemplo completo no `README.md`.

**Matéria ou chefe novo**: uma classe que herda de `Materia` em `jogo/inimigos/materias/` com `ataques()` combinando os ataques prontos (`leque`, `anel`, `rajada`, `chamada`, `chefe.investir`); o chefe é uma classe que herda de `ChefePossuido`, registrada na fábrica, com `MATERIAS = (...)` na ordem das fases. Exemplo no `README.md`.

**Arma nova**: herde de `ArmaDeDisparo` (implemente `disparar()`, que retorna `False` se não havia alvo) ou de `ArmaDeContato` (implemente `atualizar()`). Defina `NOME`, `DESCRICAO`, `ICONE`, `ATRIBUTOS` (uma tupla de 7 valores por atributo, um por nível) e `MELHORIAS` (6 textos). Acrescente a classe em `Progressao.ARMAS` para ela aparecer nas cartas.

**Item novo**: herde de `Item`, implemente `aplicar(jogador)` somando ao modificador do jogador conforme `self.nivel`, e acrescente em `ITENS` (`jogo/itens/itens.py`).

**Arte animada (estilo ilustrado, tipo Disgaea)**: os personagens são ilustrações de anime com contorno preto grosso, cores saturadas e cel shading, NÃO pixel art (o gerador de imagens não faz pixel art de verdade; testamos e ficou ruim). Cada personagem tem uma pasta `assets/sprites/<nome>/` com tiras `<animacao>-<n>.png` (`parado` com piscar no 3º quadro, `andar` com 4 quadros: passada, passagem, passada, passagem), já no tamanho de tela (herói ~76 px). A classe aponta para a pasta em `PASTA_SPRITE` e contém um `Animador`. Para criar ou trocar uma animação:
1. Gere a folha com a ferramenta de imagens do ChatGPT (`edit_image`), passando uma folha existente de `arte_bruta/disgaea/` como referência de estilo e o personagem como referência de design. Prompt que funcionou: "4-frame walk cycle ... in ONE horizontal row ... clean hand-drawn anime game illustration in the style of Disgaea character art, NOT pixel art: smooth bold black outlines, vivid saturated colors, crisp two-tone cel shading with rim light, chibi proportions ... 4 equal cells, clear empty space between frames, same baseline and scale ... transparent background".
2. Salve em `arte_bruta/disgaea/` (fora do git) e acrescente uma linha em `RECEITA` de `ferramentas/montar_sprites.py` (folha, pasta, animação, quadros, altura na tela; extras como `gigante`, `linha`, `faixa` estão documentados no topo do arquivo).
3. Rode `.venv/bin/python ferramentas/montar_sprites.py`. As folhas brutas estão com o Thaller.
Se a pasta não existir, o jogo usa a imagem estática `IMAGEM` ou um círculo colorido; nada quebra.

**Trocar a arte provisória dos alunos e do professor pelas caricaturas do grupo**: gere folhas `parado` (4 quadros, o 3º piscando) e `andar` (4 quadros) para cada um, como acima, mantendo as pastas `aluno1`, `aluno2`, `aluno2_ssj` e `professor`, e troque os nomes `NOME` em `jogo/jogador/alunos.py` e `jogo/inimigos/professor.py`.

**Mapa da UFJ**: `.venv/bin/python ferramentas/gerar_mapa.py` (baixa sozinho as fontes de satélite e OpenStreetMap se faltarem, com `--baixar` para atualizar) gera `assets/cenario/mapa_ufj.png`, os sprites dos prédios e `mapa_ufj.json`. Escala: 10 unidades por metro (prédios bem maiores que o herói); o chão é guardado em 1/3 da resolução e ampliado com suavização em blocos. Para mudar escala, recorte, cores, nomes curtos dos prédios ou densidade de árvores, edite as constantes no topo do script. Prédios são `Predio` (obstáculos com o contorno real); herói e inimigos são empurrados para fora por `Colisao.empurrar_para_fora`.

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
| 2 | 05/11 | Protótipo (tag `etapa-2-prototipo`; a versão atual já é bem mais completa) |
| 3 | 26/11 | Hierarquia completa e polimorfismo funcionando |
| Mostra | 03/12 | A turma joga os jogos e vota em "mais criativo" e "melhor arquitetura" |
| 4 | 10/12 ou 14/12 | Versão final, defesa oral individual e requisito surpresa (ex.: "crie um inimigo novo em 10 minutos sem alterar as classes existentes") |
