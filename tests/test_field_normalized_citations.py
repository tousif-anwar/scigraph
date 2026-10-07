from scigraph.evaluation.field_normalized_citations import citation_age, z_score


def test_citation_age_has_minimum_one_year():
    assert citation_age(2026, 2026) == 1
    assert citation_age(2020, 2026) == 7


def test_z_score_guards_zero_stddev():
    assert z_score(10.0, 8.0, 0.0) == 0.0
    assert z_score(10.0, 8.0, 2.0) == 1.0
