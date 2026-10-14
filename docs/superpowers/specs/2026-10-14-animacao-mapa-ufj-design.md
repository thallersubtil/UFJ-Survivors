# Animação, pixel art e mapa da UFJ: especificação

Data: 2026-10-14. Complementa `2026-10-10-ufj-survivors-design.md`; onde as duas divergirem, vale esta.

## 1. Objetivo

Pedidos do grupo:
1. Personagens animados (andar, piscar, parado), não imagens estáticas.
2. Visual mais pixelado, inspirado em HoloCure e Disgaea.
3. Sprites grandes (Professor, mini-chefes) sem perda de qualidade ao ampliar.
4. Partida de 8 minutos em vez de 15, com o balanceamento ajustado.
5. Mapa que reflita a UFJ real (Campus Jatobá), baseado em vista de satélite e fotos.

## 2. Pixel art

> **Revisão (14/10):** reduzir a arte gerada para 48 px e ampliar 2x deixou os personagens borrados (a arte gerada não tem uma grade de pixels regular) e o andar tremia (quadros centralizados pela largura). Agora: sprites guardados no tamanho de tela, reduzidos com LANCZOS, paleta comum por animação, alfa duro e alinhados pelo centro da cabeça e do tronco; andar com 4 quadros (os 2 últimos da folha repetiam a passada); janela em alta resolução com ampliação sem suavizar. O texto abaixo descreve a primeira versão.

- Toda arte do mundo (personagens, inimigos, ajudantes, projéteis, coletáveis, cenário) é guardada em **resolução nativa baixa** e desenhada **ampliada 2x com vizinho mais próximo** (`ESCALA_PIXEL = 2`). Nada do mundo usa `smoothscale`.
- Alturas nativas: heróis 48 px (96 na tela), Professor 80 px (160), lacaios 18 a 28 px, ajudantes e projéteis 10 a 28 px.
- **Mini-chefes têm sprites próprios** pixelizados em resolução nativa 3 vezes maior a partir da arte original em alta resolução, e não o sprite pequeno ampliado. O Professor também tem a sua resolução própria. Assim, quanto maior o personagem, mais detalhe ele tem.
- O HUD e as telas continuam em 1280x720 com a fonte Pixelify; ícones são reduzidos a partir da arte nativa só com vizinho mais próximo e escala inteira quando possível.

**Fluxo de arte** (`ferramentas/pixelizar.py`):
1. A ferramenta de imagens gera uma **folha de animação** (quadros lado a lado, fundo transparente) em pixel art de baixa resolução, usando o sprite atual como referência de design.
2. O script divide os quadros (por colunas vazias, ou em células iguais se estiverem encostados), alinha todos pela base, quantiza para uma paleta comum, reduz para a altura nativa escolhendo a cor mais frequente de cada bloco (com prioridade para brilhos e para o contorno escuro), põe 1 px de contorno escuro e grava `assets/sprites/<personagem>/<animacao>-<n>.png` (uma tira com `n` quadros de mesma largura).
3. A mesma folha pode ser gravada em mais de uma altura (`--gigante`), gerando o sprite do mini-chefe.

## 3. Animação

- `Animacao`: lista de quadros, quadros por segundo, se repete ou não; `quadro(tempo)` devolve a imagem do instante.
- `Animador`: guarda as animações de um personagem pelo nome (`"parado"`, `"andar"`...), a animação atual e o tempo dentro dela; `tocar(nome)` troca (reiniciando só se mudou), `atualizar(dt)`, `quadro_atual`.
- **Composição:** `Jogador`, `Inimigo`, ajudantes e projéteis animados **contêm** um `Animador`. Cada classe escolhe a animação no próprio `atualizar` (por exemplo, o herói toca `"andar"` se está se movendo e `"parado"` se não; o Super Saiyajin usa o conjunto `aluno2_ssj`).
- `Recursos.animacoes(pasta, escala)` carrega todas as tiras de `assets/sprites/<pasta>/`, deduzindo o número de quadros pelo nome do arquivo, com cache. Se a pasta não existir, cai no sprite estático antigo ou no substituto, como hoje.
- Animações mínimas: heróis e Professor têm `parado` (4 quadros, com piscar) e `andar` (6); lacaios têm `andar` (4); ajudantes têm `mover` (2 a 6); cobra e nota têm `mover` (4). A folha de prova e a estrela continuam girando por código.

## 4. Mapa da UFJ (Campus Jatobá)

**Fontes:** imagem de satélite Esri World Imagery (zoom 17) e dados do OpenStreetMap (contornos e nomes dos prédios, vias internas, caminhos de pedestres, piscina, quadra), mais fotos do Wikimedia Commons (entrada, Biblioteca Flor do Cerrado, Faculdade de Medicina) como referência de cores e formas. As fontes ficam em `arte_bruta/mapa/` (fora do git); os créditos vão para `assets/CREDITOS.md`.

