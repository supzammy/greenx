CI notes

A GitHub Actions workflow is included at `.github/workflows/ci.yml`.

What it does:
- Runs on push and pull_request
- Sets up Python 3.12
- Installs dependencies from `requirements.txt` if present, otherwise installs a minimal test set
- Runs `pytest`

To test locally replicate what CI does:

```bash
source .venv/bin/activate
pip install -r requirements.txt  # if you have one
pytest
```
