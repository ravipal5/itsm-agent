import json
import random
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.services.llm_config import gemini_configured, get_gemini_api_key, get_gemini_model


LEVEL_CONFIG = {
    "Junior": {"depth": "foundation-level", "focus": "execution, learning speed, and clarity"},
    "Mid-level": {"depth": "applied-level", "focus": "tradeoffs, delivery, and ownership"},
    "Senior": {"depth": "advanced-level", "focus": "architecture, mentoring, and decision-making"},
}

OPENERS = [
    "Let's start with your background.",
    "I want to understand how you work in real projects.",
    "I'll ask this like a real screening round.",
]

BEHAVIORAL_PATTERNS = [
    "Tell me about a time you had to deliver as a {level} {role} under pressure. What did you do first?",
    "Describe a situation where you had limited information but still had to move work forward as a {role}.",
    "Walk me through a project where your judgment mattered more than just coding speed.",
]

TECHNICAL_PATTERNS = {
    "Junior": [
        "How have you used {skill} in a project, and what exactly did you build yourself?",
        "If I asked you to explain {skill} to another junior engineer, how would you explain it simply?",
    ],
    "Mid-level": [
        "Tell me about a production decision you made using {skill}. What tradeoff did you accept?",
        "In your experience with {skill}, what usually breaks first when the system grows?",
    ],
    "Senior": [
        "At scale, how would you set standards for using {skill} across a team?",
        "Describe a hard architectural choice involving {skill}. What options did you reject and why?",
    ],
}

SCENARIO_PATTERNS = {
    "Junior": [
        "If a bug reaches production right after your change, how do you investigate it and ask for help?",
        "You join a codebase that looks unfamiliar. How do you become productive in the first week?",
    ],
    "Mid-level": [
        "A release is slipping because of unclear requirements. How do you recover without creating chaos?",
        "Your API is working, but latency is rising every week. What do you inspect before rewriting anything?",
    ],
    "Senior": [
        "A team wants speed, but the system is becoming fragile. How do you reset the direction without blocking delivery?",
        "Two senior engineers disagree on architecture. How do you drive a decision that the team will actually follow?",
    ],
}

RESUME_PATTERNS = [
    "I see {skill} on your resume. Tell me about the hardest part you personally handled with it.",
    "Your resume suggests work around {skill}. What was the real business problem behind that work?",
    "When you used {skill}, what part did you own yourself instead of just supporting others?",
]


def normalize_experience_level(experience_level: str) -> str:
    normalized = experience_level.strip().title()
    if normalized == "Mid-Level":
        normalized = "Mid-level"
    return normalized if normalized in LEVEL_CONFIG else "Junior"


def _sample_unique(pool: list[str], count: int) -> list[str]:
    if not pool:
        return []
    if len(pool) <= count:
        sampled = pool[:]
        random.shuffle(sampled)
        return sampled
    return random.sample(pool, count)


def _question(question_type: str, text: str) -> dict:
    return {"type": question_type, "question": text}


def build_interview_plan(profile: dict) -> dict:
    level = normalize_experience_level(profile.get("experience_level", "Junior"))
    role = profile.get("target_role", "Software Engineer")
    focus = LEVEL_CONFIG[level]["focus"]
    depth = LEVEL_CONFIG[level]["depth"]
    return {
        "headline": f"{level} {role} mock interview with a conversational human-interviewer style.",
        "interviewer_style": f"Tone: practical, direct, and supportive. Depth: {depth}. Focus: {focus}.",
        "stages": [
            "Warm-up and context setting from your background.",
            "Core technical questions aligned to your level and role.",
            "Scenario and tradeoff questions to evaluate decision-making.",
            "Closing question focused on impact, ownership, and communication.",
        ],
    }


def build_interview_questions(role: str, skills: str, experience_level: str) -> list[dict]:
    normalized_level = normalize_experience_level(experience_level)
    skill_list = [skill.strip() for skill in skills.split(",") if skill.strip()]
    return build_interview_package(
        {
            "interview_source": "skills",
            "target_role": role,
            "required_skills": skill_list,
            "experience_level": normalized_level,
        }
    )["questions"]


