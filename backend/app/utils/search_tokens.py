"""
Keyword-search tokens shared by every BM25 index (Excel Q&A and knowledge base).

Plain word matching missed obvious hits: the question "how do I ship an order?" never
matched shipment.md, because "ship" ≠ "shipment" / "shipping" / "shipped". Every token is
stemmed (Snowball English) so word forms match, and a trailing "-ment" is also removed
(Snowball keeps "shipment", "payment", "adjustment" whole). The same function runs on the
documents and the question, so the matching stays consistent.
"""

import re
from functools import lru_cache

import snowballstemmer

_stemmer = snowballstemmer.stemmer("english")
_MENT = re.compile(r"(?<=\w{3})ment$")


@lru_cache(maxsize=50_000)
def _stem(word: str) -> str:
    return _MENT.sub("", _stemmer.stemWord(word))


def search_tokens(text: str) -> list[str]:
    return [_stem(word) for word in re.sub(r"[^\w\s]", " ", text.lower()).split()]
