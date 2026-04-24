from app.services.elo import _expected, _k_factor, _rank_modifier


def test_expected_symmetric_at_equal_rating():
    assert abs(_expected(1500, 1500) - 0.5) < 1e-6


def test_expected_higher_rating_favored():
    assert _expected(1700, 1500) > 0.5
    assert _expected(1500, 1700) < 0.5


def test_k_factor_categories():
    assert _k_factor("Grand Slam") == 40
    assert _k_factor("Masters 1000") == 32
    assert _k_factor("ATP 500") == 28
    assert _k_factor("ATP 250") == 24
    assert _k_factor(None) == 24


def test_rank_modifier_upset_bonus():
    # winner ranked 50 beats #5 -> small bonus
    m = _rank_modifier(50, 5)
    assert 1.04 < m < 1.06
    # winner ranked 5 beats #50 -> no bonus
    assert _rank_modifier(5, 50) == 1.0
