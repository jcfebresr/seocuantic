import pandas as pd
from typing import Dict, List, Tuple

def get_domain_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrae estadísticas por dominio del dataframe normalizado.
    
    Returns:
        DataFrame con: domain, keywords, traffic, urls
    """
    stats = df.groupby('domain').agg({
        'keyword': 'count',
        'traffic': 'sum',
        'url': 'nunique'
    }).reset_index()
    
    stats.columns = ['domain', 'keywords', 'traffic', 'urls']
    stats = stats.sort_values('traffic', ascending=False)
    
    return stats

def validate_competitors(
    total_domains: int,
    tier: str
) -> Tuple[bool, str, int]:
    """
    Valida límites de competidores según tier.
    
    Returns:
        (is_valid, message, max_competitors)
    """
    limits = {
        'free': 2,
        'premium': 10
    }
    
    max_comp = limits.get(tier, 2)
    competitors = total_domains - 1  # -1 por el dominio del cliente
    
    if competitors > max_comp:
        return False, f"Tier {tier.upper()}: max {max_comp} competitors", max_comp
    
    return True, "", max_comp

def mark_project_domain(
    df: pd.DataFrame,
    selected_domain: str
) -> pd.DataFrame:
    """
    Añade columna is_client al dataframe.
    
    Args:
        df: DataFrame normalizado
        selected_domain: Dominio del proyecto del usuario
    
    Returns:
        DataFrame con columna is_client (bool)
    """
    df = df.copy()
    df['is_client'] = df['domain'] == selected_domain
    return df

def get_competitor_list(
    df: pd.DataFrame,
    selected_domain: str
) -> List[str]:
    """
    Retorna lista de dominios competidores.
    """
    all_domains = df['domain'].unique().tolist()
    return [d for d in all_domains if d != selected_domain]