def build_resume_interview_questions(
    target_role: str,
    matched_skills: list[str],
    missing_skills: list[str],
    top_terms: list[str],
    experience_level: str = "Junior",
    years_of_experience: int | None = None,
) -> list[dict]:
    normalized_level = normalize_experience_level(experience_level)
    return build_interview_package(
        {
            "interview_source": "resume",
            "target_role": target_role,
            "required_skills": matched_skills,
            "missing_skills": missing_skills,
            "top_terms": top_terms,
            "experience_level": normalized_level,
            "years_of_experience": years_of_experience,
        }
    )["questions"]


def build_interview_package(profile: dict) -> dict:
    ai_questions, ai_error = generate_ai_interview_questions(profile)
    if ai_questions:
        return {"questions": ai_questions, "source": "gemini", "error": ""}

    if not profile.get("allow_fallback", True):
        return {"questions": [], "source": "gemini-error", "error": ai_error or "Gemini question generation failed."}

    normalized_level = normalize_experience_level(profile.get("experience_level", "Junior"))
    if profile.get("interview_source") == "resume":
        fallback = build_fallback_resume_questions(
            profile.get("target_role", "Software Engineer"),
            profile.get("required_skills", []),
            profile.get("missing_skills", []),
            profile.get("top_terms", []),
            normalized_level,
            profile.get("years_of_experience"),
        )
    else:
        fallback = build_fallback_interview_questions(
            profile.get("target_role", "Software Engineer"),
            profile.get("required_skills", []),
            normalized_level,
        )
    return {"questions": fallback, "source": "fallback", "error": ai_error}


def build_fallback_interview_questions(role: str, skill_list: list[str], experience_level: str) -> list[dict]:
    opener = random.choice(OPENERS)
    questions = [
        _question("interviewer-intro", opener),
        _question("behavioral", random.choice(BEHAVIORAL_PATTERNS).format(role=role, level=experience_level)),
    ]
    technical_pool = TECHNICAL_PATTERNS[experience_level]
    focus_skills = _sample_unique(skill_list[:6] or ["problem solving", "communication"], min(4, max(2, len(skill_list[:6]) or 2)))
    for skill in focus_skills:
        questions.append(_question("technical", random.choice(technical_pool).format(skill=skill)))
    questions.append(_question("scenario", random.choice(SCENARIO_PATTERNS[experience_level])))
    questions.append(_question("closing", f"Before we close, what makes you a strong fit for this {experience_level} {role} role right now?"))
    return questions


def build_fallback_resume_questions(
    target_role: str,
    matched_skills: list[str],
    missing_skills: list[str],
    top_terms: list[str],
    experience_level: str,
    years_of_experience: int | None,
) -> list[dict]:
    focus_skills = matched_skills[:4] or top_terms[:4] or ["problem solving", "communication"]
    gap_skills = missing_skills[:2]
    intro = f"Thanks for sharing your resume. I'll ask a few questions for a {experience_level} {target_role} discussion."
    walkthrough = f"Walk me through the strongest project on your resume that best represents you for a {target_role} role."
    if years_of_experience is not None:
        walkthrough = f"You appear to have about {years_of_experience} years of experience. Which project best shows your current level for a {target_role} role?"
    questions = [_question("interviewer-intro", intro), _question("resume-walkthrough", walkthrough)]
    for skill in _sample_unique(focus_skills, min(4, len(focus_skills))):
        questions.append(_question("resume-skill", random.choice(RESUME_PATTERNS).format(skill=skill)))
    for skill in gap_skills:
        questions.append(_question("gap-check", f"{skill.title()} is important for this role. If you joined soon, how would you ramp up without slowing the team down?"))
    questions.append(_question("scenario", random.choice(SCENARIO_PATTERNS[experience_level])))
    questions.append(_question("closing", f"What should an interviewer remember about you after this conversation for the {target_role} position?"))
    return questions


def _normalize_question_type(value: str) -> str:
    normalized = (value or "").strip().lower().replace("_", "-")
    if normalized in {"intro", "interviewer-intro", "opening"}:
        return "interviewer-intro"
    if normalized in {"behavior", "behavioral"}:
        return "behavioral"
    if normalized in {"technical", "tech"}:
        return "technical"
    if normalized in {"scenario", "situational"}:
        return "scenario"
    if normalized in {"closing", "final"}:
        return "closing"
    return "technical"


