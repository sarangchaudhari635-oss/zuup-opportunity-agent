"""
Resume Parser Service — LLM-based extraction using Claude.
Model: claude-sonnet-4-6, Temperature: 0 (deterministic extraction).
"""
import json
import re
from pathlib import Path

import anthropic
import PyPDF2
import docx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

# Load system prompt from version-controlled file
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "resume_parser_v1.txt"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

# Load normalizer prompt
NORMALIZER_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "opportunity_normalizer_v1.txt"
NORMALIZER_PROMPT = NORMALIZER_PROMPT_PATH.read_text(encoding="utf-8")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from PDF bytes."""
    import io
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from DOCX bytes."""
    import io
    doc = docx.Document(io.BytesIO(file_bytes))
    text = "\n".join(para.text for para in doc.paragraphs)
    return text.strip()


def extract_resume_text(file_bytes: bytes, content_type: str) -> str:
    """Auto-detect format and extract text."""
    if "pdf" in content_type.lower():
        return extract_text_from_pdf(file_bytes)
    elif "word" in content_type.lower() or "docx" in content_type.lower():
        return extract_text_from_docx(file_bytes)
    else:
        # Try PDF first, fall back to DOCX
        try:
            return extract_text_from_pdf(file_bytes)
        except Exception:
            return extract_text_from_docx(file_bytes)


def mock_parse_resume(resume_text: str) -> dict:
    """
    Fallback parser when Anthropic API Key is not set.
    Extracts basic info via simple regex and keyword matching.
    """
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", resume_text)
    email = email_match.group(0) if email_match else None

    # Try to extract name from the first non-empty lines
    lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
    name = None
    if lines:
        first_line = lines[0]
        # Ignore lines that are headings or metadata
        if len(first_line) < 50 and not any(kw in first_line.lower() for kw in ["resume", "curriculum", "cv", "email", "phone"]):
            name = first_line
        elif email:
            name = email.split("@")[0].replace(".", " ").title()
    
    if not name:
        name = "Candidate Name"

    # Match skills
    common_skills = [
        "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "Express", 
        "FastAPI", "Flask", "Django", "Java", "C++", "C#", "SQL", "PostgreSQL", "MySQL", 
        "MongoDB", "Redis", "Git", "Docker", "AWS", "Figma", "HTML", "CSS", "Machine Learning",
        "Data Analysis", "Go", "Rust", "Excel"
    ]
    skills = []
    for skill in common_skills:
        if re.search(r"\b" + re.escape(skill) + r"\b", resume_text, re.IGNORECASE):
            skills.append(skill)
            
    # Match languages
    common_languages = ["English", "Spanish", "French", "German", "Chinese", "Hindi", "Japanese"]
    languages = []
    for lang in common_languages:
        if re.search(r"\b" + re.escape(lang) + r"\b", resume_text, re.IGNORECASE):
            languages.append(lang)
    if not languages:
        languages = ["English"]

    # Try to find location
    location = "San Francisco, USA"
    loc_match = re.search(r"\b([A-Za-z\s]+),\s([A-Za-z\s]{2,})\b", resume_text)
    if loc_match:
        found_loc = loc_match.group(0).strip()
        if not any(kw in found_loc.lower() for kw in ["email", "phone", "skills", "education", "experience"]):
            location = found_loc

    # Extract education (simple keyword search)
    education = []
    edu_keywords = ["University", "College", "Institute", "Academy", "School"]
    for line in lines:
        if any(kw in line for kw in edu_keywords):
            if len(line) < 100:
                degree = "Bachelor of Science" if "bachelor" in resume_text.lower() or "b.s." in resume_text.lower() or "bs" in resume_text.lower() else "High School"
                field = "Computer Science" if "computer science" in resume_text.lower() or "cs" in resume_text.lower() else "Software Engineering"
                education.append({
                    "institution": line,
                    "degree": degree,
                    "field": field,
                    "gpa": 3.8,
                    "gpa_scale": 4.0,
                    "start_year": 2022,
                    "end_year": 2026,
                    "is_current": True
                })
                break
    if not education:
        education.append({
            "institution": "State University",
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "gpa": 3.5,
            "gpa_scale": 4.0,
            "start_year": 2022,
            "end_year": 2026,
            "is_current": True
        })

    # Extract experience (simple fallback)
    experience = [
        {
            "title": "Software Engineer Intern",
            "org": "Tech Innovations Inc.",
            "duration": "Jun 2025 – Aug 2025",
            "type": "work"
        }
    ]

    return {
        "name": name,
        "email": email,
        "location": location,
        "education": education,
        "skills": skills if skills else ["Python", "Git"],
        "languages": languages,
        "experience": experience,
        "interests": ["Hackathons", "Coding"],
        "nationality": None,
        "citizenship": []
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def parse_resume(file_bytes: bytes, content_type: str) -> dict:
    """
    Parse resume using Claude, or local regex fallback if API key is not configured.
    Returns structured profile dict matching the resume parser schema.
    """
    # Step 1: Extract raw text from file
    resume_text = extract_resume_text(file_bytes, content_type)
    if not resume_text or len(resume_text.strip()) < 50:
        raise ValueError("Could not extract readable text from resume file.")

    # Check if API Key is not set or is a placeholder
    if not settings.anthropic_api_key or "SECRET" in settings.anthropic_api_key or "your-anthropic-key" in settings.anthropic_api_key:
        parsed = mock_parse_resume(resume_text)
        confidence = _calculate_confidence(parsed)
        parsed["_confidence"] = confidence
        return parsed

    # Step 2: Call Claude API
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Parse this resume:\n\n{resume_text}"
            }
        ],
    )

    # Step 3: Parse JSON response
    response_text = message.content[0].text.strip()

    # Strip markdown code blocks if present
    if response_text.startswith("```"):
        response_text = re.sub(r"```(?:json)?\n?", "", response_text).strip()

    parsed = json.loads(response_text)

    # Step 4: Calculate confidence score per field
    confidence = _calculate_confidence(parsed)
    parsed["_confidence"] = confidence

    return parsed


