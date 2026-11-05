import streamlit as st
from styles import apply_styles, card

apply_styles()
st.markdown('''<div class="vf-hero"><div class="vf-eyebrow">NIC VentureForge AI · From Problem to Pitch-Ready Startup</div>
<h1>Every Great Startup Begins With a Problem.</h1>
<p>Turn your ideas into real business opportunities with AI. Discover, validate, challenge, and build a startup ready to pitch.</p>
<span class="vf-pill">One problem. Three possibilities. Your next venture.</span></div>''', unsafe_allow_html=True)
left, right = st.columns([1, 3])
with left:
    if st.button('Start Building My Startup', type='primary', use_container_width=True):
        st.switch_page('pages/generator.py')
with right:
    st.markdown('[How It Works](#how-it-works)')
st.markdown('## How It Works', help='A focused journey from a real problem to a pitch-ready plan.')
for col, (title, text, label) in zip(st.columns(3), [
    ('Discover', 'Describe a problem and explore three unique startup concepts.', '01 / EXPLORE'),
    ('Validate', 'Generate a business plan and analyze its feasibility.', '02 / BUILD CONFIDENCE'),
    ('Pitch', 'Face an AI investor challenge and export your startup pitch.', '03 / MAKE YOUR CASE')]):
    with col: card(title, text, label)
st.markdown('## A small incubator. A bigger perspective.')
features = [('Voice-to-Startup Idea', 'Speak in English or Urdu. Edit your transcript and turn it into a brief.'),
            ('Three AI Startup Concepts', 'Compare a lean venture, a technology approach, and a scalable opportunity.'),
            ('AI Feasibility Analyzer', 'Explore five transparent scores and discover the assumptions to validate.'),
            ('Investor Challenge', 'Defend your plan in five rounds, then improve it using the feedback.'),
            ('Startup Pitch Export', 'Download a polished pitch, business canvas, and your assessment in one PDF.')]
cols = st.columns(3)
for i, (title, text) in enumerate(features):
    with cols[i % 3]: card(title, text, f'FEATURE {i + 1:02}')
st.markdown('''<div class="vf-investor"><div class="vf-eyebrow">FROM POSSIBILITY TO PLAN</div><h2>Your Next Big Idea Starts Here.</h2><p>Bring the problem. Build the conviction.</p></div>''', unsafe_allow_html=True)
if st.button('Generate My Startup', type='primary'):
    st.switch_page('pages/generator.py')
st.caption('Built as a student assignment for an NIC brief. No official NIC endorsement is implied. AI output requires real-world validation.')
st.caption('Developed by Muhammad Arsalan · NIC VentureForge AI')
