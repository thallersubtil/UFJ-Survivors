"""Habilidades das classes (3 por classe, nas cartas, 3 níveis) e os especiais novos."""
import random

import pygame
import pytest

from jogo.ajudantes.ajudantes import Veterano
from jogo.coletaveis.coletaveis import Nota
from jogo.inimigos.bug import Bug
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.jogador.classes import CLASSES, Calouro, CaraDaCarona, Gamer, MestreDeRPG, Monitor, Otaku, Programador
from jogo.jogador.especiais import ZonaDeRevisao
from jogo.jogador.habilidade import Habilidade
from jogo.jogador.habilidades import HABILIDADES
from jogo.progressao import Progressao


def pegar(jogo, indice, nivel=1):
    """O aluno pega a habilidade `indice` da classe dele, no `nivel`."""
    heroi = jogo.jogador
    habilidade = heroi.habilidades_da_classe[indice]
    heroi.adicionar_habilidade(habilidade)
    while habilidade.nivel < nivel:
        heroi.subir_nivel_habilidade(habilidade)
    return habilidade


def colocar(jogo, deslocamento, nome="bug", escala=1.0):
    inimigo = FabricaDeInimigos.criar(nome, jogo.jogador.posicao + pygame.Vector2(deslocamento), escala)
    jogo.adicionar(inimigo)
    jogo._incorporar_novas()
    jogo.grade.reconstruir(jogo.inimigos)
    return inimigo


def rodar(jogo, segundos, dt=1 / 30):
    for _ in range(round(segundos / dt)):
        jogo.atualizar(dt)


# ---------------------------------------------------------------- base e cartas

def test_habilidade_tem_nivel_validado_de_1_a_3():
    habilidade = HABILIDADES[0]()
    with pytest.raises(TypeError):
        habilidade.nivel = 2.0
    with pytest.raises(ValueError):
        habilidade.nivel = 4
    habilidade.subir_nivel()
    habilidade.subir_nivel()
    assert habilidade.no_maximo and habilidade.descricao_proxima() == ""
    assert all(issubclass(h, Habilidade) for h in HABILIDADES) and len(HABILIDADES) == 21


def test_as_21_sao_tres_por_classe_sem_repetir():
    vistas = [type(h) for classe in CLASSES for h in classe((0, 0)).habilidades_da_classe]
    assert len(vistas) == 21 and set(vistas) == set(HABILIDADES)


def test_carta_de_habilidade_nova_e_depois_de_nivel(jogo_limpo):
    jogo = jogo_limpo(Otaku)
    heroi = jogo.jogador
    novas = [o for o in Progressao.candidatas(heroi) if o.rotulo == "HABILIDADE"]
    assert {o.titulo for o in novas} == {h.NOME for h in heroi.habilidades_da_classe}
    novas[0].aplicar(heroi, jogo)
    assert len(heroi.habilidades) == 1
    melhorias = [o for o in Progressao.candidatas(heroi) if o.origem is type(heroi.habilidades[0])]
    assert len(melhorias) == 1 and melhorias[0].rotulo == "nível 2"
    melhorias[0].aplicar(heroi, jogo)
    assert heroi.habilidades[0].nivel == 2


def test_sorteio_de_cartas_ate_o_fim_com_todas_as_classes(jogo_limpo):
    for classe in CLASSES:
        jogo = jogo_limpo(classe)
        for _ in range(40):
            Progressao.gerar_opcoes(jogo.jogador, random.Random(1))[0].aplicar(jogo.jogador, jogo)
        rodar(jogo, 2)
        assert len(jogo.jogador.habilidades) <= 3


# ---------------------------------------------------------------- Otaku

def test_armadura_de_roteiro_segura_o_golpe_fatal_uma_vez(jogo_limpo):
    jogo = jogo_limpo(Otaku)
    armadura = pegar(jogo, 1)
    heroi = jogo.jogador
    assert jogo.ferir_jogador(heroi.vida * 10) is True
    assert heroi.vida == 1 and heroi.invencivel >= armadura.INVENCIVEL[0]
    heroi.invencivel = 0
    jogo.ferir_jogador(heroi.vida * 10)
    assert not heroi.esta_vivo                     # ainda na recarga: o segundo golpe derruba


def test_poder_da_amizade_soma_dano_por_amigo(jogo_limpo):
    jogo = jogo_limpo(Otaku)                       # o Caramelo é um ajudante em campo
    pegar(jogo, 2)
    rodar(jogo, 1)
    amigos = len(jogo.grupos["ajudante"])
    assert amigos >= 1
    assert jogo.jogador.multiplicador("dano") == pytest.approx(1 + 0.05 * amigos)


def test_super_saiyajin_sobe_de_nivel_a_cada_uso(jogo_limpo):
    jogo = jogo_limpo(Otaku)
    heroi, ssj = jogo.jogador, jogo.jogador.especial
    danos = []
    for _ in range(4):
        ssj.cargas = 1
        heroi.usar_especial(jogo)
        danos.append(heroi.multiplicador("dano"))
    assert danos == [2.0, 2.5, 3.0, 3.0] and ssj.nivel == 3


