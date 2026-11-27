"""O herói controlado pelo jogador."""
import math
from abc import ABC, abstractmethod

import pygame

from jogo.config import ESCALA_PIXEL, INVENCIBILIDADE_APOS_DANO
from jogo.nucleo.animacao import Animador
from jogo.nucleo.desenho import desenhar_sprite
from jogo.jogador.rolamento import Rolamento
from jogo.nucleo.recursos import Recursos
from jogo.nucleo.ser_vivo import SerVivo


class Jogador(SerVivo, ABC):
    grupo = "jogador"
    camada = 1

    NOME = "Jogador"
    DESCRICAO = ""
    VIDA = 100
    VELOCIDADE = 200
    IMAGEM = ""
    IMAGEM_TRANSFORMADO = None
    RETRATO = None               # arte principal (alta) da classe, mostrada na matrícula
    ROSTO = None                 # retrato só do rosto: HUD (ao lado da vida) e foto da carteirinha
    PASTA_SPRITE = None          # pasta em assets/sprites/ com as animações (parado, andar)
    PASTA_TRANSFORMADO = None    # animações da forma transformada (Super Saiyajin)
    ALTURA = 64
    RAIO = 22
    MAX_ARMAS = 4                # habilidades ativas; no limite, só melhorias (uma colab libera vaga)
    DURACAO_DA_CARETA = 0.45
    # Custo do nível n: BASE + LINEAR*(n-1) + QUADRATICO*(n-1)². Os primeiros níveis vêm rápido e os
    # últimos custam caro: só com as notas chega-se perto dos níveis 7, 11 e 14 nos três chefes. Quem quer
    # ficar mais forte que isso vai atrás dos mini-chefes do mapa (baú garantido) e das melhorias da loja.
    XP_BASE = 18
    XP_LINEAR = 10
    XP_QUADRATICO = 3.4
    MAX_ITENS = 4                # itens passivos (as habilidades da classe não ocupam vaga)
    ALCANCE_COLETA_BASE = 90
    MULT_CRITICO = 2.0           # quanto o acerto crítico multiplica o dano
    GANHO_VELOCIDADE_POR_NIVEL = 0.01    # o aluno pega ritmo: +1% de velocidade por nível
    TETO_GANHO_VELOCIDADE = 0.30

    def __init__(self, posicao):
        super().__init__(posicao, self.RAIO, self.VIDA)
        self.armas = []
        self.itens = []
        self.bonus = []
        self.armas_em_colab = set()
        self.direcao_mira = pygame.Vector2(1, 0)
        self.direcao_movimento = pygame.Vector2(1, 0)
        self.rolamento = Rolamento()
        self.movendo = False
        self.olhando_esquerda = False
        self.invencivel = 0.0
        self.careta = 0.0             # segundos que ainda mostra o quadro de dano (a careta)
        self.imortal = False          # modo treino
        self.melhorias = []           # melhorias permanentes compradas no Centro Acadêmico
        self.banidos = set()              # classes de arma e item banidas das cartas nesta partida
        self.desbloqueios = frozenset()   # armas e itens comprados que podem aparecer nas cartas
        self.tempo = 0.0
        self.transformado = False
        self.animador = Animador(self._animacoes(), inicial="parado")
        self.nivel = 1
        self.experiencia = 0
        self.habilidades = []                              # as que o aluno já pegou nas cartas
        self.habilidades_da_classe = self.criar_habilidades()   # as três que as cartas podem oferecer
        self.recalcular_atributos()
        self.especial = self.criar_especial()
        self.especial.cargas_maximas = self.cargas_especial
        self.adicionar_arma(self.criar_arma_inicial())

    @abstractmethod
    def criar_arma_inicial(self):
        """Arma com que este herói começa."""

    @abstractmethod
    def criar_habilidades(self):
        """As três habilidades desta classe (uma instância de cada), que as cartas de nível oferecem."""

    @abstractmethod
    def criar_especial(self):
        """Especial (tecla Espaço) deste herói."""

    def _redefinir_atributos(self):
        self.mult_dano = 1.0
        self.mult_velocidade = 1.0 + min(self.TETO_GANHO_VELOCIDADE,
                                         (self.nivel - 1) * self.GANHO_VELOCIDADE_POR_NIVEL)
        self.mult_recarga = 1.0
        self.mult_especial = 1.0
        self.mult_rolamento = 1.0     # fator da recarga do rolamento (menor é mais rápido)
        self.chance_critico = 0.0
        self.chance_desvio = 0.0      # chance de um golpe passar direto (Jogo de Cintura)
        self.sorte = 0.0              # +0.10 = tudo que depende de chance fica 10% mais provável
        self.chance_repeticao = 0.0   # Programador: chance de um disparo repetir na hora
        self.mult_cura = 1.0          # Garrafa Térmica: toda cura rende mais
        self.regeneracao = 0.0
        self.alcance_coleta = self.ALCANCE_COLETA_BASE
        self.vida_maxima_extra = 0
        self.mult_experiencia = 1.0
        self.fator_experiencia = 1.0  # multiplica tudo (Cola); mult_experiencia soma as melhorias
        self.mult_vida_maxima = 1.0
        self.cargas_especial = 1
        self.chance_carona = 0.0       # Cara da Carona: moeda extra de quem morre possuído
        self.mult_moedas = 1.0
        self.capacidade_cafe = 100     # doses da garrafa da Virada de Noite (Cafeinado aumenta)

    def recalcular_atributos(self):
        """Zera os modificadores e deixa cada habilidade, item e melhoria aplicar o seu (polimorfismo)."""
        maxima_antes = self.vida_maxima
        self._redefinir_atributos()
        for reagente in self.reagentes:
            reagente.aplicar(self)
        for melhoria in self.melhorias:
            melhoria.aplicar(self)
        self.vida_maxima = (self.VIDA + self.vida_maxima_extra) * self.mult_vida_maxima
        if getattr(self, "especial", None) is not None:
            self.especial.cargas_maximas = self.cargas_especial
        if self.vida_maxima > maxima_antes:
            super().curar(self.vida_maxima - maxima_antes)   # a vida ganha entra inteira, sem bônus de cura

    def chance(self, base):
        """Chance `base` (0 a 1) já com a sorte do aluno: crítico, desvio, moedas, baús."""
        return max(0.0, base * (1 + self.sorte) * self.multiplicador("sorte"))

    def receber_melhorias(self, melhorias):
        """Começa a partida com as melhorias permanentes da loja."""
        self.melhorias = list(melhorias)
        self.recalcular_atributos()

    def multiplicador(self, atributo):
        resultado = 1.0
        for b in self.bonus:
            if b.atributo == atributo:
                resultado *= b.multiplicador
        return resultado

    @property
    def velocidade(self):
        return self.VELOCIDADE * self.mult_velocidade * self.multiplicador("velocidade")

    @property
    def multiplicador_dano(self):
        return self.mult_dano * self.multiplicador("dano")

    @property
    def multiplicador_recarga(self):
        """Fator aplicado ao tempo de recarga das armas (menor é mais rápido)."""
        return self.mult_recarga * self.multiplicador("recarga")

    def tem_bonus(self, nome):
        return any(b.nome == nome for b in self.bonus)

    def adicionar_bonus(self, bonus):
        self.bonus = [b for b in self.bonus if b.nome != bonus.nome] + [bonus]

    def adicionar_arma(self, arma):
        if len(self.armas) >= self.MAX_ARMAS:
            raise ValueError("o herói já carrega o máximo de armas")
        self.armas.append(arma)

    def remover_arma(self, arma, jogo):
        arma.ao_remover(jogo)
        self.armas.remove(arma)

    def aplicar_colab(self, receita, jogo):
        """Funde as duas armas da receita na colab: ocupam uma vaga só, e a outra fica livre."""
        from jogo.armas.colabs import Colab
        jogo.marcos.add("colab")
        for arma in Colab.ingredientes_em(receita, self.armas):
            self.armas_em_colab.add(type(arma))
            self.remover_arma(arma, jogo)
        self.armas.append(receita())

    @property
    def reagentes(self):
        """Itens e habilidades: os dois reagem à partida pelos mesmos ganchos (ReageAoJogo)."""
        return self.itens + self.habilidades

    def adicionar_habilidade(self, habilidade):
        if habilidade in self.habilidades:
            raise ValueError(f"{habilidade.NOME} já foi pega")
        self.habilidades.append(habilidade)
        self.recalcular_atributos()

    def subir_nivel_habilidade(self, habilidade):
        habilidade.subir_nivel()
        self.recalcular_atributos()

    def avisar_acerto(self, inimigo, jogo):
        for reagente in self.reagentes:
            reagente.ao_acertar(inimigo, self, jogo)

    def avisar_critico(self, inimigo, jogo):
        for reagente in self.reagentes:
            reagente.ao_critico(inimigo, self, jogo)

    def avisar_eliminacao(self, inimigo, jogo):
        for reagente in self.reagentes:
            reagente.ao_eliminar(inimigo, self, jogo)

    def filtrar_dano(self, dano, jogo):
        """O dano de um golpe depois de cada item e habilidade dizer o seu (0: o golpe não entrou)."""
        for reagente in self.reagentes:
            dano = reagente.ao_ser_atingido(dano, self, jogo)
        return dano

    def ao_subir_de_nivel(self, jogo):
        """Subiu um nível na partida. Classes com algo que muda com o nível (os períodos do Calouro) sobrescrevem."""
        for reagente in list(self.reagentes):
            reagente.ao_subir_de_nivel(self, jogo)

    def ao_pegar_cafe(self, jogo):
        """Pegou um copo de café: quem decide o que ele faz é o especial."""
        self.especial.ao_pegar_cafe(self, jogo)

    def adicionar_item(self, item):
        if len(self.itens) >= self.MAX_ITENS:
            raise ValueError("o herói já carrega o máximo de itens")
        self.itens.append(item)
        self.recalcular_atributos()

    def banir(self, classe):
        """Tira uma arma ou item das cartas pelo resto da partida."""
        self.banidos.add(classe)

    def subir_nivel_item(self, item):
        item.subir_nivel()
        self.recalcular_atributos()

    def curar(self, quantidade):
        """Recupera vida, já com o que faz a cura render mais (Garrafa Térmica, CON da Ficha de Personagem)."""
        super().curar(quantidade * self.mult_cura * self.multiplicador("cura"))

    @property
    def experiencia_necessaria(self):
        """Cada nível custa bem mais que o anterior: sem as melhorias da loja não dá para levar tudo ao
        máximo (são 27 escolhas), então o jogador precisa decidir em que armas apostar."""
        return self.experiencia_do_nivel(self.nivel)

    @classmethod
    def experiencia_do_nivel(cls, nivel):
        """Quanto custa passar do `nivel` para o seguinte."""
        n = nivel - 1
        return round(cls.XP_BASE + cls.XP_LINEAR * n + cls.XP_QUADRATICO * n * n)

    def experiencia_para_subir(self, niveis):
        """Quanto falta para subir `niveis` níveis a partir de agora (aceita fração: 2,5 = dois níveis e meio)."""
        falta = self.experiencia_necessaria - self.experiencia
        inteiros, fracao = int(niveis), niveis - int(niveis)
        for i in range(1, inteiros):
            falta += self.experiencia_do_nivel(self.nivel + i)
        return falta + fracao * self.experiencia_do_nivel(self.nivel + inteiros)

    def ganhar_experiencia(self, quantidade):
        """Soma experiência e retorna quantos níveis o herói subiu."""
        if quantidade < 0:
            raise ValueError("experiência não pode ser negativa")
        self.experiencia += quantidade
        ganhos = 0
        while self.experiencia >= self.experiencia_necessaria:
            self.experiencia -= self.experiencia_necessaria
            self.nivel += 1
            ganhos += 1
        if ganhos:
            self.recalcular_atributos()     # há habilidades que crescem com o nível do aluno (Cafeinado)
        return ganhos

    @property
    def pode_levar_dano(self):
        return self.invencivel <= 0 and not self.rolamento.protegido and self.esta_vivo and not self.imortal

    def rolar(self, jogo=None):
        """Esquiva (Shift ou botão direito): rola na direção do movimento, invencível enquanto dura."""
        if not self.esta_vivo or not self.rolamento.iniciar(self.direcao_movimento):
            return False
        Recursos.tocar("rolar", 0.35)
        if jogo is not None:
            for reagente in self.reagentes:
                reagente.ao_rolar(self, jogo)
        return True

    def receber_dano(self, quantidade):
        morreu = super().receber_dano(quantidade)
        self.invencivel = max(self.invencivel, INVENCIBILIDADE_APOS_DANO)
        self.careta = self.DURACAO_DA_CARETA
        return morreu

    @classmethod
    def rosto(cls, lado):
        """O retrato do rosto num quadrado de `lado` pixels, ou None se a classe não tem essa arte."""
        if not cls.ROSTO or not (Recursos.pasta / cls.ROSTO).is_file():
            return None
        return Recursos.na_altura(Recursos.imagem(cls.ROSTO), lado)

    @classmethod
    def foto(cls, largura):
        """A foto 3x4 da carteirinha, na largura pedida; sem essa arte, o rosto do HUD (ou None)."""
        caminho = cls.ROSTO.replace("rostos/", "fotos/") if cls.ROSTO else None
        if not caminho or not (Recursos.pasta / caminho).is_file():
            return cls.rosto(largura)
        imagem = Recursos.imagem(caminho)
        return Recursos.na_altura(imagem, round(largura * imagem.get_height() / imagem.get_width()))

    def _animacoes(self):
        """As tiras do boneco (ou do boneco transformado), como estão na arte: a aparência de cada classe é fixa."""
        if self.transformado:
            return Recursos.animacoes_ou_imagem(self.PASTA_TRANSFORMADO, self.IMAGEM_TRANSFORMADO, self.ALTURA)
        return Recursos.animacoes_ou_imagem(self.PASTA_SPRITE, self.IMAGEM, self.ALTURA)

    @property
    def animado(self):
        return len(self.animador.animacoes) > 1

    def _atualizar_animacao(self, dt):
        transformado = bool(self.PASTA_TRANSFORMADO or self.IMAGEM_TRANSFORMADO) and self.tem_bonus("ssj")
        if transformado != self.transformado:
            self.transformado = transformado
            self.animador.trocar_conjunto(self._animacoes())
        if self.careta > 0 and "dano" in self.animador.animacoes:
            self.animador.tocar("dano")          # levou dano: faz careta por um instante
        else:
            self.animador.tocar("andar" if self.movendo else "parado")
        self.animador.atualizar(dt)

    def usar_especial(self, jogo):
        return self.especial.usar(self, jogo)

    def atualizar(self, dt, jogo):
        self.tempo += dt
        self.piscar = max(0.0, self.piscar - dt)
        self.invencivel = max(0.0, self.invencivel - dt)
        self.careta = max(0.0, self.careta - dt)
        direcao = pygame.Vector2(jogo.entrada.direcao)
        self.movendo = direcao.length_squared() > 0
        if self.rolamento.rolando:
            self.posicao += self.rolamento.direcao * self.velocidade * self.rolamento.fator_velocidade * dt
        elif self.movendo:
            direcao.normalize_ip()
            # mato alto e plantação seguram o passo (o rolamento passa por cima: é o jeito de sair rápido)
            self.posicao += direcao * self.velocidade * jogo.passo_do_chao(self.posicao) * dt
            self.direcao_mira = pygame.Vector2(direcao)
            self.direcao_movimento = pygame.Vector2(direcao)
            if abs(direcao.x) > 0.01:
                self.olhando_esquerda = direcao.x < 0
        self.rolamento.atualizar(dt, self.mult_rolamento)
        self.posicao = jogo.resolver_obstaculos(self.posicao, self.raio)
        arena = jogo.arena
        self.posicao.x = max(arena.left + self.raio, min(self.posicao.x, arena.right - self.raio))
        self.posicao.y = max(arena.top + self.raio, min(self.posicao.y, arena.bottom - self.raio))
        if jogo.entrada.mira is not None:
            mira = pygame.Vector2(jogo.entrada.mira) - self.posicao
            if mira.length_squared() > 1:
                self.direcao_mira = mira.normalize()
                self.olhando_esquerda = mira.x < 0
        if self.regeneracao:
            self.curar(self.regeneracao * dt)
        for b in self.bonus:
            b.atualizar(dt)
        self.bonus = [b for b in self.bonus if b.ativo]
        self._atualizar_animacao(dt)
        self.especial.atualizar(dt, self.mult_recarga * self.mult_especial)
        self.especial.agir(dt, self, jogo)
        for arma in list(self.armas):
            arma.atualizar(dt, jogo, self)
        for reagente in list(self.reagentes):
            reagente.atualizar(dt, self, jogo)

    def desenhar(self, tela, camera):
        imagem = self.animador.quadro_atual
        if self.animado:
            pulo = 0
        else:
            pulo = abs(math.sin(self.tempo * 10)) * 4 if self.movendo else (1 + math.sin(self.tempo * 2)) * 0.8
        alfa = 130 if self.invencivel > 0 and int(self.invencivel * 20) % 2 else 255
        angulo = 0.0
        if self.rolamento.rolando:     # uma cambalhota inteira durante o rolamento
            angulo = 360 * self.rolamento.fracao * (1 if self.olhando_esquerda else -1)
            alfa = 200
        desenhar_sprite(tela, camera, imagem, self.posicao, espelhar=self.olhando_esquerda,
                        piscar=self.piscar > 0, deslocamento_y=pulo, alfa=alfa, angulo=angulo)
