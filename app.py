import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
from data_loader import load_all_data
from processor import calibrate_coordinates, flag_bots, compute_coverage

# Setup Streamlit
st.set_page_config(layout="wide", page_title="Player Journey Viz")
st.title("Player Journey Visualization Tool - LILA BLACK")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "player_data")
MINIMAP_DIR = os.path.join(DATA_DIR, "minimaps")

@st.cache_data
def get_data(version=1):
    df = load_all_data(DATA_DIR)
    if not df.empty:
        df = flag_bots(df)
        
        # Calibrate coordinates per map using official origin/scale parameters
        dfs = []
        for map_id, group in df.groupby('map_id'):
            dfs.append(calibrate_coordinates(group.copy(), map_id=map_id))
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
            
    return df

df_full = get_data(version=12)

if df_full.empty:
    st.error(f"No data loaded from {DATA_DIR}. Please check the folder.")
    st.stop()

# Sidebar Match/Map Selection
st.sidebar.header("Filters")

# 1. Date Filter
dates = df_full['date'].unique() if 'date' in df_full.columns else ["All"]
selected_date = st.sidebar.selectbox("Select Date", dates)
if selected_date != "All":
    df_date = df_full[df_full['date'] == selected_date]
else:
    df_date = df_full

# 2. Map Filter
selected_map = st.sidebar.selectbox("Select Map", df_date['map_id'].unique())
df_map_calibrated = df_date[df_date['map_id'] == selected_map]

# 3. Match Filter
matches = df_map_calibrated['match_id'].unique()
selected_match = st.sidebar.selectbox("Select Match", matches)
df_match = df_map_calibrated[df_map_calibrated['match_id'] == selected_match]

# Time Slider
st.sidebar.subheader("Playback / Timeline")
min_ts = df_match['ts'].min()
max_ts = df_match['ts'].max()

if pd.isna(min_ts) or pd.isna(max_ts):
    min_ts = 0.0
    max_ts = 1.0

if min_ts == max_ts:
    max_ts = min_ts + 1.0

diff = float(max_ts) - float(min_ts)
safe_step = 1.0 if diff >= 2.0 else max(round(diff / 10.0, 3), 0.1)

selected_time = st.sidebar.slider(
    "Match Duration (Seconds):",
    min_value=float(min_ts),
    max_value=float(max_ts),
    value=float(max_ts),
    step=float(safe_step),
    format="%.1f s"
)
df_filtered = df_match[df_match['ts'] <= selected_time].copy()

heatmap_type = st.sidebar.radio("Heatmap Overlay Type", ["Movement Density (Dead Zones)", "Combat Zones (Kills/Deaths)"])

# Render Minimap Image
minimap_files = {
    "AmbroseValley": "AmbroseValley_Minimap.png",
    "GrandRift": "GrandRift_Minimap.png",
    "Lockdown": "Lockdown_Minimap.jpg"
}

img_path = os.path.join(MINIMAP_DIR, minimap_files.get(selected_map, ""))
bg_image = None
if os.path.exists(img_path):
    bg_image = Image.open(img_path)

@st.cache_data
def get_cached_coverage(df_in):
    cov, _ = compute_coverage(df_in, 20)
    return cov

# Analytics
st.subheader("Level Design Analytics")
coverage_match = get_cached_coverage(df_match)
coverage_map = get_cached_coverage(df_map_calibrated)
st.metric("Map Coverage % (Match Humans)", f"{coverage_match:.1f}%")
st.metric("Map Coverage % (All Matches Humans)", f"{coverage_map:.1f}%")

# Visualization
st.subheader("Match Minimap & Overlays")

if not df_filtered.empty:
    fig = go.Figure()

    # Add background image
    if bg_image:
        fig.add_layout_image(
            dict(
                source=bg_image,
                xref="x",
                yref="y",
                x=0,
                y=100,
                sizex=100,
                sizey=100,
                sizing="stretch",
                opacity=0.6,
                layer="below"
            )
        )
        fig.update_yaxes(range=[0, 100], scaleanchor="x", scaleratio=1)
        fig.update_xaxes(range=[0, 100])
    
    # Heatmap overlays
    if heatmap_type == "Movement Density (Dead Zones)":
        pos_data = df_filtered[df_filtered['event'].isin(['Position', 'BotPosition'])]
        if not pos_data.empty:
            fig.add_trace(go.Histogram2dContour(
                x=pos_data['x_scaled'],
                y=pos_data['z_scaled'],
                colorscale='YlOrRd',
                reversescale=False,
                opacity=0.4,
                showscale=False,
                name="Traffic Density"
            ))
    else:
        combat_data = df_filtered[df_filtered['event'].isin(['Kill', 'Killed', 'BotKill', 'BotKilled'])]
        if not combat_data.empty:
            fig.add_trace(go.Histogram2dContour(
                x=combat_data['x_scaled'],
                y=combat_data['z_scaled'],
                colorscale='Reds',
                reversescale=False,
                opacity=0.6,
                showscale=False,
                name="Combat Zones"
            ))

    # Path Tracking: Separate Humans and Bots visually via distinct markers/lines
    is_bot_mask = df_filtered.get('is_bot', False) | df_filtered.get('is_bot_heuristic', False)
    
    human_pos = df_filtered[(df_filtered['event'] == 'Position') & (~is_bot_mask)]
    if not human_pos.empty:
        fig.add_trace(go.Scatter(
            x=human_pos['x_scaled'],
            y=human_pos['z_scaled'],
            mode='markers',
            marker=dict(color='white', size=4, opacity=0.7),
            name='Human Path'
        ))
    
    # Support both explicitly labeled BotPositions and dynamically flagged bot entities
    bot_pos = df_filtered[((df_filtered['event'] == 'Position') & is_bot_mask) | (df_filtered['event'] == 'BotPosition')]
    if not bot_pos.empty:
        fig.add_trace(go.Scatter(
            x=bot_pos['x_scaled'],
            y=bot_pos['z_scaled'],
            mode='markers',
            marker=dict(color='#FFA500', size=8, symbol='triangle-up', line=dict(width=1, color='black'), opacity=0.9),
            name='Bot Path'
        ))

    # Event Markers
    event_markers = {
        'Loot': {'color': 'green', 'symbol': 'star', 'size': 14},
        'Kill': {'color': 'red', 'symbol': 'x', 'size': 14},
        'Killed': {'color': 'black', 'symbol': 'x', 'size': 14},
        'BotKill': {'color': 'darkred', 'symbol': 'x-open', 'size': 10},
        'BotKilled': {'color': 'gray', 'symbol': 'x-open', 'size': 10},
        'KilledByStorm': {'color': 'purple', 'symbol': 'diamond', 'size': 14}
    }
    
    for ev_type, style in event_markers.items():
        ev_df = df_filtered[df_filtered['event'] == ev_type]
        if not ev_df.empty:
            fig.add_trace(go.Scatter(
                x=ev_df['x_scaled'],
                y=ev_df['z_scaled'],
                mode='markers',
                marker=dict(color=style['color'], size=style['size'], symbol=style['symbol']),
                name=ev_type
            ))
            
    fig.update_layout(
        title=f"Tracking for {selected_match}",
        width=900,
        height=900,
        plot_bgcolor='rgb(15,15,15)'
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data available.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>Created by Adithya</p>", unsafe_allow_html=True)
st.markdown("**Deployment Note:** To share this tool online via a shareable link, push this folder to a GitHub repository, open [Streamlit Community Cloud](https://share.streamlit.io/), and click '**Deploy an app**'. Select `app.py` from your repository, and it will be instantly hosted for free!")
