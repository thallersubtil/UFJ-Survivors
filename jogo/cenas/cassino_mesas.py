"""As mesas do cassino: o desenho animado de cada jogo de aposta.

Cada mesa herda de Mesa e desenha o próprio aparelho (a máquina, o dado, a roleta) em `desenhar_aparelho`.
A CenaCassino só pede `mesa.desenhar_aparelho(...)`, sem perguntar qual é o jogo. Um jogo novo que não tenha
mesa própria cai na MesaGenerica, que mostra os símbolos sorteados em caixas.
"""
import math
import random
from abc import ABC, abstractmethod

import pygame

from jogo.loja.cassino import DadoDoMestre, MaquinaDeSalgadinho, RoletaDoBandejao
from jogo.ui.pixel import Paleta as P, clarear, ease_back, ease_out, escurecer_cor, fonte, icone, janela, moldura, texto


class Mesa(ABC):
    """O aparelho de um jogo em cima da mesa. As coordenadas são da camada de 640x360."""

    PASTA_CRUPIE = "monitor"
    TITULO = None                # nome curto para a aba (None: o nome do jogo)
    CENTRO = (320, 140)

    def __init__(self, jogo):
        self.jogo = jogo

    @abstractmethod
    def desenhar_aparelho(self, ui, cena, dx=0):
        cx, cy = self.CENTRO[0] + dx, self.CENTRO[1]
        corpo = pygame.Rect(cx - 112, cy - 64, 224, 144)
        pygame.draw.rect(ui, P.ESC, (corpo.x + 12, corpo.bottom - 2, corpo.w - 24, 8))        # pé
        moldura(ui, corpo, fundo=P.VERM2, borda=P.OURO, raio=6)
        placa = pygame.Rect(cx - 70, corpo.y - 13, 140, 22)
        moldura(ui, placa, fundo=P.NAVY, borda=P.OURO, raio=5)
        texto(ui, "SALGADINHO", placa.center, P.OURO, 11, ancora="center")
        f = cena.fracao_do_giro
        # alavanca: desce no começo do giro e volta
        puxada = math.sin(math.pi * janela(f, 0, 0.3)) if f is not None else 0.0
        topo = corpo.y + 30 + int(64 * puxada)
        pygame.draw.rect(ui, P.ESC, (corpo.right - 2, corpo.centery + 14, 18, 14))
        pygame.draw.rect(ui, P.CINZA, (corpo.right, corpo.centery + 16, 14, 10))
        pygame.draw.line(ui, P.ESC, (corpo.right + 10, corpo.centery + 19), (corpo.right + 10, topo), 6)
        pygame.draw.line(ui, P.CINZA, (corpo.right + 10, corpo.centery + 19), (corpo.right + 10, topo), 4)
        pygame.draw.circle(ui, P.ESC, (corpo.right + 10, topo), 10)
        pygame.draw.circle(ui, P.VERM, (corpo.right + 10, topo), 8)
        pygame.draw.circle(ui, clarear(P.VERM, 80), (corpo.right + 7, topo - 3), 2)
        # rolos
        iguais = self._rolos_premiados(cena)
        for i in range(self.jogo.ROLOS):
            rolo = pygame.Rect(cx - 96 + i * 66, corpo.y + 24, 60, 74)
            self._rolo(ui, rolo, i, cena)
            if i in iguais and int(cena.tempo * 6) % 2 == 0:
                pygame.draw.rect(ui, P.OURO, rolo.inflate(4, 4), 2)
        pygame.draw.line(ui, P.VERM, (cx - 103, corpo.y + 61), (cx - 99, corpo.y + 61), 1)
        pygame.draw.line(ui, P.VERM, (cx + 98, corpo.y + 61), (cx + 102, corpo.y + 61), 1)
        # bandeja de onde caem as moedas
        bandeja = pygame.Rect(cx - 64, corpo.bottom - 38, 128, 22)
        pygame.draw.rect(ui, P.ESC, bandeja, border_radius=3)
        pygame.draw.rect(ui, (60, 20, 34), bandeja.inflate(-4, -4), border_radius=2)
        for k in range(5):                                             # luzinhas do painel
            acesa = (k + int(cena.tempo * (10 if f is not None else 3))) % 2 == 0
            pygame.draw.circle(ui, P.OURO if acesa else P.OURO2, (cx - 48 + k * 24, corpo.bottom - 9), 2)

    @property
    def titulo(self):
        return self.TITULO or self.jogo.NOME.upper()

    def origem_do_premio(self):
        """De onde as moedas do prêmio saem voando."""
        return self.CENTRO

    def rotulo_da_escolha(self, escolha):
        return str(escolha).upper()

    def desenhar_rotulo(self, ui, linha, pos, cor):
        """Nome de uma linha da tabela de prêmios."""
        texto(ui, linha.rotulo, pos, cor, 11, contorno=None, media=True)

    @staticmethod
    def parado_com_resultado(cena):
        return cena.fracao_do_giro is None and cena.resultado is not None


