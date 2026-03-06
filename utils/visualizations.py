"""
SEO Visualizations with Plotly
Charts for traffic, categories, competitive zones
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Optional

class SEOVisualizations:
    """Interactive charts for SEO analysis"""
    
    # Color scheme
    COLORS = {
        'primary': '#8B5CF6',
        'secondary': '#4C1D95',
        'success': '#10B981',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'info': '#3B82F6',
        'dark': '#0F172A',
        'light': '#F1F5F9'
    }
    
    @staticmethod
    def traffic_by_domain(df: pd.DataFrame) -> Optional[go.Figure]:
        """
        Bar chart: Total traffic by domain
        
        Args:
            df: DataFrame with 'domain' and 'traffic' columns
        
        Returns:
            Plotly Figure or None
        """
        if 'domain' not in df.columns or 'traffic' not in df.columns:
            return None
        
        # Aggregate traffic by domain
        domain_traffic = df.groupby('domain')['traffic'].sum().reset_index()
        domain_traffic = domain_traffic.sort_values('traffic', ascending=False)
        
        # Identify project vs competitors
        if 'is_client' in df.columns:
            # Get project domain
            project_domains = df[df['is_client'] == True]['domain'].unique()
            
            # Color bars: green for project, purple for competitors
            colors = [SEOVisualizations.COLORS['success'] if d in project_domains 
                     else SEOVisualizations.COLORS['primary'] for d in domain_traffic['domain']]
        else:
            colors = [SEOVisualizations.COLORS['primary']] * len(domain_traffic)
        
        fig = go.Figure(data=[
            go.Bar(
                x=domain_traffic['domain'],
                y=domain_traffic['traffic'],
                marker_color=colors,
                text=domain_traffic['traffic'],
                texttemplate='%{text:,.0f}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Traffic: %{y:,.0f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Traffic by Domain',
            xaxis_title='Domain',
            yaxis_title='Total Traffic',
            template='plotly_dark',
            plot_bgcolor=SEOVisualizations.COLORS['dark'],
            paper_bgcolor=SEOVisualizations.COLORS['dark'],
            font=dict(color=SEOVisualizations.COLORS['light']),
            height=500
        )
        
        return fig
    
    @staticmethod
    def traffic_by_category(df: pd.DataFrame, domain: Optional[str] = None) -> Optional[go.Figure]:
        """
        Pie chart: Traffic distribution by category
        
        Args:
            df: DataFrame with 'category' and 'traffic' columns
            domain: Optional filter by specific domain
        
        Returns:
            Plotly Figure or None
        """
        if 'category' not in df.columns or 'traffic' not in df.columns:
            return None
        
        # Filter by domain if specified
        df_filtered = df[df['domain'] == domain] if domain and 'domain' in df.columns else df
        
        if len(df_filtered) == 0:
            return None
        
        # Aggregate by category
        cat_traffic = df_filtered.groupby('category')['traffic'].sum().reset_index()
        cat_traffic = cat_traffic.sort_values('traffic', ascending=False)
        
        # Remove 'Other' if zero traffic
        cat_traffic = cat_traffic[cat_traffic['traffic'] > 0]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=cat_traffic['category'],
                values=cat_traffic['traffic'],
                hole=0.4,
                marker=dict(
                    colors=px.colors.qualitative.Set3,
                    line=dict(color=SEOVisualizations.COLORS['dark'], width=2)
                ),
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Traffic: %{value:,.0f}<br>%{percent}<extra></extra>'
            )
        ])
        
        title = f'Traffic Distribution by Category'
        if domain:
            title += f' - {domain}'
        
        fig.update_layout(
            title=title,
            template='plotly_dark',
            plot_bgcolor=SEOVisualizations.COLORS['dark'],
            paper_bgcolor=SEOVisualizations.COLORS['dark'],
            font=dict(color=SEOVisualizations.COLORS['light']),
            height=500
        )
        
        return fig
    
    @staticmethod
    def domain_category_heatmap(df: pd.DataFrame) -> Optional[go.Figure]:
        """
        Heatmap: Traffic by Domain x Category
        
        Args:
            df: DataFrame with 'domain', 'category', 'traffic'
        
        Returns:
            Plotly Figure or None
        """
        if not all(col in df.columns for col in ['domain', 'category', 'traffic']):
            return None
        
        # Pivot table
        pivot = df.pivot_table(
            index='domain',
            columns='category',
            values='traffic',
            aggfunc='sum',
            fill_value=0
        )
        
        # Sort by total traffic
        pivot['_total'] = pivot.sum(axis=1)
        pivot = pivot.sort_values('_total', ascending=False)
        pivot = pivot.drop('_total', axis=1)
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='Viridis',
            text=pivot.values,
            texttemplate='%{text:,.0f}',
            textfont={"size": 10},
            hovertemplate='Domain: %{y}<br>Category: %{x}<br>Traffic: %{z:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Traffic Heatmap: Domain × Category',
            xaxis_title='Category',
            yaxis_title='Domain',
            template='plotly_dark',
            plot_bgcolor=SEOVisualizations.COLORS['dark'],
            paper_bgcolor=SEOVisualizations.COLORS['dark'],
            font=dict(color=SEOVisualizations.COLORS['light']),
            height=max(400, len(pivot) * 50)
        )
        
        return fig
    
    @staticmethod
    def top_keywords_chart(df: pd.DataFrame, top_n: int = 20) -> Optional[go.Figure]:
        """
        Horizontal bar chart: Top N keywords by traffic
        
        Args:
            df: DataFrame with 'keyword' and 'traffic'
            top_n: Number of top keywords to show
        
        Returns:
            Plotly Figure or None
        """
        if not all(col in df.columns for col in ['keyword', 'traffic']):
            return None
        
        # Get top N keywords
        top_kw = df.groupby('keyword')['traffic'].sum().reset_index()
        top_kw = top_kw.sort_values('traffic', ascending=False).head(top_n)
        
        # Reverse for horizontal bar (highest on top)
        top_kw = top_kw.sort_values('traffic', ascending=True)
        
        fig = go.Figure(data=[
            go.Bar(
                x=top_kw['traffic'],
                y=top_kw['keyword'],
                orientation='h',
                marker_color=SEOVisualizations.COLORS['primary'],
                text=top_kw['traffic'],
                texttemplate='%{text:,.0f}',
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Traffic: %{x:,.0f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=f'Top {top_n} Keywords by Traffic',
            xaxis_title='Traffic',
            yaxis_title='Keyword',
            template='plotly_dark',
            plot_bgcolor=SEOVisualizations.COLORS['dark'],
            paper_bgcolor=SEOVisualizations.COLORS['dark'],
            font=dict(color=SEOVisualizations.COLORS['light']),
            height=max(500, top_n * 25),
            margin=dict(l=200)  # More space for long keywords
        )
        
        return fig
    
    @staticmethod
    def competitive_zones_pie(zones_df: pd.DataFrame) -> Optional[go.Figure]:
        """
        Pie chart: Distribution of competitive zones
        
        Args:
            zones_df: DataFrame with 'zone' column
        
        Returns:
            Plotly Figure or None
        """
        if 'zone' not in zones_df.columns:
            return None
        
        # Count keywords per zone
        zone_counts = zones_df['zone'].value_counts().reset_index()
        zone_counts.columns = ['zone', 'count']
        
        # Custom colors per zone
        color_map = {
            '🟢 Dominio': SEOVisualizations.COLORS['success'],
            '🔴 Guerra': SEOVisualizations.COLORS['danger'],
            '🟡 QuickWin': SEOVisualizations.COLORS['warning'],
            '🟣 Gap': SEOVisualizations.COLORS['info']
        }
        
        colors = [color_map.get(z, SEOVisualizations.COLORS['primary']) for z in zone_counts['zone']]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=zone_counts['zone'],
                values=zone_counts['count'],
                marker=dict(
                    colors=colors,
                    line=dict(color=SEOVisualizations.COLORS['dark'], width=2)
                ),
                textinfo='label+percent+value',
                hovertemplate='<b>%{label}</b><br>Keywords: %{value:,.0f}<br>%{percent}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Competitive Zones Distribution',
            template='plotly_dark',
            plot_bgcolor=SEOVisualizations.COLORS['dark'],
            paper_bgcolor=SEOVisualizations.COLORS['dark'],
            font=dict(color=SEOVisualizations.COLORS['light']),
            height=500
        )
        
        return fig
    
    @staticmethod
    def category_comparison_stacked(df: pd.DataFrame) -> Optional[go.Figure]:
        """
        Stacked bar chart: Category traffic comparison across domains
        
        Args:
            df: DataFrame with 'domain', 'category', 'traffic'
        
        Returns:
            Plotly Figure or None
        """
        if not all(col in df.columns for col in ['domain', 'category', 'traffic']):
            return None
        
        # Pivot
        pivot = df.pivot_table(
            index='domain',
            columns='category',
            values='traffic',
            aggfunc='sum',
            fill_value=0
        )
        
        # Sort by total
        pivot['_total'] = pivot.sum(axis=1)
        pivot = pivot.sort_values('_total', ascending=False)
        pivot = pivot.drop('_total', axis=1)
        
        # Create traces for each category
        fig = go.Figure()
        
        for category in pivot.columns:
            fig.add_trace(go.Bar(
                name=category,
                x=pivot.index,
                y=pivot[category],
                text=pivot[category],
                texttemplate='%{text:,.0f}',
                textposition='inside',
                hovertemplate=f'<b>{category}</b><br>%{{x}}<br>Traffic: %{{y:,.0f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title='Category Traffic Comparison (Stacked)',
            xaxis_title='Domain',
            yaxis_title='Traffic',
            barmode='stack',
            template='plotly_dark',
            plot_bgcolor=SEOVisualizations.COLORS['dark'],
            paper_bgcolor=SEOVisualizations.COLORS['dark'],
            font=dict(color=SEOVisualizations.COLORS['light']),
            height=600,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            )
        )
        
        return fig
    
    @staticmethod
    def position_distribution(df: pd.DataFrame) -> Optional[go.Figure]:
        """
        Histogram: Position distribution (Top 3, Top 10, Top 20, etc)
        
        Args:
            df: DataFrame with 'position' column
        
        Returns:
            Plotly Figure or None
        """
        if 'position' not in df.columns:
            return None
        
        # Filter valid positions
        df_pos = df[df['position'].notna() & (df['position'] > 0)].copy()
        
        if len(df_pos) == 0:
            return None
        
        # Create buckets
        df_pos['bucket'] = pd.cut(
            df_pos['position'],
            bins=[0, 3, 10, 20, 50, 100, float('inf')],
            labels=['Top 3', 'Top 10', 'Top 20', 'Top 50', 'Top 100', '100+']
        )
        
        bucket_counts = df_pos['bucket'].value_counts().reset_index()
        bucket_counts.columns = ['bucket', 'count']
        
        # Sort by bucket order
        bucket_order = ['Top 3', 'Top 10', 'Top 20', 'Top 50', 'Top 100', '100+']
        bucket_counts['bucket'] = pd.Categorical(bucket_counts['bucket'], categories=bucket_order, ordered=True)
        bucket_counts = bucket_counts.sort_values('bucket')
        
        # Color gradient
        colors = [SEOVisualizations.COLORS['success'], SEOVisualizations.COLORS['info'], 
                 SEOVisualizations.COLORS['warning'], SEOVisualizations.COLORS['danger'],
                 '#94A3B8', '#64748B']
        
        fig = go.Figure(data=[
            go.Bar(
                x=bucket_counts['bucket'],
                y=bucket_counts['count'],
                marker_color=colors[:len(bucket_counts)],
                text=bucket_counts['count'],
                texttemplate='%{text:,.0f}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Keywords: %{y:,.0f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Position Distribution',
            xaxis_title='Position Bucket',
            yaxis_title='Number of Keywords',
            template='plotly_dark',
            plot_bgcolor=SEOVisualizations.COLORS['dark'],
            paper_bgcolor=SEOVisualizations.COLORS['dark'],
            font=dict(color=SEOVisualizations.COLORS['light']),
            height=500
        )
        
        return fig
