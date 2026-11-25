from jogo import config


def test_tamanhos_da_janela_e_da_arena():
    assert (config.LARGURA, config.ALTURA) == (1280, 720)
    assert config.ARENA_LARGURA > config.LARGURA
    assert config.ARENA_ALTURA > config.ALTURA
    assert config.DURACAO_PROVA == 300


def test_fonte_existe():
    assert (config.PASTA_ASSETS / config.FONTE).exists()


def test_fontes_sao_ttf():
    """WOFF2 não renderiza no pygame-ce do Windows (pygame.error: Passed a NULL pointer)."""
    for fonte in (config.FONTE, config.FONTE_MEDIA):
        assert fonte.endswith(".ttf")
        assert (config.PASTA_ASSETS / fonte).exists()


def test_fonte_que_nao_renderiza_cai_na_padrao(tmp_path, monkeypatch):
    from jogo.nucleo.recursos import Recursos
    ruim = tmp_path / "fontes" / "quebrada.ttf"
    ruim.parent.mkdir()
    ruim.write_bytes(b"isto nao e uma fonte")
    monkeypatch.setattr(Recursos, "pasta", tmp_path)
    fonte = Recursos.fonte(20, "fontes/quebrada.ttf")
    assert fonte.render("Olá", True, (255, 255, 255)).get_width() > 0
