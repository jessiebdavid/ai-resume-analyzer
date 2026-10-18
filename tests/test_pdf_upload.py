
from io import BytesIO

import pymupdf
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def create_test_pdf(text: str) -> bytes:
    """Create a small in-memory PDF containing test text."""
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def test_valid_pdf_upload():
    pdf_bytes = create_test_pdf(
        "Python SQL Machine Learning"
    )

    response = client.post(
        "/analyze-pdf",
        files={
            "file": (
                "resume.pdf",
                BytesIO(pdf_bytes),
                "application/pdf",
            )
        },
        data={
            "job_description": "Python SQL FastAPI"
        },
    )

    assert response.status_code == 200

    result = response.json()
    assert result["matched_skills"] == ["Python", "SQL"]
    assert result["missing_skills"] == ["FastAPI"]
    assert result["match_score"] == 66.7


def test_non_pdf_upload_is_rejected():
    response = client.post(
        "/analyze-pdf",
        files={
            "file": (
                "resume.txt",
                BytesIO(b"Python SQL"),
                "text/plain",
            )
        },
        data={
            "job_description": "Python SQL"
        },
    )

    assert response.status_code == 400


def test_empty_pdf_is_rejected():
    pdf_bytes = create_test_pdf("")

    response = client.post(
        "/analyze-pdf",
        files={
            "file": (
                "empty.pdf",
                BytesIO(pdf_bytes),
                "application/pdf",
            )
        },
        data={
            "job_description": "Python SQL"
        },
    )

    assert response.status_code == 422


def test_oversized_pdf_is_rejected():
    oversized_content = (
        b"%PDF-" + b"A" * (5 * 1024 * 1024)
    )

    response = client.post(
        "/analyze-pdf",
        files={
            "file": (
                "large.pdf",
                BytesIO(oversized_content),
                "application/pdf",
            )
        },
        data={
            "job_description": "Python SQL"
        },
    )

    assert response.status_code == 413

