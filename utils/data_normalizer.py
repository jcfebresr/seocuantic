"""
Data Normalization
Cleans and standardizes CSV data
"""

import pandas as pd
import re
from urllib.parse import urlparse

class DataNormalizer:
    """Normalize and clean CSV data"""
    
    @staticmethod
    def normalize_dataframe(df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
        """
        Normalize dataframe to standard schema
        """
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
            df_norm['domain'] = df_norm['url'].apply(DataNormalizer.extract_root_domain)
        
        return df_norm
    
    @staticmethod
    def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and fix data types"""
        
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
        """Clean and normalize URL"""
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
    def extract_root_domain(url: str) -> str:
        """
        Extract ROOT domain from URL (removes subdomains)
        
        Examples:
            https://blog.airdev.co/post → airdev.co
            https://www.minimum-code.com/blog → minimum-code.com
            https://docs.zeroquode.com → zeroquode.com
        """
        if pd.isna(url) or not url:
            return ""
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www.
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Split by dots
            parts = domain.split('.')
            
            # If domain has 3+ parts (e.g., blog.airdev.co), extract root
            if len(parts) >= 3:
                # Check if last part is a TLD (co, uk, etc)
                common_tlds = ['co', 'uk', 'au', 'nz', 'in', 'za', 'jp', 'br', 'ar', 'mx']
                
                # If second-to-last is a common TLD (e.g., .co.uk, .com.ar)
                if parts[-2] in common_tlds:
                    # Keep last 3 parts: example.co.uk
                    root = '.'.join(parts[-3:])
                else:
                    # Keep last 2 parts: airdev.co, zeroquode.com
                    root = '.'.join(parts[-2:])
                
                return root
            
            # If 2 parts or less, return as is (example.com)
            return domain
        except:
            return ""
    
    @staticmethod
    def remove_url_params(url: str, params_to_remove: list = None) -> str:
        """Remove tracking parameters from URL"""
        if params_to_remove is None:
            params_to_remove = ['utm_source', 'utm_medium', 'utm_campaign', 
                              'fbclid', 'gclid', 'ref', 'source']
        
        if pd.isna(url) or not url:
            return url
        
        try:
            parsed = urlparse(url)
            if not parsed.query:
                return url
            
            from urllib.parse import parse_qs, urlencode
            params = parse_qs(parsed.query)
            
            cleaned_params = {k: v for k, v in params.items() 
                            if k not in params_to_remove}
            
            if cleaned_params:
                query = urlencode(cleaned_params, doseq=True)
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{query}"
            else:
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except:
            return url
    
    @staticmethod
    def deduplicate_urls(df: pd.DataFrame) -> pd.DataFrame:
        """
        Deduplicate URLs and aggregate metrics
        """
        if 'url' not in df.columns:
            return df
        
        agg_dict = {
            'keyword': 'first',
            'domain': 'first'
        }
        
        if 'traffic' in df.columns:
            agg_dict['traffic'] = 'sum'
        if 'volume' in df.columns:
            agg_dict['volume'] = 'sum'
        if 'position' in df.columns:
            agg_dict['position'] = 'mean'
        if 'kd' in df.columns:
            agg_dict['kd'] = 'mean'
        
        df_dedup = df.groupby('url', as_index=False).agg(agg_dict)
        
        return df_dedup


# WRAPPER FUNCTION for app.py
def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """Wrapper function for backward compatibility"""
    return df  # Ya está normalizado por detect_source_and_map
