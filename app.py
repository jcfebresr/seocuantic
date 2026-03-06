import streamlit as st
import pandas as pd
import chardet
import io

# Importaciones de tus módulos
from utils.source_detector import detect_source_and_map
from utils.data_normalizer import normalize_data
from utils.project_identifier import get_domain_stats
from utils.categorizer import URLCategorizer
from utils.intelligence import SEOIntelligence

# 1. Configuración de página
st.set_page_config(
    page_title="SEOcuantic Keyword Intelligence",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS personalizado
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

# 3. Inicializar session state
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

# 4. Sidebar
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
    
    # Stats globals en Sidebar
    if st.session_state.df_processed is not None:
        st.subheader("📊 Stats" if lang == "en" else "📊 Estadísticas")
        df = st.session_state.df_processed
        
        st.metric("Total Rows" if lang == "en" else "Filas Totales", f"{len(df):,}")
        st.metric("Unique Keywords" if lang == "en" else "Keywords Únicas", f"{df['keyword'].nunique():,}")
        if 'domain' in df.columns:
            st.metric("Unique Domains" if lang == "en" else "Dominios Únicos", f"{df['domain'].nunique():,}")
        st.metric("Total Traffic" if lang == "en" else "Tráfico Total", f"{df['traffic'].sum():,.0f}")

# 5. Main content Header
st.title("🔮 SEOcuantic Keyword Intelligence")
st.markdown("**v0.6.0** - AI-Powered SEO Analysis" if lang == "en" else "**v0.6.0** - Análisis SEO con IA")

# 6. Definición de las Pestañas (Tabs)
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Upload Data" if lang == "en" else "📤 Subir Datos",
    "📁 Categorization" if lang == "en" else "📁 Categorización",
    "🧠 Intelligence" if lang == "en" else "🧠 Inteligencia",
    "📊 Analytics" if lang == "en" else "📊 Análisis"
])

# ==========================================
# TAB 1: UPLOAD DATA
# ==========================================
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
            raw_data = project_file.read()
            detected = chardet.detect(raw_data)
            encoding = detected['encoding']
            
            project_file.seek(0)
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
                source, df_mapped = detect_source_and_map(df_raw)
                
                if df_mapped is not None:
                    df_normalized = normalize_data(df_mapped)
                    
                    if st.session_state.tier == 'free' and len(df_normalized) > 100:
                        st.warning(f"⚠️ Free tier: 100 URLs max. Trimmed." if lang == "en" else f"⚠️ Tier gratuito: máximo 100 URLs. Recortado.")
                        df_normalized = df_normalized.head(100)
                    
                    if 'domain' in df_normalized.columns:
                        df_normalized['is_client'] = True
                    
                    st.session_state.df_project = df_normalized
                    st.success(f"✅ Project CSV loaded: {len(df_normalized)} rows" if lang == "en" else f"✅ CSV del proyecto cargado: {len(df_normalized)} filas")
                    
                    with st.expander("📋 Preview" if lang == "en" else "📋 Vista Previa"):
                        st.dataframe(df_normalized.head(5), use_container_width=True)
        
        except Exception as e:
            st.error(f"❌ Error loading project CSV" if lang == "en" else f"❌ Error cargando CSV del proyecto")
    
    st.markdown("---")
    
    # Sección 2: CSVs de Competidores
    st.subheader("🎯 Competitor CSVs (Optional)" if lang == "en" else "🎯 CSVs de Competidores (Opcional)")
    
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
                raw_data = competitor_file.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding']
                
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
                        
                        if 'domain' in df_normalized.columns:
                            df_normalized['is_client'] = False
                        
                        st.session_state.df_competitors.append(df_normalized)
                        st.success(f"✅ Competitor CSV loaded: {len(df_normalized)} rows" if lang == "en" else f"✅ CSV de competidor cargado: {len(df_normalized)} filas")
                        st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error loading competitor CSV" if lang == "en" else f"❌ Error cargando CSV de competidor")
    else:
        st.warning(f"⚠️ Max competitors reached ({max_competitors})" if lang == "en" else f"⚠️ Máximo de competidores alcanzado ({max_competitors})")
    
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
    
    if st.session_state.df_project is not None:
        if st.button("🚀 Process All Data" if lang == "en" else "🚀 Procesar Todos los Datos", type="primary", use_container_width=True):
            all_dfs = [st.session_state.df_project] + st.session_state.df_competitors
            df_combined = pd.concat(all_dfs, ignore_index=True)
            st.session_state.df_processed = df_combined
            
            st.success(f"✅ Data processed: {len(df_combined)} total rows" if lang == "en" else f"✅ Datos procesados: {len(df_combined)} filas totales")
            st.balloons()
            
    if st.session_state.df_processed is not None:
        st.markdown("---")
        st.subheader("📊 Domain Statistics" if lang == "en" else "📊 Estadísticas por Dominio")
        
        df = st.session_state.df_processed
        
        if 'domain' in df.columns:
            domain_stats = get_domain_stats(df)
            
            if 'is_client' in df.columns:
                project_domains = df[df['is_client'] == True]['domain'].unique()
                
                domain_stats['type'] = domain_stats['domain'].apply(
                    lambda x: '🏠 Project' if x in project_domains else '🎯 Competitor'
                )
                
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

