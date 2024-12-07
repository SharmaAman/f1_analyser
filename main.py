import fastf1
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# Enable caching (cache directory already created)
fastf1.Cache.enable_cache('cache')

# Load session
session = fastf1.get_session(2023, 22, 'R')
session.load()

# Get Verstappen's laps
ver_laps = session.laps.pick_drivers('VER')  # Using updated pick_drivers method

# Find pit stops by looking for significant time losses
print("\nAnalyzing pit stops...")
# Calculate time delta between consecutive laps
ver_laps['LapTimeDelta'] = ver_laps['LapTime'].diff()
# Identify potential pit stop laps (where delta is significantly larger)
pit_stop_laps = ver_laps[ver_laps['LapTimeDelta'] > pd.Timedelta(seconds=10)]
print("\nPotential pit stop laps:")
print(pit_stop_laps[['LapNumber', 'LapTime', 'Compound']])

# Basic lap time analysis
print("\nLap Time Statistics:")
lap_times_seconds = ver_laps['LapTime'].dt.total_seconds()
print(f"Average Lap Time: {lap_times_seconds.mean():.3f} seconds")
print(f"Fastest Lap: {lap_times_seconds.min():.3f} seconds")
print(f"Slowest Lap: {lap_times_seconds.max():.3f} seconds")

# Print stint information
print("\nTyre stints:")
for idx, stint in ver_laps.groupby(ver_laps['Stint']):
    print(f"Stint {idx}: Compound {stint['Compound'].iloc[0]}, "
          f"Laps {stint['LapNumber'].iloc[0]:.0f} to {stint['LapNumber'].iloc[-1]:.0f}")