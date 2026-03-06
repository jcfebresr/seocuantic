import streamlit as st
import pandas as pd
import chardet
import io
from utils.categorizer import URLCategorizer
from utils.intelligence import SEOIntelligence
from utils.visualizations import SEOVisualizations
from utils.source_detector import detect_source_and_map
from utils.data_normalizer import normalize_data
from utils.project_identifier import get_domain_stats

# Configuración de página
st.set_page_config(
    page_title="Keyword Intelligence",
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
        if 'domain' in df.columns:
            st.metric("Unique Domains" if lang == "en" else "Dominios Únicos", f"{df['domain'].nunique():,}")
        st.metric("Total Traffic" if lang == "en" else "Tráfico Total", f"{df['traffic'].sum():,.0f}")

# Main content
lang = st.session_state.language

st.title("🔮 Keyword Intelligence")
st.markdown("**v0.6.0** - AI-Powered SEO Analysis" if lang == "en" else "**v0.6.0** - Análisis SEO con IA")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Upload Data" if lang == "en" else "📤 Subir Datos",
    "📁 Categorization" if lang == "en" else "📁 Categorización",
    "🧠 Intelligence" if lang == "en" else "🧠 Inteligencia",
    "📊 Analytics" if lang == "en" else "📊 Análisis"
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
            st.error(f"❌ Error loading project CSV: {str(e)}" if lang == "en" else f"❌ Error cargando CSV del proyecto: {str(e)}")
    
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
                st.error(f"❌ Error loading competitor CSV: {str(e)}" if lang == "en" else f"❌ Error cargando CSV de competidor: {str(e)}")
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

# TAB 2: Categorization
with tab2:
    st.header("📁 Categorization" if lang == "en" else "📁 Categorización")
    
    if st.session_state.df_processed is None:
        st.warning("⚠️ Upload and process data first (Tab 1)" if lang == "en" else "⚠️ Primero sube y procesa datos (Tab 1)")
    else:
        df = st.session_state.df_processed
        tier = st.session_state.tier
        
        st.subheader("📂 Available Categories" if lang == "en" else "📂 Categorías Disponibles")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(", ".join([f"`{cat}`" for cat in st.session_state.categories]))
        
        with col2:
            with st.popover("➕ Add Category" if lang == "en" else "➕ Añadir Categoría"):
                new_cat = st.text_input(
                    "Category name (1 word):" if lang == "en" else "Nombre categoría (1 palabra):",
                    max_chars=20,
                    key='new_category_input'
                )
                
                if st.button("Add" if lang == "en" else "Añadir", key='add_cat_btn'):
                    is_valid, error_msg = URLCategorizer.validate_category_name(new_cat)
                    
                    if not is_valid:
                        st.error(f"❌ {error_msg}")
                    elif new_cat.capitalize() in st.session_state.categories:
                        st.error("❌ Category already exists" if lang == "en" else "❌ Categoría ya existe")
                    else:
                        st.session_state.categories.append(new_cat.capitalize())
                        st.session_state.custom_patterns[new_cat.capitalize()] = []
                        st.success(f"✅ Added: {new_cat.capitalize()}")
                        st.rerun()
        
        st.markdown("---")
        
        if tier == 'free':
            st.subheader("🆓 Pattern-Based Categorization" if lang == "en" else "🆓 Categorización por Patrones")
            
            st.info("💡 URLs are categorized by matching path patterns (e.g., /blog → Blog)" if lang == "en" else "💡 Las URLs se categorizan por patrones en la ruta (ej: /blog → Blog)")
            
            if st.button("🚀 Categorize URLs" if lang == "en" else "🚀 Categorizar URLs", type="primary", use_container_width=True):
                with st.spinner("Categorizing..." if lang == "en" else "Categorizando..."):
                    df_categorized = URLCategorizer.categorize_by_patterns(
                        df,
                        custom_patterns=st.session_state.custom_patterns
                    )
                    
                    st.session_state.df_categorized = df_categorized
                    st.session_state.df_processed = df_categorized
                    
                    st.success(f"✅ Categorized {len(df_categorized)} URLs" if lang == "en" else f"✅ {len(df_categorized)} URLs categorizadas")
                    st.balloons()
        else:
            st.subheader("⭐ AI-Powered Categorization" if lang == "en" else "⭐ Categorización con IA")
            
            st.markdown(f"""
            <div class="info-box">
                <strong>{"🔒 Privacy & Security:" if lang == "en" else "🔒 Privacidad y Seguridad:"}</strong><br>
                {"• Your API key is NOT stored" if lang == "en" else "• Tu API key NO se guarda"}<br>
                {"• Used only for this session" if lang == "en" else "• Se usa solo para esta sesión"}<br>
                {"• Direct connection to AI provider (no intermediaries)" if lang == "en" else "• Conexión directa al proveedor de IA (sin intermediarios)"}
            </div>
            """, unsafe_allow_html=True)
            
            st.info("🤖 Uses Claude AI to analyze keywords + URLs for semantic categorization" if lang == "en" else "🤖 Usa Claude IA para analizar keywords + URLs para categorización semántica")
            
            api_key = st.text_input(
                "Anthropic API Key (Claude):" if lang == "en" else "Clave API de Anthropic (Claude):",
                type="password",
                help="Get your API key at https://console.anthropic.com" if lang == "en" else "Obtén tu clave API en https://console.anthropic.com"
            )
            
            method = st.radio(
                "Method:" if lang == "en" else "Método:",
                options=['patterns', 'ai'],
                format_func=lambda x: "🔍 Patterns (Free)" if x == 'patterns' else "🤖 AI (Premium)",
                horizontal=True
            )
            
            if method == 'ai' and not api_key:
                st.warning("⚠️ Enter your API key to use AI categorization" if lang == "en" else "⚠️ Ingresa tu API key para usar categorización IA")
            
            if st.button("🚀 Categorize URLs" if lang == "en" else "🚀 Categorizar URLs", type="primary", use_container_width=True):
                
                if method == 'patterns':
                    with st.spinner("Categorizing with patterns..." if lang == "en" else "Categorizando con patrones..."):
                        df_categorized = URLCategorizer.categorize_by_patterns(
                            df,
                            custom_patterns=st.session_state.custom_patterns
                        )
                        
                        st.session_state.df_categorized = df_categorized
                        st.session_state.df_processed = df_categorized
                        
                        st.success(f"✅ Categorized {len(df_categorized)} URLs" if lang == "en" else f"✅ {len(df_categorized)} URLs categorizadas")
                
                elif method == 'ai' and api_key:
                    with st.spinner("Categorizing with AI... This may take a few minutes" if lang == "en" else "Categorizando con IA... Esto puede tomar unos minutos"):
                        try:
                            df_categorized = URLCategorizer.categorize_with_ai(
                                df,
                                api_key=api_key,
                                categories=st.session_state.categories,
                                batch_size=50
                            )
                            
                            st.session_state.df_categorized = df_categorized
                            st.session_state.df_processed = df_categorized
                            
                            st.success(f"✅ AI categorized {len(df_categorized)} URLs" if lang == "en" else f"✅ IA categorizó {len(df_categorized)} URLs")
                            st.balloons()
                        
                        except Exception as e:
                            st.error(f"❌ AI Error: {str(e)}")
        
        if st.session_state.df_categorized is not None:
            st.markdown("---")
            st.subheader("📊 Category Statistics by Domain" if lang == "en" else "📊 Estadísticas por Categoría y Dominio")
            
            df_cat = st.session_state.df_categorized
            
            if 'domain' in df_cat.columns:
                domains = df_cat['domain'].unique()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Domains" if lang == "en" else "Dominios Totales", len(domains))
                with col2:
                    total_categories = df_cat['category'].nunique()
                    st.metric("Total Categories" if lang == "en" else "Categorías Totales", total_categories)
                with col3:
                    uncategorized = len(df_cat[df_cat['category'] == 'Other'])
                    st.metric("Uncategorized" if lang == "en" else "Sin Categorizar", uncategorized)
                
                st.markdown("---")
                
                for domain in sorted(domains):
                    df_domain = df_cat[df_cat['domain'] == domain]
                    
                    is_project = df_domain['is_client'].iloc[0] if 'is_client' in df_domain.columns else False
                    domain_type = "🏠 Your Project" if is_project else "🎯 Competitor"
                    
                    st.markdown(f"### {domain_type}: **{domain}**")
                    
                    domain_stats = df_domain.groupby('category').agg({
                        'keyword': 'count',
                        'traffic': 'sum',
                        'url': 'nunique'
                    }).reset_index()
                    
                    domain_stats.columns = ['category', 'keywords', 'traffic', 'urls']
                    domain_stats = domain_stats.sort_values('traffic', ascending=False)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Keywords", f"{len(df_domain):,}")
                    with col2:
                        st.metric("Traffic", f"{df_domain['traffic'].sum():,.0f}")
                    with col3:
                        st.metric("URLs", f"{df_domain['url'].nunique():,}")
                    with col4:
                        st.metric("Categories", f"{df_domain['category'].nunique():,}")
                    
                    st.dataframe(
                        domain_stats.style.format({
                            'traffic': '{:,.0f}',
                            'keywords': '{:,.0f}',
                            'urls': '{:,.0f}'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.markdown("---")
            
            with st.expander("📋 Preview All Categorized Data" if lang == "en" else "📋 Vista Previa de Todos los Datos Categorizados"):
                st.dataframe(
                    df_cat[['domain', 'category', 'keyword', 'url', 'traffic']].head(100),
                    use_container_width=True,
                    hide_index=True
                )

# TAB 3: Intelligence
with tab3:
    st.header("🧠 Intelligence Analysis" if lang == "en" else "🧠 Análisis de Inteligencia")
    
    if st.session_state.tier != 'premium':
        st.warning("⭐ Premium feature. Switch to Premium tier to unlock." if lang == "en" else "⭐ Función Premium. Cambia a tier Premium para desbloquear.")
    elif st.session_state.df_processed is None:
        st.warning("⚠️ Upload and process data first (Tab 1)" if lang == "en" else "⚠️ Primero sube y procesa datos (Tab 1)")
    else:
        df = st.session_state.df_processed
        
        # Feature 1: Cannibalization Detection
        st.subheader("🔍 Cannibalization Detection" if lang == "en" else "🔍 Detección de Canibalización")
        
        st.markdown(f"""
        <div class="info-box">
            <strong>{"💡 What is Cannibalization?" if lang == "en" else "💡 ¿Qué es Canibalización?"}</strong><br>
            {"Multiple URLs from YOUR project competing for the same keyword." if lang == "en" else "Múltiples URLs de TU proyecto compitiendo por la misma keyword."}<br><br>
            <strong>{"Severity:" if lang == "en" else "Severidad:"}</strong><br>
            {"🔴 Critical: At least 1 URL in Top 3 (losing authority)" if lang == "en" else "🔴 Crítico: Al menos 1 URL en Top 3 (perdiendo autoridad)"}<br>
            {"🟡 Warning: At least 1 URL in Top 10 (page 1 competition)" if lang == "en" else "🟡 Advertencia: Al menos 1 URL en Top 10 (competencia en página 1)"}<br>
            {"⚪ Minor: All URLs in page 2+ (low priority)" if lang == "en" else "⚪ Menor: Todas las URLs en página 2+ (baja prioridad)"}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Analyze Cannibalization" if lang == "en" else "🚀 Analizar Canibalización", type="primary"):
            with st.spinner("Analyzing..." if lang == "en" else "Analizando..."):
                cannibalization = SEOIntelligence.detect_cannibalization(df)
                
                if len(cannibalization) == 0:
                    st.success("✅ No cannibalization detected! All keywords have unique URLs." if lang == "en" else "✅ ¡No se detectó canibalización! Todas las keywords tienen URLs únicas.")
                else:
                    stats = SEOIntelligence.get_cannibalization_stats(cannibalization)
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Cannibal Keywords" if lang == "en" else "Keywords Canibalizadas", stats['total_cannibal_keywords'])
                    with col2:
                        st.metric("🔴 Critical", stats['critical_count'])
                    with col3:
                        st.metric("🟡 Warning", stats['warning_count'])
                    with col4:
                        st.metric("⚪ Minor", stats['minor_count'])
                    
                    st.markdown("---")
                    
                    # Table
                    st.markdown("### 📋 Cannibalized Keywords" if lang == "en" else "### 📋 Keywords Canibalizadas")
                    
                    # Reorder columns for display
                    display_cols = ['severity', 'keyword', 'urls_count']
                    
                    if 'positions_list' in cannibalization.columns:
                        display_cols.append('positions_list')
                    if 'categories_list' in cannibalization.columns:
                        display_cols.append('categories_list')
                    
                    display_cols.extend(['total_traffic', 'urls_list'])
                    
                    st.dataframe(
                        cannibalization[display_cols].style.format({
                            'total_traffic': '{:,.0f}',
                            'urls_count': '{:,.0f}'
                        }),
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
        
        st.markdown("---")
        
        # Feature 2: Content Gaps
        st.subheader("🎯 Content Gaps Detection" if lang == "en" else "🎯 Detección de Brechas de Contenido")
        
        st.markdown(f"""
        <div class="info-box">
            <strong>{"💡 What are Content Gaps?" if lang == "en" else "💡 ¿Qué son Brechas de Contenido?"}</strong><br>
            {"Keywords that competitors rank for but YOU don't." if lang == "en" else "Keywords por las que rankean competidores pero TÚ no."}<br>
            {"= Content opportunities to create new pages" if lang == "en" else "= Oportunidades para crear nuevo contenido"}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Find Content Gaps" if lang == "en" else "🚀 Encontrar Brechas", type="primary", key="gaps_btn"):
            with st.spinner("Analyzing..." if lang == "en" else "Analizando..."):
                gaps = SEOIntelligence.detect_content_gaps(df)
                
                if len(gaps) == 0:
                    st.success("✅ No content gaps! You're covering all competitor keywords." if lang == "en" else "✅ ¡Sin brechas! Cubres todas las keywords de competidores.")
                else:
                    stats = SEOIntelligence.get_content_gaps_stats(gaps)
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Gap Keywords" if lang == "en" else "Keywords Faltantes", stats['total_gap_keywords'])
                    with col2:
                        st.metric("High Volume (>100)" if lang == "en" else "Alto Volumen (>100)", stats['high_volume_gaps'])
                    with col3:
                        st.metric("Total Opportunity" if lang == "en" else "Oportunidad Total", f"{stats['total_opportunity_volume']:,}")
                    with col4:
                        st.metric("Avg Competitors" if lang == "en" else "Competidores Prom.", stats['avg_competitor_count'])
                    
                    st.markdown("---")
                    
                    # Table
                    st.markdown("### 📋 Content Gap Opportunities" if lang == "en" else "### 📋 Oportunidades de Contenido")
                    
                    # Build display columns in exact order
                    display_cols = ['keyword']
                    
                    if 'volume' in gaps.columns:
                        display_cols.append('volume')
                    if 'kd' in gaps.columns:
                        display_cols.append('kd')
                    
                    display_cols.append('your_position')
                    display_cols.extend(['competitor_count', 'competitor_domains', 'competitor_urls'])
                    
                    if 'best_competitor_position' in gaps.columns:
                        display_cols.append('best_competitor_position')
                    
                    display_cols.append('competitor_traffic')
                    
                    format_dict = {'competitor_traffic': '{:,.0f}'}
                    if 'volume' in gaps.columns:
                        format_dict['volume'] = '{:,.0f}'
                    
                    st.dataframe(
                        gaps[display_cols].style.format(format_dict),
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
        
        st.markdown("---")
        
        # Feature 3: Competitive Zones
        st.subheader("🗺️ Competitive Zones" if lang == "en" else "🗺️ Zonas Competitivas")
        
        st.markdown(f"""
        <div class="info-box">
            <strong>{"💡 What are Competitive Zones?" if lang == "en" else "💡 ¿Qué son Zonas Competitivas?"}</strong><br>
            {"🟢 Dominio: Only YOU rank (protect your territory)" if lang == "en" else "🟢 Dominio: Solo TÚ rankeas (protege tu territorio)"}<br>
            {"🔴 Guerra: YOU + competitors rank (direct battle)" if lang == "en" else "🔴 Guerra: TÚ + competidores rankean (batalla directa)"}<br>
            {"🟡 QuickWin: Only competitors, low volume (easy to capture)" if lang == "en" else "🟡 QuickWin: Solo competidores, volumen bajo (fácil de capturar)"}<br>
            {"🟣 Gap: Only competitors, high volume (difficult)" if lang == "en" else "🟣 Gap: Solo competidores, volumen alto (difícil)"}
        </div>
        """, unsafe_allow_html=True)
        
        # Quick Win threshold selector
        quick_win_threshold = st.slider(
            "QuickWin threshold (volume)" if lang == "en" else "Umbral QuickWin (volumen)",
            min_value=50,
            max_value=500,
            value=100,
            step=50,
            help="Keywords below this volume = QuickWin, above = Gap" if lang == "en" else "Keywords debajo de este volumen = QuickWin, arriba = Gap"
        )
        
        if st.button("🚀 Classify Zones" if lang == "en" else "🚀 Clasificar Zonas", type="primary", key="zones_btn"):
            with st.spinner("Classifying..." if lang == "en" else "Clasificando..."):
                zones = SEOIntelligence.classify_competitive_zones(df, quick_win_threshold)
                
                if len(zones) == 0:
                    st.warning("⚠️ No data to classify" if lang == "en" else "⚠️ No hay datos para clasificar")
                else:
                    stats = SEOIntelligence.get_competitive_zones_stats(zones)
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🟢 Dominio", stats['dominio_count'])
                    with col2:
                        st.metric("🔴 Guerra", stats['guerra_count'])
                    with col3:
                        st.metric("🟡 QuickWin", stats['quickwin_count'])
                    with col4:
                        st.metric("🟣 Gap", stats['gap_count'])
                    
                    st.markdown("---")
                    
                    # Tables separated by zone
                    st.markdown("### 📋 Competitive Zone Classification" if lang == "en" else "### 📋 Clasificación de Zonas Competitivas")
                    
                    # Build display columns
                    display_cols = ['keyword']
                    
                    if 'volume' in zones.columns:
                        display_cols.append('volume')
                    if 'kd' in zones.columns:
                        display_cols.append('kd')
                    
                    display_cols.extend(['your_position', 'your_url', 'competitor_count', 'competitor_domains', 'competitor_urls'])
                    
                    format_dict = {}
                    if 'volume' in zones.columns:
                        format_dict['volume'] = '{:,.0f}'
                    
                    # Table 1: Dominio
                    st.markdown("#### 🟢 Dominio (Only YOU rank)" if lang == "en" else "#### 🟢 Dominio (Solo TÚ rankeas)")
                    dominio_data = zones[zones['zone'] == '🟢 Dominio']
                    if len(dominio_data) > 0:
                        st.dataframe(
                            dominio_data[display_cols].style.format(format_dict),
                            use_container_width=True,
                            hide_index=True,
                            height=300
                        )
                    else:
                        st.info("No keywords in this zone" if lang == "en" else "No hay keywords en esta zona")
                    
                    st.markdown("---")
                    
                    # Table 2: Guerra
                    st.markdown("#### 🔴 Guerra (YOU + Competitors)" if lang == "en" else "#### 🔴 Guerra (TÚ + Competidores)")
                    guerra_data = zones[zones['zone'] == '🔴 Guerra']
                    if len(guerra_data) > 0:
                        st.dataframe(
                            guerra_data[display_cols].style.format(format_dict),
                            use_container_width=True,
                            hide_index=True,
                            height=300
                        )
                    else:
                        st.info("No keywords in this zone" if lang == "en" else "No hay keywords en esta zona")
                    
                    st.markdown("---")
                    
                    # Table 3: QuickWin
                    st.markdown("#### 🟡 QuickWin (Low volume opportunities)" if lang == "en" else "#### 🟡 QuickWin (Oportunidades de bajo volumen)")
                    quickwin_data = zones[zones['zone'] == '🟡 QuickWin']
                    if len(quickwin_data) > 0:
                        st.dataframe(
                            quickwin_data[display_cols].style.format(format_dict),
                            use_container_width=True,
                            hide_index=True,
                            height=300
                        )
                    else:
                        st.info("No keywords in this zone" if lang == "en" else "No hay keywords en esta zona")
                    
                    st.markdown("---")
                    
                    # Table 4: Gap
                    st.markdown("#### 🟣 Gap (High volume, difficult)" if lang == "en" else "#### 🟣 Gap (Alto volumen, difícil)")
                    gap_data = zones[zones['zone'] == '🟣 Gap']
                    if len(gap_data) > 0:
                        st.dataframe(
                            gap_data[display_cols].style.format(format_dict),
                            use_container_width=True,
                            hide_index=True,
                            height=300
                        )
                    else:
                        st.info("No keywords in this zone" if lang == "en" else "No hay keywords en esta zona")

# TAB 4: Analytics
with tab4:
    st.header("📊 Analytics & Visualizations" if lang == "en" else "📊 Análisis y Visualizaciones")
    
    if st.session_state.df_processed is None:
        st.warning("⚠️ Upload and process data first" if lang == "en" else "⚠️ Primero sube y procesa datos")
    else:
        df = st.session_state.df_processed
        
        # Chart 1: Traffic by Domain
        st.subheader("🌐 Traffic by Domain" if lang == "en" else "🌐 Tráfico por Dominio")
        fig_domain = SEOVisualizations.traffic_by_domain(df)
        if fig_domain:
            st.plotly_chart(fig_domain, use_container_width=True)
        else:
            st.info("No domain data available" if lang == "en" else "No hay datos de dominio disponibles")
        
        st.markdown("---")
        
        # Chart 2: Traffic by Category
        if 'category' in df.columns:
            st.subheader("📊 Traffic by Category" if lang == "en" else "📊 Tráfico por Categoría")
            
            if 'domain' in df.columns and df['domain'].nunique() > 1:
                selected_domain = st.selectbox(
                    "Select domain:" if lang == "en" else "Selecciona dominio:",
                    options=['All'] + list(df['domain'].unique()),
                    key='viz_domain_selector'
                )
                
                fig_cat = SEOVisualizations.traffic_by_category(
                    df, 
                    domain=None if selected_domain == 'All' else selected_domain
                )
            else:
                fig_cat = SEOVisualizations.traffic_by_category(df)
            
            if fig_cat:
                st.plotly_chart(fig_cat, use_container_width=True)
            
            st.markdown("---")
        
        # Chart 3: Domain × Category Heatmap
        if 'category' in df.columns and 'domain' in df.columns:
            st.subheader("🔥 Traffic Heatmap: Domain × Category" if lang == "en" else "🔥 Mapa de Calor: Dominio × Categoría")
            fig_heatmap = SEOVisualizations.domain_category_heatmap(df)
            if fig_heatmap:
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            st.markdown("---")
        
        # Chart 4: Top Keywords
        st.subheader("🏆 Top Keywords by Traffic" if lang == "en" else "🏆 Top Keywords por Tráfico")
        top_n = st.slider(
            "Number of keywords" if lang == "en" else "Número de keywords", 
            min_value=10, 
            max_value=50, 
            value=20,
            step=5
        )
        fig_top = SEOVisualizations.top_keywords_chart(df, top_n)
        if fig_top:
            st.plotly_chart(fig_top, use_container_width=True)
        
        st.markdown("---")
        
        # Chart 5: Position Distribution
        if 'position' in df.columns:
            st.subheader("📈 Position Distribution" if lang == "en" else "📈 Distribución de Posiciones")
            fig_pos = SEOVisualizations.position_distribution(df)
            if fig_pos:
                st.plotly_chart(fig_pos, use_container_width=True)
            else:
                st.info("No position data available" if lang == "en" else "No hay datos de posición disponibles")
            
            st.markdown("---")
        
        # Chart 6: Keyword Count Comparison
        if 'category' in df.columns and 'domain' in df.columns:
            st.subheader("📊 Keyword Count Comparison" if lang == "en" else "📊 Comparación de Cantidad de Keywords")
            fig_grouped = SEOVisualizations.category_comparison_grouped(df)
            if fig_grouped:
                st.plotly_chart(fig_grouped, use_container_width=True)
            
            st.markdown("---")
        
        # Chart 7: Traffic Funnel
        if 'position' in df.columns:
            st.subheader("🎯 Traffic Funnel by Position" if lang == "en" else "🎯 Embudo de Tráfico por Posición")
            
            if 'domain' in df.columns and df['domain'].nunique() > 1:
                funnel_domain = st.selectbox(
                    "Select domain for funnel:" if lang == "en" else "Selecciona dominio para embudo:",
                    options=['All'] + list(df['domain'].unique()),
                    key='funnel_domain_selector'
                )
                
                fig_funnel = SEOVisualizations.traffic_funnel(
                    df,
                    domain=None if funnel_domain == 'All' else funnel_domain
                )
            else:
                fig_funnel = SEOVisualizations.traffic_funnel(df)
            
            if fig_funnel:
                st.plotly_chart(fig_funnel, use_container_width=True)
            
            st.markdown("---")
        
        # Chart 8: Volume vs Traffic Scatter
        if 'volume' in df.columns and 'traffic' in df.columns:
            st.subheader("📈 Volume vs Traffic Analysis" if lang == "en" else "📈 Análisis Volumen vs Tráfico")
            st.info("💡 Points above the diagonal = High efficiency. Points below = Underperforming." if lang == "en" else "💡 Puntos arriba de la diagonal = Alta eficiencia. Puntos abajo = Bajo rendimiento.")
            
            fig_scatter = SEOVisualizations.volume_vs_traffic_scatter(df)
            if fig_scatter:
                st.plotly_chart(fig_scatter, use_container_width=True)
