- `FastAPI` for the backend
- `SQLite` for storage
- server-rendered HTML with small JavaScript
- rule-based resume scoring
- a pluggable AI service layer for future API-based or tiny local-model upgrades

## Features in this MVP

- User registration and login with SQLite-backed accounts
- Optional Google login hook through OAuth credentials
- Resume upload with keyword-based fit scoring and resume-driven interview generation
- Interview question generation from job role + skills + experience level
- Browser voice assistant controls for reading questions and capturing spoken answers
- DSA practice workspace with question bank, starter code, and reference solutions
- Simple dashboard in the browser

## Recommended AI strategy on this machine

Use a hybrid model:

- Run the app locally
- Keep resume parsing and scoring lightweight
- Use a cloud API for advanced AI later
- Avoid local models larger than about 1B parameters

If you want offline AI later, prefer very small GGUF models through `llama.cpp`, but only for short prompts.

## Run

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the server:

```powershell
python -m uvicorn app.main:app --reload
```

4. Open:

`http://127.0.0.1:8000`

## Google login setup

Set these environment variables before starting the server if you want Google sign-in:

```powershell
$env:GOOGLE_CLIENT_ID="your-client-id"
$env:GOOGLE_CLIENT_SECRET="your-client-secret"
$env:SESSION_SECRET="replace-this-in-real-use"
```

## Groq/Gemini setup for interview + DSA generation

Set these environment variables before starting the server:

```powershell
$env:GROQ_API_KEY="your-groq-api-key"
$env:GROQ_MODEL="llama-3.3-70b-versatile"
$env:GROQ_DSA_MODEL="llama-3.1-8b-instant"
$env:GEMINI_API_KEY="your-gemini-api-key"
$env:GEMINI_MODEL="gemini-2.5-flash"
$env:GEMINI_DSA_MODEL="gemini-2.0-flash-lite"
```

`GROQ_API_KEY` is preferred and used first. Gemini remains available as a fallback if Groq is not configured.

## Troubleshooting generation errors

- If you see `HTTP 403 error code: 1010` on Groq generation:
  - verify the model is allowed in your Groq project limits
  - set `GROQ_DSA_MODEL=llama-3.1-8b-instant` as fallback
  - rotate API key if it was exposed
- If you see Gemini `429`:
  - it is a quota/rate-limit issue
  - wait for reset window or use another project/key

## Next practical upgrades

- add robust PDF resume text extraction
- add coding submission runner in a sandbox
- connect to an external LLM API for feedback and follow-up questions
- store interview history and candidate reports
