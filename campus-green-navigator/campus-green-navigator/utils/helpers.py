# utils/helpers.py
"""Small pure helper utilities used by the app and tests.

Keep these functions import-safe (no Streamlit) so tests can import them.
"""
from data.campus_data import EMISSION_FACTORS_G_PER_KM


def calculate_co2_grams(vehicle_type: str, distance_km: float) -> float:
    """Return grams of CO2 for the trip distance using an emission factor.

    vehicle_type: string like 'Car', 'EV', etc.
    distance_km: trip distance in kilometers
    """
    factor = EMISSION_FACTORS_G_PER_KM.get(vehicle_type, 120.0)
    return float(factor) * float(distance_km)


def format_minutes(minutes: float) -> str:
    """Pretty-format a minutes value for display.

    Returns a short string like '90 min' (keeps things stable for tests).
    """
    return f"{int(round(minutes))} min"
