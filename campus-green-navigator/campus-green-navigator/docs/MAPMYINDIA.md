MapmyIndia integration

This project supports MapmyIndia as an optional routing provider. When your MapmyIndia Client ID and Client Secret are set in the environment, the app will attempt to use MapmyIndia for routing and fall back to the local mock server or embedded campus routes.

Environment

Create a `.env` file in the project root (or set these env vars in your shell):

MAPMYINDIA_CLIENT_ID=your_client_id_here
MAPMYINDIA_CLIENT_SECRET=your_client_secret_here
CGN_API_BASE_URL=http://localhost:8000

How it works

- `api/mapmyindia.py` performs a client_credentials token exchange and caches the token in memory until expiry.
- `api/client.py` will prefer MapmyIndia when the env vars are present. If the call fails or credentials are missing, it falls back to the mock API at `CGN_API_BASE_URL` and finally to internal `data/campus_data.py`.

Manual token test (optional)

You can manually fetch a token to verify credentials using curl (replace CLIENT_ID and CLIENT_SECRET):

curl -X POST "https://outpost.mapmyindia.com/api/security/oauth/token" -u "CLIENT_ID:CLIENT_SECRET" -d "grant_type=client_credentials"

The response should contain `access_token` and `expires_in`.

Notes

- The MapmyIndia directions endpoint used in `api/mapmyindia.py` is a minimal wrapper. Depending on your MapmyIndia account, you may need to adjust the path or parsing logic to match the returned JSON structure.
- If you don't have MapmyIndia credentials or want to demo offline, start the mock server with `uvicorn api.mock_server:app --reload --port 8000` and run the Streamlit app normally.

Recorded MapmyIndia demo mode

If obtaining live MapmyIndia credentials is blocking, you can enable a recorded demo mode that returns a MapmyIndia-styled route so your app appears to use MapmyIndia for the hackathon demo.

To enable recorded demo mode (local only):

export MAPMYINDIA_USE_RECORDED=1

Then run:

streamlit run app.py

The app will return a sample route from `data/mapmyindia_sample_route.json` and tag the response with `provider: mapmyindia-recorded`. Replace the sample with a real MapmyIndia JSON later when you have keys.
