# Campus Green Navigator - Demo

Quick demo instructions

![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg)

CI
--
The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs tests, linting (flake8), type checks (mypy), and coverage. The badge above is a placeholder — update `<owner>/<repo>` to your GitHub repo to show the real status.

- Start the mock API (recommended for demos):

  uvicorn api.mock_server:app --port 8000 --reload

- Run Streamlit (use recorded MapmyIndia responses for deterministic demo):

  MAPMYINDIA_USE_RECORDED=1 streamlit run app.py --server.port 8503

Environment variables

- MAPMYINDIA_USE_RECORDED=1
  Use recorded MapmyIndia responses instead of live requests. Good for demos and offline runs.

- MAPMYINDIA_CLIENT_ID and MAPMYINDIA_CLIENT_SECRET
  When set, the app will attempt to call the live MapmyIndia APIs. Provide real credentials to use the live provider. If not present, the app falls back to the mock server or local campus routes.

Notes

- Clicking anywhere on a route card will now highlight that route and pan the map to it (the card is wrapped with a query param-based link, e.g. ?highlight=fast).
- For production use, consider adding rate-limiting, backoff, and secure credential storage for MapmyIndia keys.
