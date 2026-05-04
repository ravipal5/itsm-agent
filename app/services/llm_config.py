import os


def get_groq_api_key() -> str:
    return os.getenv("GROQ_API_KEY", "")


def groq_configured() -> bool:
    return bool(get_groq_api_key())


def get_groq_model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def get_gemini_api_key() -> str:
    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )


def gemini_configured() -> bool:
    return bool(get_gemini_api_key())


def llm_configured() -> bool:
    return groq_configured() or gemini_configured()


def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
