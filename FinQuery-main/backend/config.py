import os
from pathlib import Path


def load_project_env():
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


load_project_env()

DB_HOST = os.getenv("FINQUERY_DB_HOST", "localhost")
DB_USER = os.getenv("FINQUERY_DB_USER", "root")
DB_PASSWORD = os.getenv("FINQUERY_DB_PASSWORD", "")
DB_NAME = os.getenv("FINQUERY_DB_NAME", "finquery")
