# Plano: semestre de 20 minutos

Especificação escrita pela sessão revisora (Windows, com o HoloCure decompilado como referência), aprovada pelo Thaller e ajustada nas conversas entre as sessões em 27/11/2026. A sessão de desenvolvimento implementa; a revisora revisa cada marco.

## 0. Processo

- Branch `semestre-20min`, a partir de `rascunho/chefes-horario-fixo` (bdb1dd8), que a revisora aprovou como ponto de partida. A árvore do pai dele (7a20c06) é igual à da `main` 488102d.
- Cinco marcos, M1 a M5, nessa ordem. Ao fim de cada um: `pytest -q` verde, push do branch e mensagem para a revisora com o hash, o que mudou, o que ficou de fora e, a partir do M2, a tabela do simulador. Nada vai para a `main` antes da revisão final e da aprovação do Thaller, e nunca antes do M3 aprovado (até lá a munição não existe no código).
- Siga o AGENTS.md: requisitos de POO intactos, teste primeiro, tudo em português, uma linha no `docs/registro_ia.md` por sessão.
- Sem código legado: o que for substituído sai no mesmo marco (classes, constantes, imagens, testes, documentação).
- Esta lista é o recorte; nada além dela.
- M1 a M4: sessão "Entrega da etapa 3". M5: sessão "Chefes em horário fixo", que até o M4 ser aprovado só mexe no simulador.
- `docs/entregas/` guarda o que foi entregue nas etapas 1 a 3 e não é reescrito. Para a entrega 4, o diagrama novo sai de `ferramentas/gerar_entrega.py`, já com a `GarrafaDeCafe`.

## 1. Decisões de design

1. Uma fase só, o semestre, com relógio contínuo.
2. Três chefes principais com hora marcada: Cálculo às 5:00, Arquitetura e ED às 10:00, TD e POO às 15:00, cada um com o aviso de PERIGO. O relógio não para na luta: se um chefe ainda está de pé quando chega a hora do próximo, o próximo vem mesmo assim. Na chegada de cada chefe saem do campo só os lacaios comuns; chefes vivos, mini-chefes e objetos quebráveis ficam.
3. O objetivo é caçar os mini-chefes do mapa (os círculos de invocação). Eles são a principal fonte de níveis; só com os inimigos comuns o aluno não fica forte o bastante para o 2º chefe.
4. Fim da partida, sem corte súbito: a partir das 15:00 a dificuldade escala até o aluno morrer, com certeza, por volta dos 20:00.
   - A curva começa suave e aperta no fim, para não matar quem ainda luta com o 3º chefe às 16:00 (base: a escalada multiplicativa do antigo modo sem fim, com expoente maior a partir das 18:00; o M5 calibra).
   - A partir das 20:00 a velocidade dos inimigos também sobe (fugir e rolar deixam de funcionar), o dano de contato passa da vida máxima possível e o spawn vai ao teto.
   - Avisos: aos 15:00, que a dificuldade começou a subir; aos 19:30, "Faltam 30 s para o fim do semestre!".
   - O resultado é decidido pelos chefes. Com os três derrotados, a morte (em qualquer hora) mostra "Fim do semestre com honras!", paga o bônus (BONUS_HONRAS mais um valor por mini-chefe derrotado) e conta como vitória no ranking. Com algum de pé, reprovado, sem bônus.
   - O antigo modo sem fim vira essa reta final e deixa de existir como modo.
5. A loja tem que fazer diferença: sem melhorias, vencer os três chefes é raro; com a loja cheia, é o normal (metas no M5).

## M1. Estrutura da partida

- As três `Prova` viram uma fase `Semestre(Fase)` com a linha do tempo inteira. `Fase` continua abstrata, com `EventoDaFase`.
  - Pool de inimigos muda com o tempo: as apresentações das três provas numa linha só, cada lacaio entrando perto do chefe da matéria dele.
  - Formações com aviso a cada ~90 s; uma Greve (~7:30); no máximo 3 gigantes com hora marcada (ex.: 3:00, 8:00, 13:00).
  - Chefes: (5*60, "chefe_calculo"), (10*60, "chefe_arquitetura_ed"), (15*60, "chefe_td_poo").
  - Spawn reduzido enquanto há chefe vivo (já existe).
