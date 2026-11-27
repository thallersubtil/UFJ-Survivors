"""O que os mini-chefes do mapa jogam no aluno: multas, carros desgovernados, o feixe de abdução e a
palestra do Leão do PROERD (cartilhas, a placa de DIGA NÃO e a dancinha)."""
import pygame

from jogo.jogador.bonus import BonusTemporario
from jogo.nucleo.animacao import Animador
from jogo.nucleo.colisao import Colisao
from jogo.nucleo.desenho import desenhar_faixa_de_aviso, desenhar_sprite
from jogo.nucleo.entidade import Entidade
from jogo.nucleo.recursos import Recursos
from jogo.projeteis.tematicos import GolpeNoChao, ProjetilTematico, arte_existe, imagem_da_arte, imagem_na_largura


class Multa(ProjetilTematico):
    """Multa de atraso da Bibliotecária: quase não fere, mas tira moedas do aluno."""

    def __init__(self, posicao, velocidade, dano, valor, cor):
        super().__init__(posicao, velocidade, dano, "R$", cor, raio=13, arte="multa")
        self.valor = valor

    def verificar_colisao(self, jogo):
        if Colisao.circulos_colidem(self, jogo.jogador):
            if jogo.ferir_jogador(self.dano):
                jogo.multar(self.valor)
            self.remover()


class VeiculoDesgovernado(Entidade):
    """Carro que buzina parado por um instante (a faixa no chão avisa por onde vai passar) e atravessa a tela."""

    grupo = "projetil_inimigo"
    camada = 1

    def __init__(self, posicao, direcao, pasta, velocidade, dano, raio, aviso=0.8, duracao=2.6):
        super().__init__(posicao, raio)
        self.direcao = pygame.Vector2(direcao).normalize()
        self.velocidade = velocidade
        self.dano = dano
        self.aviso = aviso
        self.duracao = duracao
        self.tempo = 0.0
        self.animador = Animador(Recursos.animacoes(pasta))

    @property
    def parado(self):
        return self.tempo < self.aviso

    def atualizar(self, dt, jogo):
        self.tempo += dt
        if self.parado:
            return
        self.animador.atualizar(dt)
        self.posicao += self.direcao * self.velocidade * dt
        if Colisao.circulos_colidem(self, jogo.jogador):
            jogo.ferir_jogador(self.dano)
        if self.tempo >= self.aviso + self.duracao:
            self.remover()

    def esta_visivel(self, camera):
        return True                       # a faixa de aviso atravessa a tela mesmo com o carro fora dela

    def desenhar(self, tela, camera):
        if self.parado:
            inicio = camera.para_tela(self.posicao)
            fim = inicio + self.direcao * self.velocidade * self.duracao
            desenhar_faixa_de_aviso(tela, inicio, fim, self.raio * 2, tempo=self.tempo)
        desenhar_sprite(tela, camera, self.animador.quadro_atual, self.posicao, espelhar=self.direcao.x < 0)


class FeixeDeAbducao(GolpeNoChao):
    """Anel verde que enche no chão (aviso) e, quando fecha, puxa para cima quem estiver dentro."""

    COR = (130, 255, 110)
    TEXTO = "ABDUZIDO!"
    ARTE_DO_ANEL = "anel_de_abducao"
    ARTE_DO_FEIXE = "feixe_de_luz"
    ARTE_DO_ABDUZIDO = "vaca"
    ALTURA_DO_FEIXE = 420

    def desenhar_chao(self, tela, centro):
        super().desenhar_chao(tela, centro)
        if arte_existe(self.ARTE_DO_ANEL):
            anel = imagem_na_largura(self.ARTE_DO_ANEL, round(self.raio * 2.2 / 8) * 8)
            tela.blit(anel, anel.get_rect(center=(round(centro.x), round(centro.y))))

    def desenhar_golpe(self, tela, centro):
        """A coluna de luz subindo, com uma vaca que estava passando."""
        if not self.disparou:
            return
        base = (round(centro.x), round(centro.y + self.raio * 0.3))
        if arte_existe(self.ARTE_DO_FEIXE):
            feixe = pygame.transform.scale(imagem_da_arte(self.ARTE_DO_FEIXE, 128),
                                           (round(self.raio * 2), self.ALTURA_DO_FEIXE))
            feixe.set_alpha(170)
            tela.blit(feixe, feixe.get_rect(midbottom=base))
        else:
            coluna = pygame.Surface((self.raio * 2, self.ALTURA_DO_FEIXE), pygame.SRCALPHA)
            coluna.fill((170, 255, 140, 90))
            tela.blit(coluna, coluna.get_rect(midbottom=base))
        if arte_existe(self.ARTE_DO_ABDUZIDO):
            subida = (self.tempo - self.AVISO) / self.BRILHO * self.ALTURA_DO_FEIXE * 0.6
            vaca = imagem_da_arte(self.ARTE_DO_ABDUZIDO, 44)
            tela.blit(vaca, vaca.get_rect(center=(base[0], round(base[1] - 60 - subida))))