# ---------------------------------------------------------------- Programador

def test_compilar_acumula_andando_e_solta_o_pulso_parado(jogo_limpo):
    jogo = jogo_limpo(Programador)
    jogo.jogador.armas = []
    compilar = pegar(jogo, 2)
    jogo.entrada.direcao = pygame.Vector2(1, 0)
    rodar(jogo, 3)
    assert compilar.linhas == pytest.approx(30, abs=1) and compilar.contador.startswith("LINHAS")
    alvo = colocar(jogo, (100, 0), "pente_ram", escala=10)
    vida = alvo.vida
    jogo.entrada.direcao = pygame.Vector2()
    rodar(jogo, 1.2)
    assert compilar.linhas == 0 and alvo.vida < vida - 20


# ---------------------------------------------------------------- Mestre de RPG

def test_ficha_de_personagem_sorteia_um_atributo_a_cada_15_s(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    ficha = pegar(jogo, 1)
    rodar(jogo, 0.1)
    assert ficha.atributo in {sigla for sigla, _ in ficha.ATRIBUTOS} and jogo.jogador.tem_bonus("ficha")


def test_teste_de_resistencia_anula_o_golpe_com_dado_alto(jogo_limpo):
    jogo = jogo_limpo(MestreDeRPG)
    pegar(jogo, 2)
    heroi = jogo.jogador
    jogo.rng.randint = lambda a, b: 20
    assert not jogo.ferir_jogador(30) and heroi.vida == heroi.vida_maxima
    jogo.rng.randint = lambda a, b: 2
    jogo.jogador.invencivel = 0
    assert jogo.ferir_jogador(30) and heroi.vida < heroi.vida_maxima


def test_zoltraak_rola_8d6(jogo_limpo):
    from jogo.efeitos import RaioZoltraak
    jogo = jogo_limpo(MestreDeRPG)
    jogo.rng.randint = lambda a, b: b                   # tudo 6: 48
    jogo.jogador.usar_especial(jogo)
    jogo._incorporar_novas()
    raio = next(e for e in jogo.entidades if isinstance(e, RaioZoltraak))
    assert raio.dano == pytest.approx(48 * 0.65)


# ---------------------------------------------------------------- Monitor

def test_caneta_vermelha_marca_e_o_marcado_leva_mais_dano(jogo_limpo):
    jogo = jogo_limpo(Monitor)
    pegar(jogo, 1)
    jogo.rng.random = lambda: 0.0                       # sempre marca, nunca crítico
    alvo = colocar(jogo, (300, 0), "pente_ram", escala=100)
    jogo.causar_dano(alvo, 10)
    assert alvo.marcado
    vida = alvo.vida
    jogo.rng.uniform = lambda a, b: 1.0                 # sem a variação de ±10%
    jogo.causar_dano(alvo, 100)
    assert vida - alvo.vida == pytest.approx(125)


def test_horario_de_atendimento_parado_atrasa_e_cura(jogo_limpo):
    jogo = jogo_limpo(Monitor)
    jogo.jogador.armas = []
    jogo.jogador.imortal = True                         # só a cura do atendimento mexe na vida
    pegar(jogo, 2)
    heroi = jogo.jogador
    heroi.vida = heroi.vida_maxima / 2
    alvo = colocar(jogo, (150, 0), "calculadora")
    rodar(jogo, 3.2)
    assert alvo.lento > 0 and alvo.fator_lento == pytest.approx(0.8)
    assert heroi.vida > heroi.vida_maxima / 2


def test_revisao_para_prova_abre_a_zona_que_protege(jogo_limpo):
    jogo = jogo_limpo(Monitor)
    heroi = jogo.jogador
    heroi.usar_especial(jogo)
    jogo._incorporar_novas()
    assert any(isinstance(e, ZonaDeRevisao) for e in jogo.entidades)
    rodar(jogo, 0.1)
    assert not heroi.pode_levar_dano


# ---------------------------------------------------------------- Gamer

def test_frame_perfect_rolando_no_ultimo_instante(jogo_limpo):
    jogo = jogo_limpo(Gamer)
    pegar(jogo, 1)
    colocar(jogo, (40, 0), "calculadora")
    jogo.jogador.rolar(jogo)
    assert jogo.lentidao > 0 and jogo.jogador.tem_bonus("frame_perfect")


def test_rolar_longe_do_perigo_nao_e_frame_perfect(jogo_limpo):
    jogo = jogo_limpo(Gamer)
    pegar(jogo, 1)
    jogo.jogador.rolar(jogo)
    assert jogo.lentidao == 0 and not jogo.jogador.tem_bonus("frame_perfect")


def test_combo_conta_acertos_e_zera_ao_levar_dano(jogo_limpo):
    jogo = jogo_limpo(Gamer)
    combo = pegar(jogo, 2)
    alvo = colocar(jogo, (300, 0), "pente_ram", escala=1000)
    for _ in range(49):
        jogo.causar_dano(alvo, 1)
    assert combo.contador == "COMBO 49/50"
    jogo.causar_dano(alvo, 1)
    assert jogo.jogador.tem_bonus("combo") and jogo.jogador.multiplicador("golpe_duplo") == pytest.approx(1.2)
    jogo.causar_dano(alvo, 1)
    jogo.ferir_jogador(5)
    assert combo.acertos == 0


# ---------------------------------------------------------------- Calouro

def test_veterano_camarada_entra_em_campo_e_ataca(jogo_limpo):
    jogo = jogo_limpo(Calouro)
    pegar(jogo, 1)
    rodar(jogo, 0.1)
    veteranos = [e for e in jogo.entidades if isinstance(e, Veterano)]
    assert len(veteranos) == 1 and veteranos[0].multiplicador_dano == pytest.approx(0.5)
    assert type(veteranos[0].arma) is type(jogo.jogador.armas[0])


def test_perdido_no_campus_corre_mais_cercado_e_ganha_mais_experiencia(jogo_limpo):
    jogo = jogo_limpo(Calouro)
    pegar(jogo, 2)
    for i in range(5):
        colocar(jogo, pygame.Vector2(150, 0).rotate(72 * i), "pente_ram")
    rodar(jogo, 0.5)
    assert jogo.jogador.multiplicador("velocidade") == pytest.approx(1.15)


def test_calouro_muda_de_periodo_a_cada_10_niveis(jogo_limpo):
    jogo = jogo_limpo(Calouro)
    heroi = jogo.jogador
    dano = heroi.mult_dano
    jogo.dar_experiencia(sum(heroi.experiencia_do_nivel(n) for n in range(1, 11)))
    assert heroi.nivel == 11 and heroi.periodo == 2
    assert heroi.mult_dano == pytest.approx(dano * 1.05)
    assert any("2º período" in texto for texto, _ in jogo.anuncios)


# ---------------------------------------------------------------- Cara da Carona

def test_buzina_fere_e_atordoa_a_cada_10_s(jogo_limpo):
    jogo = jogo_limpo(CaraDaCarona)
    jogo.jogador.armas = []
    jogo.jogador.imortal = True
    pegar(jogo, 1)
    alvo = colocar(jogo, (100, 0), "pente_ram", escala=10)
    vida = alvo.vida
    rodar(jogo, 10.1)
    assert alvo.vida < vida and alvo.travado > 0


def test_carro_lotado_soma_dano_por_passageiro(jogo_limpo):
    jogo = jogo_limpo(CaraDaCarona)
    jogo.jogador.armas = []
    pegar(jogo, 2)
    for i in range(4):
        colocar(jogo, (300 + 40 * i, 0), "pente_ram").possuir(10)
    rodar(jogo, 0.5)
    assert jogo.jogador.multiplicador("dano") == pytest.approx(1.12)


# ---------------------------------------------------------------- polimorfismo dos ganchos

def test_itens_e_habilidades_reagem_pelos_mesmos_ganchos(jogo_limpo):
    from jogo.itens.item import Item
    from jogo.jogador.reacao import ReageAoJogo
    assert issubclass(Item, ReageAoJogo) and issubclass(Habilidade, ReageAoJogo)
    jogo = jogo_limpo(Otaku)
    pegar(jogo, 0)
    alvo = colocar(jogo, (300, 0))
    jogo.causar_dano(alvo, 9999)
    jogo._incorporar_novas()
    assert any(isinstance(e, Nota) for e in jogo.entidades)


def test_caneta_vermelha_marca_tambem_mini_chefe(jogo_limpo):
    """MiniChefe tem o próprio `marcar` (efeitos na tela): o X da caneta não pode colidir com ele."""
    jogo = jogo_limpo(Monitor)
    pegar(jogo, 1)
    jogo.rng.random = lambda: 0.0
    tia = colocar(jogo, (300, 0), "tia_da_cantina")
    jogo.causar_dano(tia, 10)
    assert tia.marcado


def test_poder_da_amizade_so_conta_amigos_de_verdade(jogo_limpo):
    from jogo.armas.apostila import Apostila
    from jogo.armas.wifi import WifiEduroam
    jogo = jogo_limpo(Otaku)
    heroi = jogo.jogador
    heroi.armas = [Apostila(), WifiEduroam()]            # folhas e sinal são ajudantes, mas não são amigos
    pegar(jogo, 2)
    rodar(jogo, 3)
    assert jogo.grupos["ajudante"] and not any(a.AMIGO for a in jogo.grupos["ajudante"])
    assert not heroi.tem_bonus("amizade")


def test_camera_lenta_nao_atrasa_o_relogio_do_semestre(jogo_limpo):
    from jogo.fase import Semestre
    jogo = jogo_limpo(Gamer)
    jogo.fase = Semestre()
    jogo.camera_lenta(1.0)
    antes_placar, antes_fase = jogo.placar.tempo, jogo.fase.tempo
    for _ in range(30):
        jogo.atualizar(1 / 30)
    assert jogo.placar.tempo - antes_placar == pytest.approx(1.0)
    assert jogo.fase.tempo - antes_fase == pytest.approx(1.0)
