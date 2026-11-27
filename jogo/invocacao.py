"""Círculo de invocação: o lugar do mapa onde um mini-chefe espera o aluno."""
import math

import pygame

from jogo.config import Cor
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos


class LocalDeInvocacao(Entidade):
    """Círculo no chão com o rosto do mini-chefe em cima. Enche enquanto o aluno fica dentro e, cheio,
    invoca o mini-chefe ali mesmo. Sair do círculo esvazia aos poucos: a escolha de lutar é do aluno.

    Quem nunca foi invocado (em nenhuma partida) é um mistério: o círculo, o mini-mapa e a seta mostram
    um "?" e o nome "Mini-boss misterioso". Invocar revela o mini-chefe para sempre (Jogo.conhecer_mini_chefe).
    """

    grupo = "invocacao"
    camada = 0
    RAIO = 84
    TEMPO = 2.5                  # segundos dentro do círculo para invocar
    PERDA = 0.6                  # quanto do progresso por segundo se perde fora dele
    NOME_MISTERIOSO = "Mini-boss misterioso"
    ROSTO_MISTERIOSO = "rostos/misterioso.png"
    COR_MISTERIOSA = (170, 150, 220)

    def __init__(self, posicao, nome_do_inimigo):
        super().__init__(posicao, self.RAIO)
        self.classe = FabricaDeInimigos.classe(nome_do_inimigo)
        self.nome_do_inimigo = nome_do_inimigo
        self.progresso = 0.0     # 0 a 1
        self.tempo = 0.0
        self.descoberto = not self.classe.SECRETO     # o secreto só entra no mapa quando o aluno chega perto
        self.revelado = False        # já foi invocado alguma vez? (o Jogo diz, a cada quadro)

    @property
    def CHAVE(self):
        """Quem ele é de verdade (nome na FabricaDeInimigos): é o que a marcação no mini-mapa guarda."""
        return self.nome_do_inimigo

    @property
    def NOME(self):
        return self.classe.NOME if self.revelado else self.NOME_MISTERIOSO

    @property
    def cor(self):
        return self.classe.COR if self.revelado else self.COR_MISTERIOSA

    DISTANCIA_PARA_DESCOBRIR = 520

    @property
    def rosto(self):
        return f"rostos/{self.classe.PASTA_SPRITE}.png" if self.revelado else self.ROSTO_MISTERIOSO

    @property
    def no_mapa(self):
        return self.descoberto

    @property
    def invocado(self):
        return False

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.revelado = jogo.mini_chefe_conhecido(self.nome_do_inimigo)
        distancia = jogo.jogador.posicao.distance_to(self.posicao)
        if not self.descoberto and distancia <= self.DISTANCIA_PARA_DESCOBRIR:
            self.descoberto = True
            jogo.marcos.add("segredo")
            jogo.anunciar("Tem alguma coisa estranha por aqui...", 3)
        dentro = distancia <= self.raio
        if dentro:
            self.progresso += dt / self.TEMPO
        else:
            self.progresso = max(0.0, self.progresso - self.PERDA * dt)
        if self.progresso >= 1:
            self.invocar(jogo)

    def invocar(self, jogo):
        chegada = jogo.fase.posicao_de_nascimento(jogo)       # logo fora da tela: ele entra andando
        chefe = FabricaDeInimigos.criar(self.nome_do_inimigo, chegada, jogo.escala_dos_mini_chefes)
        chefe.posto = pygame.Vector2(self.posicao)            # o lugar que ele guarda é o do círculo
        jogo.abrir_espaco(jogo.jogador.posicao, chefe.GUARDA)    # como na chegada de um chefe, só em volta do aluno
        jogo.adicionar(chefe)
        chefe.ao_chegar(jogo)
        jogo.chefe_a_apresentar = chefe          # a partida para e ele é apresentado, como os chefes das provas
        jogo.conhecer_mini_chefe(self.nome_do_inimigo)      # deixa de ser misterioso, nesta partida e nas próximas
        Recursos.tocar("especial", 0.6)
        self.remover()
        return chefe

    def esta_visivel(self, camera):
        return camera.visivel(self.posicao, 220)

    def desenhar(self, tela, camera):
        centro = camera.para_tela(self.posicao)
        cor = self.cor
        lado = self.raio * 2 + 12
        chao = pygame.Surface((lado, lado), pygame.SRCALPHA)
        meio = (lado // 2, lado // 2)
        pulso = 0.5 + 0.5 * math.sin(self.tempo * 3)
        pygame.draw.circle(chao, (20, 14, 30, 90), meio, self.raio)
        pygame.draw.circle(chao, (*cor, int(40 + 50 * pulso)), meio, round(self.raio * self.progresso))
        pygame.draw.circle(chao, (*cor, 200), meio, self.raio, 4)
        for i in range(8):                                     # marcas girando na borda
            ponta = pygame.Vector2(self.raio - 10, 0).rotate(self.tempo * 40 + i * 45)
            pygame.draw.circle(chao, (*cor, 230), (meio[0] + ponta.x, meio[1] + ponta.y), 4)
        if self.progresso > 0:
            caixa = pygame.Rect(0, 0, self.raio * 2, self.raio * 2)
            caixa.center = meio
            pygame.draw.arc(chao, (255, 255, 255, 240), caixa, math.pi / 2 - 2 * math.pi * self.progresso,
                            math.pi / 2, 8)
        chao = pygame.transform.scale(chao, (lado, round(lado * 0.6)))      # círculo visto de cima em 3/4
        tela.blit(chao, chao.get_rect(center=(round(centro.x), round(centro.y))))
        rosto = Recursos.imagem(self.rosto, 56)
        flutua = round(4 * math.sin(self.tempo * 2.5))
        topo = round(centro.y - 78 + flutua)
        pygame.draw.circle(tela, Cor.BORDA_ESCURA, (round(centro.x), topo), 34)
        pygame.draw.circle(tela, cor, (round(centro.x), topo), 34, 3)
        tela.blit(rosto, rosto.get_rect(center=(round(centro.x), topo)))
        nome = Recursos.fonte(15).render(self.NOME, True, Cor.TEXTO)
        tela.blit(nome, nome.get_rect(midbottom=(round(centro.x), topo - 38)))
        dica = "invocando..." if self.progresso > 0 else "fique no círculo para invocar"
        aviso = Recursos.fonte(13).render(dica, True, Cor.DESTAQUE if self.progresso > 0 else Cor.TEXTO_FRACO)
        tela.blit(aviso, aviso.get_rect(midtop=(round(centro.x), round(centro.y + self.raio * 0.6 + 4))))
