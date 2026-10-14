# UFJ Survivors: especificação do jogo

Data: 2026-10-10. **Atualizada por `2026-10-14-animacao-mapa-ufj-design.md`**: partida de 8 minutos, mapa do Campus Jatobá e pixel art animada. Trabalho prático de Programação Orientada a Objetos (UFJ, Profª Emília Alves Nogueira).

## 1. Objetivo

Jogo 2D em Pygame, no gênero "survivors" (Vampire Survivors, HoloCure): o herói anda pela arena, as armas atacam sozinhas, ondas de inimigos crescem com o tempo e um chefe aparece no fim. O tema é a própria UFJ: os inimigos são objetos das matérias do semestre que ganharam vida, o chefe é um professor e os heróis são os dois integrantes do grupo. Os poderes misturam memes, IAs e anime.

Critérios de sucesso:
- Cumpre todos os requisitos de POO da seção 2 do enunciado, de forma fácil de apontar no código e no diagrama.
- Roda localmente (`python main.py`), é jogável de ponta a ponta na primeira fase (15 minutos, com chefe final) e é visualmente agradável desde o primeiro protótipo.
- Engraçado para a turma, sem exigir que o jogador saiba o conteúdo das matérias.
- Atende às quatro entregas (proposta e diagrama, protótipo, hierarquia completa, versão final).

Escopo: somente a primeira fase. Heróis e professor usam arte genérica provisória ("aluno" e "professor"), a ser trocada depois pelas caricaturas do grupo.

## 2. Telas

1. **Título**: logo "UFJ Survivors", botões JOGAR, RANKING, SAIR.
2. **Seleção de herói**: Aluno 1 (ágil) ou Aluno 2 (resistente), com arma inicial, especial e atributos de cada um.
3. **Partida**: a fase "Semana de Provas". Esc pausa (continuar, sair para o título).
4. **Subir de nível**: sobreposta à partida, que fica pausada; 3 cartas, botões SORTEAR DE NOVO e PULAR.
5. **Fim de jogo**: vitória ou derrota, pontos, tempo, eliminações, nível; campo para o nome e gravação no ranking.
6. **Ranking**: os 10 melhores resultados (nome, herói, pontos, tempo).

Controles: WASD ou setas para andar; armas disparam sozinhas na direção do movimento (ou do mouse, se a mira por mouse estiver ligada na pausa); Espaço ativa o especial; Esc pausa; na tela de nível, teclas 1, 2, 3 ou clique.

Janela de 1280x720, 60 quadros por segundo, um jogador por vez.

## 3. A fase "Semana de Provas"

Arena: pátio do campus visto de cima, 3200x1800 pixels, com borda intransponível e decoração (árvores, bancos, postes) apenas visual. A câmera segue o herói.

Duração: 15 minutos. Linha do tempo:

| Tempo | Evento |
|---|---|
| 0:00 | Bug |
| 1:30 | Calculadora Brava |
| 3:00 | Mouse de Bolinha |
| 4:30 | Caixinha |
| 5:00 | Mini-chefe: Calculadora Gigante (solta baú) |
| 6:00 | Pi Cambaleante |
| 7:30 | Ponteiro |
| 9:00 | Pilha AA |
| 10:00 | Mini-chefe: Pente de RAM Gigante (solta baú) |
| 10:30 | Pente de RAM |
| 11:00 a 15:00 | todos misturados, mais numerosos e mais fortes |
| 15:00 | Professor (chefe final) |

- Cada lacaio, depois de apresentado, continua aparecendo. A quantidade simultânea e a vida dos inimigos crescem com o tempo.
- A cada 2 minutos, a partir do minuto 2, passa uma **formação**: uma parede ou um círculo de lacaios que atravessa a tela.
- Inimigos nascem fora da área visível, perto do herói. Há um limite de inimigos vivos (300) para manter o desempenho.
- Vitória: derrotar o Professor. Derrota: vida do herói chega a zero.

## 4. Inimigos

Estilo comum a todos: objeto do dia a dia de uma matéria que ganhou vida, com cara expressiva, bracinhos e perninhas. Cada um tem uma cor dominante e uma silhueta própria, para ser reconhecido de relance.