- Chefe derrotado: baú, cura de 50%, moedas e "Aprovado em <matéria>!". O Jogo conta quantos chefes caíram.
- Saem: `DURACAO_PROVA`; fases/índice de fase/troca de fase; `INICIO_DIFICULDADE` e `MULT_MOEDAS` por prova; `semestre()`/`PROVAS` se nada mais usar; o modo sem fim (nome "Projeto de extensão", `pontos_feitos`, o `getattr` na tela de fim, o parâmetro `sem_fim` do Jogo).
- Monitor Possuído com hora marcada sai da linha do tempo (vira mini-chefe de círculo ou é removido; a escolha vai na mensagem do marco).
- Treino: continua escolhendo o professor; "direto no chefe" começa 3 s antes da hora dele.
- Boletim: uma nota por chefe derrotado. Ranking: desempate por mais chefes, depois menos tempo.
- HUD: relógio em contagem regressiva até 20:00, contador "Mini-chefes: 3/11" e, na pausa, o "Calendário de provas".
- Correções da revisão do rascunho:
  - a mira (`inimigo_mais_proximo`) ignora objetos quebráveis, por atributo polimórfico; eles continuam acertáveis por colisão e área. Teste: caixa mais perto que um inimigo, a mira vai no inimigo;
  - pior quadro da lógica no simulador abaixo de 33 ms (o rascunho tinha 125 ms): achar a causa e mandar o número;
  - documentação sem "4, 8 e 12" nem "modo sem fim" (o registro de IA é histórico: só se acrescenta).
- Testes, no mínimo: chefes nas horas certas; relógio não para na luta; honras só com os 3 chefes, com bônus só nesse caso; reprovação sem eles; a reta final mata antes de 20:30 de jogo (semente fixa) um aluno com loja cheia, vida alta e regeneração, e outro com revive e desvio alto.

## M2. Mini-chefes como fonte de níveis e fase 2

- Experiência dos mini-chefes como proporção, sem calibrar números finos: ao morrer, cada mini-chefe solta a experiência equivalente a 2 a 3 níveis do nível atual do aluno, calculada a partir de `experiencia_necessaria` na hora da morte (acompanha qualquer curva que o M5 escolher). O baú continua. Teste: matar um mini-chefe sobe o aluno de 2 a 3 níveis, em níveis diferentes.
- A curva dos inimigos comuns saiu do M2 e foi para o M5 (decisão do Thaller, 27/11: "curva fica pro M5"), porque o M3 e o M4 mudam o dano e a resistência do aluno.
- Fase 2 dos mini-chefes aos 50% de vida, na base `MiniChefe` (método modelo): grito ou balão próprio, flash e aura; ataques 30% mais frequentes; um ataque novo por subclasse, no próprio `atacar`, pelo estado `segunda_fase`. Sem if por tipo.
- Cálculo ganha a segunda matéria (ex.: `CalculoII`, com integrais e séries). Vidas das matérias revistas no M5.
- Animação "atacar" (2 a 4 quadros) para chefes e mini-chefes no Animador, tocada antes do golpe; sem arte, cai no "parado". A arte fica com a sessão dos chefes.
- Base: o M2 parte do branch `mini-chefe/leao-do-proerd` (revisado antes, merge em commit próprio e creditado), que já tem na `MiniChefe` `mostrar`, `encenar`, `agendar`/`cumprir_agenda`, `escolher_animacao` e a segunda fase por constantes. Revisão de f916e84: cada um dos 12 já tem o ataque da fase 2 dentro do próprio `atacar`, decidido por `self.segunda_fase` (polimorfismo pelo estado, não pelo tipo), então o gancho `ataque_da_fase_2` saiu do plano. Ajustes no merge: ataques 30% mais frequentes na fase 2 por padrão na base (valor próprio só onde o golpe da fase 2 é mais pesado, com comentário), aura pulsando na `COR` do mini-chefe na fase 2 (em `MiniChefe.desenhar_corpo`, para todos), a experiência proporcional, e conferir à mão o `MiniChefe.ao_morrer` (CHAVE, Bigorna, `contar_mini_chefe`, anúncio). Com o Leão, os mini-chefes passam a 12: ajustar README e este plano.

## M3. Classes: 3 habilidades nas cartas, gimmick e especial