**Recorte:** o núcleo do campus, do acesso pela BR-364 até a segunda rotatória da avenida principal, com o gramado oval central, os prédios dos dois lados, o núcleo antigo (telhados de cerâmica), a piscina e a pista. Escala: **4 unidades do jogo por metro**, aproximadamente, o que dá uma arena de cerca de 2600x4000.

**Gerado por ferramenta, não à mão** (`ferramentas/gerar_mapa.py`), produzindo:
- `assets/cenario/mapa_ufj.png`: o chão em resolução nativa (metade da arena), pintado por classe a partir do satélite: grama, gramado mais escuro, terra vermelha do Cerrado e mata, cada uma com textura de pixel art feita por código; por cima, as vias de asfalto com meio-fio e as calçadas do OpenStreetMap.
- `assets/cenario/predios/<id>.png`: cada prédio do OpenStreetMap desenhado em pixel art 3/4 a partir do seu contorno real: paredes com janelas, telhado (branco e cinza nos blocos novos, cerâmica no núcleo antigo, cinza-escuro na Medicina) e uma plaquinha com o nome curto (RU, Biblioteca, Centro de Aulas I...).
- `assets/cenario/mapa_ufj.json`: tamanho da arena, ponto inicial do herói (gramado central), contorno de colisão de cada prédio, posição de cada sprite de prédio e a lista de decorações (árvores nos pontos de mata, palmeiras ao longo da avenida, postes, bancos, o portal de entrada com a bandeira).
- Decorações em pixel art geradas pela ferramenta de imagens: palmeira imperial, ipê-amarelo, árvore do Cerrado, poste, banco, portal da UFJ, bandeira do Brasil (animada).

**No jogo:**
- `MapaUFJ` substitui o `Cenario`: carrega o chão e o JSON, desenha só o trecho visível do chão (ampliado 2x) e cria as entidades `Predio` e `Decoracao`.
- `Predio(Entidade)`: obstáculo com contorno de colisão (polígono real) e sprite; entra no desenho ordenado por profundidade, então personagens atrás do prédio ficam escondidos.
- Herói e inimigos não atravessam prédios: `Colisao.circulo_poligono` e `Colisao.empurrar_para_fora` (`@staticmethod`); prédios ficam numa grade espacial estática para o teste ser barato. Projéteis atravessam prédios (decisão de jogabilidade, mais simples).
- Inimigos não nascem dentro de prédios (a fase sorteia de novo).

## 5. Partida de 8 minutos

| Tempo | Evento |
|---|---|
| 0:00 | Bug |
| 0:40 | Calculadora Brava |
| 1:20 | Mouse de Bolinha |
| 2:00 | Caixinha |
| 2:40 | Mini-chefe: Calculadora Gigante |
| 2:40 | Pi Cambaleante |
| 3:20 | Ponteiro |
| 4:00 | Pilha AA |
| 4:40 | Pente de RAM |
| 5:20 | Mini-chefe: Pente de RAM Gigante |
| a cada 1:00 | Formação (círculo ou parede) |
| 8:00 | Professor |

- `DURACAO_FASE = 480`; a fase usa `self.DURACAO` para o Professor.
- Dificuldade e quantidade de inimigos crescem na mesma proporção que antes, comprimidas em 8 minutos; a experiência por nível cai para o herói chegar perto do mesmo nível final.
- Critérios do simulador (robô imortal): Professor aos 8:00 e derrotado antes de 9:30; nível final entre 25 e 45; pelo menos 4 armas. Robô mortal: sobrevive pelo menos 2 minutos e morre antes de 8:00 na maioria das sementes.

## 6. O que não muda

Os requisitos de POO, as armas, os itens, as colabs, o combo 67, as telas e o ranking. O laço único de `Jogo.atualizar()` continua sem `if` por tipo: `Predio` e `Decoracao` são entidades como as outras.

## 7. Testes

- `Animacao`/`Animador`: quadro certo para cada tempo, repetição e não repetição, troca de animação reinicia só quando muda.
- `Recursos.animacoes`: conta os quadros pelo nome do arquivo; pasta ausente cai no substituto.
- Herói alterna `parado`/`andar`; Super Saiyajin troca o conjunto.
- `Colisao.circulo_poligono` e `empurrar_para_fora` (dentro, encostado, longe, polígono girado).
- Herói e inimigo não atravessam um `Predio`; inimigo não nasce dentro de prédio.
- `MapaUFJ` carrega o JSON real, o herói começa fora de prédios, o chão desenha sem erro.
- Linha do tempo de 8 minutos (apresentações, mini-chefes, Professor aos 480 s).
- Desempenho: 300 inimigos com prédios por perto continuam abaixo de 33 ms por quadro.
