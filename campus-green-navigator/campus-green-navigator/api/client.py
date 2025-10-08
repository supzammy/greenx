import os
import requests
from typing import Any, Dict

from data import campus_data

BASE_URL = os.getenv("CGN_API_BASE_URL", "http://localhost:8000")


def _has_mapmyindia_creds() -> bool:
    return bool(os.getenv("MAPMYINDIA_CLIENT_ID") and os.getenv("MAPMYINDIA_CLIENT_SECRET"))


def get_route(start: str, end: str) -> Dict[str, Any]:
    """Get route using MapmyIndia if configured; else prefer backend mock API; finally fallback to local campus_data."""
    # Prefer MapmyIndia when credentials are present
    if _has_mapmyindia_creds():
        try:
            from api.mapmyindia import directions as _mmi_directions

            return _mmi_directions(start, end)
        except Exception:
            # fall through to try mock server
            pass

    # Try backend/mock server
    try:
        resp = requests.get(f"{BASE_URL}/route", params={"start": start, "end": end}, timeout=3)
        resp.raise_for_status()
        data = resp.json()
        # Validate that the backend/mock returned the expected structure. If not,
        # treat it as an error so we can fallback to the local campus_data.
        if not isinstance(data, dict) or not all(k in data for k in ("from_loc", "to_loc", "fast", "eco")):
            raise ValueError("Invalid route response from backend")
        return data
    except Exception:
        # local fallback in-process
        for r in campus_data.ROUTES:
            if (r["from"] == start and r["to"] == end) or (r["from"] == end and r["to"] == start):
                # Ensure geometry exists for map rendering. If missing, synthesize a simple
                # straight-line geometry using campus_data.LOCATIONS coordinates.
                def _coord_for(name):
                    v = campus_data.LOCATIONS.get(name)
                    if isinstance(v, (list, tuple)) and len(v) >= 2:
                        return [float(v[0]), float(v[1])]
                    if isinstance(v, dict):
                        # support {'lat':.., 'lon':..}
                        lat = v.get('lat') or v.get('latitude') or v.get('y')
                        lon = v.get('lon') or v.get('longitude') or v.get('x')
                        if lat is not None and lon is not None:
                            return [float(lat), float(lon)]
                    return None

                s_coords = _coord_for(r['from'])
                e_coords = _coord_for(r['to'])

                def _ensure_geom(obj):
                    try:
                        geom = obj.get('geometry')
                        if isinstance(geom, (list, tuple)) and len(geom) > 0:
                            return obj
                    except Exception:
                        pass
                    # synthesize a 3-point polyline if we have both endpoints
                    if s_coords and e_coords:
                        mid = [(s_coords[0] + e_coords[0]) / 2.0, (s_coords[1] + e_coords[1]) / 2.0]
                        new = dict(obj)
                        new['geometry'] = [s_coords, mid, e_coords]
                        return new
                    # if only start known, return single-point geometry
                    if s_coords:
                        new = dict(obj)
                        new['geometry'] = [s_coords]
                        return new
                    return obj

                fast = _ensure_geom(r['fast'])
                eco = _ensure_geom(r['eco'])
                return {"from_loc": start, "to_loc": end, "fast": fast, "eco": eco}
        raise


def get_parking(hours: int = 6) -> Dict[str, Any]:
    try:
        resp = requests.get(f"{BASE_URL}/parking", params={"hours": hours}, timeout=3)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # fallback: quick synthetic pattern
        import numpy as np
        from datetime import datetime, timedelta

        out = []
        now = datetime.now()
        for i in range(hours):
            t = now + timedelta(hours=i)
            val = 0.5 + 0.4 * np.sin(2 * np.pi * (t.hour) / 24.0)
            out.append({"hour": t.strftime("%Y-%m-%d %H:%M"), "predicted_occupancy": float(val), "uncertainty_std": 0.05})
        return {"hours": out}
