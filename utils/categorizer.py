import pandas as pd
import re
import json
import requests
import time
from typing import Dict, List

class URLCategorizer:
    """Categorize URLs based on fast pattern matching or Universal AI"""
    
    DEFAULT_PATTERNS = {
        "Blog": ["/blog", "/post", "/article", "/news", "/insights", "/articulo"],
        "Products": ["/product", "/shop", "/store", "/buy", "/cart", "/item"],
        "Services": ["/service", "/solution", "/offer", "/servicio"],
        "Tools": ["/tools", "/tool", "/herramienta", "/calculator", "/generator"],
        "Directory": ["/directory", "/directorio", "/listing"],
        "Docs": ["/doc", "/guide", "/help", "/support", "/faq", "/documentation"],
        "About": ["/about", "/company", "/team", "/contact", "/contacto"],
        "Home": ["/home", "/index", "inicio"],
        "Other": []
    }

    @staticmethod
    def validate_category_name(name: str) -> tuple:
        if not name or not name.strip():
            return False, "Category name cannot be empty"
        name = name.strip()
        if ' ' in name or '-' in name or '_' in name:
            return False, "Category must be ONE word only"
        if not name.isalnum():
            return False, "Category must contain only letters and numbers"
        if len(name) > 20:
            return False, "Category name too long (max 20 characters)"
        return True, ""

    @staticmethod
    def categorize_by_patterns(df: pd.DataFrame, custom_patterns: Dict[str, List[str]] = None) -> pd.DataFrame:
        """Categorización ultra rápida basada en Regex/Contains (Vectorizada)"""
        df_cat = df.copy()
        df_cat['category'] = 'Other'
        
        urls_lower = df_cat['url'].astype(str).str.lower()
        if 'keyword' in df_cat.columns:
            kw_lower = df_cat['keyword'].astype(str).str.lower()
        else:
            kw_lower = pd.Series("", index=df_cat.index)
            
        patterns_to_check = URLCategorizer.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            for cat, pats in custom_patterns.items():
                if cat in patterns_to_check:
                    patterns_to_check[cat].extend(pats)
                else:
                    patterns_to_check[cat] = pats

        # Lógica Especial para el "Home"
        home_mask = urls_lower.str.match(r'^https?://[^/]+/?$')
        df_cat.loc[home_mask & (df_cat['category'] == 'Other'), 'category'] = 'Home'

        # Regex masivo para el resto
        for category, patterns in patterns_to_check.items():
            if category == 'Other' or not patterns: 
                continue
                
            valid_patterns = [p.lower().strip() for p in patterns if p.strip()]
            if not valid_patterns:
                continue
                
            escaped_patterns = [re.escape(p) for p in valid_patterns]
            regex_pattern = '|'.join(escaped_patterns)
            
            url_match = urls_lower.str.contains(regex_pattern, regex=True, na=False)
            kw_match = kw_lower.str.contains(regex_pattern, regex=True, na=False)
            total_match = url_match | kw_match
            
            df_cat.loc[total_match & (df_cat['category'] == 'Other'), 'category'] = category

        return df_cat

    @staticmethod
    def categorize_with_ai(df: pd.DataFrame, api_key: str, provider: str, categories: List[str], batch_size: int = 50) -> pd.DataFrame:
        """
        Categorize URLs using AI with DEDUPLICATION optimization.
        Only categorizes unique URL+keyword combinations, then broadcasts back.
        """
        
        # PASO 1: Deduplicar por (url, keyword) para enviar menos datos a la IA
        df_original = df.copy()
        
        # Crear clave única
        df_original['_dedup_key'] = df_original['url'].astype(str) + '|' + df_original.get('keyword', '').astype(str)
        
        # Extraer solo URLs únicas
        df_unique = df_original.drop_duplicates(subset='_dedup_key', keep='first').copy()
        df_unique = df_unique.reset_index(drop=True)
        
        print(f"📊 Optimization: {len(df_original)} rows → {len(df_unique)} unique URLs to categorize")
        
        # PASO 2: Categorizar solo las URLs únicas
        total_rows = len(df_unique)
        df_unique['category'] = 'Other'
        df_unique['ai_confidence'] = 0.0
        
        for i in range(0, total_rows, batch_size):
            batch = df_unique.iloc[i:i+batch_size]
            batch_data = []
            for idx, row in batch.iterrows():
                batch_data.append({
                    'index': idx,
                    'keyword': row.get('keyword', ''),
                    'url': row.get('url', '')
                })
            
            prompt = f"Categorize these URLs into EXACTLY ONE of these categories: {', '.join(categories)}\n\n"
            prompt += "Rules:\n- Return ONLY the category name\n- Analyze both URL path and keyword\n\nURLs:\n"
            prompt += "\n".join([f"{j+1}. Keyword: '{d['keyword']}' | URL: {d['url']}" for j, d in enumerate(batch_data)])
            prompt += "\n\nReturn ONLY a numbered list (e.g., \n1. Blog\n2. Products):"
            
            # Sistema de reintentos
            max_retries = 3
            retry_delay = 5
            
            for attempt in range(max_retries):
                try:
                    result_text = ""
                    
                    if provider == 'groq':
                        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                        # Modelo ultra-rápido de Groq
                        data = {
                            "model": "llama-3.1-8b-instant",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0,
                            "max_tokens": 500
                        }
                        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                        headers=headers, json=data, timeout=30)
                        r.raise_for_status()
                        result_text = r.json()['choices'][0]['message']['content']
                    
                    elif provider == 'openai':
                        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                        data = {
                            "model": "gpt-4o-mini",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0,
                            "max_tokens": 500
                        }
                        r = requests.post("https://api.openai.com/v1/chat/completions", 
                                        headers=headers, json=data, timeout=30)
                        r.raise_for_status()
                        result_text = r.json()['choices'][0]['message']['content']
                        
                    elif provider == 'anthropic':
                        headers = {
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        }
                        data = {
                            "model": "claude-3-5-sonnet-20241022",
                            "max_tokens": 1024,
                            "messages": [{"role": "user", "content": prompt}]
                        }
                        r = requests.post("https://api.anthropic.com/v1/messages", 
                                        headers=headers, json=data, timeout=30)
                        r.raise_for_status()
                        result_text = r.json()['content'][0]['text']
                        
                    elif provider == 'google':
                        headers = {"Content-Type": "application/json"}
                        data = {"contents": [{"parts": [{"text": prompt}]}]}
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                        r = requests.post(url, headers=headers, json=data, timeout=30)
                        r.raise_for_status()
                        result_text = r.json()['candidates'][0]['content']['parts'][0]['text']
                    else:
                        raise ValueError(f"Proveedor '{provider}' no reconocido")

                    # Parseo de resultados
                    lines = [line.strip() for line in result_text.split('\n') if line.strip()]
                    for line in lines:
                        if not re.match(r'^\d+\.', line):
                            continue
                            
                        parts = re.split(r'^\d+\.\s*', line)
                        if len(parts) > 1:
                            category_raw = parts[1].strip().split(' ')[0]
                            category = re.sub(r'[^a-zA-Z0-9_áéíóúÁÉÍÓÚñÑ]', '', category_raw)
                            
                            matched_cat = 'Other'
                            for valid_cat in categories:
                                if valid_cat.lower() == category.lower():
                                    matched_cat = valid_cat
                                    break
                            
                            list_num_match = re.match(r'^(\d+)\.', line)
                            if list_num_match:
                                item_idx = int(list_num_match.group(1)) - 1
                                if item_idx < len(batch_data):
                                    real_idx = batch_data[item_idx]['index']
                                    df_unique.at[real_idx, 'category'] = matched_cat
                                    df_unique.at[real_idx, 'ai_confidence'] = 0.95
                    
                    # Éxito - salir del loop de reintentos
                    print(f"✅ Batch {i//batch_size + 1}/{(total_rows + batch_size - 1)//batch_size} processed")
                    break
                                    
                except requests.exceptions.HTTPError as err:
                    if err.response.status_code == 429:  # Rate limit
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            print(f"⏳ Rate limit hit. Waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                    
                    error_msg = err.response.text if hasattr(err.response, 'text') else str(err)
                    raise Exception(f"API Error: {error_msg}")
                    
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        print(f"⏳ Timeout. Retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(retry_delay)
                        continue
                    raise Exception("API timeout after retries")
                    
                except Exception as e:
                    raise Exception(f"Error: {str(e)}")
            
            # Pausa entre batches para evitar rate limits
            if i + batch_size < total_rows:
                time.sleep(1)
        
        # PASO 3: Broadcast categories de vuelta al dataframe original
        # Crear diccionario de mapeo: _dedup_key -> category
        category_map = df_unique.set_index('_dedup_key')['category'].to_dict()
        confidence_map = df_unique.set_index('_dedup_key')['ai_confidence'].to_dict()
        
        # Aplicar al dataframe original
        df_original['category'] = df_original['_dedup_key'].map(category_map).fillna('Other')
        df_original['ai_confidence'] = df_original['_dedup_key'].map(confidence_map).fillna(0.0)
        
        # Limpiar columna temporal
        df_original = df_original.drop(columns=['_dedup_key'])
        
        print(f"🎯 Categorization complete: {len(df_original)} rows categorized")
        
        return df_original

    @staticmethod
    def get_category_stats(df: pd.DataFrame) -> pd.DataFrame:
        """Get statistics per category"""
        if 'category' not in df.columns:
            return pd.DataFrame()
            
        stats = df.groupby('category').agg(
            keywords=('keyword', 'count'),
            traffic=('traffic', 'sum'),
            urls=('url', 'nunique')
        ).reset_index()
        
        return stats.sort_values('traffic', ascending=False)
