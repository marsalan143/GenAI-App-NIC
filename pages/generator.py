"""The complete workflow lives on this page. Each button makes at most one AI task."""
import hashlib
import time
import streamlit as st
import pandas as pd
import altair as alt
from pydantic import ValidationError
from services import groq_service as ai
from services.pdf_service import create_pdf, pitch_pack_markdown
from styles import apply_styles, card, score_box
from utils import (initialize, reset, accept_concepts, select_concept, clear_plan_results,
                   validate_input, context, serializable, WEIGHTS, LABELS, DISCLAIMER,
                   feasibility_score, investor_score, record_answer)

apply_styles()
s = st.session_state
initialize(s)
if 'pending_stage' in s:
    s['stage'] = s.pop('pending_stage')
STAGES = ['Discover', 'Choose Idea', 'Business Plan', 'Feasibility', 'Investor Challenge', 'Export Pitch']

def goto(stage):
    # Apply on the next run, before the navigation widget is instantiated.
    s['pending_stage'] = stage

def wait_for_groq(seconds):
    notice = st.empty()
    for remaining in range(seconds, 0, -1):
        notice.info(f'Groq is temporarily busy. Retrying automatically in {remaining} seconds. Your startup is saved.')
        time.sleep(1)
    notice.empty()


def action(label, function):
    try:
        with st.spinner(label):
            return ai.with_rate_limit_retry(function, on_wait=wait_for_groq)
    except ai.AIRateLimitError as error:
        st.warning(str(error))
    except ai.AIError as error:
        st.error(str(error))
    except ValidationError:
        st.error('Enter a problem or theme of at least 3 characters and a market of at least 2 characters. Keep the problem under 6,000 characters.')
    except (ValueError, OSError):
        st.error('The request or export could not be completed. Your saved results are preserved; please retry.')
    return None

def bullets(title, items):
    st.markdown('#### ' + title)
    for item in items:
        st.markdown('- ' + item)

def feedback_view(feedback):
    st.metric('Answer score', f'{feedback.score}/10')
    for title, key in [('Answered well', 'answered_well'), ('Weaknesses', 'weaknesses'), ('Missing evidence', 'missing_evidence'), ('Practical suggestions', 'suggestions')]:
        bullets(title, getattr(feedback, key))

top, controls = st.columns([4, 1])
with top:
    st.caption('NIC VENTUREFORGE AI / YOUR VENTURE WORKSPACE')
    st.title('Build something that matters.')
    st.write('A focused journey from the problem you see to the pitch you can defend.')
with controls:
    st.button('Start New Startup', on_click=reset, args=(s,), use_container_width=True)
if not ai.configured():
    st.info('Add GROQ_API_KEY to .env and restart to enable AI and voice transcription. You can explore both pages without a key.')
completed = sum([bool(s['concepts']), bool(s['selected']), bool(s['original_plan']), bool(s['feasibility']), len(s['interview']) == 5, bool(s['pitch_pdf'])])
st.progress(completed / 6, text=f'{completed} of 6 milestones complete')
st.radio('Your startup journey', STAGES, horizontal=True, key='stage')
st.divider()

