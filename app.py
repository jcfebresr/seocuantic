import streamlit as st
import pandas as pd
import chardet

# Page config
st.set_page_config(
    page_title="SEOcuantic Keyword Intelligence",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0F172A;
        color: #F1F5F9;
    }
    .success-box {
        background-color: #10B98122;
        border-left: 4px solid #10B981;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #F59E0B22;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #1E293B;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #8B5CF644;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'tier' not in st.session_state:
    st.session_state.tier = 'free'
if 'df_raw' not in st.session_state:
    st.session_state.df_raw = None

# Translations
TRANSLATIONS = {
    "en": {
        "app_title": "SEOcuantic Keyword Intelligence",
        "app_subtitle": "Universal URL categorization & SEO gap analysis with AI",
        "language": "Language",
        "tier_free": "Free Tier",
        "tier_premium": "Premium Tier",
        "upgrade_button": "Upgrade to Premium",
        "tab_upload": "📁 1. Upload & Setup",
        "tab_identify": "🎯 2. Identify Your Project",
        "tab_categorize": "🧠 3. Categorization",
        "tab_insights": "📊 4. Insights & Analysis",
        "tab_export": "📥 5. Export & Save",
        "upload_csv": "Upload CSV File",
        "upload_help": "Upload SEranking, Ahrefs, Semrush, GSC or custom CSV",
        "preview_title": "Data Preview",
        "rows_loaded": "rows loaded",
        "success_upload": "CSV loaded successfully",
        "columns_detected": "Columns detected",
        "validation_passed": "Validation passed",
        "tier_limit_warning": "Free tier: Processing first 100 URLs. Upload has {total} URLs."
    },
    "es": {
        "app_title": "SEOcuantic Keyword Intelligence",
        "app_subtitle": "Categorización universal de URLs y análisis de gaps SEO con IA",
        "language": "Idioma",
        "tier_free": "Tier Gratuito",
        "tier_premium": "Tier Premium",
        "upgrade_button": "Mejorar a Premium",
        "tab_upload": "📁 1. Subir & Configurar",
        "tab_identify": "🎯 2. Identificar Tu Proyecto",
        "tab_categorize": "🧠 3. Categorización",
        "tab_insights": "📊 4. Análisis e Insights",
        "tab_export": "📥 5. Exportar & Guardar",
        "upload_csv": "Subir Archivo CSV",
        "upload_help": "Sube CSV de SEranking, Ahrefs, Semrush, GSC o personalizado",
        "preview_title": "Vista Previa de Datos",
        "rows_loaded": "filas cargadas",
        "success_upload": "CSV cargado exitosamente",
        "columns_detected": "Columnas detectadas",
        "validation_passed": "Validación exitosa",
        "tier_limit_warning": "Tier gratuito: Procesando primeras 100 URLs. El archivo tiene {total} URLs."
    }
}

def t(key, **kwargs):
    """Get translation"""
    lang = st.session_state.language
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

# Sidebar
with st.sidebar:
    st.markdown("# 🔮 SEOcuantic")
    
    # Language selector
    lang_display = st.selectbox(
        "🌐 " + t("language"),
        options=['English', 'Español'],
        index=0 if st.session_state.language == 'en' else 1
    )
    st.session_state.language = 'en' if lang_display == 'English' else 'es'
    
    st.divider()
    
    # Tier badge
    tier_label = t("tier_free" if st.session_state.tier == 'free' else "tier_premium")
    tier_color = "#F59E0B" if st.session_state.tier == 'free' else "#10B981"
    
    st.markdown(f"""
    <div style="background-color: {tier_color}22; border-left: 4px solid {tier_color}; padding: 0.75rem; border-radius: 0.5rem;">
        <strong>📊 {tier_label}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.tier == 'free':
        if st.button("⭐ " + t("upgrade_button"), use_container_width=True):
            st.info("💡 Premium features coming soon!")
    
    st.divider()
    st.caption(t('app_subtitle'))

# Main content
st.title(t('app_title'))
st.markdown(f"<p style='color: #F1F5F988;'>{t('app_subtitle')}</p>", unsafe_allow_html=True)
st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    t('tab_upload'),
    t('tab_identify'),
    t('tab_categorize'),
    t('tab_insights'),
    t('tab_export')
])

# TAB 1: Upload & Setup
with tab1:
    st.header(t('tab_upload'))
    
    uploaded_file = st.file_uploader(
        t('upload_csv'),
        type=['csv'],
        help=t('upload_help')
    )
    
    if uploaded_file:
        try:
            # Auto-detect encoding
            raw_data = uploaded_file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
            uploaded_file.seek(0)
            
            # Read CSV
            df = pd.read_csv(uploaded_file, encoding=encoding)
            df.columns = df.columns.str.strip()
            
            st.session_state.df_raw = df
            
            # Success message
            st.markdown(f"""
            <div class="success-box">
                ✅ <strong>{t('success_upload')}</strong><br>
                {len(df):,} {t('rows_loaded')}
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color: #8B5CF6;">{len(df):,}</h3>
                    <p style="margin:0; color: #F1F5F988;">Total Rows</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color: #8B5CF6;">{len(df.columns)}</h3>
                    <p style="margin:0; color: #F1F5F988;">Columns</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color: #8B5CF6;">{encoding.upper()}</h3>
                    <p style="margin:0; color: #F1F5F988;">Encoding</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Tier limit check
            max_urls = 100 if st.session_state.tier == 'free' else float('inf')
            
            if len(df) > max_urls:
                st.markdown(f"""
                <div class="warning-box">
                    ⚠️ {t('tier_limit_warning', total=len(df))}<br>
                    <a href="#" style="color: #8B5CF6; text-decoration: none;">
                        🚀 Unlock full processing
                    </a>
                </div>
                """, unsafe_allow_html=True)
                df_preview = df.head(max_urls)
            else:
                df_preview = df
            
            # Columns detected
            with st.expander(f"📋 {t('columns_detected')} ({len(df.columns)})", expanded=False):
                st.write(list(df.columns))
            
            # Data preview
            st.subheader(t('preview_title'))
            st.dataframe(df_preview.head(100), use_container_width=True, height=400)
            
            # Column stats
            with st.expander("📊 Column Statistics", expanded=False):
                col_stats = pd.DataFrame({
                    'Column': df.columns,
                    'Type': [str(dtype) for dtype in df.dtypes],
                    'Null Count': [df[col].isnull().sum() for col in df.columns],
                    'Null %': [round(df[col].isnull().sum() / len(df) * 100, 1) for col in df.columns]
                })
                st.dataframe(col_stats, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error loading CSV: {str(e)}")
    
    else:
        st.info("ℹ️ Please upload a CSV file to begin" if st.session_state.language == 'en' else "ℹ️ Por favor sube un archivo CSV para comenzar")
        
        # Example
        st.markdown("---")
        st.markdown("**Example CSV format:**" if st.session_state.language == 'en' else "**Formato CSV de ejemplo:**")
        example_df = pd.DataFrame({
            'keyword': ['seo tools', 'keyword research', 'backlink checker'],
            'url': ['example.com/tools', 'example.com/blog/research', 'example.com/backlinks'],
            'volume': [1000, 800, 500],
            'traffic': [150, 120, 80],
            'position': [3, 5, 8]
        })
        st.dataframe(example_df, use_container_width=True)

# TAB 2-5: Placeholders
with tab2:
    st.info("🚧 Module 2: Project identification - Coming soon" if st.session_state.language == 'en' else "🚧 Módulo 2: Identificación de proyecto - Próximamente")

with tab3:
    st.info("🚧 Module 3: Categorization - Coming soon" if st.session_state.language == 'en' else "🚧 Módulo 3: Categorización - Próximamente")

with tab4:
    st.info("🚧 Module 4: Insights & Analysis - Coming soon" if st.session_state.language == 'en' else "🚧 Módulo 4: Análisis e Insights - Próximamente")

with tab5:
    st.info("🚧 Module 5: Export & Save - Coming soon" if st.session_state.language == 'en' else "🚧 Módulo 5: Exportar y Guardar - Próximamente")
