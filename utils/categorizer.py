import pandas as pd
import re

class URLCategorizer:
    # 1. Cargamos los patrones semilla directamente (basados en tu JSON)
    DEFAULT_PATTERNS = {
        "Blog": ["/blog/", "/articles/", "/news/", "/post/", "/entry/", "how to", "guide", "tutorial", "que es", "como "],
        "Products": ["/product/", "/p/", "/item/", "/shop/", "/buy/", "review", "model", "caracteristicas"],
        "Services": ["/services/", "/service/", "/solutions/", "agencia", "agency"],
        "Collections": ["/category/", "/collection/", "/c/", "/catalog/"],
        "Docs": ["/docs/", "/documentation/", "/help/", "/support/"],
        "Tools": ["/tools/", "herramienta", "calculator"],
        "Home": ["/home", "/index", "inicio"]
    }

    @staticmethod
    def validate_category_name(category_name):
        if not category_name or len(category_name.strip()) == 0:
            return False, "Name cannot be empty"
        if len(category_name.split()) > 1:
            return False, "Category must be a SINGLE WORD"
        return True, ""

    @staticmethod
    def categorize_by_patterns(df, custom_patterns=None):
        """Categorización ultra rápida basada en patrones Regex/Contains"""
        # Hacemos una copia para no alterar el original en memoria
        df_cat = df.copy()
        
        # 1. Por defecto, todas nacen en 'Other'
        df_cat['category'] = 'Other'
        
        # Pre-procesamos URLs y Keywords en minúsculas para que el match no falle por mayúsculas
        urls_lower = df_cat['url'].astype(str).str.lower()
        
        # Si existe la columna keyword, la usamos, si no, creamos una serie vacía
        if 'keyword' in df_cat.columns:
            kw_lower = df_cat['keyword'].astype(str).str.lower()
        else:
            kw_lower = pd.Series("", index=df_cat.index)
            
        # 2. Unimos patrones por defecto con los que agregues tú desde la interfaz
        patterns_to_check = URLCategorizer.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            for cat, pats in custom_patterns.items():
                if cat in patterns_to_check:
                    patterns_to_check[cat].extend(pats)
                else:
                    patterns_to_check[cat] = pats

        # 3. Lógica Especial para el "Home" (Raíz del dominio)
        # Identifica URLs que terminan en .com/, .es/ o son exactamente "/"
        home_mask = urls_lower.str.match(r'^https?://[^/]+/?$')
        df_cat.loc[home_mask & (df_cat['category'] == 'Other'), 'category'] = 'Home'

        # 4. Iterar sobre las categorías y buscar si CONTIENEN el patrón
        for category, patterns in patterns_to_check.items():
            if not patterns: 
                continue
                
            # Creamos el patrón regex combinando todos los items de la lista con el operador OR '|'
            # Ejemplo: "/blog/|how to|guide"
            valid_patterns = [p.lower().strip() for p in patterns if p.strip()]
            if not valid_patterns:
                continue
                
            # Escapamos los caracteres especiales (como los slashes /) para que no rompan el regex
            escaped_patterns = [re.escape(p) for p in valid_patterns]
            regex_pattern = '|'.join(escaped_patterns)
            
            # Buscamos en URL
            url_match = urls_lower.str.contains(regex_pattern, regex=True, na=False)
            # Buscamos en Keyword
            kw_match = kw_lower.str.contains(regex_pattern, regex=True, na=False)
            
            # Máscara total: si coincide en la URL o en la Keyword
            total_match = url_match | kw_match
            
            # Asignamos la categoría SOLO a los que siguen siendo 'Other' (respeta la prioridad en cascada)
            df_cat.loc[total_match & (df_cat['category'] == 'Other'), 'category'] = category

        return df_cat
    
    @staticmethod
    def get_category_stats(df):
        if 'category' not in df.columns:
            return pd.DataFrame()
            
        stats = df.groupby('category').agg(
            keywords=('keyword', 'count'),
            traffic=('traffic', 'sum'),
            urls=('url', 'nunique')
        ).reset_index()
        
        # Ordenar por tráfico descendente
        return stats.sort_values('traffic', ascending=False)
