# Pendências

O jogo está completo e jogável (três provas de 5 minutos no mapa do Campus Jatobá, pixel art animada, 8 lacaios, 3 chefes possuídos por 5 matérias, 8 armas (2 compradas na loja), 3 colabs, 9 itens (2 comprados na loja), 3 classes com passiva, rolamento com invencibilidade, Centro Acadêmico com loja e cassino, todas as telas, 301 testes passando). Esta é a lista do que ainda vale fazer, mais ou menos em ordem de prioridade. Ao terminar um item, apague-o daqui no mesmo commit.

## Para o grupo decidir ou fazer

- [ ] **Jogar e calibrar.** O balanceamento foi feito com um jogador automático (`ferramentas/simular_partida.py`). Joguem partidas inteiras com as três classes e ajustem os números se estiver fácil ou difícil demais: `VIDA` e ritmo de cada matéria (`jogo/inimigos/materias/`), duração das provas (`DURACAO_PROVA` em `jogo/config.py`; o semestre inteiro dá de 17 a 19 minutos no simulador), `Fase.alvo_de_inimigos` e `Fase.escala_dificuldade` (`jogo/fase.py`), `DANO`/`VIDA` dos lacaios, `Jogador.experiencia_necessaria`, as passivas (`jogo/jogador/passivas.py`) e o limite de 4 armas e 4 itens (`MAX_ARMAS`, `MAX_ITENS`).
- [ ] **Caricaturas do grupo e do professor.** Gerar as folhas animadas com as caricaturas (receita no `AGENTS.md`). O Mestre de RPG ainda usa a mesma arte do Programador.
- [ ] **Boneco articulado com arte gerada (Thaller).** Aluno masculino ou feminino com cabeça, tronco, braços e pernas separados (animação no estilo Scribblenauts, braços e pernas girando separados do tronco) e mais opções de personalização além das cores (penteado, roupas, acessórios). As partes devem ser geradas no ChatGPT no mesmo estilo Disgaea, com roupas e cabelo em tom neutro para serem recoloridos por código. Uma versão desenhada só por código existiu no commit 4cfec8b (revertido) e pode servir de base para o esqueleto e as poses.
- [ ] **Mais classes.** Receita no `AGENTS.md` ("Classe nova"). Ideia: classe com o ChatGPT ou o Fusca de ativa.
- [ ] **Áudio do 67.** `assets/sons/67.wav` é uma voz sintetizada provisória; troquem pelo áudio do meme se quiserem (mesmo nome de arquivo, formato WAV).
- [ ] **Registro de IA.** Revisar e completar `docs/registro_ia.md` com as próprias palavras (etapas 1 e 2 estão adiantadas).
- [ ] **Entrega 1 (22/10).** Preencher a linha "Integrantes" em `docs/entregas/etapa1_proposta.md` e entregar a proposta com o diagrama.

## Correções pequenas (apontadas na revisão de código)

Cada uma deve vir com um teste que falha antes da correção.

- [ ] Memória de acertos usa `id(inimigo)` (`jogo/projeteis/projeteis.py`, `jogo/ajudantes/ajudantes.py`); um id reaproveitado depois da coleta de lixo pode fazer um inimigo novo ser ignorado. Guardar os próprios objetos no conjunto (entidades já usam igualdade por identidade).
- [ ] Limite de notas (`Jogo.soltar_nota`) soma `len(self._novas)`, que conta qualquer entidade na fila; contar só coletáveis.
- [ ] A tela de nível ou de baú pode abrir sobre uma partida que acabou no mesmo quadro: em `CenaPartida.atualizar`, checar `jogo.terminou` antes de empilhar.
- [ ] A barra de vida do chefe fica embaixo; a especificação pede no topo (`jogo/cenas/hud.py`).
- [ ] O HUD mostra `67` fixo; usar `COMBO_ESPECIAL` de `jogo/config.py`.
- [ ] O bando de Bugs é sempre de 6; a especificação pede de 5 a 8.
- [ ] O nome `ArmaDeContato` engana (o Claude e o Fusca não atacam por contato). Na defesa, explicar como "arma que não usa café", ou renomear para algo como `ArmaSemMunicao` (atualizando diagrama e docs).

## Centro Acadêmico, rolamento e velocidade (novos em 30/10)

- [ ] **Calibrar a economia.** Preços em `jogo/loja/melhorias.py` e `PRECO_DESBLOQUEIO` das armas e itens novos; ganhos em `Inimigo.CHANCE_MOEDA`, `MOEDAS_GIGANTE`, `Jogo.MOEDAS_POR_PROVA` e `MOEDAS_POR_MINUTO`. Joguem algumas partidas e vejam quantas são precisas para comprar algo.
- [ ] **Calibrar rolamento e velocidade.** `Rolamento.DURACAO`, `IMPULSO`, `RECARGA`; `Inimigo.GANHO_VELOCIDADE` e `TETO_VELOCIDADE`; `Jogador.GANHO_VELOCIDADE_POR_NIVEL`. O robô do simulador não rola.
- [ ] Animação própria de rolamento (hoje o sprite gira) e arte própria do projétil do Wi-Fi.
- [ ] Atualizar `docs/entregas/diagrama_classes.png` a partir do `docs/diagrama_classes.mmd` (já tem `Rolamento`, `Melhoria`, `Progresso` e `JogoDeAposta`).
- [ ] Ideias tiradas da referência, em ordem de valor: `docs/referencia_holocure.md`.

## Visual e mapa

- [ ] Ícones das armas e itens no HUD e nas cartas ainda usam a arte antiga (alta resolução, suavizada); trocar por versões em pixel art para combinar com o resto.
- [ ] A tela de título usa a ilustração antiga; dá para refazer em pixel art com o mapa da UFJ ao fundo.
- [ ] O robô do simulador às vezes fica encurralado entre prédios; se pessoas também ficarem, abrir passagens (afastar decorações) ou reduzir os contornos de colisão.

## Entrega 4 (10/12 ou 14/12)

- [ ] Roteiro da defesa oral: perguntas prováveis ("por que `Inimigo` é abstrata?", "o que muda se eu criar um inimigo novo?", "onde está o polimorfismo?", "por que composição e não herança entre `Jogador` e `Arma`?") e respostas apontando o código.
- [ ] Ensaio do requisito surpresa: cada integrante deve conseguir criar um inimigo, uma arma e um item novos em 10 minutos seguindo as receitas do `AGENTS.md`.
- [ ] Slides da apresentação: o jogo funcionando, o diagrama, os requisitos de POO e o processo (commits e registro de IA).

## Ideias para depois (fora do escopo atual)

Fases 2 em diante com outros professores, música, cooperativo local.
