# Guia do código

Mapa de tudo o que já existe no UFJ Survivors, na ordem em que vale a pena entender. Serve para estudar para a defesa oral: cada seção aponta o arquivo e a classe que provam o que está sendo dito.

## 1. O jogo em uma frase

O herói (um aluno) anda pelo Campus Jatobá; as armas atacam sozinhas; ondas de inimigos (objetos das matérias) crescem com o tempo de partida ao longo das três provas de 4 minutos; inimigos mortos soltam notas que dão experiência; a cada nível o jogador escolhe uma carta (arma, melhoria ou item); no fim de cada prova (aos 4, 8 e 12 minutos do relógio, mesmo com o chefe anterior vivo) chega o chefe: um professor possuído pela própria matéria. Vencer os três chefes = "APROVADO!", e a partida segue sem fim (o Projeto de extensão), cada vez mais difícil, até o aluno cair; morrer antes disso = "REPROVADO!".

## 2. Como o programa roda

```
main.py
 └─ Aplicacao (jogo/aplicacao.py)        janela 1280x720 e uma PILHA de cenas
     └─ CenaTitulo -> CenaMatricula -> CenaPartida -> CenaFimDeJogo -> CenaRanking
         └─ CenaTreino (escolhe o professor) -> CenaPersonalizacao -> ...
                                         │
                                         ├─ empilha CenaNivel  (escolher carta ao subir de nível)
                                         ├─ empilha CenaBau    (prêmio do mini-chefe)
                                         └─ empilha CenaPausa  (Esc)
```

Toda tela herda de `Cena` (abstrata, `jogo/cenas/cena.py`) e implementa `tratar_evento`, `atualizar` e `desenhar`. A `Aplicacao` só chama esses três métodos na cena do topo da pilha: polimorfismo também nas telas.

`OpcoesDePartida` (`jogo/opcoes.py`) viaja de tela em tela dizendo como a partida vai ser: quais provas, se é treino, se começa direto no chefe, se o aluno é imortal. `CenaPartida` cria um `Jogo` (a partida) a partir delas com o `@classmethod` `Jogo.a_partir_de(classe, opcoes)` e, a cada quadro, passa o teclado/mouse para ele e chama `jogo.atualizar(dt)` e `jogo.desenhar(tela)`; depois desenha o `Hud` por cima.

## 3. Um quadro da partida (`Jogo.atualizar`, `jogo/jogo.py`)

1. `fase.atualizar(dt, jogo)`: a linha do tempo decide quem nasce agora (pede à `FabricaDeInimigos`).
2. `grade.reconstruir(inimigos)`: grade espacial para achar inimigos próximos sem testar todos contra todos.
3. **O laço polimórfico**: `for e in self.entidades: e.atualizar(dt, self)`. Herói, inimigos, projéteis, notas, efeitos, prédios: todos são `Entidade` e cada um sabe se atualizar. Nenhum `if` por tipo.
4. Entra o que foi criado no quadro (`_incorporar_novas`) e sai o que foi removido (`_limpar`, quem tem `ativo = False`).
5. Câmera segue o herói; se a vida chegou a zero, `terminar(False)`.

`Jogo.desenhar` desenha o chão do mapa e depois as entidades visíveis ordenadas por camada e altura na tela (quem está mais embaixo fica na frente).

Regras centrais também ficam no `Jogo`: `causar_dano` (dano em inimigo, número flutuante, morte), `ferir_jogador`, `dar_experiencia`, `soltar_nota`, `pedir_bau`, `iniciar_chefe`, combo 67.

## 4. As hierarquias

### Tudo que está na arena

