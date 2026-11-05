import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from models import Concept, Feasibility, Evaluation, Question, Pitch, Canvas
from prompts import PLAN_SECTIONS

@pytest.fixture
def concept():
    return Concept(approach='Budget-Friendly', name='Campus Route', tagline='Reliable rides for students',
                   problem='Unreliable commuting', solution='Prebook shared licensed vans', customers='Karachi students',
                   usp='Verified routes', revenue_model='Monthly subscriptions', budget='PKR 300,000 (estimate)', risks=['Route utilization'])

@pytest.fixture
def plan():
    return '\n\n'.join(f'## {h}\nIllustrative estimate. Validate demand with 20 customer interviews.' for h in PLAN_SECTIONS) + '\n\n| Item | Estimate |\n|---|---|\n| Pilot | PKR 300,000 |'

@pytest.fixture
def feasibility():
    data = {k: {'score': score, 'reasoning': 'Requires pilot validation'} for k, score in zip(
        ['market_demand', 'competition', 'investment', 'technical_feasibility', 'scalability'], [80, 60, 70, 90, 50])}
    data.update(summary='Pilot first', **{k: ['Validate using real customer evidence'] for k in ['strengths', 'weaknesses', 'risks', 'recommendations', 'assumptions_to_validate']})
    return Feasibility(**data)

@pytest.fixture
def feedback():
    return Evaluation(score=7, answered_well=['Clear pilot'], weaknesses=['No retention data'], missing_evidence=['Paid customer evidence'], suggestions=['Run paid pilot'])

@pytest.fixture
def questions():
    return [Question(category=c, question=f'What evidence supports {c.lower()}?') for c in ['Market demand', 'Revenue and profitability', 'Competition', 'Customer acquisition', 'Scalability and execution']]

@pytest.fixture
def pitch():
    return Pitch(**{k: 'Illustrative planning assumption for ' + k.replace('_', ' ') for k in Pitch.model_fields})

@pytest.fixture
def canvas():
    return Canvas(**{k: ['Pilot before scaling', 'Validate this assumption with customers'] for k in Canvas.model_fields})
