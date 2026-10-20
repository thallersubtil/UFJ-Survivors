# Registro de uso de IA

Segue o formato pedido no enunciado: uma tabela por etapa, com onde a IA foi usada e o que o grupo precisou corrigir ou entender.

> **Para o grupo:** as linhas abaixo foram adiantadas a partir do que aconteceu nas sessões de trabalho. Revisem, completem e reescrevam com as próprias palavras antes de cada entrega. O registro vale 5% da nota e precisa refletir o que vocês realmente fizeram e aprenderam.

## Etapa 1: proposta e diagrama de classes

| Etapa | Onde usamos IA | O que precisamos corrigir ou entender |
|---|---|---|
| 1 | Brainstorm de estilos de jogo a partir do projeto antigo (Claude Code) | Descartamos a adaptação direta do RPG de turnos: não tinha "jogador se movendo" nem munição, que o enunciado pede. Escolhemos o estilo survivors. |
| 1 | Brainstorm do tema, dos inimigos e das armas (Claude Code) | Recusamos duas listas de inimigos por não serem visuais nem engraçadas; pedimos que a aparência viesse antes da mecânica e que nada exigisse revisar conteúdo. |
| 1 | Escrita da especificação e do diagrama de classes em Mermaid (Claude Code) | Conferimos se cada requisito da seção 2 do enunciado aparece no diagrama e numa classe concreta. |

## Etapa 2: protótipo

| Etapa | Onde usamos IA | O que precisamos corrigir ou entender |
|---|---|---|
| 2 | Arte dos personagens, inimigos e cenário com a ferramenta de imagens do ChatGPT | Ajustamos tamanhos (o chão e o Pente de RAM saíram desproporcionais) e geramos o Aluno 2 e o Super Saiyajin editando o Aluno 1, para manter o mesmo estilo. |
| 2 | Código do núcleo, do jogador e do primeiro inimigo (Claude Code, com testes automáticos) | |
| 2 e 3 | Animação por quadros e pixel art: folhas de animação geradas pelo ChatGPT e convertidas por script (Claude Code) | A primeira conversão borrou rostos; pedimos arte já em baixa resolução com olhos grandes e uma redução que preserva contorno e brilho |
| 2 e 3 | Estilo de arte: testamos pixel art (HoloCure) com a ferramenta de imagens | Nenhuma variante foi aprovada: a ferramenta não desenha pixel art de verdade (rostos borrados ao reduzir). Mudamos para arte ilustrada estilo Disgaea, em que ela é forte |
| 2 e 3 | Mapa do Campus Jatobá a partir de satélite e OpenStreetMap (Claude Code) | Conferir com fotos reais; corrigir cor de telhado da Biblioteca e a densidade de palmeiras |

## Etapa 3: hierarquia completa e polimorfismo

| Etapa | Onde usamos IA | O que precisamos corrigir ou entender |
|---|---|---|
| 3 | Guia do código para estudo (Claude) | Usado para entender o que já existia antes de mudar: fluxo das telas, laço polimórfico, hierarquias e onde está cada requisito. |
| 3 | Chefes possuídos pelas matérias, `Materia` e `ChefePossuido` (Claude, com testes) | A ideia e a ordem das provas foram nossas (Cálculo I, depois Arquitetura/ED, por último TD/POO, com a matéria mais fácil primeiro). Escolhemos composição (o chefe contém matérias) em vez de uma subclasse por fase, para a troca de matéria no meio da luta. |
| 3 | Três provas em sequência no lugar da partida única de 8 minutos (Claude) | No simulador o chefe de Cálculo I levava quase 5 minutos para cair com o herói ainda fraco; reduzimos a vida dele de 2600 para 1500. |
| 3 | Modo treino e personalização do aluno por recoloração dos sprites (Claude) | A primeira versão da recoloração apagava a transparência (fundo preto); corrigido restaurando o canal alfa. O cabelo dourado do Super Saiyajin precisou ficar fora da recoloração. |
| 3 | Limite de 4 armas e 4 itens, classes (Otaku, Programador, Mestre de RPG) com passiva e crítico (Claude, com testes) | A ideia das classes e do Otaku (Caramelo, crítico crescente, Super Saiyajin) foi nossa. Um boneco articulado desenhado só por código chegou a ser feito, mas foi revertido: queremos as partes geradas no mesmo estilo Disgaea da arte do jogo. |

## Etapa 4: versão final

| Etapa | Onde usamos IA | O que precisamos corrigir ou entender |
|---|---|---|
| | | |
