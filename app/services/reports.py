import json

from app.db import get_connection


def save_interview_report(user_id: int, profile: dict, question_answers: list[dict], feedback: dict) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO interview_reports (
                user_id, source, role, level, profile_json, qa_json, feedback_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                str(profile.get("interview_source", "skills")),
                str(profile.get("target_role", "")),
                str(profile.get("experience_level", "")),
                json.dumps(profile),
                json.dumps(question_answers),
                json.dumps(feedback),
            ),
        )
        return int(cursor.lastrowid)


def list_interview_reports(user_id: int, limit: int = 20) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, source, role, level, feedback_json, created_at
            FROM interview_reports
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    reports: list[dict] = []
    for row in rows:
        feedback = json.loads(row["feedback_json"] or "{}")
        reports.append(
            {
                "id": row["id"],
                "source": row["source"],
                "role": row["role"],
                "level": row["level"],
                "created_at": row["created_at"],
                "completion": feedback.get("completion", 0),
                "overall": feedback.get("overall", ""),
            }
        )
    return reports


def save_dsa_submission(user_id: int, submission: dict) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO dsa_submissions (
                user_id, question_id, question_title, language, ok, passed_count, total_count, error_text, code_text, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                str(submission.get("question_id", "")),
                str(submission.get("question_title", "")),
                str(submission.get("language", "")),
                1 if submission.get("ok") else 0,
                int(submission.get("passed_count", 0) or 0),
                int(submission.get("total_count", 0) or 0),
                str(submission.get("error", "")),
                str(submission.get("code", "")),
                json.dumps(submission.get("run_result", {})),
            ),
        )
        return int(cursor.lastrowid)


def list_dsa_submissions(user_id: int, limit: int = 50, question_id: str | None = None) -> list[dict]:
    with get_connection() as connection:
        if question_id:
            rows = connection.execute(
                """
                SELECT id, question_id, question_title, language, ok, passed_count, total_count, error_text, code_text, result_json, created_at
                FROM dsa_submissions
                WHERE user_id = ? AND question_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, question_id, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, question_id, question_title, language, ok, passed_count, total_count, error_text, code_text, result_json, created_at
                FROM dsa_submissions
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

    submissions: list[dict] = []
    for row in rows:
        submissions.append(
            {
                "id": row["id"],
                "question_id": row["question_id"],
                "question_title": row["question_title"],
                "language": row["language"],
                "ok": bool(row["ok"]),
                "passed_count": row["passed_count"],
                "total_count": row["total_count"],
                "error": row["error_text"] or "",
                "code": row["code_text"] or "",
                "run_result": json.loads(row["result_json"] or "{}"),
                "submitted_at": row["created_at"],
            }
        )
    return submissions
