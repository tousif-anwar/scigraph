import pytest

from scigraph.streaming.microbatch import alert_triggered, batch_id_for_position


def test_batch_id_for_position() -> None:
    assert batch_id_for_position(1, 100) == 0
    assert batch_id_for_position(100, 100) == 0
    assert batch_id_for_position(101, 100) == 1


def test_batch_id_for_position_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        batch_id_for_position(0, 100)
    with pytest.raises(ValueError):
        batch_id_for_position(1, 0)


def test_alert_triggered_requires_rate_above_threshold() -> None:
    assert alert_triggered(0.06, 0.05)
    assert not alert_triggered(0.05, 0.05)
