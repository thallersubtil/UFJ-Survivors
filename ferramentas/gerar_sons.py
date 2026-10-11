"""Sintetiza os efeitos sonoros do jogo em assets/sons/*.wav.

O áudio do 67 usa a voz do sistema (comando `say` do macOS) quando existe;
o grupo pode substituir assets/sons/67.wav pelo áudio que quiser.
"""
import math
import random
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

TAXA = 22050
PASTA = Path(__file__).resolve().parent.parent / "assets" / "sons"


def tom(freq_ini, freq_fim, duracao, forma="quadrada", volume=0.5, ruido=0.0):
    amostras = []
    fase = 0.0
    total = int(TAXA * duracao)
    for i in range(total):
        t = i / total
        freq = freq_ini + (freq_fim - freq_ini) * t
        fase += 2 * math.pi * freq / TAXA
        if forma == "quadrada":
            v = 1.0 if math.sin(fase) >= 0 else -1.0
        elif forma == "triangular":
            v = 2 / math.pi * math.asin(math.sin(fase))
        else:
            v = math.sin(fase)
        v = v * (1 - ruido) + random.uniform(-1, 1) * ruido
        envelope = min(1.0, i / (TAXA * 0.004)) * (1 - t) ** 1.5
        amostras.append(v * envelope * volume)
    return amostras


def silencio(duracao):
    return [0.0] * int(TAXA * duracao)


def gravar(nome, amostras):
    PASTA.mkdir(parents=True, exist_ok=True)
    with wave.open(str(PASTA / f"{nome}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, a)) * 32000)) for a in amostras))


def arpejo(notas, duracao_nota, forma="quadrada", volume=0.4):
    resultado = []
    for n in notas:
        resultado += tom(n, n, duracao_nota, forma, volume)
    return resultado


def gerar_67():
    destino = PASTA / "67.wav"
    if shutil.which("say") and shutil.which("afconvert"):
        with tempfile.TemporaryDirectory() as pasta:
            aiff = Path(pasta) / "67.aiff"
            subprocess.run(["say", "-v", "Samantha", "-r", "170", "-o", str(aiff), "six seven"], check=True)
            subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@22050", "-c", "1", str(aiff), str(destino)], check=True)
            return
    gravar("67", arpejo([523, 659], 0.25, "triangular", 0.6))


def main():
    random.seed(67)
    gravar("acerto", tom(220, 90, 0.05, "quadrada", 0.25, ruido=0.6))
    gravar("disparo", tom(900, 500, 0.04, "quadrada", 0.18))
    gravar("coleta", tom(880, 1320, 0.06, "triangular", 0.35))
    gravar("nivel", arpejo([523, 659, 784, 1046], 0.08, "quadrada", 0.3))
    gravar("bau", arpejo([392, 523, 659, 784, 1046, 1318], 0.07, "triangular", 0.45))
    gravar("buzina", tom(420, 400, 0.16, "quadrada", 0.35) + silencio(0.05) + tom(420, 400, 0.22, "quadrada", 0.35))
    gravar("dano", tom(220, 70, 0.15, "quadrada", 0.4, ruido=0.3))
    gravar("especial", tom(250, 1200, 0.6, "triangular", 0.5))
    gravar("claude", tom(1400, 300, 0.18, "senoidal", 0.5, ruido=0.2))
    gravar("vitoria", arpejo([523, 523, 784, 1046], 0.16, "quadrada", 0.35) + tom(1046, 1046, 0.5, "triangular", 0.4))
    gravar("derrota", arpejo([392, 370, 349], 0.22, "quadrada", 0.35) + tom(330, 160, 0.7, "triangular", 0.4))
    gerar_67()
    print(f"sons gravados em {PASTA}")


if __name__ == "__main__":
    main()
