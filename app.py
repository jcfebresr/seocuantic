import streamlit as st
import pandas as pd
import chardet
import io
from utils.source_detector import detect_source_and_map
from utils.data_normalizer import normalize_data
from utils.project_identifier import (
    get_domain_stats,
    validate_competitors,
    mark_project_domain,
    get_competitor_list
)

# Configuración de página
st.set_page_config(
    page_title="SEOcuantic Keyword Intelligence",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .stApp {
        background-color: #0F172A;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'tier' not in st.session_state:
    st.session_state.tier = 'free'
if 'language' not in st.session_state:
    st.session_state.language = 'en'

st.title("🔮 SEOcuantic Keyword Intelligence")
st.write("v0.3.0")

st.success("✅ Paso 2: Imports de utils funcionan")
