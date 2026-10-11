"""Inimigos do jogo.

Todo módulo desta pasta é importado aqui, e cada inimigo se registra na
FabricaDeInimigos com o decorador @FabricaDeInimigos.registrar. Para criar
um inimigo novo basta um arquivo novo nesta pasta: nenhuma classe existente muda.
"""
import importlib
import pkgutil

for _modulo in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_modulo.name}")
