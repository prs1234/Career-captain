

import re
import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# ================================
# Load Hugging Face Skill Extraction Model (with fallback)
# ================================
try:
    MODEL_NAME = "AI4Bharat/SkillNER-BERT"  # public fine-tuned for skills
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)
    print("✅ Loaded fine-tuned SkillNER-BERT model.")
except Exception as e:
    print(f"⚠️ SkillNER model failed to load: {e}")
    print("➡️ Falling back to general-purpose NER model (dslim/bert-base-NER).")
    MODEL_NAME = "dslim/bert-base-NER"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)

ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

# ================================
# Predefined skill dictionary (fallback support)
# ================================
SKILLS_DICT = [
    "Python", "Java", "C++", "SQL", "JavaScript", "HTML", "CSS",
    "Machine Learning", "Deep Learning", "Data Science", "NLP",
    "Django", "Flask", "React", "Node.js", "AWS", "Azure", "GCP",
    "Docker", "Kubernetes", "TensorFlow", "PyTorch", "Spark",
    "Hadoop", "Power BI", "Tableau", "Git", "MLOps", "FastAPI"
]

# ================================
# Helper: Clean text
# ================================
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text

# ================================
# Extract skills using hybrid NER + dictionary
# ================================
def extract_skills(text: str) -> list:
    if not text:
        return []
    try:
        ner_results = ner_pipeline(text[:2000])  # limit text length for performance
        ner_skills = [
            r["word"].replace("##", "").strip()
            for r in ner_results if r["entity_group"] in ["MISC", "ORG", "SKILL"]
        ]
    except Exception as e:
        print(f"⚠️ NER extraction failed: {e}")
        ner_skills = []

    # Fallback dictionary matching
    dict_skills = [s for s in SKILLS_DICT if s.lower() in text.lower()]

    # Merge & deduplicate
    combined = list(set([s.title() for s in ner_skills + dict_skills]))
    return combined

# ================================
# Extract contact info (email, phone)
# ================================
def extract_contact_info(text: str) -> dict:
    email = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", text)
    phone = re.findall(r"\+?\d[\d\s-]{8,}\d", text)
    return {"email": email[0] if email else None, "phone": phone[0] if phone else None}

# ================================
# Parse resume from PDF
# ================================
def parse_resume(file_path: str) -> dict:
    pdf = fitz.open(file_path)
    text = " ".join(page.get_text("text") for page in pdf)
    pdf.close()
    text = clean_text(text)
    skills = extract_skills(text)
    contact = extract_contact_info(text)

    return {
        "text": text,
        "skills": skills,
        "email": contact["email"],
        "phone": contact["phone"]
    }

# ================================
# Parse job posting text or from URL
# ================================
def parse_job_posting_from_url(url: str) -> dict:
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Job Posting"
        return {"title": title, "text": clean_text(text), "skills": extract_skills(text)}
    except Exception as e:
        print(f"⚠️ Failed to parse job URL {url}: {e}")
        return {"title": "Unknown", "text": "", "skills": []}

# ================================
# Match resume to job based on extracted skills
# ================================
def match_resume_to_job(resume_data: dict, job_data: dict) -> dict:
    resume_skills = set([s.lower() for s in resume_data.get("skills", [])])
    job_skills = set([s.lower() for s in job_data.get("skills", [])])

    matched = [s.title() for s in resume_skills & job_skills]
    missing = [s.title() for s in job_skills - resume_skills]

    score = (len(matched) / len(job_skills) * 100) if job_skills else 0

    return {
        "score": round(score, 2),
        "matched_skills": matched,
        "missing_skills": missing
    }

# ================================
# Convert Apify job object to comparable dict
# ================================
def apify_job_to_skill_dict(job: dict) -> dict:
    title = job.get("Job Title", "No title provided")
    description = job.get("Description", "")
    skills_tags = job.get("Skills/Tags", "")
    text = clean_text(f"{title} {description} {skills_tags}")
    return {"title": title, "text": text, "skills": extract_skills(text)}
