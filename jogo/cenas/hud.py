"""Informações da partida desenhadas por cima do jogo, no estilo do HoloCure (HUD A aprovado)."""
import math

import pygame

from jogo.config import COMBO_ESPECIAL
from jogo.nucleo.recursos import Recursos
from jogo.ui.pixel import (A, ESCALA, L, CamadaPixel, Paleta as P, barra, ease_back, fonte, icone, janela, moldura,
                           no_quadrado, texto)


class Hud:
    VELOCIDADE_ATRASO = 0.6      # fração da vida por segundo que o branco do dano perde
    ESPERA_ATRASO = 0.25         # o branco fica parado um instante antes de cair
    DURACAO_DESTAQUE = 0.8       # pulso da etiqueta de nível ao subir

    RETRATO = pygame.Rect(9, 13, 40, 40)      # quadro do rosto do herói, na camada

    def __init__(self):
        self.camada = CamadaPixel()
        self.tempo = 0.0
        self.vida_atrasada = None
        self._espera = 0.0
        self._nivel_visto = None
        self.destaque_nivel = 0.0

    # ------------------------------------------------------------ estado que anima
    def atualizar(self, dt, jogo):
        j = jogo.jogador
        self.tempo += dt
        frac = j.vida / j.vida_maxima
        if self.vida_atrasada is None or frac >= self.vida_atrasada:
            self.vida_atrasada = frac
            self._espera = self.ESPERA_ATRASO
        else:
            self._espera -= dt
            if self._espera <= 0:
                self.vida_atrasada = max(frac, self.vida_atrasada - self.VELOCIDADE_ATRASO * dt)
        if self._nivel_visto is not None and j.nivel > self._nivel_visto:
            self.destaque_nivel = self.DURACAO_DESTAQUE
        else:
            self.destaque_nivel = max(0.0, self.destaque_nivel - dt)
        self._nivel_visto = j.nivel

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela, jogo):
        ui = self.camada.limpar()
        self._experiencia(ui, jogo)
        self._heroi(ui, jogo)
        self._vagas(ui, jogo)
        self._tempo_e_placar(ui, jogo)
        self._chefe(ui, jogo)
        self._anuncios(ui, jogo)
        self.camada.apresentar(tela)
        self._rosto_nitido(tela, jogo.jogador)
        self._rumo_dos_mini_chefes(tela, jogo)
        if jogo.perigo > 0:
            self._perigo(tela)

    MARGEM_DO_RUMO = 70

    def _rumo_dos_mini_chefes(self, tela, jogo):
        """Mini-chefe marcado no mini-mapa e fora da tela: o rosto aparece na borda, com uma seta para ele."""
        largura, altura = tela.get_size()
        meio = pygame.Vector2(largura / 2, altura / 2)
        for marcador in jogo.marcadores():
            if marcador.NOME not in jogo.marcados:
                continue
            na_tela = jogo.camera.para_tela(marcador.posicao)
            if 0 <= na_tela.x <= largura and 0 <= na_tela.y <= altura:
                continue
            rumo = na_tela - meio
            fator = min((largura / 2 - self.MARGEM_DO_RUMO) / max(1.0, abs(rumo.x)),
                        (altura / 2 - self.MARGEM_DO_RUMO) / max(1.0, abs(rumo.y)))
            ponto = meio + rumo * fator
            centro = (round(ponto.x), round(ponto.y))
            cor = (255, 214, 92)
            direcao = rumo.normalize()
            ponta = ponto + direcao * (34 + 4 * math.sin(self.tempo * 6))
            lado = pygame.Vector2(-direcao.y, direcao.x) * 9
            pygame.draw.polygon(tela, cor, [ponta, ponto + direcao * 22 + lado, ponto + direcao * 22 - lado])
            pygame.draw.circle(tela, (16, 12, 24), centro, 22)
            rosto = Recursos.imagem(marcador.rosto, 36)
            tela.blit(rosto, rosto.get_rect(center=centro))
            pygame.draw.circle(tela, cor, centro, 22, 3)

    def _perigo(self, tela):
        """Aviso de chefe chegando: faixas zebradas correndo, borda vermelha pulsando e PERIGO! piscando."""
        largura, altura = tela.get_size()
        pulso = 0.5 + 0.5 * math.sin(self.tempo * 12)
        veu = pygame.Surface((largura, altura), pygame.SRCALPHA)
        veu.fill((200, 20, 30, int(26 + 34 * pulso)))
        pygame.draw.rect(veu, (255, 40, 50, int(150 + 90 * pulso)), veu.get_rect(), 14)
        tela.blit(veu, (0, 0))
        amarelo, preto, alto = (250, 204, 40), (22, 18, 26), 58
        for y, sentido in ((int(altura * 0.25), 1), (int(altura * 0.68), -1)):
            faixa = pygame.Surface((largura, alto))
            faixa.fill(amarelo)
            passo = int(self.tempo * 260 * sentido) % 80
            for x in range(-160 + passo, largura + 160, 80):               # listras na diagonal
                pygame.draw.polygon(faixa, preto, [(x, 0), (x + 40, 0), (x + 40 - alto, alto), (x - alto, alto)])
            pygame.draw.rect(faixa, preto, (0, 12, largura, alto - 24))
            passo_texto = int(self.tempo * 320 * -sentido) % 300
            for x in range(-300 + passo_texto, largura + 300, 300):
                texto(faixa, "PERIGO!", (x, alto // 2), amarelo, 23, contorno=None, ancora="midleft")
            pygame.draw.line(faixa, preto, (0, 0), (largura, 0), 3)
            pygame.draw.line(faixa, preto, (0, alto - 1), (largura, alto - 1), 3)
            tela.blit(faixa, (0, y))
        if int(self.tempo * 5) % 2 == 0:
            texto(tela, "PERIGO!", (largura // 2, int(altura * 0.47)), (255, 60, 60), 92, ancora="center")
            texto(tela, "o chefe está chegando", (largura // 2, int(altura * 0.47) + 62), P.BRANCO, 23, ancora="center")

    def _rosto_nitido(self, tela, jogador):
        """O rosto vai direto na tela, em resolução cheia: pela camada (metade da resolução) sairia borrado."""
        rosto = jogador.rosto(self.RETRATO.w * ESCALA)
        if rosto is not None:
            tela.blit(rosto, (self.RETRATO.x * ESCALA, self.RETRATO.y * ESCALA))

    def _experiencia(self, ui, jogo):
        j = jogo.jogador
        barra(ui, (0, 0, L, 7), j.experiencia / j.experiencia_necessaria, P.AZUL, P.AZUL2, fundo=(20, 18, 40),
              brilho_t=self.tempo * 0.5)

    def _retrato(self, jogador):
        animacoes = jogador.animador.animacoes
        animacao = animacoes.get("parado") or next(iter(animacoes.values()))
        quadro = animacao.quadros[int(self.tempo * 6) % len(animacao.quadros)]
        caixa = quadro.get_bounding_rect()
        if caixa.w and caixa.h:
            quadro = quadro.subsurface(caixa)
        return no_quadrado(quadro, 74)

    def _heroi(self, ui, jogo):
        j = jogo.jogador
        moldura(ui, (6, 10, 46, 46), fundo=(52, 74, 150), raio=4)
        if j.rosto(self.RETRATO.w * ESCALA) is None:        # sem a arte do rosto: o próprio boneco, de perto
            retrato = self._retrato(j)
            ui.subsurface(self.RETRATO).blit(retrato, retrato.get_rect(midtop=(20, 2)))
        pulso = self.destaque_nivel / self.DURACAO_DESTAQUE
        tag = pygame.Rect(0, 0, int(30 * (1 + 0.3 * pulso)), int(12 * (1 + 0.3 * pulso)))
        tag.center = (29, 58)
        moldura(ui, tag, fundo=P.OURO if pulso else P.AZUL2, raio=2, brilho=False)
        texto(ui, f"NV {j.nivel}", tag.center, P.ESC if pulso else P.BRANCO, 11, contorno=None, ancora="center")

        texto(ui, j.NOME.upper(), (58, 10), P.BRANCO, 11)
        barra(ui, (58, 22, 112, 11), j.vida / j.vida_maxima, P.VERM, P.VERM2, atraso=self.vida_atrasada)
        texto(ui, f"{round(j.vida)}/{round(j.vida_maxima)}", (114, 22), P.BRANCO, 11, ancora="midtop")
        especial = j.especial
        pronto = especial.pronto
        cor = P.OURO if not pronto or int(self.tempo * 6) % 2 else (255, 250, 200)
        barra(ui, (58, 36, 112, 6), 1.0 if pronto else especial.progresso, cor, P.OURO2, segmentos=5)
        rotulo = "ESPECIAL PRONTO! (ESPAÇO)" if pronto else "ESPECIAL"
        if especial.cargas_maximas > 1:               # Pendrive: cargas guardadas
            rotulo += f"  x{especial.cargas}"
        texto(ui, rotulo, (58, 44), P.OURO if pronto else P.CINZA, 11)
        # rolamento: tracinho embaixo do retrato
        rolamento = j.rolamento
        barra(ui, (6, 64 - 2, 46, 4), rolamento.progresso, P.VERDE if rolamento.pronto else P.CINZA)

    def _vaga(self, ui, x, y, coisa, tam=22):
        no_maximo = coisa is not None and coisa.no_maximo
        moldura(ui, (x, y, tam, tam), fundo=(22, 26, 52), borda=P.OURO if no_maximo else (190, 205, 240), raio=2,
                brilho=False, alfa=255 if coisa is not None else 150)
        if coisa is None:
            return
        img = icone(coisa.ICONE, tam - 6)
        ui.blit(img, img.get_rect(center=(x + tam // 2, y + tam // 2)))
        cafe = getattr(coisa, "fracao_cafe", None)
        if cafe is not None and cafe < 1:              # recarga do café: véu que desce
            h = int((tam - 2) * (1 - cafe))
            veu = pygame.Surface((tam - 2, h), pygame.SRCALPHA)
            veu.fill((0, 0, 0, 120))
            ui.blit(veu, (x + 1, y + 1))
        texto(ui, "MAX" if no_maximo else str(coisa.nivel), (x + tam + 2, y + tam + 3),
              P.OURO if no_maximo else P.BRANCO, 11, ancora="bottomright")

    def _vagas(self, ui, jogo):
        j = jogo.jogador
        for i in range(j.MAX_ARMAS):
            self._vaga(ui, 6 + i * 25, 70, j.armas[i] if i < len(j.armas) else None)
        for i in range(j.MAX_ITENS):
            self._vaga(ui, 6 + i * 25, 95, j.itens[i] if i < len(j.itens) else None)

    def _tempo_e_placar(self, ui, jogo):
        placar = jogo.placar
        pilula = pygame.Rect(0, 0, 74, 24)
        pilula.midtop = (L // 2, 9)
        moldura(ui, pilula, fundo=(22, 26, 52), raio=8, brilho=False)
        texto(ui, placar.tempo_formatado, pilula.center, P.BRANCO, 23, contorno=None, ancora="center")
        texto(ui, jogo.fase.NOME.upper(), (L // 2, 35), (210, 220, 255), 11, ancora="midtop")
        moeda = icone("icones/moeda.png", 12)
        larg = max(1, int(12 * abs(math.cos(self.tempo * 3))))      # moeda girando
        valor = str(placar.moedas)
        x = L - 6 - 14 - fonte(11).size(valor)[0]
        ui.blit(pygame.transform.scale(moeda, (larg, 12)), (x + (12 - larg) // 2, 10))
        texto(ui, valor, (L - 6, 10), P.OURO, 11, ancora="topright")
        texto(ui, f"{placar.pontos} pts  ·  {placar.eliminacoes} eliminações", (L - 6, 24), P.BRANCO, 11,
              ancora="topright")
        combo = placar.combo % COMBO_ESPECIAL
        texto(ui, f"COMBO {combo}/{COMBO_ESPECIAL}", (L - 6, 36),
              P.OURO if combo > COMBO_ESPECIAL * 3 // 4 else P.CINZA, 11, ancora="topright")

    def _chefe(self, ui, jogo):
        chefe = jogo.chefe
        if chefe is None or not chefe.ativo:
            return
        r = pygame.Rect(0, 0, 280, 9)
        r.midtop = (L // 2, 62)
        texto(ui, chefe.rotulo_da_barra, (L // 2, r.top - 13), P.BRANCO, 11, ancora="midtop")
        barra(ui, r, chefe.vida / chefe.vida_maxima, P.VERM, P.VERM2, segmentos=4)

    def _anuncios(self, ui, jogo):
        for i, (mensagem, restante) in enumerate(jogo.anuncios[-3:]):
            y = A // 3 + i * 28
            alfa = int(255 * min(1.0, restante / 0.4))
            if mensagem == "67!":                       # o combo especial aparece grande e pulando
                k = ease_back(janela(2.5 - restante, 0, 0.3))
                img = pygame.Surface((80, 30), pygame.SRCALPHA)
                texto(img, mensagem, (40, 15), P.OURO, 23, ancora="center")
                img = pygame.transform.scale_by(img, 1 + k)
                img.set_alpha(alfa)
                ui.blit(img, img.get_rect(center=(L // 2, y)))
            else:
                texto(ui, mensagem, (L // 2, y), P.OURO, 23, ancora="center", alfa=alfa)

