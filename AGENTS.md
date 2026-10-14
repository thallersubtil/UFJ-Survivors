# Instruções para agentes de IA (Claude Code, Codex, Cursor e afins)

Leia este arquivo inteiro antes de mexer no projeto. Ele vale para qualquer pessoa do grupo e para a IA que ela usar.

## O que é este projeto

**UFJ Survivors** é o trabalho prático de Programação Orientada a Objetos da UFJ (Profª Emília Alves Nogueira). É um jogo 2D em Pygame no estilo "survivors" (Vampire Survivors, HoloCure): o herói anda pelo Campus Jatobá da UFJ (mapa gerado a partir de satélite e OpenStreetMap), as armas atacam sozinhas, as ondas de inimigos crescem e o Professor aparece aos 8 minutos como chefe final. Toda a arte do mundo é pixel art animada (estilo HoloCure/Disgaea). Os inimigos são objetos das matérias do semestre que ganharam vida; as armas misturam memes, IAs e anime.

- O enunciado do trabalho está resumido em `docs/superpowers/specs/2026-10-10-ufj-survivors-design.md` (seções 1 e 12). **A especificação é a referência**: se algo aqui ou no código contradizer a especificação, siga a especificação ou converse com o grupo.
- O plano de implementação que gerou o código está em `docs/superpowers/plans/2026-10-10-ufj-survivors.md`.
- Animação, pixel art, mapa da UFJ e partida de 8 minutos: `docs/superpowers/specs/2026-10-14-animacao-mapa-ufj-design.md` (vale sobre a especificação original onde divergirem).
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
jogo/fase.py           Fase (abstrata) e SemanaDeProvas: linha do tempo dos 8 minutos
jogo/mapa.py           Mapa (abstrata), MapaUFJ, Predio (obstáculo), Decoracao; jogo/cenario.py: pátio genérico
jogo/nucleo/animacao.py  Animacao e Animador (composição: personagens contêm um Animador)
jogo/nucleo/           Entidade, SerVivo, Colisao, Camera, GradeEspacial, Recursos (arte/som com substitutos), desenho
jogo/jogador/          Jogador (abstrata), AlunoAgil, AlunoResistente, especiais, BonusTemporario
jogo/inimigos/         Inimigo (abstrata), FabricaDeInimigos, um arquivo por lacaio, Chefe, Professor
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

**Inimigo novo** (é o "requisito surpresa" mais provável na apresentação): um arquivo novo em `jogo/inimigos/` com uma classe que herda de `Inimigo`, decorada com `@FabricaDeInimigos.registrar("nome")` e implementando `mover()`. O pacote importa todos os arquivos da pasta sozinho; **nenhuma classe existente muda**. Para aparecer na fase, acrescente `(segundos, "nome")` em `SemanaDeProvas.APRESENTACOES`. Exemplo completo no `README.md`.

**Arma nova**: herde de `ArmaDeDisparo` (implemente `disparar()`, que retorna `False` se não havia alvo) ou de `ArmaDeContato` (implemente `atualizar()`). Defina `NOME`, `DESCRICAO`, `ICONE`, `ATRIBUTOS` (uma tupla de 7 valores por atributo, um por nível) e `MELHORIAS` (6 textos). Acrescente a classe em `Progressao.ARMAS` para ela aparecer nas cartas.

**Item novo**: herde de `Item`, implemente `aplicar(jogador)` somando ao modificador do jogador conforme `self.nivel`, e acrescente em `ITENS` (`jogo/itens/itens.py`).

**Arte animada (pixel art)**: toda a arte do mundo é pixel art em resolução baixa, desenhada ampliada 2x sem suavizar (`ESCALA_PIXEL` em `jogo/config.py`). Cada personagem tem uma pasta `assets/sprites/<nome>/` com tiras de quadros `<animacao>-<n>.png` (`parado`, `andar`, `mover`...); a classe aponta para a pasta em `PASTA_SPRITE` e contém um `Animador` que escolhe a animação. Mini-chefes usam `<nome>_gigante/`, em resolução própria. Para criar ou trocar uma animação:
1. Gere a folha com a ferramenta de imagens do ChatGPT (`edit_image`), passando uma folha existente como referência de estilo e o personagem como referência de design. O prompt que funcionou: "low-resolution pixel art sprite sheet for a HoloCure / Disgaea style game ... exactly N frames in ONE horizontal row, equal cells, clear empty space between frames, same size and same baseline ... true low-resolution pixel art with big crisp square pixels, about 16 colors, solid 1-pixel dark outline, no anti-aliasing ... transparent background". Para piscar: "frame 3 eyes closed".
2. Salve a folha em `arte_bruta/folhas/` (fora do git) e acrescente uma linha em `RECEITA` de `ferramentas/montar_sprites.py` (folha, pasta, animação, número de quadros, altura nativa, e `gigante` se for mini-chefe).
3. Rode `.venv/bin/python ferramentas/montar_sprites.py`. As folhas brutas do grupo estão com o Thaller; peça a ele se precisar refazer algum sprite antigo.
Se a pasta não existir, o jogo usa a imagem estática `IMAGEM` ou um círculo colorido; nada quebra.

**Trocar a arte provisória dos alunos e do professor pelas caricaturas do grupo**: gere folhas `parado` (4 quadros, o 3º piscando) e `andar` (6 quadros) para cada um, como acima, mantendo as pastas `aluno1`, `aluno2`, `aluno2_ssj` e `professor`, e troque os nomes `NOME` em `jogo/jogador/alunos.py` e `jogo/inimigos/professor.py`.

**Mapa da UFJ**: `.venv/bin/python ferramentas/gerar_mapa.py` (baixa sozinho as fontes de satélite e OpenStreetMap se faltarem, com `--baixar` para atualizar) gera `assets/cenario/mapa_ufj.png`, os sprites dos prédios e `mapa_ufj.json`. Para mudar escala, recorte, cores, nomes curtos dos prédios ou densidade de árvores, edite as constantes no topo do script. Prédios são `Predio` (obstáculos com o contorno real); herói e inimigos são empurrados para fora por `Colisao.empurrar_para_fora`.

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
