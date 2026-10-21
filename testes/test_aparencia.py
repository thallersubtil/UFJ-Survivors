import pygame
import pytest

from jogo.aplicacao import Aplicacao
from jogo.cenas.partida import CenaPartida
from jogo.cenas.personalizacao import CenaPersonalizacao
from jogo.cenas.selecao import CenaSelecao
from jogo.jogador.classes import Programador, Otaku
from jogo.jogador.aparencia import Aparencia, classificar, vestir_animacoes
from jogo.nucleo.recursos import Recursos
from jogo.ranking import Ranking


ALUNOS = [(pasta, moletom) for pasta, moletom in
          [("aluno1", "verde"), ("aluno2", "laranja"), ("aluna1", "verde"), ("aluna2", "laranja")]
          if Recursos.animacoes(pasta)]


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


@pytest.fixture
def app(tmp_path):
    a = Aplicacao(pygame.Surface((1280, 720)))
    a.ranking = Ranking(tmp_path / "ranking.json")
    return a


def quadro(pasta):
    return Recursos.animacoes(pasta)["parado"].quadros[0]


def test_aparencia_valida_as_escolhas():
    aparencia = Aparencia()
    assert aparencia.original
    aparencia.cabelo = "Ruivo"
    assert aparencia.cabelo == "Ruivo" and not aparencia.original
    with pytest.raises(ValueError):
        aparencia.pele = "Verde-limão"
    assert aparencia.pele == "Original"


def test_trocar_da_a_volta_na_lista():
    aparencia = Aparencia()
    aparencia.trocar("calca", -1)
    assert aparencia.calca == "Vinho"
    aparencia.trocar("calca", 1)
    assert aparencia.calca == "Original"


def test_aparencias_iguais_sao_iguais_e_tem_o_mesmo_hash():
    a = Aparencia("Escura", "Preto", "Vermelho", "Preta")
    b = Aparencia("Escura", "Preto", "Vermelho", "Preta")
    assert a == b and hash(a) == hash(b)
    assert a != Aparencia()
    assert "cabelo: Preto" in str(a)


@pytest.mark.parametrize("pasta, moletom", ALUNOS)
def test_classificacao_acha_as_partes_do_aluno(pasta, moletom):
    imagem = quadro(pasta)
    rgb = pygame.surfarray.array3d(imagem) / 255
    alfa = pygame.surfarray.array_alpha(imagem)
    mascaras = classificar(rgb, alfa, moletom)
    visiveis = (alfa > 128).sum()
    for parte in ("pele", "cabelo", "moletom", "calca"):
        assert mascaras[parte].sum() > visiveis * 0.03, parte
    assert not (mascaras["pele"] & mascaras["cabelo"]).any()
    assert not (mascaras["pele"] & mascaras["moletom"]).any()


def test_recolorir_troca_a_cor_e_mantem_a_transparencia():
    imagem = quadro("aluno1")
    nova = Aparencia(moletom="Vermelho").recolorir(imagem, "verde")
    assert nova is not imagem and nova.get_size() == imagem.get_size()
    assert pygame.surfarray.array_alpha(nova).tolist() == pygame.surfarray.array_alpha(imagem).tolist()
    rgb = pygame.surfarray.array3d(imagem) / 255
    mascara = classificar(rgb, pygame.surfarray.array_alpha(imagem), "verde")["moletom"]
    antes = pygame.surfarray.array3d(imagem)[mascara].mean(0)
    depois = pygame.surfarray.array3d(nova)[mascara].mean(0)
    assert antes[1] > antes[0]          # era verde
    assert depois[0] > depois[1] * 1.5  # ficou vermelho


def test_aparencia_original_nao_copia_nada():
    animacoes = Recursos.animacoes("aluno1")
    assert vestir_animacoes(animacoes, Aparencia()) is animacoes
    assert vestir_animacoes(animacoes, None) is animacoes


def test_jogador_vestido_usa_as_cores_e_guarda_em_cache():
    aparencia = Aparencia("Morena", "Loiro", "Azul", "Cáqui")
    a = Programador((0, 0))
    a.vestir(aparencia)
    b = Programador((0, 0))
    b.vestir(Aparencia("Morena", "Loiro", "Azul", "Cáqui"))
    original = Programador((0, 0))
    assert a.animador.animacoes["parado"].quadros[0] is b.animador.animacoes["parado"].quadros[0]
    assert a.animador.animacoes["parado"].quadros[0] is not original.animador.animacoes["parado"].quadros[0]


