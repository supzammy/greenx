"""Minimal campus data used by the demo app and mock API.

This file intentionally contains a very small set of locations and routes so
the demo can run without external data dependencies.
"""

LOCATIONS = {
    "Main Gate": {"lat": 12.9716, "lon": 77.5946},
    "Library": {"lat": 12.9720, "lon": 77.5950},
    "Cafeteria": {"lat": 12.9710, "lon": 77.5955},
}

ROUTES = [
    {
        "from": "Main Gate",
        "to": "Library",
        "fast": {"distance_km": 0.5, "time_min": 6},
        "eco": {"distance_km": 0.55, "time_min": 8},
    },
    {
        "from": "Library",
        "to": "Cafeteria",
        "fast": {"distance_km": 0.3, "time_min": 4},
        "eco": {"distance_km": 0.32, "time_min": 5},
    },
]
