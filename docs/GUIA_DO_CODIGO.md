# Guia do código

Mapa de tudo o que já existe no UFJ Survivors, na ordem em que vale a pena entender. Serve para estudar para a defesa oral: cada seção aponta o arquivo e a classe que provam o que está sendo dito.

## 1. O jogo em uma frase

O herói (um aluno) anda pelo Campus Jatobá; as armas atacam sozinhas; ondas de inimigos (objetos das matérias) crescem com o tempo ao longo de um semestre de 20 minutos; inimigos mortos soltam notas que dão experiência; a cada nível o jogador escolhe uma carta (arma, melhoria ou item); com hora marcada (5, 10 e 15 minutos do relógio, mesmo com o chefe anterior vivo) chega um chefe: um professor possuído pela própria matéria. Das 15:00 em diante a dificuldade dispara até o aluno cair por volta dos 20:00. Quem derrota os três chefes termina o semestre; quem ainda chega vivo aos 20:00 termina com honras; quem não derrota os três é reprovado.

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
│  ├─ Jogador (abstrata: criar_arma_inicial, criar_habilidades, criar_especial)   jogo/jogador/classes.py
│  │  └─ as 7 classes (Otaku, Programador, MestreDeRPG, Monitor, Gamer, Calouro, CaraDaCarona): arma inicial +
│  │     3 habilidades nas cartas + especial (o do Programador, a ViradaDeNoite, contém a GarrafaDeCafe)
│  └─ Inimigo (abstrata: mover)                     jogo/inimigos/inimigo.py
│     ├─ Bug, CalculadoraBrava, MouseDeBolinha, Caixinha (-> CaixinhaPequena),
│     │  PiCambaleante, Ponteiro, PilhaAA, PenteDeRAM      (um arquivo cada)
│     └─ Chefe (abstrata: ataques)                  jogo/inimigos/chefe.py
│        └─ ChefePossuido (abstrata: CONTÉM matérias) jogo/inimigos/chefe_possuido.py
│           ├─ ProfessorDeCalculo          Cálculo I, depois Cálculo II
│           ├─ ProfessorDeArquiteturaEED   Arquitetura de Computadores -> Estrutura de Dados em C
│           └─ ProfessoraDeTDEPOO          Transformação Digital -> POO
├─ Projetil (abstrata: verificar_colisao)           jogo/projeteis/projeteis.py
│  ├─ ProjetilDoHeroi -> CobraProjetil, TiroChatGPT, ProjetilDivisivel (EstrelaGemini, CobraGemea)
│  └─ ProjetilInimigo -> ProjetilDaMateria (o símbolo da matéria: "dx", "*p", "{}"...)
├─ Ajudante (abstrata)    CachorroCaramelo, MascoteFlutuante, FuscaVeiculo, QuadroGigante, Veterano
├─ Coletavel (abstrata: ao_coletar)   Nota, Ima, PocaoDeVida, Moeda, Bau
├─ Efeito (abstrata)      TextoFlutuante, FaiscaExplosao, RaioZoltraak, AuraSSJ, GolpeClaude, RaioDebate
└─ Predio, Decoracao      obstáculos e enfeites do mapa
```

### Tudo que o jogador carrega (não está na arena)

```
Arma (abstrata: atualizar; nivel 1 a 4 com @property, o 4º é a forma suprema)    jogo/armas/arma.py
│  EXCLUSIVA: a arma inicial de cada classe só ela tem (fora das cartas das outras e das colabs)
├─ ArmaDeDisparo (dispara e espera a recarga: espera com @property)
│  ├─ exclusivas: Lightstick, TecladoMecanico, DadoDeVinteLados, CanetaDeCorrecao, Controle, MapaDoCampus
│  └─ comuns: CobraPython, MascoteChatGPT, Gemini, PequiExplosivo, ReguaDeUmMetro, CorrenteDeWhatsApp
│     (golpes, lightstick, alfinetes e corrente em jogo/ajudantes/golpes.py)
├─ ArmaContinua (age o tempo todo, no próprio ritmo)
│  └─ FuscaAzul (exclusiva); Caramelo, MascoteClaude, WifiEduroam, Apostila, QuadroBranco
└─ Colab (duas armas comuns no nível máximo viram uma arma nova)          jogo/armas/colabs.py
   └─ SerpenteEstelar, MetralhadoraDePrompts, FakeNews, AulaExpositiva, Caramelo5G, CatapultaDoCerrado
      (herança múltipla: Colab + ArmaContinua; ajudantes em jogo/ajudantes/colabs_novas.py)

