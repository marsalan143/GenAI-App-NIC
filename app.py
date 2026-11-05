import streamlit as st
from styles import apply_styles
from utils import initialize

st.set_page_config(page_title='NIC VentureForge AI', page_icon='✦', layout='wide')
apply_styles()
initialize(st.session_state)
page = st.navigation([
    st.Page('pages/landing.py', title='Welcome', icon=':material/auto_awesome:', default=True),
    st.Page('pages/generator.py', title='Startup Idea Generator', icon=':material/rocket_launch:', url_path='generator'),
], position='top')
page.run()
