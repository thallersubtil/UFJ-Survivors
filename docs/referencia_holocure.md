# UFJ Survivors x HoloCure: o que aprendemos com a referência

Comparação feita em 30/10/2026 com a engenharia reversa do HoloCure v0.7 (pacote "holocure decompilado", com a documentação dos sistemas em `docs/systems/` e as tabelas de design em `data/design/`). A referência serve **só para estudar estrutura e mecânicas**: arte, sons e textos são da hololive/Kay Yu e ficam fora do repositório. O conteúdo do UFJ Survivors (classes, armas, inimigos, provas, loja, cassino) é nosso.

## O que já adotamos

| Mecânica | Na referência | No UFJ Survivors |
|---|---|---|
| **Rolamento com invencibilidade** | `obj_Player.StartDash`: impulso `dashSPD` que decai (`dashFallOff 0.7`), `invincibilityTimer` durante o dash, recarga (`canDash`) | `Rolamento` (composição no `Jogador`, como o `Especial`): impulso 3,2x que cai até 1x em 0,3 s, invencível enquanto rola e mais 0,1 s, recarga de 1,1 s. Shift ou botão direito. Itens e melhorias mexem em `mult_rolamento` |
| **Velocidade que evolui aos poucos** | Personagens com SPD 1,2–1,6; inimigos bem mais lentos (Shrimp 0,35) e com `levels`: a onda escolhe o nível e o nível sobe o SPD (Shrimp 0,35 → 0,6 → 0,8); SPD sobe com loja e itens | `Inimigo.fator_de_velocidade(escala)`: +10% por ponto de dificuldade, teto de +60%. O aluno ganha +0,6% por nível (teto +30%), mais Energético, Treino no Ginásio e o 67. No começo o aluno mais lento corre mais que o Bug; no fim o Otaku evoluído ainda alcança o Bug mais rápido |
| **Moedas, loja e gacha** | HoloCoins por moeda coletada x multiplicador do estágio + bônus ao terminar; loja com stats por nível e custo em fórmula, aplicados num ponto só no início da run (`ApplyProgressionStats`) | Moeda (coletável) + 150 por prova aprovada + bolsa por minuto sobrevivido. `Progresso` salva em `dados/progresso.json`. `Melhoria` (abstrata) com custo `base x 1,6^nível`, aplicada pelo `Jogador.recalcular_atributos()` igual aos itens |
| **Desbloqueios** | `UnlockThing(..., "ITEM")` por conquista; gacha de personagens | Armas e itens com `PRECO_DESBLOQUEIO > 0` só aparecem nas cartas depois de comprados (Pequi Explosivo, Wi-Fi Eduroam, Tênis de Corrida, Óculos de Grau) |
| **Cassino no hub** | Cassino da Usada: blackjack, roleta, caça-níquel, maior ou menor, pedra-papel-tesoura | Centro Acadêmico (menu principal) com Máquina de Salgadinho (caça-níquel) e Dado do Mestre (d20 acima/abaixo). `JogoDeAposta` é abstrata; retorno esperado abaixo de 100% (testado) |

## Comparação dos outros sistemas

| Sistema | HoloCure | UFJ Survivors | Diferença que importa |
|---|---|---|---|
| Armas | Dados (`config` + níveis) num único `obj_Attack` | Uma classe por arma (`Arma` → `ArmaDeDisparo` / `ArmaDeContato`) | A nossa é melhor para a defesa de POO; mantenham |
| Acerto repetido | Cooldown por projétil e por alvo (`hitCD`, `enemiesInvincMap`) | Conjunto de `id(inimigo)` por projétil; mordidas com espera por id | Ver melhoria 1 |
| Dano | `ATK x damage x 10`, variação de ±10%, crítico > 100% vira multiplicador | Dano fixo da tabela x `multiplicador_dano`; crítico 2x | Ver melhoria 3 |
| Curva de XP | `round((4 x (nível+1))^2,1)` | `6 + 3 x (nível - 1)` (linear) | Linear funciona para 15 min; potência faria sentido com partidas mais longas |
| Cartas de nível | 4 opções, sorteio ponderado (`weight`), reroll, eliminar, guardar | 3 opções sem peso, reroll (R) e pular (P) | Ver melhoria 4 |
| Limites | 6 armas e 6 itens | 4 e 4 (colab libera vaga) | Escolha nossa, para partidas curtas |
| Ondas | Pool ponderado trocado por eventos com hora marcada; nível do inimigo escolhido pela onda; avisos 1 s antes de paredes e cercos | `APRESENTACOES` (sorteio uniforme), `escala_dificuldade` contínua, formação por minuto | Ver melhorias 2 e 5 |
| Mini-chefes | A cada ~2 min | 1 ou 2 por prova | Ok para provas de 5 min |
| Hub | Holo House: pesca, fazenda, culinária, móveis | Centro Acadêmico: loja e cassino | Ver melhoria 7 |

## Onde ainda dá para melhorar (em ordem de valor)

1. **Cooldown de acerto por projétil.** Trocar os conjuntos de `id(inimigo)` (`jogo/projeteis/projeteis.py`, `jogo/ajudantes/ajudantes.py`) por um dicionário `{inimigo: tempo_restante}`, como o `hitCD` da referência. Resolve de quebra a pendência do id reaproveitado.
2. **Avisos antes das formações.** Hoje "Cercado!" aparece junto com o cerco. Mostrar setas na borda da tela 1 s antes (como os `AlertA…D`) e só então criar o círculo ou a parede, em `Fase.formacao_circulo` / `formacao_parede`. Combina com o rolamento: dá para atravessar a parede rolando.
3. **Variação de ±10% no dano** em `Jogo.causar_dano`, para os números não repetirem, e crítico acima de 100% virando multiplicador extra (a Sorte de Calouro e os Óculos de Grau podem passar de 100% no fim).
4. **Cartas com peso e "banir".** Um `PESO` de classe em `Arma`/`Item` (o conteúdo desbloqueado pode começar raro) e uma tecla para banir uma carta pelo resto da partida. Quando não sobrar nada, oferecer cartas de atributo (+vida, +dano) no lugar do Lanche da Cantina.
5. **Pool de inimigos com peso por prova.** `APRESENTACOES` poderia ter `(segundos, nome, peso)` e eventos que tiram um lacaio do sorteio, como o `RemoveMobChoice`. Variantes de papel com a mesma arte (parede lenta de Pilhas, enxame rápido de Bugs) dão variedade sem arte nova.
6. **Moedas por prova e bônus de dificuldade.** Multiplicador de moedas por prova (1,0 / 1,2 / 1,4) como o `coinMultiplier` dos estágios, para valer a pena ir longe.
7. **Mais coisas no Centro Acadêmico.** Lanche da Cantina comprado antes da partida (buff temporário, como a culinária da Holo House), um terceiro jogo no cassino (maior ou menor com as provas antigas) e conquistas que desbloqueiam itens.
8. **Bigorna/carimbos.** Um baú especial que melhora uma arma além do nível 7 ou dá um modificador (tamanho, perfuração), como os Stamps.