ReageAoJogo (ganchos: atualizar, ao_acertar, ao_critico, ao_eliminar, ao_ser_atingido...)
├─ Item (abstrata: aplicar)   18 itens passivos em jogo/itens/itens.py
│     Energético, Marmita do RU, Mochila Pesada, Fone de Ouvido, Garrafa Térmica, Tênis de Corrida,
│     Óculos de Grau, Cola, Convite da Atlética, Pendrive, Moeda da Sorte, Jogo de Cintura,
│     Kit de Primeiros Socorros, Atestado Médico, Noite sem Dormir, Pré-treino Duvidoso,
│     Parcelar no Cartão, Mensalidade da Atlética
└─ Habilidade (abstrata, 3 níveis)   3 por classe, nas cartas de nível    jogo/jogador/habilidades.py
Especial (abstrata: ativar)   Zoltraak, SuperSaiyajin       jogo/jogador/especiais.py
BonusTemporario               efeitos com tempo (combo 67, Super Saiyajin)
```

### Partida, mapa e telas

```
Fase (abstrata: criar_eventos)  -> Semestre (o calendário: três ProvaMarcada)   jogo/fase.py
Materia (abstrata: ataques)     -> CalculoI, CalculoII, ArquiteturaDeComputadores, EstruturaDeDadosEmC,
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
- `Jogador` contém uma lista de `Arma` (até 4), uma lista de `Item` (até 4), as `Habilidade` que pegou (até 3, da classe), um `Especial`, bônus temporários e um `Animador`. A `ViradaDeNoite` (especial do Programador) contém a `GarrafaDeCafe`.
- `Animador` contém várias `Animacao` (parado, andar), e cada `Animacao` contém os quadros.

Por que composição e não herança entre `Jogador` e `Arma`: o jogador **tem** armas, não **é** uma arma; ele ganha, troca e funde armas durante a partida, o que herança não permitiria.

## 6. Onde está cada requisito do enunciado e como explicar

| Requisito | Onde | Como explicar em uma frase |
|---|---|---|
| Classe abstrata | `Entidade` (`atualizar`, `desenhar` com `@abstractmethod`) | Não existe "uma entidade" genérica na tela; ela só define o contrato que o laço do `Jogo` usa. |
| Herança (3+ inimigos) | `Inimigo` e 8 lacaios + `Chefe` > `ChefePossuido` > 3 chefes | O que é comum (vida, perseguir, soltar nota, animação) está em `Inimigo`; cada lacaio só sobrescreve `mover` e às vezes `ao_morrer`. |
| Polimorfismo | `Jogo.atualizar`, laço `for e in self.entidades` | O mesmo `e.atualizar()` faz o Bug correr, o Ponteiro mergulhar e a nota ser atraída. |
| Encapsulamento | `SerVivo.vida`, `Placar.pontos`, `GarrafaDeCafe.municao` | O atributo real é `_vida`; o setter impede vida negativa ou acima do máximo. A munição são as doses de café da garrafa do Programador: o setter só aceita número inteiro (`TypeError`) entre 0 e a capacidade (`ValueError`), e é por `gastar()` que cada tiro da Virada de Noite desconta uma dose. |
| Composição | ver seção 5 | |
| Métodos especiais | `RegistroRanking.__lt__`, `__eq__`, `__str__` | `__lt__` é o que deixa `sorted()` ordenar o ranking. |
| `@classmethod` | `FabricaDeInimigos.registrar/criar` | A fábrica guarda um registro na própria classe; inimigo novo se registra com um decorador. |
| Polimorfismo (2) | `ReageAoJogo` (itens e habilidades) | O `Jogador` chama `aplicar`, `ao_acertar`, `ao_eliminar`, `ao_ser_atingido` e os outros ganchos em itens e habilidades juntos (`reagentes`), sem saber qual é qual; cada classe sobrescreve só os que usa. |
| `@staticmethod` | `Colisao.circulos_colidem` | Função pura de geometria; não precisa de instância. |

