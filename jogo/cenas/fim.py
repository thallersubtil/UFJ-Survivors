import pygame

from jogo.cenas.cena import Cena
from jogo.cenas.ranking import CenaRanking
from jogo.cenas.widgets import desenhar_fundo, desenhar_painel, desenhar_texto
from jogo.config import ALTURA, LARGURA, Cor
from jogo.ranking import RegistroRanking


class CenaFimDeJogo(Cena):
    def __init__(self, app, jogo):
        super().__init__(app)
        self.jogo = jogo
        self.nome = ""
        self.tempo = 0.0
        pygame.key.start_text_input()

    def _salvar(self):
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

    def desenhar(self, tela):
        desenhar_fundo(tela, "cenario/titulo_fundo.png", escuro=190)
        venceu = self.jogo.venceu
        titulo = "APROVADO!" if venceu else "REPROVADO!"
        frase = "Você derrotou o Professor!" if venceu else "A Semana de Provas venceu desta vez."
        desenhar_texto(tela, titulo, 72, Cor.APROVADO if venceu else Cor.REPROVADO, centro=(LARGURA // 2, 110))
        desenhar_texto(tela, frase, 22, Cor.TEXTO, centro=(LARGURA // 2, 170))
        painel = pygame.Rect(0, 0, 560, 250)
        painel.center = (LARGURA // 2, 340)
        desenhar_painel(tela, painel)
        placar = self.jogo.placar
        linhas = (
            ("Pontuação final", str(placar.pontuacao_final(venceu))),
            ("Tempo", placar.tempo_formatado),
            ("Eliminações", str(placar.eliminacoes)),
            ("Nível", str(self.jogo.jogador.nivel)),
            ("Combos 67", str(placar.combos_67)),
        )
        for i, (rotulo, valor) in enumerate(linhas):
            y = painel.top + 26 + i * 42
            desenhar_texto(tela, rotulo, 22, Cor.TEXTO_FRACO, topo_esquerda=(painel.left + 30, y))
            desenhar_texto(tela, valor, 24, Cor.DESTAQUE, topo_direita=(painel.right - 30, y))
        cursor = "_" if int(self.tempo * 2) % 2 == 0 else " "
        caixa = pygame.Rect(0, 0, 460, 56)
        caixa.center = (LARGURA // 2, 540)
        desenhar_painel(tela, caixa, alfa=255)
        desenhar_texto(tela, f"Seu nome: {self.nome}{cursor}", 26, Cor.TEXTO, topo_esquerda=(caixa.left + 20, caixa.top + 12))
        desenhar_texto(tela, "[Enter] salvar no ranking    [Esc] sair sem salvar", 16, Cor.TEXTO_FRACO,
                       centro=(LARGURA // 2, ALTURA - 40))
