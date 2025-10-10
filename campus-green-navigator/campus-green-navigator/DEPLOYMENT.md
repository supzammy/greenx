Deployment notes for Campus Green Navigator

Run locally
-----------
# create and activate venv (macOS / Linux)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# run streamlit app
streamlit run app.py

Run tests
---------
# ensure local imports resolve
PYTHONPATH=. pytest -q

Redeploy / Streamlit Cloud
--------------------------
1. Push to `main` branch. Streamlit Cloud watches the repository and will build on new commits.
2. Streamlit Cloud installs packages from the `requirements.txt` at the repository root. Ensure `streamlit-folium` is listed there.
3. If a ModuleNotFoundError occurs during startup, check the deployment logs in Streamlit Cloud:
   - Look for the "Installing collected packages" list and confirm `streamlit-folium` was installed.
   - If it's not present or the install failed, pin a compatible version in `requirements.txt` and push again.
4. If redeploy is needed manually, use Streamlit Cloud's "Deploy latest" / "Trigger deploy" button.

Notes
-----
- The app includes a defensive import for `streamlit_folium` so missing package won't crash the app at import time; however the intended fix is to make sure `streamlit-folium` is installed in the deploy environment.
- If you are using a platform other than Streamlit Cloud, ensure your build steps install the `requirements.txt` from the repository root.
