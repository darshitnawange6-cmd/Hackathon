import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from root or backend directory
env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Configurable SQLite DB path (can be mounted on persistent disk on Render)
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "backend" / "campus.db")))

# Listen on PORT provided by cloud environment (Render, Railway, Fly, Heroku)
PORT = int(os.getenv("PORT", "8000") or 8000)
HOST = os.getenv("HOST", "0.0.0.0")

# CORS Origins: comma-separated list of allowed domains, or "*" for open access
CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "*").strip()
if CORS_ORIGINS_RAW == "*" or not CORS_ORIGINS_RAW:
    CORS_ORIGINS = ["*"]
else:
    CORS_ORIGINS = [orig.strip() for orig in CORS_ORIGINS_RAW.split(",") if orig.strip()]

# AI Provider settings: "demo" (default fallback, no keys required), "gemini", "openai", "groq"
AI_PROVIDER = os.getenv("AI_PROVIDER", "demo").lower().strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# Determine effective provider
if not GEMINI_API_KEY and not OPENAI_API_KEY and not GROQ_API_KEY:
    AI_PROVIDER = "demo"
elif AI_PROVIDER == "gemini" and not GEMINI_API_KEY:
    AI_PROVIDER = "demo"
elif AI_PROVIDER == "openai" and not OPENAI_API_KEY:
    AI_PROVIDER = "demo"
elif AI_PROVIDER == "groq" and not GROQ_API_KEY:
    AI_PROVIDER = "demo"

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash" if AI_PROVIDER == "gemini" else ("gpt-4o-mini" if AI_PROVIDER == "openai" else "demo-engine"))

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
IS_SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_KEY)
