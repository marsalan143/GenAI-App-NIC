import pytest
from utils import initialize, select_concept, accept_concepts, reset, record_answer, validate_input

def test_independent_initialization():
    state = {}
    initialize(state)
    state['problem'] = 'Saved problem'
    initialize(state)
    assert state['problem'] == 'Saved problem'
    assert state['interview'] == []

def test_selection_clears_dependents(concept):
    state = {}; initialize(state)
    select_concept(state, concept)
    state.update(original_plan='old', feasibility='old', improved='old', pitch_pdf=b'old', interview=[1])
    select_concept(state, concept)
    assert state['original_plan'] == 'old'
    select_concept(state, concept.model_copy(update={'name': 'Another'}))
    assert state['original_plan'] is None and state['interview'] == [] and state['pitch_pdf'] is None

def test_new_concepts_reset_and_reset(concept):
    state = {}; initialize(state)
    state['original_plan'] = 'old'
    accept_concepts(state, validate_input('Transport', [], '', 'Pakistan', ''), [concept])
    assert state['original_plan'] is None and state['selected'] is None
    reset(state)
    assert state['concepts'] == [] and state['market'] == 'Pakistan'

def test_duplicate_answer_prevention(questions, feedback):
    state = {}; initialize(state); state['questions'] = questions
    record_answer(state, 0, 'My answer', feedback)
    assert state['interview'][0]['answer'] == 'My answer'
    with pytest.raises(ValueError): record_answer(state, 0, 'Duplicate', feedback)
    with pytest.raises(ValueError): record_answer(state, 2, 'Out of order', feedback)
    with pytest.raises(ValueError): record_answer(state, 1, ' ', feedback)
