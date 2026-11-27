"""Itens passivos. Cada um soma seu efeito em Jogador.recalcular_atributos()."""
import pygame

from jogo.config import Cor
from jogo.itens.item import Item


class Energetico(Item):
    NOME = "Energético"
    DESCRICAO = "+10% de velocidade e armas 2,5% mais rápidas por nível, mas -5% de vida máxima por nível."
    ICONE = "icones/energetico.png"
    MELHORIAS = ("+10% de velocidade, -2,5% de recarga, -5% de vida máxima.",) * 3

    def aplicar(self, jogador):
        jogador.mult_velocidade += 0.10 * self.nivel
        jogador.mult_recarga *= 1 - 0.025 * self.nivel
        jogador.mult_vida_maxima *= 1 - 0.05 * self.nivel


class MarmitaDoRU(Item):
    """Comida de verdade: mais vida, e quem tem mais vida bate mais forte com a arma inicial e o especial."""
    NOME = "Marmita do RU"
    DESCRICAO = "+15 de vida máxima por nível; cada 6 de vida máxima dá +1% de dano da arma inicial e do especial."
    ICONE = "icones/marmita.png"
    MELHORIAS = ("+15 de vida máxima.",) * 3
    VIDA_POR_NIVEL = 15
    VIDA_POR_PONTO = 6               # cada tanto de vida máxima vale +1% de dano da arma inicial e do especial

    def aplicar(self, jogador):
        jogador.vida_maxima_extra += self.VIDA_POR_NIVEL * self.nivel
        jogador.reforco_por_vida += 0.01 / self.VIDA_POR_PONTO


def mais_perto(jogo, jogador, raio):
    """O inimigo mais perto do aluno dentro de `raio`, ou None."""
    return jogo.inimigo_mais_proximo(jogador.posicao, raio)


class MochilaPesada(Item):
    NOME = "Mochila Pesada"
    DESCRICAO = "-6% de dano recebido por nível e -10% de velocidade; às vezes devolve o golpe em dobro."
    ICONE = "icones/mochila.png"
    MELHORIAS = ("-6% de dano recebido; mais chance de devolver.",) * 3
    REDUCAO_POR_NIVEL = 0.0625       # no nível 4: -25%
    DEVOLVER_POR_NIVEL = 0.125       # no nível 4: 50% de chance
    DEVOLVE = 2.0                    # devolve 200% do golpe
    LENTIDAO = 0.10
    ALCANCE_DO_TROCO = 160

    def aplicar(self, jogador):
        jogador.mult_velocidade -= self.LENTIDAO

    def ao_ser_atingido(self, dano, jogador, jogo):
        if dano <= 0:
            return dano
        if jogo.rng.random() < jogador.chance(self.DEVOLVER_POR_NIVEL * self.nivel):
            alvo = mais_perto(jogo, jogador, self.ALCANCE_DO_TROCO)
            if alvo is not None:
                jogo.causar_dano(alvo, dano * self.DEVOLVE, alvo.posicao - jogador.posicao, forte=True)
        return dano * (1 - self.REDUCAO_POR_NIVEL * self.nivel)


class FoneDeOuvido(Item):
    NOME = "Fone de Ouvido"
    DESCRICAO = "6% de chance de nem sentir o golpe: o som estoura e empurra os inimigos em volta."
    ICONE = "icones/fone.png"
    MELHORIAS = ("9% de chance.", "12% de chance.", "15% de chance.")
    CHANCE = (0.06, 0.09, 0.12, 0.15)
    RAIO = 200
    FORCA = 520

    def aplicar(self, jogador):
        """Nada fixo: o efeito está em `ao_ser_atingido`."""

    def ao_ser_atingido(self, dano, jogador, jogo):
        if dano <= 0 or jogo.rng.random() >= jogador.chance(self.CHANCE[self.nivel - 1]):
            return dano
        from jogo.efeitos import OndaDoGrito, TextoFlutuante
        for inimigo in jogo.inimigos_proximos(jogador.posicao, self.RAIO):
            direcao = inimigo.posicao - jogador.posicao
            inimigo.empurrar(direcao if direcao.length_squared() > 0 else pygame.Vector2(1, 0), self.FORCA)
        jogo.adicionar(OndaDoGrito(jogador, self.RAIO))
        jogo.adicionar(TextoFlutuante("NO VOLUME MÁXIMO!", jogador.posicao - (0, 60), Cor.CURA, 18))
        return 0


