import streamlit as st
import fastf1
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

fastf1.Cache.enable_cache('cache')

st.set_page_config(
    page_title="Aman's Formula 1 Analyser",
    page_icon="🏎️",
    layout="wide",
)

st.title("🏎️ Aman's Formula 1 Analyser - Analytics Project")


def get_latest_session(year, race):
    session_order = ['R', 'Q', 'S', 'FP3', 'FP2', 'FP1']
    session_names = {
        'R': 'Race',
        'Q': 'Qualifying',
        'S': 'Sprint',
        'FP3': 'Practice 3',
        'FP2': 'Practice 2',
        'FP1': 'Practice 1'
    }

    for session_type in session_order:
        try:
            session = fastf1.get_session(year, race, session_type)
            session.load()
            return session, session_names[session_type]
        except:
            continue
    return None, None


def load_session_data(year, race, session_type):
    session = fastf1.get_session(year, race, session_type)
    try:
        session.load(telemetry=True, weather=False, messages=False)
        return session
    except Exception as e:
        st.error(f"Error loading session: {str(e)}")
        return None


# Selection area using columns
st.markdown("### Select Parameters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    years = list(range(2024, 2017, -1))
    selected_year = st.selectbox("Year", years, index=0)

with col2:
    try:
        schedule = fastf1.get_event_schedule(selected_year)
        races = schedule['EventName'].tolist()
        # Get the latest race that has data
        latest_race_index = 0
        for idx, race in enumerate(races):
            session, _ = get_latest_session(selected_year, race)
            if session is not None:
                latest_race_index = idx
                break
        selected_race = st.selectbox("Circuit", races, index=latest_race_index)
    except Exception as e:
        st.error(f"Error loading race schedule: {str(e)}")
        st.stop()

# Get latest available session for selected race
latest_session, session_type_name = get_latest_session(selected_year, selected_race)

with col3:
    session_types = ['Race', 'Qualifying', 'Sprint', 'Practice 3', 'Practice 2', 'Practice 1']
    default_index = session_types.index(session_type_name) if session_type_name in session_types else 0
    selected_session = st.selectbox("Session", session_types, index=default_index)

with st.spinner('Loading session data...'):
    try:
        session = load_session_data(
            selected_year,
            selected_race,
            {'Race': 'R', 'Qualifying': 'Q', 'Sprint': 'S',
             'Practice 3': 'FP3', 'Practice 2': 'FP2', 'Practice 1': 'FP1'}[selected_session]
        )

        if session is not None:
            drivers = pd.unique(session.laps['Driver']).tolist()
            constructors = pd.unique(session.laps['Team']).tolist()

            st.markdown("### Select Competitors")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                primary_driver = st.selectbox("Primary Driver", drivers, index=0)
            with col2:
                primary_constructor = st.selectbox("Primary Constructor", constructors, index=0)
            with col3:
                secondary_drivers = st.multiselect(
                    "Secondary Driver(s)",
                    [d for d in drivers if d != primary_driver],
                    default=[drivers[1]] if len(drivers) > 1 else []
                )
            with col4:
                secondary_constructors = st.multiselect(
                    "Secondary Constructor(s)",
                    [c for c in constructors if c != primary_constructor],
                    default=[constructors[1]] if len(constructors) > 1 else []
                )

            st.divider()

            # Analysis Sections
            st.header("1. Basic Session Analysis")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Driver Position Progression")
                st.caption("Track position changes throughout the session")

                if selected_session == "Race":
                    position_fig = go.Figure()
                    position_fig.add_trace(go.Scatter(
                        x=session.laps.pick_driver(primary_driver)['LapNumber'],
                        y=session.laps.pick_driver(primary_driver)['Position'],
                        name=primary_driver,
                        line=dict(color='red', width=3)
                    ))

                    for driver in secondary_drivers:
                        position_fig.add_trace(go.Scatter(
                            x=session.laps.pick_driver(driver)['LapNumber'],
                            y=session.laps.pick_driver(driver)['Position'],
                            name=driver,
                            line=dict(width=2)
                        ))

                    position_fig.update_layout(
                        yaxis_autorange="reversed",
                        yaxis_title="Position",
                        xaxis_title="Lap Number"
                    )
                    st.plotly_chart(position_fig, use_container_width=True)
                else:
                    st.info("Position progression is only available for race sessions")

            with col2:
                st.subheader("Lap Time Distribution")
                st.caption("Distribution of lap times showing consistency and outliers")

                laptimes_fig = go.Figure()
                primary_laps = session.laps.pick_driver(primary_driver)['LapTime'].dt.total_seconds()

                laptimes_fig.add_trace(go.Histogram(
                    x=primary_laps,
                    name=primary_driver,
                    nbinsx=30,
                    opacity=0.7
                ))

                for driver in secondary_drivers:
                    driver_laps = session.laps.pick_driver(driver)['LapTime'].dt.total_seconds()
                    laptimes_fig.add_trace(go.Histogram(
                        x=driver_laps,
                        name=driver,
                        nbinsx=30,
                        opacity=0.5
                    ))

                laptimes_fig.update_layout(
                    barmode='overlay',
                    xaxis_title="Lap Time (seconds)",
                    yaxis_title="Count"
                )
                st.plotly_chart(laptimes_fig, use_container_width=True)

            st.header("2. Sector Analysis")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Sector Times Comparison")
                st.caption("Detailed breakdown of sector performance")

                sector_fig = go.Figure()
                primary_sectors = session.laps.pick_driver(primary_driver)

                sectors = ['Sector1Time', 'Sector2Time', 'Sector3Time']
                for sector in sectors:
                    sector_fig.add_trace(go.Box(
                        y=primary_sectors[sector].dt.total_seconds(),
                        name=f"{primary_driver} {sector[:-4]}",
                        boxpoints='outliers'
                    ))

                for driver in secondary_drivers:
                    driver_sectors = session.laps.pick_driver(driver)
                    for sector in sectors:
                        sector_fig.add_trace(go.Box(
                            y=driver_sectors[sector].dt.total_seconds(),
                            name=f"{driver} {sector[:-4]}",
                            boxpoints='outliers'
                        ))

                st.plotly_chart(sector_fig, use_container_width=True)

            with col2:
                st.subheader("Speed Analysis")
                st.caption("Speed comparison across different track sections")

                speed_fig = make_subplots(rows=3, cols=1,
                                          subplot_titles=('Speed Trap 1', 'Speed Trap 2', 'Finish Line'))

                primary_laps = session.laps.pick_driver(primary_driver)
                speed_metrics = ['SpeedI1', 'SpeedI2', 'SpeedFL']

                for idx, metric in enumerate(speed_metrics, 1):
                    speed_fig.add_trace(
                        go.Box(y=primary_laps[metric], name=primary_driver,
                               boxpoints='outliers'), row=idx, col=1
                    )

                    for driver in secondary_drivers:
                        driver_laps = session.laps.pick_driver(driver)
                        speed_fig.add_trace(
                            go.Box(y=driver_laps[metric], name=driver,
                                   boxpoints='outliers'), row=idx, col=1
                        )

                speed_fig.update_layout(height=800, showlegend=False)
                st.plotly_chart(speed_fig, use_container_width=True)

            st.header("3. Advanced Telemetry")

            st.subheader("Detailed Lap Analysis")
            st.caption("Comprehensive telemetry data for selected laps")

            col1, col2 = st.columns([1, 3])

            with col1:
                primary_laps = session.laps.pick_driver(primary_driver)
                selected_lap = st.selectbox(
                    "Select Lap Number",
                    options=primary_laps['LapNumber'].astype(int).tolist(),
                    index=len(primary_laps['LapNumber']) // 2
                )

            with col2:
                telemetry_fig = plot_speed_trace(primary_laps, selected_lap)
                if telemetry_fig is not None:
                    st.plotly_chart(telemetry_fig, use_container_width=True)

            if selected_session == "Race":
                st.header("4. Race Pace Analysis")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Rolling Race Pace")
                    st.caption("5-lap rolling average pace comparison")

                    pace_fig = go.Figure()
                    primary_pace = session.laps.pick_driver(primary_driver)['LapTime'].dt.total_seconds()
                    pace_fig.add_trace(go.Scatter(
                        x=session.laps.pick_driver(primary_driver)['LapNumber'],
                        y=primary_pace.rolling(window=5).mean(),
                        name=primary_driver,
                        line=dict(color='red', width=3)
                    ))

                    for driver in secondary_drivers:
                        driver_pace = session.laps.pick_driver(driver)['LapTime'].dt.total_seconds()
                        pace_fig.add_trace(go.Scatter(
                            x=session.laps.pick_driver(driver)['LapNumber'],
                            y=driver_pace.rolling(window=5).mean(),
                            name=driver
                        ))

                    st.plotly_chart(pace_fig, use_container_width=True)

                with col2:
                    st.subheader("Gap Evolution")
                    st.caption("Time gap evolution to race leader")

                    if len(secondary_drivers) > 0:
                        gap_fig = go.Figure()
                        reference_driver = secondary_drivers[0]

                        lap_times_ref = session.laps.pick_driver(reference_driver)['LapTime'].dt.total_seconds()
                        lap_times_primary = session.laps.pick_driver(primary_driver)['LapTime'].dt.total_seconds()

                        cumulative_gap = (lap_times_primary - lap_times_ref).cumsum()

                        gap_fig.add_trace(go.Scatter(
                            x=session.laps.pick_driver(primary_driver)['LapNumber'],
                            y=cumulative_gap,
                            name=f"{primary_driver} vs {reference_driver}",
                            line=dict(color='red', width=3)
                        ))

                        st.plotly_chart(gap_fig, use_container_width=True)
                    else:
                        st.info("Select secondary drivers to view gap evolution")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try different parameters or refresh the page.")

st.caption("Created by Aman")
