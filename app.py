import streamlit as st
import fastf1
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Enable FastF1 cache
fastf1.Cache.enable_cache('cache')

# Set page config
st.set_page_config(
    page_title="F1 Analysis Hub",
    page_icon="🏎️",
    layout="wide"
)

# Add title and description
st.title("🏎️ Formula 1 Analysis Hub")
st.markdown("Explore F1 race data with interactive visualizations")

# Sidebar for user inputs
st.sidebar.header("Select Race Details")

# Get available years (you might want to limit this range)
years = list(range(2024, 2017, -1))
selected_year = st.sidebar.selectbox("Select Year", years)


# Load available races for selected year
@st.cache_data
def load_races(year):
    schedule = fastf1.get_event_schedule(year)
    return schedule


try:
    schedule = load_races(selected_year)
    races = schedule['EventName'].tolist()
    selected_race = st.sidebar.selectbox("Select Race", races)

    # Session selection
    session_types = ['Race', 'Qualifying', 'Sprint', 'Practice 3', 'Practice 2', 'Practice 1']
    selected_session = st.sidebar.selectbox("Select Session", session_types)


    # Load session data
    @st.cache_data
    def load_session_data(year, race, session):
        session_map = {
            'Race': 'R',
            'Qualifying': 'Q',
            'Sprint': 'S',
            'Practice 3': 'FP3',
            'Practice 2': 'FP2',
            'Practice 1': 'FP1'
        }
        session = fastf1.get_session(year, race, session_map[session])
        session.load()
        return session


    with st.spinner('Loading session data...'):
        session = load_session_data(selected_year, selected_race, selected_session)

    # Get list of drivers
    drivers = pd.unique(session.laps['Driver']).tolist()
    selected_drivers = st.sidebar.multiselect("Select Drivers", drivers, default=drivers[:2])

    # Analysis Options
    analysis_type = st.sidebar.selectbox(
        "Select Analysis Type",
        ["Lap Times Comparison", "Speed Analysis", "Position Changes", "Tire Strategy"]
    )

    # Main content area
    st.header(f"{selected_race} {selected_year} - {selected_session} Analysis")

    if analysis_type == "Lap Times Comparison":
        st.subheader("Lap Times Comparison")

        fig = go.Figure()
        for driver in selected_drivers:
            driver_laps = session.laps.pick_driver(driver)
            fig.add_trace(go.Scatter(
                x=driver_laps['LapNumber'],
                y=driver_laps['LapTime'].dt.total_seconds(),
                name=driver,
                mode='lines+markers'
            ))

        fig.update_layout(
            xaxis_title="Lap Number",
            yaxis_title="Lap Time (seconds)",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    elif analysis_type == "Speed Analysis":
        st.subheader("Speed Analysis")

        fig = go.Figure()
        for driver in selected_drivers:
            driver_laps = session.laps.pick_driver(driver)
            fig.add_trace(go.Box(
                y=driver_laps['SpeedI1'],
                name=f"{driver} - Sector 1",
                boxpoints='all'
            ))
            fig.add_trace(go.Box(
                y=driver_laps['SpeedI2'],
                name=f"{driver} - Sector 2",
                boxpoints='all'
            ))
            fig.add_trace(go.Box(
                y=driver_laps['SpeedFL'],
                name=f"{driver} - Final",
                boxpoints='all'
            ))

        fig.update_layout(
            yaxis_title="Speed (km/h)",
            boxmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)

    elif analysis_type == "Position Changes":
        st.subheader("Position Changes Through Race")

        if selected_session == "Race":
            fig = go.Figure()
            for driver in selected_drivers:
                driver_laps = session.laps.pick_driver(driver)
                fig.add_trace(go.Scatter(
                    x=driver_laps['LapNumber'],
                    y=driver_laps['Position'],
                    name=driver,
                    mode='lines+markers'
                ))

            fig.update_layout(
                xaxis_title="Lap Number",
                yaxis_title="Position",
                yaxis_autorange="reversed"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Position changes analysis is only available for race sessions.")

    elif analysis_type == "Tire Strategy":
        st.subheader("Tire Strategy Analysis")

        for driver in selected_drivers:
            driver_stints = session.laps.pick_driver(driver).groupby('Stint')['Compound'].first()
            st.write(f"**{driver}'s Tire Strategy:**")

            stint_data = []
            for stint, compound in driver_stints.items():
                stint_laps = session.laps.pick_driver(driver).query(f"Stint == {stint}")
                stint_data.append({
                    'Stint': stint,
                    'Compound': compound,
                    'Laps': len(stint_laps),
                    'Avg Time': stint_laps['LapTime'].mean().total_seconds()
                })

            stint_df = pd.DataFrame(stint_data)
            st.dataframe(stint_df)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("This might be due to missing data for the selected combination. Please try different parameters.")

# Footer
st.markdown("---")
st.markdown("Created with FastF1 and Streamlit")