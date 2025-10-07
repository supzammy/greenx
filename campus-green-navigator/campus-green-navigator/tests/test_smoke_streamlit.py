import subprocess
import time
import requests
import os
from pathlib import Path


def test_streamlit_smoke(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    # Start streamlit in the project dir
    p = subprocess.Popen([env.get('VIRTUAL_ENV') + '/bin/streamlit' if env.get('VIRTUAL_ENV') else 'streamlit', 'run', 'app.py', '--server.port', '8504'], cwd=str(root), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        # wait for the server to come up
        started = False
        for _ in range(20):
            try:
                r = requests.get('http://localhost:8504', timeout=1)
                if r.status_code == 200:
                    started = True
                    break
            except Exception:
                time.sleep(0.5)
        assert started, 'Streamlit did not start in time'
    finally:
        p.terminate()
        try:
            p.wait(timeout=3)
        except Exception:
            p.kill()