def _finalize_ai_questions(profile: dict, questions: list[dict]) -> list[dict]:
    target_count = 8
    deduped: list[dict] = []
    seen: set[str] = set()
    for item in questions:
        text = str(item.get("question", "")).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append({"type": _normalize_question_type(item.get("type", "technical")), "question": text})

    fallback = build_fallback_resume_questions(
        profile.get("target_role", "Software Engineer"),
        profile.get("required_skills", []),
        profile.get("missing_skills", []),
        profile.get("top_terms", []),
        normalize_experience_level(profile.get("experience_level", "Junior")),
        profile.get("years_of_experience"),
    ) if profile.get("interview_source") == "resume" else build_fallback_interview_questions(
        profile.get("target_role", "Software Engineer"),
        profile.get("required_skills", []),
        normalize_experience_level(profile.get("experience_level", "Junior")),
    )

    for item in fallback:
        if len(deduped) >= target_count:
            break
        key = item["question"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    if len(deduped) >= target_count:
        return deduped[:target_count]

    while len(deduped) < target_count:
        supplement = random.choice(fallback)
        key = supplement["question"].strip().lower()
        if key in seen:
            # Force a slight wording variant so a repeated fallback prompt
            # does not collapse to a single deterministic set.
            variant = {
                "type": supplement["type"],
                "question": supplement["question"].rstrip("?") + " Can you give a concrete example?",
            }
            variant_key = variant["question"].lower()
            if variant_key in seen:
                continue
            seen.add(variant_key)
            deduped.append(variant)
            continue
        seen.add(key)
        deduped.append(supplement)

    return deduped[:target_count]


def generate_ai_interview_questions(profile: dict) -> tuple[list[dict], str]:
    if not gemini_configured():
        return [], "GEMINI_API_KEY is missing."

    variation_token = random.randint(100000, 999999)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Generate a realistic human-sounding mock interview. "
                            "Return only valid JSON. "
                            "Ask one-question-at-a-time style questions, not explanations. "
                            "Vary the questions on every request while staying relevant to the candidate profile.\n\n"
                            + build_generation_prompt(profile, variation_token)
                            + "\n\nReturn JSON with this exact shape: "
                            '{"questions":[{"type":"behavioral","question":"..." }]}'
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 1.15,
        },
    }

    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{get_gemini_model()}:generateContent",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-goog-api-key": get_gemini_api_key(),
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = str(exc)
        return [], f"Gemini request failed: {detail}"
    except (TimeoutError, URLError, ValueError, OSError) as exc:
        return [], f"Gemini request failed: {exc}"

    output_text = extract_gemini_text(data).strip()
    if not output_text:
        return [], "Gemini returned no text output."

    parsed = extract_json_payload(output_text)
    if not parsed:
        return [], "Gemini returned invalid JSON."

    cleaned = []
    for item in parsed.get("questions", []):
        question_text = str(item.get("question", "")).strip()
        question_type = _normalize_question_type(str(item.get("type", "technical")))
        if question_text:
            cleaned.append({"type": question_type, "question": question_text})
    finalized = _finalize_ai_questions(profile, cleaned)
    if not finalized:
        return [], "Gemini returned an empty question list."
    return finalized, ""


def extract_gemini_text(payload: dict) -> str:
    texts: list[str] = []
    for candidate in payload.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            text = part.get("text")
            if text:
                texts.append(text)
    return "".join(texts)


