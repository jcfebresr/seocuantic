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