Durante o escudo ou a troca de matéria o chefe fica `invulneravel` (propriedade que todo `Inimigo` tem, falsa por padrão): `Jogo.causar_dano` não mostra dano e o chefe não fere por contato. `ChefePossuido` é abstrata de verdade: `MATERIAS` é uma propriedade abstrata que cada chefe preenche com uma constante.

Pergunta provável: "o que muda se eu criar um inimigo novo?". Resposta: nada nas classes existentes. Arquivo novo em `jogo/inimigos/`, classe herdando de `Inimigo`, `@FabricaDeInimigos.registrar("nome")`, implementar `mover()`; para aparecer, uma linha em `APRESENTACOES` do `Semestre`. A receita completa está no `AGENTS.md`. Para um chefe novo, o mesmo vale com `Materia` e `ChefePossuido`.

## 7. O semestre (`jogo/fase.py`)

Uma fase só, `Semestre(Fase)`, com a linha do tempo inteira. O calendário (`CALENDARIO`) tem três `ProvaMarcada` (dados: hora, chefe, matéria, rótulo, nível do treino):

| Hora | Chefe | Lacaios que entram perto dele |
|---|---|---|
| 5:00 | Cálculo I, depois Cálculo II | bug, calculadora, pi, caixinha, mouse |
| 10:00 | Arquitetura de Computadores, depois Estrutura de Dados em C | pente de RAM, ponteiro, pilha |
| 15:00 | Transformação Digital, depois POO | (todos os anteriores) |

- `Semestre` só preenche dados (`APRESENTACOES`, `FORMACOES`, `GIGANTES`, `GREVE`) e monta a linha do tempo em `criar_eventos`: aviso de PERIGO e chefe na hora de cada prova, um cerco ou parede a cada ~90 s, três gigantes (3:00, 8:00, 13:00), greve às 7:30 e os avisos das 15:00 e das 19:30.
- **Mais inimigos com o tempo**: `alvo_de_inimigos()` cresce com o relógio até `MAX_INIMIGOS`; `intervalo_de_nascimento()` encurta junto. Com chefe em campo o alvo cai para 60%, e na luta com mini-chefe para 50% (`alvo_com` usa `Jogo.alivio_de_nascimento`, o menor `ALIVIO_NO_CAMPO` entre os inimigos vivos). O dano de cada família sai de um número só (`FRACAO_DO_DANO`: lacaios 0,6, mini-chefes 0,7, professores 1) e a vida dos mini-chefes de `MiniChefe.FRACAO_DA_VIDA`. Ao invocar um mini-chefe, `Jogo.abrir_espaco` tira os lacaios comuns em volta do aluno, como na chegada de um chefe.
- **Chefes no relógio**: `Fase.chamar_chefe(jogo, prova)` põe o chefe em campo com `Jogo.iniciar_chefe(chefe, prova)`, que antes pede a cada inimigo `ao_chegar_o_chefe` (o lacaio comum sai; `Chefe` e `MiniChefe` sobrescrevem para ficar). O relógio não para: `Jogo.chefes` guarda os que estão em campo e o HUD desenha uma barra para cada um.
- Quando um chefe cai, `Jogo.aprovar(chefe)` guarda a nota da prova dele em `Jogo.notas[prova]`, paga as moedas, cura metade da vida e dá um baú. Com as três provas aprovadas, `venceu` vira verdadeiro (no treino a partida acaba ali; no semestre, segue).
- **Reta final**: das 15:00 em diante `escala_dificuldade` multiplica por 1,15 a cada 15 s e, depois das 18:00, por 1,3. Depois dos 20:00 a `furia` da fase multiplica dano e velocidade de todo inimigo em campo (`Inimigo.enfurecer`) e o alvo vai ao teto: ninguém dura muito.
- **O que conta como vitória**: derrotar os três chefes (`Jogo.venceu`, "Fim do semestre!"): o boletim mostra as três notas e o ranking registra `venceu` e o número de chefes. Quem, além disso, está vivo quando o relógio chega aos 20:00 ganha as honras (`Jogo.honras`, marcado nesse quadro, com anúncio), mesmo caindo logo depois na fúria: carimbo HONRAS e o bônus de moedas (`Jogo.bonus_de_honras`: `BONUS_HONRAS` mais `MOEDAS_POR_MINI_CHEFE` por mini-chefe derrotado). Quem cai com chefe de pé é reprovado em toda prova cujo chefe estava vivo (nota de 4 a 5,9 pelo dano feito nele) e na prova que corria (até 4 pelo tempo); as que não começaram ficam como NÃO CURSOU.