if s['stage'] == 'Discover':
    st.header('01 / Start with a real problem')
    st.write('Type a problem, a few keywords, or a theme. You can also speak your idea first.')
    with st.expander('Record Your Idea · English or Urdu', expanded=False):
        st.caption('Allow microphone access in your browser. If recording is unavailable, the text box below always works. Audio and text are sent to Groq only when you submit them.')
        language = st.selectbox('Speech language', ['Urdu', 'English', 'Auto detect'])
        st.caption('For Urdu script (اردو), keep Urdu selected. Auto detect may confuse Urdu and Hindi.')
        audio = st.audio_input('Record Your Idea', key='recording_idea')
        if st.button('Transcribe Recording', disabled=audio is None):
            raw = audio.getvalue()
            digest = hashlib.sha256(raw + language.encode()).hexdigest()
            if digest == s['audio_digest']:
                st.info('This recording is already transcribed. Edit the problem below or record a new clip.')
            else:
                result = action('Transcribing your recording…', lambda: ai.transcribe_audio(raw, {'English': 'en', 'Urdu': 'ur'}.get(language)))
                if result:
                    s['voice_transcript'] = result
                    s['problem'] = result
                    s['audio_digest'] = digest
                    st.success('Transcribed. Review and edit the problem below before generating ideas.')
        if s['voice_transcript']:
            st.caption('Original voice transcript')
            st.write(s['voice_transcript'])
    with st.form('startup_brief'):
        st.text_area('What problem are you trying to solve?', key='problem', height=130,
                     placeholder='Students in Karachi struggle to find affordable and reliable transport.', max_chars=6000)
        a, b = st.columns(2)
        with a:
            st.multiselect('Industry / theme', ['Education', 'Healthcare', 'Technology', 'Ecommerce', 'Agriculture', 'Environment', 'Transportation', 'Finance', 'Social Impact', 'Artificial Intelligence', 'Other'], key='themes')
            st.text_input('Custom theme (optional)', key='custom_theme', max_chars=120)
            st.text_input('Target audience (optional)', key='audience', max_chars=300)
        with b:
            st.text_input('Country / market', key='market', max_chars=120)
            st.text_input('Startup budget (optional, include currency)', key='budget', placeholder='e.g. PKR 500,000', max_chars=200)
        submitted = st.form_submit_button('Generate 3 Startup Ideas', type='primary')
    if submitted:
        themes = s['themes'] + ([s['custom_theme'].strip()] if s['custom_theme'].strip() else [])
        problem = s['problem'].strip() or ', '.join(themes)
        data = action('Checking your brief…', lambda: validate_input(problem, themes, s['audience'], s['market'], s['budget']))
        if data:
            result = action('Exploring three different approaches…', lambda: ai.generate_startup_concepts(data.model_dump()))
            if result:
                accept_concepts(s, data, result.concepts)
                goto('Choose Idea')
                st.rerun()
    if s['concepts']:
        st.button('View Existing Concepts', on_click=goto, args=('Choose Idea',))

elif s['stage'] == 'Choose Idea':
    st.header('02 / Three routes. One decision.')
    if not s['concepts']:
        st.info('Describe your problem in Discover to generate your three concepts.')
    else:
        st.caption('All budgets are illustrative estimates. Compare operating models and risks before choosing.')
        for col, concept in zip(st.columns(3), s['concepts']):
            with col:
                card(concept.name, concept.tagline, concept.approach)
                with st.container(border=True):
                    for label, key in [('Problem', 'problem'), ('Solution', 'solution'), ('Customers', 'customers'), ('Unique selling point', 'usp'), ('Revenue model', 'revenue_model'), ('Estimated initial budget', 'budget')]:
                        st.markdown(f'**{label}**')
                        st.write(getattr(concept, key))
                    bullets('Main risks', concept.risks)
                    selected = s['selected'] == concept
                    if st.button('Selected · Continue' if selected else 'Select This Idea', key='select_' + concept.approach, type='primary' if selected else 'secondary', use_container_width=True):
                        select_concept(s, concept)
                        goto('Business Plan')
                        st.rerun()
        st.dataframe([{'Approach': c.approach, 'Startup': c.name, 'Estimated budget': c.budget, 'Revenue model': c.revenue_model} for c in s['concepts']], hide_index=True, use_container_width=True)

elif s['stage'] == 'Business Plan':
    st.header('03 / Give your startup a blueprint')
    if not s['selected']:
        st.info('Select a startup in Choose Idea first.')
    else:
        st.subheader(s['selected'].name)
        st.caption('Regenerating a successful plan clears its previous feasibility, interview, revisions and exports.')
        if st.button('Regenerate Business Plan' if s['original_plan'] else 'Generate Business Plan', type='primary'):
            result = action('Building your complete business plan…', lambda: ai.generate_business_plan(context(s)))
            if result:
                clear_plan_results(s)
                s['original_plan'] = result
                st.rerun()
        if s['original_plan']:
            st.warning('Planning assumptions: market figures, competitor claims and financial forecasts require independent validation.')
            st.markdown(s['original_plan'])
            st.download_button('Download Markdown', s['original_plan'], 'business-plan.md', 'text/markdown', on_click='ignore')
            st.button('Continue to Feasibility', on_click=goto, args=('Feasibility',), type='primary')

