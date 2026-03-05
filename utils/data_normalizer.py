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
        
        Args:
            df: Original dataframe
            column_mapping: Dict mapping standard_name -> csv_column_name
        
        Returns:
            Normalized dataframe with standard column names
        """
        df_norm = pd.DataFrame()
        
        # Map columns
        for standard_col, csv_col in column_mapping.items():
            if csv_col and csv_col in df.columns:
                df_norm[standard_col] = df[csv_col]
            else:
                # Create empty column with defaults
                if standard_col in ['volume', 'traffic', 'cpc']:
                    df_norm[standard_col] = 0
                elif standard_col in ['position', 'kd']:
                    df_norm[standard_col] = None
                else:
                    df_norm[standard_col] = None
        
        # Ensure required columns exist
        required = ['keyword', 'url']
        for col in required:
            if col not in df_norm.columns:
                df_norm[col] = None
        
        # Clean data
        df_norm = DataNormalizer._clean_data(df_norm)
        
        # Extract domain
        if 'url' in df_norm.columns:
            df_norm['domain'] = df_norm['url'].apply(DataNormalizer.extract_domain)
        
        return df_norm
    
    @staticmethod
    def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and fix data types"""
        
        # Clean URLs
        if 'url' in df.columns:
            df['url'] = df['url'].apply(DataNormalizer.clean_url)
        
        # Clean keyword (strip whitespace)
        if 'keyword' in df.columns:
            df['keyword'] = df['keyword'].astype(str).str.strip()
        
        # Convert numeric columns
        numeric_cols = ['volume', 'traffic', 'position', 'kd', 'cpc']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Fill NaN for numeric columns
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
        
        # Add http:// if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Remove trailing slash
        url = url.rstrip('/')
        
        # Lowercase domain only
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
        """Extract domain from URL"""
        if pd.isna(url) or not url:
            return ""
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove www.
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain.lower()
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
            
            # Parse query params
            from urllib.parse import parse_qs, urlencode
            params = parse_qs(parsed.query)
            
            # Remove tracking params
            cleaned_params = {k: v for k, v in params.items() 
                            if k not in params_to_remove}
            
            # Rebuild URL
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
        Groups by unique URL and sums traffic/volume
        """
        if 'url' not in df.columns:
            return df
        
        # Group by URL
        agg_dict = {
            'keyword': 'first',  # Keep first keyword
            'domain': 'first'
        }
        
        # Add aggregations for numeric columns
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
