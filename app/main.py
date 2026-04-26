import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.db import init_db
from app.services.auth import (
    authenticate_user,
    create_user,
    get_user_by_id,
    google_oauth_configured,
    upsert_google_user,
)
from app.services.dsa import (
    DSA_QUESTIONS,
    build_generated_dsa_question,
    gemini_dsa_configured,
    get_generated_dsa_questions_for_user,
    get_all_dsa_questions,
    get_dsa_question,
    save_generated_dsa_questions_for_user,
)
from app.services.dsa_runner import run_dsa_code
from app.services.interview import (
    build_interview_plan,
    build_interview_package,
    build_interview_questions,
    build_resume_interview_questions,
    gemini_configured,
    generate_interview_feedback,
    normalize_experience_level,
)
from app.services.resume import extract_resume_text, infer_resume_profile


BASE_DIR = Path(__file__).resolve().parent.parent


def load_local_env() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()

app = FastAPI(title="AI Interview and Resume Platform")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "dev-session-secret"))
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
async def startup_event() -> None:
    init_db()


def get_current_user(request: Request) -> dict | None:
    return get_user_by_id(request.session.get("user_id"))


def pop_flash(request: Request) -> str | None:
    return request.session.pop("flash", None)


def require_user(request: Request) -> dict | RedirectResponse:
    user = get_current_user(request)
    if user:
        return user
    request.session["flash"] = "Please log in first."
    return RedirectResponse(url="/?auth=login", status_code=303)


def get_session_dsa_questions(request: Request) -> list[dict]:
    user_id = request.session.get("user_id")
    if not user_id:
        return []
    return get_generated_dsa_questions_for_user(user_id)


def save_session_dsa_questions(request: Request, questions: list[dict]) -> None:
    user_id = request.session.get("user_id")
    if not user_id:
        return
    save_generated_dsa_questions_for_user(user_id, questions)


def render_dashboard(
    request: Request,
    *,
    interview_questions: list[dict] | None = None,
    interview_source: str | None = None,
    auth_mode: str = "login",
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": get_current_user(request),
            "auth_mode": auth_mode,
            "flash_message": pop_flash(request),
            "google_ready": google_oauth_configured(),
            "google_callback_url": str(request.url_for("google_callback")),
            "gemini_ready": gemini_configured(),
            "dsa_questions": get_all_dsa_questions(get_session_dsa_questions(request)),
            "interview_questions": interview_questions,
            "interview_source": interview_source,
        },
    )


def render_interview_page(
    request: Request,
    *,
    interview_title: str,
    interview_summary: str,
    interview_questions: list[dict],
    interview_source: str,
    profile: dict,
    interview_plan: dict,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "interview.html",
        {
            "user": get_current_user(request),
            "flash_message": pop_flash(request),
            "interview_title": interview_title,
            "interview_summary": interview_summary,
            "interview_questions": interview_questions,
            "interview_source": interview_source,
            "profile": profile,
            "interview_plan": interview_plan,
            "gemini_ready": gemini_configured(),
        },
    )


def render_dsa_page(
    request: Request,
    question_id: str,
    *,
    code: str | None = None,
    language: str = "python",
    run_result: dict | None = None,
) -> HTMLResponse:
    session_questions = get_session_dsa_questions(request)
    question = get_dsa_question(question_id, session_questions)
    if not question:
        raise HTTPException(status_code=404, detail="DSA question not found")
    if language not in question["starter_code"]:
        language = "python"
    return templates.TemplateResponse(
        request,
        "dsa.html",
        {
            "user": get_current_user(request),
            "flash_message": pop_flash(request),
            "dsa_questions": get_all_dsa_questions(session_questions),
            "active_dsa": question,
            "selected_language": language,
            "editor_code": code or question["starter_code"][language],
            "run_result": run_result,
            "gemini_ready": gemini_dsa_configured(),
        },
    )


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, auth: str = "login") -> HTMLResponse:
    return render_dashboard(request, auth_mode=auth if auth in {"login", "register"} else "login")


