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
        
        # Flatten column names
        col_names = ['keyword', 'competitor_count', 'competitor_domains', 'competitor_urls', 'competitor_traffic']
        
        if 'volume' in df_gaps.columns:
            col_names.insert(1, 'volume')  # Insert after keyword
        if 'kd' in df_gaps.columns:
            idx = 2 if 'volume' in df_gaps.columns else 1
            col_names.insert(idx, 'kd')
        if 'position' in df_gaps.columns:
            col_names.append('best_competitor_position')
        
        gaps.columns = col_names
        
        # Convert competitor_count to int (handle NaN values first)
        gaps['competitor_count'] = gaps['competitor_count'].fillna(0).astype(int)
        
        # Add "Your Position" column (always "Not Ranking" for gaps)
        # Insert after kd or volume
        insert_idx = 1
        if 'volume' in gaps.columns:
            insert_idx += 1
        if 'kd' in gaps.columns:
            insert_idx += 1
        
        gaps.insert(insert_idx, 'your_position', 'Not Ranking')
        
        # Sort by volume (high opportunity first)
        if 'volume' in gaps.columns:
            gaps = gaps.sort_values('volume', ascending=False)
        else:
            gaps = gaps.sort_values('competitor_traffic', ascending=False)
        
        return gaps
