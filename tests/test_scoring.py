import pytest
from utils import feasibility_score, investor_score, WEIGHTS

def test_weighted_score(feasibility):
    assert sum(WEIGHTS.values()) == pytest.approx(1)
    assert feasibility_score(feasibility) == 71

def test_investor_score(feedback):
    assert investor_score([{'feedback': feedback}] * 5) == 70
    with pytest.raises(ValueError): investor_score([])