| Inimigo | Matéria | Aparência | Comportamento |
|---|---|---|---|
| **Bug** | POO | Besourinho verde-limão, olhos esbugalhados, anteninhas | Rápido e fraco; nasce em bandos de 5 a 8; persegue o herói |
| **Calculadora Brava** | Cálculo | Calculadora científica cinza, cara emburrada no visor, "ERROR" | Velocidade e vida médias; persegue |
| **Mouse de Bolinha** | Arquitetura | Mouse bege antigo, fio como rabo de rato | Investidas: corre rápido em linha reta na direção do herói, para, repete |
| **Caixinha** | POO | Caixa de papelão marrom, etiqueta "class", olhos curiosos | Anda em pulos; ao morrer, solta duas caixinhas menores (que não se dividem) |
| **Pi Cambaleante** | Cálculo | Letra π amarela e gorducha, anda com as "pernas" do π, chapeuzinho de festa | Zigue-zague a caminho do herói; ao morrer, mostra "3,14..." |
| **Ponteiro** | Estrutura de Dados I | Setinha branca do mouse com contorno preto | Mergulho: voa rápido em linha reta atravessando a posição do herói, faz a curva e repete |
| **Pilha AA** | Estrutura de Dados I | Pilha laranja e preta, carinha brava, perninhas | Anda aos saltos; ao morrer solta faíscas que ferem o herói se estiver perto |
| **Pente de RAM** | Arquitetura | Placa verde de memória com contatos dourados como patas | Centopeia: corpo de segmentos que ondula seguindo a cabeça; lento e com muita vida |

Mini-chefes: versões 3 vezes maiores, com 30 vezes a vida, de um lacaio; ao morrer soltam um **baú**.

**Professor** (chefe final, arte genérica provisória): barra de vida no topo da tela. Ataques que se alternam:
- **Folhas de prova**: leque de projéteis.
- **Investida**: carrega por um instante (aviso visual) e avança em linha reta.
- **Chamada**: invoca um grupo de lacaios em volta de si.
Abaixo de 50% de vida, alterna os ataques mais depressa.

Contato com qualquer inimigo causa dano ao herói, com 0,5 s de invencibilidade depois de cada dano.

## 5. Heróis

| | Aluno 1 (ágil) | Aluno 2 (resistente) |
|---|---|---|
| Vida | 80 | 130 |
| Velocidade | 230 px/s | 180 px/s |
| Arma inicial | Cobra Python | Caramelo |
| Especial | Zoltraak | Super Saiyajin |

- **Zoltraak** (recarga 60 s): raio mágico largo na direção da mira, por 1,5 s; atravessa e acerta tudo no caminho.
- **Super Saiyajin** (recarga 60 s): 10 s de cabelo dourado e aura; dano x2 e velocidade +40%.

Arte provisória: um aluno genérico chibi de mochila; o Aluno 2 com outra cor de roupa. Na versão Super Saiyajin, uma variante com cabelo dourado.

## 6. Progressão

- **Notas**: fichinhas com "10" que os inimigos derrubam; dão experiência e são puxadas pelo herói quando ele chega perto. A experiência necessária cresce a cada nível.
- **Subir de nível**: pausa e oferece 3 cartas sorteadas entre: arma nova, melhoria de arma que o herói já tem, item novo, melhoria de item. Limites: 6 armas e 6 itens. SORTEAR DE NOVO: 3 usos por partida. PULAR: troca a escolha por uma pequena cura.
- **Café (munição)**: as armas de disparo têm estoque próprio de café, que recarrega sozinho; sem café, atiram bem mais devagar. Copinhos de café derrubados pelos inimigos enchem o estoque de todas as armas. O jogador vê o café numa barra no HUD.
- **Baú**: aberto ao encostar; animação de abertura (arte reaproveitada) e uma melhoria aleatória de arma ou item.
- **Poção de vida** (arte reaproveitada): derrubada raramente; recupera vida.
- **Combo 67**: 67 eliminações seguidas sem levar dano. Ao completar: toca o áudio "six seven", aparece "67!" grande na tela, +50% de velocidade de movimento por 6 s. Levar dano zera a contagem; o combo pode ser repetido.
- **Pontuação**: pontos por inimigo (maiores para mini-chefes e Professor), bônus por tempo vivo e por vitória.

## 7. Armas

Todas vão do nível 1 ao 7; cada nível melhora um atributo (dano, quantidade, alcance, recarga, duração).

