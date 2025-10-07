
"""Minimal helper utilities used by the Streamlit demo.

These implementations are intentionally small and pure so the UI can
import them for the demo and unit tests.
"""
from typing import Union


def calculate_co2_grams(vehicle_type: str, distance_km: Union[int, float]) -> float:
	"""Return a simple CO2 grams estimate for a trip.

	vehicle_type: one of "Car", "Bike", "Walk", "EV".
	distance_km: distance in kilometers.
	"""
	base_per_km = {
		"Car": 192.0,  # g CO2 per km (approx)
		"Bike": 21.0,
		"Walk": 0.0,
		"EV": 50.0,
	}
	per_km = base_per_km.get(str(vehicle_type), 150.0)
	try:
		return float(per_km) * float(distance_km)
	except Exception:
		return 0.0


def format_minutes(minutes: Union[int, float]) -> str:
	"""Return a human-friendly minutes string."""
	try:
		m = int(round(float(minutes)))
	except Exception:
		return "N/A"
	if m < 60:
		return f"{m} min"
	hours = m // 60
	rem = m % 60
	return f"{hours} h {rem} min"