class MesaGenerica(Mesa):
    """Para um jogo sem mesa própria: os símbolos do resultado em caixas."""

    def desenhar_aparelho(self, ui, cena, dx=0):
        if cena.resultado is not None and cena.fracao_do_giro is None:
            simbolos = cena.resultado.simbolos
        else:
            simbolos = ("?",)
        cx, cy = self.CENTRO
        for i, simbolo in enumerate(simbolos):
            caixa = pygame.Rect(0, 0, 84, 84)
            caixa.center = (cx + dx + (i - (len(simbolos) - 1) / 2) * 96, cy)
            moldura(ui, caixa, fundo=P.PAPEL, borda=P.OURO)
            texto(ui, str(simbolo), caixa.center, P.VERM2, 11, contorno=None, ancora="center")


class MesaDaMaquina(Mesa):
    """Caça-níquel: três rolos que correm e param um de cada vez, com alavanca."""

    PASTA_CRUPIE = "gamer"
    TITULO = "SALGADINHO"
    ICONES = {
        "Pequi": "icones/pequi.png",
        "Café": "sprites/cafe.png",
        "Pão de Queijo": "icones/pao_de_queijo.png",
        "Nota 10": "sprites/nota.png",
        "Caramelo": "sprites/caramelo.png",
    }
    PARADAS = (0.55, 0.75, 0.95)       # fração do giro em que cada rolo para
    CELULA = 48

    def _simbolo(self, ui, nome, centro, tam=38):
        if nome in self.ICONES:
            img = icone(self.ICONES[nome], tam)
            ui.blit(img, img.get_rect(center=centro))
        else:
            texto(ui, nome, centro, P.VERM, 23 if tam > 16 else 11, ancora="center",
                  contorno=P.ESC if tam > 16 else None)

    def posicao_do_rolo(self, i, cena):
        """Posição (em células) do rolo `i` na fita de símbolos; o número inteiro é o símbolo no meio."""
        simbolos = self.jogo.SIMBOLOS
        if cena.resultado is None:
            return float(i)
        alvo = simbolos.index(cena.resultado.simbolos[i])
        if cena.fracao_do_giro is None:
            return float(alvo)
        voltas = 14 + 5 * i
        return alvo - voltas * (1 - ease_back(cena.fracao_do_giro / self.PARADAS[i], 1.2))

    def _rolo(self, ui, janela_rolo, i, cena):
        simbolos = self.jogo.SIMBOLOS
        pos = self.posicao_do_rolo(i, cena)
        base = math.floor(pos)
        resto = pos - base
        pygame.draw.rect(ui, P.ESC, janela_rolo.inflate(4, 4))
        pygame.draw.rect(ui, P.PAPEL, janela_rolo)
        recorte = ui.get_clip()
        ui.set_clip(janela_rolo)
        for d in (-2, -1, 0, 1, 2):
            nome = simbolos[(base + d) % len(simbolos)]
            self._simbolo(ui, nome, (janela_rolo.centerx, janela_rolo.centery - (d - resto) * self.CELULA))
        ui.set_clip(recorte)
        sombra = pygame.Surface((janela_rolo.w, 8), pygame.SRCALPHA)
        for y in range(8):
            pygame.draw.line(sombra, (20, 10, 30, 150 - y * 18), (0, y), (janela_rolo.w, y))
        ui.blit(sombra, janela_rolo.topleft)
        ui.blit(pygame.transform.flip(sombra, False, True), (janela_rolo.x, janela_rolo.bottom - 8))

    def desenhar_aparelho(self, ui, cena, dx=0):
        cx, cy = self.CENTRO[0] + dx, self.CENTRO[1]
        corpo = pygame.Rect(cx - 86, cy - 62, 172, 124)
        pygame.draw.rect(ui, P.ESC, (corpo.x + 10, corpo.bottom - 2, corpo.w - 20, 8))        # pé
        moldura(ui, corpo, fundo=P.VERM2, borda=P.OURO, raio=6)
        placa = pygame.Rect(cx - 62, corpo.y - 12, 124, 22)
        moldura(ui, placa, fundo=P.NAVY, borda=P.OURO, raio=5)
        texto(ui, "SALGADINHO", placa.center, P.OURO, 11, ancora="center")
        f = cena.fracao_do_giro
        # alavanca: desce no começo do giro e volta
        puxada = math.sin(math.pi * janela(f, 0, 0.3)) if f is not None else 0.0
        topo = corpo.y + 26 + int(54 * puxada)
        pygame.draw.rect(ui, P.ESC, (corpo.right - 2, corpo.centery + 14, 16, 12))
        pygame.draw.rect(ui, P.CINZA, (corpo.right, corpo.centery + 16, 12, 8))
        pygame.draw.line(ui, P.ESC, (corpo.right + 9, corpo.centery + 18), (corpo.right + 9, topo), 5)
        pygame.draw.line(ui, P.CINZA, (corpo.right + 9, corpo.centery + 18), (corpo.right + 9, topo), 3)
        pygame.draw.circle(ui, P.ESC, (corpo.right + 9, topo), 8)
        pygame.draw.circle(ui, P.VERM, (corpo.right + 9, topo), 6)
        pygame.draw.circle(ui, clarear(P.VERM, 80), (corpo.right + 7, topo - 2), 2)
        # rolos
        iguais = self._rolos_premiados(cena)
        for i in range(self.jogo.ROLOS):
            rolo = pygame.Rect(cx - 73 + i * 50, corpo.y + 22, 46, 58)
            self._rolo(ui, rolo, i, cena)
            if i in iguais and int(cena.tempo * 6) % 2 == 0:
                pygame.draw.rect(ui, P.OURO, rolo.inflate(4, 4), 2)
        pygame.draw.line(ui, P.VERM, (cx - 78, corpo.y + 51), (cx - 75, corpo.y + 51), 1)
        pygame.draw.line(ui, P.VERM, (cx + 75, corpo.y + 51), (cx + 78, corpo.y + 51), 1)
        # bandeja de onde caem as moedas
        bandeja = pygame.Rect(cx - 50, corpo.bottom - 32, 100, 18)
        pygame.draw.rect(ui, P.ESC, bandeja, border_radius=3)
        pygame.draw.rect(ui, (60, 20, 34), bandeja.inflate(-4, -4), border_radius=2)
        for k in range(5):                                             # luzinhas do painel
            acesa = (k + int(cena.tempo * (10 if f is not None else 3))) % 2 == 0
            pygame.draw.circle(ui, P.OURO if acesa else P.OURO2, (cx - 40 + k * 20, corpo.bottom - 8), 2)

    def _rolos_premiados(self, cena):
        if not self.parado_com_resultado(cena):
            return ()
        simbolos = cena.resultado.simbolos
        return tuple(i for i, s in enumerate(simbolos) if simbolos.count(s) > 1)

    def origem_do_premio(self):
        return self.CENTRO[0], self.CENTRO[1] + 53

    def desenhar_rotulo(self, ui, linha, pos, cor):
        nome = linha.rotulo.removeprefix("Três ")
        if nome == linha.rotulo:
            return super().desenhar_rotulo(ui, linha, pos, cor)
        for k in range(3):                                   # o trio em figurinhas, que é mais curto que o nome
            self._simbolo(ui, nome, (pos[0] + 8 + k * 20, pos[1] + 6), 15)


