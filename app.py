import streamlit as st
import pandas as pd
import chardet
import io
from utils.source_detector import detect_source_and_map
from utils.data_normalizer import normalize_data
from utils.project_identifier import get_domain_stats

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
    .metric-card {
        background-color: #1E293B;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #8B5CF6;
    }
    .success-box {
        background-color: #10B98120;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10B981;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #F59E0B20;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #F59E0B;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #3B82F620;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3B82F6;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'tier' not in st.session_state:
    st.session_state.tier = 'free'
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'df_project' not in st.session_state:
    st.session_state.df_project = None
if 'df_competitors' not in st.session_state:
    st.session_state.df_competitors = []
if 'df_processed' not in st.session_state:
    st.session_state.df_processed = None
if 'categories' not in st.session_state:
    st.session_state.categories = ['Blog', 'Products', 'Services', 'Tools', 'Home', 'About', 'Docs', 'Directory', 'Other']
if 'custom_patterns' not in st.session_state:
    st.session_state.custom_patterns = {}
if 'df_categorized' not in st.session_state:
    st.session_state.df_categorized = None

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/8B5CF6/FFFFFF?text=SEOcuantic", use_container_width=True)
    
    # Language toggle
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🇬🇧 EN", use_container_width=True):
            st.session_state.language = 'en'
            st.rerun()
    with col2:
        if st.button("🇪🇸 ES", use_container_width=True):
            st.session_state.language = 'es'
            st.rerun()
    
    lang = st.session_state.language
    
    st.markdown("---")
    
    # Tier selector
    st.subheader("💎 Plan" if lang == "en" else "💎 Plan")
    tier = st.radio(
        "Select tier:" if lang == "en" else "Selecciona tier:",
        options=['free', 'premium'],
        format_func=lambda x: f"{'🆓 Free' if x == 'free' else '⭐ Premium'}",
        key='tier_selector',
        label_visibility='collapsed'
    )
    st.session_state.tier = tier
    
    # Tier info
    if tier == 'free':
        st.info("**Free Tier**\n- Max 100 URLs\n- Max 2 competitors\n- Basic exports")
    else:
        st.success("**Premium Tier**\n- Unlimited URLs\n- Max 10 competitors\n- AI categorization\n- Intelligence Analysis\n- Advanced exports")
    
    st.markdown("---")
    
    # Stats
    if st.session_state.df_processed is not None:
        st.subheader("📊 Stats" if lang == "en" else "📊 Estadísticas")
        df = st.session_state.df_processed
        
        st.metric("Total Rows" if lang == "en" else "Filas Totales", f"{len(df):,}")
        st.metric("Unique Keywords" if lang == "en" else "Keywords Únicas", f"{df['keyword'].nunique():,}")
        st.metric("Unique Domains" if lang == "en" else "Dominios Únicos", f"{df['domain'].nunique():,}")
        st.metric("Total Traffic" if lang == "en" else "Tráfico Total", f"{df['traffic'].sum():,.0f}")

# Main content
lang = st.session_state.language

st.title("🔮 SEOcuantic Keyword Intelligence")
st.markdown("**v0.6.0** - AI-Powered SEO Analysis" if lang == "en" else "**v0.6.0** - Análisis SEO con IA")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Upload Data" if lang == "en" else "📤 Subir Datos",
    "📁 Categorization" if lang == "en" else "📁 Categorización",
    "🧠 Intelligence" if lang == "en" else "🧠 Inteligencia",
    "📊 Analytics" if lang == "en" else "📊 Análisis"
])

# TAB 1: Upload CSV (mantengo solo lo esencial)
with tab1:
    st.header("📤 Upload Data" if lang == "en" else "📤 Subir Datos")
    st.info("Tab 1 funcionando - completar después")

# TAB 2: Categorization
with tab2:
    st.header("📁 Categorization" if lang == "en" else "📁 Categorización")
    
    if st.session_state.df_processed is None:
        st.warning("⚠️ Upload and process data first (Tab 1)" if lang == "en" else "⚠️ Primero sube y procesa datos (Tab 1)")
    else:
        st.info("Categorization tab - por implementar completamente")

# TAB 3: Intelligence
with tab3:
    st.header("🧠 Intelligence Analysis" if lang == "en" else "🧠 Análisis de Inteligencia")
    
    if st.session_state.tier != 'premium':
        st.warning("⭐ Premium feature" if lang == "en" else "⭐ Función Premium")
    elif st.session_state.df_processed is None:
        st.warning("⚠️ Upload data first" if lang == "en" else "⚠️ Sube datos primero")
    else:
        st.info("Intelligence features: Cannibalization, Content Gaps, Competitive Zones")

# TAB 4: Analytics
with tab4:
    st.header("📊 Analytics & Visualizations" if lang == "en" else "📊 Análisis y Visualizaciones")
    
    if st.session_state.df_processed is None:
        st.warning("⚠️ Upload and process data first" if lang == "en" else "⚠️ Primero sube y procesa datos")
    else:
        from utils.visualizations import SEOVisualizations
        
        df = st.session_state.df_processed
        
        # Chart 1: Traffic by Domain
        st.subheader("🌐 Traffic by Domain" if lang == "en" else "🌐 Tráfico por Dominio")
        fig_domain = SEOVisualizations.traffic_by_domain(df)
        if fig_domain:
            st.plotly_chart(fig_domain, use_container_width=True)
        
        st.markdown("---")
        
        # Chart 2: Top Keywords
        st.subheader("🏆 Top Keywords by Traffic" if lang == "en" else "🏆 Top Keywords por Tráfico")
        top_n = st.slider("Number of keywords" if lang == "en" else "Número de keywords", 10, 50, 20)
        fig_top = SEOVisualizations.top_keywords_chart(df, top_n)
        if fig_top:
            st.plotly_chart(fig_top, use_container_width=True)
