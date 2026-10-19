# Guia do código

Mapa de tudo o que já existe no UFJ Survivors, na ordem em que vale a pena entender. Serve para estudar para a defesa oral: cada seção aponta o arquivo e a classe que provam o que está sendo dito.

## 1. O jogo em uma frase

O herói (um aluno) anda pelo Campus Jatobá; as armas atacam sozinhas; ondas de inimigos (objetos das matérias) crescem durante 8 minutos; inimigos mortos soltam notas que dão experiência; a cada nível o jogador escolhe uma carta (arma, melhoria ou item); aos 8:00 chega o chefe (Professor). Vencer o chefe = "APROVADO!"; morrer = "REPROVADO!".

## 2. Como o programa roda

```
main.py
 └─ Aplicacao (jogo/aplicacao.py)        janela 1280x720 e uma PILHA de cenas
     └─ CenaTitulo -> CenaSelecao -> CenaPartida -> CenaFimDeJogo -> CenaRanking
                                         │
                                         ├─ empilha CenaNivel  (escolher carta ao subir de nível)
                                         ├─ empilha CenaBau    (prêmio do mini-chefe)
                                         └─ empilha CenaPausa  (Esc)
```

Toda tela herda de `Cena` (abstrata, `jogo/cenas/cena.py`) e implementa `tratar_evento`, `atualizar` e `desenhar`. A `Aplicacao` só chama esses três métodos na cena do topo da pilha: polimorfismo também nas telas.

`CenaPartida` cria um `Jogo` (a partida) e, a cada quadro, passa o teclado/mouse para ele e chama `jogo.atualizar(dt)` e `jogo.desenhar(tela)`; depois desenha o `Hud` por cima.

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
│  ├─ Jogador (abstrata: criar_arma_inicial, criar_especial)
│  │  ├─ AlunoAgil          80 de vida, rápido, Cobra Python + Zoltraak
│  │  └─ AlunoResistente   130 de vida, lento, Caramelo + Super Saiyajin
│  └─ Inimigo (abstrata: mover)                     jogo/inimigos/inimigo.py
│     ├─ Bug, CalculadoraBrava, MouseDeBolinha, Caixinha (-> CaixinhaPequena),
│     │  PiCambaleante, Ponteiro, PilhaAA, PenteDeRAM      (um arquivo cada)
│     └─ Chefe (abstrata: ataques)                  jogo/inimigos/chefe.py
│        └─ Professor       folhas em leque, investida, chamada de lacaios
├─ Projetil (abstrata: verificar_colisao)           jogo/projeteis/projeteis.py
│  ├─ ProjetilDoHeroi -> CobraProjetil, TiroChatGPT, ProjetilDivisivel (EstrelaGemini, CobraGemea)
│  └─ ProjetilInimigo -> FolhaDeProva
├─ Ajudante (abstrata)    CachorroCaramelo, MascoteFlutuante, FuscaVeiculo, FuscaCircular
├─ Coletavel (abstrata: ao_coletar)   Nota, CopoDeCafe, PocaoDeVida, Bau
├─ Efeito (abstrata)      TextoFlutuante, FaiscaExplosao, RaioZoltraak, AuraSSJ, GolpeClaude, RaioDebate
└─ Predio, Decoracao      obstáculos e enfeites do mapa
```

### Tudo que o jogador carrega (não está na arena)

```
Arma (abstrata: atualizar; nivel 1 a 7 com @property)    jogo/armas/arma.py
├─ ArmaDeDisparo (gasta café: municao com @property)
│  └─ CobraPython, MascoteChatGPT, Gemini
├─ ArmaDeContato (não gasta café)
│  └─ Caramelo, MascoteClaude, FuscaAzul
└─ Colab (duas armas no nível 7 viram uma)               jogo/armas/colabs.py
   └─ CarameloNoFusca, CobrasGemeas, DebateDasIAs  (herança múltipla: Colab + família da arma)

Item (abstrata: aplicar)   7 itens passivos em jogo/itens/itens.py
                           (Caderno de Resumos, Energético, Marmita do RU, Mochila Pesada,
                            Fone de Ouvido, Relógio de Pulso, Garrafa Térmica)
