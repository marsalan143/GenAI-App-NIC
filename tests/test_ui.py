"""Run real Streamlit scripts with mocked AI, without a browser or API key."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
from models import Concepts, Questions, ImprovedPlan
from services import groq_service as ai

ROOT = Path(__file__).resolve().parents[1]

def button(app, label):
    return next(b for b in app.button if b.label == label)

def stage(app, name):
    app.radio(key='stage').set_value(name).run()
    assert not app.exception

def test_landing_renders():
    app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=20).run()
    assert not app.exception
    assert button(app, 'Start Building My Startup')

def test_generator_direct_and_gates():
    app = AppTest.from_file(str(ROOT / 'pages/generator.py'), default_timeout=20).run()
    assert not app.exception
    assert app.text_area(key='problem')
    for name in ['Choose Idea', 'Business Plan', 'Feasibility', 'Investor Challenge', 'Export Pitch']:
        stage(app, name)
        assert app.info

def test_full_mocked_journey(monkeypatch, concept, plan, feasibility, questions, feedback, pitch, canvas):
    calls = {'concepts': 0, 'plan': 0}
    concepts = Concepts(concepts=[concept.model_copy(update={'name': str(i), 'solution': f'Solution {i}', 'approach': a}) for i, a in enumerate(['Budget-Friendly', 'Technology-Driven', 'High-Growth'])])
    def generate(data):
        calls['concepts'] += 1
        assert 'Students' in data['problem']
        return concepts
    def generate_plan(data):
        calls['plan'] += 1
        return plan
    monkeypatch.setattr(ai, 'generate_startup_concepts', generate)
    monkeypatch.setattr(ai, 'generate_business_plan', generate_plan)
    monkeypatch.setattr(ai, 'analyze_feasibility', lambda data: feasibility)
    monkeypatch.setattr(ai, 'generate_investor_questions', lambda data: Questions(questions=questions))
    monkeypatch.setattr(ai, 'evaluate_investor_answer', lambda data: feedback)
    monkeypatch.setattr(ai, 'improve_business_plan', lambda data: ImprovedPlan(markdown=plan + '\nImproved acquisition pilot.', changes=['Refined acquisition pilot']))
    monkeypatch.setattr(ai, 'generate_pitch_summary', lambda data: pitch)
    monkeypatch.setattr(ai, 'generate_business_model_canvas', lambda data: canvas)
    app = AppTest.from_file(str(ROOT / 'pages/generator.py'), default_timeout=15).run()
    app.text_area(key='problem').set_value('Students need reliable transport')
    button(app, 'Generate 3 Startup Ideas').click().run()
    assert not app.exception and app.session_state['stage'] == 'Choose Idea'
    button(app, 'Select This Idea').click().run()
    assert app.session_state['selected'] == concepts.concepts[0]
    button(app, 'Generate Business Plan').click().run()
    assert not app.exception and app.session_state['original_plan'] == plan
    app.run()
    assert calls == {'concepts': 1, 'plan': 1}
    stage(app, 'Discover')
    assert app.text_area(key='problem').value == 'Students need reliable transport'
    stage(app, 'Feasibility')
    button(app, 'Analyze My Startup').click().run()
    assert not app.exception and app.session_state['feasibility'] == feasibility
    stage(app, 'Investor Challenge')
    button(app, 'Challenge My Idea').click().run()
    for i in range(5):
        app.text_area(key=f'answer_{i}').set_value(f'Pilot evidence for round {i + 1}')
        button(app, 'Submit My Answer').click().run()
        assert not app.exception and len(app.session_state['interview']) == i + 1
        assert not any(b.label == 'Submit My Answer' for b in app.button)
        button(app, 'View Results' if i == 4 else 'Next Question').click().run()
    button(app, 'Improve My Startup Plan').click().run()
    assert not app.exception and app.session_state['improved']
    assert app.session_state['original_plan'] == plan
    stage(app, 'Export Pitch')
    button(app, 'Prepare Pitch Summary & Canvas').click().run()
    assert not app.exception and app.session_state['pitch_pdf'].startswith(b'%PDF')
    stage(app, 'Investor Challenge')
    button(app, 'Improve My Startup Plan').click().run()
    assert not app.exception and app.session_state['pitch'] is None and app.session_state['canvas'] is None
    stage(app, 'Choose Idea')
    next(b for b in app.button if b.key == 'select_Technology-Driven').click().run()
    assert app.session_state['original_plan'] is None and app.session_state['interview'] == []
    button(app, 'Start New Startup').click().run()
    assert not app.exception and app.session_state['concepts'] == []

def test_voice_transcript_editable(monkeypatch):
    # Native browser recording is a manual check; this verifies transcript handoff and editing.
    captured = []
    def generate(data):
        captured.append(data['problem'])
        raise ai.AIError('Mock API failure; input preserved.')
    monkeypatch.setattr(ai, 'generate_startup_concepts', generate)
    app = AppTest.from_file(str(ROOT / 'pages/generator.py'), default_timeout=20).run()
    app.session_state['voice_transcript'] = 'طلبہ کو ٹرانسپورٹ کی ضرورت ہے'
    app.session_state['problem'] = 'طلبہ کو ٹرانسپورٹ کی ضرورت ہے'
    app.run()
    app.text_area(key='problem').set_value('Corrected student transport problem')
    button(app, 'Generate 3 Startup Ideas').click().run()
    assert app.text_area(key='problem').value == 'Corrected student transport problem'
    assert captured == ['Corrected student transport problem']
    assert not app.exception

def test_plan_export_without_assessments(concept, plan):
    app = AppTest.from_file(str(ROOT / 'pages/generator.py'), default_timeout=20)
    app.session_state['selected'] = concept
    app.session_state['original_plan'] = plan
    app.session_state['stage'] = 'Export Pitch'
    app.run()
    assert not app.exception
    assert 'Download Complete Business Plan PDF' in [x.label for x in app.get('download_button')]
    assert app.session_state['feasibility'] is None and app.session_state['interview'] == []
