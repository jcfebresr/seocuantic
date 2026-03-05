import streamlit as st
import pandas as pd
from pathlib import Path

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
if 'df_raw' not in st.session_state:
    st.session_state.df_raw = None

# Sidebar
with st.sidebar:
    st.markdown("# 🔮 SEOcuantic")
    
    # Language selector
    lang = st.selectbox(
        "🌐 Language",
        options=['English', 'Español'],
        index=0 if st.session_state.language == 'en' else 1
    )
    st.session_state.language = 'en' if lang == 'English' else 'es'
    
    st.divider()
    st.markdown("**Free Tier** 🆓")
    st.caption("Universal URL categorization & SEO gap analysis")

# Main content
st.title("🔮 SEOcuantic Keyword Intelligence")
st.markdown("*Universal URL categorization & SEO gap analysis with AI*")
st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📁 1. Upload & Setup",
    "🎯 2. Identify Project",
    "🧠 3. Categorization",
    "📊 4. Insights",
    "📥 5. Export"
])

# TAB 1: Upload
with tab1:
    st.header("📁 Upload & Setup")
    
    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=['csv'],
        help="Upload SEranking, Ahrefs, Semrush, GSC or custom CSV"
    )
    
    if uploaded_file:
        try:
            # Try reading CSV
            df = pd.read_csv(uploaded_file)
            st.session_state.df_raw = df
            
            # Success message
            st.markdown(f"""
            <div class="success-box">
                ✅ <strong>CSV loaded successfully</strong><br>
                {len(df):,} rows loaded
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
                    <h3 style="margin:0; color: #8B5CF6;">UTF-8</h3>
                    <p style="margin:0; color: #F1F5F988;">Encoding</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Preview
            st.subheader("📊 Data Preview")
            st.dataframe(df.head(100), use_container_width=True, height=400)
            
            # Column info
            with st.expander("📋 Columns Detected", expanded=False):
                st.write(list(df.columns))
            
        except Exception as e:
            st.error(f"❌ Error loading CSV: {str(e)}")
    
    else:
        st.info("ℹ️ Please upload a CSV file to begin")
        
        # Example
        st.markdown("---")
        st.markdown("**Example CSV format:**")
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
    st.info("🚧 Module 2: Project identification - Coming soon")

with tab3:
    st.info("🚧 Module 3: Categorization - Coming soon")

with tab4:
    st.info("🚧 Module 4: Insights & Analysis - Coming soon")

with tab5:
    st.info("🚧 Module 5: Export & Save - Coming soon")
