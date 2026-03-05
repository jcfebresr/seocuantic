# TAB 2: Categorization
with tab2:
    st.header("📁 Categorization" if lang == "en" else "📁 Categorización")
    
    if st.session_state.df_processed is None:
        st.warning("⚠️ Upload and process data first (Tab 1)" if lang == "en" else "⚠️ Primero sube y procesa datos (Tab 1)")
    else:
        from utils.categorizer import URLCategorizer
        
        df = st.session_state.df_processed
        tier = st.session_state.tier
        
        # Mostrar categorías actuales
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
        
        # FREE TIER: Pattern-based categorization
        if tier == 'free':
            st.subheader("🆓 Pattern-Based Categorization" if lang == "en" else "🆓 Categorización por Patrones")
            
            st.info("💡 URLs are categorized by matching path patterns (e.g., /blog → Blog)" if lang == "en" else "💡 Las URLs se categorizan por patrones en la ruta (ej: /blog → Blog)")
            
            # Show/edit patterns
            with st.expander("⚙️ Edit Patterns" if lang == "en" else "⚙️ Editar Patrones"):
                for category in st.session_state.categories:
                    default_patterns = URLCategorizer.DEFAULT_PATTERNS.get(category, [])
                    custom = st.session_state.custom_patterns.get(category, [])
                    
                    all_patterns = default_patterns + custom
                    
                    patterns_text = st.text_input(
                        f"{category} patterns (comma-separated):",
                        value=", ".join(all_patterns),
                        key=f'pattern_{category}'
                    )
                    
                    # Update custom patterns
                    new_patterns = [p.strip() for p in patterns_text.split(',') if p.strip()]
                    st.session_state.custom_patterns[category] = [p for p in new_patterns if p not in default_patterns]
            
            # Categorize button
            if st.button("🚀 Categorize URLs" if lang == "en" else "🚀 Categorizar URLs", type="primary", use_container_width=True):
                with st.spinner("Categorizing..." if lang == "en" else "Categorizando..."):
                    df_categorized = URLCategorizer.categorize_by_patterns(
                        df,
                        custom_patterns=st.session_state.custom_patterns
                    )
                    
                    st.session_state.df_categorized = df_categorized
                    st.session_state.df_processed = df_categorized  # Update main df
                    
                    st.success(f"✅ Categorized {len(df_categorized)} URLs" if lang == "en" else f"✅ {len(df_categorized)} URLs categorizadas")
                    st.balloons()
        
        # PREMIUM TIER: AI categorization
        else:
            st.subheader("⭐ AI-Powered Categorization" if lang == "en" else "⭐ Categorización con IA")
            
            st.info("🤖 AI analyzes keywords + URLs for semantic categorization and intent detection" if lang == "en" else "🤖 La IA analiza keywords + URLs para categorización semántica y detección de intención")
            
            # --- NUEVA SECCIÓN: Selector de IA y API Key segura ---
            col_ai1, col_ai2 = st.columns([1, 2])
            
            with col_ai1:
                ai_provider = st.selectbox(
                    "Select AI Engine:" if lang == "en" else "Motor de IA:",
                    options=["Groq (Fast & Free)", "OpenAI (GPT-4o)", "Anthropic (Claude 3.5)", "Google (Gemini)"],
                    index=0
                )
            
            with col_ai2:
                # Cambiar el label dinámicamente según el proveedor
                provider_name = ai_provider.split(" ")[0]
                api_key = st.text_input(
                    f"{provider_name} API Key:",
                    type="password",
                    help="Keys are processed entirely in your browser's memory and are never stored or logged." if lang == "en" else "Las claves se procesan en la memoria de tu navegador y NUNCA se almacenan ni registran."
                )
            
            # Trust Badge
            st.markdown(f"""
            <div style='font-size: 0.85rem; color: #10B981; margin-top: -10px; margin-bottom: 20px;'>
                🔒 <b>{'100% Secure & Private:' if lang == 'en' else '100% Seguro y Privado:'}</b> 
                {'Your API Key is only used for this session and is never sent to our servers.' if lang == 'en' else 'Tu API Key solo se usa en esta sesión y nunca se envía a nuestros servidores.'}
            </div>
            """, unsafe_allow_html=True)
            # --- FIN NUEVA SECCIÓN ---
            
            # Categorization method selector
            method = st.radio(
                "Method:" if lang == "en" else "Método:",
                options=['patterns', 'ai'],
                format_func=lambda x: "🔍 Patterns (Free)" if x == 'patterns' else "🤖 AI (Premium)",
                horizontal=True
            )
            
            if method == 'ai' and not api_key:
                st.warning("⚠️ Enter API key to use AI categorization" if lang == "en" else "⚠️ Ingresa tu API key para usar categorización IA")
            
            # Categorize button
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
                    with st.spinner(f"Categorizing with {provider_name}... This may take a few minutes" if lang == "en" else f"Categorizando con {provider_name}... Esto puede tomar unos minutos"):
                        try:
                            # Aquí se pasará el provider seleccionado a tu función core
                            df_categorized = URLCategorizer.categorize_with_ai(
                                df,
                                api_key=api_key,
                                provider=provider_name.lower(), # 'groq', 'openai', 'anthropic', 'google'
                                categories=st.session_state.categories,
                                batch_size=50
                            )
                            
                            st.session_state.df_categorized = df_categorized
                            st.session_state.df_processed = df_categorized
                            
                            st.success(f"✅ AI categorized {len(df_categorized)} URLs" if lang == "en" else f"✅ IA categorizó {len(df_categorized)} URLs")
                            st.balloons()
                        
                        except Exception as e:
                            st.error(f"❌ AI Error ({provider_name}): {str(e)}")
        
        # Show category statistics if categorized
        if st.session_state.df_categorized is not None:
            st.markdown("---")
            st.subheader("📊 Category Statistics" if lang == "en" else "📊 Estadísticas por Categoría")
            
            category_stats = URLCategorizer.get_category_stats(st.session_state.df_categorized)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Categories" if lang == "en" else "Categorías Totales", len(category_stats))
            with col2:
                top_cat = category_stats.iloc[0]['category'] if len(category_stats) > 0 else 'N/A'
                st.metric("Top Category" if lang == "en" else "Categoría Principal", top_cat)
            with col3:
                uncategorized = len(st.session_state.df_categorized[st.session_state.df_categorized['category'] == 'Other'])
                st.metric("Uncategorized" if lang == "en" else "Sin Categorizar", uncategorized)
            
            # Table
            st.dataframe(
                category_stats.style.format({
                    'traffic': '{:,.0f}',
                    'keywords': '{:,.0f}',
                    'urls': '{:,.0f}'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Preview categorized data
            with st.expander("📋 Preview Categorized Data" if lang == "en" else "📋 Vista Previa de Datos Categorizados"):
                # Mostrar Intent y Confidence si existen (IA)
                cols_to_show = ['category', 'keyword', 'url', 'traffic']
                if 'intent' in st.session_state.df_categorized.columns:
                    cols_to_show.extend(['intent', 'ai_confidence'])
                    
                st.dataframe(
                    st.session_state.df_categorized[cols_to_show].head(100),
                    use_container_width=True,
                    hide_index=True
                )
