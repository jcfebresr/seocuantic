"""
SEO Data Visualizations
Interactive charts with Plotly
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

class SEOVisualizations:
    """Create interactive visualizations for SEO data"""
    
    # Color schemes
    COLORS_PRIMARY = ['#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444']
    COLORS_ZONES = {
        '🟢 Dominio': '#10B981',
        '🔴 Guerra': '#EF4444',
        '🟡 QuickWin': '#F59E0B',
        '🟣 Gap': '#8B5CF6'
    }
    
    @staticmethod
    def traffic_by_category(df: pd.DataFrame) -> go.Figure:
        """
        Bar chart: Traffic distribution by category
        """
        if 'category' not in df.columns or 'traffic' not in df.columns:
            return None
        
        category_traffic = df.groupby('category')['traffic'].sum().reset_index()
        category_traffic = category_traffic.sort_values('traffic', ascending=False)
        
        fig = px.bar(
            category_traffic,
            x='category',
            y='traffic',
            title='Traffic Distribution by Category',
            labels={'category': 'Category', 'traffic': 'Traffic'},
            color='traffic',
            color_continuous_scale='Purples'
        )
        
        fig.update_layout(
            template='plotly_dark',
            xaxis_tickangle=-45,
            height=400
        )
        
        return fig
    
    @staticmethod
    def domain_category_heatmap(df: pd.DataFrame) -> go.Figure:
        """
        Heatmap: Domains vs Categories
        Shows which categories each domain dominates
        """
        if 'domain' not in df.columns or 'category' not in df.columns:
            return None
        
        # Create pivot table: domains as rows, categories as columns
        pivot = df.groupby(['domain', 'category']).size().reset_index(name='count')
        pivot_table = pivot.pivot(index='domain', columns='category', values='count').fillna(0)
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='Purples',
            text=pivot_table.values,
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Keywords")
        ))
        
        fig.update_layout(
            title='Domain vs Category Heatmap',
            xaxis_title='Category',
            yaxis_title='Domain',
            template='plotly_dark',
            height=max(400, len(pivot_table.index) * 30)
        )
        
        return fig
    
    @staticmethod
    def top_keywords_chart(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
        """
        Horizontal bar chart: Top keywords by traffic
        """
        if 'keyword' not in df.columns or 'traffic' not in df.columns:
            return None
        
        top_keywords = df.nlargest(top_n, 'traffic')[['keyword', 'traffic']]
        
        fig = px.bar(
            top_keywords,
            y='keyword',
            x='traffic',
            orientation='h',
            title=f'Top {top_n} Keywords by Traffic',
            labels={'keyword': 'Keyword', 'traffic': 'Traffic'},
            color='traffic',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            template='plotly_dark',
            height=max(400, top_n * 25),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig
    
    @staticmethod
    def competitive_zones_pie(zones_df: pd.DataFrame) -> go.Figure:
        """
        Pie chart: Distribution of competitive zones
        """
        if 'zone' not in zones_df.columns:
            return None
        
        zone_counts = zones_df['zone'].value_counts().reset_index()
        zone_counts.columns = ['zone', 'count']
        
        colors = [SEOVisualizations.COLORS_ZONES.get(z, '#94A3B8') for z in zone_counts['zone']]
        
        fig = go.Figure(data=[go.Pie(
            labels=zone_counts['zone'],
            values=zone_counts['count'],
            marker=dict(colors=colors),
            hole=0.3,
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            title='Competitive Zones Distribution',
            template='plotly_dark',
            height=400
        )
        
        return fig
    
    @staticmethod
    def position_distribution(df: pd.DataFrame) -> go.Figure:
        """
        Histogram: Keyword position distribution
        Shows how many keywords rank in Top 3, Top 10, etc.
        """
        if 'position' not in df.columns:
            return None
        
        # Filter valid positions
        positions = df[df['position'].notna() & (df['position'] > 0)]['position']
        
        if len(positions) == 0:
            return None
        
        fig = px.histogram(
            positions,
            nbins=20,
            title='Keyword Position Distribution',
            labels={'value': 'Position', 'count': 'Keywords'},
            color_discrete_sequence=['#8B5CF6']
        )
        
        # Add vertical lines for Top 3, Top 10
        fig.add_vline(x=3.5, line_dash="dash", line_color="green", annotation_text="Top 3")
        fig.add_vline(x=10.5, line_dash="dash", line_color="orange", annotation_text="Top 10")
        
        fig.update_layout(
            template='plotly_dark',
            xaxis_title='Position',
            yaxis_title='Number of Keywords',
            height=400
        )
        
        return fig
    
    @staticmethod
    def traffic_by_domain(df: pd.DataFrame) -> go.Figure:
        """
        Bar chart: Traffic comparison by domain
        """
        if 'domain' not in df.columns or 'traffic' not in df.columns:
            return None
        
        domain_traffic = df.groupby('domain')['traffic'].sum().reset_index()
        domain_traffic = domain_traffic.sort_values('traffic', ascending=False)
        
        # Color client vs competitors
        colors = []
        if 'is_client' in df.columns:
            for domain in domain_traffic['domain']:
                is_client = df[df['domain'] == domain]['is_client'].iloc[0]
                colors.append('#10B981' if is_client else '#8B5CF6')
        else:
            colors = SEOVisualizations.COLORS_PRIMARY * len(domain_traffic)
        
        fig = go.Figure(data=[go.Bar(
            x=domain_traffic['domain'],
            y=domain_traffic['traffic'],
            marker_color=colors
        )])
        
        fig.update_layout(
            title='Traffic by Domain',
            xaxis_title='Domain',
            yaxis_title='Traffic',
            template='plotly_dark',
            xaxis_tickangle=-45,
            height=400
        )
        
        return fig
