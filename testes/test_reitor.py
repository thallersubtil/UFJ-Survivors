"""O Reitor de verdade: muito alto, promete o CEIA e o datacenter para o ano que vem."""
from jogo.inimigos.fabrica import FabricaDeInimigos
from jogo.nucleo.recursos import Recursos


def test_reitor_promete_o_ceia_ao_ser_invocado():
    reitor = FabricaDeInimigos.classe("reitor")
    assert reitor.GRITO == "Ano que vem chega o CEIA ein... Estamos conversando... Vai sair ein..."
    assert any("datacenter" in promessa for promessa in reitor.PROMESSAS)


def test_reitor_repete_as_promessas_em_rodizio_quando_carimba(jogo_limpo):
    jogo = jogo_limpo()
    jogo.jogador.imortal = True
    reitor = FabricaDeInimigos.criar("reitor", jogo.jogador.posicao + (200, 0))
    jogo.adicionar(reitor)
    jogo._incorporar_novas()
    falas = []
    falar = reitor.falar
    reitor.falar = lambda jogo, texto, tamanho=18: (falas.append(texto), falar(jogo, texto, tamanho))
    for ataque in range(1, 2 * len(reitor.PROMESSAS) + 1):
        reitor.ataques = ataque
        jogo._novas.clear()
        reitor.atacar(jogo)
    assert falas == list(reitor.PROMESSAS)


def test_reitor_e_bem_mais_alto_que_o_aluno(jogo_limpo):
    jogo = jogo_limpo()
    reitor = FabricaDeInimigos.criar("reitor", jogo.jogador.posicao + (200, 0))
    assert reitor.altura_sprite >= 5 * jogo.jogador.animador.quadro_atual.get_height()     # 375 px contra 72
    assert reitor.raio >= 40
    assert Recursos.imagem("rostos/reitor.png").get_size() == (64, 64)
