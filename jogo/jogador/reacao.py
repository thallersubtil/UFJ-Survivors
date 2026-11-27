"""O que reage ao que acontece na partida: itens e habilidades têm os mesmos ganchos.

O Jogador percorre itens e habilidades juntos (`Jogador.reagentes`) e chama o mesmo método em cada um,
sem perguntar o tipo de ninguém: cada classe sobrescreve só os ganchos de que precisa.
"""


class ReageAoJogo:
    """Ganchos vazios por padrão. Quem herda sobrescreve os que usa."""

    def atualizar(self, dt, jogador, jogo):
        """Chamado a cada quadro."""

    def ao_acertar(self, inimigo, jogador, jogo):
        """O aluno acabou de acertar um inimigo (antes de saber se ele morreu)."""

    def ao_critico(self, inimigo, jogador, jogo):
        """O golpe no inimigo foi crítico."""

    def ao_eliminar(self, inimigo, jogador, jogo):
        """O aluno eliminou um inimigo."""

    def ao_ser_atingido(self, dano, jogador, jogo):
        """Um golpe vai acertar o aluno. Devolve o dano que de fato entra (0 anula o golpe)."""
        return dano

    def ao_rolar(self, jogador, jogo):
        """O aluno começou um rolamento."""

    def ao_subir_de_nivel(self, jogador, jogo):
        """O aluno subiu um nível."""
