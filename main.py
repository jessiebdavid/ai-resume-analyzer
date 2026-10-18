import re
from io import BytesIO

import fitz
from fastapi import File, Form, HTTPException, UploadFile

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

def analyze_text(resume_text: str, job_description: str) -> dict:
    resume_skills = extract_skills(resume_text)
    required_skills = extract_skills(job_description)

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


@app.post("/analyze")
def analyze_resume(request: AnalyzeRequest):
    return analyze_text(
        request.resume_text,
        request.job_description,
    )

MAX_PDF_SIZE = 5 * 1024 * 1024  # 5 MB


@app.post("/analyze-pdf")
async def analyze_pdf(
    file: UploadFile = File(...),
    job_description: str = Form(..., min_length=1, max_length=20000),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file.",
        )

    pdf_bytes = await file.read(MAX_PDF_SIZE + 1)

    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=413,
            detail="PDF must be 5 MB or smaller.",
        )

    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF.",
        )

    try:
        with fitz.open(stream=BytesIO(pdf_bytes), filetype="pdf") as document:
            if document.is_encrypted:
                raise HTTPException(
                    status_code=400,
                    detail="Password-protected PDFs are not supported.",
                )

            resume_text = "\n".join(
                page.get_text() for page in document
            ).strip()

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read this PDF. Please upload a valid PDF.",
        )

    if not resume_text:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found. Scanned PDFs are not supported yet.",
        )

    if not job_description.strip():
        raise HTTPException(
            status_code=422,
            detail="Job description must not be blank.",
        )

    return analyze_text(resume_text, job_description)