Especial (abstrata: ativar)   Zoltraak, SuperSaiyajin       jogo/jogador/especiais.py
BonusTemporario               efeitos com tempo (combo 67, Super Saiyajin)
```

### Partida, mapa e telas

```
Fase (abstrata: criar_eventos)  -> SemanaDeProvas     jogo/fase.py
Mapa (abstrata)                 -> MapaUFJ, Cenario   jogo/mapa.py, jogo/cenario.py
Cena (abstrata)                 -> 8 telas            jogo/cenas/
Placar, Ranking, RegistroRanking                      jogo/placar.py, jogo/ranking.py
FabricaDeInimigos, Colisao, Camera, GradeEspacial, Recursos, Animacao, Animador
```

## 5. Composição (quem contém quem)

- `Jogo` contém `Jogador`, `Fase`, `Placar`, `Mapa`, `Camera`, `GradeEspacial` e a lista de entidades.
- `Jogador` contém uma lista de `Arma`, uma lista de `Item`, um `Especial`, bônus temporários e um `Animador`.
- `Animador` contém várias `Animacao` (parado, andar), e cada `Animacao` contém os quadros.

Por que composição e não herança entre `Jogador` e `Arma`: o jogador **tem** armas, não **é** uma arma; ele ganha, troca e funde armas durante a partida, o que herança não permitiria.

## 6. Onde está cada requisito do enunciado e como explicar

| Requisito | Onde | Como explicar em uma frase |
|---|---|---|
| Classe abstrata | `Entidade` (`atualizar`, `desenhar` com `@abstractmethod`) | Não existe "uma entidade" genérica na tela; ela só define o contrato que o laço do `Jogo` usa. |
| Herança (3+ inimigos) | `Inimigo` e 8 lacaios + `Chefe`/`Professor` | O que é comum (vida, perseguir, soltar nota, animação) está em `Inimigo`; cada lacaio só sobrescreve `mover` e às vezes `ao_morrer`. |
| Polimorfismo | `Jogo.atualizar`, laço `for e in self.entidades` | O mesmo `e.atualizar()` faz o Bug correr, o Ponteiro mergulhar e a nota ser atraída. |
| Encapsulamento | `SerVivo.vida`, `Placar.pontos`, `ArmaDeDisparo.municao` | O atributo real é `_vida`; o setter impede vida negativa ou acima do máximo. |
| Composição | ver seção 5 | |
| Métodos especiais | `RegistroRanking.__lt__`, `__eq__`, `__str__` | `__lt__` é o que deixa `sorted()` ordenar o ranking. |
| `@classmethod` | `FabricaDeInimigos.registrar/criar` | A fábrica guarda um registro na própria classe; inimigo novo se registra com um decorador. |
| `@staticmethod` | `Colisao.circulos_colidem` | Função pura de geometria; não precisa de instância. |

Pergunta provável: "o que muda se eu criar um inimigo novo?". Resposta: nada nas classes existentes. Arquivo novo em `jogo/inimigos/`, classe herdando de `Inimigo`, `@FabricaDeInimigos.registrar("nome")`, implementar `mover()`; para aparecer, uma linha em `SemanaDeProvas.APRESENTACOES`. A receita completa está no `AGENTS.md`.

## 7. A partida de 8 minutos (`SemanaDeProvas`)

- Um lacaio novo entra no sorteio a cada 40 s: Bug (0:00), Calculadora (0:40), Mouse (1:20), Caixinha (2:00), Pi (2:40), Ponteiro (3:20), Pilha AA (4:00), Pente de RAM (4:40).
- Formações a cada minuto (círculo e parede, alternando).
- Mini-chefes: Calculadora Gigante (2:40) e Pente de RAM Gigante (5:20); soltam baú.
- 8:00: o Professor. Com menos de metade da vida ele fica furioso (ataca mais rápido e mais forte).
- A dificuldade sobe com o tempo (`escala_dificuldade`) e o número de inimigos na tela tem teto (`MAX_INIMIGOS`).

## 8. Sistemas de jogo

- **Café é munição**: `ArmaDeDisparo` gasta café, que recarrega sozinho; sem café atira mais devagar.
- **Experiência e cartas**: notas dão experiência; `Progressao` (`jogo/progressao.py`) sorteia 3 cartas (arma nova, melhoria, item). R sorteia de novo, P pula.
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

Lista viva em `docs/PENDENCIAS.md`. Resumo: calibrar a dificuldade jogando, trocar arte provisória dos alunos e do professor, correções pequenas de código, ícones antigos no HUD, roteiro da defesa e ensaio do requisito surpresa.