elif s['stage'] == 'Feasibility':
    st.header('04 / Test the business behind the idea')
    if not s['original_plan']:
        st.info('Generate a business plan first.')
    else:
        st.caption('Assesses the original plan. Higher scores mean stronger positioning, more practical investment, easier implementation, and better scalability.')
        if st.button('Reanalyze My Startup' if s['feasibility'] else 'Analyze My Startup', type='primary'):
            result = action('Examining five dimensions of feasibility…', lambda: ai.analyze_feasibility(context(s)))
            if result:
                s['feasibility'] = result
                s['pitch_pdf'] = None
                s['improved'] = None
        if s['feasibility']:
            f = s['feasibility']
            score_box('Startup Feasibility', feasibility_score(f))
            st.caption(DISCLAIMER)
            st.write(f.summary)
            left, right = st.columns(2)
            with left:
                for key, weight in WEIGHTS.items():
                    rating = getattr(f, key)
                    st.progress(rating.score / 100, text=f'{LABELS[key]} · {rating.score:g}/100 · weight {weight:.0%}')
                    st.caption(rating.reasoning)
            with right:
                data = pd.DataFrame([{'Category': LABELS[k], 'Score': getattr(f, k).score} for k in WEIGHTS])
                chart = alt.Chart(data).mark_bar(cornerRadiusEnd=8).encode(
                    x=alt.X('Score:Q', scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y('Category:N', sort=list(LABELS.values()), title=None),
                    color=alt.Color('Category:N', legend=None, scale=alt.Scale(range=['#2563EB', '#06B6D4', '#7C3AED', '#10B981', '#F59E0B'])),
                    tooltip=['Category', 'Score']).properties(height=310)
                st.altair_chart(chart, use_container_width=True)
            cols = st.columns(2)
            for i, (label, key) in enumerate([('Strengths', 'strengths'), ('Weaknesses', 'weaknesses'), ('Major risks', 'risks'), ('AI recommendations', 'recommendations'), ('Validate before investing', 'assumptions_to_validate')]):
                with cols[i % 2]: bullets(label, getattr(f, key))
            st.button('Enter Investor Challenge', on_click=goto, args=('Investor Challenge',), type='primary')

elif s['stage'] == 'Investor Challenge':
    st.markdown('<div class="vf-investor"><div class="vf-eyebrow">THE PITCH ROOM</div><h2>The Investor Challenge</h2><p>Your idea sounds promising. But can you defend it?</p></div>', unsafe_allow_html=True)
    st.caption('Simulated AI investor, not a real investment panel. Scores are educational estimates based on the original plan.')
    if not s['original_plan']:
        st.info('Generate a business plan to enter the pitch room.')
    else:
        if not s['questions']:
            if st.button('Challenge My Idea', type='primary'):
                result = action('Preparing five questions for your startup…', lambda: ai.generate_investor_questions(context(s)))
                if result:
                    s['questions'] = result.questions
                    st.rerun()
        else:
            index = s['question_index']
            st.progress(len(s['interview']) / 5, text=f'{len(s["interview"])} of 5 answers evaluated')
            if index < 5:
                question = s['questions'][index]
                st.caption(f'ROUND {index + 1} / 5 · {question.category.upper()}')
                st.subheader(question.question)
                already = index < len(s['interview'])
                if already:
                    st.write('**Your answer**')
                    st.write(s['interview'][index]['answer'])
                    feedback_view(s['interview'][index]['feedback'])
                    if st.button('View Results' if index == 4 else 'Next Question', type='primary'):
                        s['question_index'] += 1
                        st.rerun()
                else:
                    with st.form(f'investor_answer_{index}'):
                        answer = st.text_area('Your answer', key=f'answer_{index}', max_chars=5000, height=150, placeholder='Explain your reasoning and evidence. Be specific about what you have and have not validated.')
                        submit = st.form_submit_button('Submit My Answer', type='primary')
                    if submit:
                        if not answer.strip():
                            st.error('Please enter an answer before submitting.')
                        else:
                            data = {**context(s), 'question': question.model_dump(), 'answer': answer.strip()}
                            result = action('Your simulated investor is reviewing the answer…', lambda: ai.evaluate_investor_answer(data))
                            if result:
                                record_answer(s, index, answer, result)
                                st.rerun()
            if index >= 5:
                st.header('Investor Challenge Results')
                score_box('Pitch readiness', investor_score(s['interview']))
                st.caption('Readiness = sum of five answer scores / 50 × 100. Each answer uses evidence (4), reasoning (3), and specificity (3).')
                for i, item in enumerate(s['interview'], 1):
                    with st.expander(f'Question {i} · {item["question"].category} · {item["feedback"].score}/10'):
                        st.write(item['question'].question)
                        st.write('**Your answer:** ' + item['answer'])
                        feedback_view(item['feedback'])
                cols = st.columns(3)
                for col, label, key in zip(cols, ['Strengths', 'Weaknesses', 'Investor recommendations'], ['answered_well', 'weaknesses', 'suggestions']):
                    with col: bullets(label, list(dict.fromkeys(x for item in s['interview'] for x in getattr(item['feedback'], key))))
                if not s['feasibility']:
                    st.info('For a stronger revision, complete Feasibility first. Unassessed feasibility will be marked as such.')
                if st.button('Improve My Startup Plan', type='primary'):
                    data = {**context(s), 'feasibility': serializable(s['feasibility']), 'interview': serializable(s['interview'])}
                    result = action('Revising your plan using the evidence and feedback…', lambda: ai.improve_business_plan(data))
                    if result:
                        s['improved'] = result
                        s['pitch_pdf'] = None
                        s['pitch'] = None
                        s['canvas'] = None
                        s['pitch_source'] = None
                if s['improved']:
                    bullets('Summary of Improvements', s['improved'].changes)
                    original, improved = st.columns(2)
                    with original:
                        st.subheader('Original Plan')
                        st.markdown(s['original_plan'])
                    with improved:
                        st.subheader('Improved Plan')
                        st.markdown(s['improved'].markdown)
                st.button('Continue to Export', on_click=goto, args=('Export Pitch',))
            if s['interview'] and index < 5:
                with st.expander('Previous answers and feedback'):
                    for i, item in enumerate(s['interview']):
                        st.markdown(f'**Round {i + 1}: {item["question"].question}**')
                        st.write(item['answer'])
                        feedback_view(item['feedback'])

elif s['stage'] == 'Export Pitch':
    st.header('06 / Make your next conversation count')
    if not s['original_plan']:
        st.info('Generate a business plan first. Feasibility and the Investor Challenge are optional for export.')
    else:
        choices = ['Original plan'] + (['Improved plan'] if s['improved'] else [])
        source = st.radio('Plan version to export', choices)
        plan = s['improved'].markdown if source == 'Improved plan' else s['original_plan']
        st.caption('Prepare the AI pitch summary and nine-block canvas once, then download the complete Pitch Pack in one click. Assessments always refer to the original plan.')
        if source != s['pitch_source']:
            s.update(pitch=None, canvas=None, pitch_pdf=None, pitch_source=source)
        if not s['pitch'] or not s['canvas']:
            if st.button('Prepare Pitch Summary & Canvas', type='primary'):
                data = context(s, improved=source == 'Improved plan')
                if not s['pitch']:
                    result = action('Writing your investor pitch summary…', lambda: ai.generate_pitch_summary(data))
                    if result: s['pitch'] = result
                if s['pitch'] and not s['canvas']:
                    result = action('Building your Business Model Canvas…', lambda: ai.generate_business_model_canvas(data))
                    if result: s['canvas'] = result
                if s['pitch'] and s['canvas']: st.rerun()
        if s['pitch'] and s['canvas']:
            if not s['pitch_pdf']:
                s['pitch_pdf'] = action('Formatting your pitch pack…', lambda: create_pdf('Startup Pitch Pack', s['selected'].name,
                    pitch_pack_markdown(s['pitch'], s['canvas'], s['feasibility'], s['interview'], source)))
            if s['pitch_pdf']:
                st.download_button('Download Startup Pitch Pack', s['pitch_pdf'], 'startup-pitch-pack.pdf', 'application/pdf', type='primary', on_click='ignore')
            with st.expander('Investor Pitch Summary', expanded=True):
                for key, value in s['pitch'].model_dump().items():
                    st.markdown(f'**{key.replace("_", " ").title()}**')
                    st.write(value)
            st.subheader('Business Model Canvas')
            cols = st.columns(3)
            for i, (key, values) in enumerate(s['canvas'].model_dump().items()):
                with cols[i % 3]:
                    with st.container(border=True): bullets(key.replace('_', ' ').title(), values)
        st.divider()
        st.subheader('Complete Business Plan')
        st.caption('Available immediately, even without feasibility or investor results.')
        pdf = action('Formatting your complete plan…', lambda: create_pdf('Complete Startup Business Plan', s['selected'].name, plan))
        if pdf:
            st.download_button('Download Complete Business Plan PDF', pdf, 'complete-business-plan.pdf', 'application/pdf', on_click='ignore')
        st.download_button('Download Plan Markdown', plan, 'startup-plan.md', 'text/markdown', on_click='ignore')

st.caption('NIC VentureForge AI · AI assists the thinking. You validate the opportunity. Session data is kept only for this browser session.')
st.caption('Developed by Muhammad Arsalan · NIC VentureForge AI')
