# TAB 3: Intelligence Analysis
with tab3:
    st.header("🧠 Intelligence Analysis" if lang == "en" else "🧠 Análisis de Inteligencia")
    
    # Check tier
    if st.session_state.tier != 'premium':
        st.warning("⭐ Premium feature. Switch to Premium tier to unlock." if lang == "en" else "⭐ Función Premium. Cambia a tier Premium para desbloquear.")
    elif st.session_state.df_processed is None:
        st.warning("⚠️ Upload and process data first (Tab 1)" if lang == "en" else "⚠️ Primero sube y procesa datos (Tab 1)")
    else:
        from utils.intelligence import SEOIntelligence
        
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
        st.info("🚧 More features coming: Content Gaps, Competitive Zones" if lang == "en" else "🚧 Más funciones próximamente: Content Gaps, Zonas Competitivas")
