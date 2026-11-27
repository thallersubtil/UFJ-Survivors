"""As 21 habilidades das classes (3 por classe). Aparecem nas cartas de nível e têm 3 níveis.

Números de partida: o balanceamento (marco M5 do plano do semestre) ajusta. Cada uma tem o próprio ícone em
assets/icones/ (gerado em 27/11/2026 e aprovado pelo Thaller).
"""

from jogo.config import Cor
from jogo.efeitos import OndaDoGrito, TextoFlutuante
from jogo.jogador.bonus import BonusTemporario
from jogo.jogador.habilidade import Habilidade
from jogo.nucleo.recursos import Recursos


def passageiros(jogo):
    """Inimigos possuídos agora (lutam do lado do aluno)."""
    return sum(1 for inimigo in jogo.inimigos if inimigo.possuido > 0)


def avisar(jogo, jogador, texto, cor=Cor.DESTAQUE, tamanho=20):
    jogo.adicionar(TextoFlutuante(texto, jogador.posicao - (0, 70), cor, tamanho, duracao=1.2))


class HabilidadeComRelogio(Habilidade):
    """Habilidade que confere a partida de tempos em tempos (contar ajudantes, inimigos perto...), em vez de a
    cada quadro. Quem herda implementa `conferir`."""

    INTERVALO_DE_CONFERENCIA = 0.4

    def __init__(self):
        super().__init__()
        self._relogio = 0.0

    def atualizar(self, dt, jogador, jogo):
        self._relogio -= dt
        if self._relogio <= 0:
            self._relogio = self.INTERVALO_DE_CONFERENCIA
            self.conferir(jogador, jogo)

    def conferir(self, jogador, jogo):
        """O que a habilidade confere a cada INTERVALO_DE_CONFERENCIA segundos."""


# ---------------------------------------------------------------- Otaku

class InstintoOtaku(Habilidade):
    NOME = "Instinto Otaku"
    ICONE = "icones/instinto_otaku.png"
    CHANCE = (0.08, 0.16, 0.25)
    DESCRICAO = "8% de chance de acerto crítico (dano em dobro)."
    MELHORIAS = ("16% de chance de crítico.", "25% de chance de crítico.")

    def aplicar(self, jogador):
        jogador.chance_critico += self.valor(self.CHANCE)


class ArmaduraDeRoteiro(Habilidade):
    """O protagonista não morre no meio do episódio."""
    NOME = "Armadura de Roteiro"
    ICONE = "icones/armadura_de_roteiro.png"
    INVENCIVEL = (2.0, 3.0, 4.0)
    RECARGA = (90.0, 75.0, 60.0)
    DESCRICAO = "O golpe que te derrubaria deixa 1 de vida e 2 s de invencibilidade. Volta em 90 s."
    MELHORIAS = ("3 s invencível; volta em 75 s.", "4 s invencível; volta em 60 s.")

    def __init__(self):
        super().__init__()
        self.espera = 0.0

    def aplicar(self, jogador):
        """Nada fixo: o efeito está em `ao_ser_atingido`."""

    def atualizar(self, dt, jogador, jogo):
        self.espera = max(0.0, self.espera - dt)

    def ao_ser_atingido(self, dano, jogador, jogo):
        if self.espera > 0 or dano < jogador.vida:
            return dano
        self.espera = self.valor(self.RECARGA)
        jogador.invencivel = max(jogador.invencivel, self.valor(self.INVENCIVEL))
        avisar(jogo, jogador, "ARMADURA DE ROTEIRO!")
        return max(0.0, jogador.vida - 1)


