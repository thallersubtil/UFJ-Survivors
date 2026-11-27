# Instruções para agentes de IA (Claude Code, Codex, Cursor e afins)

Leia este arquivo inteiro antes de mexer no projeto. Ele vale para qualquer pessoa do grupo e para a IA que ela usar.

## O que é este projeto

**UFJ Survivors** é o trabalho prático de Programação Orientada a Objetos da UFJ (Profª Emília Alves Nogueira). É um jogo 2D em Pygame no estilo "survivors" (Vampire Survivors, HoloCure): o herói anda pelo Campus Jatobá da UFJ (mapa gerado a partir de satélite e OpenStreetMap), as armas atacam sozinhas, as ondas de inimigos crescem e, no fim de cada uma das três provas de 5 minutos, chega um professor possuído pela própria matéria (Cálculo I; Arquitetura de Computadores e depois ED em C; Transformação Digital e depois POO). O jogador escolhe uma classe (Otaku, Programador, Mestre de RPG, Monitor, Gamer, Calouro, Cara da Carona), cada uma com ativa, passiva, especial e aparência próprios (um chibi na partida, o retrato grande na matrícula e o rosto no HUD); a escolha é feita na tela de matrícula, na secretaria, que imprime a carteirinha. As armas têm 4 níveis e o último é uma forma suprema com mecânica própria; duas armas certas no máximo liberam uma colab secreta. Carrega no máximo 4 armas e 4 itens, rola para esquivar (invencível durante o rolamento) e fica mais rápido aos poucos, enquanto os inimigos também aceleram com a prova; há um modo treino para enfrentar um chefe escolhido. Entre as partidas, o Centro Acadêmico (menu principal) tem a loja de melhorias permanentes e desbloqueios, paga com as moedas das provas, e um cassino com essas moedas. A arte dos monstros é ilustrada e animada, no estilo Disgaea (contorno grosso, cores saturadas); personagens, ícones e efeitos novos são chibis em pixel art. A arte nova é montada a partir de folhas em `nova_arte/_bruto/` (fora do git, como `arte_bruta/`) pelas ferramentas `ferramentas/montar_*.py` e `pintar_predios.py`. Os inimigos são objetos das matérias do semestre que ganharam vida; as armas misturam memes, IAs e anime.

- O enunciado pede um jogo 2D em Pygame que cumpra os requisitos de POO da tabela abaixo; as entregas e os prazos estão no fim deste arquivo.
- O que ainda falta fazer está em `docs/PENDENCIAS.md`. **Comece por lá.**
- Comparação com o HoloCure (estrutura de referência) e lista do que ainda dá para melhorar: `docs/referencia_holocure.md`. A referência serve só para estudar mecânicas; nada da arte, dos sons ou do código dela entra no repositório.

## Como rodar e testar

```bash
python3.12 -m venv .venv                 # Windows: py -3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py                 # abre o jogo
.venv/bin/pytest -q                      # testes (todos devem passar antes de qualquer commit)
.venv/bin/python ferramentas/simular_partida.py --heroi 1 --imortal   # partida inteira sem janela, para balancear
.venv/bin/python ferramentas/demonstrar_polimorfismo.py               # hierarquia lida do código e o laço único rodando
```

Os testes rodam sem janela (`testes/conftest.py` define `SDL_VIDEODRIVER=dummy`). Para scripts próprios que importam pygame sem abrir janela, use as mesmas variáveis.

## Requisitos de POO que NÃO podem quebrar

A nota depende de estes pontos continuarem verdadeiros e fáceis de mostrar na defesa oral. Toda mudança precisa preservá-los:

