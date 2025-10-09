# app.py
import os
import joblib
import pandas as pd
import streamlit as st

from data import campus_data
from utils.helpers import calculate_co2_grams, format_minutes
from api.client import get_route, get_parking
from components.points_system import init_points, redeem_reward, REWARDS
import json
from streamlit.components.v1 import html as components_html

# Defensive import: streamlit-folium may not be installed in some deploy environments.
# Import lazily and provide a fallback to avoid ModuleNotFoundError during import time.
try:
    from streamlit_folium import st_folium  # noqa: F401
    _HAS_ST_FOLIUM = True
except Exception:
    _HAS_ST_FOLIUM = False
    def st_folium(*args, **kwargs):
        st.warning("streamlit-folium is not installed. Map embedding disabled. Install 'streamlit-folium' to enable interactive maps.")
        return None

# Defensive import: streamlit-folium may not be installed in some deploy environments.
# Import it lazily and provide a fallback to avoid ModuleNotFoundError during import time.
try:
    from streamlit_folium import st_folium  # noqa: F401
    _HAS_ST_FOLIUM = True
except Exception:
    # Provide a fallback function that renders a helpful message in the Streamlit app
    _HAS_ST_FOLIUM = False
    def st_folium(*args, **kwargs):
        st.warning("streamlit-folium is not installed. Map embedding disabled. Install 'streamlit-folium' to enable interactive maps.")
        return None


