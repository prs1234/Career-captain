
import os
import sqlite3
import hashlib
from datetime import datetime
from apify_client import ApifyClient
import google.generativeai as genai
from backend.resume_job_parser import parse_resume, apify_job_to_skill_dict, match_resume_to_job

# ================================
# CONFIGURATION 
# ================================
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "YOUR_APIFY_TOKEN_HERE")
APIFY_ACTOR = "apify/linkedin-jobs-scraper"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
genai.configure(api_key=GEMINI_API_KEY)


# ================================
# DATABASE INITIALIZATION
# ================================
def init_db():
    conn = sqlite3.connect("career_captain.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            keywords TEXT,
            location TEXT,
            timestamp TEXT,
            top_job TEXT,
            score INTEGER
        )
    """)
    conn.commit()
    conn.close()


# ================================
# AUTH HELPERS
# ================================
def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(input_password: str, stored_hash: str) -> bool:
    return hash_password(input_password) == stored_hash


# ================================
# GEMINI SUMMARIZER
# ================================
def summarize_skills(job_title, matched_skills, missing_skills):
    """Summarize how well the candidate fits a given role."""
    prompt = f"""
    You are a career analyst. Evaluate the candidate's fit for the role '{job_title}'.
    Matched skills: {', '.join(matched_skills)}.
    Missing skills: {', '.join(missing_skills)}.
    Write a short summary (3–5 lines) highlighting key strengths and skill improvement suggestions.
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(response, "text") else "No summary available."
    except Exception as e:
        return f"⚠️ Gemini Summary Error: {e}"


# ================================
# INTERVIEW QUESTIONS GENERATOR
# ================================
def generate_questions(job_title, skills, matched, missing):
    prompt = f"""
    You are an interview coach. The candidate is applying for '{job_title}'.
    Job skills: {', '.join(skills)}.
    Candidate strengths: {', '.join(matched)}.
    Candidate weak areas: {', '.join(missing)}.

    Generate:
    • 5 interview questions likely to be asked.
    • 5 technical practice questions for improvement.
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(response, "text") else "⚠️ Could not generate questions."
    except Exception as e:
        return f"⚠️ Gemini Error: {e}"


# ================================
# FETCH JOBS (LinkedIn Scraper)
# ================================
def fetch_jobs(keywords, location, max_items=5):
    """Fetch jobs dynamically from LinkedIn using Apify."""
    client = ApifyClient(APIFY_TOKEN)
    try:
        run_input = {
            "queries": [f"{keywords} in {location}"],
            "maxResults": max_items,
        }

        run = client.actor(APIFY_ACTOR).call(run_input=run_input)
        dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        if not dataset_items:
            raise ValueError("No jobs found for given query.")

        return dataset_items[:max_items]

    except Exception as e:
        print(f"⚠️ Apify job fetch failed: {e}")
        # fallback data
        return [
            {
                "Job Title": "AI Engineer",
                "Company Name": "Techify Labs",
                "Location": "Bangalore, India",
                "Description": "We’re hiring an AI Engineer with ML, Python, and TensorFlow experience.",
                "Skills/Tags": "Python, TensorFlow, Machine Learning, Deep Learning",
                "Job URL": "https://www.linkedin.com/jobs/view/ai-engineer"
            },
            {
                "Job Title": "Data Scientist",
                "Company Name": "DataWiz Analytics",
                "Location": "Chennai, India",
                "Description": "Looking for a Data Scientist experienced in NLP, AWS, and Scikit-learn.",
                "Skills/Tags": "Python, NLP, AWS, Scikit-learn",
                "Job URL": "https://www.linkedin.com/jobs/view/data-scientist"
            },
        ]


# ================================
# MATCH RESUME WITH JOBS
# ================================
def match_resume_with_jobs(resume_path, keywords, location, max_items=5, username="guest"):
    """Parse resume, fetch jobs, and score alignment."""
    print("📄 Parsing resume...")
    resume_data = parse_resume(resume_path)

    print("🌐 Fetching job listings...")
    jobs = fetch_jobs(keywords, location, max_items)
    results = []

    for job in jobs:
        job_data = apify_job_to_skill_dict(job)
        match = match_resume_to_job(resume_data, job_data)

        skills_text = job.get("Skills/Tags") or job.get("skills") or ""
        skill_list = [s.strip() for s in skills_text.split(",") if s.strip()]

        summary = summarize_skills(
            job.get("Job Title", "Unknown"),
            match.get("matched_skills", []),
            match.get("missing_skills", []),
        )

        questions = generate_questions(
            job.get("Job Title", "Unknown"),
            skill_list,
            match.get("matched_skills", []),
            match.get("missing_skills", []),
        )

        result = {
            "title": job.get("Job Title", "Unknown Role"),
            "company": job.get("Company Name", "Unknown Company"),
            "location": job.get("Location", "Unknown Location"),
            "skills": skill_list or ["No skills found"],
            "score": match.get("score", 0),
            "matched": match.get("matched_skills", []),
            "missing": match.get("missing_skills", []),
            "link": job.get("Job URL", "No link available"),
            "summary": summary,
            "ai_questions": questions,
        }

        results.append(result)

    # Save top result in DB
    if results:
        conn = sqlite3.connect("career_captain.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_searches (username, keywords, location, timestamp, top_job, score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            username, keywords, location, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            results[0]["title"], results[0]["score"]
        ))
        conn.commit()
        conn.close()

    return sorted(results, key=lambda x: x["score"], reverse=True)


# ================================
# LOCAL TEST
# ================================
if __name__ == "__main__":
    print("🚀 Starting Career Captain Matching...")
    resume = "data/sample_resume.pdf"

    results = match_resume_with_jobs(
        resume,
        keywords="AI Software Engineer, Machine Learning",
        location="Chennai, India",
        max_items=5,
        username="Prashant"
    )

    from pprint import pprint
    print("\n📌 Top Job Matches:\n")
    for r in results:
        pprint(r)
        print("\n🧠 Gemini Summary:\n", r["summary"])
        print("\n🎤 AI Interview Questions:\n", r["ai_questions"])
        print("=" * 90)
