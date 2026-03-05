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
        st.success("**Premium Tier**\n- Unlimited URLs\n- Max 10 competitors\n- AI categorization\n- Advanced exports")
    
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
st.markdown("**v0.3.0** - AI-Powered SEO Analysis" if lang == "en" else "**v0.3.0** - Análisis SEO con IA")

# Tabs
tab1, tab2 = st.tabs([
    "📤 Upload Data" if lang == "en" else "📤 Subir Datos",
    "📁 Categorization" if lang == "en" else "📁 Categorización"
])

# TAB 1: Upload CSV
with tab1:
    st.header("📤 Upload Data" if lang == "en" else "📤 Subir Datos")
    
    st.markdown(f"""
    <div class="info-box">
        <strong>{"ℹ️ Upload Strategy:" if lang == "en" else "ℹ️ Estrategia de Subida:"}</strong><br>
        {"1. Upload YOUR project CSV first" if lang == "en" else "1. Sube el CSV de TU proyecto primero"}<br>
        {"2. Then upload competitor CSVs (optional)" if lang == "en" else "2. Luego sube CSVs de competidores (opcional)"}
    </div>
    """, unsafe_allow_html=True)
    
    # Sección 1: CSV del Proyecto
    st.subheader("🏠 Your Project CSV" if lang == "en" else "🏠 CSV de Tu Proyecto")
    
    project_file = st.file_uploader(
        "Upload your project keywords CSV" if lang == "en" else "Sube el CSV de keywords de tu proyecto",
        type=['csv'],
        key='project_uploader',
        help="Main CSV with your website's keywords" if lang == "en" else "CSV principal con las keywords de tu sitio"
    )
    
    if project_file is not None:
        try:
            # Detectar encoding
            raw_data = project_file.read()
            detected = chardet.detect(raw_data)
            encoding = detected['encoding']
            
            # Leer CSV
            project_file.seek(0)
            
            # Intentar leer con diferentes separadores
            separators = [',', '\t', ';']
            df_raw = None
            
            for sep in separators:
                try:
                    project_file.seek(0)
                    df_raw = pd.read_csv(
                        project_file,
                        encoding=encoding,
                        sep=sep,
                        on_bad_lines='skip',
                        engine='python'
                    )
                    if len(df_raw.columns) > 1:
                        break
                except:
                    continue
            
            if df_raw is not None and len(df_raw) > 0:
                # Auto-detectar fuente y normalizar
                source, df_mapped = detect_source_and_map(df_raw)
                
                if df_mapped is not None:
                    df_normalized = normalize_data(df_mapped)
                    
                    # Validar tier limits
                    if st.session_state.tier == 'free' and len(df_normalized) > 100:
                        st.warning(f"⚠️ Free tier: 100 URLs max. Trimmed." if lang == "en" else f"⚠️ Tier gratuito: máximo 100 URLs. Recortado.")
                        df_normalized = df_normalized.head(100)
                    
                    # Marcar como proyecto
                    if 'domain' in df_normalized.columns:
                        df_normalized['is_client'] = True
                    
                    st.session_state.df_project = df_normalized
                    
                    st.success(f"✅ Project CSV loaded: {len(df_normalized)} rows" if lang == "en" else f"✅ CSV del proyecto cargado: {len(df_normalized)} filas")
                    
                    # Preview
                    with st.expander("📋 Preview" if lang == "en" else "📋 Vista Previa"):
                        st.dataframe(df_normalized.head(50), use_container_width=True)
        
        except Exception as e:
            st.error(f"❌ Error loading project CSV" if lang == "en" else f"❌ Error cargando CSV del proyecto")
    
    st.markdown("---")
    
    # Sección 2: CSVs de Competidores
    st.subheader("🎯 Competitor CSVs (Optional)" if lang == "en" else "🎯 CSVs de Competidores (Opcional)")
    
    # Tier limits
    tier = st.session_state.tier
    max_competitors = 2 if tier == 'free' else 10
    current_competitors = len(st.session_state.df_competitors)
    
    st.info(f"📊 {current_competitors}/{max_competitors} competitors loaded" if lang == "en" else f"📊 {current_competitors}/{max_competitors} competidores cargados")
    
    if current_competitors < max_competitors:
        competitor_file = st.file_uploader(
            f"Upload competitor CSV ({current_competitors + 1}/{max_competitors})" if lang == "en" else f"Sube CSV de competidor ({current_competitors + 1}/{max_competitors})",
            type=['csv'],
            key=f'competitor_uploader_{current_competitors}',
            help="CSV with competitor keywords" if lang == "en" else "CSV con keywords de competidor"
        )
        
        if competitor_file is not None:
            try:
                # Detectar encoding
                raw_data = competitor_file.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding']
                
                # Leer CSV
                competitor_file.seek(0)
                
                separators = [',', '\t', ';']
                df_raw = None
                
                for sep in separators:
                    try:
                        competitor_file.seek(0)
                        df_raw = pd.read_csv(
                            competitor_file,
                            encoding=encoding,
                            sep=sep,
                            on_bad_lines='skip',
                            engine='python'
                        )
                        if len(df_raw.columns) > 1:
                            break
                    except:
                        continue
                
                if df_raw is not None and len(df_raw) > 0:
                    source, df_mapped = detect_source_and_map(df_raw)
                    
                    if df_mapped is not None:
                        df_normalized = normalize_data(df_mapped)
                        
                        # Marcar como competidor
                        if 'domain' in df_normalized.columns:
                            df_normalized['is_client'] = False
                        
                        st.session_state.df_competitors.append(df_normalized)
                        
                        st.success(f"✅ Competitor CSV loaded: {len(df_normalized)} rows" if lang == "en" else f"✅ CSV de competidor cargado: {len(df_normalized)} filas")
                        st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error loading competitor CSV" if lang == "en" else f"❌ Error cargando CSV de competidor")
    else:
        st.warning(f"⚠️ Max competitors reached ({max_competitors})" if lang == "en" else f"⚠️ Máximo de competidores alcanzado ({max_competitors})")
    
    # Mostrar competidores cargados
    if len(st.session_state.df_competitors) > 0:
        st.markdown("#### Loaded Competitors:" if lang == "en" else "#### Competidores Cargados:")
        for i, df_comp in enumerate(st.session_state.df_competitors):
            col1, col2 = st.columns([4, 1])
            with col1:
                domains = df_comp['domain'].unique() if 'domain' in df_comp.columns else []
                st.text(f"{i+1}. {', '.join(domains[:3])} ({len(df_comp)} rows)")
            with col2:
                if st.button("🗑️", key=f"remove_comp_{i}"):
                    st.session_state.df_competitors.pop(i)
                    st.rerun()
    
    st.markdown("---")
    
    # Botón para combinar y procesar
    if st.session_state.df_project is not None:
        if st.button("🚀 Process All Data" if lang == "en" else "🚀 Procesar Todos los Datos", type="primary", use_container_width=True):
            # Combinar todos los dataframes
            all_dfs = [st.session_state.df_project] + st.session_state.df_competitors
            df_combined = pd.concat(all_dfs, ignore_index=True)
            
            st.session_state.df_processed = df_combined
            
            st.success(f"✅ Data processed: {len(df_combined)} total rows" if lang == "en" else f"✅ Datos procesados: {len(df_combined)} filas totales")
            st.balloons()
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Rows" if lang == "en" else "Filas", len(df_combined))
            with col2:
                st.metric("Unique Keywords" if lang == "en" else "Keywords Únicas", df_combined['keyword'].nunique())
            with col3:
                st.metric("Unique Domains" if lang == "en" else "Dominios Únicos", df_combined['domain'].nunique())
            with col4:
                st.metric("Total Traffic" if lang == "en" else "Tráfico Total", f"{df_combined['traffic'].sum():,.0f}")
    
    # Mostrar tabla de estadísticas por dominio si hay datos procesados
    if st.session_state.df_processed is not None:
        st.markdown("---")
        st.subheader("📊 Domain Statistics" if lang == "en" else "📊 Estadísticas por Dominio")
        
        df = st.session_state.df_processed
        
        if 'domain' in df.columns:
            domain_stats = get_domain_stats(df)
            
            # Separar proyecto vs competidores si existe is_client
            if 'is_client' in df.columns:
                # Identificar dominio del proyecto
                project_domains = df[df['is_client'] == True]['domain'].unique()
                
                if len(project_domains) > 0:
                    st.markdown(f"**🏠 Your Project:** {', '.join(project_domains)}")
                
                # Marcar en la tabla
                domain_stats['type'] = domain_stats['domain'].apply(
                    lambda x: '🏠 Project' if x in project_domains else '🎯 Competitor'
                )
                
                # Reordenar columnas
                domain_stats = domain_stats[['type', 'domain', 'keywords', 'traffic', 'urls']]
            
            st.dataframe(
                domain_stats.style.format({
                    'traffic': '{:,.0f}',
                    'keywords': '{:,.0f}',
                    'urls': '{:,.0f}'
                }),
                use_container_width=True,
                hide_index=True
            )

# TAB 2: Categorization (placeholder)
with tab2:
    st.header("📁 Categorization" if lang == "en" else "📁 Categorización")
    
    if st.session_state.df_processed is None:
        st.warning("⚠️ Upload and process data first (Tab 1)" if lang == "en" else "⚠️ Primero sube y procesa datos (Tab 1)")
    else:
        st.info("🚧 Coming soon: URL categorization" if lang == "en" else "🚧 Próximamente: categorización de URLs")
