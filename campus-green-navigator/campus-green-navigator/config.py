import os
from dotenv import load_dotenv

load_dotenv()

# Base URL for API (mock server by default)
CGN_API_BASE_URL = os.getenv("CGN_API_BASE_URL", "http://localhost:8000")

# Placeholder for MapmyIndia keys (drop into .env when available)
MAPMYINDIA_CLIENT_ID = os.getenv("MAPMYINDIA_CLIENT_ID")
MAPMYINDIA_CLIENT_SECRET = os.getenv("MAPMYINDIA_CLIENT_SECRET")
# config.py
# Put your MapmyIndia API keys or set as environment variables and load them here.

import os

MAPMYINDIA_API_KEY = os.environ.get("MAPMYINDIA_API_KEY", "YOUR_MAPMYINDIA_API_KEY")
MAPMYINDIA_BASE_URL = "https://apis.mapmyindia.com/advancedmaps/v1"
