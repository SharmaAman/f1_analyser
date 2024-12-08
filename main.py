import streamlit as st
import fastf1
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

fastf1.Cache.enable_cache('cache')

st.set_page_config(page_title="Aman's Formula 1 Analyser", page_icon="🏎️", layout="wide")

st.title("🏎️ Aman's Formula 1 Analyser - Analytics Project")


def load_session_data(year, race, session_type):
    session = fastf1.get_session(year, race, session_type)
    session.load()
    return session


def calculate_stint_statistics(laps_data):
    stint_stats = laps_data.groupby('Stint').agg({
        'LapTime': ['count', 'mean', 'std', 'min', 'max'],
        'Compound': lambda x: x.iloc[0],
        'TyreLife': ['min', 'max'],
        'SpeedI1': 'mean',
        'SpeedI2': 'mean',
        'SpeedFL': 'mean'
    })
    return stint_stats


def analyze_sector_performance(laps_data):
    sector_times = pd.DataFrame({
        'Sector 1': laps_data['Sector1Time'].dt.total_seconds(),
        'Sector 2': laps_data['Sector2Time'].dt.total_seconds(),
        'Sector 3': laps_data['Sector3Time'].dt.total_seconds()
    })
    return sector_times.describe()


def calculate_tire_degradation(laps_data):
    degradation = laps_data.groupby(['Compound', 'TyreLife'])['LapTime'].mean().reset_index()
    return degradation


def battle_analysis(session_data, driver1, driver2):
    driver1_laps = session_data.laps.pick_driver(driver1)
    driver2_laps = session_data.laps.pick_driver(driver2)

    merged_laps = pd.merge(
        driver1_laps[['LapNumber', 'Position', 'LapTime']],
        driver2_laps[['LapNumber', 'Position', 'LapTime']],
        on='LapNumber',
        suffixes=('_1', '_2')
    )

    merged_laps['Gap'] = abs(merged_laps['Position_1'] - merged_laps['Position_2'])
    merged_laps['TimeDiff'] = (merged_laps['LapTime_1'] - merged_laps['LapTime_2']).dt.total_seconds()

    return merged_laps


def plot_speed_trace(laps_data, lap_number):
    lap_telemetry = laps_data.pick_lap(lap_number).get_telemetry()

    fig = make_subplots(rows=2, cols=1, subplot_titles=('Speed Trace', 'Throttle/Brake'))

    fig.add_trace(go.Scatter(x=lap_telemetry['Distance'], y=lap_telemetry['Speed'],
                             name='Speed', line=dict(color='blue')), row=1, col=1)

    fig.add_trace(go.Scatter(x=lap_telemetry['Distance'], y=lap_telemetry['Throttle'],
                             name='Throttle', line=dict(color='green')), row=2, col=1)
    fig.add_trace(go.Scatter(x=lap_telemetry['Distance'], y=lap_telemetry['Brake'] * 100,
                             name='Brake', line=dict(color='red')), row=2, col=1)

    fig.update_layout(height=800)
    return fig


years = list(range(2024, 2017, -1))
selected_year = st.sidebar.selectbox("Select Year", years)