### Como o chefe possuído funciona

- A matéria atual define o nome na tela, a vida, o ritmo e os ataques; o chefe só repassa (`ChefePossuido.ataques` devolve os ataques da matéria).
- Com menos da metade da vida, fica furioso: ataques maiores e mais rápidos.
- `receber_dano` é sobrescrito: se a vida zerou e ainda há matéria, a próxima possui o professor (vida cheia, 1,6 s invulnerável, anúncio da fase 2). Só a última matéria derrota o chefe.
- Ataques prontos em `Materia`: `leque`, `anel`, `rajada` (vários disparos seguidos) e `chamada` (lacaios); `chefe.investir()` faz a investida. As ações de várias etapas são objetos `AcaoDoChefe` (`Investida`, `Rajada`), executados um quadro por vez.

## 8. Sistemas de jogo

- **Armas e munição**: `ArmaDeDisparo` atira sempre que a `espera` zera e volta a esperar a recarga da arma. A munição do jogo é do Programador: a Virada de Noite enche a `GarrafaDeCafe` e, segurando Espaço, cada dose é um tiro de código; os copos de café que os inimigos soltam (`CopoDeCafe`) chamam `Jogador.ao_pegar_cafe`, e o especial decide: a Virada põe 10 doses na garrafa, os outros adiantam a recarga.
- **Habilidades**: cada classe tem três (`criar_habilidades`), que aparecem nas cartas de nível (nova ou próximo nível, até 3). Uma habilidade soma um efeito fixo em `aplicar` e reage à partida pelos ganchos de `ReageAoJogo`, os mesmos dos itens: o `Jogo` avisa o `Jogador` (acerto, crítico, eliminação, golpe, rolamento, nível) e ele repassa a itens e habilidades.
- **Experiência e cartas**: notas dão experiência; `Progressao` (`jogo/progressao.py`) sorteia 3 cartas (arma nova, item, habilidade ou melhoria). R sorteia de novo, P pula. Com tudo no nível máximo, as cartas viram duas: recuperar 30% da vida ou ganhar 50 moedas.
- **Ímã**: cada inimigo comum tem 0,15% de chance de soltar um `Ima`; quem pega chama `Jogo.puxar_experiencia()`, que manda todo coletável `puxar_experiencia()`. Só a `Nota` sobrescreve o método (voa até o aluno); os outros herdam o que não faz nada, então não há `isinstance`. A Revisão para Prova do Monitor usa o mesmo caminho.
- **Cura**: os inimigos não soltam mais poção. Ela vem (1) dos objetos quebráveis e (2) do item Kit de Primeiros Socorros, que a cada 30, 24, 18 ou 12 s (conforme o nível) faz o próximo eliminado soltar uma poção, pelo gancho `ao_eliminar`, que `Jogo._contar_eliminacao` repassa pelo `Jogador.avisar_eliminacao`.
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