def render():
    st.set_page_config(page_title="Campus Green Navigator", layout="wide")

    # Global styles to match spec (minimal, pastel green accents)
    st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
    :root{
        --bg:#f6fbf6;
        --card:#ffffff;
        --muted:#6b7280;
        --accent:#34c759;
        --accent-2:#2fa84a;
        --danger:#ff6b6b;
        --glass: rgba(255,255,255,0.85);
    }
    html,body,iframe{font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;}
    .reportview-container .main { background: linear-gradient(180deg, #f7fdf7 0%, #f3fbf6 100%); }
    .card { background:var(--card); border-radius:12px; padding:16px; box-shadow:0 6px 18px rgba(18,38,17,0.06); transition:box-shadow .18s ease, transform .12s ease; }
    .card:hover { transform: translateY(-4px); box-shadow:0 12px 30px rgba(18,38,17,0.08); }
    .card--active{ border-left:6px solid var(--accent); box-shadow:0 14px 40px rgba(18,38,17,0.10); }
    .card--fast{ border-left:6px solid var(--danger); }
    .card--eco{ border-left:6px solid var(--accent); }
    .sidebar-logo { font-weight:700; font-size:18px; margin-bottom:8px; text-align:center; padding:10px 0; color:var(--accent); }
    .primary-btn > button { background: linear-gradient(90deg,var(--accent),var(--accent-2)) !important; color: white !important; border-radius:10px !important; width:100% !important; border: none !important; padding:8px 12px !important; }
    .stButton>button { border-radius:10px !important; }
    .legend { background:var(--glass); padding:8px 10px; border-radius:8px; box-shadow:0 6px 16px rgba(18,38,17,0.04); font-size:13px }
    .muted { color:var(--muted); }
    .control-panel{ background: linear-gradient(180deg,#fbfff8 0%, #f7fbf7 100%); padding:14px; border-radius:10px; }
    /* Sidebar spacing */
    .sidebar .card { margin-bottom:12px }
    /* small utility */
    .small { font-size:13px }
</style>
""", unsafe_allow_html=True)

    # Sidebar header (compact)

    # Initialize session
    init_points()

    # Sidebar: logo and navigation
    st.sidebar.markdown('<div style="display:flex;align-items:center;gap:10px;padding:8px;background:linear-gradient(90deg,#f0fff4,#f7fbf7);border-radius:10px;margin-bottom:10px"><div style="font-size:22px">🌿</div><div><div style="font-weight:700">Campus Green Navigator</div><div style="font-size:12px;color:#6b7280">Eco routing demo</div></div></div>', unsafe_allow_html=True)
    username = st.sidebar.text_input("Username", value=st.session_state.get("username", "you"))
    st.session_state["username"] = username

    # Simple multipage selector
    page = st.sidebar.selectbox("Page", options=["Home", "Parking", "Leaderboard"]) 

    st.sidebar.markdown("---")
    st.sidebar.markdown('<div class="card">', unsafe_allow_html=True)
    st.sidebar.markdown('### Route Planner')
    # Use sidebar-specific keys to avoid duplicate widget keys with the page controls
    st.sidebar.selectbox("Start", options=list(campus_data.LOCATIONS.keys()), index=0, key='ui_start_sb')
    st.sidebar.selectbox("End", options=[k for k in campus_data.LOCATIONS.keys() if k != st.session_state.get('ui_start_sb')], index=0, key='ui_end_sb')
    st.sidebar.radio("Vehicle Type", options=["Car", "Bike", "EV", "Walk"], index=0, key='ui_vehicle_sb')
    st.sidebar.selectbox("Routing preference", options=["Eco", "Fastest"], index=0, key='ui_pref_sb')
    st.sidebar.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    if st.sidebar.button("Find Eco-Route"):
        pass
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="card">', unsafe_allow_html=True)
    st.sidebar.markdown('### Parking Settings')
    # Sidebar-specific keys for parking controls
    st.sidebar.checkbox("Show parking availability", value=True, key='ui_show_parking_sb')
    st.sidebar.selectbox("Day type", options=["Weekday", "Weekend"], index=0, key='ui_daytype_sb')
    st.sidebar.markdown('Context: <span style="color:#6b7280">Exam Season</span>', unsafe_allow_html=True)
    if st.sidebar.button('Refresh Parking'):
        # Some Streamlit builds may not expose experimental_rerun; fallback to toggling a session flag
        try:
            if hasattr(st, 'experimental_rerun'):
                st.experimental_rerun()
            else:
                raise AttributeError
        except Exception:
            # Toggle a dummy session key to force a rerun
            st.session_state['_refresh_parking'] = not st.session_state.get('_refresh_parking', False)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    with st.sidebar.expander('Developer Details', expanded=False):
        st.text('Route source: ' + str(st.session_state.get('route_source', 'unknown')))
        st.button('Show raw payload (console)')
        st.markdown('Last run logs:')
        st.text_area('Logs', value='No logs yet', height=120)

    st.sidebar.markdown('---')
    st.sidebar.subheader('Your Points')
    st.sidebar.metric('Points', st.session_state.points)

    st.sidebar.markdown('### Redeem Rewards')
    for rname, cost in REWARDS.items():
        btn_label = f"Redeem {rname} — {cost} pts"
        if st.sidebar.button(btn_label, key=f'redeem_{rname}'):
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

    if page == "Home":
        # Page title + compact header
        st.markdown("<h1 style='margin-bottom:4px'>Campus Green Navigator</h1><p style='color:#666;margin-top:0'>Eco-routing & smart parking demo</p>", unsafe_allow_html=True)
        st.markdown("<style> .card { background:#fff; border-radius:8px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,0.06); } .route-fast{border-left:6px solid #ff6b6b} .route-eco{border-left:6px solid #34c759} .control-panel{background:#f7fbf7; padding:16px; border-radius:8px;} .map-placeholder{background:#e9eef7; border-radius:8px; height:340px; display:flex; align-items:center; justify-content:center; color:#6b7280; font-size:18px}</style>", unsafe_allow_html=True)
        # We'll collect route inputs from the left control panel (single source of truth)

        # Page layout: left control panel + right map & route cards
        # make the map bigger and more responsive
        st.markdown("<style> .map-placeholder{height:520px !important; width:100%;}</style>", unsafe_allow_html=True)

        left, right = st.columns([1, 2])
        with left:
            st.markdown('<div class="control-panel">', unsafe_allow_html=True)
            st.subheader("Route Planner")
            # Page-scoped widget keys (avoid colliding with sidebar keys)
            st.selectbox("Start", options=list(campus_data.LOCATIONS.keys()), index=0, key='ui_start_page')
            st.selectbox("End", options=[k for k in campus_data.LOCATIONS.keys() if k != st.session_state.get('ui_start_page')], index=0, key='ui_end_page')
            st.radio("Vehicle Type", options=["Car", "Bike", "Walk", "EV"], index=0, key='ui_vehicle_page')
            st.checkbox("Prefer eco route", value=True, key='ui_eco_page')
            st.markdown("<br>")
            if st.button("Find Eco-Route"):
                # trigger re-run; values are read below
                pass
        st.markdown('</div>', unsafe_allow_html=True)
        # read selected inputs (session-state keys are set by the left controls above)
        # Read selected inputs from page-scoped keys
        start = st.session_state.get('ui_start_page', list(campus_data.LOCATIONS.keys())[0])
        end = st.session_state.get('ui_end_page', next((k for k in campus_data.LOCATIONS.keys() if k != start), list(campus_data.LOCATIONS.keys())[1]))
        vehicle = st.session_state.get('ui_vehicle_page', 'Car')

        # Allow click-anywhere card selection via query params (e.g. ?highlight=fast)
        try:
            from utils.query_helpers import parse_highlight_from_streamlit
            hl = parse_highlight_from_streamlit(st)
            if hl is not None:
                st.session_state['highlight'] = hl
        except Exception:
            # if anything fails, fall back silently
            pass

        # Defensive initial values and attempt to fetch route before rendering the map
        fast = None
        eco = None
        co2_fast = 0.0
        co2_eco = 0.0
        co2_savings = 0.0

        route_source = 'provider'
        try:
            route_resp = get_route(start, end)
            fast = route_resp.get('fast')
            eco = route_resp.get('eco')
        except Exception:
            route_source = 'local'
            route = find_route(start, end)
            if route is None:
                st.warning('No pre-defined route between selected points.')
                fast = None
                eco = None
            else:
                fast = route['fast']
                eco = route['eco']

        # Debug: show which source provided the route
        st.sidebar.write(f"Route source: {route_source}")

        with right:
            # Highlight controls for map interactivity
            st.markdown('<div style="display:flex;gap:8px;margin-bottom:8px">', unsafe_allow_html=True)
            if st.button('Highlight Fast'):
                st.session_state['highlight'] = 'fast'
            if st.button('Highlight Eco'):
                st.session_state['highlight'] = 'eco'
            if st.button('Clear Highlight'):
                st.session_state['highlight'] = None
            st.markdown('</div>', unsafe_allow_html=True)
            # Prepare geometries for the map (list of [lat, lon]) and markers for origin/destination
            fast_geom = []
            eco_geom = []
            origin_marker = None
            dest_marker = None
            try:
                if fast and isinstance(fast.get('geometry'), (list, tuple)):
                    fast_geom = [[float(p[0]), float(p[1])] for p in fast.get('geometry')]
                    # origin/destination from first/last points
                    if len(fast_geom) >= 2:
                        origin_marker = fast_geom[0]
                        dest_marker = fast_geom[-1]
            except Exception:
                fast_geom = []
            try:
                if eco and isinstance(eco.get('geometry'), (list, tuple)):
                    eco_geom = [[float(p[0]), float(p[1])] for p in eco.get('geometry')]
                    if not origin_marker and len(eco_geom) >= 2:
                        origin_marker = eco_geom[0]
                        dest_marker = eco_geom[-1]
            except Exception:
                eco_geom = []

            # default center if no geometry
            default_center = [28.6139, 77.2090]

            highlight = st.session_state.get('highlight')
            map_payload = {
                'fast': fast_geom,
                'eco': eco_geom,
                'center': fast_geom[0] if len(fast_geom) else (eco_geom[0] if len(eco_geom) else default_center),
                'highlight': highlight,
                'origin': origin_marker,
                'dest': dest_marker
            }
            # Build HTML as a plain string and inject the JSON payload afterwards to avoid
            # Python f-string interpolation conflicts with JS template braces like {s}/{z}/{x}/{y}
            map_html = """
            <!doctype html>
            <html>
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
                        <style> #map { height:520px; width:100%; border-radius:12px; box-shadow:0 8px 24px rgba(18,38,17,0.06);} .map-legend { position: absolute; top: 12px; right: 12px; z-index:1000; }</style>
            </head>
            <body>
            <div id="map"></div>
            <div class="map-legend"> <div class="legend"> <span style="color:red;font-weight:700">■</span> Fast &nbsp; <span style="color:green;font-weight:700">■</span> Eco </div></div>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <script>
            const payload = __MAP_PAYLOAD__;
            const map = L.map('map').setView(payload.center, 14);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '© OpenStreetMap'
            }).addTo(map);

            function drawLine(coords, color, label, highlight) {
                if (!coords || coords.length === 0) return null;
                const latlngs = coords.map(c => [c[0], c[1]]);
                const isHighlighted = highlight === label;
                const opts = {
                    color: color,
                    weight: isHighlighted ? 8 : 4,
                    opacity: isHighlighted ? 1.0 : 0.7,
                };
                const line = L.polyline(latlngs, opts).addTo(map);
                return line;
            }

            const fastLine = drawLine(payload.fast, 'red', 'fast', payload.highlight);
            const ecoLine = drawLine(payload.eco, 'green', 'eco', payload.highlight);

            // draw origin/dest markers
            if (payload.origin) {
                L.marker(payload.origin).addTo(map).bindPopup('Origin');
            }
            if (payload.dest) {
                L.marker(payload.dest).addTo(map).bindPopup('Destination');
            }

            // Fit map to available layers, or focus on highlighted route
            function safeFitBounds(layer) {
                try {
                    map.fitBounds(layer.getBounds(), {padding: [30,30]});
                } catch (e) {
                    // fallback
                    map.setView(payload.center, 14);
                }
            }

            const group = new L.FeatureGroup();
            if (fastLine) group.addLayer(fastLine);
            if (ecoLine) group.addLayer(ecoLine);

            if (payload.highlight === 'fast' && fastLine) {
                safeFitBounds(fastLine);
            } else if (payload.highlight === 'eco' && ecoLine) {
                safeFitBounds(ecoLine);
            } else if (group.getLayers().length > 0) {
                map.fitBounds(group.getBounds(), {padding: [30,30]});
            } else {
                map.setView(payload.center, 14);
            }
            </script>
            </body>
            </html>
            """

            # Inject the JSON safely (replace the placeholder) and render
            map_html = map_html.replace("__MAP_PAYLOAD__", json.dumps(map_payload))
            components_html(map_html, height=540)
            st.markdown('<div style="height:12px"></div>')
            # Route comparison cards
            rcol1, rcol2 = st.columns(2)
            # After we've rendered the controls, read the selected values and fetch route
        # read selected inputs (session-state keys are set by the left controls above)
        # Re-read selected inputs (page-scoped keys)
        start = st.session_state.get('ui_start_page', list(campus_data.LOCATIONS.keys())[0])
        end = st.session_state.get('ui_end_page', next((k for k in campus_data.LOCATIONS.keys() if k != start), list(campus_data.LOCATIONS.keys())[1]))
        vehicle = st.session_state.get('ui_vehicle_page', 'Car')

        # Defensive initial values
        fast = None
        eco = None
        co2_fast = 0.0
        co2_eco = 0.0
        co2_savings = 0.0

        # Try to fetch route from provider (MapmyIndia/mock), fallback to local
        route_source = 'provider'
        try:
            route_resp = get_route(start, end)
            fast = route_resp.get('fast')
            eco = route_resp.get('eco')
        except Exception:
            route_source = 'local'
            route = find_route(start, end)
            if route is None:
                st.warning('No pre-defined route between selected points.')
                fast = None
                eco = None
            else:
                fast = route['fast']
                eco = route['eco']

        # Debug: show which source provided the route
        st.sidebar.write(f"Route source: {route_source}")

        # compute CO2 and time comparisons for UI
        try:
            co2_fast = calculate_co2_grams(vehicle, fast['distance_km']) if fast is not None else 0
        except Exception:
            co2_fast = 0
        try:
            co2_eco = calculate_co2_grams(vehicle, eco['distance_km']) if eco is not None else 0
        except Exception:
            co2_eco = 0
        co2_savings = max(0, co2_fast - co2_eco)

        with rcol1:
            # Render the card HTML with active styling when highlighted
            if fast is not None:
                active_cls = ' card--active' if st.session_state.get('highlight') == 'fast' else ''
                # wrap the card in an anchor to set ?highlight=fast so clicking anywhere activates
                card_html = f"<a href='?highlight=fast' style='text-decoration:none;color:inherit'><div class='card card--fast{active_cls}'><h4>Fastest Route</h4><div class='small'><strong>Time:</strong> {format_minutes(fast['time_min'])} &nbsp; <strong>Distance:</strong> {fast['distance_km']} km</div><div style='color:{'#ff6b6b'}'><strong>CO2:</strong> {co2_fast:.0f} g</div></div></a>"
                st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.markdown("<div class='card card--fast'>N/A</div>", unsafe_allow_html=True)

        with rcol2:
            if eco is not None:
                active_cls = ' card--active' if st.session_state.get('highlight') == 'eco' else ''
                card_html = f"<a href='?highlight=eco' style='text-decoration:none;color:inherit'><div class='card card--eco{active_cls}'><h4>Eco-Friendly Route</h4><div class='small'><strong>Time:</strong> {format_minutes(eco['time_min'])} &nbsp; <strong>Distance:</strong> {eco['distance_km']} km</div><div style='color:{'#34c759'}'><strong>CO2:</strong> {co2_eco:.0f} g</div><div style='margin-top:8px'><strong>CO2 Savings:</strong> {int((co2_savings / max(1, co2_fast))*100)}%</div></div></a>"
                st.markdown(card_html, unsafe_allow_html=True)
                # show a small progress bar below the card as well
                if co2_fast > 0:
                    pct = int((co2_savings / co2_fast) * 100)
                else:
                    pct = 0
                # custom colored progress bar using inline HTML
                st.markdown(f"<div style='background:#e6f5ea;border-radius:8px;padding:6px'><div style='width:{pct}%;background:linear-gradient(90deg,var(--accent),var(--accent-2));height:10px;border-radius:6px'></div><div class='small muted' style='margin-top:6px'>{pct}% CO₂ reduction</div></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='card card--eco'>N/A</div>", unsafe_allow_html=True)

        # Environmental impact callout below the cards
        with right:
            if co2_savings > 0:
                st.markdown(f"<div class='card' style='background:#f0fff4'><strong>Environmental Impact</strong><p style='margin:4px 0'>Taking the eco route saves approximately <strong>{int((co2_savings / max(1, co2_fast))*100)}%</strong> CO₂ compared to the fastest route.</p></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='card' style='background:#fff'><strong>Environmental Impact</strong><p style='margin:4px 0'>No CO₂ savings available for the selected trip.</p></div>", unsafe_allow_html=True)

    elif page == "Parking":
        st.title("Campus Green Navigator — Parking Predictions")
        # Keep the ML parking block here
        MODEL_PATH = "ml/parking_model.joblib"
        if os.path.exists(MODEL_PATH):
            try:
                with st.spinner("Loading parking model..."):
                    model = joblib.load(MODEL_PATH)
                st.success("Parking model loaded.")

                from datetime import datetime, timedelta
                import numpy as np

                now = datetime.now()
                feature_rows = []
                hours = []
                for i in range(6):
                    t = now + timedelta(hours=i)
                    hour = t.hour
                    weekday = t.weekday()
                    hour_sin = np.sin(2 * np.pi * hour / 24.0)
                    hour_cos = np.cos(2 * np.pi * hour / 24.0)
                    day_sin = np.sin(2 * np.pi * weekday / 7.0)
                    day_cos = np.cos(2 * np.pi * weekday / 7.0)
                    is_weekend = int(weekday >= 5)
                    is_exam = 0
                    feature_rows.append({
                        "hour_sin": hour_sin,
                        "hour_cos": hour_cos,
                        "day_sin": day_sin,
                        "day_cos": day_cos,
                        "is_weekend": is_weekend,
                        "is_exam": is_exam,
                    })
                    hours.append(t.strftime("%Y-%m-%d %H:%M"))

                X_df = pd.DataFrame(feature_rows)

                try:
                    preds = model.predict(X_df)
                    try:
                        import warnings
                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore", message="X has feature names", category=UserWarning)
                            all_preds = np.vstack([est.predict(X_df.to_numpy()) for est in model.estimators_])
                        stds = np.std(all_preds, axis=0)
                    except Exception:
                        stds = np.zeros_like(preds)

                    df_out = pd.DataFrame({
                        "hour": hours,
                        "predicted_occupancy": preds,
                        "uncertainty_std": stds
                    })

                    st.subheader("6-hour occupancy forecast")
                    st.table(df_out.round(3))

                    st.subheader("Forecast chart")
                    chart_df = df_out.set_index("hour")["predicted_occupancy"]
                    st.line_chart(chart_df)

                except Exception as e:
                    st.error(f"Prediction failed: {e}")

                try:
                    st.subheader("Feature importances")
                    feat_names = ["hour_sin", "hour_cos", "day_sin", "day_cos", "is_weekend", "is_exam"]
                    importances = getattr(model, "feature_importances_", None)
                    if importances is not None:
                        fi = pd.Series(importances, index=feat_names).sort_values(ascending=False)
                        st.bar_chart(fi)
                    else:
                        st.info("Feature importances not available for this model.")
                except Exception as e:
                    st.warning(f"Failed to compute feature importances: {e}")

            except Exception as e:
                st.error(f"Failed to load model: {e}")
        else:
            st.info("Parking model not found. Run the training script to generate one (see README).")

    elif page == "Leaderboard":
        st.title("Campus Green Navigator — Leaderboard")
        lb = st.session_state.get("leaderboard", {"you": st.session_state.points})
        # show top entries sorted
        df_lb = pd.DataFrame(list(lb.items()), columns=["user", "points"]).sort_values("points", ascending=False).reset_index(drop=True)
        # render with small badges
        rows_html = []
        for i, row in df_lb.iterrows():
            rows_html.append(f"<div style='display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-bottom:1px solid #f0f3f0'><div><strong>{i+1}. {row['user']}</strong></div><div style='background:linear-gradient(90deg,var(--accent),var(--accent-2));color:white;padding:6px 10px;border-radius:999px;font-weight:600'>{int(row['points'])}</div></div>")
        st.markdown("<div class='card'>" + "".join(rows_html) + "</div>", unsafe_allow_html=True)

    # ----------------------
    # Parking occupancy (via API client mock or model)
    # Only fetch when user requests (on Parking page or when sidebar toggle enabled) to avoid blocking every rerun
    # ----------------------
    st.markdown("---")
    st.header("Parking Occupancy Prediction (demo)")

    show_parking = st.session_state.get('ui_show_parking_sb', False)
    if page == 'Parking' or show_parking:
        try:
            with st.spinner('Fetching parking predictions...'):
                park = get_parking(hours=6)
            df_out = pd.DataFrame(park.get("hours", []))
            if not df_out.empty:
                st.subheader("6-hour occupancy forecast")
                st.table(df_out.round(3))
                st.subheader("Forecast chart")
                chart_df = df_out.set_index("hour")["predicted_occupancy"]
                st.line_chart(chart_df)
            else:
                st.info("No parking data returned by API.")
        except Exception as e:
            st.error(f"Parking API failed: {e}")
    else:
        st.info("Enable 'Show parking availability' or open the Parking page to fetch forecasts.")


if __name__ == '__main__':
    # When run directly (python app.py) call render(). When executed by `streamlit run`,
    # Streamlit imports the file and expects top-level code to run; however, keeping this
    # guarded reduces side-effects for test imports.
    render()