class MesaDoDado(Mesa):
    """O d20 que quica, gira e cai mostrando o número."""

    PASTA_CRUPIE = "mestre_de_rpg"
    RAIO = 44

    def rotulo_da_escolha(self, escolha):
        meio = self.jogo.LADOS // 2
        return f"ACIMA ({meio + 1}-{self.jogo.LADOS})" if escolha == "acima" else f"ABAIXO (2-{meio})"

    def _d20(self, ui, centro, angulo, numero, cor):
        cx, cy = centro
        fora = [(cx + self.RAIO * math.cos(angulo + k * math.pi / 3), cy + self.RAIO * math.sin(angulo + k * math.pi / 3))
                for k in range(6)]
        dentro = [(cx + self.RAIO * 0.52 * math.cos(angulo + math.pi / 6 + k * 2 * math.pi / 3),
                   cy + self.RAIO * 0.52 * math.sin(angulo + math.pi / 6 + k * 2 * math.pi / 3)) for k in range(3)]
        pygame.draw.polygon(ui, escurecer_cor(cor, 60), fora)
        for k in range(3):                                    # facetas claras e escuras
            a, b = fora[2 * k], fora[2 * k + 1]
            pygame.draw.polygon(ui, cor if k else clarear(cor, 40), [a, b, dentro[k]])
        pygame.draw.polygon(ui, clarear(cor, 20), dentro)
        for k in range(3):
            for ponta in (fora[2 * k], fora[2 * k + 1], fora[(2 * k + 2) % 6]):
                pygame.draw.line(ui, P.ESC, dentro[k], ponta)
        pygame.draw.polygon(ui, P.ESC, dentro, 1)
        pygame.draw.polygon(ui, P.ESC, fora, 2)
        texto(ui, numero, (cx, cy), P.BRANCO, 23 if len(numero) < 3 else 11, ancora="center")

    def desenhar_aparelho(self, ui, cena, dx=0):
        cx, cy = self.CENTRO[0] + dx, self.CENTRO[1] + 18
        bandeja = pygame.Rect(cx - 130, cy + 30, 260, 40)                    # bandeja de couro
        pygame.draw.ellipse(ui, P.ESC, bandeja.inflate(4, 4))
        pygame.draw.ellipse(ui, (112, 66, 36), bandeja)
        pygame.draw.ellipse(ui, (54, 30, 40), bandeja.inflate(-12, -10))
        f = cena.fracao_do_giro
        if f is not None:
            k = ease_out(f)
            x = cx - 240 * (1 - k)
            y = cy - abs(math.sin(f * math.pi * 4.5)) * 84 * (1 - f)
            angulo = (1 - k) * 5 * math.pi
            numero = str(random.Random(cena.tique).randint(1, self.jogo.LADOS)) if f < 0.92 \
                else cena.resultado.simbolos[0]
            cor = P.ROXO
        elif cena.resultado is not None:
            x, y, angulo = cx, cy, 0.0
            numero = cena.resultado.simbolos[0]
            cor = P.OURO2 if numero == str(self.jogo.LADOS) else (110, 106, 124) if numero == "1" else P.ROXO
        else:
            x, y, angulo, numero, cor = cx, cy - 6 + 4 * math.sin(cena.tempo * 2), 0.0, "?", P.ROXO
        sombra = pygame.Surface((90, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, 90), sombra.get_rect())
        ui.blit(sombra, (x - 45, cy + 42))
        self._d20(ui, (x, y), angulo - math.pi / 2, numero, cor)

    def origem_do_premio(self):
        return self.CENTRO[0], self.CENTRO[1] + 18