class GarrafaTermica(Item):
    NOME = "Garrafa Térmica"
    DESCRICAO = "Sopa quente o dia todo: tudo que recupera vida recupera 20% a mais por nível."
    ICONE = "icones/garrafa.png"
    MELHORIAS = ("+20% de cura.", "+20% de cura.", "+20% de cura.")
    CURA_POR_NIVEL = 0.20

    def aplicar(self, jogador):
        jogador.mult_cura += self.CURA_POR_NIVEL * self.nivel


class TenisDeCorrida(Item):
    NOME = "Tênis de Corrida"
    DESCRICAO = "O rolamento recarrega 15% mais rápido por nível."
    ICONE = "icones/tenis.png"
    MELHORIAS = ("-15% de recarga do rolamento.", "-15% de recarga do rolamento.", "-15% de recarga do rolamento.")
    PRECO_DESBLOQUEIO = 250

    def aplicar(self, jogador):
        jogador.mult_rolamento *= 1 - 0.15 * self.nivel


class OculosDeGrau(Item):
    NOME = "Óculos de Grau"
    DESCRICAO = "Enxerga o ponto fraco: +5% de chance de crítico por nível."
    ICONE = "icones/oculos.png"
    MELHORIAS = ("+5% de crítico.", "+5% de crítico.", "+5% de crítico.")
    PRECO_DESBLOQUEIO = 300
    DISFARCE_POR_NIVEL = 0.20        # cada nível esconde melhor a Cola

    @property
    def disfarce_de_cola(self):
        return self.DISFARCE_POR_NIVEL * self.nivel

    def aplicar(self, jogador):
        jogador.chance_critico += 0.05 * self.nivel


class Cola(Item):
    """Notas mais rápido colando, com vida máxima menor e risco de ser pego.

    Pego colando, a cola é confiscada por alguns níveis: sem o bônus e sem o custo, e as notas
    rendem só metade até a punição acabar. Só aparece nas cartas de nível, nunca no baú.
    """
    NOME = "Cola"
    DESCRICAO = "1,5x de experiência, -15% de vida máxima. Cuidado para não ser pego!"
    ICONE = "sprites/nota.png"
    NIVEL_MAXIMO = 3
    MELHORIAS = ("2x de experiência, -20% de vida máxima.", "2,5x de experiência, -25% de vida máxima.")
    SO_AO_SUBIR_DE_NIVEL = True
    PESO = 0.5                          # aparece menos que os outros
    EXPERIENCIA = (1.5, 2.0, 2.5)
    CUSTO_VIDA = (0.15, 0.20, 0.25)
    CHANCE_FLAGRA = (0.02, 0.03, 0.04)        # por nível que o herói sobe
    EXPERIENCIA_PUNIDO = 0.5
    NIVEIS_DE_PUNICAO = 2

    def __init__(self):
        super().__init__()
        self._castigo = 0

    @property
    def punido(self):
        return self._castigo > 0

    def aplicar(self, jogador):
        if self.punido:
            jogador.fator_experiencia *= self.EXPERIENCIA_PUNIDO
            return
        jogador.fator_experiencia *= self.EXPERIENCIA[self.nivel - 1]
        jogador.mult_vida_maxima *= 1 - self.CUSTO_VIDA[self.nivel - 1]

    def chance_de_flagra(self, jogador, jogo):
        chance = self.CHANCE_FLAGRA[self.nivel - 1]
        if jogo.chefe is not None and jogo.chefe.ativo:
            chance *= 2                  # o professor está olhando
        for item in jogador.itens:       # quem disfarça a cola (os Óculos de Grau) diz o quanto
            chance *= max(0.0, 1 - item.disfarce_de_cola)
        return chance

    def ao_subir_de_nivel(self, jogador, jogo):
        if self.punido:
            self._castigo -= 1
            if not self.punido:
                jogo.anunciar("Cola devolvida")
                jogador.recalcular_atributos()
        elif jogo.rng.random() < self.chance_de_flagra(jogador, jogo):
            self._castigo = self.NIVEIS_DE_PUNICAO
            jogo.marcos.add("pego_colando")
            jogo.anunciar("PEGO COLANDO!", 3)
            jogador.recalcular_atributos()


