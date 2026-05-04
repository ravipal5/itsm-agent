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
    add_dsa_submission_for_user,
    build_submission_entry,
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
from app.services.reports import (
    list_dsa_submissions,
    list_interview_reports,
    save_dsa_submission,
    save_interview_report,
)


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
    user = get_current_user(request)
    dsa_submissions = list_dsa_submissions(user["id"], limit=30) if user else []
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "auth_mode": auth_mode,
            "flash_message": pop_flash(request),
            "google_ready": google_oauth_configured(),
            "google_callback_url": str(request.url_for("google_callback")),
            "gemini_ready": gemini_configured(),
            "dsa_questions": get_all_dsa_questions(get_session_dsa_questions(request)),
            "dsa_submissions": dsa_submissions,
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
    submission_report: dict | None = None,
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
            "submission_report": submission_report,
            "submission_history": list_dsa_submissions(request.session.get("user_id") or 0, question_id=question["id"], limit=30),
            "gemini_ready": gemini_dsa_configured(),
        },
    )


def build_submission_report(code: str, language: str, run_result: dict) -> dict:
    code_lines = [line for line in code.splitlines() if line.strip()]
    passed_count = sum(1 for item in run_result.get("results", []) if item.get("passed"))
    total_count = len(run_result.get("results", []))
    score = int((passed_count / total_count) * 100) if total_count else 0

    hints: list[str] = []
    if not code_lines:
        hints.append("Code is empty. Start from starter function and implement logic.")
    if language == "python" and "def " not in code:
        hints.append("Define the required function with `def`.")
    if language == "java" and "class Solution" not in code:
        hints.append("Use `class Solution` and keep the required method signature.")
    if language == "cpp" and "return" not in code:
        hints.append("Make sure the function returns the required value.")
    if language == "csharp" and "class Solution" not in code:
        hints.append("Use `class Solution` and keep the required method signature.")
    if run_result.get("error"):
        hints.append("Fix compile/runtime errors first, then submit again.")
    if run_result.get("ok") and passed_count < total_count:
        hints.append("Some tests failed. Re-check edge cases and constraints.")
    if run_result.get("ok") and passed_count == total_count:
        hints.append("Great job. All tests passed for this submission.")

    return {
        "language": language.upper(),
        "line_count": len(code_lines),
        "passed_count": passed_count,
        "total_count": total_count,
        "score": score,
        "status": "Passed" if run_result.get("ok") else "Failed",
        "error": str(run_result.get("error", "")).strip(),
        "hints": hints[:4],
    }


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
    feedback = generate_interview_feedback(question_answers, profile)
    report_id = save_interview_report(user["id"], profile, question_answers, feedback)
    feedback["report_id"] = report_id
    return JSONResponse(feedback)


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


@app.get("/interview/history")
async def interview_history(request: Request) -> JSONResponse:
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Please log in first.")
    return JSONResponse({"reports": list_interview_reports(user["id"], limit=30)})


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


@app.post("/dsa/{question_id}/submit")
async def dsa_submit(request: Request, question_id: str, code: str = Form(...), language: str = Form(...)) -> HTMLResponse:
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        return user

    question = get_dsa_question(question_id, get_session_dsa_questions(request))
    if not question:
        raise HTTPException(status_code=404, detail="DSA question not found")

    run_result = run_dsa_code(question, code, language)
    submission_report = build_submission_report(code, language, run_result)
    user_id = request.session.get("user_id")
    if user_id:
        submission_entry = build_submission_entry(question, language, run_result)
        submission_entry["code"] = code
        submission_entry["run_result"] = run_result
        add_dsa_submission_for_user(user_id, submission_entry)
        save_dsa_submission(user_id, submission_entry)

    if run_result.get("ok"):
        passed_count = sum(1 for item in run_result.get("results", []) if item.get("passed"))
        total_count = len(run_result.get("results", []))
        request.session["flash"] = f"Submission saved: {question.get('title')} ({language.upper()}) {passed_count}/{total_count} passed."
    else:
        request.session["flash"] = f"Submission saved with errors: {question.get('title')} ({language.upper()})."
    return render_dsa_page(
        request,
        question_id,
        code=code,
        language=language,
        run_result=run_result,
        submission_report=submission_report,
    )


@app.get("/api/dsa/submissions")
async def dsa_submission_history(request: Request) -> JSONResponse:
    user = require_user(request)
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Please log in first.")
    return JSONResponse({"submissions": list_dsa_submissions(user["id"], limit=50)})


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
