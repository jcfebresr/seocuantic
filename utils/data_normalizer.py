"""
Data Normalization
"""

import pandas as pd
import re
from urllib.parse import urlparse

class DataNormalizer:
    """Normalize and clean CSV data"""
    
    @staticmethod
    def normalize_dataframe(df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
        df_norm = pd.DataFrame()
        
        for standard_col, csv_col in column_mapping.items():
            if csv_col and csv_col in df.columns:
                df_norm[standard_col] = df[csv_col]
            else:
                if standard_col in ['volume', 'traffic', 'cpc']:
                    df_norm[standard_col] = 0
                elif standard_col in ['position', 'kd']:
                    df_norm[standard_col] = None
                else:
                    df_norm[standard_col] = None
        
        required = ['keyword', 'url']
        for col in required:
            if col not in df_norm.columns:
                df_norm[col] = None
        
        df_norm = DataNormalizer._clean_data(df_norm)
        
        if 'url' in df_norm.columns:
            df_norm['domain'] = df_norm['url'].apply(DataNormalizer.extract_domain)
        
        return df_norm
    
    @staticmethod
    def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
        if 'url' in df.columns:
            df['url'] = df['url'].apply(DataNormalizer.clean_url)
        
        if 'keyword' in df.columns:
            df['keyword'] = df['keyword'].astype(str).str.strip()
        
        numeric_cols = ['volume', 'traffic', 'position', 'kd', 'cpc']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        if 'volume' in df.columns:
            df['volume'] = df['volume'].fillna(0).astype(int)
        if 'traffic' in df.columns:
            df['traffic'] = df['traffic'].fillna(0).astype(int)
        
        return df
    
    @staticmethod
    def clean_url(url: str) -> str:
        if pd.isna(url) or not url:
            return ""
        
        url = str(url).strip()
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        url = url.rstrip('/')
        
        try:
            parsed = urlparse(url)
            domain_lower = parsed.netloc.lower()
            url = f"{parsed.scheme}://{domain_lower}{parsed.path}"
            if parsed.query:
                url += f"?{parsed.query}"
        except:
            pass
        
        return url
    
    @staticmethod
    def extract_domain(url: str) -> str:
        if pd.isna(url) or not url:
            return ""
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain.lower()
        except:
            return ""


# WRAPPER FUNCTION for app.py
def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """Wrapper function for backward compatibility"""
    return df  # Ya está normalizado por detect_source_and_map
