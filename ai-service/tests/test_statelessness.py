import os
import re
from pathlib import Path

AI_SERVICE_DIR = Path(__file__).resolve().parent.parent


def test_zero_database_credentials_or_drivers():
    """
    Ensure the AI service remains 100% stateless with zero DB credentials or DB drivers.
    """
    forbidden_terms = [
        "postgresql://",
        "psycopg2.connect",
        "create_engine",
        "asyncpg",
        "supabase-py",
        "SUPABASE_DB_URL",
        "SUPABASE_DB_PASSWORD"
    ]

    for py_file in (AI_SERVICE_DIR / "app").glob("**/*.py"):
        content = py_file.read_text(encoding="utf-8")
        for term in forbidden_terms:
            assert term not in content, f"Forbidden database reference '{term}' found in {py_file}"
