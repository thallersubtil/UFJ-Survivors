"""Matrícula: o jogador escolhe a classe na secretaria, tira a foto e a carteirinha sai da impressora.

Cada classe tem a aparência fixa: o retrato grande (a arte principal) aparece na webcam e o
chibi, que é quem anda na partida, aparece no canto. Enter tira a foto, a impressora solta a
carteirinha e a partida começa.
"""
import math

import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_ENTER
from jogo.jogador.classes import CLASSES
from jogo.nucleo.recursos import Recursos
from jogo.opcoes import OpcoesDePartida
from jogo.ui.materiais import madeira, papel
from jogo.ui.pixel import (A, ESCALA, L, CamadaPixel, Paleta as P, barra, ease_out, fonte, icone, janela, moldura,
                           no_quadrado, quebrar, texto)

FOTO_AZUL = (200, 214, 236)


class CenaMatricula(Cena):
    DURACAO_TROCA = 0.35               # o retrato novo se abre em círculo sobre o anterior
    DURACAO_FOTO = 1.1                 # flash + carteirinha saindo da impressora
    AVISO = pygame.Rect(478, 104, 150, 76)    # quadro "na partida", na camada
    MARGEM_DA_FOTO = 6                 # folga dos lados do retrato na webcam
    MARGEM_DO_TOPO = 22                # folga acima da cabeça (também livra o aviso "AO VIVO")
    VIDA_MAXIMA_BARRA, VELOCIDADE_MAXIMA_BARRA = 130, 240

    MONITOR = pygame.Rect(12, 10, 456, 250)

    def __init__(self, app, opcoes=None):
        super().__init__(app)
        self.opcoes = opcoes or OpcoesDePartida()
        self.indice = getattr(app, "classe_escolhida", 0) % len(CLASSES)
        self.tempo = 0.0
        self.camada = CamadaPixel()
        self.exemplos = [classe((0, 0)) for classe in CLASSES]
        self._retratos = {}
        self._anterior = self.indice
        self._t_troca = -10.0
        self.foto_tirada_em = None
        self._chibis_grandes = {}          # pasta -> quadros do andar no tamanho do quadro "na partida"
        self._topo_da_carteirinha = None   # até onde a carteirinha já subiu (ela passa na frente do boneco)
        self._foto_impressa = None         # onde a foto da carteirinha está na camada (quando já saiu)
        self._limite_da_impressora = 0

    # ------------------------------------------------------------ regras
    @property
    def classe(self):
        return CLASSES[self.indice]

    def escolher(self, i):
        i %= len(CLASSES)
        if i != self.indice and self.foto_tirada_em is None:
            self._anterior, self.indice, self._t_troca = self.indice, i, self.tempo

    def tirar_foto(self):
        if self.foto_tirada_em is None:
            self.foto_tirada_em = self.tempo
            Recursos.tocar("nivel", 0.3)

    def _comecar(self):
        from jogo.cenas.partida import CenaPartida
        self.app.classe_escolhida = self.indice
        self.app.trocar(CenaPartida(self.app, self.classe, self.opcoes))

    def _voltar(self):
        if self.opcoes.treino:
            from jogo.cenas.treino import CenaTreino
            self.app.trocar(CenaTreino(self.app))
        else:
            from jogo.cenas.titulo import CenaTitulo
            self.app.trocar(CenaTitulo(self.app))

    # ------------------------------------------------------------ posições na camada
    @property
    def _tela_monitor(self):
        return self.MONITOR.inflate(-24, -24)

    @property
    def _webcam(self):
        t = self._tela_monitor
        return pygame.Rect(t.x + 6, t.y + 22, 150, 198)

    @property
    def _ficha(self):
        t, cam = self._tela_monitor, self._webcam
        return pygame.Rect(cam.right + 10, cam.y, t.right - cam.right - 16, cam.h)

    @property
    def botao_foto(self):
        f = self._ficha
        return pygame.Rect(f.x, f.bottom - 20, f.w, 20)

    def aba(self, i):
        r = pygame.Rect(0, 0, 84, 20)
        r.center = (L // 2 + (i - (len(CLASSES) - 1) / 2) * 88, A - 46)
        return r

    # ------------------------------------------------------------ entrada
    def tratar_evento(self, evento):
        if self.foto_tirada_em is not None:
            return
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                self.escolher(self.indice - 1)
            elif evento.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                self.escolher(self.indice + 1)
            elif evento.key in TECLAS_ENTER:
                self.tirar_foto()
            elif evento.key == pygame.K_ESCAPE:
                self._voltar()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pos = CamadaPixel.para_camada(evento.pos)
            for i in range(len(CLASSES)):
                if self.aba(i).collidepoint(pos):
                    self.escolher(i)
                    return
            if self.botao_foto.collidepoint(pos):
                self.tirar_foto()

    def atualizar(self, dt):
        self.tempo += dt
        if self.foto_tirada_em is not None and self.tempo - self.foto_tirada_em >= self.DURACAO_FOTO:
            self._comecar()

    # ------------------------------------------------------------ desenho
    def _chibi(self, i, animacao="andar", altura=None):
        """Quadro da vez do chibi da classe (o personagem como aparece na partida)."""
        animacoes = self.exemplos[i].animador.animacoes
        tira = animacoes.get(animacao) or next(iter(animacoes.values()))
        quadro = tira.quadros[int(self.tempo * tira.fps) % len(tira.quadros)]
        return no_quadrado(quadro, altura) if altura else quadro

    def _retrato(self, i, tamanho):
        """A arte principal da classe enquadrada como foto: a largura inteira do desenho e, de altura, o que
        couber na proporção pedida a partir da cabeça. Assim ninguém sai do quadro, seja largo ou estreito.
        Sem a arte, o chibi ampliado."""
        largura, altura = tamanho
        chave = (i, largura, altura)
        if chave not in self._retratos:
            caminho = CLASSES[i].RETRATO
            if caminho and (Recursos.pasta / caminho).is_file():
                arte = Recursos.imagem(caminho)
                corte_altura = min(arte.get_height(), round(arte.get_width() * altura / largura))
                corte = arte.subsurface((0, 0, arte.get_width(), corte_altura))
                escala = min(largura / corte.get_width(), altura / corte.get_height())
                novo = (max(1, round(corte.get_width() * escala)), max(1, round(corte.get_height() * escala)))
                # ampliando, não suaviza (os pixels do desenho ficam nítidos); reduzindo, suaviza para não serrilhar
                ampliar = pygame.transform.scale if escala >= 1 else pygame.transform.smoothscale
                self._retratos[chave] = ampliar(corte, novo)
            else:
                self._retratos[chave] = None
        return self._retratos[chave] or self._chibi(i, "parado", min(altura, largura))

    def _na_webcam(self, tamanho):
        """A foto ao vivo; logo depois de trocar de classe, a nova se abre em círculo sobre a anterior."""
        def foto(i):
            s = pygame.Surface(tamanho)
            s.fill(FOTO_AZUL)
            fator = tamanho[0] / self._webcam.w              # 1 na camada, ESCALA quando desenha direto na tela
            img = self._retrato(i, (round(tamanho[0] - self.MARGEM_DA_FOTO * 2 * fator),
                                    round(tamanho[1] - self.MARGEM_DO_TOPO * fator)))
            s.blit(img, img.get_rect(midbottom=(tamanho[0] // 2, tamanho[1])))
            return s
        nova = foto(self.indice)
        dt = self.tempo - self._t_troca
        if dt >= self.DURACAO_TROCA:
            return nova
        raio = int(math.hypot(*tamanho) * ease_out(dt / self.DURACAO_TROCA))
        centro = (tamanho[0] // 2, tamanho[1] // 2)
        mascara = pygame.Surface(tamanho, pygame.SRCALPHA)
        pygame.draw.circle(mascara, (255, 255, 255, 255), centro, raio)
        parte = nova.convert_alpha()
        parte.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        img = foto(self._anterior)
        img.blit(parte, (0, 0))
        pygame.draw.circle(img, P.BRANCO, centro, raio, 3)
        return img

    def _sala(self, ui):
        pygame.draw.rect(ui, (176, 196, 170), (0, 0, L, 270))
        for y in range(0, 270, 30):
            pygame.draw.line(ui, (160, 182, 156), (0, y), (L, y))
        pygame.draw.rect(ui, (120, 140, 116), (0, 200, L, 6))
        madeira(ui, pygame.Rect(0, 266, L, 94), (128, 86, 52), tabuas=10, semente=4)
        pygame.draw.line(ui, P.ESC, (0, 266), (L, 266), 2)
        papel(ui, pygame.Rect(478, 12, 150, 22), P.PAPEL, semente=2)
        texto(ui, "SECRETARIA ACADÊMICA", (553, 17), (40, 60, 40), 11, contorno=None, ancora="midtop")
        painel = pygame.Rect(478, 40, 150, 44)
        pygame.draw.rect(ui, (20, 16, 20), painel, border_radius=4)
        pygame.draw.rect(ui, P.ESC, painel, 2, border_radius=4)
        texto(ui, "SENHA", (painel.x + 8, painel.y + 6), (200, 200, 200), 11, contorno=None)
        chamando = 0.4 <= self.tempo < 1.2 and int(self.tempo * 6) % 2 == 0
        texto(ui, "041" if self.tempo < 0.4 else "042", (painel.x + 70, painel.y + 9),
              (120, 30, 30) if chamando else (255, 70, 60), 23, contorno=None)
        if 0.4 <= self.tempo < 1.0:
            texto(ui, "DING!", (painel.right - 2, painel.bottom + 4), P.OURO, 11, ancora="topright")
        aviso = self.AVISO                                              # o chibi: quem anda na partida
        papel(ui, aviso, P.PAPEL2, semente=8)
        texto(ui, "NA PARTIDA", (aviso.centerx, aviso.y + 4), (60, 60, 90), 11, contorno=None, ancora="midtop")

    def _chibi_grande(self, i):
        """O quadro da vez do andar na arte feita no tamanho deste quadro (assets/retratos/chibis): ampliar o boneco
        da partida deixaria o traço fora de foco. Sem essa arte, amplia mesmo."""
        pasta = CLASSES[i].PASTA_SPRITE
        if pasta not in self._chibis_grandes:
            caminho = f"retratos/chibis/{pasta}/andar-8.png"
            quadros = None
            if (Recursos.pasta / caminho).is_file():
                tira = Recursos.imagem(caminho)
                largura = tira.get_width() // 8
                quadros = [tira.subsurface((k * largura, 0, largura, tira.get_height())) for k in range(8)]
            self._chibis_grandes[pasta] = quadros
        quadros = self._chibis_grandes[pasta]
        animacoes = self.exemplos[i].animador.animacoes
        tira = animacoes.get("andar") or next(iter(animacoes.values()))
        if quadros is None or len(tira.quadros) != len(quadros):
            quadro = self._chibi(i)
            altura = 54 * ESCALA
            return pygame.transform.smoothscale(quadro, (round(quadro.get_width() * altura / quadro.get_height()), altura))
        return quadros[int(self.tempo * tira.fps) % len(quadros)]

    def _chibi_nitido(self, tela):
        """O boneco da partida vai direto na tela, suavizado: pela camada (ampliada em blocos) sairia serrilhado."""
        chibi = self._chibi_grande(self.indice)
        if self._topo_da_carteirinha is not None:               # a carteirinha impressa passa na frente dele
            tela.set_clip(pygame.Rect(0, 0, tela.get_width(), self._topo_da_carteirinha * ESCALA))
        tela.blit(chibi, chibi.get_rect(midbottom=(self.AVISO.centerx * ESCALA, (self.AVISO.bottom - 4) * ESCALA)))
        tela.set_clip(None)

    def _dados(self, ui, r, heroi):
        """Ficha da classe no monitor: nome, descrição, barras e os três blocos (arma, habilidades, especial)."""
        fraco = (176, 190, 226)
        texto(ui, heroi.NOME.upper(), (r.x, r.y - 2), P.OURO, 23)
        texto(ui, heroi.DESCRICAO, (r.x, r.y + 22), fraco, 11, contorno=None, media=True)
        for i, (nome, valor, maximo, cor) in enumerate((("Vida", heroi.VIDA, self.VIDA_MAXIMA_BARRA, P.VERM),
                                                        ("Velocidade", heroi.VELOCIDADE, self.VELOCIDADE_MAXIMA_BARRA,
                                                         P.AZUL))):
            y = r.y + 38 + i * 13
            texto(ui, nome, (r.x, y), fraco, 11, contorno=None, media=True)
            barra(ui, (r.x + 66, y + 2, r.w - 100, 8), valor / maximo, cor)
            texto(ui, str(round(valor)), (r.right, y), P.BRANCO, 11, contorno=None, ancora="topright")
        arma, especial = heroi.armas[0], heroi.especial
        habilidades = heroi.habilidades_da_classe
        blocos = (("ARMA", arma.NOME, arma.DESCRICAO, arma.ICONE),
                  ("HABILIDADES", "", ", ".join(h.NOME for h in habilidades) + " (nas cartas de nível)",
                   habilidades[0].ICONE),
                  ("ESPECIAL", especial.NOME, especial.DESCRICAO, especial.ICONE))
        for i, (tipo, nome, descricao, ic) in enumerate(blocos):
            y = r.y + 68 + i * 36
            caixa = pygame.Rect(r.x, y, 32, 32)
            moldura(ui, caixa, fundo=(22, 26, 52), borda=(150, 160, 220), raio=2, brilho=False)
            if ic:
                img = icone(ic, 26)
                ui.blit(img, img.get_rect(center=caixa.center))
            else:
                texto(ui, "P", caixa.center, P.OURO, 23, contorno=None, ancora="center")
            texto(ui, tipo, (r.x + 38, y - 2), fraco, 11, contorno=None)
            texto(ui, nome, (r.x + 38 + fonte(11).size(tipo)[0] + 6, y - 2), P.BRANCO, 11, contorno=None)
            for j, linha in enumerate(quebrar(descricao, fonte(11, True), r.w - 40)[:2]):
                texto(ui, linha, (r.x + 38, y + 10 + j * 11), fraco, 11, contorno=None, media=True)

    def _monitor(self, ui):
        mon = self.MONITOR
        pygame.draw.rect(ui, (214, 208, 190), mon, border_radius=8)
        pygame.draw.rect(ui, P.ESC, mon, 2, border_radius=8)
        tela_m = self._tela_monitor
        pygame.draw.rect(ui, (30, 50, 110), tela_m)
        pygame.draw.rect(ui, (60, 90, 170), (tela_m.x, tela_m.y, tela_m.w, 16))
        modo = "modo treino" if self.opcoes.treino else "matrícula 2026/2"
        texto(ui, f"SIGAA  ·  {modo}  ·  foto da carteirinha", (tela_m.x + 6, tela_m.y + 2), P.BRANCO, 11,
              contorno=None, media=True)
        cam = self._webcam
        pygame.draw.rect(ui, FOTO_AZUL, cam)            # a foto entra depois, em resolução de tela (_foto_nitida)
        self._dados(ui, self._ficha, self.exemplos[self.indice])
        b = self.botao_foto
        apertado = self.foto_tirada_em is not None
        pygame.draw.rect(ui, (30, 90, 45) if apertado else (40, 120, 60), b, border_radius=3)
        pygame.draw.rect(ui, P.OURO, b, 1, border_radius=3)
        texto(ui, "TIRAR FOTO E MATRICULAR  (Enter)", b.center, P.BRANCO, 11, contorno=None, ancora="center")

    def _abas(self, ui):
        for i, heroi in enumerate(self.exemplos):
            r = self.aba(i)
            sel = i == self.indice
            if sel:
                r.y -= 4
            pygame.draw.rect(ui, P.VERDE_UFJ if sel else (30, 40, 34), r, border_radius=3)
            pygame.draw.rect(ui, P.OURO if sel else (90, 110, 96), r, 1, border_radius=3)
            nome = heroi.NOME if fonte(11).size(heroi.NOME)[0] <= r.w - 6 else heroi.NOME.split()[0]
            texto(ui, nome, r.center, P.OURO if sel else P.PAPEL, 11, contorno=None, ancora="center")

    def _impressora(self, ui):
        self._foto_impressa = None
        self._topo_da_carteirinha = None
        imp = pygame.Rect(478, 208, 150, 50)
        foto_t = None if self.foto_tirada_em is None else self.tempo - self.foto_tirada_em
        if foto_t is not None and foto_t >= 0.1:
            heroi = self.exemplos[self.indice]
            k = ease_out(janela(foto_t, 0.1, 0.5))
            c = pygame.Rect(0, 0, 140, 88)
            c.midbottom = (imp.centerx, imp.y + 98 - int(108 * k))
            papel(ui, c, P.PAPEL, semente=5)
            pygame.draw.rect(ui, P.VERDE_UFJ, (c.x, c.y, c.w, 12))
            texto(ui, "UFJ · ESTUDANTE", (c.x + 4, c.y + 1), P.PAPEL, 11, contorno=None, media=True)
            foto = pygame.Surface((44, 58))
            foto.fill(FOTO_AZUL)
            self._foto_impressa = pygame.Rect(c.x + 6, c.y + 18, 44, 58)
            self._topo_da_carteirinha = c.y
            self._limite_da_impressora = imp.y
            if self.classe.foto(44 * ESCALA) is None:            # sem a arte da foto: o retrato reduzido
                mini = self._retrato(self.indice, (40, 54))
                foto.blit(mini, mini.get_rect(midbottom=(22, 58)))
            ui.blit(foto, self._foto_impressa)
            pygame.draw.rect(ui, (60, 60, 80), (c.x + 6, c.y + 18, 44, 58), 1)
            nome = heroi.NOME if fonte(11).size(heroi.NOME)[0] <= 80 else heroi.NOME.split()[0]
            texto(ui, nome, (c.x + 56, c.y + 18), P.MARGEM, 11, contorno=None)
            semente = sum(map(ord, heroi.NOME))
            texto(ui, f"matr. {semente * 37 % 9000 + 1000}", (c.x + 56, c.y + 32), (90, 90, 110), 11,
                  contorno=None, media=True)
            for j in range(24):                                       # código de barras
                pygame.draw.rect(ui, P.ESC, (c.x + 56 + j * 3, c.y + 50, 1 if (semente >> (j % 9)) & 1 else 2, 22))
        pygame.draw.rect(ui, (70, 72, 84), imp, border_radius=4)
        pygame.draw.rect(ui, P.ESC, imp, 2, border_radius=4)
        pygame.draw.rect(ui, (20, 20, 26), (imp.x + 20, imp.y + 10, imp.w - 40, 5))
        pygame.draw.circle(ui, P.VERDE if foto_t is not None else (40, 70, 40), (imp.right - 12, imp.bottom - 12), 3)

    def desenhar(self, tela):
        tela.fill(P.ESC)
        ui = self.camada.limpar()
        self._sala(ui)
        self._monitor(ui)
        self._abas(ui)
        self._impressora(ui)
        texto(ui, "Setas: escolher a classe    Enter: foto e matrícula    Esc: voltar", (L // 2, A - 18), P.BRANCO, 11,
              ancora="midtop")
        self.camada.apresentar(tela)
        self._foto_nitida(tela)

    def _foto_nitida(self, tela):
        """Desenha o retrato direto na tela, em resolução cheia.

        A camada da interface tem metade da resolução e é ampliada; passando por ela o retrato
        perderia metade dos pixels e sairia borrado. Aqui ele entra quase no tamanho original
        da arte, sem suavizar, então os pixels do desenho ficam nítidos.
        """
        cam = self._webcam
        area = pygame.Rect(cam.x * ESCALA, cam.y * ESCALA, cam.w * ESCALA, cam.h * ESCALA)
        tela.blit(self._na_webcam(area.size), area)
        pygame.draw.rect(tela, P.BRANCO, area, ESCALA)
        pygame.draw.circle(tela, P.VERM if int(self.tempo * 2) % 2 else (100, 20, 20),
                           (area.x + 10 * ESCALA, area.y + 10 * ESCALA), 3 * ESCALA)
        texto(tela, "AO VIVO", (area.x + 16 * ESCALA, area.y + 4 * ESCALA), P.BRANCO, 23, media=True)
        self._chibi_nitido(tela)
        rosto = self.classe.foto(44 * ESCALA)
        if self._foto_impressa is not None and rosto is not None:      # o rosto na carteirinha, também nítido
            f = self._foto_impressa
            tela.set_clip(pygame.Rect(0, 0, tela.get_width(), self._limite_da_impressora * ESCALA))   # some atrás da impressora
            tela.blit(rosto, rosto.get_rect(midbottom=((f.centerx) * ESCALA, f.bottom * ESCALA)))
            tela.set_clip(None)
        foto_t = None if self.foto_tirada_em is None else self.tempo - self.foto_tirada_em
        if foto_t is not None and foto_t < 0.25:
            flash = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(240 * (1 - foto_t / 0.25))))
            tela.blit(flash, (0, 0))
