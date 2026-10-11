"""Funções de desenho de sprites com animação simples feita por código."""
import pygame

from jogo.nucleo.recursos import Recursos

_sombras = {}


def desenhar_sombra(tela, centro_tela, largura):
    largura = max(6, int(largura))
    if largura not in _sombras:
        altura = max(3, largura // 3)
        sombra = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 70), sombra.get_rect())
        _sombras[largura] = sombra
    sombra = _sombras[largura]
    tela.blit(sombra, sombra.get_rect(center=(round(centro_tela[0]), round(centro_tela[1]))))


def desenhar_sprite(tela, camera, imagem, posicao, *, espelhar=False, piscar=False,
                    escala=(1.0, 1.0), angulo=0.0, deslocamento_y=0.0, sombra=True, alfa=255):
    """Desenha a imagem centrada na posição, com os pés na base do sprite.

    `deslocamento_y` levanta o sprite (pulo/balanço) sem mover a sombra.
    """
    centro = camera.para_tela(posicao)
    base_y = centro.y + imagem.get_height() / 2
    if sombra:
        desenhar_sombra(tela, (centro.x, base_y), imagem.get_width() * 0.75)
    img = imagem
    if piscar:
        img = Recursos.silhueta_branca(img)
    if espelhar:
        img = Recursos.espelhada(img)
    if escala != (1.0, 1.0):
        img = pygame.transform.scale(img, (max(1, int(img.get_width() * escala[0])),
                                           max(1, int(img.get_height() * escala[1]))))
    if angulo:
        img = Recursos.rotacionada(img, angulo)
        retangulo = img.get_rect(center=(round(centro.x), round(centro.y - deslocamento_y)))
    else:
        retangulo = img.get_rect(midbottom=(round(centro.x), round(base_y - deslocamento_y)))
    if alfa < 255:
        img = img.copy()
        img.set_alpha(alfa)
    tela.blit(img, retangulo)
