"""
SEO Intelligence Analysis
Cannibalization, Gaps, Competitive Zones
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class SEOIntelligence:
    """SEO competitive intelligence tools"""
    
    @staticmethod
    def detect_cannibalization(df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect keyword cannibalization (multiple URLs for same keyword)
        Analyzes client's project and uses ranking position for severity.
        
        Severity Rules:
        - 🔴 Critical: At least 1 URL in Top 3 (fighting for podium)
        - 🟡 Warning: At least 1 URL in Top 10 (fighting on page 1)
        - ⚪ Minor: All URLs in page 2+ (low priority)
        
        Returns:
            DataFrame with: keyword, urls_count, urls_list, positions_list, 
                          categories_list, severity, total_traffic
        """
        if 'is_client' not in df.columns:
            return pd.DataFrame()
        
        # Filter only client URLs
        df_client = df[df['is_client'] == True].copy()
        
        if len(df_client) == 0:
            return pd.DataFrame()
        
        # Get client domain (assuming single project domain)
        client_domain = df_client['domain'].iloc[0] if 'domain' in df_client.columns else 'Unknown'
        
        # Dynamic aggregation dict (in case columns are missing)
        agg_dict = {
            'url': ['count', lambda x: ' | '.join(x.astype(str).unique())],
            'traffic': 'sum'
        }
        
        # If position exists, save it for severity calculation
        if 'position' in df_client.columns:
            agg_dict['position'] = [
                lambda x: ' | '.join([str(int(p)) if pd.notna(p) else '-' for p in x]),  # For display
                lambda x: list(x)  # For internal logic
            ]
        
        # If category exists, show it to detect "Intent Mismatch"
        if 'category' in df_client.columns:
            agg_dict['category'] = lambda x: ' | '.join(x.fillna('Unknown').astype(str))
        
        # Group by keyword
        cannibalization = df_client.groupby('keyword').agg(agg_dict).reset_index()
        
        # Flatten multi-level column names
        col_names = ['keyword', 'urls_count', 'urls_list', 'total_traffic']
        if 'position' in df_client.columns:
            col_names.extend(['positions_list', 'positions_raw'])
        if 'category' in df_client.columns:
            col_names.append('categories_list')
        
        cannibalization.columns = col_names
        
        # Filter only keywords with 2+ URLs
        cannibalization = cannibalization[cannibalization['urls_count'] >= 2].copy()
        
        if len(cannibalization) == 0:
            return pd.DataFrame()
        
        # Calculate severity based on POSITION (Premium Logic)
        def calculate_severity(row):
            if 'positions_raw' in row.index:
                # Filter valid positions > 0
                valid_positions = [p for p in row['positions_raw'] if pd.notna(p) and p > 0]
                if not valid_positions:
                    return '⚪ Minor'
                
                min_pos = min(valid_positions)
                
                if min_pos <= 3:
                    return '🔴 Critical'  # At least 1 in Top 3 fighting
                elif min_pos <= 10:
                    return '🟡 Warning'   # At least 1 in page 1 fighting
                else:
                    return '⚪ Minor'     # Fighting in page 2+
            else:
                # Fallback if CSV has no position column
                return '🟡 Warning' if row['urls_count'] >= 2 else '⚪ Minor'
        
        cannibalization['severity'] = cannibalization.apply(calculate_severity, axis=1)
        
        # Add client domain column
        cannibalization.insert(0, 'your_domain', client_domain)
        
        # Add "Your Best Position" column
        if 'positions_raw' in cannibalization.columns:
            def get_best_position(positions_raw):
                valid_positions = [p for p in positions_raw if pd.notna(p) and p > 0]
                if not valid_positions:
                    return 'Not Ranking'
                return str(int(min(valid_positions)))
            
            cannibalization.insert(1, 'your_best_position', cannibalization['positions_raw'].apply(get_best_position))
        else:
            cannibalization.insert(1, 'your_best_position', 'Not Ranking')
        
        # Remove raw column used for calculation
        if 'positions_raw' in cannibalization.columns:
            cannibalization = cannibalization.drop('positions_raw', axis=1)
        
        # Sort by severity then by wasted traffic
        severity_order = {'🔴 Critical': 0, '🟡 Warning': 1, '⚪ Minor': 2}
        cannibalization['severity_rank'] = cannibalization['severity'].map(severity_order)
        cannibalization = cannibalization.sort_values(['severity_rank', 'total_traffic'], ascending=[True, False])
        cannibalization = cannibalization.drop('severity_rank', axis=1)
        
        return cannibalization
    
    @staticmethod
    def get_cannibalization_stats(cannibalization_df: pd.DataFrame) -> Dict:
        """
        Get summary stats for cannibalization
        
        Returns:
            {
                'total_cannibal_keywords': int,
                'critical_count': int,
                'warning_count': int,
                'minor_count': int,
                'affected_traffic': int
            }
        """
        if cannibalization_df is None or len(cannibalization_df) == 0:
            return {
                'total_cannibal_keywords': 0,
                'critical_count': 0,
                'warning_count': 0,
                'minor_count': 0,
                'affected_traffic': 0
            }
        
        critical = len(cannibalization_df[cannibalization_df['severity'] == '🔴 Critical'])
        warning = len(cannibalization_df[cannibalization_df['severity'] == '🟡 Warning'])
        minor = len(cannibalization_df[cannibalization_df['severity'] == '⚪ Minor'])
        
        return {
            'total_cannibal_keywords': len(cannibalization_df),
            'critical_count': critical,
            'warning_count': warning,
            'minor_count': minor,
            'affected_traffic': int(cannibalization_df['total_traffic'].sum())
        }
    
    @staticmethod
    def detect_content_gaps(df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect content gaps: keywords competitors have but YOU don't
        
        Returns:
            DataFrame with: your_domain, your_position, keyword, competitor_domains, 
                          competitor_count, competitor_traffic, volume, best_competitor_position
        """
        if 'is_client' not in df.columns:
            return pd.DataFrame()
        
        # Get client domain
        df_client = df[df['is_client'] == True]
        client_domain = df_client['domain'].iloc[0] if len(df_client) > 0 and 'domain' in df_client.columns else 'Unknown'
        
        # Get client and competitor keywords
        client_keywords = set(df_client['keyword'].unique())
        df_competitors = df[df['is_client'] == False].copy()
        
        if len(df_competitors) == 0:
            return pd.DataFrame()
        
        # Filter keywords that competitors have but client doesn't
        df_gaps = df_competitors[~df_competitors['keyword'].isin(client_keywords)].copy()
        
        if len(df_gaps) == 0:
            return pd.DataFrame()
        
        # Aggregate by keyword
        agg_dict = {
            'domain': ['nunique', lambda x: ' | '.join(x.unique())],
            'traffic': 'sum',
        }
        
        if 'volume' in df_gaps.columns:
            agg_dict['volume'] = 'first'
        
        if 'position' in df_gaps.columns:
            agg_dict['position'] = lambda x: min([p for p in x if pd.notna(p) and p > 0], default=None)
        
        gaps = df_gaps.groupby('keyword').agg(agg_dict).reset_index()
        
        # Flatten column names
        col_names = ['keyword', 'competitor_count', 'competitor_domains', 'competitor_traffic']
        
        if 'volume' in df_gaps.columns:
            col_names.append('volume')
        if 'position' in df_gaps.columns:
            col_names.append('best_competitor_position')
        
        gaps.columns = col_names
        
        # Add client domain column at the beginning
        gaps.insert(0, 'your_domain', client_domain)
        
        # Add "Your Position" column (always "Not Ranking" for gaps)
        gaps.insert(1, 'your_position', 'Not Ranking')
        
        # Sort by volume (high opportunity first)
        if 'volume' in gaps.columns:
            gaps = gaps.sort_values('volume', ascending=False)
        else:
            gaps = gaps.sort_values('competitor_traffic', ascending=False)
        
        return gaps
    
    @staticmethod
    def get_content_gaps_stats(gaps_df: pd.DataFrame) -> Dict:
        """
        Get summary stats for content gaps
        
        Returns:
            {
                'total_gap_keywords': int,
                'high_volume_gaps': int (volume > 100),
                'total_opportunity_volume': int,
                'avg_competitor_count': float
            }
        """
        if gaps_df is None or len(gaps_df) == 0:
            return {
                'total_gap_keywords': 0,
                'high_volume_gaps': 0,
                'total_opportunity_volume': 0,
                'avg_competitor_count': 0
            }
        
        high_volume = 0
        total_volume = 0
        
        if 'volume' in gaps_df.columns:
            high_volume = len(gaps_df[gaps_df['volume'] > 100])
            total_volume = int(gaps_df['volume'].sum())
        
        avg_competitors = gaps_df['competitor_count'].mean()
        
        return {
            'total_gap_keywords': len(gaps_df),
            'high_volume_gaps': high_volume,
            'total_opportunity_volume': total_volume,
            'avg_competitor_count': round(avg_competitors, 1)
        }