| Requisito | Onde está |
|---|---|
| Classe abstrata `Entidade` com `atualizar()` e `desenhar()` | `jogo/nucleo/entidade.py` |
| 3+ inimigos herdando de `Inimigo` | `jogo/inimigos/` (8 lacaios + 3 chefes possuídos) |
| **Um único laço** `for e in self.entidades: e.atualizar(dt, self)` **sem `if`/`isinstance` por tipo** | `Jogo.atualizar()` em `jogo/jogo.py` |
| `vida`, `pontos`, `municao` com `@property` e validação | `SerVivo`, `Placar`, `ArmaDeDisparo` (também `moedas` em `Placar` e `Progresso`) |
| `Jogo` contém `Jogador`, `Fase`, `Placar`; `Jogador` contém `Arma` | `jogo/jogo.py`, `jogo/jogador/jogador.py` |
| `__str__`, `__eq__`, `__lt__` | `RegistroRanking` em `jogo/ranking.py` |
| `@classmethod` (fábrica) e `@staticmethod` (colisão) | `FabricaDeInimigos`, `Colisao` |

Regras que decorrem disso:
- Comportamento específico de um tipo vai num **método sobrescrito** (`mover`, `ao_morrer`, `desenhar_corpo`, `ao_acertar`, `ao_coletar`, `aplicar`...), nunca num `if type(...)`/`isinstance` dentro dos laços do `Jogo`.
- Não troque `@property` por atributo público nem remova a validação.
- Ao criar uma classe nova, encaixe-a na hierarquia existente (veja o diagrama em `docs/entregas/diagrama_classes.svg`, redesenhado por `ferramentas/gerar_entrega.py`) e atualize `docs/diagrama_classes.mmd` se ela for importante para a defesa.

## Mapa do código

```
main.py                ponto de entrada (abre a CenaTitulo)
jogo/config.py         tamanhos, cores e números gerais
jogo/jogo.py           Jogo: a partida; o laço polimórfico; regras de dano, morte, combo 67, notas
jogo/fase.py           Fase (abstrata), Prova e as três provas (Cálculo I; Arquitetura e ED; TD e POO), 5 min cada
jogo/mapa.py           Mapa (abstrata), MapaUFJ, Predio (obstáculo), Decoracao; jogo/cenario.py: pátio genérico
jogo/nucleo/animacao.py  Animacao e Animador (composição: personagens contêm um Animador)
jogo/nucleo/           Entidade, SerVivo, Colisao, Camera, GradeEspacial, Recursos (arte/som com substitutos), desenho
jogo/jogador/          Jogador (abstrata), classes.py (as 7 classes), Passiva e passivas,
                       especiais, Rolamento (esquiva), BonusTemporario
jogo/loja/             Centro Acadêmico: Progresso (moedas e compras salvas), Melhoria (abstrata) e as melhorias
                       permanentes, JogoDeAposta (abstrata) e os jogos do cassino
jogo/inimigos/         Inimigo (abstrata), FabricaDeInimigos, um arquivo por lacaio, Chefe, ChefePossuido e os três chefes,
                       MiniChefe (abstrata) e os 12 mini-chefes do mapa (mini_chefes.py), LacaioDoCampus e os lacaios deles
                       (lacaios_do_campus.py)
jogo/inimigos/materias/  Materia (abstrata) e as cinco matérias: os ataques de cada chefe
jogo/armas/            Arma, ArmaDeDisparo (usa café), ArmaSemMunicao (não usa café), uma arma por arquivo, colabs.py
jogo/itens/            Item (abstrata) e os 14 itens (4 só depois de comprados na loja; a Cola só aparece ao subir de nível)
jogo/projeteis/  jogo/ajudantes/  jogo/coletaveis/  jogo/efeitos.py   o que as armas e inimigos colocam na arena
                       (projeteis/tematicos.py: os ataques desenhados dos chefes e mini-chefes, com a arte em
                       assets/ataques/ montada por ferramentas/montar_ataques.py: ProjetilTematico, Bumerangue,
                       GolpeNoChao, Poca e Marca)
jogo/progressao.py     cartas de nível e prêmio do baú
jogo/tesouro.py        Raridade (comum, épico, lendário) e Tesouro: o que sai de um baú, com crítico de sorte
jogo/invocacao.py      LocalDeInvocacao: o círculo do mapa que invoca um mini-chefe opcional
jogo/cenas/            telas (Cena abstrata) e o HUD
jogo/ui/               interface em pixel art: CamadaPixel (640x360 ampliada 2x), texto, moldura, barra (pixel.py),
                       papel, madeira, giz, carimbo (materiais.py) e AreaInterativa (área clicável sobre a arte)
jogo/boletim.py        Boletim do fim de jogo: uma nota por prova (Jogo.notas guarda as das provas vencidas)
assets/                sprites/, icones/, cenario/, sons/, fontes/, legado/ (arte reaproveitada de outro jogo)
ferramentas/           pixelizar.py e montar_sprites.py (folhas de animação), gerar_mapa.py (mapa da UFJ),
                       gerar_sons.py, simular_partida.py, preparar_arte.py (imagens soltas, ex.: título)
testes/                pytest, um arquivo por assunto; fixture `jogo_limpo` em conftest.py
docs/                  entregas, diagrama, registro de uso de IA, guia do código, pendências
```