class MesaDaRoleta(Mesa):
    """Roda do cardápio: gira rápido, vai perdendo força e para com o prato no ponteiro."""

    PASTA_CRUPIE = "monitor"
    TITULO = "BANDEJÃO"
    RAIO = 73
    CORES = {"Strogonoff": P.OURO2, "Bife": P.VERM2, "Frango": (214, 110, 40), "Salada": (50, 140, 76)}
    SEM_PREMIO = ((44, 50, 96), (30, 34, 70))

    def rotacao(self, cena):
        """Ângulo (radianos) da roda. No fim, o meio do setor sorteado fica embaixo do ponteiro (em cima)."""
        setores = self.jogo.SETORES
        if cena.resultado is None:
            return cena.tempo * 0.35
        fatia = 2 * math.pi / len(setores)
        alvo = -math.pi / 2 - (setores.index(cena.resultado.simbolos[0]) + 0.5) * fatia
        if cena.fracao_do_giro is None:
            return alvo
        return alvo - 7 * 2 * math.pi * (1 - ease_out(cena.fracao_do_giro))

    def desenhar_aparelho(self, ui, cena, dx=0):
        cx, cy = self.CENTRO[0] + dx, self.CENTRO[1] + 3
        r = self.RAIO
        pygame.draw.polygon(ui, P.ESC, [(cx - 7, cy), (cx + 7, cy), (cx + 22, cy + r + 4), (cx - 22, cy + r + 4)])   # pé
        pygame.draw.polygon(ui, (120, 74, 40), [(cx - 5, cy), (cx + 5, cy), (cx + 19, cy + r + 2), (cx - 19, cy + r + 2)])
        pygame.draw.circle(ui, P.ESC, (cx, cy), r + 5)
        pygame.draw.circle(ui, P.OURO2, (cx, cy), r + 3)
        setores = self.jogo.SETORES
        fatia = 2 * math.pi / len(setores)
        rot = self.rotacao(cena)
        sorteado = cena.resultado.simbolos[0] if self.parado_com_resultado(cena) else None
        for i, nome in enumerate(setores):
            a0 = rot + i * fatia
            cor = self.CORES.get(nome, self.SEM_PREMIO[i % 2])
            if nome == sorteado and int(cena.tempo * 6) % 2 == 0:
                cor = clarear(cor, 70)
            pontos = [(cx, cy)] + [(cx + r * math.cos(a0 + fatia * k / 6), cy + r * math.sin(a0 + fatia * k / 6))
                                   for k in range(7)]
            pygame.draw.polygon(ui, cor, pontos)
            pygame.draw.line(ui, P.ESC, (cx, cy), pontos[1])
        for i, nome in enumerate(setores):                      # nomes ao longo do raio
            meio = rot + (i + 0.5) * fatia
            img = fonte(11, True).render(nome, False, P.BRANCO if nome in self.CORES else P.CINZA)
            graus = -math.degrees(meio)
            if math.cos(meio) < 0:
                graus += 180
            img = pygame.transform.rotate(img, graus)
            ui.blit(img, img.get_rect(center=(cx + r * 0.55 * math.cos(meio), cy + r * 0.55 * math.sin(meio))))
        for k in range(16):                                      # lâmpadas do aro
            a = k * math.pi / 8
            acesa = (k + int(cena.tempo * (12 if cena.fracao_do_giro is not None else 2))) % 2 == 0
            pygame.draw.circle(ui, P.BRANCO if acesa else P.OURO, (cx + (r + 3) * math.cos(a), cy + (r + 3) * math.sin(a)), 1)
        pygame.draw.circle(ui, P.ESC, (cx, cy), 6)
        pygame.draw.circle(ui, P.OURO, (cx, cy), 4)
        pygame.draw.circle(ui, P.OURO2, (cx, cy), 2)
        # ponteiro: balança enquanto os pinos passam
        bate = math.sin(rot * len(setores)) * 4 if cena.fracao_do_giro is not None else 0
        ponta = (cx + bate, cy - r + 5)
        pygame.draw.polygon(ui, P.ESC, [(cx - 8, cy - r - 7), (cx + 8, cy - r - 7), (ponta[0], ponta[1] + 2)])
        pygame.draw.polygon(ui, P.VERM, [(cx - 6, cy - r - 6), (cx + 6, cy - r - 6), ponta])

    def origem_do_premio(self):
        return self.CENTRO


MESAS = {MaquinaDeSalgadinho: MesaDaMaquina, DadoDoMestre: MesaDoDado, RoletaDoBandejao: MesaDaRoleta}


def mesa_de(jogo):
    """A mesa do jogo; quem não tem uma própria usa a genérica."""
    return MESAS.get(type(jogo), MesaGenerica)(jogo)