| Arma | Tipo | Comportamento | O que os níveis melhoram |
|---|---|---|---|
| **Cobra Python** | Disparo (café) | Cobrinha verde e amarela que avança serpenteando na direção da mira | Mais cobras por disparo; atravessa mais inimigos |
| **Caramelo** | Contato | Vira-lata caramelo que corre em volta do herói e morde quem encosta | Mais cachorros; voltas mais rápidas e maiores |
| **Mascote do ChatGPT** | Disparo (café) | Mascote flutuante que atira no inimigo mais próximo; 15% de chance de "alucinar" e atirar para um lado aleatório com dano dobrado | Mais disparos; recarga menor |
| **Mascote do Claude** | Contato | Bichinho laranja que "pensa" (barrinha carregando) e golpeia forte o inimigo com mais vida na tela | Pensa mais rápido; o golpe causa dano em área |
| **Gemini** | Disparo (café) | Estrela de quatro pontas que se divide em duas ao acertar | Mais gerações de divisão; mais estrelas |
| **Fusca Azul** | Contato | De tempos em tempos um fusca azul atravessa a tela buzinando; inimigos atingidos ficam "possuídos": param de perseguir o herói e socam o inimigo mais próximo | Mais fuscas; possessão mais longa; recarga menor |

**Colabs**: quando duas armas da receita estão no nível 7, a próxima tela de nível oferece a colab, que substitui as duas.

| Colab | Receita | Comportamento |
|---|---|---|
| **Caramelo no Fusca** | Caramelo + Fusca Azul | O Caramelo dirige o fusca, que circula pela arena sem parar atropelando e possuindo inimigos |
| **Cobras Gêmeas** | Cobra Python + Gemini | Cobras que se dividem em duas a cada acerto |
| **Debate das IAs** | Mascote do ChatGPT + Mascote do Claude | Os dois mascotes flutuam em lados opostos do herói, ligados por um raio contínuo que acerta tudo no meio |

## 8. Itens passivos

Até o nível 3 cada um.

| Item | Efeito por nível |
|---|---|
| Caderno de Resumos | +10% de dano |
| Energético | +10% de velocidade |
| Marmita do RU | recupera 1 de vida a cada 3 / 2 / 1 s |
| Mochila Pesada | +20 de vida máxima |
| Fone de Ouvido | +30% de alcance para puxar notas |
| Relógio de Pulso | -8% de recarga de armas e especial |
| Garrafa Térmica | +25% de café máximo e de recarga de café |

## 9. Arte e som

**Estilo**: pixel art chibi, vista de cima em leve perspectiva, contorno escuro grosso, cores saturadas; combina com a arte reaproveitada do jogo antigo (baú, poções, botões, molduras de painel, moeda, ícones e a fonte Pixelify Sans).

**Geração**: todos os sprites novos são gerados com a ferramenta de imagens (ChatGPT) em fundo transparente, a partir de um prompt-base de estilo comum, e depois reduzidos ao tamanho de jogo por um script em `ferramentas/`. Uma imagem por personagem; a animação é procedural: balanço ao andar, achatamento ao pular, espelhamento horizontal conforme a direção, piscar branco ao levar dano, partículas simples.

Lista de arte nova:
- Heróis: aluno genérico (2 cores) e variante Super Saiyajin.
- Professor genérico.
- 8 lacaios (os mini-chefes usam o lacaio ampliado).
- Armas e ajudantes: cobra, cachorro caramelo, mascote do ChatGPT, mascote do Claude, estrela do Gemini, fusca azul; colabs: Caramelo no Fusca (as outras duas combinam sprites existentes).
- Projéteis e coletáveis: folha de prova, tiro do ChatGPT, nota "10", copinho de café.
- Ícones das cartas: 6 armas, 3 colabs, 7 itens (os itens podem reaproveitar ícones antigos quando combinarem).
- Cenário: chão do pátio em ladrilho que se repete sem emenda, árvores, bancos, postes; fundo e logo da tela de título.

O raio do Zoltraak, a aura do Super Saiyajin, o raio do Debate das IAs, as faíscas e os números de dano são desenhados por código.

**Som**: efeitos sonoros livres (Kenney.nl, licença CC0) para acerto, coleta, nível, baú e buzina do fusca. O áudio do 67 começa como uma voz sintetizada provisória; o grupo pode trocar pelo arquivo que quiser em `assets/sons/67.ogg`.

## 10. Arquitetura

Python 3.12 e Pygame, em ambiente virtual. Nomes de classes e métodos em português.

### Hierarquia

