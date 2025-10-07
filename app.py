from streamlit_folium import st_folium
import os
import joblib
import pandas as pd
import streamlit as st

from data import campus_data
from utils.helpers import calculate_co2_grams, format_minutes
from components.points_system import (
    init_points,
    calculate_points,
    add_points,
    redeem_reward,
    REWARDS,
)


def render() -> None:
    # Interactive map (Leaflet via streamlit-folium)
    st.markdown("## Campus Map")
    import folium
    # Center map on campus
    center = [12.9716, 77.5946]
    m = folium.Map(location=center, zoom_start=17)
    # Add markers for locations
    for name, loc in campus_data.LOCATIONS.items():
        folium.Marker([loc["lat"], loc["lon"]], popup=name).add_to(m)
    # Draw routes
    for route in campus_data.ROUTES:
        points = [
            [campus_data.LOCATIONS[route["from"]]["lat"], campus_data.LOCATIONS[route["from"]]["lon"]],
            [campus_data.LOCATIONS[route["to"]]["lat"], campus_data.LOCATIONS[route["to"]]["lon"]],
        ]
        folium.PolyLine(points, color="green", weight=4, opacity=0.7).add_to(m)
    st_folium(m, width=700, height=400)
    st.set_page_config(page_title="Campus Green Navigator", layout="wide")

    # Initialize session
    init_points()

    # Sidebar
    st.sidebar.title("Campus Green Navigator")
    start = st.sidebar.selectbox("Start", options=list(campus_data.LOCATIONS.keys()), index=0, key="start_select")
    end = st.sidebar.selectbox("End", options=[k for k in campus_data.LOCATIONS.keys() if k != start], index=0, key="end_select")
    vehicle = st.sidebar.radio("Vehicle", options=["Car", "Bike", "Walk", "EV"], index=0, key="vehicle_radio")
    eco_route_toggle = st.sidebar.checkbox("Prefer eco route", value=True, key="eco_checkbox")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Your Points")
    st.sidebar.metric("Points", st.session_state.get("points", 0))

    st.sidebar.markdown("### Redeem Rewards")
    for rname, cost in REWARDS.items():
        if st.sidebar.button(f"Redeem: {rname} ({cost})", key=f"redeem_{rname}"):
            ok, msg = redeem_reward(rname)
            if ok:
                st.sidebar.success(msg)
            else:
                st.sidebar.warning(msg)

    # Find route combos
    def find_route(start_, end_):
        for r in campus_data.ROUTES:
            if r["from"] == start_ and r["to"] == end_:
                return r
            if r["from"] == end_ and r["to"] == start_:
                return r
        return None

    route = find_route(start, end)
    if route is None:
        st.warning("No pre-defined route between selected points.")
        return

    # Compare fast vs eco
    fast = route["fast"]
    eco = route["eco"]

    col1, col2 = st.columns(2)
    with col1:
        st.header("Fast Route")
        st.write(f"Distance: {fast['distance_km']} km")
        st.write(f"Time: {format_minutes(fast['time_min'])}")
        st.write(f"Estimated CO2: {calculate_co2_grams(vehicle, fast['distance_km']):.0f} g")
    with col2:
        st.header("Eco Route")
        st.write(f"Distance: {eco['distance_km']} km")
        st.write(f"Time: {format_minutes(eco['time_min'])}")
        st.write(f"Estimated CO2: {calculate_co2_grams(vehicle, eco['distance_km']):.0f} g")

    # Carbon savings
    co2_fast = calculate_co2_grams(vehicle, fast["distance_km"])
    co2_eco = calculate_co2_grams(vehicle, eco["distance_km"])
    co2_savings = max(0.0, co2_fast - co2_eco)
    time_diff = eco["time_min"] - fast["time_min"]

    st.markdown("---")
    st.subheader("Route Comparison")
    st.metric("CO2 Savings (g)", f"{co2_savings:.0f}")
    st.metric("Extra Time (min)", f"{time_diff:.0f}")

    # Visualize CO2 savings
    st.progress(min(1.0, co2_savings / 200.0))  # simple visual scale

    # Points
    if st.button("Take Eco Route / Claim Points", key="take_eco_button"):
        pts = calculate_points(co2_savings, extra_minutes=max(0, time_diff))
        add_points(pts, reason=f"Eco-route {start}→{end}")
        st.success(f"You earned {pts} points! 🎉")

    # Quick ML parking prediction loader (if model available)
    st.markdown("---")
    st.header("Parking Occupancy Prediction (demo)")

    MODEL_PATH = "ml/parking_model.joblib"
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            st.success("Parking model loaded.")
            # Basic next-6-hour forecast (using current hour features)
            from datetime import datetime, timedelta

            now = datetime.now()
            rows = []
            for i in range(6):
                t = now + timedelta(hours=i)
                hour = t.hour
                weekday = t.weekday()
                np = __import__("numpy")
                hour_sin = np.sin(2 * np.pi * hour / 24.0)
                hour_cos = np.cos(2 * np.pi * hour / 24.0)
                day_sin = np.sin(2 * np.pi * weekday / 7.0)
                day_cos = np.cos(2 * np.pi * weekday / 7.0)
                is_weekend = int(weekday >= 5)
                X = [[hour_sin, hour_cos, day_sin, day_cos, is_weekend, 0]]
                pred = model.predict(X)[0]
                rows.append({"hour": t.strftime("%Y-%m-%d %H:%M"), "predicted_occupancy": float(pred)})
            st.table(pd.DataFrame(rows))
        except Exception as e:
            st.error(f"Failed to load model: {e}")
    else:
        st.info("Parking model not found. Run the training script to generate one (see README).")