- `Passiva` vira `Habilidade` (abstrata): NOME, ICONE, DESCRICAO, MELHORIAS, NIVEL_MAXIMO = 3, `nivel` com @property e validação, `aplicar(jogador)` e ganchos vazios `atualizar(dt, jogador, jogo)`, `ao_eliminar(inimigo, jogo)`, `ao_ser_atingido(dano, jogo)`, `ao_critico(inimigo, jogo)`, `ao_rolar(jogo)`.
- O Jogo chama os ganchos por um método do Jogador que percorre itens e habilidades juntos (o laço de `Item.ao_eliminar` em `_contar_eliminacao` passa a ser esse método).
- Cada classe define `criar_habilidades()` com 3 instâncias; o aluno começa sem nenhuma; a carta "HABILIDADE" entra na Progressao com peso parecido com o de arma nova.
- Habilidades e especiais (números de partida; o M5 ajusta; * = gimmick):
  - Otaku: Instinto Otaku; Armadura de Roteiro (ao chegar a 0 fica com 1 e invencível 2/3/4 s, recarga 90/75/60 s); Poder da Amizade (+5/7/10% de ATK por ajudante em campo, até 50%). Especial*: Super Saiyajin em níveis (SSJ, SSJ2, SSJ3 a cada uso).
  - Programador: Laço de Repetição (projéteis extras, a do rascunho); Cafeinado (armas recarregam 1,6% mais rápido por nível e a garrafa ganha +20/40/60 doses); *Compilar (andando e atacando acumula "linhas"; parado 1 s, solta um pulso de 1/1,5/2x a força acumulada). Especial: Virada de Noite com a Garrafa de Café (abaixo).
  - Mestre de RPG: Rolagem de Iniciativa; Ficha de Personagem (a cada 15 s, +30/40/50% num atributo sorteado por 15 s); Teste de Resistência (ao levar golpe, d20 anula com 18+/16+/14+). Especial: Zoltraak com dano 8d6. *Gimmick: a arma inicial Dado de 20 Lados (M4).
  - Monitor: Plantão de Dúvidas; Caneta Vermelha (10/15/20% de marcar com X: +25/33/50% de dano, pode curar ao morrer); *Horário de Atendimento (parado 1 s: inimigos em volta -20/30/40% de velocidade e cura de 2/3/4% a cada 2 s). Especial: Revisão para Prova + 10 s de zona de revisão com invencibilidade.
  - Gamer: Reflexo; *Frame Perfect (rolar no último instante antes de um golpe: câmera lenta de 1 s e +30/45/60% de ATK por 8 s); Combo (50 acertos sem levar dano: +20/30/40% de velocidade e de golpe duplo por 10 s, contador no HUD). Especial: Tela Azul (a do rascunho, que trava os inimigos e apaga os projéteis), com ícone próprio. Saem Alt+F4 e Speedrun.
  - Calouro: Sede de Aprender; Veterano Camarada (ajudante com a arma inicial a 50/75/100%); Perdido no Campus (+3/4/5% de velocidade por inimigo perto, até 80%, e mais experiência de quem morre perto). *Períodos (a cada 10 níveis, "2º período!" e um bônus fixo pequeno). Especial: Calourada (40% de chance de os inimigos em volta virarem aliados por 8 s; os outros -30% de ATK), no lugar de Trote Reverso.
  - Cara da Carona: Carona Solidária; Buzina (a cada 10 s, onda de 100/150/200% com atordoamento); *Carro Lotado (+3/4/5% de ATK por passageiro ativo, até 60%). Especial: Lotação.
- Saem: `Passiva` e as passivas que não viraram habilidade, Speedrun e Trote Reverso (com testes e textos).
- **Munição: Garrafa de Café** (mesmo commit, para o requisito não ficar quebrado no meio):
  - `jogo/jogador/garrafa_de_cafe.py`, classe `GarrafaDeCafe`: `capacidade`; `municao` com @property e setter que valida (TypeError se não for int, bool não vale; ValueError abaixo de 0 ou acima da capacidade); `encher()`, `gastar(doses=1) -> bool`, `vazia`.
  - `ViradaDeNoite(Especial)` contém uma `GarrafaDeCafe`. Ativar enche 100 doses; segurando Espaço, dispara uma rajada de código na mira, 10 tiros por segundo, 1 dose por tiro; soltar guarda as doses. Vazia: a Virada acaba e o Programador fica 3 s com "SEM CAFÉ!" (-30% de velocidade); com o botão apertado e a garrafa vazia, não sai tiro.
  - O coletável Café vale +10 doses para quem tem garrafa e +3% de carga do especial para os outros, por `Jogador.ao_pegar_cafe(jogo)` sobrescrito (sem isinstance).
  - HUD: barra de café (`Cor.CAFE`) abaixo da barra do especial, com "64/100", só para quem tem garrafa (o especial devolve `medidor_extra` ou `None`), piscando abaixo de 20%.
  - Testes em `testes/test_garrafa_de_cafe.py`: setter recusa `True`, `1.5`, `"10"`, `-1`, `capacidade+1`; `gastar` não fica negativo; com a Virada ativa e o botão apertado sai tiro até zerar e depois nenhum; o café coletado não passa da capacidade.
  - No mesmo commit, reescrever os testes do rascunho que proíbem munição e café (`test_sem_municao.py`) e atualizar a linha da munição no README, no AGENTS e no `.mmd` para `GarrafaDeCafe.municao`. O `espera` com @property nas armas fica, mas não é ele que cumpre o requisito.