class ConviteDaAtletica(Item):
    """Chamado para a Atlética: de tempos em tempos solta um grito de guerra que fere e empurra os inimigos."""
    NOME = "Convite da Atlética"
    DESCRICAO = "A cada 12 s, um grito de guerra fere e empurra os inimigos em volta."
    ICONE = "icones/atletica.png"
    MELHORIAS = ("Grita a cada 10 s, mais forte e mais longe.", "Grita a cada 8 s, mais forte e mais longe.",
                 "Grita a cada 6 s, mais forte e mais longe.")
    INTERVALO = (12.0, 10.0, 8.0, 6.0)
    RAIO = (160, 190, 220, 250)
    DANO = (10, 14, 18, 24)
    FORCA = 520

    def __init__(self):
        super().__init__()
        self._espera = self.INTERVALO[0]

    @property
    def intervalo(self):
        return self.INTERVALO[self.nivel - 1]

    @property
    def raio(self):
        return self.RAIO[self.nivel - 1]

    def aplicar(self, jogador):
        """O efeito é ativo (o grito); não mexe nos atributos."""

    def atualizar(self, dt, jogador, jogo):
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.intervalo
        self.gritar(jogador, jogo)

    def gritar(self, jogador, jogo):
        from jogo.efeitos import OndaDoGrito, TextoFlutuante
        from jogo.nucleo.recursos import Recursos
        dano = self.DANO[self.nivel - 1] * jogador.multiplicador_dano
        for inimigo in jogo.inimigos_proximos(jogador.posicao, self.raio):
            direcao = inimigo.posicao - jogador.posicao
            if direcao.length_squared() == 0:
                direcao = pygame.Vector2(1, 0)
            jogo.causar_dano(inimigo, dano, direcao)
            inimigo.empurrar(direcao, self.FORCA)
        jogo.adicionar(OndaDoGrito(jogador, self.raio))
        jogo.adicionar(TextoFlutuante("VAI, ATLÉTICA!", jogador.posicao - (0, 70), Cor.DESTAQUE, 20, duracao=1.0))
        Recursos.tocar("especial", 0.3)


class Pendrive(Item):
    """Guarda o especial: mais cargas para usar seguidas."""
    NOME = "Pendrive"
    DESCRICAO = "Guarda um especial a mais (2 cargas)."
    ICONE = "icones/pendrive.png"
    MELHORIAS = ("O especial recarrega 15% mais rápido.", "Mais uma carga (3 no total).",
                 "O especial recarrega 30% mais rápido.")

    def aplicar(self, jogador):
        jogador.cargas_especial += 1 if self.nivel < 3 else 2
        if self.nivel >= 2:
            jogador.mult_especial *= 0.70 if self.nivel >= 4 else 0.85


class MoedaDaSorte(Item):
    NOME = "Moeda da Sorte"
    DESCRICAO = "+15% de sorte por nível: mais crítico, desvio, moedas e baús melhores."
    ICONE = "legado/itens/item_luckycoin.png"
    MELHORIAS = ("+15% de sorte.", "+15% de sorte.", "+15% de sorte.")
    PRECO_DESBLOQUEIO = 350

    def aplicar(self, jogador):
        jogador.sorte += 0.15 * self.nivel


class JogoDeCintura(Item):
    NOME = "Jogo de Cintura"
    DESCRICAO = "5% de chance por nível de desviar de um golpe (a sorte aumenta)."
    ICONE = "legado/itens/item_smokebomb.png"
    MELHORIAS = ("+5% de desvio.", "+5% de desvio.", "+5% de desvio.")
    PRECO_DESBLOQUEIO = 300

    def aplicar(self, jogador):
        jogador.chance_desvio += 0.05 * self.nivel


