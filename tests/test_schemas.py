import pytest
from pydantic import ValidationError
from models import Concepts, Questions, Rating, Evaluation
from utils import validate_input

@pytest.mark.parametrize('problem,market', [('', 'Pakistan'), ('  ', 'Pakistan'), ('ab', 'Pakistan'), ('Transport', '')])
def test_invalid_input(problem, market):
    with pytest.raises(ValidationError): validate_input(problem, [], '', market, '')

def test_urdu_input():
    assert validate_input('طلبہ کو سفر میں مشکلات ہیں', ['Transportation'], '', 'Pakistan', '').problem

def test_three_distinct_concepts(concept):
    concepts = [concept.model_copy(update={'name': str(i), 'solution': f'Solution {i}', 'approach': approach}) for i, approach in enumerate(['Budget-Friendly', 'Technology-Driven', 'High-Growth'])]
    assert len(Concepts(concepts=concepts).concepts) == 3
    with pytest.raises(ValidationError): Concepts(concepts=[concept] * 3)
    with pytest.raises(ValidationError): Concepts(concepts=concepts[:2])

@pytest.mark.parametrize('score', [-1, 101, float('nan'), float('inf')])
def test_invalid_scores(score):
    with pytest.raises(ValidationError): Rating(score=score, reasoning='Reason')

def test_question_coverage(questions):
    assert len(Questions(questions=questions).questions) == 5
    with pytest.raises(ValidationError): Questions(questions=[questions[0]] * 5)

def test_evaluation_bounds(feedback):
    with pytest.raises(ValidationError): Evaluation(**{**feedback.model_dump(), 'score': 11})
