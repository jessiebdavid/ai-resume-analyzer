import re

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

app = FastAPI(
    title="AI Resume Analyzer",
    description="Compare resume skills with job requirements.",
    version="0.2.0",
)

SKILL_PATTERNS = {
    "Python": [r"\bpython\b"],
    "SQL": [r"\bsql\b"],
    "FastAPI": [r"\bfast[\s-]?api\b"],
    "Machine Learning": [r"\bmachine[\s-]+learning\b", r"\bml\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "Scikit-learn": [r"\bscikit[\s-]?learn\b", r"\bsklearn\b"],
    "Git": [r"\bgit\b"],
    "GitHub": [r"\bgithub\b"],
    "Java": [r"\bjava\b"],
    "JavaScript": [r"\bjavascript\b"],
    "React": [r"\breact\b"],
    "HTML": [r"\bhtml\b"],
    "CSS": [r"\bcss\b"],
    "C++": [r"(?<!\w)c\+\+(?!\w)"],
    "PostgreSQL":[r"\bpostgres(?:ql)?\b"],
    "MySQL": [r"\bmysql\b"],
    "Docker": [r"\bdocker\b"],
    "Linux": [r"\blinux\b"],
    "TensorFlow": [r"\btensorflow\b"],
    "PyTorch": [r"\bpytorch\b"],
}

class AnalyzeRequest(BaseModel):
    resume_text: str = Field(min_length=1, max_length=20000)
    job_description: str = Field(min_length=1, max_length=20000)

    @field_validator("resume_text", "job_description")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text must not be blank.")
        return value

def extract_skills(text: str) -> list[str]:
    """Return the recognized skills found in the supplied text."""
    found = []

    for skill, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found.append(skill)
                break

    return found


@app.post("/analyze")
def analyze_resume(request: AnalyzeRequest):
    resume_skills = extract_skills(request.resume_text)
    required_skills = extract_skills(request.job_description)

    matched_skills = [
        skill for skill in required_skills
        if skill in resume_skills
    ]

    missing_skills = [
        skill for skill in required_skills
        if skill not in resume_skills
    ]

    if required_skills:
        match_score = round(
            len(matched_skills) / len(required_skills) * 100,
            1,
        )
        message = "Analysis completed."
    else:
        match_score = 0.0
        message = "No recognized skills were found in the job description."

    return {
        "message": message,
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_score": match_score,
    }
