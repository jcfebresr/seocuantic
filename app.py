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
        from utils.categorizer import URLCategorizer
        
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
