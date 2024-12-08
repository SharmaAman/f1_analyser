import fastf1
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st

# Enable cache
fastf1.Cache.enable_cache('cache')


import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st


def plot_speed_trace(laps_data, lap_number):
    try:
        lap_telemetry = laps_data.pick_lap(lap_number).get_telemetry()
        fig = make_subplots(rows=2, cols=1, subplot_titles=('Speed Trace', 'Throttle/Brake'))

        fig.add_trace(go.Scatter(
            x=lap_telemetry['Distance'],
            y=lap_telemetry['Speed'],
            name='Speed',
            line=dict(color='blue')
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=lap_telemetry['Distance'],
            y=lap_telemetry['Throttle'],
            name='Throttle',
            line=dict(color='green')
        ), row=2, col=1)

        fig.add_trace(go.Scatter(
            x=lap_telemetry['Distance'],
            y=lap_telemetry['Brake'] * 100,
            name='Brake',
            line=dict(color='red')
        ), row=2, col=1)

        fig.update_layout(
            height=800,
            showlegend=True,
            title_text=f"Lap {lap_number} Telemetry",
            xaxis_title="Distance (m)",
            xaxis2_title="Distance (m)",
            yaxis_title="Speed (km/h)",
            yaxis2_title="Percentage"
        )

        return fig
    except Exception as e:
        st.error(f"Error plotting speed trace: {str(e)}")
        return None


def analyze_sector_performance(laps_data):
    sector_times = pd.DataFrame({
        'Sector 1': laps_data['Sector1Time'].dt.total_seconds(),
        'Sector 2': laps_data['Sector2Time'].dt.total_seconds(),
        'Sector 3': laps_data['Sector3Time'].dt.total_seconds()
    })
    return sector_times.describe()


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