```
Entidade (abstrata: atualizar, desenhar)            jogo/nucleo/entidade.py
├─ SerVivo (abstrata: vida com @property)           jogo/nucleo/ser_vivo.py
│  ├─ Jogador (abstrata: criar_arma_inicial, criar_passiva, criar_especial)   jogo/jogador/classes.py
│  │  ├─ Otaku           130 de vida, lento, Caramelo + Instinto Otaku (crítico por nível) + Super Saiyajin
│  │  ├─ Programador      80 de vida, rápido, Cobra Python + Laço de Repetição + Tela Azul
│  │  └─ MestreDeRPG     100 de vida, Gemini + Rolagem de Iniciativa + Zoltraak
│  └─ Inimigo (abstrata: mover)                     jogo/inimigos/inimigo.py
│     ├─ Bug, CalculadoraBrava, MouseDeBolinha, Caixinha (-> CaixinhaPequena),
│     │  PiCambaleante, Ponteiro, PilhaAA, PenteDeRAM      (um arquivo cada)
│     └─ Chefe (abstrata: ataques)                  jogo/inimigos/chefe.py
│        └─ ChefePossuido (abstrata: CONTÉM matérias) jogo/inimigos/chefe_possuido.py
│           ├─ ProfessorDeCalculo          Cálculo I
│           ├─ ProfessorDeArquiteturaEED   Arquitetura de Computadores -> Estrutura de Dados em C
│           └─ ProfessoraDeTDEPOO          Transformação Digital -> POO
├─ Projetil (abstrata: verificar_colisao)           jogo/projeteis/projeteis.py
│  ├─ ProjetilDoHeroi -> CobraProjetil, TiroChatGPT, ProjetilDivisivel (EstrelaGemini, CobraGemea)
│  └─ ProjetilInimigo -> ProjetilDaMateria (o símbolo da matéria: "dx", "*p", "{}"...)
├─ Ajudante (abstrata)    CachorroCaramelo, MascoteFlutuante, FuscaVeiculo, FuscaCircular
├─ Coletavel (abstrata: ao_coletar)   Nota, Ima, PocaoDeVida, Moeda, Bau
├─ Efeito (abstrata)      TextoFlutuante, FaiscaExplosao, RaioZoltraak, AuraSSJ, GolpeClaude, RaioDebate
└─ Predio, Decoracao      obstáculos e enfeites do mapa
```

### Tudo que o jogador carrega (não está na arena)

```
Arma (abstrata: atualizar; nivel 1 a 7 com @property)    jogo/armas/arma.py
├─ ArmaDeDisparo (dispara e espera a recarga: espera com @property)
│  └─ CobraPython, MascoteChatGPT, Gemini
├─ ArmaContinua (age o tempo todo, no próprio ritmo)
│  └─ Caramelo, MascoteClaude, FuscaAzul
└─ Colab (duas armas no nível máximo viram a versão suprema)               jogo/armas/colabs.py
   └─ CarameloNoFusca, CobrasGemeas, DebateDasIAs  (herança múltipla: Colab + família da arma)

Item (abstrata: aplicar)   7 itens passivos em jogo/itens/itens.py
                           (Caderno de Resumos, Energético, Marmita do RU, Mochila Pesada,
                            Fone de Ouvido, Relógio de Pulso, Garrafa Térmica)
Especial (abstrata: ativar)   Zoltraak, SuperSaiyajin       jogo/jogador/especiais.py
BonusTemporario               efeitos com tempo (combo 67, Super Saiyajin)
```

### Partida, mapa e telas

```
Fase (abstrata: criar_eventos)  -> Prova -> ProvaDeCalculo, ProvaDeArquiteturaEED, ProvaDeTDEPOO   jogo/fase.py
Materia (abstrata: ataques)     -> CalculoI, ArquiteturaDeComputadores, EstruturaDeDadosEmC,
                                   TransformacaoDigital, ProgramacaoOrientadaAObjetos   jogo/inimigos/materias/
AcaoDoChefe (abstrata)          -> Investida, Rajada   jogo/inimigos/acoes_do_chefe.py
Mapa (abstrata)                 -> MapaUFJ, Cenario   jogo/mapa.py, jogo/cenario.py
Cena (abstrata)                 -> 8 telas            jogo/cenas/
Placar, Ranking, RegistroRanking                      jogo/placar.py, jogo/ranking.py
FabricaDeInimigos, Colisao, Camera, GradeEspacial, Recursos, Animacao, Animador
```

## 5. Composição (quem contém quem)

