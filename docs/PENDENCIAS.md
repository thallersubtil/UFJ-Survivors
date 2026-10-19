# Pendências

O jogo está completo e jogável (três provas de 5 minutos no mapa do Campus Jatobá, pixel art animada, 8 lacaios, 3 chefes possuídos por 5 matérias, 6 armas, 3 colabs, 7 itens, todas as telas, 239 testes passando). Esta é a lista do que ainda vale fazer, mais ou menos em ordem de prioridade. Ao terminar um item, apague-o daqui no mesmo commit.

## Para o grupo decidir ou fazer

- [ ] **Jogar e calibrar.** O balanceamento foi feito com um jogador automático (`ferramentas/simular_partida.py`). Joguem partidas inteiras com os dois alunos e ajustem os números se estiver fácil ou difícil demais: `VIDA` e ritmo de cada matéria (`jogo/inimigos/materias/`), duração das provas (`DURACAO_PROVA` em `jogo/config.py`; o semestre inteiro dá de 17 a 19 minutos no simulador), `Fase.alvo_de_inimigos` e `Fase.escala_dificuldade` (`jogo/fase.py`), `DANO`/`VIDA` dos lacaios, `Jogador.experiencia_necessaria`.
- [ ] **Caricaturas do grupo e do professor.** Gerar as folhas animadas com as caricaturas (receita no `AGENTS.md`) e trocar os nomes "Aluno 1", "Aluno 2" e "Professor".
- [ ] **Áudio do 67.** `assets/sons/67.wav` é uma voz sintetizada provisória; troquem pelo áudio do meme se quiserem (mesmo nome de arquivo, formato WAV).
- [ ] **Registro de IA.** Revisar e completar `docs/registro_ia.md` com as próprias palavras (etapas 1 e 2 estão adiantadas).
- [ ] **Entrega 1 (22/10).** Preencher a linha "Integrantes" em `docs/entregas/etapa1_proposta.md` e entregar a proposta com o diagrama.

## Correções pequenas (apontadas na revisão de código)

Cada uma deve vir com um teste que falha antes da correção.

- [ ] Memória de acertos usa `id(inimigo)` (`jogo/projeteis/projeteis.py`, `jogo/ajudantes/ajudantes.py`); um id reaproveitado depois da coleta de lixo pode fazer um inimigo novo ser ignorado. Guardar os próprios objetos no conjunto (entidades já usam igualdade por identidade).
- [ ] Limite de notas (`Jogo.soltar_nota`) soma `len(self._novas)`, que conta qualquer entidade na fila; contar só coletáveis.
- [ ] A tela de nível ou de baú pode abrir sobre uma partida que acabou no mesmo quadro: em `CenaPartida.atualizar`, checar `jogo.terminou` antes de empilhar.
- [ ] A barra de vida do chefe fica embaixo; a especificação pede no topo (`jogo/cenas/hud.py`).
- [ ] Arte dos chefes: o professor de Cálculo e o de Arquitetura/ED usam a mesma arte; a professora ainda usa a arte do professor (pasta `assets/sprites/professora/` pendente).
- [ ] O HUD mostra `67` fixo; usar `COMBO_ESPECIAL` de `jogo/config.py`.
- [ ] O bando de Bugs é sempre de 6; a especificação pede de 5 a 8.
- [ ] O nome `ArmaDeContato` engana (o Claude e o Fusca não atacam por contato). Na defesa, explicar como "arma que não usa café", ou renomear para algo como `ArmaSemMunicao` (atualizando diagrama e docs).

## Visual e mapa

- [ ] Ícones das armas e itens no HUD e nas cartas ainda usam a arte antiga (alta resolução, suavizada); trocar por versões em pixel art para combinar com o resto.
- [ ] A tela de título usa a ilustração antiga; dá para refazer em pixel art com o mapa da UFJ ao fundo.
- [ ] O robô do simulador às vezes fica encurralado entre prédios; se pessoas também ficarem, abrir passagens (afastar decorações) ou reduzir os contornos de colisão.

## Entrega 4 (10/12 ou 14/12)

- [ ] Roteiro da defesa oral: perguntas prováveis ("por que `Inimigo` é abstrata?", "o que muda se eu criar um inimigo novo?", "onde está o polimorfismo?", "por que composição e não herança entre `Jogador` e `Arma`?") e respostas apontando o código.
- [ ] Ensaio do requisito surpresa: cada integrante deve conseguir criar um inimigo, uma arma e um item novos em 10 minutos seguindo as receitas do `AGENTS.md`.
- [ ] Slides da apresentação: o jogo funcionando, o diagrama, os requisitos de POO e o processo (commits e registro de IA).

## Ideias para depois (fora do escopo atual)

Fases 2 em diante com outros professores, loja de melhorias permanentes, música, cooperativo local.
