"""Workflow and scores use ordinary Python; they do not need an API key."""
from copy import deepcopy
from models import StartupInput

WEIGHTS = {'market_demand': .30, 'competition': .20, 'investment': .20,
           'technical_feasibility': .15, 'scalability': .15}
LABELS = {'market_demand': 'Market demand', 'competition': 'Competitive positioning',
          'investment': 'Investment practicality', 'technical_feasibility': 'Technical feasibility',
          'scalability': 'Scalability'}
DISCLAIMER = 'AI-generated preliminary assessment. Not a substitute for market research or professional financial advice.'
DEPENDENT = {'original_plan': None, 'feasibility': None, 'questions': [], 'interview': [],
             'question_index': 0, 'improved': None, 'pitch': None, 'canvas': None,
             'pitch_pdf': None, 'pitch_source': None}
DEFAULTS = {'problem': '', 'voice_transcript': '', 'themes': [], 'audience': '',
            'market': 'Pakistan', 'budget': '', 'custom_theme': '', 'input_data': None,
            'concepts': [], 'selected': None, 'audio_digest': None, 'stage': 'Discover', **DEPENDENT}

def initialize(state):
    for key, value in DEFAULTS.items():
        if key not in state:
            state[key] = deepcopy(value)
        else:
            # Keep widget-backed values when their stage is not currently rendered.
            state[key] = state[key]

def reset(state):
    for key in list(state):
        if key in DEFAULTS or key.startswith(('answer_', 'recording_')):
            del state[key]
    initialize(state)

def clear_plan_results(state):
    for key, value in DEPENDENT.items():
        state[key] = deepcopy(value)
    for key in list(state):
        if key.startswith('answer_'):
            del state[key]

def select_concept(state, concept):
    if state.get('selected') != concept:
        clear_plan_results(state)
        state['selected'] = concept

def accept_concepts(state, data, concepts):
    clear_plan_results(state)
    state.update(input_data=data, concepts=concepts, selected=None)

def feasibility_score(assessment):
    return round(sum(getattr(assessment, key).score * weight for key, weight in WEIGHTS.items()), 1)

def investor_score(interview):
    if len(interview) != 5:
        raise ValueError('Complete all five questions before calculating pitch readiness.')
    return round(sum(item['feedback'].score for item in interview) * 2, 1)

def record_answer(state, index, answer, feedback):
    if index != len(state['interview']) or index >= len(state['questions']):
        raise ValueError('This answer was already submitted or is out of order.')
    if not answer.strip():
        raise ValueError('Please enter an answer.')
    state['interview'].append({'question': state['questions'][index], 'answer': answer.strip(), 'feedback': feedback})
    state['pitch_pdf'] = None

def validate_input(problem, themes, audience, market, budget):
    return StartupInput(problem=problem, themes=themes, audience=audience, market=market, budget=budget)

def serializable(value):
    if hasattr(value, 'model_dump'):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: serializable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serializable(v) for v in value]
    return value

def context(state, improved=False):
    return serializable({'input': state['input_data'], 'concept': state['selected'],
                         'plan': state['improved'].markdown if improved and state['improved'] else state['original_plan']})
