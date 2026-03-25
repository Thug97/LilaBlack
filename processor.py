import pandas as pd
import numpy as np

# Official per-map coordinate conversion parameters
# Formula: u = (x - origin_x) / scale, v = (z - origin_z) / scale
# pixel_x = u * img_size, pixel_y = (1 - v) * img_size  (Y is flipped, image origin is top-left)
MAP_PARAMS = {
    'AmbroseValley': {'scale': 900,  'origin_x': -370, 'origin_z': -473},
    'GrandRift':     {'scale': 581,  'origin_x': -290, 'origin_z': -290},
    'Lockdown':      {'scale': 1000, 'origin_x': -500, 'origin_z': -500},
}

def calibrate_coordinates(df, map_id=None):
    """
    Convert world (x, z) coordinates to minimap-scaled coordinates using
    the official per-map origin and scale parameters.
    Falls back to min-max scaling if map_id is unknown.
    """
    if df.empty:
        return df

    params = MAP_PARAMS.get(map_id) if map_id else None

    if params:
        scale = params['scale']
        ox = params['origin_x']
        oz = params['origin_z']
        # Step 1: World to UV (0-1 range)
        u = (df['x'] - ox) / scale
        v = (df['z'] - oz) / scale
        # Step 2: UV to pixel-like coordinates (0-100 range for Plotly)
        df['x_scaled'] = u * 100
        df['z_scaled'] = (1 - v) * 100  # Y is flipped (image origin is top-left)
    else:
        # Fallback: dynamic min-max scaling for unknown maps
        min_x, max_x = df['x'].min(), df['x'].max()
        min_z, max_z = df['z'].min(), df['z'].max()
        range_x = (max_x - min_x) if (max_x - min_x) != 0 else 1
        range_z = (max_z - min_z) if (max_z - min_z) != 0 else 1
        df['x_scaled'] = ((df['x'] - min_x) / range_x) * 100
        df['z_scaled'] = 100 - ((df['z'] - min_z) / range_z) * 100  # Flip Y

    return df

def flag_bots(df):
    """
    Identifies if a user_id is a bot based strictly on short numeric IDs.
    """
    if df.empty:
        df['is_bot_heuristic'] = False
        df['is_bot'] = False
        return df
        
    # Definitive Identity Check: bots are strictly short numeric IDs (e.g., '1440', '382')
    df['is_bot'] = df['user_id'].astype(str).str.len() < 20
    df['is_bot_heuristic'] = False
    
    return df

def compute_coverage(df, grid_size=20):
    """
    Calculate Map Coverage % based on scaled coordinates.
    """
    if df.empty:
        return 0.0, None
        
    df['x_bin'] = pd.cut(df['x_scaled'], bins=grid_size, labels=False)
    df['z_bin'] = pd.cut(df['z_scaled'], bins=grid_size, labels=False)
    
    total_cells = grid_size * grid_size
    # Focus on human players using definitive ID logic
    human_df = df[~df['is_bot']]
    
    if human_df.empty:
        return 0.0, df
        
    visited_cells = human_df.drop_duplicates(subset=['x_bin', 'z_bin'])
    coverage = (len(visited_cells) / total_cells) * 100
    
    return coverage, df
