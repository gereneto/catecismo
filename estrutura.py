# -*- coding: utf-8 -*-
"""Calcula as aberturas de tópico e grava-as em dados/manifesto.json.

A trilha de cada ponto (campo "trail") nem sempre traz todos os níveis: um
ponto fundo costuma omitir a seção ou o artigo a que pertence. Por isso a
trilha bruta não serve para comparar dois pontos vizinhos — o que aqui se faz
é reconstruir, ponto a ponto, a hierarquia inteira, e só então ver o que
mudou.

Rode depois de acrescentar ou alterar pontos:

    python estrutura.py
"""

import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, "dados")

# Os seis níveis, do mais amplo ao mais estreito. O último — o subtítulo
# marginal — vem colado ao tópico na trilha, separado por " · ".
NIVEIS = ["parte", "secao", "capitulo", "artigo", "topico", "subtitulo"]
SUBTITULO = NIVEIS.index("subtitulo")

ORDINAIS = "Primeira|Segunda|Terceira|Quarta|Quinta|Sexta"


def nivel(titulo):
    """A que nível da hierarquia pertence uma entrada da trilha."""
    if re.match(r"^Prólogo$", titulo):
        return 0
    if re.match(r"^(%s) parte\b" % ORDINAIS, titulo):
        return 0
    if re.match(r"^(%s) seção\b" % ORDINAIS, titulo):
        return 1
    if re.match(r"^Capítulo\b", titulo):
        return 2
    if re.match(r"^Artigo\b", titulo):
        return 3
    return 4                      # "I. ...", "Resumindo" e afins


def partir(titulo, n):
    """Separa "Capítulo primeiro — O homem…" em rótulo e título.

    Só os níveis com nome próprio (parte, seção, capítulo, artigo) trazem
    esse rótulo; nos tópicos o texto vale inteiro.
    """
    if n <= 3 and " — " in titulo:
        rotulo, resto = titulo.split(" — ", 1)
        return rotulo, resto
    return None, titulo


def hierarquia(pontos):
    """Devolve, para cada ponto, a hierarquia completa em seis níveis."""
    completo = {}
    anterior = [None] * len(NIVEIS)
    for n in sorted(pontos):
        atual = list(anterior)

        entradas = []
        for t in pontos[n]:
            k = nivel(t)
            if " · " in t:
                if k != 4:
                    sys.exit("ponto %d: separador · fora de um tópico: %r" % (n, t))
                topico, sub = t.split(" · ", 1)
                entradas.append((4, topico))
                entradas.append((SUBTITULO, sub))
            else:
                entradas.append((k, t))

        # Ao mudar um nível, tudo o que está abaixo dele recomeça; o que a
        # trilha não menciona e não foi reiniciado permanece como estava.
        mudou = [k for k, t in entradas if atual[k] != t]
        if mudou:
            for k in range(min(mudou) + 1, len(NIVEIS)):
                atual[k] = None
        for k, t in entradas:
            atual[k] = t

        completo[n] = atual
        anterior = atual
    return completo


def main():
    caminho = os.path.join(DADOS, "manifesto.json")
    with io.open(caminho, encoding="utf-8") as f:
        man = json.load(f)

    pontos = {}
    for b in man["blocos"]:
        with io.open(os.path.join(DADOS, b["file"]), encoding="utf-8") as f:
            d = json.load(f)
        for n in range(b["de"], b["ate"] + 1):
            if str(n) not in d:
                sys.exit("ponto %d anunciado no manifesto mas ausente de %s"
                         % (n, b["file"]))
            pontos[n] = d[str(n)]["trail"]

    completo = hierarquia(pontos)

    aberturas = {}
    subtitulos = {}
    anterior = [None] * len(NIVEIS)
    for n in sorted(completo):
        atual = completo[n]

        # O subtítulo marginal não ganha página; vai no alto do corpo do
        # primeiro ponto que lhe pertence.
        if atual[SUBTITULO] and atual[SUBTITULO] != anterior[SUBTITULO]:
            subtitulos[str(n)] = atual[SUBTITULO]

        novos = [k for k in range(SUBTITULO)
                 if atual[k] and atual[k] != anterior[k]]
        if novos:
            anuncio = []
            for k in novos:
                rotulo, titulo = partir(atual[k], k)
                anuncio.append(
                    {"nivel": NIVEIS[k], "rotulo": rotulo, "titulo": titulo})
            # O que já estava aberto acima do nível mais alto que mudou fica
            # como contexto: sem ele uma abertura de "Resumindo" não diria
            # resumo de quê.
            aberturas[str(n)] = {
                "contexto": [atual[k] for k in range(min(novos)) if atual[k]],
                "novos": anuncio,
            }

        anterior = atual

    man["aberturas"] = aberturas
    man["subtitulos"] = subtitulos

    with io.open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(man, ensure_ascii=False, indent=1))
        f.write(u"\n")

    print("%d pontos, %d aberturas, %d subtitulos"
          % (len(completo), len(aberturas), len(subtitulos)))


if __name__ == "__main__":
    main()
