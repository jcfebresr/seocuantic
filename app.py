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
if 'df_raw' not in st.session_state:
    st.session_state.df_raw = None
if 'df_processed' not in st.session_state:
    st.session_state.df_processed = None
if 'source_detected' not in st.session_state:
    st.session_state.source_detected = None
if 'encoding_detected' not in st.session_state:
    st.session_state.encoding_detected = None
if 'selected_domain' not in st.session_state:
    st.session_state.selected_domain = None
if 'competitor_domains' not in st.session_state:
    st.session_state.competitor_domains = []
if 'project_identified' not in st.session_state:
    st.session_state.project_identified = False

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
tab1, tab2, tab3 = st.tabs([
    "📤 Upload CSV" if lang == "en" else "📤 Subir CSV",
    "🎯 Identify Project" if lang == "en" else "🎯 Identificar Proyecto",
    "📁 Categorization" if lang == "en" else "📁 Categorización"
])

# TAB 1: Upload CSV
with tab1:
    st.header("📤 Upload CSV" if lang == "en" else "📤 Subir CSV")
    
    st.markdown("""
    **Supported sources:**
    - SEranking
    - Ahrefs (Top Pages, Organic Keywords, Generic)
    - Semrush
    - Google Search Console
    """ if lang == "en" else """
    **Fuentes soportadas:**
    - SEranking
    - Ahrefs (Top Pages, Organic Keywords, Genérico)
    - Semrush
    - Google Search Console
    """)
    
    uploaded_file = st.file_uploader(
        "Drop your CSV here" if lang == "en" else "Arrastra tu CSV aquí",
        type=['csv'],
        help="CSV file with keyword data" if lang == "en" else "Archivo CSV con datos de keywords"
    )
    
    if uploaded_file is not None:
        try:
            # Detectar encoding
            raw_data = uploaded_file.read()
            detected = chardet.detect(raw_data)
            encoding = detected['encoding']
            st.session_state.encoding_detected = encoding
            
            # Leer CSV
            uploaded_file.seek(0)
            
            # Intentar leer con diferentes separadores
            separators = [',', '\t', ';']
            df_raw = None
            
            for sep in separators:
                try:
                    uploaded_file.seek(0)
                    df_raw = pd.read_csv(
                        uploaded_file,
                        encoding=encoding,
                        sep=sep,
                        on_bad_lines='skip',
                        engine='python'
                    )
                    if len(df_raw.columns) > 1:  # Validar que se separó correctamente
                        break
                except:
                    continue
            
            if df_raw is None or len(df_raw) == 0:
                st.error("❌ Could not read CSV. Check format." if lang == "en" else "❌ No se pudo leer el CSV. Verifica el formato.")
            else:
                st.session_state.df_raw = df_raw
                
                # Auto-detectar fuente y normalizar
                with st.spinner("🔍 Detecting source and normalizing..." if lang == "en" else "🔍 Detectando fuente y normalizando..."):
                    source, df_mapped = detect_source_and_map(df_raw)
                    st.session_state.source_detected = source
                    
                    if df_mapped is not None:
                        df_normalized = normalize_data(df_mapped)
                        st.session_state.df_processed = df_normalized
                        
                        # Validar tier limits
                        if st.session_state.tier == 'free' and len(df_normalized) > 100:
                            st.warning(f"⚠️ Free tier: 100 URLs max. Showing first 100 rows." if lang == "en" else f"⚠️ Tier gratuito: máximo 100 URLs. Mostrando primeras 100 filas.")
                            st.session_state.df_processed = df_normalized.head(100)
                        
                        # Success message
                        st.markdown(f"""
                        <div class="success-box">
                            <h3>✅ {"CSV Processed Successfully!" if lang == "en" else "¡CSV Procesado Exitosamente!"}</h3>
                            <p><strong>{"Source detected:" if lang == "en" else "Fuente detectada:"}</strong> {source.upper()}</p>
                            <p><strong>{"Encoding:" if lang == "en" else "Codificación:"}</strong> {encoding}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Rows" if lang == "en" else "Filas", len(df_normalized))
                        with col2:
                            st.metric("Unique Keywords" if lang == "en" else "Keywords Únicas", df_normalized['keyword'].nunique())
                        with col3:
                            st.metric("Unique Domains" if lang == "en" else "Dominios Únicos", df_normalized['domain'].nunique())
                        with col4:
                            st.metric("Total Traffic" if lang == "en" else "Tráfico Total", f"{df_normalized['traffic'].sum():,.0f}")
                        
                        # Preview
                        st.subheader("📋 Data Preview" if lang == "en" else "📋 Vista Previa")
                        st.dataframe(df_normalized.head(100), use_container_width=True)
                    else:
                        st.error("❌ Could not map columns. Unknown format." if lang == "en" else "❌ No se pudieron mapear las columnas. Formato desconocido.")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# TAB 2: Identify Project
with tab2:
    st.header("🎯 Identify Your Project" if lang == "en" else "🎯 Identifica Tu Proyecto")
    
    if 'df_processed' not in st.session_state or st.session_state.df_processed is None:
        st.warning("⚠️ Upload a CSV first" if lang == "en" else "⚠️ Primero sube un CSV")
    else:
        df = st.session_state.df_processed
        
        # Extraer estadísticas por dominio
        domain_stats = get_domain_stats(df)
        
        st.subheader("📊 Detected Domains" if lang == "en" else "📊 Dominios Detectados")
        st.markdown(f"**{len(domain_stats)}** domains found" if lang == "en" else f"**{len(domain_stats)}** dominios encontrados")
        
        # Validar límites de tier
        tier = st.session_state.get('tier', 'free')
        is_valid, msg, max_comp = validate_competitors(len(domain_stats), tier)
        
        if not is_valid:
            st.markdown(f"""
            <div class="warning-box">
                <strong>⚠️ {msg}</strong><br>
                {"Select which competitors to keep." if lang == "en" else "Selecciona qué competidores mantener."}
            </div>
            """, unsafe_allow_html=True)
        
        # Tabla de selección
        st.markdown("---")
        st.markdown("**Select YOUR domain** (rest = competitors)" if lang == "en" else "**Selecciona TU dominio** (resto = competidores)")
        
        # Radio buttons para seleccionar dominio propio
        selected_domain = st.radio(
            "Your project domain:" if lang == "en" else "Tu dominio:",
            options=domain_stats['domain'].tolist(),
            format_func=lambda x: f"🌐 {x} — {domain_stats[domain_stats['domain']==x]['keywords'].values[0]:,.0f} kws, {domain_stats[domain_stats['domain']==x]['traffic'].values[0]:,.0f} traffic",
            key='domain_selector',
            label_visibility='collapsed'
        )
        
        # Mostrar tabla completa con stats
        st.dataframe(
            domain_stats.style.format({
                'traffic': '{:,.0f}',
                'keywords': '{:,.0f}',
                'urls': '{:,.0f}'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Botón de confirmación
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("✅ Confirm" if lang == "en" else "✅ Confirmar", type="primary", use_container_width=True):
                
                # Validar límite de competidores
                competitors = get_competitor_list(df, selected_domain)
                
                if len(competitors) > max_comp:
                    st.error(f"❌ Limit: {max_comp} competitors. You have {len(competitors)}." if lang == "en" else f"❌ Límite: {max_comp} competidores. Tienes {len(competitors)}.")
                else:
                    # Marcar dominio del cliente
                    df_marked = mark_project_domain(df, selected_domain)
                    
                    # Actualizar session state
                    st.session_state.df_processed = df_marked
                    st.session_state.selected_domain = selected_domain
                    st.session_state.competitor_domains = competitors
                    st.session_state.project_identified = True
                    
                    st.success(f"✅ Project identified: **{selected_domain}**" if lang == "en" else f"✅ Proyecto identificado: **{selected_domain}**")
                    st.info(f"🎯 {len(competitors)} competitors marked" if lang == "en" else f"🎯 {len(competitors)} competidores marcados")
                    st.balloons()
        
        # Mostrar estado si ya está identificado
        if st.session_state.get('project_identified', False):
            st.markdown("---")
            st.markdown("### ✅ Project Status" if lang == "en" else "### ✅ Estado del Proyecto")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Your Domain" if lang == "en" else "Tu Dominio", st.session_state.selected_domain)
            with col2:
                client_kws = len(df[df['is_client'] == True])
                st.metric("Your Keywords" if lang == "en" else "Tus Keywords", f"{client_kws:,}")
            with col3:
                st.metric("Competitors" if lang == "en" else "Competidores", len(st.session_state.competitor_domains))
            
            # Listado de competidores
            with st.expander("📋 View Competitors" if lang == "en" else "📋 Ver Competidores"):
                for comp in st.session_state.competitor_domains:
                    comp_stats = domain_stats[domain_stats['domain'] == comp].iloc[0]
                    st.markdown(f"- **{comp}** — {comp_stats['keywords']:,.0f} kws, {comp_stats['traffic']:,.0f} traffic")

# TAB 3: Categorization (placeholder)
with tab3:
    st.header("📁 Categorization" if lang == "en" else "📁 Categorización")
    
    if not st.session_state.get('project_identified', False):
        st.warning("⚠️ Identify your project first (Tab 2)" if lang == "en" else "⚠️ Primero identifica tu proyecto (Tab 2)")
    else:
        st.info("🚧 Coming soon: URL categorization" if lang == "en" else "🚧 Próximamente: categorización de URLs")