- `Jogo` contém `Jogador`, as três `Fase` (provas) e a atual, `Placar`, `Mapa`, `Camera`, `GradeEspacial` e a lista de entidades.
- `ChefePossuido` contém suas `Materia`: o chefe não **é** Cálculo; ele **está possuído** por Cálculo. Por isso composição: o mesmo professor troca de matéria no meio da luta, o que herança não permitiria.
- `Jogador` contém uma lista de `Arma` (até 4), uma lista de `Item` (até 4), uma `Passiva`, um `Especial`, bônus temporários e um `Animador`.
- `Animador` contém várias `Animacao` (parado, andar), e cada `Animacao` contém os quadros.

Por que composição e não herança entre `Jogador` e `Arma`: o jogador **tem** armas, não **é** uma arma; ele ganha, troca e funde armas durante a partida, o que herança não permitiria.

## 6. Onde está cada requisito do enunciado e como explicar

| Requisito | Onde | Como explicar em uma frase |
|---|---|---|
| Classe abstrata | `Entidade` (`atualizar`, `desenhar` com `@abstractmethod`) | Não existe "uma entidade" genérica na tela; ela só define o contrato que o laço do `Jogo` usa. |
| Herança (3+ inimigos) | `Inimigo` e 8 lacaios + `Chefe` > `ChefePossuido` > 3 chefes | O que é comum (vida, perseguir, soltar nota, animação) está em `Inimigo`; cada lacaio só sobrescreve `mover` e às vezes `ao_morrer`. |
| Polimorfismo | `Jogo.atualizar`, laço `for e in self.entidades` | O mesmo `e.atualizar()` faz o Bug correr, o Ponteiro mergulhar e a nota ser atraída. |
| Encapsulamento | `SerVivo.vida`, `Placar.pontos`, `ArmaDeDisparo.espera` | O atributo real é `_vida`; o setter impede vida negativa ou acima do máximo. Na arma, `_espera` são os segundos até o próximo disparo: o setter recusa o que não é número (`TypeError`) e valor negativo (`ValueError`), e é por ele que `atualizar` desconta o tempo. A munição (`municao`) saiu do jogo em 26/11 e a `espera` entrou no lugar dela como exemplo. |
| Composição | ver seção 5 | |
| Métodos especiais | `RegistroRanking.__lt__`, `__eq__`, `__str__` | `__lt__` é o que deixa `sorted()` ordenar o ranking. |
| `@classmethod` | `FabricaDeInimigos.registrar/criar` | A fábrica guarda um registro na própria classe; inimigo novo se registra com um decorador. |
| Polimorfismo (2) | `Passiva.aplicar` | O `Jogador` chama `passiva.aplicar(self)` sem saber qual é a classe, do mesmo jeito que faz com os itens. |
| `@staticmethod` | `Colisao.circulos_colidem` | Função pura de geometria; não precisa de instância. |

Durante o escudo ou a troca de matéria o chefe fica `invulneravel` (propriedade que todo `Inimigo` tem, falsa por padrão): `Jogo.causar_dano` não mostra dano e o chefe não fere por contato. `Prova` e `ChefePossuido` são abstratas de verdade: `CHEFE` e `MATERIAS` são propriedades abstratas que cada subclasse preenche com uma constante.

Pergunta provável: "o que muda se eu criar um inimigo novo?". Resposta: nada nas classes existentes. Arquivo novo em `jogo/inimigos/`, classe herdando de `Inimigo`, `@FabricaDeInimigos.registrar("nome")`, implementar `mover()`; para aparecer, uma linha em `APRESENTACOES` de uma das provas. A receita completa está no `AGENTS.md`. Para um chefe novo, o mesmo vale com `Materia` e `ChefePossuido`.

## 7. As três provas (`jogo/fase.py`)

| Prova | Lacaios | Mini-chefe | Chefe (no fim dos 4 min: 4:00, 8:00 e 12:00 de partida) |
|---|---|---|---|
| `ProvaDeCalculo` | bug, calculadora, pi, caixinha, mouse | Calculadora Gigante (2:30) | Cálculo I |
| `ProvaDeArquiteturaEED` | bug, mouse, pente de RAM, ponteiro, pilha, calculadora | Pente de RAM Gigante (2:30) | Arquitetura de Computadores, depois Estrutura de Dados em C |
| `ProvaDeTDEPOO` | todos | Caixinha Gigante (2:00), Ponteiro Gigante (3:30) | Transformação Digital, depois POO |

