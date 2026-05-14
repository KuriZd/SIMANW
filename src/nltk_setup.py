from __future__ import annotations

import nltk


RECURSOS_NLTK = {
    "tokenizers/punkt": "punkt",
    "tokenizers/punkt_tab": "punkt_tab",
    "corpora/stopwords": "stopwords",
    "sentiment/vader_lexicon.zip": "vader_lexicon",
}


def descargar_recursos() -> None:
    for ruta, paquete in RECURSOS_NLTK.items():
        try:
            nltk.data.find(ruta)
        except LookupError:
            nltk.download(paquete, quiet=True)


def main() -> None:
    descargar_recursos()
    print("Recursos de NLTK listos para SIMANW.")


if __name__ == "__main__":
    main()