@app.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
) -> RedirectResponse:
    success, message = create_user(name, email, password)
    request.session["flash"] = message
    return RedirectResponse(url="/?auth=login" if success else "/?auth=register", status_code=303)


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
) -> RedirectResponse:
    user = authenticate_user(email, password)
    if not user:
        request.session["flash"] = "Invalid email or password."
        return RedirectResponse(url="/?auth=login", status_code=303)

    request.session["user_id"] = user["id"]
    request.session["flash"] = f"Welcome back, {user['name']}."
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/?auth=login", status_code=303)


@app.get("/auth/google")
async def google_login(request: Request) -> RedirectResponse:
    if not google_oauth_configured():
        request.session["flash"] = "Google login is not configured for this app yet. Add Google OAuth credentials first."
        return RedirectResponse(url="/?auth=login", status_code=303)

    state = os.urandom(16).hex()
    request.session["google_state"] = state
    params = urlencode(
        {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "redirect_uri": str(request.url_for("google_callback")),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }
    )
    return RedirectResponse(
        url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}",
        status_code=303,
    )


@app.get("/auth/google/callback")
async def google_callback(request: Request, code: str = "", state: str = "") -> RedirectResponse:
    expected_state = request.session.get("google_state")
    request.session.pop("google_state", None)
    if not code or state != expected_state:
        request.session["flash"] = "Google login failed because the OAuth state or code was invalid."
        return RedirectResponse(url="/?auth=login", status_code=303)

    try:
        token_payload = urlencode(
            {
                "code": code,
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uri": str(request.url_for("google_callback")),
                "grant_type": "authorization_code",
            }
        ).encode()
        token_request = UrlRequest(
            "https://oauth2.googleapis.com/token",
            data=token_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(token_request) as response:
            token_data = json.loads(response.read().decode())

        userinfo_request = UrlRequest(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        with urlopen(userinfo_request) as response:
            profile = json.loads(response.read().decode())
    except Exception:
        request.session["flash"] = (
            f"Google login could not complete. Verify Google Cloud credentials and callback URL {request.url_for('google_callback')}."
        )
        return RedirectResponse(url="/?auth=login", status_code=303)

    user = upsert_google_user(
        google_sub=profile["sub"],
        email=profile.get("email", ""),
        name=profile.get("name", "Google User"),
    )
    request.session["user_id"] = user["id"]
    request.session["flash"] = f"Signed in with Google as {user['name']}."
    return RedirectResponse(url="/", status_code=303)


@app.post("/resume", response_class=HTMLResponse)
async def resume_screen(
    request: Request,
    resume: UploadFile = File(...),
):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user

    resume_bytes = await resume.read()
    resume_text = extract_resume_text(resume.filename or "", resume_bytes)
    if not resume_text.strip():
        request.session["flash"] = "Could not read text from that resume. Try PDF, DOCX, or TXT."
        return RedirectResponse(url="/", status_code=303)

    profile = infer_resume_profile(resume_text, resume.filename or "")
    profile["interview_source"] = "resume"
    profile["missing_skills"] = []
    profile["top_terms"] = []
    profile["allow_fallback"] = False
    profile["refresh_token"] = os.urandom(8).hex()
    profile["previous_questions"] = []
    interview_package = build_interview_package(profile)
    profile["generation_source"] = interview_package["source"]
    profile["generation_error"] = interview_package["error"]
    return render_interview_page(
        request,
        interview_title=f"{profile['target_role']} Interview",
        interview_summary=(
            f"Resume-based interview generated from detected skills and approximately "
            f"{profile['years_of_experience']} years of experience."
        ),
        interview_questions=interview_package["questions"],
        interview_source="resume",
        profile=profile,
        interview_plan=build_interview_plan(profile),
    )


@app.post("/interview", response_class=HTMLResponse)
async def interview_plan(
    request: Request,
    role: str = Form(...),
    skills: str = Form(...),
    experience_level: str = Form(...),
):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user

    profile = {
        "target_role": role,
        "required_skills": [skill.strip() for skill in skills.split(",") if skill.strip()],
        "experience_level": experience_level,
        "years_of_experience": None,
        "interview_source": "skills",
        "missing_skills": [],
        "top_terms": [],
        "allow_fallback": False,
        "refresh_token": os.urandom(8).hex(),
        "previous_questions": [],
    }
    interview_package = build_interview_package(profile)
    profile["generation_source"] = interview_package["source"]
    profile["generation_error"] = interview_package["error"]
    return render_interview_page(
        request,
        interview_title=f"{experience_level} {role} Interview",
        interview_summary="Skill-based interview generated from the selected role, skills, and level.",
        interview_questions=interview_package["questions"],
        interview_source="skills",
        profile=profile,
        interview_plan=build_interview_plan(profile),
    )


@app.post("/interview/feedback")
async def interview_feedback(
    request: Request,
    payload: dict,
) -> JSONResponse:
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Please log in first.")

    question_answers = payload.get("question_answers", [])
    profile = payload.get("profile", {})
    return JSONResponse(generate_interview_feedback(question_answers, profile))


@app.post("/interview/questions")
async def interview_questions_api(
    request: Request,
    payload: dict,
) -> JSONResponse:
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Please log in first.")

    profile = payload.get("profile", {})
    level = normalize_experience_level(payload.get("experience_level") or profile.get("experience_level", "Junior"))
    interview_source = payload.get("interview_source", "skills")
    previous_questions = payload.get("previous_questions", [])

    profile["experience_level"] = level
    profile["interview_source"] = interview_source
    profile["allow_fallback"] = False
    profile["refresh_token"] = str(payload.get("refresh_token") or os.urandom(8).hex())
    profile["previous_questions"] = previous_questions if isinstance(previous_questions, list) else []
    interview_package = build_interview_package(profile)
    profile["generation_source"] = interview_package["source"]
    profile["generation_error"] = interview_package["error"]
    return JSONResponse(
        {
            "questions": interview_package["questions"],
            "profile": profile,
            "interview_plan": build_interview_plan(profile),
        }
    )


@app.get("/dsa", response_class=HTMLResponse)
async def dsa_landing(request: Request):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    return render_dsa_page(request, get_all_dsa_questions(get_session_dsa_questions(request))[0]["id"])


@app.get("/dsa/{question_id}", response_class=HTMLResponse)
async def dsa_question_page(request: Request, question_id: str, language: str = "python"):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user
    return render_dsa_page(request, question_id, language=language)


@app.post("/dsa/{question_id}/run", response_class=HTMLResponse)
async def dsa_run(request: Request, question_id: str, code: str = Form(...), language: str = Form(...)):
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user

    question = get_dsa_question(question_id, get_session_dsa_questions(request))
    if not question:
        raise HTTPException(status_code=404, detail="DSA question not found")

    run_result = run_dsa_code(question, code, language)
    return render_dsa_page(request, question_id, code=code, language=language, run_result=run_result)


@app.post("/dsa/generate")
async def dsa_generate(request: Request, payload: dict) -> JSONResponse:
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Please log in first.")

    topic = str(payload.get("topic", "Array")).strip() or "Array"
    difficulty = str(payload.get("difficulty", "Medium")).strip() or "Medium"
    refresh_token = str(payload.get("refresh_token") or os.urandom(8).hex())
    generated_question, generation_error = build_generated_dsa_question(topic, difficulty, refresh_token=refresh_token)
    if not generated_question:
        return JSONResponse(status_code=502, content={"detail": generation_error})
    session_questions = get_session_dsa_questions(request)
    session_questions.insert(0, generated_question)
    save_session_dsa_questions(request, session_questions[:12])
    return JSONResponse({"question_id": generated_question["id"]})