- Cada prova é uma subclasse de `Prova` que só preenche dados (`APRESENTACOES`, `FORMACOES`, `MINI_CHEFES`, `CHEFE`); a `Prova` monta a linha do tempo a partir deles.
- Cada prova dura 4 minutos e continua de onde a anterior parou (`INICIO_DIFICULDADE` = 0, 240 e 480 s; `tempo_de_partida` soma os dois); a dificuldade sobe com esse tempo (`escala_dificuldade`).
- **Mais inimigos com o tempo**: `alvo_de_inimigos()` (quantos a fase quer em campo) cresce com o tempo de partida, de 10 no começo a 154 aos 4 min, 346 aos 8 e o teto `MAX_INIMIGOS` (450) aos 10; `intervalo_de_nascimento()` encurta junto (de 0,5 s para 0,125 s entre um grupo e outro). Com chefe em campo o alvo cai para 60% (`alvo_com`).
- **Chefes no relógio**: o evento do fim da prova chama `Fase.chamar_chefe`, que põe o chefe em campo (`Jogo.iniciar_chefe`) e avisa `Jogo.avancar_prova()`: a prova seguinte começa na hora, sem limpar o campo, com o chefe vivo ou não. `Jogo.chefes` guarda os que estão em campo (podem ser dois; `Jogo.chefe` é o mais antigo) e o HUD desenha uma barra para cada um.
- Quando um chefe cai, `Jogo.aprovar_prova(chefe)` guarda a nota da prova dele em `Jogo.notas[índice]`, paga as moedas, cura metade da vida e dá um baú. Com as três provas aprovadas, `venceu` vira verdadeiro e a fase passa a ser `ModoSemFim` (no treino a partida acaba ali).
- **Modo sem fim** (`ModoSemFim`, uma `Fase` como as provas): todos os lacaios, uma formação a cada 45 s, um gigante a cada 60 s, e a dificuldade multiplicada por 1,15 a cada 15 s (`escala_dificuldade` sobrescrito: cresce exponencialmente). Essa conta não aparece na tela: o HUD mostra só "Projeto de extensão" e, no fim, o boletim diz quanto tempo o aluno durou nele e quantos pontos fez ali (`ModoSemFim.pontos_feitos`). Só acaba quando o aluno cai.
- **O que conta como vitória**: derrotar os três chefes. Quem cai no modo sem fim continua aprovado: o boletim mostra as três notas, o ranking registra `venceu`, os pontos levam o bônus de vitória mais o tempo e as eliminações do Projeto de extensão, e as moedas pegas lá também valem (1,6x). Quem cai antes é reprovado em toda prova cujo chefe estava vivo (nota de 4 a 5,9 pelo dano feito nele) e na prova que corria (até 4 pelo tempo); as que não começaram ficam como NÃO CURSOU.

### Como o chefe possuído funciona

- A matéria atual define o nome na tela, a vida, o ritmo e os ataques; o chefe só repassa (`ChefePossuido.ataques` devolve os ataques da matéria).
- Com menos da metade da vida, fica furioso: ataques maiores e mais rápidos.
- `receber_dano` é sobrescrito: se a vida zerou e ainda há matéria, a próxima possui o professor (vida cheia, 1,6 s invulnerável, anúncio da fase 2). Só a última matéria derrota o chefe.
- Ataques prontos em `Materia`: `leque`, `anel`, `rajada` (vários disparos seguidos) e `chamada` (lacaios); `chefe.investir()` faz a investida. As ações de várias etapas são objetos `AcaoDoChefe` (`Investida`, `Rajada`), executados um quadro por vez.

## 8. Sistemas de jogo