def test_personalizacao_vem_antes_da_classe_e_os_cartoes_usam_o_aluno_personalizado(app):
    from jogo.cenas.titulo import CenaTitulo
    app.trocar(CenaTitulo(app))
    app.passo(1 / 60, [])
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])               # JOGAR
    cena = app.cena_atual
    assert isinstance(cena, CenaPersonalizacao)
    app.passo(1 / 60, [tecla(pygame.K_DOWN), tecla(pygame.K_DOWN), tecla(pygame.K_RIGHT)])   # cabelo
    assert cena.aparencia.cabelo != "Original"
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    selecao = app.cena_atual
    assert isinstance(selecao, CenaSelecao)
    assert selecao.opcoes.aparencia == cena.aparencia
    assert all(exemplo.aparencia == cena.aparencia for exemplo in selecao.exemplos)
    app.passo(1 / 60, [tecla(pygame.K_RIGHT), tecla(pygame.K_RETURN)])
    partida = app.cena_atual
    assert isinstance(partida, CenaPartida) and isinstance(partida.jogo.jogador, Programador)
    assert partida.jogo.jogador.aparencia == cena.aparencia
    assert app.aparencia == cena.aparencia      # lembra a última escolha


def test_esc_na_selecao_volta_para_a_personalizacao(app):
    cena = CenaPersonalizacao(app)
    app.trocar(cena)
    app.passo(1 / 60, [tecla(pygame.K_RETURN)])
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert isinstance(app.cena_atual, CenaPersonalizacao)


def test_personalizacao_aleatoria_e_voltar(app):
    from jogo.cenas.titulo import CenaTitulo
    cena = CenaPersonalizacao(app)
    app.trocar(cena)
    app.passo(1 / 60, [])
    app.passo(1 / 60, [tecla(pygame.K_r)])
    app.passo(1 / 60, [tecla(pygame.K_ESCAPE)])
    assert isinstance(app.cena_atual, CenaTitulo)


def test_tecla_p_volta_as_cores_para_o_padrao_e_mantem_o_genero(app):
    cena = CenaPersonalizacao(app)
    app.trocar(cena)
    for parte, nome in (("genero", "Feminino"), ("pele", "Escura"), ("cabelo", "Azul"), ("moletom", "Roxo"),
                        ("calca", "Preta")):
        setattr(cena.aparencia, parte, nome)
    app.passo(1 / 60, [tecla(pygame.K_p)])
    assert cena.aparencia.original
    assert cena.aparencia.genero == "Feminino"
    assert cena.previa.aparencia == cena.aparencia


def test_genero_valida_e_entra_na_igualdade():
    a = Aparencia()
    assert a.genero == "Masculino"
    with pytest.raises(ValueError):
        a.genero = "Robô"
    b = Aparencia(genero="Feminino")
    assert b.original                       # gênero não é cor: continua "original"
    assert a != b and hash(a) != hash(b)
    assert Aparencia(*b.chave()) == b
    assert "genero: Feminino" in str(b)


@pytest.mark.parametrize("classe", [Programador, Otaku])
def test_aluna_usa_a_arte_feminina(classe):
    aluno = classe((0, 0))
    aluna = classe((0, 0))
    aluna.vestir(Aparencia(genero="Feminino"))
    assert classe.PASTA_SPRITE_FEMININA
    quadro_aluno = aluno.animador.animacoes["parado"].quadros[0]
    quadro_aluna = aluna.animador.animacoes["parado"].quadros[0]
    esperado = Recursos.animacoes(classe.PASTA_SPRITE_FEMININA)["parado"].quadros[0]
    assert quadro_aluna is esperado and quadro_aluna is not quadro_aluno


def test_sem_arte_feminina_usa_a_masculina():
    class SemArte(Programador):
        PASTA_SPRITE_FEMININA = "pasta_que_nao_existe"
    aluna = SemArte((0, 0))
    aluna.vestir(Aparencia(genero="Feminino"))
    assert aluna.animador.animacoes["parado"].quadros[0] is Recursos.animacoes("aluno1")["parado"].quadros[0]


def _partes(pasta, moletom, animacao="parado"):
    imagem = Recursos.animacoes(pasta)[animacao].quadros[0]
    rgb = pygame.surfarray.array3d(imagem) / 255
    return classificar(rgb, pygame.surfarray.array_alpha(imagem), moletom), imagem.get_height()


