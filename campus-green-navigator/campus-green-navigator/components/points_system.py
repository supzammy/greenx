# components/points_system.py
import streamlit as st

REWARDS = {
    "Free Coffee": 50,
    "Library Priority": 100,
    "Parking Discount": 200,
}


def init_points():
    if "points" not in st.session_state:
        st.session_state.points = 0
    if "history" not in st.session_state:
        st.session_state.history = []


def calculate_points(co2_savings_g: float, extra_minutes: float) -> int:
    """
    Points formula:
      - Base points = CO2 savings (in kg) * 2
      - Time penalty deduction = extra_minutes * 5
      - Minimum 10 points for any eco-route
    """
    co2_kg = co2_savings_g / 1000.0
    base = co2_kg * 2.0
    penalty = extra_minutes * 5.0
    raw = base - penalty
    pts = max(10, int(round(raw)))
    return pts


def add_points(points: int, reason: str = ""):
    init_points()
    st.session_state.points += points
    st.session_state.history.append({"points": points, "reason": reason})


def redeem_reward(reward_key: str) -> tuple[bool, str]:
    init_points()
    cost = REWARDS.get(reward_key)
    if cost is None:
        return False, "Invalid reward."
    if st.session_state.points >= cost:
        st.session_state.points -= cost
        st.session_state.history.append({"points": -cost, "reason": f"Redeemed {reward_key}"})
        return True, f"Redeemed {reward_key} for {cost} points!"
    else:
        return False, "Not enough points."
