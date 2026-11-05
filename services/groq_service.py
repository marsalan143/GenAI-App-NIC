"""One SDK client, bounded retries, and validated responses. No fake fallbacks."""
import os
import math
import re
import time
import unicodedata
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq, AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError
from pydantic import ValidationError
from models import Concepts, Feasibility, Questions, Evaluation, ImprovedPlan, Pitch, Canvas
from prompts import SYSTEM, build_prompt, PLAN_SECTIONS

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

class AIError(Exception):
    """Safe, actionable message suitable for display in the UI."""

class AIRateLimitError(AIError):
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


def rate_limit_error(error):
    body = error.body if isinstance(error.body, dict) else {}
    details = body.get('error', body)
    provider_message = str(details.get('message', '')).lower() if isinstance(details, dict) else ''
    if 'request too large' in provider_message:
        return AIRateLimitError('This request exceeds the account token limit. Shorten the input or use an account with a higher token allowance. Waiting alone will not fix an oversized request.')
    if any(term in provider_message for term in ['per day', '(tpd)', '(rpd)', 'daily', 'quota', 'billing']):
        return AIRateLimitError('Groq daily usage or account quota has been reached. Wait for the quota to reset or check your Groq account limits. Your saved startup is unchanged.')
    try:
        seconds = float(error.response.headers.get('retry-after', ''))
    except (ValueError, TypeError):
        match = re.search(r'try again in\s+(?:(\d+(?:\.\d+)?)m)?\s*(?:(\d+(?:\.\d+)?)s)?', provider_message)
        seconds = (float(match[1] or 0) * 60 + float(match[2] or 0)) if match and any(match.groups()) else 60
    if not math.isfinite(seconds):
        seconds = 60
    seconds = max(1, math.ceil(seconds))
    return AIRateLimitError(f'Groq temporary rate limit. Retry in {seconds} seconds. Your saved startup is unchanged.', seconds)


def with_rate_limit_retry(operation, on_wait=None):
    """Retry once after a short provider cooldown; never loop on daily quotas."""
    try:
        return operation()
    except AIRateLimitError as error:
        if error.retry_after is None or error.retry_after > 60:
            raise
        if on_wait:
            on_wait(error.retry_after)
        else:
            time.sleep(error.retry_after)
        return operation()


OUTPUT_TOKENS = {'concepts': 2600, 'plan': 3600, 'improve': 4200,
                 'feasibility': 2200, 'questions': 1200, 'evaluate': 1200,
                 'pitch': 1800, 'canvas': 1800}


def configuration():
    config = {key: os.getenv(key, '') for key in ['GROQ_API_KEY', 'GROQ_MODEL', 'GROQ_TRANSCRIPTION_MODEL']}
    try:
        import streamlit as st
        for key in config:
            config[key] = config[key] or str(st.secrets.get(key, ''))
    except (FileNotFoundError, KeyError):
        pass
    config['GROQ_MODEL'] = config['GROQ_MODEL'] or 'openai/gpt-oss-20b'
    config['GROQ_TRANSCRIPTION_MODEL'] = config['GROQ_TRANSCRIPTION_MODEL'] or 'whisper-large-v3-turbo'
    if config['GROQ_API_KEY'] == 'your_groq_api_key_here':
        config['GROQ_API_KEY'] = ''
    return config

def configured():
    return bool(configuration()['GROQ_API_KEY'])

def client():
    key = configuration()['GROQ_API_KEY']
    if not key:
        raise AIError('Set GROQ_API_KEY in .env or Streamlit secrets, then restart the app.')
    return Groq(api_key=key, timeout=75.0, max_retries=0)

class AITransientError(AIError):
    pass


def safe_call(operation):
    for attempt in range(3):
        try:
            return call_once(operation)
        except AITransientError:
            if attempt == 2:
                raise
            time.sleep(.5 * (2 ** attempt))


