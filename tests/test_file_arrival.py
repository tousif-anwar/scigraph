from scigraph.streaming.file_arrival import missing_rate


def test_missing_rate_guards_zero_records():
    assert missing_rate(5, 0) == 0.0
    assert missing_rate(2, 10) == 0.2