class PoderDaAmizade(HabilidadeComRelogio):
    NOME = "Poder da Amizade"
    ICONE = "icones/poder_da_amizade.png"
    POR_AMIGO = (0.05, 0.07, 0.10)
    MAXIMO = 0.50
    DESCRICAO = "+5% de dano por amigo em campo (Caramelo, Fusca, mascotes, possuídos), até +50%."
    MELHORIAS = ("+7% de dano por amigo.", "+10% de dano por amigo.")

    def aplicar(self, jogador):
        """Nada fixo: o bônus é conferido em campo."""

    def conferir(self, jogador, jogo):
        amigos = sum(ajudante.AMIGO for ajudante in jogo.grupos["ajudante"]) + passageiros(jogo)
        bonus = min(self.MAXIMO, amigos * self.valor(self.POR_AMIGO))
        if bonus > 0:
            jogador.adicionar_bonus(BonusTemporario("amizade", "dano", 1 + bonus, self.INTERVALO_DE_CONFERENCIA + 0.2))


# ---------------------------------------------------------------- Programador

class LacoDeRepeticao(Habilidade):
    NOME = "Laço de Repetição"
    ICONE = "icones/laco_de_repeticao.png"
    CHANCE = (0.10, 0.18, 0.28)
    DESCRICAO = "Cada disparo tem 10% de chance de repetir na hora."
    MELHORIAS = ("18% de chance de repetir.", "28% de chance de repetir.")

    def aplicar(self, jogador):
        jogador.chance_repeticao += self.valor(self.CHANCE)


class Cafeinado(Habilidade):
    NOME = "Cafeinado"
    ICONE = "icones/cafeinado.png"
    DOSES = (20, 40, 60)
    RECARGA_POR_NIVEL = 0.016        # por nível do aluno
    RECARGA_MAXIMA = 0.40
    DESCRICAO = "Armas recarregam 1,6% mais rápido por nível do aluno; a garrafa da Virada leva +20 doses."
    MELHORIAS = ("A garrafa leva +40 doses.", "A garrafa leva +60 doses.")

    def aplicar(self, jogador):
        jogador.mult_recarga *= 1 - min(self.RECARGA_MAXIMA, self.RECARGA_POR_NIVEL * (jogador.nivel - 1))
        jogador.capacidade_cafe += self.valor(self.DOSES)


class Compilar(Habilidade):
    """Gimmick do Programador: escreve código andando e, parado, compila tudo de uma vez."""
    NOME = "Compilar"
    ICONE = "icones/compilar.png"
    LINHAS_POR_SEGUNDO = 10
    MAXIMO_DE_LINHAS = 200
    MINIMO_PARA_COMPILAR = 10
    PARADO = 1.0                     # segundos parado até compilar
    RAIO = 260
    FORCA = (1.0, 1.5, 2.0)
    DESCRICAO = "Andando, acumula linhas de código; parado 1 s, compila: um pulso com o dano acumulado."
    MELHORIAS = ("O pulso dá 1,5x o acumulado.", "O pulso dá 2x o acumulado.")

    def __init__(self):
        super().__init__()
        self.linhas = 0.0
        self._parado = 0.0

    def aplicar(self, jogador):
        """Nada fixo: o efeito vem de andar e parar."""

    def atualizar(self, dt, jogador, jogo):
        if jogador.movendo:
            self.linhas = min(self.MAXIMO_DE_LINHAS, self.linhas + self.LINHAS_POR_SEGUNDO * dt)
            self._parado = 0.0
            return
        self._parado += dt
        if self._parado >= self.PARADO and self.linhas >= self.MINIMO_PARA_COMPILAR:
            self.compilar(jogador, jogo)

    def compilar(self, jogador, jogo):
        dano = self.linhas * self.valor(self.FORCA) * jogador.multiplicador_dano
        for inimigo in jogo.inimigos_proximos(jogador.posicao, self.RAIO):
            jogo.causar_dano(inimigo, dano, inimigo.posicao - jogador.posicao, forte=True)
        jogo.adicionar(OndaDoGrito(jogador, self.RAIO))
        avisar(jogo, jogador, "COMPILOU!", (120, 230, 120))
        self.linhas = 0.0

    @property
    def contador(self):
        return f"LINHAS {int(self.linhas)}"


# ---------------------------------------------------------------- Mestre de RPG

