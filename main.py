from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from fastapi.middleware.cors import CORSMiddleware

from risk_calculator import calculate_risk
from framework_registry import FRAMEWORKS
from policy_scanner import scan_privacy_policy
from security_scanner import scan_security_headers
from url_utils import validate_and_resolve_url

import time

app = FastAPI(title="AuditApp Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://auditapp.in",
        "https://www.auditapp.in",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# -----------------------------
# Request Models
# -----------------------------

class WebsiteScanRequest(BaseModel):
    url: str


class SelfAssessmentRequest(BaseModel):
    framework: str
    answers: Dict[str, bool]


# -----------------------------
# FRAMEWORK QUESTIONS API
# -----------------------------

@app.get("/framework/{framework_name}")
def get_framework_questions(framework_name: str):

    if framework_name not in FRAMEWORKS:
        return {"error": "Framework not found"}

    controls = FRAMEWORKS[framework_name]

    questions = []

    for key, value in controls.items():
        questions.append({
            "id": key,
            "question": value["description"]
        })

    return {
        "framework": framework_name,
        "questions": questions
    }


# -----------------------------
# WEBSITE SCAN API
# -----------------------------

SCAN_CACHE = {}

@app.post("/scan")
def scan_website(data: WebsiteScanRequest):

    start_time = time.time()

    website_url = data.url.strip()
    
    # 1. URL Normalization & Resilience Layer
    try:
        resolved_url = validate_and_resolve_url(website_url)
    except Exception as e:
        return {
            "error": str(e),
            "privacy_score": 0,
            "security_score": 0,
            "overall_score": 0,
            "risk_grade": "F",
            "detected_privacy": [],
            "missing_privacy": [],
            "detected_security": [],
            "missing_security": [],
            "metadata": {
                "input_url": website_url,
                "status": "invalid"
            }
        }

    cache_key = resolved_url.lower()
    if cache_key in SCAN_CACHE:
        return SCAN_CACHE[cache_key]

    privacy_result = scan_privacy_policy(resolved_url)
    security_result = scan_security_headers(resolved_url)

    if privacy_result.get("error"):
        detected_privacy = []
        missing_privacy = []
    else:
        detected_privacy = privacy_result.get("detected", [])
        missing_privacy = privacy_result.get("missing", [])

    detected_security = security_result.get("detected", [])
    missing_security = security_result.get("missing", [])
    
    privacy_score = int(privacy_result.get("score", 0))
    security_score = int(security_result.get("score", 0))

    overall_score = int((privacy_score + security_score) / 2)

    if overall_score >= 90:
        risk_grade = "A"
    elif overall_score >= 75:
        risk_grade = "B"
    elif overall_score >= 50:
        risk_grade = "C"
    elif overall_score >= 25:
        risk_grade = "D"
    else:
        risk_grade = "F"

    scan_duration = round(time.time() - start_time, 2)

    metadata = {
        "input_url": website_url,
        "normalized_url": resolved_url,
        "status": "validated",
        "scan_duration": f"{scan_duration} seconds",
        "security_headers_checked": len(detected_security) + len(missing_security),
        "privacy_signals_checked": len(detected_privacy) + len(missing_privacy),
        "security_error": security_result.get("error"),
        "privacy_error": privacy_result.get("error")
    }
    
    # If there is a top-level error (e.g. backend unreachable)
    scan_error = None
    if metadata["security_error"] or metadata["privacy_error"]:
        scan_error = "There were errors completing the full scan. Results may be incomplete."

    result_data = {
        "error": scan_error,
        "privacy_score": privacy_score,
        "security_score": security_score,
        "overall_score": overall_score,
        "risk_grade": risk_grade,
        "detected_privacy": detected_privacy,
        "missing_privacy": missing_privacy,
        "privacy_confidence_scores": privacy_result.get("confidence_scores", {}),
        "privacy_page_url": privacy_result.get("privacy_url"),
        "detected_security": detected_security,
        "missing_security": missing_security,
        "metadata": metadata
    }

    SCAN_CACHE[cache_key] = result_data

    return result_data


# -----------------------------
# SELF ASSESSMENT API
# -----------------------------

@app.post("/self-assessment")
def self_assessment(data: SelfAssessmentRequest):

    framework = data.framework
    answers = data.answers

    controls = FRAMEWORKS[framework]

    result = calculate_risk(
        answers,
        controls
    )

    return result


# -----------------------------
# ROOT API
# -----------------------------

@app.get("/")
def root():
    return {"message": "AuditApp Backend Running"}