## Receitas

**Inimigo novo** (é o "requisito surpresa" mais provável na apresentação): um arquivo novo em `jogo/inimigos/` com uma classe que herda de `Inimigo`, decorada com `@FabricaDeInimigos.registrar("nome")` e implementando `mover()`. O pacote importa todos os arquivos da pasta sozinho; **nenhuma classe existente muda**. Para aparecer, acrescente `(segundos, "nome")` em `APRESENTACOES` de uma das provas em `jogo/fase.py`. Exemplo completo no `README.md`.

**Matéria ou chefe novo**: uma classe que herda de `Materia` em `jogo/inimigos/materias/` com `ataques()` combinando os ataques prontos (`leque`, `anel`, `rajada`, `chamada`, `chefe.investir`); o chefe é uma classe que herda de `ChefePossuido`, registrada na fábrica, com `MATERIAS = (...)` na ordem das fases. Exemplo no `README.md`.

**Arma nova**: herde de `ArmaDeDisparo` (implemente `disparar()`, que retorna `False` se não havia alvo) ou de `ArmaSemMunicao` (implemente `atualizar()`). Defina `NOME`, `DESCRICAO`, `ICONE`, `ATRIBUTOS` (uma tupla de 7 valores por atributo, um por nível) e `MELHORIAS` (6 textos). Acrescente a classe em `Progressao.ARMAS` para ela aparecer nas cartas.

**Item novo**: herde de `Item`, implemente `aplicar(jogador)` somando ao modificador do jogador conforme `self.nivel`, e acrescente em `ITENS` (`jogo/itens/itens.py`).

**Arma ou item que se compra na loja**: igual aos de cima, com `PRECO_DESBLOQUEIO = <moedas>`. Ele aparece sozinho na aba Desbloqueios do Centro Acadêmico e só entra nas cartas depois de comprado (`liberada()` em `Arma`/`Item`, filtro em `Progressao.candidatas`).

**Melhoria permanente nova**: herde de `Melhoria` (`jogo/loja/melhorias.py`) com `CHAVE` única (é o nome salvo no arquivo; não mude depois), `NOME`, `DESCRICAO`, `ICONE`, `NIVEL_MAXIMO`, `CUSTO_BASE` e `aplicar(jogador)`; acrescente em `MELHORIAS`. A loja lista sozinha.

**Jogo novo no cassino**: herde de `JogoDeAposta` (`jogo/loja/cassino.py`), implemente `sorteios()` (todos os sorteios possíveis, com a mesma chance) e `avaliar(sorteio, escolha)` devolvendo um `Desfecho` (linha da tabela, multiplicador, mensagem, símbolos) e acrescente em `JOGOS_DE_APOSTA`. O sorteio (`jogar`), a tabela de chances da tela (`tabela`) e o `retorno_esperado` saem desses dois métodos; teste que o retorno fica abaixo de 100% (veja `testes/test_cassino.py`). Sem mais nada o jogo aparece numa mesa genérica; para um aparelho animado, crie uma `Mesa` em `jogo/cenas/cassino_mesas.py` e registre em `MESAS`.

