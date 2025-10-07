
"""Simple points system used by the demo Streamlit app.

This file implements a tiny in-memory/session-based points store so the
UI can call into it without requiring a backend during local demos.
"""
from typing import Tuple

REWARDS = {
	"Coffee Discount": 50,
	"Free Bike Helmet": 200,
}


def init_points(session_state=None) -> None:
	"""Initialize Streamlit session state for points.

	The session_state parameter is provided for testability; in the app we
	will pass st.session_state.
	"""
	if session_state is None:
		try:
			import streamlit as _st

			session_state = _st.session_state
		except Exception:
			session_state = {}
	if "points" not in session_state:
		session_state["points"] = 0


def calculate_points(co2_saved_grams: float, extra_minutes: int = 0) -> int:
	"""Calculate points awarded for CO2 savings and time penalty.

	Very simple formula: 1 point per 10 grams saved, minus 1 per 5 extra minutes.
	"""
	pts = int(max(0, round(co2_saved_grams / 10.0)))
	penalty = int(extra_minutes // 5)
	return max(0, pts - penalty)


def add_points(points: int, reason: str = "") -> None:
	try:
		import streamlit as _st

		_st.session_state["points"] = _st.session_state.get("points", 0) + int(points)
	except Exception:
		# fallback no-op for tests
		return None


def redeem_reward(name: str) -> Tuple[bool, str]:
	try:
		import streamlit as _st

		cost = REWARDS.get(name)
		if cost is None:
			return False, "Unknown reward"
		if _st.session_state.get("points", 0) < cost:
			return False, "Not enough points"
		_st.session_state["points"] -= cost
		return True, f"Redeemed {name}"
	except Exception:
		return False, "Session unavailable"
