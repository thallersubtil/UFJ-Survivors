"""O crupiê do cassino: o personagem que toca a mesa, com expressões, falas e animação.

Cada mesa tem o seu (Mesa.PASTA_CRUPIE). A arte fica em assets/crupies/<pasta>/<expressão>.png, uma ilustração da
cintura para cima por expressão: `espera` (recebendo o aluno), `torcida` (durante o sorteio), `riso` (a casa
ganhou) e `choro` (o aluno ganhou). É desenhado direto na tela, em resolução cheia, entre a parede e a mesa.
"""
import math
import random

import pygame

from jogo.nucleo.recursos import Recursos
from jogo.ui.pixel import Paleta as P, ease_back, ease_out, fonte, janela, moldura, onda, texto


class Crupie:
    EXPRESSOES = ("espera", "torcida", "riso", "choro")
    ALTURA = 300                       # na tela de 1280x720
    DURACAO_DA_REACAO = 3.2            # depois disso ele volta a esperar a próxima aposta
    DURACAO_DA_FALA = 2.6
    FALAS = {                          # usadas quando a mesa não tem falas próprias
        "espera": ("Façam suas apostas!", "A casa está aberta."),
        "torcida": ("Vai que vai...", "Olha lá, olha lá..."),
        "riso": ("A casa agradece.", "Volte sempre!"),
        "choro": ("Não acredito!", "Assim a casa quebra!"),
    }

    def __init__(self, pasta, falas=None, sorte=None):
        self.pasta = pasta
        self.falas = {**self.FALAS, **(falas or {})}
        self.sorte = sorte or random.Random()
        self.expressao = "espera"
        self.mudou_em = 0.0
        self.entrou_em = 0.0
        self.fala = self.sorte.choice(self.falas["espera"])
        self._imagens = {}

    @property
    def tem_arte(self):
        return (Recursos.pasta / "crupies" / self.pasta / "espera.png").exists()

    def imagem(self, expressao):
        if expressao not in self._imagens:
            caminho = f"crupies/{self.pasta}/{expressao}.png"
            if not (Recursos.pasta / caminho).exists():
                caminho = f"crupies/{self.pasta}/espera.png"
            self._imagens[expressao] = Recursos.na_altura(Recursos.imagem(caminho), self.ALTURA)
        return self._imagens[expressao]

    def entrar(self, tempo):
        """Chegou à mesa (o aluno trocou de jogo): sobe de trás dela e cumprimenta."""
        self.entrou_em = tempo
        self._mudar("espera", tempo)

    def expressao_para(self, cena):
        """A cara que o momento pede."""
        if cena.girando:
            return "torcida"
        t = cena.tempo_do_resultado
        if t is not None and t < self.DURACAO_DA_REACAO:
            if cena.resultado.ganhou:
                return "choro"
            if not cena.resultado.premio:
                return "riso"
        return "espera"

    def _mudar(self, expressao, tempo):
        self.expressao = expressao
        self.mudou_em = tempo
        self.fala = self.sorte.choice(self.falas[expressao])

    def atualizar(self, cena):
        nova = self.expressao_para(cena)
        if nova != self.expressao:
            self._mudar(nova, cena.tempo)

    def desenhar(self, tela, tempo, centro_x, base_y, recorte):
        """Desenha na tela cheia, com os pés em `base_y` (atrás da mesa), sem sair de `recorte`."""
        if not self.tem_arte:
            return
        img = self.imagem(self.expressao)
        desde = tempo - self.mudou_em
        pulo = ease_back(janela(desde, 0, 0.28), 2.4)                 # estica ao trocar de expressão
        respiro = math.sin(tempo * 2.4) * 0.012
        sx, sy = 1 + (1 - pulo) * 0.10 - respiro, 0.90 + 0.10 * pulo + respiro
        dx = dy = 0.0
        if self.expressao == "torcida":                               # balança de ansiedade
            dx = onda(tempo, 3.2, 5)
            dy = -abs(math.sin(tempo * 12)) * 5
        elif self.expressao == "riso":                                # pula de alegria
            dy = -abs(math.sin(desde * 9)) * 22 * (1 - janela(desde, 0, 1.8))
        elif self.expressao == "choro":                               # treme
            dx = onda(desde, 16, 5) * (1 - janela(desde, 0, 1.2))
        chegada = 1 - ease_out(janela(tempo - self.entrou_em, 0, 0.45))
        dy += chegada * self.ALTURA * 0.8
        img = pygame.transform.smoothscale(img, (max(1, round(img.get_width() * sx)), max(1, round(img.get_height() * sy))))
        anterior = tela.get_clip()
        tela.set_clip(recorte)
        tela.blit(img, img.get_rect(midbottom=(round(centro_x + dx), round(base_y + dy))))
        tela.set_clip(anterior)

    def desenhar_fala(self, ui, tempo, ponta):
        """Balão de fala na camada de pixel art; `ponta` é para onde o rabicho aponta (o crupiê)."""
        desde = tempo - self.mudou_em
        if desde > self.DURACAO_DA_FALA or tempo - self.entrou_em < 0.3:
            return
        frase = self.fala[:max(1, int(desde * 40))]                   # vai sendo escrita
        largura = fonte(11).size(self.fala)[0] + 18
        balao = pygame.Rect(0, 0, largura, 20)
        balao.midtop = (max(ponta[0], 24 + largura // 2), ponta[1] + 7 - int(4 * (1 - ease_back(janela(desde, 0, 0.2)))))
        pygame.draw.polygon(ui, P.ESC, [(ponta[0] - 7, balao.y + 2), (ponta[0] + 7, balao.y + 2), (ponta[0], ponta[1] - 1)])
        moldura(ui, balao, fundo=P.PAPEL, borda=P.PAPEL2, raio=4, brilho=False)
        pygame.draw.polygon(ui, P.PAPEL, [(ponta[0] - 4, balao.y + 3), (ponta[0] + 4, balao.y + 3), (ponta[0], ponta[1] + 2)])
        texto(ui, frase, (balao.x + 9, balao.y + 4), P.ESC, 11, contorno=None)
