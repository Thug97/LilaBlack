import os
import pandas as pd
import pyarrow.parquet as pq
import streamlit as st

def load_all_data(base_path):
    """
    Loads all Parquet files from the directory structure, decodes events,
    and returns a consolidated DataFrame.
    """
    frames = []
    
    if not os.path.exists(base_path):
        return pd.DataFrame()
        
    for item in os.listdir(base_path):
        day_path = os.path.join(base_path, item)
        if os.path.isdir(day_path) and item.startswith('February_'):
            for f in os.listdir(day_path):
                filepath = os.path.join(day_path, f)
                if not os.path.isfile(filepath):
                    continue
                try:
                    t = pq.read_table(filepath)
                    df_temp = t.to_pandas()
                    df_temp['date'] = item.replace('_', ' ')
                    frames.append(df_temp)
                except Exception as e:
                    print(f"Failed to read {filepath}: {e}")
                    continue
                    
    if not frames:
        return pd.DataFrame()
    
    df = pd.concat(frames, ignore_index=True)
    
    # Decode the event column
    if 'event' in df.columns:
        df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
    
    # Clean match_id: strip the '.nakama-N' suffix safely
    if 'match_id' in df.columns:
        df['match_id'] = df['match_id'].astype(str).str.split('.nakama').str[0]
    
    # Clean user_id: decode bytes if needed
    if 'user_id' in df.columns:
        df['user_id'] = df['user_id'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else str(x))
    
    # Process the 'ts' column
    if 'ts' in df.columns:
        # The parquet stores the Unix epoch in SECONDS (~1.77 billion) but typed as timestamp[ms].
        # In newer pandas, this becomes datetime64[ms]. Extracting it.astype('int64') 
        # gives us back the raw ~1.77 billion integer which is the timestamp in seconds.
        if pd.api.types.is_datetime64_any_dtype(df['ts']):
            ts_sec = df['ts'].astype('int64')
        else:
            ts_sec = df['ts']
            
        df['ts_sec'] = ts_sec.astype(float)
        
        # Normalize per match to get relative timeline in seconds
        if 'match_id' in df.columns:
            min_ts_per_match = df.groupby('match_id')['ts_sec'].transform('min')
            df['ts'] = df['ts_sec'] - min_ts_per_match
            df = df.drop(columns=['ts_sec'])
            df = df.sort_values(by=['match_id', 'ts']).reset_index(drop=True)
        else:
            df['ts'] = df['ts_sec'] - df['ts_sec'].min()
            df = df.drop(columns=['ts_sec'])
            df = df.sort_values('ts').reset_index(drop=True)
            
    return df