class PapelDoProerd(ProjetilTematico):
    """O material da palestra do Leão do PROERD: cartilhas, certificados e medalhas, que voam girando."""

    GIRAM = {**ProjetilTematico.GIRAM, "cartilha": 300, "certificado": 240, "medalha": 420}
    ALTURAS = {**ProjetilTematico.ALTURAS, "cartilha": 34, "certificado": 30, "medalha": 30}


class PlacaDigaNao(GolpeNoChao):
    """A placa de DIGA NÃO desce do céu em cima do aluno e deixa o carimbo no chão."""

    COR = (230, 50, 50)
    TEXTO = "DIGA NÃO!"
    AVISO = 0.85
    BRILHO = 0.45
    ARTE_DO_GOLPE = "placa_diga_nao"
    ARTE_DA_MARCA = "diga_nao"


class RugidoDoLeao(GolpeNoChao):
    """O rugido do Leão do PROERD: o chão em volta dele enche (aviso) e, quando ele ruge, quem ainda estiver
    perto fica paralisado de medo, andando bem mais devagar por um tempo."""

    COR = (255, 120, 40)
    TEXTO = "PARALISADO DE MEDO!"
    AVISO = 1.1
    LENTIDAO = 0.45              # fator da velocidade do aluno enquanto dura o medo
    DURACAO_DO_MEDO = 2.5

    def ao_acertar(self, jogo):
        super().ao_acertar(jogo)
        jogo.jogador.adicionar_bonus(BonusTemporario("medo_do_leao", "velocidade", self.LENTIDAO,
                                                     self.DURACAO_DO_MEDO))


class MordidaDaToca(GolpeNoChao):
    """O Lobo-Guará saindo da terra debaixo do aluno: o chão racha (aviso) e ele morde quem ainda estiver em cima."""

    COR = (210, 120, 60)
    TEXTO = "MORDIDA!"
    AVISO = 0.45
    BRILHO = 0.35
    ARTE_DA_MARCA = "pegada"


class Silencio(GolpeNoChao):
    """O "SHHH!" da Bibliotecária: quem ainda estiver perto quando ela pede silêncio fica com as armas mais lentas
    por um tempo (biblioteca não é lugar de barulho)."""

    COR = (190, 110, 240)
    TEXTO = "SHHH!"
    AVISO = 0.45
    LENTIDAO = 2.5               # fator da recarga das armas enquanto dura o silêncio
    DURACAO_DO_SILENCIO = 3.0

    def ao_acertar(self, jogo):
        super().ao_acertar(jogo)
        jogo.jogador.adicionar_bonus(BonusTemporario("silencio", "recarga", self.LENTIDAO, self.DURACAO_DO_SILENCIO))


class OndaDeChoque(GolpeNoChao):
    """O Técnico em fúria soca o chão: o chão em volta dele racha e explode."""

    COR = (120, 235, 70)
    TEXTO = "ESMAGOU!"
    AVISO = 0.5


class ChegadaDoCeia(GolpeNoChao):
    """A promessa do Reitor finalmente chega: a placa do CEIA cai do céu em cima do aluno."""

    COR = (40, 150, 240)
    TEXTO = "CHEGOU O CEIA!"
    AVISO = 0.85
    BRILHO = 0.45
    ARTE_DO_GOLPE = "ceia_logo"
    ARTE_DA_MARCA = "ceia_icone"


class ColunaDeFogo(GolpeNoChao):
    """O Grão-Mestre ascendido marca o aluno com o olho que tudo vê e, depois, uma coluna de fogo dourado desce."""

    COR = (255, 200, 60)
    TEXTO = "QUEIMADO!"
    AVISO = 1.0
    BRILHO = 0.4
    ARTE_DO_GOLPE = "chama_dourada"
    ARTE_DA_MARCA = "olho"
