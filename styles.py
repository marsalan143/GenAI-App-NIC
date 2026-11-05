import html
import streamlit as st

def apply_styles():
    st.markdown('''<style>
    .vf-hero{background:radial-gradient(ellipse at 95% 10%,#2563eb88,transparent 50%),linear-gradient(120deg,#0b1026,#242052 70%,#133d59);padding:clamp(28px,5vw,70px);border-radius:26px;color:white;margin:12px 0 28px;box-shadow:0 20px 60px #0b10261c}
    .vf-hero h1{color:white;font-size:clamp(2rem,4.2vw,4.3rem);line-height:1.08;letter-spacing:-.045em;max-width:850px}
    .vf-hero p{color:#dbeafe;font-size:1.12rem;max-width:690px;line-height:1.7}
    .vf-eyebrow{font-size:.76rem;letter-spacing:.17em;text-transform:uppercase;font-weight:700;color:#67e8f9;margin-bottom:20px}
    .vf-card{border:1px solid #e2e8f0;background:white;border-radius:20px;padding:25px;margin-bottom:16px;box-shadow:0 8px 25px #0b102608;transition:transform .2s}
    .vf-card:hover{transform:translateY(-3px)}
    .vf-card h3{font-size:1.2rem;color:#0b1026;margin:8px 0 12px}.vf-card p{color:#475569;line-height:1.65}
    .vf-pill{display:inline-block;border-radius:30px;background:#eef2ff;color:#4338ca;padding:5px 12px;font-size:.72rem;font-weight:700;letter-spacing:.05em}
    .vf-investor{background:linear-gradient(125deg,#0b1026,#30205c);padding:32px;border-radius:22px;color:white;margin-bottom:22px}
    .vf-investor h2{color:white}.vf-investor p{color:#c4b5fd}
    .vf-score{background:linear-gradient(110deg,#2563eb,#7c3aed);color:white;border-radius:20px;padding:25px;margin:15px 0}.vf-score strong{font-size:2.6rem;letter-spacing:-.06em}
    .vf-note{color:#64748b;font-size:.82rem;margin-top:24px}
    @media(prefers-reduced-motion:reduce){.vf-card{transition:none}}
    </style>''', unsafe_allow_html=True)

def card(title, text, label=''):
    st.markdown(f'<div class="vf-card"><span class="vf-pill">{html.escape(label)}</span><h3>{html.escape(title)}</h3><p>{html.escape(text)}</p></div>', unsafe_allow_html=True)

def score_box(label, score):
    st.markdown(f'<div class="vf-score">{html.escape(label)}<br><strong>{score}/100</strong><br>Provisional AI assessment</div>', unsafe_allow_html=True)