class RolagemDeIniciativa(Habilidade):
    NOME = "Rolagem de Iniciativa"
    ICONE = "icones/rolagem_de_iniciativa.png"
    RECARGA = (0.15, 0.30, 0.45)
    DESCRICAO = "O especial recarrega 15% mais rápido."
    MELHORIAS = ("30% mais rápido.", "45% mais rápido.")

    def aplicar(self, jogador):
        jogador.mult_especial *= 1 - self.valor(self.RECARGA)


class FichaDePersonagem(Habilidade):
    NOME = "Ficha de Personagem"
    ICONE = "icones/ficha_de_personagem.png"
    INTERVALO = 15.0
    BONUS = (0.30, 0.40, 0.50)
    ATRIBUTOS = (("FOR", "dano"), ("DES", "velocidade"), ("CON", "cura"), ("INT", "recarga"), ("SAB", "coleta"),
                 ("CAR", "sorte"))
    DESCRICAO = "A cada 15 s, +30% num atributo sorteado por 15 s (FOR, DES, CON, INT, SAB ou CAR)."
    MELHORIAS = ("+40% no atributo sorteado.", "+50% no atributo sorteado.")

    def __init__(self):
        super().__init__()
        self._espera = 0.0
        self.atributo = None             # sigla do atributo que está valendo agora

    def aplicar(self, jogador):
        """Nada fixo: o atributo é sorteado em campo."""

    def atualizar(self, dt, jogador, jogo):
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.INTERVALO
        sigla, atributo = jogo.rng.choice(self.ATRIBUTOS)
        bonus = self.valor(self.BONUS)
        multiplicador = 1 / (1 + bonus) if atributo == "recarga" else 1 + bonus     # recarga: menor é melhor
        jogador.adicionar_bonus(BonusTemporario("ficha", atributo, multiplicador, self.INTERVALO))
        self.atributo = sigla
        avisar(jogo, jogador, f"{sigla} +{round(bonus * 100)}%!")


class TesteDeResistencia(Habilidade):
    __test__ = False             # o nome começa com "Teste", mas não é um teste do pytest
    NOME = "Teste de Resistência"
    ICONE = "icones/teste_de_resistencia.png"
    DIFICULDADE = (18, 16, 14)       # tirando isto ou mais no d20, o golpe não entra
    DESCRICAO = "Ao levar um golpe, rola um d20: com 18 ou mais, o golpe não entra."
    MELHORIAS = ("Salva com 16 ou mais.", "Salva com 14 ou mais.")

    def aplicar(self, jogador):
        """Nada fixo: o efeito está em `ao_ser_atingido`."""

    def ao_ser_atingido(self, dano, jogador, jogo):
        dado = jogo.rng.randint(1, 20)
        if dado < self.valor(self.DIFICULDADE):
            return dano
        avisar(jogo, jogador, f"SALVOU! ({dado})", Cor.CURA, 18)
        return 0


# ---------------------------------------------------------------- Monitor

class PlantaoDeDuvidas(Habilidade):
    NOME = "Plantão de Dúvidas"
    ICONE = "icones/plantao_de_duvidas.png"
    REGENERACAO = (0.4, 0.8, 1.2)    # vida por segundo
    COLETA = (1.2, 1.4, 1.6)
    DESCRICAO = "Recupera 0,4 de vida por segundo e puxa as notas 20% mais de longe."
    MELHORIAS = ("0,8 de vida por segundo; notas 40% mais de longe.", "1,2 por segundo; notas 60% mais de longe.")

    def aplicar(self, jogador):
        jogador.regeneracao += self.valor(self.REGENERACAO)
        jogador.alcance_coleta *= self.valor(self.COLETA)


