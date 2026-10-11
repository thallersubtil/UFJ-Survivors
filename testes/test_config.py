from jogo import config


def test_tamanhos_da_janela_e_da_arena():
    assert (config.LARGURA, config.ALTURA) == (1280, 720)
    assert config.ARENA_LARGURA > config.LARGURA
    assert config.ARENA_ALTURA > config.ALTURA
    assert config.DURACAO_FASE == 900


def test_fonte_existe():
    assert (config.PASTA_ASSETS / config.FONTE).exists()
