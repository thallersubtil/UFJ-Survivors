"""Funções de desenho de sprites com animação simples feita por código."""
import math

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
                    escala=(1.0, 1.0), angulo=0.0, deslocamento_y=0.0, sombra=True, alfa=255, aura=None):
    """Desenha a imagem centrada na posição, com os pés na base do sprite.

    `deslocamento_y` levanta o sprite (pulo/balanço) sem mover a sombra. `aura` é a cor do
    contorno da forma suprema (arma no nível máximo): o sprite sai maior e brilhando.
    """
    if aura is not None:
        imagem = Recursos.suprema(imagem, aura)
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


def desenhar_faixa_de_aviso(tela, inicio, fim, largura, cor=(235, 60, 60), tempo=0.0):
    """Faixa translúcida no chão, com setas correndo, que mostra por onde um golpe em linha reta vai passar."""
    inicio, fim = pygame.Vector2(inicio), pygame.Vector2(fim)
    rumo = fim - inicio
    comprimento = rumo.length()
    if comprimento < 1:
        return
    rumo /= comprimento
    lado = pygame.Vector2(-rumo.y, rumo.x) * (largura / 2)
    caixa = pygame.Rect(min(inicio.x, fim.x) - largura, min(inicio.y, fim.y) - largura,
                        abs(fim.x - inicio.x) + largura * 2, abs(fim.y - inicio.y) + largura * 2).clip(tela.get_rect())
    if caixa.width <= 0 or caixa.height <= 0:
        return
    origem = pygame.Vector2(caixa.topleft)
    faixa = pygame.Surface(caixa.size, pygame.SRCALPHA)
    cantos = [inicio + lado - origem, fim + lado - origem, fim - lado - origem, inicio - lado - origem]
    pulso = 0.5 + 0.5 * math.sin(tempo * 14)
    pygame.draw.polygon(faixa, (*cor, round(45 + 40 * pulso)), cantos)
    pygame.draw.line(faixa, (*cor, 220), cantos[0], cantos[1], 3)
    pygame.draw.line(faixa, (*cor, 220), cantos[3], cantos[2], 3)
    passo = max(40.0, largura * 1.6)
    avanco = (tempo * 260) % passo
    for i in range(int(comprimento // passo) + 1):          # setas apontando para onde o golpe vai
        ponta = inicio + rumo * min(comprimento, i * passo + avanco + largura * 0.35) - origem
        asa = rumo * (largura * 0.35)
        pygame.draw.lines(faixa, (255, 240, 200, 190), False,
                          [ponta - asa + lado * 0.7, ponta, ponta - asa - lado * 0.7], max(3, round(largura / 8)))
    tela.blit(faixa, caixa.topleft)