## M4. Armas e itens

- Armas continuam com NIVEL_MAXIMO = 4 e forma suprema no 4º. Novas: Dado de 20 Lados (arma inicial do Mestre de RPG: dano = número tirado, 20 crítico triplo, 1 erra; suprema com 3 dados e vantagem; o Gemini vira arma comum); Régua de 1 Metro (arco à frente na mira; suprema frente e trás); Caneta Bic (estocadas à frente; suprema deixa poça de tinta que fere); Corrente de WhatsApp (pula de inimigo em inimigo). Colab: Corrente de WhatsApp + Mascote do ChatGPT = Fake News. As corpo a corpo têm animação de golpe.
- Itens que saem: Caderno de Resumos e Relógio de Pulso.
- Refeitos: Energético (+40% de velocidade, +10% de recarga, -20% de vida máxima); Mochila Pesada (-25% de dano recebido, -10% de velocidade, 50% de devolver 200%); Marmita do RU (+15 de vida máxima; cada 6 de vida máxima dá +1% de dano da arma inicial e do especial); Fone de Ouvido (15% de anular um golpe e soltar onda que empurra).
- Novos: Atestado Médico (1 revive com 50%, derruba os não-chefes em volta); Noite sem Dormir (1,3x de dano e +10% de recarga, leva +30%); Pré-treino Duvidoso (perde 5% de vida por segundo até 1, +40% de ATK); Parcelar no Cartão (30% do golpe na hora, o resto aos poucos); Mensalidade da Atlética (-3 moedas por segundo; com moedas, +30% de ATK e -10% de dano recebido).
- Ficam: Cola, Convite da Atlética, Pendrive, Moeda da Sorte, Jogo de Cintura, Óculos de Grau, Garrafa Térmica (a do rascunho, que faz a cura render mais), Tênis de Corrida, Kit de Primeiros Socorros (com ícone próprio). O Bandejão Completo sai do plano (igual à Garrafa Térmica).
- O `isinstance(item, OculosDeGrau)` da Cola vira atributo polimórfico (ex.: `disfarce_de_cola`).
- Conferir lanches e melhorias da loja que usam ícones de itens removidos.

## M5. Balanceamento e loja (sessão "Chefes em horário fixo")

