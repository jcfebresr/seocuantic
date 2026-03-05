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

# Import utilities (will be added to GitHub)
try:
    from utils.source_detector import SourceDetector
    from utils.data_normalizer import DataNormalizer
    has_utils = True
except:
    has_utils = False

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
    .info-box {
        background-color: #3B82F622;
        border-left: 4px solid #3B82F6;
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
    .source-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        background-color: #8B5CF622;
        border: 1px solid #8B5CF6;
        border-radius: 0.5rem;
        font-weight: bold;
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
if 'df_normalized' not in st.session_state:
    st.session_state.df_normalized = None
if 'source_detected' not in st.session_state:
    st.session_state.source_detected = None
if 'column_mapping' not in st.session_state:
    st.session_state.column_mapping = {}

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
        "source_detected": "Source Detected",
        "column_mapping": "Column Mapping",
        "mapping_confirmed": "Mapping confirmed",
        "normalized_data": "Normalized Data",
        "unique_domains": "unique domains"
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
        "source_detected": "Fuente Detectada",
        "column_mapping": "Mapeo de Columnas",
        "mapping_confirmed": "Mapeo confirmado",
        "normalized_data": "Datos Normalizados",
        "unique_domains": "dominios únicos"
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
    
    lang_display = st.selectbox(
        "🌐 " + t("language"),
        options=['English', 'Español'],
        index=0 if st.session_state.language == 'en' else 1
    )
    st.session_state.language = 'en' if lang_display == 'English' else 'es'
    
    st.divider()
    
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
            
            # === MODULE 2: SOURCE DETECTION ===
            if has_utils:
                source, confidence = SourceDetector.detect_source(df.columns.tolist())
                st.session_state.source_detected = source
                
                source_info = SourceDetector.get_source_info(source)
                
                st.markdown(f"""
                <div class="info-box">
                    <strong>{source_info['icon']} {t('source_detected')}: {source_info['name']}</strong><br>
                    Confidence: {confidence*100:.0f}%
                </div>
                """, unsafe_allow_html=True)
                
                # Column Mapping
                st.subheader(f"🔗 {t('column_mapping')}")
                
                mapping = SourceDetector.map_columns(df.columns.tolist(), source)
                st.session_state.column_mapping = mapping
                
                # Show mapping table
                mapping_df = pd.DataFrame([
                    {"Standard Field": k.upper(), "CSV Column": v or "❌ Not found"}
                    for k, v in mapping.items()
                ])
                
                st.dataframe(mapping_df, use_container_width=True, hide_index=True)
                
                # Normalize button
                if st.button("✨ Normalize Data", type="primary"):
                    df_norm = DataNormalizer.normalize_dataframe(df, mapping)
                    st.session_state.df_normalized = df_norm
                    st.success(f"✅ {t('mapping_confirmed')}")
                    st.rerun()
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
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
            
            with col4:
                if st.session_state.df_normalized is not None and 'domain' in st.session_state.df_normalized.columns:
                    n_domains = st.session_state.df_normalized['domain'].nunique()
                else:
                    n_domains = 0
                
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color: #8B5CF6;">{n_domains}</h3>
                    <p style="margin:0; color: #F1F5F988;">{t('unique_domains')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Show normalized data if available
            if st.session_state.df_normalized is not None:
                st.subheader(f"✨ {t('normalized_data')}")
                st.dataframe(
                    st.session_state.df_normalized.head(100),
                    use_container_width=True,
                    height=400
                )
            else:
                # Show original preview
                st.subheader(t('preview_title'))
                st.dataframe(df.head(100), use_container_width=True, height=400)
            
            # Column info
            with st.expander(f"📋 {t('columns_detected')} ({len(df.columns)})", expanded=False):
                st.write(list(df.columns))
            
        except Exception as e:
            st.error(f"❌ Error loading CSV: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
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
