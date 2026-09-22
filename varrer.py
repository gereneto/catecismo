# -*- coding: utf-8 -*-
"""Procura mesóclises no texto do site.

Faz o mesmo que o grep de sempre, mas em Python, porque o grep do shell
compara bytes: quando o verbo e a terminação trazem acento — «perdê-la-á»,
«dar-nos-ão» —, o padrão não casa e a ocorrência passa despercebida. Aqui a
comparação é por caractere, e essas formas são encontradas.

    python varrer.py
    python varrer.py um_arquivo.json
"""

import glob
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

PRONOMES = "lo|la|los|las|o|a|os|as|me|te|se|lhe|lhes|nos|vos|no|na"
# Terminações do futuro do presente e do futuro do pretérito.
FUTUROS = "ei|as|á|ás|emos|eis|ão|ia|ias|íamos|íeis|iam"
MESOCLISE = re.compile(
    r"[^\W\d_]+-(?:%s)-(?:%s)(?![^\W\d_])" % (PRONOMES, FUTUROS), re.UNICODE)


def main():
    alvos = sys.argv[1:]
    if not alvos:
        alvos = sorted(glob.glob(os.path.join(AQUI, "dados", "*.json")))
        alvos.append(os.path.join(AQUI, "index.html"))

    achados = 0
    for caminho in alvos:
        with io.open(caminho, encoding="utf-8") as f:
            texto = f.read()
        for m in MESOCLISE.finditer(texto):
            achados += 1
            volta = texto[max(0, m.start() - 90):m.end() + 60].replace("\n", " ")
            print("%s: %s" % (os.path.basename(caminho), m.group(0)))
            print("    ...%s..." % volta)

    if achados:
        print("\n%d mesóclise(s) — reescrever com próclise ou ênclise." % achados)
        return 1
    print("nenhuma mesóclise em %d arquivo(s)." % len(alvos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
