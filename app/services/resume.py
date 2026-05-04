from collections import Counter
from datetime import datetime
from io import BytesIO
import re
from xml.etree import ElementTree
import zipfile

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency during import
    PdfReader = None


def extract_resume_text(filename: str, content: bytes) -> str:
    lower_name = filename.lower()
    if lower_name.endswith(".pdf") and PdfReader:
        try:
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    return ""

            chunks: list[str] = []
            for page in reader.pages:
                text = page.extract_text() or ""
                if not text.strip():
                    try:
                        text = page.extract_text(extraction_mode="layout") or ""
                    except Exception:
                        text = ""
                if text.strip():
                    chunks.append(text)

            merged = "\n".join(chunks)
            merged = re.sub(r"\s+\n", "\n", merged)
            merged = re.sub(r"\n{3,}", "\n\n", merged)
            return merged.strip()
        except Exception:
            return ""

    if lower_name.endswith(".docx"):
        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                xml_bytes = archive.read("word/document.xml")
            root = ElementTree.fromstring(xml_bytes)
            text_parts = [node.text for node in root.iter() if node.text]
            return " ".join(text_parts)
        except Exception:
            return ""

    return content.decode("utf-8", errors="ignore")


KNOWN_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "node", "fastapi",
    "django", "flask", "sql", "mysql", "postgresql", "mongodb", "aws",
    "docker", "kubernetes", "git", "rest api", "dsa", "machine learning",
]

ROLE_KEYWORDS = {
    "Data Scientist": ["machine learning", "pandas", "numpy", "data analysis"],
    "Frontend Developer": ["react", "javascript", "typescript", "html", "css"],
    "Backend Developer": ["python", "fastapi", "django", "flask", "api", "sql"],
    "Full Stack Developer": ["react", "node", "python", "sql", "javascript"],
    "DevOps Engineer": ["docker", "kubernetes", "aws", "ci/cd"],
}


def infer_resume_profile(resume_text: str, fallback_filename: str = "") -> dict:
    text = resume_text.lower()
    skills = [skill for skill in KNOWN_SKILLS if skill in text]

    best_role = "Software Engineer"
    best_score = 0
    for role, role_skills in ROLE_KEYWORDS.items():
        score = sum(1 for skill in role_skills if skill in text)
        if score > best_score:
            best_role = role
            best_score = score

    if "frontend" in fallback_filename.lower():
        best_role = "Frontend Developer"
    elif "backend" in fallback_filename.lower():
        best_role = "Backend Developer"

    years_of_experience = estimate_years_of_experience(resume_text)
    experience_level = "Junior"
    if years_of_experience >= 6:
        experience_level = "Senior"
    elif years_of_experience >= 3:
        experience_level = "Mid-level"

    selected_skills = skills[:6] or ["communication", "problem solving"]
    return {
        "target_role": best_role,
        "required_skills": selected_skills,
        "experience_level": experience_level,
        "years_of_experience": years_of_experience,
    }


def estimate_years_of_experience(resume_text: str) -> int:
    current_year = datetime.now().year
    pattern = re.compile(r"(20\d{2})\s*(?:-|–|—|to)\s*(present|current|20\d{2})", re.IGNORECASE)
    spans = []

    for start_text, end_text in pattern.findall(resume_text):
        start_year = int(start_text)
        end_year = current_year if not end_text[:2].isdigit() else int(end_text)
        if 1990 <= start_year <= current_year and start_year <= end_year:
            spans.append((start_year, end_year))

    unique_years = set()
    for start_year, end_year in spans:
        for year in range(start_year, end_year + 1):
            unique_years.add(year)

    if unique_years:
        return max(1, len(unique_years))

    explicit_match = re.search(r"(\d+)\+?\s+years", resume_text, re.IGNORECASE)
    if explicit_match:
        return int(explicit_match.group(1))

    graduation_years = [int(year) for year in re.findall(r"\b(20\d{2})\b", resume_text)]
    if graduation_years:
        plausible = [year for year in graduation_years if 2000 <= year <= current_year]
        if plausible:
            return max(0, current_year - min(plausible))

    return 0


def score_resume_text(resume_text: str, target_role: str, required_skills: str) -> dict:
    skills = [skill.strip().lower() for skill in required_skills.split(",") if skill.strip()]
    text = resume_text.lower()
    matches = [skill for skill in skills if skill in text]
    missing = [skill for skill in skills if skill not in text]
    counts = Counter(word.strip(".,()[]{}:;").lower() for word in resume_text.split())
    top_terms = [term for term, _ in counts.most_common(8) if len(term) > 3]

    score = 0
    if skills:
        score = round((len(matches) / len(skills)) * 100)

    verdict = "Shortlist"
    if score < 40:
        verdict = "Reject"
    elif score < 70:
        verdict = "Review"

    return {
        "target_role": target_role,
        "score": score,
        "verdict": verdict,
        "matched_skills": matches,
        "missing_skills": missing,
        "top_terms": top_terms,
    }
