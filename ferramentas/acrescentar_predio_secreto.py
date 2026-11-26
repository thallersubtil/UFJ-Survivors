"""Acrescenta ao mapa o Centro de Aulas Secreto 51: um prédio inventado, num descampado afastado do campus.

O mapa vem do satélite e do OpenStreetMap (gerar_mapa.py), que não conhecem este prédio; por isso ele é
acrescentado depois, direto em assets/cenario/mapa_ufj.json. Rodar de novo não duplica: rode sempre que
gerar o mapa outra vez.

Uso: python ferramentas/acrescentar_predio_secreto.py
"""
import json
import zlib
from pathlib import Path

from pintar_predios import CENARIO, ESTILO_CONHECIDO, RAIZ, pintar_predio

IDENT = "predio_secreto_51"
NOME = "CENTRO DE AULAS SECRETO 51"
POLIGONO = [(5290, 2380), (5290, 2640), (5730, 2640), (5730, 2380), (5290, 2380)]   # terra batida, a nordeste
ALTURA_PAREDE = 128
ESTILO_CONHECIDO[NOME] = "metal"            # galpão de telhado metálico


def main():
    arquivo = CENARIO / "mapa_ufj.json"
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    dados["predios"] = [p for p in dados["predios"] if p["id"] != IDENT]
    sprite, canto = pintar_predio(POLIGONO, ALTURA_PAREDE, "metal", NOME, zlib.crc32(IDENT.encode()))
    caminho = f"cenario/predios/{IDENT}.png"
    sprite.save(RAIZ / "assets" / caminho)
    dados["predios"].append({"id": IDENT, "nome": NOME, "poligono": [list(p) for p in POLIGONO],
                             "sprite": caminho, "canto": list(canto)})
    perto = lambda d: 5150 < d["x"] < 5870 and 2200 < d["y"] < 2900      # sem árvore em cima do prédio
    dados["decoracoes"] = [d for d in dados["decoracoes"] if not perto(d)]
    dados["decoracoes"] += [{"tipo": "poste", "x": x, "y": 2760} for x in (5230, 5790)]
    arquivo.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    print(IDENT, sprite.size, canto)


if __name__ == "__main__":
    main()
