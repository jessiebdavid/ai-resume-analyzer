import re

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

app = FastAPI(
    title="AI Resume Analyzer",
    description="Compare resume skills with job requirements.",
    version="0.2.0",
)

@app.get("/")
def home():
    return{
        "message": "Welcome to AI Resume Analyzer!",
        "status": "running",
    }