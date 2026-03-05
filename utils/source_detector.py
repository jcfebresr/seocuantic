"""
Source Detection for SEO Tool CSVs
Detects which tool exported the CSV based on column patterns
"""

from difflib import get_close_matches
from typing import Tuple, Dict, Optional

class SourceDetector:
    """Detect CSV source and map columns"""
    
    # Detection patterns for each source
    SOURCES = {
        "seranking": {
            "name": "SEranking",
            "markers": ["Keyword", "Search vol.", "Position", "URL", "Traffic"],
            "icon": "🔵",
            "mappings": {
                "keyword": ["Keyword", "keyword"],
                "volume": ["Search vol.", "Search Volume", "volume"],
                "traffic": ["Traffic", "traffic", "Current organic traffic"],
                "url": ["URL", "url", "Page", "Current URL"],
                "position": ["Position", "position", "Pos", "Current position"],
                "kd": ["Difficulty", "KD", "Keyword Difficulty"],
                "cpc": ["CPC"],
                "previous_position": ["Previous position"]
            }
        },
        "ahrefs_organic_keywords": {
            "name": "Ahrefs (Organic Keywords)",
            "markers": ["Keyword", "Volume", "KD", "Current position", "Current URL", "Current organic traffic"],
            "icon": "🟠",
            "mappings": {
                "keyword": ["Keyword"],
                "volume": ["Volume"],
                "traffic": ["Current organic traffic", "Organic traffic"],
                "url": ["Current URL", "URL"],
                "position": ["Current position", "Position"],
                "kd": ["KD"],
                "cpc": ["CPC"],
                "previous_position": ["Previous position"]
            }
        },
        "ahrefs_top_pages": {
            "name": "Ahrefs (Top Pages)",
            "markers": ["URL", "Traffic", "Top keyword", "Top keyword: Volume"],
            "icon": "🟠",
            "mappings": {
                "url": ["URL"],
                "traffic": ["Traffic"],
                "keyword": ["Top keyword"],
                "volume": ["Top keyword: Volume"],
                "position": ["Top keyword: Position"]
            }
        },
        "ahrefs_generic": {
            "name": "Ahrefs",
            "markers": ["Keyword", "Volume", "Traffic", "URL", "Position"],
            "icon": "🟠",
            "mappings": {
                "keyword": ["Keyword", "Top keyword"],
                "volume": ["Volume", "Search volume", "Top keyword: Volume"],
                "traffic": ["Traffic", "Current organic traffic"],
                "url": ["URL", "Page", "Current URL"],
                "position": ["Position", "Pos", "Current position", "Top keyword: Position"],
                "kd": ["KD", "Keyword Difficulty"],
                "cpc": ["CPC"]
            }
        },
        "semrush": {
            "name": "Semrush",
            "markers": ["Keyword", "Position", "Search Volume", "Traffic (%)", "CPC (USD)"],
            "icon": "🟢",
            "mappings": {
                "keyword": ["Keyword"],
                "volume": ["Search Volume", "Volume"],
                "traffic": ["Traffic (%)", "Traffic"],
                "url": ["Landing Page", "URL"],
                "position": ["Position", "Pos"],
                "kd": ["Keyword Difficulty", "KD"],
                "cpc": ["CPC (USD)", "CPC"]
            }
        },
        "gsc": {
            "name": "Google Search Console",
            "markers": ["Query", "Impressions", "Clicks"],
            "icon": "🔴",
            "mappings": {
                "keyword": ["Query", "Keyword"],
                "volume": ["Impressions"],
                "traffic": ["Clicks"],
                "url": ["Top pages", "URL", "Page"],
                "position": ["Position"]
            }
        }
    }
    
    @staticmethod
    def detect_source(columns: list) -> Tuple[str, float]:
        """
        Detect CSV source based on column names
        
        Returns:
            (source_name, confidence_score)
        """
        columns_lower = [col.lower().strip() for col in columns]
        
        best_match = "unknown"
        best_score = 0.0
        
        # Check sources in priority order (most specific first)
        priority_order = [
            "ahrefs_organic_keywords",
            "ahrefs_top_pages", 
            "seranking",
            "semrush",
            "gsc",
            "ahrefs_generic"
        ]
        
        for source_key in priority_order:
            if source_key not in SourceDetector.SOURCES:
                continue
                
            source_data = SourceDetector.SOURCES[source_key]
            markers = source_data["markers"]
            markers_lower = [m.lower() for m in markers]
            
            # Count how many markers are present (exact match)
            exact_matches = 0
            for marker_lower in markers_lower:
                for col_lower in columns_lower:
                    if marker_lower == col_lower:
                        exact_matches += 1
                        break
            
            # Calculate score
            score = exact_matches / len(markers)
            
            if score > best_score:
                best_score = score
                best_match = source_key
        
        # If confidence too low, mark as unknown
        if best_score < 0.5:
            best_match = "unknown"
        
        return best_match, best_score
    
    @staticmethod
    def map_columns(columns: list, source: str = None) -> Dict[str, Optional[str]]:
        """
        Map CSV columns to standard schema
        
        Args:
            columns: List of column names from CSV
            source: Detected source (optional)
        
        Returns:
            Dictionary mapping standard_name -> csv_column_name
        """
        if source is None or source == "unknown":
            # Try all sources
            source, _ = SourceDetector.detect_source(columns)
        
        if source == "unknown":
            # Fuzzy matching fallback
            return SourceDetector._fuzzy_map(columns)
        
        mappings = SourceDetector.SOURCES[source]["mappings"]
        result = {}
        
        for standard_col, possible_names in mappings.items():
            matched = None
            
            # Try exact match first
            for csv_col in columns:
                if csv_col in possible_names:
                    matched = csv_col
                    break
            
            # Try case-insensitive match
            if not matched:
                for csv_col in columns:
                    if csv_col.lower() in [p.lower() for p in possible_names]:
                        matched = csv_col
                        break
            
            result[standard_col] = matched
        
        return result
    
    @staticmethod
    def _fuzzy_map(columns: list) -> Dict[str, Optional[str]]:
        """Fuzzy matching for unknown sources"""
        standard_keywords = {
            "keyword": ["keyword", "query", "term", "search term"],
            "url": ["url", "page", "landing page", "link"],
            "volume": ["volume", "search volume", "searches", "impressions"],
            "traffic": ["traffic", "clicks", "visits"],
            "position": ["position", "pos", "rank", "ranking"],
            "kd": ["difficulty", "kd", "keyword difficulty", "competition"],
            "cpc": ["cpc", "cost per click"]
        }
        
        result = {}
        columns_lower = [col.lower() for col in columns]
        
        for standard, keywords in standard_keywords.items():
            match = None
            
            # Try exact substring match
            for csv_col, csv_col_lower in zip(columns, columns_lower):
                if any(keyword in csv_col_lower for keyword in keywords):
                    match = csv_col
                    break
            
            # Try fuzzy match
            if not match:
                matches = get_close_matches(standard, columns_lower, n=1, cutoff=0.6)
                if matches:
                    idx = columns_lower.index(matches[0])
                    match = columns[idx]
            
            result[standard] = match
        
        return result
    
    @staticmethod
    def get_source_info(source: str) -> Dict:
        """Get display info for a source"""
        if source in SourceDetector.SOURCES:
            return SourceDetector.SOURCES[source]
        return {
            "name": "Unknown",
            "icon": "❓",
            "markers": []
        }
