import pygame

from jogo.nucleo.recursos import Recursos, SomMudo


def test_imagem_existente_carrega_e_vem_do_cache():
    a = Recursos.imagem("legado/itens/potion_hp.png")
    b = Recursos.imagem("legado/itens/potion_hp.png")
    assert a is b
    assert a.get_size() == (46, 68)


def test_imagem_redimensionada_pela_altura():
    img = Recursos.imagem("legado/itens/potion_hp.png", 34)
    assert img.get_height() == 34
    assert img.get_width() == 23


def test_imagem_ausente_vira_substituto_sem_erro():
    img = Recursos.imagem("sprites/nao_existe.png", 40)
    assert img.get_size() == (40, 40)


def test_icone_cabe_no_quadrado():
    img = Recursos.icone("legado/itens/potion_hp.png", 32)
    assert max(img.get_size()) == 32


def test_silhueta_branca_preserva_transparencia():
    sup = pygame.Surface((4, 4), pygame.SRCALPHA)
    sup.fill((10, 20, 30, 255), pygame.Rect(0, 0, 2, 2))
    branca = Recursos.silhueta_branca(sup)
    assert branca.get_at((0, 0)) == pygame.Color(255, 255, 255, 255)
    assert branca.get_at((3, 3)).a == 0


def test_som_ausente_vira_som_mudo():
    som = Recursos.som("som_que_nao_existe")
    assert isinstance(som, SomMudo)
    Recursos.tocar("som_que_nao_existe")


def test_fonte_carrega():
    fonte = Recursos.fonte(20)
    assert fonte.render("Olá", True, (255, 255, 255)).get_width() > 0


def test_caminho_vazio_ou_imagem_corrompida_vira_substituto(tmp_path, monkeypatch):
    (tmp_path / "quebrada.png").write_bytes(b"isto nao e um png")
    monkeypatch.setattr(Recursos, "pasta", tmp_path)
    Recursos.limpar()
    assert Recursos.imagem("", 20).get_height() == 20
    assert Recursos.imagem("quebrada.png", 24).get_height() == 24
    Recursos.limpar()
