"""Configurações gerais e números de balanceamento do jogo."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_ASSETS = RAIZ / "assets"
PASTA_DADOS = RAIZ / "dados"
ARQUIVO_RANKING = PASTA_DADOS / "ranking.json"

TITULO = "UFJ Survivors"
LARGURA, ALTURA = 1280, 720
FPS = 60
ESCALA_PIXEL = 2          # a arte do mundo é pixel art ampliada 2x, sem suavizar

ARENA_LARGURA, ARENA_ALTURA = 3200, 1800
DURACAO_FASE = 15 * 60
MAX_INIMIGOS = 300
DISTANCIA_REPOSICIONAR = 1400   # inimigo mais longe que isso do herói renasce perto dele
INVENCIBILIDADE_APOS_DANO = 0.5
COMBO_ESPECIAL = 67
BONUS_67_VELOCIDADE = 1.5
BONUS_67_DURACAO = 6.0
SORTEIOS_POR_PARTIDA = 3
CURA_AO_PULAR = 20
LIMITE_COLETAVEIS = 400
LIMITE_EFEITOS = 150

FONTE = "fontes/pixelify-sans-latin-700-normal.woff2"
FONTE_MEDIA = "fontes/pixelify-sans-latin-500-normal.woff2"


class Cor:
    FUNDO = (24, 20, 37)
    PAINEL = (34, 30, 52)
    BORDA = (214, 168, 74)
    BORDA_ESCURA = (16, 12, 24)
    TEXTO = (245, 236, 214)
    TEXTO_FRACO = (168, 160, 190)
    VIDA = (226, 64, 74)
    EXPERIENCIA = (96, 196, 255)
    CAFE = (176, 112, 64)
    DESTAQUE = (255, 214, 92)
    DANO = (255, 255, 255)
    DANO_FORTE = (255, 214, 92)
    DANO_HEROI = (255, 90, 90)
    CURA = (120, 230, 120)
    APROVADO = (120, 230, 120)
    REPROVADO = (240, 80, 80)
    GRAMA_FORA = (36, 58, 40)