class KitDePrimeirosSocorros(Item):
    """Os inimigos não soltam mais cura sozinhos: com o kit, de tempos em tempos o próximo eliminado solta uma poção."""

    NOME = "Kit de Primeiros Socorros"
    DESCRICAO = "A cada 30 s, o próximo inimigo eliminado deixa cair uma poção de vida."
    ICONE = "legado/itens/potion_hp.png"
    MELHORIAS = ("A poção vem a cada 24 s.", "A poção vem a cada 18 s.", "A poção vem a cada 12 s.")
    INTERVALOS = (30.0, 24.0, 18.0, 12.0)     # segundos entre uma poção e outra, por nível

    def __init__(self):
        super().__init__()
        self._espera = 0.0                     # começa carregado: a primeira eliminação já solta

    @property
    def intervalo(self):
        return self.INTERVALOS[self.nivel - 1]

    @property
    def pronto(self):
        return self._espera <= 0

    def aplicar(self, jogador):
        """Não mexe em atributo nenhum: o efeito está em `ao_eliminar`."""

    def atualizar(self, dt, jogador, jogo):
        self._espera = max(0.0, self._espera - dt)

    def ao_eliminar(self, inimigo, jogador, jogo):
        if self.pronto:
            from jogo.coletaveis.coletaveis import PocaoDeVida
            self._espera = self.intervalo
            jogo.adicionar(PocaoDeVida(inimigo.posicao + (10, 0)))


class AtestadoMedico(Item):
    """Uma vez só: o golpe que derrubaria o aluno vira atestado. Volta com metade da vida e o susto derruba quem
    estava em volta (chefes e mini-chefes aguentam)."""
    NOME = "Atestado Médico"
    DESCRICAO = "Uma vez por partida: em vez de cair, volta com 50% da vida e derruba os inimigos em volta."
    ICONE = "icones/caderno.png"
    NIVEL_MAXIMO = 1
    MELHORIAS = ()
    VIDA = 0.50
    RAIO = 320
    INVENCIVEL = 1.5

    def aplicar(self, jogador):
        """Nada fixo: o efeito está em `ao_ser_atingido`."""

    def ao_ser_atingido(self, dano, jogador, jogo):
        if dano < jogador.vida:
            return dano
        from jogo.efeitos import OndaDoGrito, TextoFlutuante
        jogador.vida = jogador.vida_maxima * self.VIDA
        jogador.invencivel = max(jogador.invencivel, self.INVENCIVEL)
        for inimigo in jogo.inimigos_proximos(jogador.posicao, self.RAIO):
            if not inimigo.CHEFE:
                jogo.causar_dano(inimigo, inimigo.vida * 10, inimigo.posicao - jogador.posicao)
        jogo.adicionar(OndaDoGrito(jogador, self.RAIO))
        jogo.adicionar(TextoFlutuante("ATESTADO MÉDICO!", jogador.posicao - (0, 70), Cor.CURA, 22, duracao=1.5))
        jogador.consumir_item(self)
        return 0


class NoiteSemDormir(Item):
    NOME = "Noite sem Dormir"
    DESCRICAO = "+7,5% de dano e armas 2,5% mais rápidas por nível, mas leva 30% a mais de dano."
    ICONE = "icones/energetico.png"
    MELHORIAS = ("+7,5% de dano e -2,5% de recarga.",) * 3
    DANO_RECEBIDO = 1.30

    def aplicar(self, jogador):
        jogador.mult_dano *= 1 + 0.075 * self.nivel
        jogador.mult_recarga *= 1 - 0.025 * self.nivel

    def ao_ser_atingido(self, dano, jogador, jogo):
        return dano * self.DANO_RECEBIDO


class PreTreinoDuvidoso(Item):
    NOME = "Pré-treino Duvidoso"
    DESCRICAO = "+10% de dano por nível, mas a vida escorre 5% por segundo até sobrar 1."
    ICONE = "icones/energetico.png"
    MELHORIAS = ("+10% de dano.",) * 3
    ESCORRE = 0.05                   # fração da vida máxima por segundo

    def aplicar(self, jogador):
        jogador.mult_dano *= 1 + 0.10 * self.nivel

    def atualizar(self, dt, jogador, jogo):
        if jogador.vida > 1 and not jogador.imortal:
            jogador.vida = max(1.0, jogador.vida - jogador.vida_maxima * self.ESCORRE * dt)


