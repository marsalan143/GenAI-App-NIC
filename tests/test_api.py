from types import SimpleNamespace as NS
from unittest.mock import Mock
import httpx
import pytest
from groq import AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError
from services import groq_service as ai
from prompts import build_prompt, PLAN_SECTIONS
from models import Concepts

def response(content, finish='stop'):
    return NS(choices=[NS(message=NS(content=content), finish_reason=finish)])

def test_prompt_construction():
    prompt = build_prompt('concepts', {'problem': 'Student transport', 'market': 'Pakistan'}, Concepts)
    assert 'Student transport' in prompt and 'Pakistan' in prompt and 'JSON schema' in prompt
    assert all(h in build_prompt('plan', {}) for h in PLAN_SECTIONS)

def test_malformed_json_repair(monkeypatch):
    api = Mock(); api.chat.completions.create.return_value = response('{invalid')
    monkeypatch.setattr(ai, 'client', lambda: api)
    with pytest.raises(ai.AIError, match='invalid content twice'): ai.generate_startup_concepts({})
    assert api.chat.completions.create.call_count == 2

def test_repair_succeeds(monkeypatch, concept):
    api = Mock()
    valid = Concepts(concepts=[concept.model_copy(update={'name': str(i), 'solution': str(i), 'approach': approach}) for i, approach in enumerate(['Budget-Friendly', 'Technology-Driven', 'High-Growth'])])
    api.chat.completions.create.side_effect = [response(''), response(valid.model_dump_json())]
    monkeypatch.setattr(ai, 'client', lambda: api)
    assert len(ai.generate_startup_concepts({}).concepts) == 3

def test_plan_validation(monkeypatch, plan):
    api = Mock(); api.chat.completions.create.return_value = response(plan)
    monkeypatch.setattr(ai, 'client', lambda: api)
    assert ai.generate_business_plan({}) == plan
    api.chat.completions.create.return_value = response('Incomplete plan')
    with pytest.raises(ai.AIError): ai.generate_business_plan({})

@pytest.mark.parametrize('error_type', [AuthenticationError, RateLimitError, APIStatusError, APITimeoutError, APIConnectionError])
def test_api_failures(error_type):
    request = httpx.Request('POST', 'https://api.groq.com')
    if error_type == APITimeoutError:
        error = error_type(request=request)
    elif error_type == APIConnectionError:
        error = error_type(request=request)
    else:
        error = error_type('private provider detail', response=httpx.Response(429 if error_type == RateLimitError else 401, request=request), body={})
    def fail(): raise error
    with pytest.raises(ai.AIError) as caught: ai.safe_call(fail)
    assert 'private provider detail' not in str(caught.value)

@pytest.mark.parametrize('language', ['en', 'ur', None])
def test_transcription_endpoint(monkeypatch, language):
    api = Mock(); api.audio.transcriptions.create.return_value = NS(text='  Editable transcript  ')
    monkeypatch.setattr(ai, 'client', lambda: api)
    assert ai.transcribe_audio(b'RIFF-test-recording', language) == 'Editable transcript'
    args = api.audio.transcriptions.create.call_args.kwargs
    assert args['file'][0] == 'idea.wav' and args['response_format'] == 'json'
    assert args.get('language') == language

def test_empty_transcription(monkeypatch):
    api = Mock(); api.audio.transcriptions.create.return_value = NS(text='')
    monkeypatch.setattr(ai, 'client', lambda: api)
    with pytest.raises(ai.AIError): ai.transcribe_audio(b'RIFF')
    with pytest.raises(ai.AIError): ai.transcribe_audio(b'')

def test_missing_key(monkeypatch):
    monkeypatch.setattr(ai, 'configuration', lambda: {'GROQ_API_KEY': ''})
    with pytest.raises(ai.AIError, match='GROQ_API_KEY'): ai.client()

@pytest.mark.parametrize('function,fixture', [
    ('analyze_feasibility', 'feasibility'), ('evaluate_investor_answer', 'feedback'),
    ('generate_pitch_summary', 'pitch'), ('generate_business_model_canvas', 'canvas')])
def test_structured_service_functions(monkeypatch, request, function, fixture):
    expected = request.getfixturevalue(fixture)
    api = Mock(); api.chat.completions.create.return_value = response(expected.model_dump_json())
    monkeypatch.setattr(ai, 'client', lambda: api)
    assert getattr(ai, function)({'startup': 'Campus Route'}) == expected
    assert api.chat.completions.create.call_args.kwargs['response_format'] == {'type': 'json_object'}

def test_questions_and_improvement_service(monkeypatch, questions, plan):
    from models import Questions, ImprovedPlan
    api = Mock(); monkeypatch.setattr(ai, 'client', lambda: api)
    api.chat.completions.create.return_value = response(Questions(questions=questions).model_dump_json())
    assert ai.generate_investor_questions({}).questions == questions
    expected = ImprovedPlan(markdown=plan, changes=['Specific improvement'])
    api.chat.completions.create.return_value = response(expected.model_dump_json())
    assert ai.improve_business_plan({}) == expected