if __name__ == "__main__":
    render()
# app.py
import streamlit as st
from data import campus_data
from utils.helpers import calculate_co2_grams, format_minutes
from components.points_system import init_points, calculate_points, add_points, redeem_reward, REWARDS
import pandas as pd
import joblib
import os

st.set_page_config(page_title="Campus Green Navigator", layout="wide")

# Initialize session
init_points()

# Sidebar
st.sidebar.title("Campus Green Navigator")
start = st.sidebar.selectbox("Start", options=list(campus_data.LOCATIONS.keys()), index=0)
end = st.sidebar.selectbox("End", options=[k for k in campus_data.LOCATIONS.keys() if k != start], index=0)
vehicle = st.sidebar.radio("Vehicle", options=["Car", "Bike", "Walk", "EV"], index=0)
eco_route_toggle = st.sidebar.checkbox("Prefer eco route", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Your Points")
st.sidebar.metric("Points", st.session_state.points)

st.sidebar.markdown("### Redeem Rewards")
for rname, cost in REWARDS.items():
    if st.sidebar.button(f"Redeem: {rname} ({cost})"):
        ok, msg = redeem_reward(rname)
        if ok:
            st.sidebar.success(msg)
        else:
            st.sidebar.warning(msg)

# Find route combos
def find_route(start, end):
    for r in campus_data.ROUTES:
        if r["from"] == start and r["to"] == end:
            return r
        if r["from"] == end and r["to"] == start:
            return r
    return None

route = find_route(start, end)
if route is None:
    st.warning("No pre-defined route between selected points.")
    st.stop()

# Compare fast vs eco
fast = route["fast"]
eco  = route["eco"]

col1, col2 = st.columns(2)
with col1:
    st.header("Fast Route")
    st.write(f"Distance: {fast['distance_km']} km")
    st.write(f"Time: {format_minutes(fast['time_min'])}")
    st.write(f"Estimated CO2: {calculate_co2_grams(vehicle, fast['distance_km']):.0f} g")
with col2:
    st.header("Eco Route")
    st.write(f"Distance: {eco['distance_km']} km")
    st.write(f"Time: {format_minutes(eco['time_min'])}")
    st.write(f"Estimated CO2: {calculate_co2_grams(vehicle, eco['distance_km']):.0f} g")

# Carbon savings
co2_fast = calculate_co2_grams(vehicle, fast["distance_km"])
co2_eco  = calculate_co2_grams(vehicle, eco["distance_km"])
co2_savings = max(0.0, co2_fast - co2_eco)
time_diff = eco["time_min"] - fast["time_min"]

st.markdown("---")
st.subheader("Route Comparison")
st.metric("CO2 Savings (g)", f"{co2_savings:.0f}")
st.metric("Extra Time (min)", f"{time_diff:.0f}")

# Visualize CO2 savings
st.progress(min(1.0, co2_savings / 200.0))  # simple visual scale

# Points
if st.button("Take Eco Route / Claim Points"):
    pts = calculate_points(co2_savings, extra_minutes=max(0, time_diff))
    add_points(pts, reason=f"Eco-route {start}→{end}")
    st.success(f"You earned {pts} points! 🎉")

# Quick ML parking prediction loader (if model available)
st.markdown("---")
st.header("Parking Occupancy Prediction (demo)")

MODEL_PATH = "ml/parking_model.joblib"
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        st.success("Parking model loaded.")
        # Basic next-6-hour forecast (using current hour features)
        from datetime import datetime, timedelta
        now = datetime.now()
        rows = []
        for i in range(6):
            t = now + timedelta(hours=i)
            hour = t.hour
            weekday = t.weekday()
            hour_sin = __import__("numpy").sin(2 * __import__("numpy").pi * hour / 24.0)
            hour_cos = __import__("numpy").cos(2 * __import__("numpy").pi * hour / 24.0)
            day_sin = __import__("numpy").sin(2 * __import__("numpy").pi * weekday / 7.0)
            day_cos = __import__("numpy").cos(2 * __import__("numpy").pi * weekday / 7.0)
            is_weekend = int(weekday >= 5)
            # feature vector
            X = [[hour_sin, hour_cos, day_sin, day_cos, is_weekend, 0]]  # not exam
            pred = model.predict(X)[0]
            rows.append({"hour": t.strftime("%Y-%m-%d %H:%M"), "predicted_occupancy": float(pred)})
        st.table(pd.DataFrame(rows))
    except Exception as e:
        st.error(f"Failed to load model: {e}")
else:
    st.info("Parking model not found. Run the training script to generate one (see README).")