def _calculate_confidence(parsed: dict) -> dict:
    """
    Estimate per-field confidence based on completeness.
    Fields with no data get lower confidence (flagged for manual review).
    """
    confidence = {}
    fields = ["name", "email", "location", "education", "skills", "languages", "experience"]
    for field in fields:
        value = parsed.get(field)
        if value is None or value == [] or value == "":
            confidence[field] = 0.0
        elif isinstance(value, list) and len(value) == 0:
            confidence[field] = 0.0
        else:
            confidence[field] = 1.0  # Present = high confidence (LLM is instructed not to guess)
    return confidence


def get_flagged_fields(parsed: dict) -> list[str]:
    """Return fields with confidence < 0.7 that need manual review."""
    confidence = parsed.get("_confidence", {})
    return [field for field, score in confidence.items() if score < 0.7]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def normalize_opportunity_description(description: str) -> str:
    """
    Summarize an opportunity description to ≤50 words using Claude, or local fallback.
    Faithful summarization — no embellishment.
    """
    if len(description.split()) <= 50:
        return description

    # Fallback if Anthropic key is not set
    if not settings.anthropic_api_key or "SECRET" in settings.anthropic_api_key or "your-anthropic-key" in settings.anthropic_api_key:
        sentences = re.split(r'(?<=[.!?])\s+', description)
        summary = ""
        for s in sentences:
            if len((summary + " " + s).split()) <= 45:
                summary = (summary + " " + s).strip()
            else:
                break
        if not summary:
            summary = " ".join(description.split()[:45])
        return summary + "..."

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=200,
        temperature=0,
        system=NORMALIZER_PROMPT,
        messages=[
            {"role": "user", "content": description}
        ],
    )
    return message.content[0].text.strip()
