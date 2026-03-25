# ARCHITECTURE

## Project Structure
- `data_loader.py`: Resiliently scans the directory structure for Apache Parquet files, manages deserialization, byte-string decoding, relative timestamp conversion, and caches resulting DataFrames into memory.
- `processor.py`: Contains the official World-to-Minimap coordinate conversion and the Bot Heuristics (Zero Loot, Movement Uniformity).
- `app.py`: Streamlit-powered frontend, responsible for stitching backend components to Plotly visualization charts.

## 1. World-to-Minimap Coordinate Conversion

Each map has specific `origin` and `scale` parameters used to convert 3D world coordinates to 2D minimap pixel positions.

**The Tricky Part (Axis Inversion & Scaling):**
The tricky part of mapping 3D world coordinates to a 2D Plotly surface is dealing with relative origins and axis inversions. 
1. **Base Approach**: We use the official center `origin` for each map and its `scale` radius to normalize the game's `x` (east/west) and `z` (north/south) into a 0.0 to 1.0 `(u, v)` percentage grid using: `u = (x - origin_x) / scale`.
2. **Y-Axis Inversion**: Plotly background images draw from the top-left (0,0), but world coordinates treat North (positive Z) as "up". If we plot raw `v` percentages, the player paths render upside down. The solution explicitly flips the vertical axis: `(1 - v) * 100`, cleanly projecting the traces correctly onto Plotly's `x=[0,100], y=[0,100]` grid.
3. **Dynamic Fallbacks**: For unknown maps missing from the registry, the code falls back to dynamic min-max normalization (`(x - min) / (max - min)`) to prevent pipeline crashes.

**Per-Map Parameters:**
| Map | Scale | Origin (x, z) |
|---|---|---|
| AmbroseValley | 900 | (-370, -473) |
| GrandRift | 581 | (-290, -290) |
| Lockdown | 1000 | (-500, -500) |

> **Note:** The `y` column in the data represents elevation/height in the 3D world. For 2D minimap plotting, only `x` and `z` are used.

## Bot Filtering Heuristics
The visualizer builds two layers to identify Bots:
1. **Loot Deprivation (Indicator A)**: Looks for tracks with positional updates but exactly zero looting events across stretches exceeding 5 real-time minutes.
2. **Velocity Variance (Indicator B)**: Scans for suspiciously uniform translation patterns (a variance of essentially zero in pointwise velocity speed).

---

## 2. Data Assumptions & Ambiguities

During development, the raw telemetry Parquet files presented several ambiguities that required handling:

- **Ambiguous Timestamp Formats**: The `ts` (timestamp) column was typed as `timestamp[ms]` in Parquet but actually contained Unix epoch *seconds* (~1.77 billion). 
  - **Handling**: Explicitly extracted the raw integer (`astype('int64')`) and subtracted the minimum timestamp per match group to build a reliable relative `0 to N` seconds localized timeline.
- **Fragmented Match IDs**: Match session strings contained suffix artifacts (e.g., `match_uuid.nakama-N`). 
  - **Handling**: Safely split and stripped the `.nakama` postfix so continuous sessions aren't fractured into multiple games during groupby operations.
- **Bot vs Human Labels**: The `user_id` did not explicitly label bot entities in older file structures. 
  - **Handling**: Assumed real human UUIDs are long string hashes (>20 chars), while bots execute under short numeric identifiers. Added the behavioral heuristics mentioned above as a fallback to catch injected test-bots.

## 3. Major Tradeoffs

| Tradeoff | Consideration | Final Decision & Why |
|---|---|---|
| **Data Imputation vs Stripping** | Handling corrupted or missing coordinate/timestamp rows gracefully. | **Stripped invalid rows/dropped outliers.** Clean telemetry visualization is better than plotting guessed interpolation paths that could confuse level designers. |
| **Local Memory vs Database** | Storing millions of rows of Parquet events. | **Local Memory (Pandas cache).** Faster timeline scrubbing with Streamlit `@st.cache_data`. The tool targets localized match debugging sessions, not broad aggregate historical analytics. |
| **Grid Bins vs Exact Polygons** | Calculating "Dead Zone" interaction map coverage. | **Abstract 20x20 uniform geometric grid.** Fast to compute using `pd.cut`. Exact 3D navmesh polygons were unavailable and computationally overkill for 2D heatmap traffic detection. |
| **Batch Parquet vs Realtime API** | Sourcing and syncing telemetry events. | **Batch local Parquet loads.** Simpler, lightweight setup for offline level designers iterating on maps over past playtest days without demanding live server connectivity. |
