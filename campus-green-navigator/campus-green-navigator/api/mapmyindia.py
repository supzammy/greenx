import os
import time
from typing import Dict, Any, Optional, Tuple, List
import requests

MAP_TOKEN_INFO = {
    "access_token": None,
    "expires_at": 0,
}


def _get_token_from_env() -> Optional[Dict[str, str]]:
    client_id = os.getenv("MAPMYINDIA_CLIENT_ID")
    client_secret = os.getenv("MAPMYINDIA_CLIENT_SECRET")
    if client_id and client_secret:
        return {"client_id": client_id, "client_secret": client_secret}
    return None


def fetch_token() -> str:
    """Fetch OAuth2 client_credentials token from MapmyIndia and cache it in memory."""
    creds = _get_token_from_env()
    if creds is None:
        raise RuntimeError("MapmyIndia credentials not configured in env")

    now = time.time()
    if MAP_TOKEN_INFO["access_token"] and MAP_TOKEN_INFO["expires_at"] > now + 30:
        return MAP_TOKEN_INFO["access_token"]

    token_url = "https://outpost.mapmyindia.com/api/security/oauth/token"
    resp = requests.post(token_url, auth=(creds["client_id"], creds["client_secret"]), params={"grant_type": "client_credentials"}, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    access_token = data.get("access_token")
    expires_in = data.get("expires_in", 3600)
    MAP_TOKEN_INFO["access_token"] = access_token
    MAP_TOKEN_INFO["expires_at"] = now + int(expires_in)
    return access_token


def _parse_geometry_from_feature(feature: Dict[str, Any]) -> List[Tuple[float, float]]:
    """Extract list of (lat, lon) points from a GeoJSON-like feature.

    Many MapmyIndia responses use [lon, lat] ordering. Convert to (lat, lon) tuples.
    """
    geom = feature.get("geometry") or {}
    coords = geom.get("coordinates")
    if not coords:
        return []

    # If coords is a single LineString (list of [lon,lat])
    if isinstance(coords[0][0], (int, float)):
        pts = [(c[1], c[0]) for c in coords]
        return pts

    # If nested (e.g., MultiLineString), flatten first element
    first = coords[0]
    pts = [(c[1], c[0]) for c in first]
    return pts


def geocode(place: str) -> Tuple[float, float]:
    """Resolve a place name to (lat, lon) using MapmyIndia Geocode API.

    If `place` already looks like 'lat,lon' this returns that parsed pair.
    """
    if "," in place:
        try:
            parts = [p.strip() for p in place.split(",")]
            if len(parts) >= 2:
                # Accept 'lat,lon' or 'lon,lat' heuristically: prefer lat in [-90,90]
                a = float(parts[0])
                b = float(parts[1])
                if -90 <= a <= 90:
                    return a, b
                else:
                    return b, a
        except Exception:
            pass

    creds = _get_token_from_env()
    if creds is None:
        # Without creds, we cannot call MapmyIndia; raise and allow caller to fallback
        raise RuntimeError("MapmyIndia credentials not configured for geocode")

    token = fetch_token()
    headers = {"Authorization": "Bearer " + token}
    url = "https://atlas.mapmyindia.com/api/places/geocode"
    params = {"query": place}
    resp = requests.get(url, headers=headers, params=params, timeout=5)
    resp.raise_for_status()
    j = resp.json()
    # Try common places structure
    try:
        # MapmyIndia may return 'suggestedLocations' or 'results'
        candidates = j.get("suggestedLocations") or j.get("results") or []
        if isinstance(candidates, dict):
            # sometimes object with 'suggestions'
            candidates = candidates.get("suggestions") or []

        if len(candidates) == 0:
            raise RuntimeError("No geocode candidates")
        first = candidates[0]
        lat = float(first.get("lat") or first.get("latitude") or first.get("y"))
        lon = float(first.get("lon") or first.get("longitude") or first.get("x"))
        return lat, lon
    except Exception as e:
        raise RuntimeError(f"Failed to parse geocode response: {e}")


def directions(start: str, end: str) -> Dict[str, Any]:
    """Call MapmyIndia Directions API to get route and geometry from start->end.

    Returns an object with 'fast' and 'eco' entries. Each entry contains
    distance_km, time_min, and geometry (list of (lat,lon) tuples).
    """
    creds = _get_token_from_env()
    if creds is None:
        raise RuntimeError("MapmyIndia credentials not configured in env")

    # Resolve coordinates
    try:
        s_lat, s_lon = geocode(start)
    except Exception:
        # allow start to be a raw 'lat,lon' pair already — geocode will parse that
        s_lat, s_lon = geocode(start)

    try:
        e_lat, e_lon = geocode(end)
    except Exception:
        e_lat, e_lon = geocode(end)

    # Build request — using the advanced maps route endpoint (account-specific id may be required)
    token = fetch_token()
    headers = {"Authorization": f"Bearer {token}"}
    client_id = os.getenv("MAPMYINDIA_CLIENT_ID")
    base = "https://apis.mapmyindia.com/advancedmaps/v1"
    # The API expects lon,lat pairs separated by semicolon
    s_pair = f"{s_lon},{s_lat}"
    e_pair = f"{e_lon},{e_lat}"
    url = f"{base}/{client_id}/route_adv/driving/{s_pair};{e_pair}"

    resp = requests.get(url, headers=headers, timeout=8)
    resp.raise_for_status()
    j = resp.json()

    # Defensive parse for several possible structures
    try:
        # Prefer top-level 'routes' list
        routes = j.get("routes") or j.get("features") or []
        if isinstance(routes, dict):
            # sometimes returned as GeoJSON FeatureCollection
            routes = routes.get("features") or []

        if isinstance(routes, list) and len(routes) > 0:
            r0 = routes[0]
            # distance/duration keys may be in route or properties
            dist_m = r0.get("distance") or r0.get("properties", {}).get("distance") or j.get("distance") or 0
            dur_s = r0.get("duration") or r0.get("properties", {}).get("duration") or j.get("duration") or 0

            # try to extract geometry
            geometry = []
            if r0.get("geometry"):
                geometry = _parse_geometry_from_feature(r0)
            elif r0.get("legs"):
                # try legs -> steps -> geometry
                legs = r0.get("legs")
                if isinstance(legs, list) and len(legs) > 0:
                    first_leg = legs[0]
                    if first_leg.get("steps"):
                        # try collect step geometries
                        coords = []
                        for step in first_leg.get("steps"):
                            if step.get("geometry"):
                                coords.extend(_parse_geometry_from_feature(step))
                        geometry = coords
            else:
                # fallback to features array geometry
                if j.get("features") and isinstance(j.get("features"), list) and len(j.get("features")) > 0:
                    geometry = _parse_geometry_from_feature(j.get("features")[0])

            distance_km = float(dist_m) / 1000.0 if dist_m else 0.0
            time_min = float(dur_s) / 60.0 if dur_s else 0.0

            fast_obj = {"distance_km": round(distance_km, 2), "time_min": int(round(time_min)), "geometry": geometry}
            # basic eco alternative heuristic: slightly shorter distance but slower speed
            eco_obj = {"distance_km": round(distance_km * 0.95, 2), "time_min": max(1, int(round(time_min * 1.05))), "geometry": geometry}

            return {"from_loc": start, "to_loc": end, "provider": "mapmyindia", "fast": fast_obj, "eco": eco_obj}

        # If we get here, no route found
        raise RuntimeError("No routes found in response")
    except Exception as e:
        raise RuntimeError(f"Failed to parse MapmyIndia directions response: {e}")
