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
            'url': lambda x: ' | '.join(x.astype(str).unique()),  # Competitor URLs
            'traffic': 'sum',
        }
        
        if 'volume' in df_gaps.columns:
            agg_dict['volume'] = 'first'
        
        if 'kd' in df_gaps.columns:
            agg_dict['kd'] = 'first'
        
        if 'position' in df_gaps.columns:
            agg_dict['position'] = lambda x: min([p for p in x if pd.notna(p) and p > 0], default=None)
        
        gaps = df_gaps.groupby('keyword').agg(agg_dict).reset_index()
        
        # Flatten multi-level columns manually
        # gaps structure: keyword, (domain, nunique), (domain, <lambda>), url, traffic, [volume], [kd], [position]
        
        result = pd.DataFrame()
        result['keyword'] = gaps.iloc[:, 0]  # keyword
        
        # Domain columns are multi-level: (domain, nunique) and (domain, <lambda>)
        result['competitor_count'] = gaps.iloc[:, 1]  # (domain, nunique)
        result['competitor_domains'] = gaps.iloc[:, 2]  # (domain, <lambda>)
        
        # Find position of other columns
        col_idx = 3
        result['competitor_urls'] = gaps.iloc[:, col_idx]
        col_idx += 1
        
        result['competitor_traffic'] = gaps.iloc[:, col_idx]
        col_idx += 1
        
        # Add optional columns
        if 'volume' in df_gaps.columns:
            result.insert(1, 'volume', gaps.iloc[:, col_idx])
            col_idx += 1
        
        if 'kd' in df_gaps.columns:
            idx = 2 if 'volume' in result.columns else 1
            result.insert(idx, 'kd', gaps.iloc[:, col_idx])
            col_idx += 1
        
        if 'position' in df_gaps.columns:
            result['best_competitor_position'] = gaps.iloc[:, col_idx]
        
        # Convert competitor_count to int
        result['competitor_count'] = pd.to_numeric(result['competitor_count'], errors='coerce').fillna(0).astype(int)
        
        # Add "Your Position" column (always "Not Ranking" for gaps)
        # Insert after kd or volume
        insert_idx = 1
        if 'volume' in result.columns:
            insert_idx += 1
        if 'kd' in result.columns:
            insert_idx += 1
        
        result.insert(insert_idx, 'your_position', 'Not Ranking')
        
        # Sort by volume (high opportunity first)
        if 'volume' in result.columns:
            result = result.sort_values('volume', ascending=False)
        else:
            result = result.sort_values('competitor_traffic', ascending=False)
        
        return result
    
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
    
    @staticmethod
    def classify_competitive_zones(df: pd.DataFrame, quick_win_threshold: int = 100) -> pd.DataFrame:
        """
        Classify keywords into competitive zones
        
        Zones:
        - 🟢 Dominio: Only YOU rank (no competition)
        - 🔴 Guerra: YOU + competitors rank (direct battle)
        - 🟡 QuickWin: Only competitors, low volume (easy to capture)
        - 🟣 Gap: Only competitors, high volume (difficult, requires investment)
        
        Args:
            df: DataFrame with is_client column
            quick_win_threshold: Volume threshold for QuickWin vs Gap (default 100)
        
        Returns:
            DataFrame with: keyword, zone, volume, your_position, competitor_count, competitor_domains
        """
        if 'is_client' not in df.columns:
            return pd.DataFrame()
        
        # Separate client and competitor data
        client_keywords = set(df[df['is_client'] == True]['keyword'].unique())
        competitor_keywords = set(df[df['is_client'] == False]['keyword'].unique())
        
        # Build result dataframe
        all_keywords = list(client_keywords.union(competitor_keywords))
        result = pd.DataFrame({'keyword': all_keywords})
        
        # Classify zones
        def get_zone(keyword):
            in_client = keyword in client_keywords
            in_competitors = keyword in competitor_keywords
            
            if in_client and not in_competitors:
                return '🟢 Dominio'
            elif in_client and in_competitors:
                return '🔴 Guerra'
            elif not in_client and in_competitors:
                # Check volume for QuickWin vs Gap
                if 'volume' in df.columns:
                    vol = df[df['keyword'] == keyword]['volume'].max()
                    if vol < quick_win_threshold:
                        return '🟡 QuickWin'
                    else:
                        return '🟣 Gap'
                else:
                    return '🟡 QuickWin'  # Default if no volume data
            else:
                return 'Unknown'
        
        result['zone'] = result['keyword'].apply(get_zone)
        
        # Add volume
        if 'volume' in df.columns:
            result['volume'] = result['keyword'].apply(lambda k: df[df['keyword'] == k]['volume'].max())
        
        # Add KD
        if 'kd' in df.columns:
            result['kd'] = result['keyword'].apply(lambda k: df[df['keyword'] == k]['kd'].max())
        
        # Add your position
        def get_your_position(keyword):
            client_data = df[(df['keyword'] == keyword) & (df['is_client'] == True)]
            if len(client_data) > 0 and 'position' in df.columns:
                positions = [p for p in client_data['position'] if pd.notna(p) and p > 0]
                if positions:
                    return int(min(positions))
            return 'Not Ranking'
        
        result['your_position'] = result['keyword'].apply(get_your_position)
        
        # Add competitor count and domains
        def get_competitor_info(keyword):
            comp_data = df[(df['keyword'] == keyword) & (df['is_client'] == False)]
            if len(comp_data) > 0:
                domains = comp_data['domain'].unique()
                return len(domains), ' | '.join(domains)
            return 0, '-'
        
        result[['competitor_count', 'competitor_domains']] = result['keyword'].apply(
            lambda k: pd.Series(get_competitor_info(k))
        )
        
        # Sort by zone priority then volume
        zone_order = {'🟢 Dominio': 0, '🔴 Guerra': 1, '🟡 QuickWin': 2, '🟣 Gap': 3}
        result['zone_rank'] = result['zone'].map(zone_order)
        
        if 'volume' in result.columns:
            result = result.sort_values(['zone_rank', 'volume'], ascending=[True, False])
        else:
            result = result.sort_values('zone_rank')
        
        result = result.drop('zone_rank', axis=1)
        
        return result
    
    @staticmethod
    def get_competitive_zones_stats(zones_df: pd.DataFrame) -> Dict:
        """
        Get summary stats for competitive zones
        
        Returns:
            {
                'dominio_count': int,
                'guerra_count': int,
                'quickwin_count': int,
                'gap_count': int
            }
        """
        if zones_df is None or len(zones_df) == 0:
            return {
                'dominio_count': 0,
                'guerra_count': 0,
                'quickwin_count': 0,
                'gap_count': 0
            }
        
        return {
            'dominio_count': len(zones_df[zones_df['zone'] == '🟢 Dominio']),
            'guerra_count': len(zones_df[zones_df['zone'] == '🔴 Guerra']),
            'quickwin_count': len(zones_df[zones_df['zone'] == '🟡 QuickWin']),
            'gap_count': len(zones_df[zones_df['zone'] == '🟣 Gap'])
        }