```
Entidade (abstrata: atualizar(dt, jogo), desenhar(tela, camera))
├── SerVivo (abstrata; vida e vida_maxima com @property e validação; receber_dano(), esta_vivo)
│   ├── Jogador (abstrata)
│   │   ├── AlunoAgil
│   │   └── AlunoResistente
│   └── Inimigo (abstrata; mover(dt, jogo) abstrato; ao_morrer(jogo); possessão do Fusca)
│       ├── Bug, CalculadoraBrava, MouseDeBolinha, Caixinha,
│       │   PiCambaleante, Ponteiro, PilhaAA, PenteDeRAM
│       └── Chefe (abstrata; padrões de ataque, barra de vida)
│           └── Professor
├── Projetil → CobraProjetil, EstrelaGemini, TiroChatGPT, FolhaDeProva
├── Ajudante → CachorroCaramelo, FuscaVeiculo, MascoteClaudeAjudante, MascoteChatGPTAjudante
├── Coletavel → Nota, CopoDeCafe, PocaoDeVida, Bau
└── Efeito → TextoFlutuante, Particula, RaioZoltraak

Arma (abstrata; nivel 1..7 com @property e validação; atualizar(dt, jogo, dono); __str__)
├── ArmaDeDisparo (abstrata; municao e municao_maxima com @property e validação)
│   └── CobraPython, MascoteChatGPT, Gemini
├── ArmaDeContato (abstrata) → Caramelo, MascoteClaude, FuscaAzul
└── Colab (abstrata; RECEITAS; @staticmethod colabs_disponiveis(armas))
    └── CarameloNoFusca, CobrasGemeas, DebateDasIAs

Item (abstrata; nivel 1..3; aplicar(jogador)) → CadernoDeResumos, Energetico, MarmitaDoRU,
                                                 MochilaPesada, FoneDeOuvido, RelogioDePulso, GarrafaTermica
Especial (abstrata; recarga; ativar(jogador, jogo)) → Zoltraak, SuperSaiyajin
BonusTemporario (atributo, multiplicador, duração): usado pelo Super Saiyajin e pelo combo 67
Cena (abstrata; tratar_evento, atualizar, desenhar) → CenaTitulo, CenaSelecao, CenaPartida,
                                                      CenaNivel, CenaFimDeJogo, CenaRanking
```

### Composição

- `Aplicacao`: janela, laço principal, pilha de cenas.
- `CenaPartida` contém um `Jogo`.
- `Jogo` contém `Jogador`, `Fase`, `Placar`, `Camera` e a lista de entidades.
- `Jogador` contém suas `Arma`s, seus `Item`s, um `Especial` e os `BonusTemporario` ativos.
- `Fase` contém a linha do tempo (eventos com tempo e ação) e usa `FabricaDeInimigos`.
- `Placar` contém pontos, eliminações, tempo e o contador do combo 67.
- `Ranking` contém uma lista de `RegistroRanking`, salva em `dados/ranking.json`.

### Polimorfismo

`Jogo.atualizar()` percorre todas as entidades num único laço, sem `if` por tipo:

```python
for e in self.entidades:
    e.atualizar(dt, self)
```

O mesmo vale para `desenhar()`, para as armas do jogador (`arma.atualizar(dt, jogo, dono)`), os itens (`item.aplicar(jogador)`) e as cenas. Reações específicas ficam em métodos sobrescritos (`ao_morrer`, `mover`, `ao_coletar`, `ao_acertar`).

### Fábrica e colisão

```python
@FabricaDeInimigos.registrar("bug")
class Bug(Inimigo): ...

inimigo = FabricaDeInimigos.criar("bug", posicao, escala_dificuldade)  # @classmethod
```

Um inimigo novo exige só uma classe nova decorada em um arquivo novo; nenhuma classe existente muda. A fábrica também cria mini-chefes (`criar_gigante`, @classmethod).

`Colisao` reúne @staticmethods: `circulos_colidem(a, b)`, `ponto_no_circulo`, `segmento_acerta_circulo` (raios). Entidades colidem como círculos. Para desempenho, uma `GradeEspacial` divide a arena em células e só testa pares vizinhos.

### Mapeamento dos requisitos