def call_once(operation):
    try:
        return operation()
    except AuthenticationError:
        raise AIError('Groq rejected the API key. Check GROQ_API_KEY and restart the app.') from None
    except RateLimitError as error:
        raise rate_limit_error(error) from None
    except APITimeoutError:
        raise AITransientError('Groq timed out. Your saved results are unchanged; please try again.') from None
    except APIConnectionError:
        raise AITransientError('Cannot connect to Groq. Check your internet connection and try again.') from None
    except APIStatusError as error:
        body = error.body if isinstance(error.body, dict) else {}
        details = body.get('error', body)
        code = details.get('code', '') if isinstance(details, dict) else ''
        if error.status_code == 404 or code == 'model_not_found':
            message = 'Groq model unavailable (404). Check GROQ_MODEL or GROQ_TRANSCRIPTION_MODEL against the models available to your account, then restart.'
        elif error.status_code == 403:
            message = 'Groq denied access (403). Check your project permissions and model access.'
        elif error.status_code == 400:
            message = 'Groq rejected this request (400). Check model compatibility or shorten the input and retry.'
        elif error.status_code == 413:
            message = 'Groq rejected the request size (413). Shorten the recording or input.'
        elif error.status_code >= 500:
            raise AITransientError('Groq is temporarily unavailable. Please try again shortly.') from None
        else:
            message = f'Groq could not complete this request (HTTP {error.status_code}). Check your model and account configuration.'
        raise AIError(message) from None

def request(task, data, schema=None):
    api = client()
    messages = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': build_prompt(task, data, schema)}]
    # At most one repair call; safe_call retries transient failures, not rate limits.
    for attempt in range(2):
        kwargs = {'model': configuration()['GROQ_MODEL'], 'messages': messages,
                  'temperature': .5 if task == 'concepts' else .25, 'max_completion_tokens': OUTPUT_TOKENS[task]}
        if kwargs['model'] in ('openai/gpt-oss-20b', 'openai/gpt-oss-120b'):
            kwargs['reasoning_effort'] = 'low'
        if schema:
            kwargs['response_format'] = {'type': 'json_object'}
        response = safe_call(lambda: api.chat.completions.create(**kwargs))
        choice = response.choices[0] if response.choices else None
        content = choice.message.content.strip() if choice and choice.message.content else ''
        try:
            if not content or (choice and choice.finish_reason == 'length'):
                raise ValueError('Empty or truncated output')
            if schema:
                result = schema.model_validate_json(content)
                if task == 'improve':
                    validate_plan(result.markdown)
                return result
            validate_plan(content)
            return content
        except (ValueError, ValidationError) as error:
            if attempt:
                raise AIError('Groq returned incomplete or invalid content twice. Please retry; previous results are preserved.') from None
            issue = 'JSON did not match the requested schema.' if isinstance(error, ValidationError) else str(error)
            messages = messages[:2] + [{'role': 'user', 'content': 'Validation issue: ' + issue + ' Regenerate the complete result with every required section heading verbatim and follow the JSON schema where requested.'}]

def validate_plan(markdown):
    def normalize(text):
        text = unicodedata.normalize('NFKC', text).casefold()
        text = re.sub(r'[\u2010-\u2015\u2212]', '-', text)
        return ' '.join(text.replace('&', ' and ').replace('*', '').split())
    normalized = normalize(markdown)
    missing = [section for section in PLAN_SECTIONS if normalize(section) not in normalized]
    if missing:
        raise ValueError('Missing required business plan headings: ' + '; '.join(missing))

def transcribe_audio(audio_bytes, language=None):
    if not audio_bytes or len(audio_bytes) > 24 * 1024 * 1024:
        raise AIError('Record a short nonempty audio clip under 24 MB, or type your problem below.')
    kwargs = {'file': ('idea.wav', audio_bytes, 'audio/wav'), 'model': configuration()['GROQ_TRANSCRIPTION_MODEL'], 'response_format': 'json'}
    if language:
        kwargs['language'] = language
    if language == 'ur':
        kwargs['prompt'] = 'یہ اردو گفتگو کی نقل ہے، اردو رسم الخط میں، دیوناگری ہندی میں نہیں۔'
    kwargs['temperature'] = 0
    api = client()
    for attempt in range(2):
        result = safe_call(lambda: api.audio.transcriptions.create(**kwargs))
        text = result.text.strip() if result.text else ''
        if not text:
            raise AIError('No speech was transcribed. Please record again or use text input.')
        if language == 'ur' and any('\u0900' <= char <= '\u097f' for char in text):
            if attempt == 0:
                continue
            raise AIError('The speech model returned Hindi script instead of Urdu after retrying. Keep Urdu selected and record a clearer clip, or type your Urdu text below.')
        return text

def generate_startup_concepts(data): return request('concepts', data, Concepts)
def generate_business_plan(data): return request('plan', data)
def analyze_feasibility(data): return request('feasibility', data, Feasibility)
def generate_investor_questions(data): return request('questions', data, Questions)
def evaluate_investor_answer(data): return request('evaluate', data, Evaluation)
def improve_business_plan(data): return request('improve', data, ImprovedPlan)
def generate_pitch_summary(data): return request('pitch', data, Pitch)
def generate_business_model_canvas(data): return request('canvas', data, Canvas)
