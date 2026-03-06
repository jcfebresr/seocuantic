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
        else:
            st.info("No domain data available" if lang == "en" else "No hay datos de dominio disponibles")
        
        st.markdown("---")
        
        # Chart 2: Traffic by Category
        if 'category' in df.columns:
            st.subheader("📊 Traffic by Category" if lang == "en" else "📊 Tráfico por Categoría")
            
            # Domain selector if multiple domains
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
        
        # Chart 6: Category Comparison Stacked
        if 'category' in df.columns and 'domain' in df.columns:
            st.subheader("📊 Category Traffic Comparison" if lang == "en" else "📊 Comparación de Tráfico por Categoría")
            fig_stacked = SEOVisualizations.category_comparison_stacked(df)
            if fig_stacked:
                st.plotly_chart(fig_stacked, use_container_width=True)
            
            st.markdown("---")
        
        # Chart 7: Competitive Zones (Premium only)
        if st.session_state.tier == 'premium' and 'zone' in df.columns:
            st.subheader("🗺️ Competitive Zones Distribution" if lang == "en" else "🗺️ Distribución de Zonas Competitivas")
            fig_zones = SEOVisualizations.competitive_zones_pie(df)
            if fig_zones:
                st.plotly_chart(fig_zones, use_container_width=True)
        
        # Export charts section
        st.markdown("---")
        st.subheader("💾 Export Charts" if lang == "en" else "💾 Exportar Gráficos")
        
        if st.session_state.tier == 'premium':
            st.info("📥 Premium: Download charts as PNG/SVG" if lang == "en" else "📥 Premium: Descarga gráficos como PNG/SVG")
            # Plotly tiene export built-in via modebar
        else:
            st.info("⭐ Upgrade to Premium to export charts" if lang == "en" else "⭐ Actualiza a Premium para exportar gráficos")