class CanetaVermelha(Habilidade):
    NOME = "Caneta Vermelha"
    ICONE = "icones/caneta_vermelha.png"
    CHANCE = (0.10, 0.15, 0.20)
    DANO_EXTRA = (0.25, 0.33, 0.50)
    DURACAO_DA_MARCA = 5.0
    CHANCE_DE_CURA = 0.30            # quem morre marcado pode curar o aluno
    CURA = 0.02                      # fração da vida máxima
    DESCRICAO = "10% de chance de marcar o inimigo com um X: ele leva 25% a mais de dano e pode curar ao morrer."
    MELHORIAS = ("15% de chance; o marcado leva 33% a mais.", "20% de chance; o marcado leva 50% a mais.")

    def aplicar(self, jogador):
        """Nada fixo: a marca sai nos acertos."""

    def ao_acertar(self, inimigo, jogador, jogo):
        if not inimigo.marcado and jogo.rng.random() < jogador.chance(self.valor(self.CHANCE)):
            inimigo.marcar_com_x(self.DURACAO_DA_MARCA, self.valor(self.DANO_EXTRA))

    def ao_eliminar(self, inimigo, jogador, jogo):
        if inimigo.marcado and jogo.rng.random() < jogador.chance(self.CHANCE_DE_CURA):
            jogador.curar(jogador.vida_maxima * self.CURA)


class HorarioDeAtendimento(Habilidade):
    """Gimmick do Monitor: parado, abre o horário de atendimento."""
    NOME = "Horário de Atendimento"
    ICONE = "icones/horario_de_atendimento.png"
    PARADO = 1.0
    RAIO = 230
    LENTIDAO = (0.20, 0.30, 0.40)
    CURA = (0.02, 0.03, 0.04)        # fração da vida máxima a cada INTERVALO_DE_CURA
    INTERVALO_DE_CURA = 2.0
    DESCRICAO = "Parado por 1 s: os inimigos em volta ficam 20% mais lentos e você cura 2% da vida a cada 2 s."
    MELHORIAS = ("30% mais lentos; cura 3%.", "40% mais lentos; cura 4%.")

    def __init__(self):
        super().__init__()
        self._parado = 0.0
        self._cura = 0.0

    def aplicar(self, jogador):
        """Nada fixo: o efeito vem de ficar parado."""

    @property
    def atendendo(self):
        return self._parado >= self.PARADO

    def atualizar(self, dt, jogador, jogo):
        if jogador.movendo:
            self._parado = self._cura = 0.0
            return
        antes = self.atendendo
        self._parado += dt
        if not self.atendendo:
            return
        if not antes:
            jogo.adicionar(OndaDoGrito(jogador, self.RAIO))
        for inimigo in jogo.inimigos_proximos(jogador.posicao, self.RAIO):
            inimigo.atrasar(0.3, 1 - self.valor(self.LENTIDAO))
        self._cura += dt
        if self._cura >= self.INTERVALO_DE_CURA:
            self._cura -= self.INTERVALO_DE_CURA
            jogador.curar(jogador.vida_maxima * self.valor(self.CURA))


# ---------------------------------------------------------------- Gamer

class Reflexo(Habilidade):
    NOME = "Reflexo"
    ICONE = "icones/reflexo.png"
    RECARGA = (0.15, 0.30, 0.45)
    DESCRICAO = "O rolamento recarrega 15% mais rápido."
    MELHORIAS = ("30% mais rápido.", "45% mais rápido.")

    def aplicar(self, jogador):
        jogador.mult_rolamento *= 1 - self.valor(self.RECARGA)


class FramePerfect(Habilidade):
    """Gimmick do Gamer: rolar no último instante."""
    NOME = "Frame Perfect"
    ICONE = "icones/frame_perfect.png"
    PERIGO = 90                      # px: um golpe a esta distância está "chegando"
    CAMERA_LENTA = 1.0
    DANO = (0.30, 0.45, 0.60)
    DURACAO = 8.0
    DESCRICAO = "Rolar no último instante antes de um golpe: câmera lenta por 1 s e +30% de dano por 8 s."
    MELHORIAS = ("+45% de dano.", "+60% de dano.")

    def aplicar(self, jogador):
        """Nada fixo: o efeito está em `ao_rolar`."""

    def ao_rolar(self, jogador, jogo):
        if not self._golpe_chegando(jogador, jogo):
            return
        jogo.camera_lenta(self.CAMERA_LENTA)
        jogador.adicionar_bonus(BonusTemporario("frame_perfect", "dano", 1 + self.valor(self.DANO), self.DURACAO))
        avisar(jogo, jogador, "FRAME PERFECT!", (120, 200, 255), 22)

    def _golpe_chegando(self, jogador, jogo):
        if any(p.posicao.distance_to(jogador.posicao) <= self.PERIGO for p in jogo.grupos["projetil_inimigo"]):
            return True
        return any(i.posicao.distance_to(jogador.posicao) <= i.raio + jogador.raio + self.PERIGO / 2
                   for i in jogo.inimigos_proximos(jogador.posicao, self.PERIGO))