- Linha de base (main 488102d, semente 3, robô antigo): o robô morre cedo demais para servir de medida.
- Primeira medida do robô novo (sessão dos chefes, 27/11, sem imortal): loja vazia caçando morre na mediana às 3:44 e nunca vence o Cálculo; loja cheia caçando morre às 4:37, vence o Cálculo em 14% e os três em 10%. O jogo está difícil demais no começo, não no fim: a primeira alavanca é a pressão dos primeiros 5 minutos (alvo inicial, intervalo de nascimento, dano dos lacaios), antes de qualquer ajuste na reta final.
- Caçar hoje mata mais cedo do que não caçar. Conferir se o robô espera um nível mínimo para invocar (o jogador de verdade espera) e se `escala_dos_mini_chefes` (1 + tempo/180) não deixa o mini-chefe forte demais para os níveis 1 a 3. O objetivo do Thaller é que caçar seja o caminho para ficar forte: caçar tem que compensar.
- Revisão do robô (0349e51, no Windows, `--todas-as-classes --sementes 2`): loja vazia, ninguém vence o Cálculo, mediana de morte às 3:59 e nenhum mini-chefe, porque o robô morre antes do nível 6 que exige para caçar; loja cheia, 14% de honras (Programador e Monitor), mediana às 3:18, Gamer caindo às 2:12; diferença entre classes de 50 pontos (limite: 25). Antes de mexer em números, conferir com `--detalhe` se Gamer, Cara da Carona e Mestre de RPG morrem cedo por causa do robô (alcance do Controle, Fusca fora do alcance) e não das classes.
- Robô: quando a Virada de Noite com a Garrafa de Café entrar (M3), ele precisa segurar o especial enquanto houver café e alvo (no commit da garrafa ou logo depois). Na carta de nível máximo, trocar a busca da palavra "vida" na descrição por um campo da Opcao (ex.: `cura=True`).
- Curva de experiência dos comuns (veio do M2): XP_BASE/XP_LINEAR/XP_QUADRATICO e valor das notas para quem não caça chegar ~ao nível 7 / 10 / 13 nos três chefes. Nada de mexer nisso, nas vidas ou na loja antes do M4 aprovado.
- Robô: desviar com o rolamento, chegar perto o bastante, escolher cartas por prioridade simples, caçar mini-chefes (sem chefe vivo, ir ao círculo mais perto, invocar e lutar).
- Simulador: `--loja nada|metade|cheia`, `--sementes N`, `--todas-as-classes`, `--sem-caca`. Uma linha por partida (nível na chegada de cada chefe, hora em que cada chefe caiu, mini-chefes derrotados, resultado, moedas) e uma tabela-resumo por classe.
- Metas (sem `--imortal`; 7 classes x 5 sementes):
  - sem caça, loja vazia: nunca vence o 2º chefe;
  - caçando, loja vazia: vence o 1º em >= 80%, os três em <= 15%, partida mediana de 9 a 14 min;
  - caçando, loja pela metade (~5.000 moedas): vence os três em 40 a 60%;
  - caçando, loja cheia: vence os três em >= 85%;
  - nível na chegada dos chefes (caçando, sem loja): perto de 10 / 17 / 23;
  - classe mais forte contra a mais fraca: no máximo 25 pontos percentuais de vitória.
- Economia: partida sem loja que morre no 2º chefe, 250 a 450 moedas; com honras, 900 a 1.300; encher a loja leva de 15 a 25 partidas.
- Medir se a cura (quebráveis, Kit, cartas de nível máximo) basta para as metas sem loja antes de mexer em vida.
- `MAX_INIMIGOS` 450 só fica se o pior quadro ficar abaixo de 33 ms com o pico real. Hoje formações, gigantes e chamadas dos chefes passam do teto (pico de 479 antes das 20:00): decidir se o teto vale para todos antes dos 20:00.
- Reta final: às 15:00 a dificuldade está em 6 e chega a 9,1 às 15:59, 27,9 às 17:59 e 70 às 18:59, com o 3º chefe chegando às 15:00. Se "loja cheia vence os três em >= 85%" não fechar, suavizar primeiro 15:00 a 18:00 (fator menor, ou a reta final começando quando o 3º chefe cai, com teto às 16:30). Não mexer na vida do chefe.
- Bigorna: saem 11 por partida (uma por mini-chefe) contra 12 carimbos possíveis (4 armas x 3). Conferir se isso não deixa carimbar tudo sempre.

## Arte para gerar (no estilo atual)

Ícones das 21 habilidades e dos especiais novos (Calourada, Tela Azul); SSJ2 e SSJ3 (variações de cor ou aura); armas novas (Dado de 20 Lados, Régua de 1 Metro e Caneta Bic com golpe e suprema, Corrente de WhatsApp, colab Fake News); ícones dos itens novos e refeitos; animação "atacar" dos 3 professores e dos mini-chefes, aura da fase 2 e ilustração de apresentação para quem não tem; cor e símbolo da matéria nova de Cálculo; telas de fim "Fim do semestre com honras!" e "Reprovado: o semestre acabou".

## Limpeza e documentação (último commit antes da revisão final)

README (calendário de provas, classes com habilidades, controles); AGENTS.md (mapa do código, receitas "Habilidade nova" e "Mini-chefe novo com fase 2", classe com `criar_habilidades()`); `docs/PENDENCIAS.md` em dia; diagrama `.mmd` com `Habilidade`, `Semestre` e `GarrafaDeCafe`; linha no registro de IA. Grep por nomes removidos (Prova, DURACAO_PROVA, Passiva, Speedrun, TroteReverso, CadernoDeResumos, RelogioDePulso, ModoSemFim, sem_fim) só pode achar o que é intencional. Apagar imagens que nada mais carrega.