def extract_json_payload(text: str) -> dict | None:
    raw = (text or "").strip()
    if not raw:
        return None

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def build_generation_prompt(profile: dict, variation_token: int) -> str:
    role = profile.get("target_role", "Software Engineer")
    skills = ", ".join(profile.get("required_skills", [])) or "general software engineering"
    experience_level = normalize_experience_level(profile.get("experience_level", "Junior"))
    years_of_experience = profile.get("years_of_experience")
    interview_source = profile.get("interview_source", "skills")
    missing_skills = ", ".join(profile.get("missing_skills", [])) or "none"
    top_terms = ", ".join(profile.get("top_terms", [])) or "none"
    refresh_token = profile.get("refresh_token")
    previous_questions = [str(item).strip() for item in profile.get("previous_questions", []) if str(item).strip()]
    previous_questions_text = " | ".join(previous_questions[:8]) or "none"
    level_guidance = {
        "Junior": (
            "Ask fundamentals, implementation choices, debugging steps, and learning behavior. "
            "Avoid architecture-at-scale and staff-level leadership topics."
        ),
        "Mid-level": (
            "Ask production tradeoffs, ownership decisions, incident handling, and practical scaling choices. "
            "Avoid deep distributed-systems architecture unless candidate explicitly mentions it."
        ),
        "Senior": "Ask architecture, cross-team tradeoffs, leadership judgment, and long-term system direction.",
    }[experience_level]
    return (
        f"Create a realistic mock interview for a candidate led by a human interviewer.\n"
        f"Role: {role}\n"
        f"Experience level: {experience_level}\n"
        f"Years of experience: {years_of_experience}\n"
        f"Key skills: {skills}\n"
        f"Interview source: {interview_source}\n"
        f"Missing skills: {missing_skills}\n"
        f"Resume keywords: {top_terms}\n"
        f"Variation token (use internally, do not output): {variation_token}\n"
        f"Refresh token (use internally, do not output): {refresh_token}\n"
        f"Difficulty guidance: {level_guidance}\n"
        f"Do not repeat these previous questions: {previous_questions_text}\n"
        "Requirements:\n"
        "- Produce exactly 8 unique interview questions.\n"
        "- Questions should sound like a real interviewer speaking naturally in a live round.\n"
        "- Include a mix of behavioral, technical, scenario, and closing questions.\n"
        "- Match the difficulty to the experience level.\n"
        "- Each question must be one sentence and directly ask for experience, reasoning, or decision-making.\n"
        "- Use plain, conversational language. Keep each question under 28 words.\n"
        "- Do not include greetings, answers, notes, or numbering.\n"
        "- Do not repeat question phrasing from previous rounds.\n"
        "- Return JSON only."
    )


def generate_interview_feedback(question_answers: list[dict], profile: dict) -> dict:
    answered = [item for item in question_answers if item.get("answer", "").strip()]
    total_questions = len(question_answers)
    answered_count = len(answered)
    completion = int((answered_count / total_questions) * 100) if total_questions else 0
    strong_signals = 0
    needs_depth = 0
    communication_notes: list[str] = []
    skill_hits: list[str] = []
    profile_skills = [skill.lower() for skill in profile.get("required_skills", [])]
    for item in answered:
        answer = item.get("answer", "").strip()
        words = answer.split()
        lowered = answer.lower()
        if len(words) >= 20:
            strong_signals += 1
        else:
            needs_depth += 1
        if any(token in lowered for token in ["built", "improved", "reduced", "increased", "designed", "led", "owned"]):
            communication_notes.append("Used action-oriented language and described ownership.")
        if any(char.isdigit() for char in answer):
            communication_notes.append("Included measurable details, which improves credibility.")
        for skill in profile_skills:
            if skill and skill in lowered and skill.title() not in skill_hits:
                skill_hits.append(skill.title())
    if answered_count == 0:
        overall = "Interview did not complete because no spoken answers were captured."
    elif strong_signals >= max(2, answered_count // 2):
        overall = "Good interview flow. Answers showed reasonable depth and enough signal to continue screening."
    else:
        overall = "Mixed interview performance. Some answers need more structure, specifics, and evidence of impact."
    strengths = []
    if answered_count:
        strengths.append(f"Answered {answered_count} of {total_questions} questions.")
    if skill_hits:
        strengths.append(f"Referenced relevant skills: {', '.join(skill_hits[:5])}.")
    if communication_notes:
        strengths.append(communication_notes[0])
    if strong_signals:
        strengths.append(f"{strong_signals} answers had enough detail to sound interview-ready.")
    improvements = []
    if answered_count < total_questions:
        improvements.append("Finish every question so the interviewer can evaluate consistency.")
    if needs_depth:
        improvements.append("Give longer answers using project, action, and result instead of short statements.")
    if not any(char.isdigit() for item in answered for char in item.get("answer", "")):
        improvements.append("Add metrics, scale, or outcome numbers to make impact more credible.")
    if not skill_hits and profile_skills:
        improvements.append("Name the exact tools and skills from your background more explicitly in each answer.")
    recommendation = "Use a simple structure for each answer: context, what you personally did, the result, and what you learned."
    return {
        "completion": completion,
        "overall": overall,
        "strengths": strengths[:4],
        "improvements": improvements[:4],
        "recommendation": recommendation,
    }
