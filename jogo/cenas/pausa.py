"""Pausa como intervalo: um quadro negro com o menu em giz e as armas e itens em fotos num varal (opção G)."""
import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.widgets import TECLAS_CONFIRMAR, escurecer
from jogo.ui.materiais import giz, lousa, tachinha
from jogo.ui.pixel import (L, CamadaPixel, Paleta as P, ease_out, fonte, icone, janela, piscar,
                           quebrar, texto)


class CenaPausa(Cena):
    QUADRO = pygame.Rect(70, 22, 500, 220)
    Y_VARAL = 268

    def __init__(self, app, partida):
        super().__init__(app)
        self.partida = partida
        self.camada = CamadaPixel()
        self.tempo = 0.0
        self.no_menu = True
        self.indice = 0           # item do menu
        self.foto = 0             # foto destacada no varal
        self._tempo_foto = 0.0    # para o giz escrever a descrição aos poucos

    # ------------------------------------------------------------ menu
    @property
    def itens_menu(self):
        mira = "Mira: mouse" if self.app.modo_mira == "mouse" else "Mira: automática"
        return [("Voltar pra aula", self._continuar), (mira, self.app.alternar_mira), ("Ir embora", self._sair)]

    @property
    def fotos(self):
        jogador = self.partida.jogo.jogador
        return list(jogador.armas) + list(jogador.itens)

    def _continuar(self):
        self.app.desempilhar()

    def _sair(self):
        from jogo.cenas.titulo import CenaTitulo
        self.app.trocar(CenaTitulo(self.app))

    def _ir_para_fotos(self):
        if self.fotos:
            self.no_menu = False
            self.foto = min(self.foto, len(self.fotos) - 1)
            self._tempo_foto = self.tempo

    def _destacar_foto(self, i):
        if i != self.foto or self.no_menu:
            self._tempo_foto = self.tempo
        self.no_menu, self.foto = False, i

    # ------------------------------------------------------------ posições (camada 640x360)
    def _rect_menu(self, i):
        q = self.QUADRO
        return pygame.Rect(q.x + 22, q.y + 64 + i * 40, 200, 30)

    def _centro_foto(self, i):
        n = max(1, len(self.fotos))
        passo = min(100, 500 // n)
        x0 = L // 2 - (n - 1) * passo / 2
        return int(x0 + i * passo), self.Y_VARAL + 44 + i % 2

    def _rect_foto(self, i):
        r = pygame.Rect(0, 0, 66, 78)
        r.center = self._centro_foto(i)
        return r

    # ------------------------------------------------------------ entrada
    def tratar_evento(self, evento):
        if evento.type == pygame.KEYDOWN:
            self._tecla(evento.key)
        elif evento.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            pos = CamadaPixel.para_camada(evento.pos)
            for i in range(len(self.itens_menu)):
                if self._rect_menu(i).collidepoint(pos):
                    self.no_menu, self.indice = True, i
                    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                        self.itens_menu[i][1]()
                    return
            for i in range(len(self.fotos)):
                if self._rect_foto(i).collidepoint(pos):
                    self._destacar_foto(i)
                    return

    def _tecla(self, k):
        if k == pygame.K_ESCAPE:
            self._continuar()
        elif self.no_menu:
            if k in (pygame.K_UP, pygame.K_w):
                self.indice = (self.indice - 1) % len(self.itens_menu)
            elif k in (pygame.K_DOWN, pygame.K_s):
                if self.indice == len(self.itens_menu) - 1:
                    self._ir_para_fotos()
                else:
                    self.indice += 1
            elif k in TECLAS_CONFIRMAR:
                self.itens_menu[self.indice][1]()
        else:
            if k in (pygame.K_UP, pygame.K_w):
                self.no_menu = True
            elif k in (pygame.K_LEFT, pygame.K_a):
                self._destacar_foto((self.foto - 1) % len(self.fotos))
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self._destacar_foto((self.foto + 1) % len(self.fotos))

    def atualizar(self, dt):
        self.tempo += dt

    # ------------------------------------------------------------ desenho
    def _aluno_em_giz(self, altura):
        """O sprite do jogador desenhado em giz: contorno e algumas hachuras."""
        animacoes = self.partida.jogo.jogador.animador.animacoes
        animacao = animacoes.get("parado") or next(iter(animacoes.values()))
        quadro = animacao.quadros[int(self.tempo * 5) % len(animacao.quadros)]
        caixa = quadro.get_bounding_rect()
        if caixa.w and caixa.h:
            quadro = quadro.subsurface(caixa)
        img = pygame.transform.scale(quadro, (max(1, round(quadro.get_width() * altura / quadro.get_height())), altura))
        mascara = pygame.mask.from_surface(img)
        s = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        for x, y in mascara.outline(2):
            s.fill((*P.GIZ, 230), (x, y, 2, 2))
        for y in range(0, img.get_height(), 7):
            for x in range(0, img.get_width(), 3):
                if mascara.get_at((x, y)) and (x + y) % 9 == 0:
                    s.fill((*P.GIZ, 110), (x, y, 2, 1))
        return s

    def _polaroide(self, coisa):
        larg, alt = 66, 78
        s = pygame.Surface((larg, alt), pygame.SRCALPHA)
        s.fill((250, 248, 240))
        pygame.draw.rect(s, (60, 70, 90), (6, 6, larg - 12, alt - 34))
        img = icone(coisa.ICONE, 40)
        s.blit(img, img.get_rect(center=(larg // 2, 6 + (alt - 34) // 2)))
        nome = coisa.NOME if fonte(11).size(coisa.NOME)[0] <= larg - 6 else coisa.NOME.split()[0]
        texto(s, nome, (larg // 2, alt - 25), (50, 50, 70), 11, contorno=None, ancora="midtop")
        texto(s, "MAX" if coisa.no_maximo else f"nv {coisa.nivel}", (larg - 6, alt - 13), P.MARGEM, 11,
              contorno=None, ancora="topright")
        pygame.draw.rect(s, (200, 196, 186), s.get_rect(), 1)
        return s

    def _quadro(self, ui):
        jogo = self.partida.jogo
        k = ease_out(janela(self.tempo, 0.0, 0.35))
        q = self.QUADRO.move(0, -int(260 * (1 - k)))
        lousa(ui, q, semente=9)
        giz(ui, "INTERVALO", (q.x + 22, q.y + 16), 23, P.GIZ, semente=2, progresso=janela(self.tempo, 0.2, 0.4))
        pygame.draw.line(ui, (90, 120, 104), (q.x + 22, q.y + 46), (q.x + 200, q.y + 47), 1)
        for i, (nome, _) in enumerate(self.itens_menu):
            ke = janela(self.tempo, 0.4 + i * 0.12, 0.25)
            if ke <= 0:
                continue
            r = self._rect_menu(i).move(0, q.y - self.QUADRO.y)
            sel = self.no_menu and i == self.indice
            cor = P.GIZ_AMARELO if sel else P.GIZ
            escrito = giz(ui, nome, (r.x + 16, r.y), 23, cor, semente=11 + i, progresso=ke)
            if sel and ke >= 1:
                pygame.draw.line(ui, cor, (escrito.x, escrito.bottom + 2), (escrito.right, escrito.bottom + 3), 2)
                giz(ui, ">", (r.x, r.y), 23, cor, semente=3)
        pygame.draw.line(ui, (70, 98, 84), (q.centerx + 30, q.y + 18), (q.centerx + 30, q.bottom - 18), 1)
        lado = pygame.Rect(q.centerx + 44, q.y + 14, q.right - q.centerx - 58, q.h - 28)
        if self.no_menu or not self.fotos:
            aluno = self._aluno_em_giz(78)
            ui.blit(aluno, aluno.get_rect(midtop=(lado.centerx, lado.y + 2)))
            giz(ui, f"{jogo.jogador.NOME}  ·  nível {jogo.jogador.nivel}  ·  {jogo.placar.tempo_formatado}",
                (lado.centerx, lado.y + 84), 11, P.GIZ, ancora="midtop", semente=5)
            self._calendario(ui, jogo, lado)
        else:
            coisa = self.fotos[self.foto]
            p = janela(self.tempo - self._tempo_foto, 0, 0.3)
            img = icone(coisa.ICONE, 56)
            ui.blit(img, img.get_rect(midtop=(lado.centerx, lado.y + 4)))
            giz(ui, coisa.NOME, (lado.centerx, lado.y + 70), 11, P.GIZ_AMARELO, ancora="midtop", semente=8, progresso=p)
            nivel = "MÁXIMO" if coisa.no_maximo else f"nível {coisa.nivel} de {coisa.NIVEL_MAXIMO}"
            giz(ui, nivel, (lado.centerx, lado.y + 86), 11, (190, 214, 200), ancora="midtop", semente=9, progresso=p)
            for j, linha in enumerate(quebrar(coisa.DESCRICAO, fonte(11, True), lado.w)[:5]):
                giz(ui, linha, (lado.centerx, lado.y + 112 + j * 14), 11, P.GIZ, ancora="midtop", semente=20 + j,
                    progresso=p)
        giz(ui, "Cima/baixo: menu e fotos    Esc: voltar", (q.x + 22, q.bottom - 22), 11, (150, 180, 164), semente=4)

    def _calendario(self, ui, jogo, lado):
        """O calendário de provas: a hora de cada chefe e como está cada prova."""
        giz(ui, "Calendário de provas", (lado.centerx, lado.y + 106), 11, P.GIZ_AMARELO, ancora="midtop", semente=6)
        for i, prova in enumerate(jogo.fase.provas):
            minutos, segundos = divmod(int(prova.hora), 60)
            if prova in jogo.notas:
                situacao = "aprovado"
            elif jogo.chefe_da_prova(prova) is not None:
                situacao = "em campo"
            else:
                situacao = "por vir"
            linha = f"{minutos:02d}:{segundos:02d}  {prova.curto}: {situacao}"
            giz(ui, linha, (lado.x, lado.y + 124 + i * 16), 11, (190, 214, 200), semente=30 + i)

    def _varal(self, ui):
        kv = ease_out(janela(self.tempo, 0.3, 0.4))
        desce = int(120 * (1 - kv))
        pygame.draw.line(ui, (200, 190, 170), (60, self.Y_VARAL + desce), (580, self.Y_VARAL + 6 + desce), 1)
        for i, coisa in enumerate(self.fotos):
            sel = not self.no_menu and i == self.foto
            cx, cy = self._centro_foto(i)
            img = self._polaroide(coisa)
            img = pygame.transform.rotozoom(img, 0 if sel else (i * 7) % 9 - 4, 1.1 if sel else 1.0)
            r = img.get_rect(center=(cx, cy + desce - (6 if sel else 0)))
            sombra = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            sombra.fill((0, 0, 0, 70))
            ui.blit(sombra, r.move(3, 4))
            ui.blit(img, r)
            tachinha(ui, (r.centerx, r.y + 4))
            if sel:
                pygame.draw.rect(ui, (*P.OURO, int(255 * piscar(self.tempo))), r.inflate(6, 6), 2)

    def desenhar(self, tela):
        escurecer(tela, int(190 * ease_out(janela(self.tempo, 0, 0.25))))
        ui = self.camada.limpar()
        self._quadro(ui)
        self._varal(ui)
        self.camada.apresentar(tela)