try:
    schedule = fastf1.get_event_schedule(selected_year)
    races = schedule['EventName'].tolist()
    selected_race = st.sidebar.selectbox("Select Race", races)

    session_types = ['Race', 'Qualifying', 'Sprint', 'Practice 3', 'Practice 2', 'Practice 1']
    selected_session = st.sidebar.selectbox("Select Session", session_types)

    session_map = {
        'Race': 'R',
        'Qualifying': 'Q',
        'Sprint': 'S',
        'Practice 3': 'FP3',
        'Practice 2': 'FP2',
        'Practice 1': 'FP1'
    }

    with st.spinner('Loading session data...'):
        session = load_session_data(selected_year, selected_race, session_map[selected_session])

    drivers = pd.unique(session.laps['Driver']).tolist()

    analysis_options = [
        "Comprehensive Driver Analysis",
        "Advanced Stint Analysis",
        "Telemetry Deep Dive",
        "Head-to-Head Battle Analysis",
        "Race Pace Evolution"
    ]

    selected_analysis = st.sidebar.selectbox("Analysis Type", analysis_options)

    if selected_analysis == "Comprehensive Driver Analysis":
        selected_driver = st.selectbox("Select Driver", drivers)
        driver_laps = session.laps.pick_driver(selected_driver)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Lap Time Distribution")
            valid_laptimes = driver_laps['LapTime'].dt.total_seconds()
            fig = go.Figure(data=[go.Histogram(x=valid_laptimes, nbinsx=30)])
            fig.update_layout(title=f"Lap Time Distribution for {selected_driver}")
            st.plotly_chart(fig)

            st.subheader("Sector Analysis")
            sector_stats = analyze_sector_performance(driver_laps)
            st.dataframe(sector_stats)

        with col2:
            st.subheader("Speed Analysis")
            speed_fig = go.Figure()
            speed_fig.add_trace(go.Box(y=driver_laps['SpeedI1'], name='Speed Sector 1'))
            speed_fig.add_trace(go.Box(y=driver_laps['SpeedI2'], name='Speed Sector 2'))
            speed_fig.add_trace(go.Box(y=driver_laps['SpeedFL'], name='Speed Final'))
            st.plotly_chart(speed_fig)

            if selected_session == "Race":
                st.subheader("Position Changes")
                pos_fig = go.Figure()
                pos_fig.add_trace(go.Scatter(x=driver_laps['LapNumber'],
                                             y=driver_laps['Position'],
                                             mode='lines+markers'))
                pos_fig.update_layout(yaxis_autorange="reversed")
                st.plotly_chart(pos_fig)

    elif selected_analysis == "Advanced Stint Analysis":
        selected_driver = st.selectbox("Select Driver", drivers)
        driver_laps = session.laps.pick_driver(selected_driver)

        stint_stats = calculate_stint_statistics(driver_laps)
        st.subheader("Stint Analysis")
        st.dataframe(stint_stats)

        tire_deg = calculate_tire_degradation(driver_laps)
        st.subheader("Tire Degradation")
        fig = px.scatter(tire_deg, x='TyreLife', y='LapTime',
                         color='Compound', trendline="lowess")
        st.plotly_chart(fig)

    elif selected_analysis == "Telemetry Deep Dive":
        selected_driver = st.selectbox("Select Driver", drivers)
        driver_laps = session.laps.pick_driver(selected_driver)

        lap_number = st.slider("Select Lap Number",
                               min_value=int(driver_laps['LapNumber'].min()),
                               max_value=int(driver_laps['LapNumber'].max()))

        st.subheader("Detailed Telemetry Analysis")
        telemetry_fig = plot_speed_trace(driver_laps, lap_number)
        st.plotly_chart(telemetry_fig)

    elif selected_analysis == "Head-to-Head Battle Analysis":
        col1, col2 = st.columns(2)
        with col1:
            driver1 = st.selectbox("Select First Driver", drivers)
        with col2:
            driver2 = st.selectbox("Select Second Driver", drivers, index=1)

        battle_data = battle_analysis(session, driver1, driver2)

        st.subheader("Gap Analysis")
        gap_fig = go.Figure()
        gap_fig.add_trace(go.Scatter(x=battle_data['LapNumber'],
                                     y=battle_data['Gap'],
                                     mode='lines+markers'))
        st.plotly_chart(gap_fig)

        st.subheader("Lap Time Difference")
        time_diff_fig = go.Figure()
        time_diff_fig.add_trace(go.Scatter(x=battle_data['LapNumber'],
                                           y=battle_data['TimeDiff'],
                                           mode='lines+markers'))
        st.plotly_chart(time_diff_fig)

    elif selected_analysis == "Race Pace Evolution":
        if selected_session == "Race":
            selected_drivers = st.multiselect("Select Drivers to Compare", drivers, default=drivers[:3])

            pace_fig = go.Figure()
            for driver in selected_drivers:
                driver_laps = session.laps.pick_driver(driver)
                rolling_pace = driver_laps['LapTime'].dt.total_seconds().rolling(window=5).mean()
                pace_fig.add_trace(go.Scatter(x=driver_laps['LapNumber'],
                                              y=rolling_pace,
                                              name=driver))

            st.plotly_chart(pace_fig)

            fuel_effect = pd.DataFrame()
            for driver in selected_drivers:
                driver_laps = session.laps.pick_driver(driver)
                fuel_effect[driver] = driver_laps['LapTime'].dt.total_seconds()

            st.subheader("Fuel Effect Analysis")
            fuel_fig = px.line(fuel_effect)
            st.plotly_chart(fuel_fig)
        else:
            st.info("Race Pace Evolution analysis is only available for race sessions.")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("Please try different parameters or refresh the page.")