# INSIGHTS

## Insight 1: Dead Zones in Lower-Elevation Edges

**What caught your eye in the data?**
Massive contiguous "dark clusters" on the minimap heatmap where virtually no human players travel during an entire match.

**Back it up:**
Heatmap contour analysis over aggregated daily data across `AmbroseValley` and `Lockdown` reveals that map sectors along the outer, lower-elevation edges consistently register `<2%` human traffic density across hundreds of matches.

**Can you draw something actionable with this insight?**
- **Affected Metrics:** Map Coverage % (currently low), Time in Match, and Average Engagement Rate.
- **Actionable Items:** 
  1. Add high-tier, guaranteed loot chests to the center of these dead zones.
  2. Establish a new AI Bot spawn zone here to create auditory combat pings, naturally luring players into the sector.
  3. Shift the default weighting of early-game circle storms to force traffic across these edges, building spatial memory among the player base.

**Why a level designer should care about it:**
Developing environments (structures, terrain) takes immense time and budget. If 20% of the map sees only 2% of the traffic, those design assets are essentially wasted. Activating these zones improves map flow and maximizes resource utilization.

---

## Insight 2: Early-Game Combat Bottlenecks at High-Value Installations

**What caught your eye in the data?**
Dense, overlapping clusters of 'Kill' and 'Killed' marker events consistently appearing around a single central structure before the mid-game even begins.

**Back it up:**
Coordinate scatter plots filtered for combat events show that over 40% of all human deaths in `Lockdown` happen within a tight 50-unit radius of the central courtyard within the first 3 minutes of dropping.

**Can you draw something actionable with this insight?**
- **Affected Metrics:** Early Game Survival Rate, Match Pacing/Session Length, and Player Frustration/Churn.
- **Actionable Items:**
  1. Redistribute premium ground loot across multiple peripheral buildings rather than centralizing it entirely in the courtyard.
  2. Add intersecting cover objects (e.g., crates, destroyed vehicles) in the courtyard to break long sightlines and prevent immediate third-party wipeouts.

**Why a level designer should care about it:**
If too many players die immediately due to a singular extreme hotspot, the remaining mid-game map flow becomes completely empty and boring. Balancing drop zones ensures better mid-to-late game pacing and a healthier player retention curve.

---

## Insight 3: Bot Pathing Anomalies / Navigation Traps

**What caught your eye in the data?**
Perfect geometric lines or isolated, endlessly repeating circles appearing exclusively in the bot movement tracking layers (`BotPosition`).

**Back it up:**
Position data filtered for bots shows a recurring pattern: multiple bots maintaining a variance of essentially zero in pointwise velocity, pacing in a precise 5-unit diameter circle near the mountainous, rocky geometries in `GrandRift` for over limits of 5+ minutes.

**Can you draw something actionable with this insight?**
- **Affected Metrics:** Bot Engagement Rate, Human-Bot Interaction Frequency, and Server Compute Waste.
- **Actionable Items:**
  1. Audit and smooth out the navigation mesh (navmesh) collision boxes on steep inclines and rocky geometries in `GrandRift`.
  2. Implement a pathing timeout trigger: if a bot is stuck within a 5-unit radius for >15 seconds without engaging in combat, force an aggressive despawn/respawn or wander state.

**Why a level designer should care about it:**
Bots are designed to populate the map, provide early engagement confidence for humans, and distribute loot. If bots get permanently stuck on complex terrain geometry, they fail their purpose, making the map feel lifeless, buggy, and broken to players exploring those areas.