@pytest.mark.parametrize("pasta, moletom", ALUNOS)
def test_cabelo_e_moletom_nao_invadem_o_rosto(pasta, moletom):
    """Olhos e sobrancelhas têm o tom do cabelo, e a bochecha tem o tom do moletom laranja:
    nenhum deles pode entrar na máscara errada. O rosto é a pele entre a franja e o queixo."""
    import numpy as np
    for animacao in ("parado", "andar"):
        mascaras, altura = _partes(pasta, moletom, animacao)
        pele = mascaras["pele"]
        from jogo.jogador.aparencia import rgb_para_hsv
        imagem = Recursos.animacoes(pasta)[animacao].quadros[0]
        _, sat, val = rgb_para_hsv(pygame.surfarray.array3d(imagem) / 255)
        y = np.arange(altura)[None, :] * np.ones(pele.shape)
        branco_do_olho = (pygame.surfarray.array_alpha(imagem) > 128) & (sat < 0.2) & (val > 0.8) \
            & (y > altura * 0.2) & (y < altura * 0.42)
        olhos_ate = int(y[branco_do_olho].max())
        linhas = range(olhos_ate + 1, olhos_ate + 1 + max(3, altura // 20))   # logo abaixo dos olhos: bochecha e boca
        xs, ys = np.where(pele)
        abaixo = (ys >= linhas.start) & (ys < linhas.stop)
        centro = int(np.median(xs[abaixo]))
        largura = int(np.median([np.ptp(np.where(pele[:, l])[0]) for l in linhas if pele[:, l].sum() > 1]))
        # miolo do rosto (orelha e mechas laterais do cabelo comprido ficam fora)
        miolo = slice(centro - largura // 4, centro + largura // 4 + 1)
        for linha in linhas:
            colunas = np.where(pele[:, linha])[0]
            if len(colunas) < 2:
                continue
            dentro = slice(max(miolo.start, colunas.min()), min(miolo.stop, colunas.max() + 1))
            assert not mascaras["moletom"][dentro, linha].any(), (animacao, linha)
            assert not mascaras["cabelo"][dentro, linha].any(), (animacao, linha)


@pytest.mark.parametrize("pasta, moletom", ALUNOS)
def test_olhos_nao_entram_no_cabelo(pasta, moletom):
    """A íris tem tom de cabelo e às vezes encosta na franja; ela não pode pegar a cor do cabelo."""
    import numpy as np
    from jogo.jogador.aparencia import rgb_para_hsv
    imagem = Recursos.animacoes(pasta)["parado"].quadros[0]
    mascaras, altura = _partes(pasta, moletom)
    h, s, v = rgb_para_hsv(pygame.surfarray.array3d(imagem) / 255)
    alfa = pygame.surfarray.array_alpha(imagem)
    topo = (alfa > 128).any(0).argmax() / altura
    y = np.arange(altura)[None, :] / altura
    branco = (alfa > 128) & (s < 0.2) & (v > 0.8) & (y > topo + 0.2) & (y < 0.42)
    assert branco.any()
    ao_lado = branco.copy()               # a íris fica ao lado do branco do olho, na mesma linha
    for _ in range(2):
        ao_lado[1:, :] |= ao_lado[:-1, :].copy()
        ao_lado[:-1, :] |= ao_lado[1:, :].copy()
    assert not (mascaras["cabelo"] & ao_lado & (v < 0.6)).any()


def test_aluno_sem_bone_nao_tem_mascara_de_bone():
    mascaras, _ = _partes("aluno1", "verde")
    assert not mascaras["bone"].any()


def test_capuz_do_aluno2_andando_entra_no_moletom():
    import numpy as np
    from jogo.jogador.aparencia import rgb_para_hsv
    imagem = Recursos.animacoes("aluno2")["andar"].quadros[0]
    rgb = pygame.surfarray.array3d(imagem) / 255
    mascaras = classificar(rgb, pygame.surfarray.array_alpha(imagem), "laranja")
    h, s, v = rgb_para_hsv(rgb)
    laranja_forte = (pygame.surfarray.array_alpha(imagem) > 128) & (h >= 5) & (h < 45) & (s >= 0.95) & (v > 0.5)
    assert (laranja_forte & ~mascaras["moletom"]).sum() <= 0.05 * laranja_forte.sum()


@pytest.mark.parametrize("pasta, moletom", ALUNOS)
def test_pele_da_testa_entre_as_mechas_nao_vira_cabelo(pasta, moletom):
    """A testa aparece em pedacinhos entre as mechas da franja; eles são pele, não cabelo."""
    import numpy as np
    from jogo.jogador.aparencia import rgb_para_hsv
    for animacao in ("parado", "andar"):
        mascaras, altura = _partes(pasta, moletom, animacao)
        imagem = Recursos.animacoes(pasta)[animacao].quadros[0]
        h, s, v = rgb_para_hsv(pygame.surfarray.array3d(imagem) / 255)
        alfa = pygame.surfarray.array_alpha(imagem)
        topo = (alfa > 128).any(0).argmax() / altura
        y = np.arange(altura)[None, :] / altura
        branco = (alfa > 128) & (s < 0.2) & (v > 0.8) & (y > topo + 0.2) & (y < 0.38)
        olho_topo = np.nonzero(branco)[1].min() / altura
        # a testa: os poucos pixels logo acima dos olhos (mais acima são os reflexos do cabelo)
        pele_clara = (h >= 14) & (h < 40) & (s >= 0.35) & (v > 0.7) & (y > olho_topo - 0.06) & (y < olho_topo)
        assert not (mascaras["cabelo"] & pele_clara).any(), animacao


def _quadros(pasta):
    for animacao in ("parado", "andar"):
        for i, imagem in enumerate(Recursos.animacoes(pasta)[animacao].quadros):
            yield f"{animacao}{i}", imagem


@pytest.mark.parametrize("pasta, moletom", ALUNOS)
def test_cabelo_escuro_nunca_vira_pele_em_nenhum_quadro(pasta, moletom):
    """Em todos os quadros (inclusive o de olhos fechados), o cabelo escuro fica no cabelo:
    se a pele pegasse mechas, trocar o tom de pele pintaria o cabelo."""
    import numpy as np
    from jogo.jogador.aparencia import rgb_para_hsv
    for nome, imagem in _quadros(pasta):
        rgb = pygame.surfarray.array3d(imagem) / 255
        alfa = pygame.surfarray.array_alpha(imagem)
        mascaras = classificar(rgb, alfa, moletom)
        h, s, v = rgb_para_hsv(rgb)
        y = np.arange(imagem.get_height())[None, :] / imagem.get_height()
        cabelo_escuro = (alfa > 128) & (v > 0.08) & (v < 0.4) & (s > 0.25) & (y < 0.3)
        # a sombra da franja sobre a testa é escura também, mas são poucos pixels
        assert (mascaras["pele"] & cabelo_escuro).sum() <= 0.05 * cabelo_escuro.sum(), nome
        assert mascaras["cabelo"].sum() > 0.6 * (cabelo_escuro & ~mascaras["bone"]).sum(), nome


@pytest.mark.parametrize("pasta, moletom", ALUNOS)
def test_cordoes_do_capuz_nao_sao_pele(pasta, moletom):
    """Os cordões claros do capuz têm tom de pele e encostam no pescoço; não podem trocar com a pele."""
    import numpy as np
    for nome, imagem in _quadros(pasta):
        mascaras = classificar(pygame.surfarray.array3d(imagem) / 255, pygame.surfarray.array_alpha(imagem), moletom)
        altura = imagem.get_height()
        pele = mascaras["pele"]
        largura = pele.shape[0]
        peito = pele[largura // 4: 3 * largura // 4, int(altura * 0.47): int(altura * 0.56)]
        assert not peito.any(), nome


@pytest.mark.parametrize("pasta", [p for p, m in ALUNOS if m == "laranja"])
def test_parte_de_tras_do_bone_nao_e_cabelo(pasta):
    """O boné (inclusive a sombra puxada para o marrom na parte de trás) troca com o moletom, nunca com o cabelo."""
    from jogo.jogador.aparencia import rgb_para_hsv
    for nome, imagem in _quadros(pasta):
        rgb = pygame.surfarray.array3d(imagem) / 255
        alfa = pygame.surfarray.array_alpha(imagem)
        mascaras = classificar(rgb, alfa, "laranja")
        h, s, v = rgb_para_hsv(rgb)
        vermelho = (alfa > 128) & ((h < 12) | (h >= 345)) & (s >= 0.8) & (v > 0.5)
        assert not (mascaras["cabelo"] & vermelho).any(), nome
        assert mascaras["bone"].sum() > 0.9 * vermelho[:, : imagem.get_height() // 4].sum(), nome
