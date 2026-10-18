
from fastapi.testclient import TestClient

from main import app, extract_skills, analyze_text


client = TestClient(app)


def test_extract_skills():
    text = "I use Python, SQL, and React."
    skills = extract_skills(text)

    assert "Python" in skills
    assert "SQL" in skills
    assert "React" in skills


def test_analyze_text_match_score():
    result = analyze_text(
        "Python, SQL, Machine Learning",
        "Python, SQL, FastAPI, Machine Learning",
    )

    assert result["match_score"] == 75.0
    assert result["missing_skills"] == ["FastAPI"]


def test_homepage():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Welcome to the AI Resume Analyzer!"
    )


def test_analyze_rejects_empty_resume():
    response = client.post(
        "/analyze",
        json={
            "resume_text": "",
            "job_description": "Python and SQL",
        },
    )

    assert response.status_code == 422