| Requisito do enunciado | Onde está |
|---|---|
| Classe abstrata `Entidade` com `atualizar()` e `desenhar()` | `jogo/nucleo/entidade.py` (ABC) |
| Pelo menos 3 inimigos herdando de uma base | 8 lacaios e o Professor herdam de `Inimigo` |
| Um único laço `for e in entidades: e.atualizar()` sem `if` por tipo | `Jogo.atualizar()` |
| Vida, pontuação e munição com `@property` e validação | `SerVivo.vida`, `Placar.pontos`, `ArmaDeDisparo.municao` (não aceitam negativo; vida e munição não passam do máximo) |
| Jogo contém Jogador, Fase e Placar; Jogador contém Arma | `Jogo.__init__`, `Jogador.armas` |
| `__str__`, `__eq__` ou `__lt__` | `RegistroRanking` (`__lt__`, `__eq__`, `__str__`; o ranking usa `sorted()`); `__str__` em `Placar` e `Arma` |
| Fábrica de inimigos (`@classmethod`) e utilitário de colisão (`@staticmethod`) | `FabricaDeInimigos.criar()`, `Colisao.circulos_colidem()` |

### Recursos

`Recursos` carrega e guarda em cache imagens, fontes e sons (@classmethod). Se um arquivo não existir, gera um substituto (forma colorida com a inicial do nome; som mudo) para o jogo nunca quebrar por falta de arte.

### Pastas

```
main.py                 ponto de entrada
requirements.txt        pygame-ce, pytest
jogo/
  config.py             tamanhos, cores, números de balanceamento
  aplicacao.py          Aplicacao (janela e cenas)
  jogo.py               Jogo (a partida)
  fase.py  placar.py  ranking.py
  nucleo/               entidade.py, ser_vivo.py, colisao.py, grade.py, camera.py, recursos.py, efeitos.py
  jogador/              jogador.py, alunos.py, especiais.py, bonus.py
  inimigos/             inimigo.py, fabrica.py, um arquivo por lacaio, chefe.py, professor.py
  armas/                arma.py, um arquivo por arma, colabs.py
  ajudantes/  projeteis/  coletaveis/
  itens/                itens.py
  cenas/                um arquivo por cena, hud.py, widgets.py
assets/                 sprites/, cenario/, icones/, sons/, fontes/, legado/ (arte reaproveitada)
dados/ranking.json      criado em tempo de execução (ignorado no git)
ferramentas/            scripts de preparo da arte (reduzir, recortar)
testes/                 pytest
docs/                   especificação, diagrama de classes, entregas, registro de uso de IA
```

Usamos `pygame-ce` (versão mantida do Pygame, mesma API `import pygame`), que tem pacotes prontos para Python 3.12 no macOS e no Windows.

## 11. Testes

- **Unidade (pytest)**: validação de `vida`, `pontos`, `municao` e `nivel`; `FabricaDeInimigos` (registrar, criar, nome desconhecido gera erro); `Colisao`; ordem e igualdade de `RegistroRanking`; gravar e ler o ranking; receitas de colab; itens aplicando efeitos; combo 67 (contagem, zerar ao levar dano).
- **Fumaça**: rodar `Jogo` por alguns minutos simulados sem janela (`SDL_VIDEODRIVER=dummy`), com um jogador automático, e verificar que não há erro, que os inimigos da linha do tempo aparecem e que o chefe surge aos 15:00.
- **Manual**: jogar a fase completa com os dois heróis.

## 12. Entregas

| Etapa | Data | O que o projeto fornece |
|---|---|---|
| 1 | 22/10 | Proposta (resumo desta especificação) e diagrama de classes em `docs/entregas/` (Mermaid e imagem) |
| 2 | 05/11 | Protótipo: janela, herói se movendo, um tipo de inimigo, com arte |
| 3 | 26/11 | Hierarquia completa e polimorfismo: todos os inimigos, armas, itens, fase de 15 min |
| 4 | 10/12 ou 14/12 | Versão final, roteiro de defesa oral (perguntas prováveis e respostas), ensaio de requisito surpresa, slides |

Mostra em sala em 03/12: a versão da etapa 3 deve estar jogável e polida até lá.

Processo: registro de uso de IA por etapa em `docs/registro_ia.md`, no formato da tabela do enunciado. Os commits devem ser feitos pelos dois integrantes ao longo das etapas (10% da nota).

## 13. Fora do escopo

Fases 2 em diante, outros professores, loja de melhorias permanentes, gacha, selos, cooperativo local, música própria, caricaturas reais dos integrantes e professores (substituição futura da arte provisória), versão web.