- **Armas sem munição**: `ArmaDeDisparo` atira sempre que a `espera` zera e volta a esperar a recarga da arma; não há café nem nada para acabar. O que existia em volta do café foi trocado: a Garrafa Térmica faz toda cura render mais, o lanche virou Caldo de Cana e o Programador ganhou o Laço de Repetição (chance de o disparo repetir) e a Tela Azul (trava os inimigos da tela).
- **Experiência e cartas**: notas dão experiência; `Progressao` (`jogo/progressao.py`) sorteia 3 cartas (arma nova, melhoria, item). R sorteia de novo, P pula. Com tudo no nível máximo, as cartas viram duas: recuperar 30% da vida ou ganhar 50 moedas.
- **Ímã**: cada inimigo comum tem 0,15% de chance de soltar um `Ima`; quem pega chama `Jogo.puxar_experiencia()`, que manda todo coletável `puxar_experiencia()`. Só a `Nota` sobrescreve o método (voa até o aluno); os outros herdam o que não faz nada, então não há `isinstance`. A Revisão para Prova do Monitor usa o mesmo caminho.
- **Cura**: os inimigos não soltam mais poção. Ela vem (1) dos objetos quebráveis e (2) do item Kit de Primeiros Socorros, que a cada 30, 24, 18 ou 12 s (conforme o nível) faz o próximo eliminado soltar uma poção, pelo gancho `Item.ao_eliminar`, chamado em `Jogo._contar_eliminacao`.
- **Objetos quebráveis** (`jogo/inimigos/quebraveis.py`): `CaixaDePapelao`, `Lixeira` e `VasoDePlanta` herdam de `ObjetoQuebravel`, que herda de `Inimigo` para toda arma já saber acertá-los, e sobrescreve `mover` (não anda), `tocar_jogador` (não fere), `empurrar`, `possuir`, `assustar` e `ao_morrer` (solta poção ou moedas). Ficam no grupo `quebravel`, fora da lista de inimigos: não pesam no alvo da fase, e `CONTA_NO_PLACAR = False` os deixa fora das eliminações e do combo. O `Jogo` espalha 80 pelo campus uma vez só, no começo (`_espalhar_quebraveis`): em pontos sorteados, fora dos prédios, a pelo menos 320 de distância uns dos outros e 900 de onde o aluno começa. Sem semente, cada partida tem um arranjo diferente; quebrado, o objeto não volta.
- **Mini-chefe misterioso**: `LocalDeInvocacao.NOME` e `rosto` são propriedades: enquanto o mini-chefe não foi invocado em partida nenhuma, devolvem "Mini-boss misterioso" e um rosto com "?", e o círculo fica lilás. Invocar chama `Jogo.conhecer_mini_chefe`, a `CenaPartida` grava a CHAVE no `Progresso` na hora, e as próximas partidas recebem os conhecidos pelas `OpcoesDePartida`. A marcação no mini-mapa (`Jogo.marcados`) guarda a CHAVE, não o nome, porque vários misteriosos têm o mesmo nome na tela.
- **Colabs**: duas armas no nível máximo viram uma terceira.
- **Combo 67**: 67 eliminações sem levar dano dão velocidade por 6 s e tocam o áudio.
- **Ranking**: 10 melhores em `dados/ranking.json`.

## 9. Arte, som e mapa

- `Recursos` (`jogo/nucleo/recursos.py`) carrega imagens, animações, fontes e sons com cache. Se um arquivo faltar, usa um substituto (círculo colorido, som mudo): o jogo nunca quebra por falta de arte.
- Cada personagem tem uma pasta `assets/sprites/<nome>/` com tiras `parado-4.png` e `andar-4.png`.
- Ferramentas em `ferramentas/`: `gerar_mapa.py` (mapa da UFJ de satélite + OpenStreetMap), `montar_sprites.py` e `pixelizar.py` (folhas de animação), `gerar_sons.py`, `simular_partida.py` (robô que joga sozinho, para balancear).

## 10. Testes

`pytest -q` roda 190 testes sem abrir janela, um arquivo por assunto em `testes/`. Antes de qualquer commit, todos têm que passar.

## 11. O que ainda está aberto

Lista viva em `docs/PENDENCIAS.md`. Resumo: calibrar a dificuldade jogando, trocar arte provisória dos alunos e dos professores, correções pequenas de código, ícones antigos no HUD, roteiro da defesa e ensaio do requisito surpresa.