class Combo(Habilidade):
    NOME = "Combo"
    ICONE = "icones/combo.png"
    ACERTOS = 50
    BONUS = (0.20, 0.30, 0.40)
    DURACAO = 10.0
    DESCRICAO = "50 acertos sem levar dano: +20% de velocidade e 20% de chance de golpe duplo por 10 s."
    MELHORIAS = ("+30% de velocidade e de golpe duplo.", "+40% de velocidade e de golpe duplo.")

    def __init__(self):
        super().__init__()
        self.acertos = 0

    def aplicar(self, jogador):
        """Nada fixo: o efeito vem dos acertos seguidos."""

    def ao_acertar(self, inimigo, jogador, jogo):
        self.acertos += 1
        if self.acertos < self.ACERTOS:
            return
        self.acertos = 0
        bonus = self.valor(self.BONUS)
        jogador.adicionar_bonus(BonusTemporario("combo", "velocidade", 1 + bonus, self.DURACAO))
        jogador.adicionar_bonus(BonusTemporario("golpe_duplo", "golpe_duplo", 1 + bonus, self.DURACAO))
        avisar(jogo, jogador, "COMBO!", (255, 120, 200), 22)

    def ao_ser_atingido(self, dano, jogador, jogo):
        if dano > 0:
            self.acertos = 0
        return dano

    @property
    def contador(self):
        return f"COMBO {self.acertos}/{self.ACERTOS}"


# ---------------------------------------------------------------- Calouro

class SedeDeAprender(Habilidade):
    NOME = "Sede de Aprender"
    ICONE = "icones/sede_de_aprender.png"
    EXPERIENCIA = (0.15, 0.30, 0.45)
    DESCRICAO = "+15% de experiência."
    MELHORIAS = ("+30% de experiência.", "+45% de experiência.")

    def aplicar(self, jogador):
        jogador.mult_experiencia += self.valor(self.EXPERIENCIA)


class VeteranoCamarada(Habilidade):
    NOME = "Veterano Camarada"
    ICONE = "icones/veterano_camarada.png"
    FORCA = (0.50, 0.75, 1.00)
    DESCRICAO = "Um veterano anda com você e usa a sua arma inicial com 50% da força."
    MELHORIAS = ("O veterano bate com 75% da força.", "O veterano bate com 100% da força.")

    def __init__(self):
        super().__init__()
        self.veterano = None

    def aplicar(self, jogador):
        """Nada fixo: o veterano entra em campo."""

    def atualizar(self, dt, jogador, jogo):
        from jogo.ajudantes.ajudantes import Veterano
        if self.veterano is None or not self.veterano.ativo:
            self.veterano = Veterano(jogador, jogador.criar_arma_inicial())
            jogo.adicionar(self.veterano)
        self.veterano.forca = self.valor(self.FORCA)


class PerdidoNoCampus(HabilidadeComRelogio):
    NOME = "Perdido no Campus"
    ICONE = "icones/perdido_no_campus.png"
    RAIO = 260
    POR_INIMIGO = (0.03, 0.04, 0.05)
    MAXIMO = 0.80
    EXPERIENCIA_EXTRA = (0.25, 0.35, 0.50)
    DESCRICAO = "+3% de velocidade por inimigo perto (até +80%) e +25% de experiência de quem morre perto."
    MELHORIAS = ("+4% por inimigo; +35% de experiência.", "+5% por inimigo; +50% de experiência.")

    def aplicar(self, jogador):
        """Nada fixo: o bônus depende de quem está perto."""

    def conferir(self, jogador, jogo):
        perto = len(jogo.inimigos_proximos(jogador.posicao, self.RAIO))
        bonus = min(self.MAXIMO, perto * self.valor(self.POR_INIMIGO))
        if bonus > 0:
            jogador.adicionar_bonus(BonusTemporario("perdido", "velocidade", 1 + bonus,
                                                    self.INTERVALO_DE_CONFERENCIA + 0.2))

    def ao_eliminar(self, inimigo, jogador, jogo):
        if inimigo.posicao.distance_to(jogador.posicao) <= self.RAIO:
            jogo.dar_experiencia(inimigo.valor_em_experiencia * self.valor(self.EXPERIENCIA_EXTRA))


