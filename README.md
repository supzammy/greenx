# Campus Green Navigator

[![CI](https://github.com/supzammy/greenx/actions/workflows/ci.yml/badge.svg)](https://github.com/supzammy/greenx/actions)

A Streamlit demo for campus navigation, eco-routing, parking prediction, and gamified points.

## Features
- Interactive map (Leaflet)
- Fast vs eco route comparison
- Parking occupancy ML forecast
- Points and rewards system
- Mock backend for demos

## Quickstart
```bash
# Clone the repo
https://github.com/supzammy/greenx.git
cd greenx

# (Optional) Create a virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the mock API (in a separate terminal)
python3 api/mock_server.py

# Run the Streamlit app
streamlit run app.py
```

## Deployment

### Streamlit Cloud
1. Fork or push this repo to your GitHub account.
2. Go to [Streamlit Cloud](https://streamlit.io/cloud) and click "New app".
3. Select your repo, set `app.py` as the main file.
4. Add `requirements.txt` (already present).
5. Click "Deploy". Your app will be live at a public URL.

### Hugging Face Spaces
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click "Create new Space".
2. Choose "Streamlit" as the SDK.
3. Point to your forked repo or upload files.
4. Ensure `requirements.txt` is present.
5. Click "Create". The app will build and deploy automatically.

### Heroku
1. Add a `Procfile` with: `web: streamlit run app.py --server.port $PORT`
2. Push to Heroku with `requirements.txt` and `Procfile`.
3. The app will deploy and run on Heroku.

## Map Provider
- Uses Leaflet via [streamlit-folium](https://github.com/randyzwitch/streamlit-folium) for interactive maps.

## CI
- Automated tests and lint via GitHub Actions.

## License
MIT