def test_unavailable_model_error_is_actionable():
    error = APIStatusError('private provider detail', response=httpx.Response(404, request=httpx.Request('POST', 'https://api.groq.com')), body={'error': {'code': 'model_not_found'}})
    def fail(): raise error
    with pytest.raises(ai.AIError, match='model unavailable'):
        ai.safe_call(fail)


def test_urdu_script_prompt_and_retry(monkeypatch):
    api = Mock()
    api.audio.transcriptions.create.side_effect = [NS(text='यह हिंदी है'), NS(text='یہ اردو متن ہے')]
    monkeypatch.setattr(ai, 'client', lambda: api)
    assert ai.transcribe_audio(b'RIFF', 'ur') == 'یہ اردو متن ہے'
    assert api.audio.transcriptions.create.call_count == 2
    args = api.audio.transcriptions.create.call_args.kwargs
    assert args['language'] == 'ur' and 'اردو' in args['prompt'] and args['temperature'] == 0


def test_urdu_does_not_display_hindi_after_retry(monkeypatch):
    api = Mock(); api.audio.transcriptions.create.return_value = NS(text='यह हिंदी है')
    monkeypatch.setattr(ai, 'client', lambda: api)
    with pytest.raises(ai.AIError, match='Hindi script instead of Urdu'):
        ai.transcribe_audio(b'RIFF', 'ur')
    assert api.audio.transcriptions.create.call_count == 2


def rate_error(message='', retry_after=None):
    headers = {'retry-after': str(retry_after)} if retry_after is not None else {}
    return RateLimitError('private provider detail', response=httpx.Response(429, request=httpx.Request('POST', 'https://api.groq.com'), headers=headers), body={'error': {'message': message}})


def test_rate_limit_header_and_message_delay():
    assert ai.rate_limit_error(rate_error(retry_after=5.1)).retry_after == 6
    assert ai.rate_limit_error(rate_error('Please try again in 1m2.5s')).retry_after == 63
    assert ai.rate_limit_error(rate_error()).retry_after == 60


@pytest.mark.parametrize('message', ['Tokens per day (TPD) exceeded', 'Daily quota reached', 'Request too large for model'])
def test_nonretryable_limits(message):
    error = ai.rate_limit_error(rate_error(message))
    assert error.retry_after is None
    operation = Mock(side_effect=error)
    wait = Mock()
    with pytest.raises(ai.AIRateLimitError): ai.with_rate_limit_retry(operation, wait)
    assert operation.call_count == 1
    wait.assert_not_called()


def test_short_cooldown_retries_once():
    operation = Mock(side_effect=[ai.AIRateLimitError('Wait', 3), 'saved plan'])
    wait = Mock()
    assert ai.with_rate_limit_retry(operation, wait) == 'saved plan'
    assert operation.call_count == 2
    wait.assert_called_once_with(3)


def test_cooldown_never_loops():
    operation = Mock(side_effect=ai.AIRateLimitError('Wait', 3))
    wait = Mock()
    with pytest.raises(ai.AIRateLimitError): ai.with_rate_limit_retry(operation, wait)
    assert operation.call_count == 2 and wait.call_count == 1
    operation = Mock(side_effect=ai.AIRateLimitError('Wait', 90))
    with pytest.raises(ai.AIRateLimitError): ai.with_rate_limit_retry(operation, wait)
    assert operation.call_count == 1


def test_plan_token_budget_and_reasoning(monkeypatch, plan):
    api = Mock(); api.chat.completions.create.return_value = response(plan)
    monkeypatch.setattr(ai, 'client', lambda: api)
    monkeypatch.setattr(ai, 'configuration', lambda: {'GROQ_MODEL': 'openai/gpt-oss-20b'})
    assert ai.generate_business_plan({}) == plan
    kwargs = api.chat.completions.create.call_args.kwargs
    assert kwargs['max_completion_tokens'] == 3600 and kwargs['reasoning_effort'] == 'low'


def test_repair_does_not_resend_failed_output(monkeypatch, plan):
    api = Mock(); api.chat.completions.create.side_effect = [response('TRUNCATED_OUTPUT' * 100, 'length'), response(plan)]
    monkeypatch.setattr(ai, 'client', lambda: api)
    assert ai.generate_business_plan({}) == plan
    assert 'TRUNCATED_OUTPUT' not in str(api.chat.completions.create.call_args.kwargs['messages'])


def test_plan_validation_accepts_equivalent_punctuation(plan):
    variant = plan.replace('90-Day', '90‑Day').replace('Revenue and Cost', 'Revenue & Cost')
    ai.validate_plan(variant)


def test_plan_prompt_requires_exact_headings():
    prompt = build_prompt('plan', {})
    assert 'VERBATIM' in prompt
    assert all('## ' + heading in prompt for heading in PLAN_SECTIONS)
