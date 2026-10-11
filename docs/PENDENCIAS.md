# Pendências

O jogo está completo e jogável (fase de 15 minutos, 8 lacaios, Professor, 6 armas, 3 colabs, 7 itens, todas as telas, 146 testes passando). Esta é a lista do que ainda vale fazer, mais ou menos em ordem de prioridade. Ao terminar um item, apague-o daqui no mesmo commit.

## Para o grupo decidir ou fazer

- [ ] **Jogar e calibrar.** O balanceamento foi feito com um jogador automático (`ferramentas/simular_partida.py`). Joguem partidas inteiras com os dois alunos e ajustem os números se estiver fácil ou difícil demais: vida do `Professor` (`jogo/inimigos/professor.py`), `Fase.alvo_de_inimigos` e `Fase.escala_dificuldade` (`jogo/fase.py`), `DANO`/`VIDA` dos lacaios, `Jogador.experiencia_necessaria`.
- [ ] **Caricaturas do grupo e do professor.** Trocar a arte provisória (receita no `AGENTS.md`) e os nomes "Aluno 1", "Aluno 2" e "Professor".
- [ ] **Áudio do 67.** `assets/sons/67.wav` é uma voz sintetizada provisória; troquem pelo áudio do meme se quiserem (mesmo nome de arquivo, formato WAV).
- [ ] **Registro de IA.** Revisar e completar `docs/registro_ia.md` com as próprias palavras (etapas 1 e 2 estão adiantadas).
- [ ] **Entrega 1 (22/10).** Preencher a linha "Integrantes" em `docs/entregas/etapa1_proposta.md` e entregar a proposta com o diagrama.

## Correções pequenas (apontadas na revisão de código)

Cada uma deve vir com um teste que falha antes da correção.

- [ ] Imagem **corrompida** (não ausente) derruba o carregamento: em `Recursos.imagem` (`jogo/nucleo/recursos.py`), tratar `pygame.error` no `pygame.image.load` e usar o substituto.
- [ ] Memória de acertos usa `id(inimigo)` (`jogo/projeteis/projeteis.py`, `jogo/ajudantes/ajudantes.py`); um id reaproveitado depois da coleta de lixo pode fazer um inimigo novo ser ignorado. Guardar os próprios objetos no conjunto (entidades já usam igualdade por identidade).
- [ ] Limite de notas (`Jogo.soltar_nota`) soma `len(self._novas)`, que conta qualquer entidade na fila; contar só coletáveis.
- [ ] A tela de nível ou de baú pode abrir sobre uma partida que acabou no mesmo quadro: em `CenaPartida.atualizar`, checar `jogo.terminou` antes de empilhar.
- [ ] A barra de vida do chefe fica embaixo; a especificação pede no topo (`jogo/cenas/hud.py`).
- [ ] O HUD mostra `67` fixo; usar `COMBO_ESPECIAL` de `jogo/config.py`.
- [ ] `Fase.DURACAO` não é usado; o Professor aparece em `900` fixo em `SemanaDeProvas.criar_eventos`.
- [ ] O bando de Bugs é sempre de 6; a especificação pede de 5 a 8.
- [ ] O nome `ArmaDeContato` engana (o Claude e o Fusca não atacam por contato). Na defesa, explicar como "arma que não usa café", ou renomear para algo como `ArmaSemMunicao` (atualizando diagrama e docs).

## Entrega 4 (10/12 ou 14/12)

- [ ] Roteiro da defesa oral: perguntas prováveis ("por que `Inimigo` é abstrata?", "o que muda se eu criar um inimigo novo?", "onde está o polimorfismo?", "por que composição e não herança entre `Jogador` e `Arma`?") e respostas apontando o código.
- [ ] Ensaio do requisito surpresa: cada integrante deve conseguir criar um inimigo, uma arma e um item novos em 10 minutos seguindo as receitas do `AGENTS.md`.
- [ ] Slides da apresentação: o jogo funcionando, o diagrama, os requisitos de POO e o processo (commits e registro de IA).

## Ideias para depois (fora do escopo atual)

Fases 2 em diante com outros professores, loja de melhorias permanentes, música, cooperativo local.