# ==========================================
# TAB 2: CATEGORIZATION
# ==========================================
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
            
            with st.expander("⚙️ Edit Patterns" if lang == "en" else "⚙️ Editar Patrones"):
                for category in st.session_state.categories:
                    default_patterns = URLCategorizer.DEFAULT_PATTERNS.get(category, [])
                    custom = st.session_state.custom_patterns.get(category, [])
                    all_patterns = default_patterns + custom
                    
                    patterns_text = st.text_input(
                        f"{category} patterns:",
                        value=", ".join(all_patterns),
                        key=f'pattern_{category}'
                    )
                    
                    new_patterns = [p.strip() for p in patterns_text.split(',') if p.strip()]
                    st.session_state.custom_patterns[category] = [p for p in new_patterns if p not in default_patterns]
            
            if st.button("🚀 Categorize URLs" if lang == "en" else "🚀 Categorizar URLs", type="primary", use_container_width=True):
                with st.spinner("Categorizing..." if lang == "en" else "Categorizando..."):
                    df_categorized = URLCategorizer.categorize_by_patterns(
                        df,
                        custom_patterns=st.session_state.custom_patterns
                    )
                    st.session_state.df_categorized = df_categorized
                    st.session_state.df_processed = df_categorized
                    st.success(f"✅ Categorized {len(df_categorized)} URLs" if lang == "en" else f"✅ {len(df_categorized)} URLs categorizadas")
        
        else:
            st.subheader("⭐ AI-Powered Categorization" if lang == "en" else "⭐ Categorización con IA")
            st.info("🤖 AI analyzes keywords + URLs for semantic categorization and intent detection" if lang == "en" else "🤖 La IA analiza keywords + URLs para categorización semántica y detección de intención")
            
            col_ai1, col_ai2 = st.columns([1, 2])
            with col_ai1:
                ai_provider = st.selectbox("Select AI Engine:" if lang == "en" else "Motor de IA:",
                    options=["Groq (Fast & Free)", "OpenAI (GPT-4o)", "Anthropic (Claude)", "Google (Gemini)"], index=0)
            
            provider_name = ai_provider.split(" ")[0].lower() # Aseguramos que sea minúsculas y solo el nombre ('groq', 'openai', etc.)
            
            with col_ai2:
                api_key = st.text_input(f"{provider_name.capitalize()} API Key:", type="password")
                
            st.markdown(f"""
            <div style='font-size: 0.85rem; color: #10B981; margin-top: -10px; margin-bottom: 20px;'>
                🔒 <b>{'100% Secure & Private:' if lang == 'en' else '100% Seguro y Privado:'}</b> 
                {'API Keys are only used for this session and never sent to our servers.' if lang == 'en' else 'Las API Keys solo se usan en esta sesión y nunca se envían a nuestros servidores.'}
            </div>
            """, unsafe_allow_html=True)
            
            method = st.radio("Method:" if lang == "en" else "Método:",
                options=['patterns', 'ai'],
                format_func=lambda x: "🔍 Patterns (Free)" if x == 'patterns' else "🤖 AI (Premium)", horizontal=True)
            
            if st.button("🚀 Categorize URLs" if lang == "en" else "🚀 Categorizar URLs", type="primary", use_container_width=True):
                if method == 'patterns':
                    with st.spinner("Categorizing..."):
                        df_cat = URLCategorizer.categorize_by_patterns(df, st.session_state.custom_patterns)
                        st.session_state.df_categorized = df_cat
                        st.session_state.df_processed = df_cat
                        st.success("✅ Done!")
                elif method == 'ai':
                    if not api_key:
                        st.error("⚠️ Enter an API Key to use AI." if lang == "en" else "⚠️ Ingresa una API Key para usar la IA.")
                    else:
                        with st.spinner(f"AI Processing with {provider_name.capitalize()}..."):
                            try:
                                # AQUI ESTÁ EL ARREGLO EXPLICITO CON KWARGS PARA EVITAR ERRORES DE POSICIÓN
                                df_cat = URLCategorizer.categorize_with_ai(
                                    df=df, 
                                    api_key=api_key, 
                                    provider=provider_name, 
                                    categories=st.session_state.categories,
                                    batch_size=50
                                )
                                st.session_state.df_categorized = df_cat
                                st.session_state.df_processed = df_cat
                                st.success("✅ AI Categorization Done!" if lang == "en" else "✅ ¡Categorización con IA completada!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"❌ AI Error ({provider_name.capitalize()}): {str(e)}")
        
        # Mostrar Estadísticas Separadas por Dominio
        if st.session_state.df_categorized is not None:
            st.markdown("---")
            st.subheader("📊 Category Analysis by Domain" if lang == "en" else "📊 Análisis de Categorías por Dominio")
            
            df_cat = st.session_state.df_categorized
            if 'domain' in df_cat.columns:
                domains = df_cat['domain'].unique()
                for domain in domains:
                    df_domain = df_cat[df_cat['domain'] == domain]
                    is_client = df_domain['is_client'].iloc[0] if 'is_client' in df_domain.columns else False
                    icon = "🏠 Project:" if is_client else "🎯 Competitor:"
                    
                    st.markdown(f"### {icon} {domain}")
                    category_stats = URLCategorizer.get_category_stats(df_domain)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Categories" if lang == "en" else "Categorías Usadas", len(category_stats))
                    with col2:
                        top_cat = category_stats.iloc[0]['category'] if len(category_stats) > 0 else 'N/A'
                        st.metric("Top Category" if lang == "en" else "Categoría Principal", top