# ---------------------------------------------------------------- Cara da Carona

class CaronaSolidaria(Habilidade):
    NOME = "Carona Solidária"
    ICONE = "icones/carona_solidaria.png"
    CHANCE = (0.12, 0.24, 0.36)
    DESCRICAO = "Inimigo que morre possuído (atropelado) tem 12% de chance de deixar uma moeda."
    MELHORIAS = ("24% de chance de moeda.", "36% de chance de moeda.")

    def aplicar(self, jogador):
        jogador.chance_carona += self.valor(self.CHANCE)


class Buzina(Habilidade):
    NOME = "Buzina"
    ICONE = "icones/buzina.png"
    INTERVALO = 10.0
    RAIO = 260
    DANO_BASE = 20
    FORCA = (1.0, 1.5, 2.0)
    ATORDOAMENTO = 0.6
    DESCRICAO = "A cada 10 s, uma buzinada em volta: dano (mais forte no centro) e atordoa por um instante."
    MELHORIAS = ("Buzinada 50% mais forte.", "Buzinada com o dobro de dano.")

    def __init__(self):
        super().__init__()
        self._espera = self.INTERVALO

    def aplicar(self, jogador):
        """Nada fixo: a buzina toca de tempos em tempos."""

    def atualizar(self, dt, jogador, jogo):
        self._espera -= dt
        if self._espera > 0:
            return
        self._espera = self.INTERVALO
        base = self.DANO_BASE * self.valor(self.FORCA) * jogador.multiplicador_dano
        for inimigo in jogo.inimigos_proximos(jogador.posicao, self.RAIO):
            perto = 1 - min(1.0, inimigo.posicao.distance_to(jogador.posicao) / self.RAIO)
            jogo.causar_dano(inimigo, base * (1 + perto), inimigo.posicao - jogador.posicao)
            inimigo.travar(self.ATORDOAMENTO)
        jogo.adicionar(OndaDoGrito(jogador, self.RAIO))
        Recursos.tocar("buzina", 0.4)


class CarroLotado(HabilidadeComRelogio):
    """Gimmick do Cara da Carona: quanto mais gente no carro, mais forte."""
    NOME = "Carro Lotado"
    ICONE = "icones/carro_lotado.png"
    POR_PASSAGEIRO = (0.03, 0.04, 0.05)
    MAXIMO = 0.60
    DESCRICAO = "+3% de dano por passageiro (inimigo possuído) em campo, até +60%."
    MELHORIAS = ("+4% por passageiro.", "+5% por passageiro.")

    def aplicar(self, jogador):
        """Nada fixo: o bônus é conferido em campo."""

    def conferir(self, jogador, jogo):
        bonus = min(self.MAXIMO, passageiros(jogo) * self.valor(self.POR_PASSAGEIRO))
        if bonus > 0:
            jogador.adicionar_bonus(BonusTemporario("lotado", "dano", 1 + bonus, self.INTERVALO_DE_CONFERENCIA + 0.2))


HABILIDADES = (InstintoOtaku, ArmaduraDeRoteiro, PoderDaAmizade, LacoDeRepeticao, Cafeinado, Compilar,
               RolagemDeIniciativa, FichaDePersonagem, TesteDeResistencia, PlantaoDeDuvidas, CanetaVermelha,
               HorarioDeAtendimento, Reflexo, FramePerfect, Combo, SedeDeAprender, VeteranoCamarada, PerdidoNoCampus,
               CaronaSolidaria, Buzina, CarroLotado)
