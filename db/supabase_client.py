import logging
import os

from dotenv import load_dotenv

for env_file in [".env", "/etc/secrets/.env", os.path.join(os.getcwd(), ".env")]:
    if os.path.exists(env_file):
        load_dotenv(env_file)

logger = logging.getLogger("db.supabase_client")

_supabase_client = None
_init_attempted = False

def get_supabase_client():
    """
    Returns an initialized Supabase Client if credentials are provided in the environment.
    Gracefully returns None if credentials are not configured or connection cannot be established.
    """
    global _supabase_client, _init_attempted
    if _init_attempted:
        return _supabase_client

    _init_attempted = True
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        print("[DB] Supabase credentials not found in environment. Using local file/JSON storage fallback.")
        logger.info("[DB] Supabase credentials not found in environment. Using local file/JSON storage fallback.")
        _supabase_client = None
        return None

    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
        print(f"[DB] Connected to Supabase at {url}")
        logger.info(f"[DB] Connected to Supabase at {url}")
        return _supabase_client
    except Exception as e:
        print(f"[DB] Failed to initialize Supabase client ({e}). Operating in local fallback mode.")
        logger.warning(f"[DB] Failed to initialize Supabase client ({e}). Operating in local fallback mode.")
        _supabase_client = None
        return None

def is_supabase_enabled() -> bool:
    """Check whether a live Supabase connection is available."""
    client = get_supabase_client()
    return client is not None
