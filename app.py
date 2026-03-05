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

# Import utilities
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
if 'df_processed' not in st.session_state:
    st.session_state.df_processed = None
if 'source_detected' not in st.session_state:
    st.session_state.source_detected = None

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
        "success_upload": "CSV processed successfully",
        "source_detected": "Detected",
        "unique_domains": "unique domains",
        "rows_skipped": "rows skipped (malformed)"
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
        "success_upload": "CSV procesado exitosamente",
        "source_detected": "Detectado",
        "unique_domains": "dominios únicos",
        "rows_skipped": "filas omitidas (mal formadas)"
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
            
            # Read CSV with robust parsing - detect separator
            import io
            
            # Detect separator (tab, comma, semicolon)
            uploaded_file.seek(0)
            sample = uploaded_file.read(2000).decode(encoding)
            uploaded_file.seek(0)
            
            # Count separators in first line
            first_line = sample.split('\n')[0]
            sep_counts = {
                '\t': first_line.count('\t'),
                ',': first_line.count(','),
                ';': first_line.count(';')
            }
            detected_sep = max(sep_counts, key=sep_counts.get)
            
            try:
                # Try with detected separator
                df_raw = pd.read_csv(
                    uploaded_file, 
                    encoding=encoding,
                    sep=detected_sep,
                    on_bad_lines='skip'
                )
                rows_skipped = 0
            except:
                # Fallback to auto-detect
                uploaded_file.seek(0)
                df_raw = pd.read_csv(
                    uploaded_file, 
                    encoding=encoding,
                    on_bad_lines='skip',
                    engine='python',
                    sep=None
                )
                rows_skipped = 0
            
            df_raw.columns = df_raw.columns.str.strip()
            
            # === AUTO PROCESSING (SILENT) ===
            if has_utils:
                # Detect source
                source, confidence = SourceDetector.detect_source(df_raw.columns.tolist())
                st.session_state.source_detected = source
                source_info = SourceDetector.get_source_info(source)
                
                # Auto-map columns
                mapping = SourceDetector.map_columns(df_raw.columns.tolist(), source)
                
                # Auto-normalize
                df_processed = DataNormalizer.normalize_dataframe(df_raw, mapping)
                st.session_state.df_processed = df_processed
            else:
                # Fallback if utils not available
                df_processed = df_raw
                st.session_state.df_processed = df_processed
                source_info = {"name": "Unknown", "icon": "❓"}
            
            # Success message with source badge
            success_msg = f"""
            <div class="success-box">
                ✅ <strong>{t('success_upload')}</strong><br>
                {len(df_processed):,} {t('rows_loaded')} • {source_info['icon']} {t('source_detected')}: {source_info['name']}
            """
            
            if rows_skipped > 0:
                success_msg += f"<br>⚠️ {rows_skipped} {t('rows_skipped')}"
            
            success_msg += "</div>"
            
            st.markdown(success_msg, unsafe_allow_html=True)
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color: #8B5CF6;">{len(df_processed):,}</h3>
                    <p style="margin:0; color: #F1F5F988;">Total Rows</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                n_keywords = df_processed['keyword'].nunique() if 'keyword' in df_processed.columns else 0
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color: #8B5CF6;">{n_keywords:,}</h3>
                    <p style="margin:0; color: #F1F5F988;">Unique Keywords</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                n_domains = df_processed['domain'].nunique() if 'domain' in df_processed.columns else 0
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color: #8B5CF6;">{n_domains}</h3>
                    <p style="margin:0; color: #F1F5F988;">{t('unique_domains').title()}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                total_traffic = int(df_processed['traffic'].sum()) if 'traffic' in df_processed.columns else 0
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color: #8B5CF6;">{total_traffic:,}</h3>
                    <p style="margin:0; color: #F1F5F988;">Total Traffic</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Data preview
            st.subheader(t('preview_title'))
            st.dataframe(
                df_processed.head(100),
                use_container_width=True,
                height=400
            )
            
            # Column stats
            with st.expander("📊 Column Statistics", expanded=False):
                col_stats = pd.DataFrame({
                    'Column': df_processed.columns,
                    'Type': [str(dtype) for dtype in df_processed.dtypes],
                    'Null Count': [df_processed[col].isnull().sum() for col in df_processed.columns],
                    'Null %': [round(df_processed[col].isnull().sum() / len(df_processed) * 100, 1) for col in df_processed.columns]
                })
                st.dataframe(col_stats, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error loading CSV: {str(e)}")
            with st.expander("🔍 Show full error trace"):
                import traceback
                st.code(traceback.format_exc())
    
    else:
        st.info("ℹ️ Please upload a CSV file to begin" if st.session_state.language == 'en' else "ℹ️ Por favor sube un archivo CSV para comenzar")
        
        # Example
        st.markdown("---")
        st.markdown("**Example CSV format:**" if st.session_state.language == 'en' else "**Formato CSV de ejemplo:**")
        example_df = pd.DataFrame({
            'Keyword': ['seo tools', 'keyword research', 'backlink checker'],
            'URL': ['example.com/tools', 'example.com/blog/research', 'example.com/backlinks'],
            'Search vol.': [1000, 800, 500],
            'Traffic': [150, 120, 80],
            'Position': [3, 5, 8]
        })
        st.dataframe(example_df, use_container_width=True)

# TAB 2-5: Placeholders
with tab2:
    if st.session_state.df_processed is not None:
        st.success("✅ Ready for project identification")
        st.info("🚧 Coming in Module 3")
    else:
        st.info("⬅️ Upload CSV first")

with tab3:
    st.info("🚧 Module 3: Categorization - Coming soon" if st.session_state.language == 'en' else "🚧 Módulo 3: Categorización - Próximamente")

with tab4:
    st.info("🚧 Module 4: Insights & Analysis - Coming soon" if st.session_state.language == 'en' else "🚧 Módulo 4: Análisis e Insights - Próximamente")

with tab5:
    st.info("🚧 Module 5: Export & Save - Coming soon" if st.session_state.language == 'en' else "🚧 Módulo 5: Exportar y Guardar - Próximamente")
