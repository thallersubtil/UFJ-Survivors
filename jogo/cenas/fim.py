"""Fim de jogo: o boletim oficial do semestre na mesa, datilografado, com carimbo (opção A aprovada).

Uma nota por prova (classe Boletim), o desempenho da partida e as conquistas. O nome para o ranking é a
assinatura do aluno no pé do boletim.
"""
import math

import pygame

from jogo.boletim import Boletim
from jogo.cenas.cena import Cena
from jogo.cenas.ranking import CenaRanking
from jogo.loja.conquistas import Conquistas
from jogo.nucleo.recursos import Recursos
from jogo.ranking import RegistroRanking
from jogo.ui.materiais import caneta, carimbo, circulo_caneta, madeira, papel
from jogo.ui.pixel import A, ESCALA, L, CamadaPixel, Paleta as P, ease_back, ease_out, icone, janela, no_quadrado, texto

TINTA = (40, 40, 80)
AZUL_CANETA = (40, 50, 120)


def _milhar(valor):
    return f"{valor:,}".replace(",", ".")


class CenaFimDeJogo(Cena):
    FOLHA = pygame.Rect(70, 10, 500, 336)
    VELOCIDADE_DIGITAR = 30          # letras por segundo da "máquina de escrever"

    def __init__(self, app, jogo):
        super().__init__(app)
        self._caixa_da_foto = None
        self.jogo = jogo
        self.nome = ""
        self.tempo = 0.0
        self.camada = CamadaPixel()
        self._mesa = None
        self.moedas = jogo.moedas_ganhas()
        if self.moedas:
            app.progresso.ganhar(self.moedas)
        self.conquistas = [] if jogo.treino else Conquistas.verificar(jogo, app.progresso)
        self.boletim = Boletim(jogo)
        pygame.key.start_text_input()

    @staticmethod
    def motivo(jogo):
        """Em que matéria o aluno reprovou (a do chefe mais antigo em campo ou, sem chefe, a da prova);
        para quem venceu o semestre e caiu no projeto de extensão, quanto durou nele e quantos pontos fez."""
        if jogo.venceu:
            pontos = getattr(jogo.fase, "pontos_feitos", None)
            if pontos is None:                  # treino: acabou quando o chefe caiu
                return ""
            minutos, segundos = divmod(int(jogo.fase.tempo), 60)
            return (f"Semestre aprovado. Projeto de extensão: durou {minutos:02d}:{segundos:02d} "
                    f"e fez {_milhar(pontos(jogo.placar))} pontos.")
        if jogo.chefe is not None and jogo.chefe.ativo:
            return f"Reprovado em {jogo.chefe.nome}."
        return f"Reprovado em {jogo.fase.MATERIA}." if jogo.fase.MATERIA else "Reprovado."

    # ------------------------------------------------------------ regras
    def _salvar(self):
        if self.jogo.treino:
            self._sair()
            return
        registro = self.jogo.resultado(self.nome)
        self.app.ranking.adicionar(registro)
        pygame.key.stop_text_input()
        self.app.trocar(CenaRanking(self.app, destaque=registro))

    def _sair(self):
        from jogo.cenas.titulo import CenaTitulo
        pygame.key.stop_text_input()
        self.app.trocar(CenaTitulo(self.app))

    def tratar_evento(self, evento):
        if evento.type == pygame.TEXTINPUT:
            for letra in evento.text:
                if letra.isprintable() and len(self.nome) < RegistroRanking.TAMANHO_NOME:
                    self.nome += letra
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_BACKSPACE:
                self.nome = self.nome[:-1]
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._salvar()
            elif evento.key == pygame.K_ESCAPE:
                self._sair()

    def atualizar(self, dt):
        self.tempo += dt

    # ------------------------------------------------------------ desenho
    def _digitar(self, inicio, txt, vel=None):
        return txt[:max(0, int((self.tempo - inicio) * (vel or self.VELOCIDADE_DIGITAR)))]

    def _fundo_mesa(self, tela):
        if self._mesa is None or self._mesa.get_size() != tela.get_size():
            mesa = pygame.Surface((L, A))
            madeira(mesa, mesa.get_rect(), (104, 66, 40), tabuas=28, semente=6)
            self._mesa = pygame.transform.scale(mesa, tela.get_size())
        tela.blit(self._mesa, (0, 0))

    def _foto(self, ui, r):
        s = pygame.Surface(r.size)
        s.fill((200, 214, 236))
        self._caixa_da_foto = r                    # a foto 3x4 entra depois, direto na tela (veja _foto_nitida)
        if self.jogo.jogador.foto(r.w * ESCALA) is None:      # sem a arte da foto: o boneco de perto
            animacoes = self.jogo.jogador.animador.animacoes
            animacao = animacoes.get("parado") or next(iter(animacoes.values()))
            quadro = animacao.quadros[int(self.tempo * 5) % len(animacao.quadros)]
            caixa = quadro.get_bounding_rect()
            if caixa.w and caixa.h:
                quadro = quadro.subsurface(caixa)
            img = no_quadrado(quadro, int(r.h * 1.5))
            s.blit(img, img.get_rect(midtop=(r.w // 2, 3)))
        ui.blit(s, r)
        pygame.draw.rect(ui, (70, 70, 90), r, 1)

    def _foto_nitida(self, tela):
        """A foto 3x4 do aluno vai direto na tela, em resolução cheia: pela camada sairia em blocos."""
        r = self._caixa_da_foto
        foto = self.jogo.jogador.foto(r.w * ESCALA) if r is not None else None
        if foto is None:
            return
        area = pygame.Rect(r.x * ESCALA, r.y * ESCALA, r.w * ESCALA, r.h * ESCALA).inflate(-2 * ESCALA, -2 * ESCALA)
        tela.set_clip(area.clip(tela.get_rect()))
        tela.blit(foto, foto.get_rect(midtop=area.midtop))
        tela.set_clip(None)

    def _cabecalho(self, ui, b):
        if (Recursos.pasta / "sprites/logo.png").exists():
            ui.blit(icone("sprites/logo.png", 70), (b.x + 12, b.y + 8))
        texto(ui, "UNIVERSIDADE FEDERAL DE JATAÍ", (b.x + 92, b.y + 10), (30, 40, 90), 11, contorno=None)
        subtitulo = "Boletim do semestre 2026/2" + ("  ·  MODO TREINO" if self.jogo.treino else "")
        texto(ui, subtitulo, (b.x + 92, b.y + 24), (90, 90, 110), 11, contorno=None, media=True)
        pygame.draw.line(ui, (30, 40, 90), (b.x + 10, b.y + 50), (b.right - 10, b.y + 50), 2)
        self._foto(ui, pygame.Rect(b.right - 62, b.y + 8, 48, 60))
        j = self.jogo.jogador
        texto(ui, f"Aluno(a): {j.NOME.upper()}", (b.x + 12, b.y + 58), TINTA, 11, contorno=None)
        texto(ui, f"Nível {j.nivel}  ·  média {self.boletim.media:.1f}".replace(".", ","), (b.x + 180, b.y + 58),
              (90, 90, 110), 11, contorno=None, media=True)

    def _tabela(self, ui, b):
        colunas = (("Disciplina", 12), ("Nota", 330), ("Situação", 400))
        ty = b.y + 78
        pygame.draw.rect(ui, (226, 232, 244), (b.x + 10, ty, b.w - 20, 16))
        for nome, x in colunas:
            texto(ui, nome, (b.x + x, ty + 3), (40, 50, 110), 11, contorno=None)
        cores = {"APROVADO": (40, 140, 60), "REPROVADO": P.MARGEM, "NÃO CURSOU": (130, 130, 150)}
        for i, linha in enumerate(self.boletim.linhas):
            y = ty + 20 + i * 22
            pygame.draw.line(ui, (210, 210, 220), (b.x + 10, y + 18), (b.right - 10, y + 18))
            inicio = 0.6 + i * 0.5
            disciplina = linha.disciplina if len(linha.disciplina) <= 44 else linha.disciplina[:42] + "."
            texto(ui, self._digitar(inicio, disciplina), (b.x + 12, y + 2), TINTA, 11, contorno=None)
            if self.tempo > inicio + 0.4:
                texto(ui, linha.nota_texto, (b.x + 338, y + 2), P.MARGEM if linha.nota is not None else TINTA, 11,
                      contorno=None)
                if linha.nota is not None:
                    circulo_caneta(ui, pygame.Rect(b.x + 330, y - 2, 36, 18), ease_out(janela(self.tempo, inicio + 0.4, 0.3)))
                texto(ui, linha.situacao, (b.x + 400, y + 2), cores[linha.situacao], 11, contorno=None)
        altura = 20 + len(self.boletim.linhas) * 22
        for x in (320, 390):
            pygame.draw.line(ui, (210, 210, 220), (b.x + x, ty), (b.x + x, ty + altura))
        return ty + altura

    def _desempenho(self, ui, b, y):
        placar = self.jogo.placar
        dados = (("Tempo", placar.tempo_formatado), ("Eliminações", _milhar(placar.eliminacoes)),
                 ("Pontos", _milhar(placar.pontuacao_final(self.jogo.venceu))), ("Combos 67", str(placar.combos_67)),
                 ("Moedas", f"+{self.moedas}"))
        texto(ui, "Desempenho", (b.x + 12, y), (40, 50, 110), 11, contorno=None)
        for i, (nome, valor) in enumerate(dados):
            x = b.x + 12 + i * 96
            texto(ui, nome, (x, y + 16), (110, 110, 130), 11, contorno=None, media=True)
            if self.tempo > 2.2 + i * 0.1:
                texto(ui, valor, (x, y + 30), TINTA, 11, contorno=None)
        y += 48
        motivo = self.motivo(self.jogo)
        if motivo:
            texto(ui, motivo, (b.x + 12, y), (40, 150, 60) if self.jogo.venceu else P.MARGEM, 11, contorno=None,
                  media=True)
            y += 14
        if self.conquistas:
            nomes = ", ".join(f"{c.NOME} (+{c.PREMIO})" for c in self.conquistas[:3])
            texto(ui, f"Conquistas: {nomes}", (b.x + 12, y), (150, 100, 20), 11, contorno=None, media=True)

    def _assinatura(self, ui, b):
        linha_y = b.bottom - 30
        pygame.draw.line(ui, (120, 110, 90), (b.x + 20, linha_y), (b.x + 200, linha_y))
        if self.jogo.treino:
            texto(ui, "Treino não entra no ranking", (b.x + 20, linha_y + 4), (110, 110, 130), 11, contorno=None,
                  media=True)
            return
        texto(ui, "Assinatura do aluno (seu nome)", (b.x + 20, linha_y + 4), (110, 110, 130), 11, contorno=None,
              media=True)
        cursor = "_" if int(self.tempo * 2) % 2 == 0 else ""
        texto(ui, self.nome + cursor, (b.x + 26, linha_y - 16), AZUL_CANETA, 11, contorno=None)
        if self.nome:                       # rabisco embaixo do nome, como assinatura
            fim = b.x + 26 + min(170, len(self.nome) * 8)
            pontos = [(x, linha_y - 3 + int(1.5 * math.sin(x * 0.5))) for x in range(b.x + 26, fim, 4)]
            if len(pontos) > 1:
                caneta(ui, pontos, AZUL_CANETA, 1)

    def desenhar(self, tela):
        self._fundo_mesa(tela)
        ui = self.camada.limpar()
        b = self.FOLHA.move(0, int(360 * (1 - ease_out(janela(self.tempo, 0, 0.5)))))
        papel(ui, b, (252, 250, 242), semente=41)
        pygame.draw.rect(ui, (170, 170, 186), (b.x + 30, b.y - 8, 14, 34), 2, border_radius=6)       # clipe
        self._cabecalho(ui, b)
        fim_tabela = self._tabela(ui, b)
        self._desempenho(ui, b, fim_tabela + 10)
        self._assinatura(ui, b)
        if self.tempo > 3.0:
            aprovado = self.jogo.venceu
            k = ease_back(janela(self.tempo, 3.0, 0.3), 2.5)
            marca = carimbo("APROVADO" if aprovado else "REPROVADO", (40, 150, 60) if aprovado else P.MARGEM, 14,
                            2.6 - 1.6 * k, 23)
            ui.blit(marca, marca.get_rect(center=(b.right - 110, b.bottom - 50)))
            if self.tempo < 3.15:
                tremor = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
                tremor.fill((255, 255, 255, 40))
                tela.blit(tremor, (0, 0))
        rodape = "Enter: voltar ao título" if self.jogo.treino else \
            "Digite seu nome    Enter: salvar no ranking    Esc: sair sem salvar"
        texto(ui, rodape, (L // 2, A - 12), P.BRANCO, 11, ancora="midtop")
        self.camada.apresentar(tela)
        self._foto_nitida(tela)