**Arte animada (estilo ilustrado, tipo Disgaea)**: os personagens são ilustrações de anime com contorno preto grosso, cores saturadas e cel shading, NÃO pixel art (o gerador de imagens não faz pixel art de verdade; testamos e ficou ruim). Cada personagem tem uma pasta `assets/sprites/<nome>/` com tiras `<animacao>-<n>.png` (`parado` com piscar no 3º quadro, `andar` com 4 quadros: passada, passagem, passada, passagem), já no tamanho de tela (herói ~76 px). A classe aponta para a pasta em `PASTA_SPRITE` e contém um `Animador`. Para criar ou trocar uma animação:
1. Gere a folha com a ferramenta de imagens do ChatGPT (`edit_image`), passando uma folha existente de `arte_bruta/disgaea/` como referência de estilo e o personagem como referência de design. Prompt que funcionou: "4-frame walk cycle ... in ONE horizontal row ... clean hand-drawn anime game illustration in the style of Disgaea character art, NOT pixel art: smooth bold black outlines, vivid saturated colors, crisp two-tone cel shading with rim light, chibi proportions ... 4 equal cells, clear empty space between frames, same baseline and scale ... transparent background".
2. Salve em `arte_bruta/disgaea/` (fora do git) e acrescente uma linha em `RECEITA` de `ferramentas/montar_sprites.py` (folha, pasta, animação, quadros, altura na tela; extras como `gigante`, `linha`, `faixa` estão documentados no topo do arquivo).
3. Rode `.venv/bin/python ferramentas/montar_sprites.py`. As folhas brutas estão com o Thaller.
Se a pasta não existir, o jogo usa a imagem estática `IMAGEM` ou um círculo colorido; nada quebra.

**Animação especial de mini-chefe** (arremesso, golpe, segunda fase): gere a folha com a folha de andar dele como referência (quadros em grade, com vão entre eles), acrescente a animação em `EXTRAS` de `ferramentas/montar_mini_chefes.py` (corte, âncora e escala estão explicados ali) e rode a ferramenta: todas as tiras dele saem com os pés na mesma linha. No código, `MiniChefe` já oferece `encenar(animacao, duracao, parado)` para tocar a animação, `agendar(atraso, acao)` para o golpe sair no quadro certo, `mostrar(animacao, quadro)` para quem controla o quadro pelo próprio ataque e a segunda fase por constantes (`SEGUNDA_FASE_ABAIXO_DE`, `FALA_DA_SEGUNDA_FASE`, `ANDAR_DA_SEGUNDA_FASE`...). Todos os 12 mini-chefes já têm; testes em `testes/test_animacoes_especiais.py`. Os professores (chefes das provas) têm a tira `atacar-4`, que `Chefe` toca sozinho a cada ataque (`TEMPO_DO_ATAQUE`); a folha vai em `PROFESSORES` da mesma ferramenta.

**Classe nova**: uma classe em `jogo/jogador/classes.py` que herda de `Jogador`, com `NOME`, `DESCRICAO`, `VIDA`, `VELOCIDADE`, `PASTA_SPRITE` e os três métodos `criar_arma_inicial()`, `criar_passiva()` e `criar_especial()`; acrescente-a em `CLASSES`. A passiva herda de `Passiva` (`jogo/jogador/passivas.py`) e soma o efeito em `aplicar(jogador)` usando `jogador.nivel`, como os itens.