class ParcelarNoCartao(Item):
    NOME = "Parcelar no Cartão"
    DESCRICAO = "Cada golpe entra só 30% na hora; o resto vem parcelado em 3 s. A parcela que mataria vence a dívida toda."
    ICONE = "icones/moeda.png"
    MELHORIAS = ("Parcelado em 4 s.", "Parcelado em 5 s.", "Parcelado em 6 s.")
    NA_HORA = 0.30
    PARCELAS = (3.0, 4.0, 5.0, 6.0)  # segundos em que o resto do golpe é cobrado

    def __init__(self):
        super().__init__()
        self.dividas = []            # [quanto falta, quanto cobra por segundo]
        self.cobrando = False        # a dívida venceu e está passando pelos outros itens: não parcela de novo

    def aplicar(self, jogador):
        """Nada fixo: o efeito está nos golpes."""

    def ao_ser_atingido(self, dano, jogador, jogo):
        if dano <= 0 or self.cobrando:
            return dano
        resto = dano * (1 - self.NA_HORA)
        self.dividas.append([resto, resto / self.PARCELAS[self.nivel - 1]])
        return dano * self.NA_HORA

    @property
    def em_aberto(self):
        return sum(divida[0] for divida in self.dividas)

    def atualizar(self, dt, jogador, jogo):
        if jogador.imortal:
            self.dividas = []
            return
        if jogador.invencivel > 0 or not self.dividas:   # invencível não paga: a cobrança espera
            return
        parcelas = [min(divida[0], divida[1] * dt) for divida in self.dividas]
        if jogador.vida - sum(parcelas) <= 0:
            self._vencer(jogador, jogo)
            return
        for divida, parcela in zip(self.dividas, parcelas):
            divida[0] -= parcela
        jogador.vida = jogador.vida - sum(parcelas)
        self.dividas = [d for d in self.dividas if d[0] > 1e-6]

    def _vencer(self, jogador, jogo):
        """A parcela mataria: a dívida inteira vence de uma vez e entra como um golpe, pelos outros itens e
        habilidades (o Atestado Médico e a Armadura de Roteiro decidem se o aluno cai)."""
        divida, self.dividas = self.em_aberto, []
        self.cobrando = True
        try:
            dano = jogador.filtrar_dano(divida, jogo)
        finally:
            self.cobrando = False
        if dano > 0:
            jogador.vida = jogador.vida - dano


class MensalidadeDaAtletica(Item):
    NOME = "Mensalidade da Atlética"
    DESCRICAO = "Custa 3 moedas por segundo; enquanto tiver moedas: +7,5% de dano por nível e -10% de dano recebido."
    ICONE = "icones/atletica.png"
    MELHORIAS = ("+7,5% de dano enquanto paga.",) * 3
    CUSTO = 3                        # moedas por segundo
    PROTECAO = 0.90

    def __init__(self):
        super().__init__()
        self._a_pagar = 0.0

    def aplicar(self, jogador):
        """Nada fixo: o bônus depende de ter moedas."""

    def atualizar(self, dt, jogador, jogo):
        from jogo.jogador.bonus import BonusTemporario
        self._a_pagar += self.CUSTO * dt
        while self._a_pagar >= 1 and jogo.placar.moedas > 0:
            jogo.placar.moedas -= 1
            self._a_pagar -= 1
        if jogo.placar.moedas <= 0:
            self._a_pagar = 0.0
            return
        jogador.adicionar_bonus(BonusTemporario("mensalidade", "dano", 1 + 0.075 * self.nivel, 0.3))

    def ao_ser_atingido(self, dano, jogador, jogo):
        return dano * self.PROTECAO if jogo.placar.moedas > 0 else dano


ITENS = (Energetico, MarmitaDoRU, MochilaPesada, FoneDeOuvido, GarrafaTermica, TenisDeCorrida, OculosDeGrau, Cola,
         ConviteDaAtletica, Pendrive, MoedaDaSorte, JogoDeCintura, KitDePrimeirosSocorros, AtestadoMedico,
         NoiteSemDormir, PreTreinoDuvidoso, ParcelarNoCartao, MensalidadeDaAtletica)
