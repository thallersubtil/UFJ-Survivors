# Créditos da arte e do som

- `assets/sprites/`, `assets/icones/`, `assets/cenario/`: gerados com a ferramenta de imagens do ChatGPT para este trabalho (uso acadêmico, sem fins lucrativos). Mascotes, logos e memes citados pertencem aos seus donos.
- `assets/legado/` e `assets/fontes/`: reaproveitados do jogo "Crônicas do Saber" (Fiuphis/Rpggame). Fonte Pixelify Sans (licença OFL). Os arquivos `pixelify-sans-ufj-*.ttf` são a mesma fonte com o "C" mais aberto (gerados por `ferramentas/ajustar_fonte.py`), renomeada "Pixelify Sans UFJ" como a OFL pede.
- `assets/sons/`: sintetizados por `ferramentas/gerar_sons.py`; o 67 usa a voz do sistema macOS.
- `assets/sprites/<personagem>/`: folhas de animação geradas com a ferramenta de imagens do ChatGPT e convertidas em pixel art por `ferramentas/montar_sprites.py`.
- `assets/cenario/mapa_ufj.png`, `assets/cenario/predios/`, `assets/cenario/mapa_ufj.json`: gerados por `ferramentas/gerar_mapa.py`. Contornos e nomes dos prédios, vias e calçadas: © colaboradores do OpenStreetMap, licença ODbL (openstreetmap.org/copyright). As cores do chão foram classificadas a partir de imagem de satélite Esri World Imagery, usada só como referência (a imagem não é distribuída).
- Referências visuais do portal, da Biblioteca Flor do Cerrado e da Faculdade de Medicina: fotos do Wikimedia Commons ("Entrada da UFJ", "Universidade Federal de Jataí" e "Biblioteca Flor-do-Cerrado", CC BY-SA 4.0; "Fmufj", domínio público).

## Professores (chefes das três provas)

`assets/sprites/professor/`, `assets/sprites/professor_computacao/` e `assets/sprites/professora/`, e as ilustrações de apresentação em `assets/chefes/` (`calculo.png`, `arquitetura_ed.png`, `td_poo.png`): caricaturas dos professores Flávio (Cálculo I), Bruno (Arquitetura de Computadores e Estrutura de Dados) e Emília (Transformação Digital e POO), que aparecem no jogo com o primeiro nome. Foram geradas em novembro de 2026 com a ferramenta de imagens do ChatGPT a partir de fotos de referência dos professores, como homenagem bem-humorada do trabalho. As fotos não estão no repositório.

## Centro Acadêmico (30/10/2026)

`assets/icones/{moeda,pequi,wifi,tenis,oculos,pao_de_queijo,loja_vida,rolamento}.png` e `assets/cenario/centro_academico.png`: gerados com o Nano Banana 2 (via Cloudinary). Para os ícones, a referência de estilo foi uma folha com seis ícones de objetos do HoloCure (moeda, curativo, doce, pena, peixe, chapéu), só para o traço de pixel art; os desenhos são novos e nenhum sprite do HoloCure foi copiado para o projeto. Para o fundo, a referência foi o nosso `titulo_fundo.png`. A folha de ícones foi recortada em 8 e reduzida para 64x64 sem suavizar; o fundo passou por `ferramentas/preparar_arte.py --tela 1280x720`.