**Trocar a arte provisória dos alunos e dos professores**: gere folhas `parado` (4 quadros, o 3º piscando) e `andar` (4 quadros) para cada um, como acima. Pastas: `aluno1` e `aluna1` (Programador e Mestre de RPG), `aluno2`, `aluna2`, `aluno2_ssj` e `aluna2_ssj` (Otaku), `professor` (chefe de Cálculo), `professor_computacao` (chefe de Arquitetura e ED) e `professora` (chefe de TD e POO; gerada em 19/10 com a mesma receita, usando as folhas do professor como referência de estilo). Para dar uma arte própria a um chefe, troque `PASTA_SPRITE` em `jogo/inimigos/professor_de_calculo.py`, `professor_de_arquitetura_ed.py` ou `professora_de_td_e_poo.py`. A pasta de cada classe fica em `PASTA_SPRITE` em `jogo/jogador/classes.py`. A arte tem que parecer pixel art como a dos alunos (contorno escuro de 1 px, transparência sem meio-termo, paleta curta); se sair lisa, passe `ferramentas/endurecer_sprite.py`.

**Mapa da UFJ**: `.venv/bin/python ferramentas/gerar_mapa.py` (baixa sozinho as fontes de satélite e OpenStreetMap se faltarem, com `--baixar` para atualizar) gera `assets/cenario/mapa_ufj.png`, os sprites dos prédios e `mapa_ufj.json`. Escala: 10 unidades por metro (prédios bem maiores que o herói); o chão é guardado em 1/3 da resolução e ampliado com suavização em blocos. Para mudar escala, recorte, cores, nomes curtos dos prédios ou densidade de árvores, edite as constantes no topo do script. Prédios são `Predio` (obstáculos com o contorno real); herói e inimigos são empurrados para fora por `Colisao.empurrar_para_fora`.

## Convenções

- **Tudo em português**: nomes de classes, métodos, variáveis, comentários, textos do jogo e mensagens de commit. Textos do jogo sem emojis.
- Siga o estilo do código vizinho: docstrings curtas, constantes de classe em MAIÚSCULAS, um arquivo por inimigo/arma.
- **Teste primeiro**: para comportamento novo ou correção de defeito, escreva o teste em `testes/`, veja falhar, implemente, veja passar, rode a suíte inteira.
- Não versione `arte_bruta/`, `.venv/`, `dados/ranking.json` nem `dados/progresso.json` (já estão no `.gitignore`).

## Processo do trabalho (vale nota)

- **Commits distribuídos entre os integrantes valem 10% da nota.** Cada pessoa commita o próprio trabalho, no próprio nome (`git config user.name` / `user.email` da pessoa). Commits pequenos, um assunto por commit, mensagem em português dizendo o que mudou.
- **Registro de uso de IA vale 5%.** A cada sessão com IA, acrescente uma linha na tabela da etapa atual em `docs/registro_ia.md`: onde a IA foi usada e o que precisou ser corrigido ou entendido. Escreva com as próprias palavras.
- Antes de dar push: `git pull`, rode `.venv/bin/pytest -q`, depois `git push`. Trabalhem direto no `main` ou em branches curtos; não reescrevam o histórico de quem já fez push.

## Prazos

| Etapa | Data | Entrega |
|---|---|---|
| 1 | 22/10 | Proposta e diagrama de classes (`docs/entregas/etapa1_proposta.md`) |
| 2 | 05/11 | Protótipo (tag `etapa-2-prototipo`; a versão atual já é bem mais completa) |
| 3 | 26/11 | Hierarquia completa e polimorfismo funcionando (`docs/entregas/etapa3_hierarquia_e_polimorfismo.html`, página autocontida gerada por `ferramentas/gerar_entrega.py`; rode de novo depois de mudar classes) |
| Mostra | 03/12 | A turma joga os jogos e vota em "mais criativo" e "melhor arquitetura" |
| 4 | 10/12 ou 14/12 | Versão final, defesa oral individual e requisito surpresa (ex.: "crie um inimigo novo em 10 minutos sem alterar as classes existentes") |
