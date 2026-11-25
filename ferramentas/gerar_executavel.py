"""Gera a pasta "UFJ Survivors/" com o executável do jogo (PyInstaller, modo pasta).

Uso (no Windows, para sair um .exe; em outro sistema sai o executável daquele sistema):
    python -m pip install -r requirements.txt pyinstaller
    python ferramentas/gerar_executavel.py

Passos:
1. Empacota um teste de fumaça (ferramentas/teste_executavel.py) do mesmo jeito que o
   jogo e roda: ele entra numa partida com cada classe. Se falhar, para aqui e a pasta
   antiga fica como estava.
2. Empacota o jogo (main.py) sem console, com o ícone assets/icone.ico.
3. Troca o conteúdo de "UFJ Survivors/" pelo novo build, mantendo a pasta dados/
   (ranking e progresso de quem já jogou), e escreve o LEIA-ME.txt.

Todo módulo de jogo/ entra como --hidden-import: os inimigos são carregados por
pkgutil.iter_modules e o PyInstaller só acha sozinho o que aparece em import direto.
O GitHub Actions (.github/workflows/executavel.yml) roda este script a cada push no main.
"""
import datetime
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOME = "UFJ Survivors"
DESTINO = RAIZ / NOME

LEIA_ME = """UFJ Survivors - Trabalho de POO (UFJ, 2026/2)
==============================================

Como jogar
  De dois cliques em "UFJ Survivors.exe". Nao precisa instalar Python nem nada.
  Se o Windows mostrar "O Windows protegeu o computador", clique em
  "Mais informacoes" e depois em "Executar assim mesmo" (o jogo nao tem assinatura digital).

Controles
  WASD ou setas: andar      Mouse: mirar (clique esquerdo troca para mira automatica)
  Espaco: especial          Shift ou clique direito: rolamento       Esc: pausa

Onde ficam os saves
  A pasta "dados" (criada ao lado do .exe na primeira partida) guarda o ranking,
  as moedas e as compras do Centro Academico. Para levar seu progresso para outro
  computador, copie essa pasta junto.

Nao apague nem mova a pasta "_internal": o jogo precisa dela.

Esta pasta e gerada automaticamente a partir do ramo main
(ferramentas/gerar_executavel.py). Nao edite os arquivos dela a mao.

Versao: {versao}
"""


def modulos_do_jogo():
    for arquivo in sorted((RAIZ / "jogo").rglob("*.py")):
        partes = arquivo.relative_to(RAIZ).with_suffix("").parts
        if partes[-1] == "__init__":
            partes = partes[:-1]
        yield ".".join(partes)


def empacotar(script, nome, pasta_saida, trabalho, janela):
    comando = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
               "--windowed" if janela else "--console", "--name", nome,
               "--add-data", f"{RAIZ / 'assets'}{';' if sys.platform == 'win32' else ':'}assets",
               "--paths", str(RAIZ), "--distpath", str(pasta_saida), "--workpath", str(trabalho),
               "--specpath", str(trabalho), "--log-level", "WARN"]
    if janela:
        comando += ["--icon", str(RAIZ / "assets" / "icone.ico")]
    comando += [f"--hidden-import={m}" for m in modulos_do_jogo()]
    subprocess.run(comando + [str(script)], check=True, cwd=RAIZ)
    return pasta_saida / nome


def versao():
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                cwd=RAIZ, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "sem git"
    return f"commit {commit}, gerada em {datetime.date.today():%d/%m/%Y}"


def main():
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        print("1/3 testando o executavel numa partida de verdade...")
        teste = empacotar(RAIZ / "ferramentas" / "teste_executavel.py", "teste_executavel",
                          temp / "dist", temp / "build_teste", janela=False)
        exe = next(p for p in teste.iterdir() if p.stem == "teste_executavel" and p.is_file())
        resultado = subprocess.run([str(exe)], capture_output=True, text=True)
        print(resultado.stdout[-2000:], resultado.stderr[-2000:])
        if resultado.returncode != 0 or "SMOKE OK" not in resultado.stdout:
            sys.exit("O teste do executavel falhou; a pasta antiga nao foi trocada.")

        print("2/3 empacotando o jogo...")
        novo = empacotar(RAIZ / "main.py", NOME, temp / "dist", temp / "build_jogo", janela=True)

        print(f"3/3 atualizando a pasta '{NOME}'...")
        DESTINO.mkdir(exist_ok=True)
        for item in DESTINO.iterdir():
            if item.name == "dados":                  # saves de quem jogou por esta pasta
                continue
            shutil.rmtree(item) if item.is_dir() else item.unlink()
        for item in novo.iterdir():
            shutil.move(str(item), DESTINO / item.name)
        (DESTINO / "LEIA-ME.txt").write_text(LEIA_ME.format(versao=versao()), encoding="utf-8", newline="\r\n")
    print("Pronto:", DESTINO)


if __name__ == "__main__":
    main()
