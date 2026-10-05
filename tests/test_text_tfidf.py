import math

from scigraph.text.tfidf import DEFAULT_STOP_WORDS, idf, is_valid_token, normalize_token


def test_normalize_token() -> None:
    assert normalize_token("Data-at-Scale!") == "data at scale"


def test_is_valid_token_filters_short_numeric_and_stopwords() -> None:
    assert is_valid_token("spark", stop_words=DEFAULT_STOP_WORDS)
    assert not is_valid_token("at", stop_words=DEFAULT_STOP_WORDS)
    assert not is_valid_token("123", stop_words=DEFAULT_STOP_WORDS)
    assert not is_valid_token("research", stop_words=DEFAULT_STOP_WORDS)


def test_idf_uses_smoothing() -> None:
    assert idf(100, 9) == math.log(101 / 10) + 1
