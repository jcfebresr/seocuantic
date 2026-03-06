"""
URL Categorization
Free: Pattern matching
Premium: AI with Claude API
"""

import pandas as pd
import re
from typing import Dict, List, Optional

class URLCategorizer:
    """Categorize URLs based on patterns or AI"""
    
    # Default categories and their URL patterns
    DEFAULT_PATTERNS = {
        'Blog': ['/blog', '/post', '/article', '/news', '/insights'],
        'Products': ['/product', '/shop', '/store', '/buy', '/cart'],
        'Services': ['/service', '/solution', '/offer'],
        'Home': ['/', '/home', '/index'],
        'About': ['/about', '/company', '/team', '/contact'],
        'Docs': ['/doc', '/guide', '/help', '/support', '/faq'],
        'Other': []
    }
    
    @staticmethod
    def categorize_by_patterns(
        df: pd.DataFrame,
        custom_patterns: Dict[str, List[str]] = None
    ) -> pd.DataFrame:
        """
        Categorize URLs using pattern matching (Free tier)
        """
        df = df.copy()
        
        # Merge default + custom patterns
        patterns = URLCategorizer.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            patterns.update(custom_patterns)
        
        def match_category(url: str) -> str:
            if pd.isna(url) or not url:
                return 'Other'
            
            url_lower = url.lower()
            
            # Try each category's patterns
            for category, pattern_list in patterns.items():
                if category == 'Other':
                    continue
                    
                for pattern in pattern_list:
                    if pattern in url_lower:
                        return category
            
            return 'Other'
        
        df['category'] = df['url'].apply(match_category)
        
        return df
    
    @staticmethod
    def categorize_with_ai(
        df: pd.DataFrame,
        api_key: str,
        categories: List[str],
        batch_size: int = 50
    ) -> pd.DataFrame:
        """
        Categorize URLs using Claude AI (Premium tier)
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install anthropic: pip install anthropic")
        
        df = df.copy()
        client = anthropic.Anthropic(api_key=api_key)
        
        # Process in batches
        total_rows = len(df)
        df['category'] = 'Other'
        df['ai_confidence'] = 0.0
        
        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i:i+batch_size]
            
            # Prepare batch data
            batch_data = []
            for idx, row in batch.iterrows():
                batch_data.append({
                    'index': idx,
                    'keyword': row.get('keyword', ''),
                    'url': row.get('url', '')
                })
            
            # Create prompt
            prompt = f"""Categorize these URLs into ONE of these categories: {', '.join(categories)}

Rules:
- Return ONLY the category name (one word)
- Analyze both the URL path and keyword intent
- Be consistent

URLs to categorize:
{chr(10).join([f"{i+1}. Keyword: '{d['keyword']}' | URL: {d['url']}" for i, d in enumerate(batch_data)])}

Return format (one per line):
1. CategoryName
2. CategoryName
...
"""
            
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Parse response
                result_text = response.content[0].text.strip()
                lines = [line.strip() for line in result_text.split('\n') if line.strip()]
                
                # Extract categories
                for j, line in enumerate(lines):
                    if j >= len(batch_data):
                        break
                    
                    # Remove numbering (1., 2., etc)
                    category = re.sub(r'^\d+\.\s*', '', line).strip()
                    
                    # Validate category
                    if category not in categories:
                        category = 'Other'
                    
                    idx = batch_data[j]['index']
                    df.at[idx, 'category'] = category
                    df.at[idx, 'ai_confidence'] = 0.9
            
            except Exception as e:
                print(f"AI categorization error for batch {i}: {e}")
        
        return df
    
    @staticmethod
    def get_category_stats(df: pd.DataFrame) -> pd.DataFrame:
        """
        Get statistics per category
        """
        if 'category' not in df.columns:
            return pd.DataFrame()
        
        stats = df.groupby('category').agg({
            'keyword': 'count',
            'traffic': 'sum',
            'url': 'nunique'
        }).reset_index()
        
        stats.columns = ['category', 'keywords', 'traffic', 'urls']
        stats = stats.sort_values('traffic', ascending=False)
        
        return stats
    
    @staticmethod
    def validate_category_name(name: str) -> tuple:
        """
        Validate category name (must be 1 word only)
        """
        if not name or not name.strip():
            return False, "Category name cannot be empty"
        
        name = name.strip()
        
        # Check single word
        if ' ' in name or '-' in name or '_' in name:
            return False, "Category must be ONE word only (no spaces, hyphens, underscores)"
        
        # Check alphanumeric
        if not name.isalnum():
            return False, "Category must contain only letters and numbers"
        
        # Check length
        if len(name) > 20:
            return False, "Category name too long (max 20 characters)"
        
        return True, ""
