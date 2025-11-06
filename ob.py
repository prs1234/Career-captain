# streamlit_app.py
import streamlit as st
import threading
import time
import json
import os
import base64
import datetime
import pymysql
from pprint import pprint

# Import your parser + matching modules (adjust paths if needed)
# parse_resume should return {'text':..., 'skills': [...], 'name':..., 'email':..., 'phone':..., 'no_of_pages': int}
from backend.resume_job_parser import parse_resume, apify_job_to_skill_dict, SKILLS_DICT  # your existing module
from main import match_resume_with_jobs  # if you have this orchestrator; else we call match_resume_to_job directly
from backend.resume_job_parser import extract_skills  # if available (the hybrid NER + dict)

# -------------------------
# CONFIG — edit as needed
# -------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Prs5/10/2002",
    "db": "sra"
}
APIFY_API_KEY = "YOUR_APIFY_KEY"  # optional
USE_OFFLINE_JOBS = True  # Set to False for live Apify scraping
JOBS_CACHE_FILE = "data/jobs_cache.json"

# -------------------------
# DB Helpers
# -------------------------
def get_db_conn():
    conn = pymysql.connect(host=DB_CONFIG["host"], user=DB_CONFIG["user"],
                           password=DB_CONFIG["password"], cursorclass=pymysql.cursors.DictCursor)
    return conn

def ensure_db_tables():
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS sra;")
            cur.execute("USE sra;")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT NOT NULL AUTO_INCREMENT,
                username VARCHAR(100) UNIQUE,
                password VARCHAR(200),
                name VARCHAR(200),
                email VARCHAR(200),
                created_at VARCHAR(50),
                PRIMARY KEY (id)
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INT NOT NULL AUTO_INCREMENT,
                user_id INT,
                file_path VARCHAR(500),
                parsed_text LONGTEXT,
                skills TEXT,
                projects TEXT,
                internships TEXT,
                pages INT,
                created_at VARCHAR(50),
                PRIMARY KEY (id)
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS job_matches (
                id INT NOT NULL AUTO_INCREMENT,
                user_id INT,
                job_title VARCHAR(500),
                company VARCHAR(300),
                job_skills TEXT,
                matched_skills TEXT,
                missing_skills TEXT,
                job_link VARCHAR(1000),
                score FLOAT,
                matched_at VARCHAR(50),
                PRIMARY KEY (id)
            );""")
        conn.commit()
    finally:
        conn.close()

# -------------------------
# Skill extraction helpers
# -------------------------
# Try to extract skills from sections (projects, internships, experience) using simple heuristics
PROJECT_SECTION_HEADERS = ["project", "projects", "academic project", "final year project"]
INTERNSHIP_HEADERS = ["intern", "internship", "work experience", "experience"]

def extract_section_text(full_text: str, headers):
    """Return concatenated text for lines under headings (simple heuristic)."""
    text = full_text or ""
    lines = text.splitlines()
    out = []
    capture = False
    for line in lines:
        low = line.strip().lower()
        # start capture on header
        if any(h in low for h in headers):
            capture = True
            out.append(line)
            continue
        # stop capture if we hit another all-caps section-like line or blank line followed by next header
        if capture:
            if low.strip() == "":
                # small heuristic: break after 5 blanks or a big gap
                out.append(line)
                continue
            # stop if we hit another header word
            if any(h in low for h in ["education", "skills", "certification", "achievements", "personal"]):
                break
            out.append(line)
    return "\n".join(out).strip()

def extract_skills_from_text(full_text):
    """Hybrid: SKILL_DICT matches + simple tokenization to find tech names + lowercase normalized."""
    if not full_text:
        return []
    found = set()
    low = full_text.lower()
    # keyword dictionary match (SKILLS_DICT from your resume parser)
    try:
        for s in SKILLS_DICT:
            if s.lower() in low:
                found.add(s.lower())
    except Exception:
        pass
    # simple regex-like detection for common tech tokens (e.g., "reactjs", "node.js", "c++", "tensorflow")
    tokens = set([t.strip(".,()[]") for t in low.replace("/", " ").replace("-", " ").split()])
    for tok in tokens:
        if len(tok) > 1 and tok.isalnum():
            # if token matches known tech substring
            for s in SKILLS_DICT:
                if tok in s.lower():
                    found.add(s.lower())
    return sorted(found)

# -------------------------
# Jobs fetchers
# -------------------------
def load_cached_jobs():
    if os.path.exists(JOBS_CACHE_FILE):
        with open(JOBS_CACHE_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return []

def save_cached_jobs(jobs):
    os.makedirs(os.path.dirname(JOBS_CACHE_FILE) or ".", exist_ok=True)
    with open(JOBS_CACHE_FILE, "w", encoding="utf-8") as fh:
        json.dump(jobs, fh, ensure_ascii=False, indent=2)

def fetch_jobs_offline(keywords, location, max_items=10):
    # quick dummy job set with skills
    dummy = [
        {
            "Job Title": "AI Engineer",
            "Company": "TechCorp",
            "Location": location,
            "Skills/Tags": "Python, Machine Learning, Deep Learning, PyTorch, AWS",
            "Job URL": "https://example.com/job/ai-1"
        },
        {
            "Job Title": "Digital Marketing Executive",
            "Company": "AdWorks",
            "Location": location,
            "Skills/Tags": "Digital Marketing, Google Ads, SEO, Facebook Ads",
            "Job URL": "https://example.com/job/dm-1"
        },
        {
            "Job Title": "Data Scientist",
            "Company": "DataLabs",
            "Location": location,
            "Skills/Tags": "Python, SQL, Pandas, Scikit-learn, Tableau",
            "Job URL": "https://example.com/job/ds-1"
        }
    ]
    out = dummy[:max_items]
    save_cached_jobs(out)
    return out

def fetch_jobs_live_apify(keywords, location, max_items=10):
    # This will run the Apify actor synchronously (can be slow).
    # For responsive UI we run it in background thread (see worker below).
    # Implementation left as a placeholder — use apify_client to start actor and fetch dataset.
    from apify_client import ApifyClient
    client = ApifyClient(APIFY_API_KEY)
    actor_id = "codemaverick/naukri-job-scraper-latest"
    input_data = {"keywords": keywords, "location": location, "maxItems": max_items}
    run = client.actor(actor_id).call(run_input=input_data)
    dataset_id = run["defaultDatasetId"]
    items = client.dataset(dataset_id).list_items().items
    save_cached_jobs(items)
    return items[:max_items]

# -------------------------
# Background worker for live scraping & matching
# -------------------------
def background_scrape_and_match(keywords, location, max_items, user_id, resume_skills):
    """
    Background thread: fetch jobs (live or offline), filter by keywords,
    perform matching, store matches in DB and push into session_state
    """
    st.session_state["scrape_status"] = "running"
    try:
        if USE_OFFLINE_JOBS:
            jobs = fetch_jobs_offline(keywords, location, max_items)
        else:
            jobs = fetch_jobs_live_apify(keywords, location, max_items)
    except Exception as e:
        st.session_state["scrape_status"] = f"error: {str(e)}"
        return

    # Filter jobs by keywords: keep only those that contain any of the keywords
    kw_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    filtered = []
    for j in jobs:
        job_text = (j.get("Job Title", "") + " " + j.get("Description", "") + " " + j.get("Skills/Tags", "")).lower()
        if not kw_list:
            filtered.append(j)
            continue
        # keep if any keyword present in job_text
        if any(kw in job_text for kw in kw_list):
            filtered.append(j)

    # match each job with resume skills (simple set overlap)
    results = []
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("USE sra;")
            for job in filtered:
                job_dict = apify_job_to_skill_dict(job)
                job_skills = job_dict.get("skills", [])
                resume_set = set([s.lower() for s in resume_skills])
                job_set = set([s.lower() for s in job_skills])
                matched = sorted(list(resume_set & job_set))
                missing = sorted(list(job_set - resume_set))
                score = (len(matched) / len(job_set) * 100) if job_set else 0.0

                # store match in DB
                now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute("""
                    INSERT INTO job_matches (user_id, job_title, company, job_skills, matched_skills, missing_skills, job_link, score, matched_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    user_id,
                    job.get("Job Title") or "No title",
                    job.get("Company") or "Unknown",
                    ",".join(job_skills),
                    ",".join(matched),
                    ",".join(missing),
                    job.get("Job URL") or job.get("Link") or "",
                    float(score),
                    now
                ))
                results.append({
                    "title": job.get("Job Title"),
                    "company": job.get("Company"),
                    "location": job.get("Location"),
                    "skills": job_skills,
                    "matched": matched,
                    "missing": missing,
                    "score": round(score, 2),
                    "link": job.get("Job URL")
                })
            conn.commit()
    finally:
        conn.close()

    # set results to session state so Streamlit UI can consume
    st.session_state["job_results"] = sorted(results, key=lambda x: x["score"], reverse=True)
    st.session_state["scrape_status"] = "done"

# -------------------------
# App UI
# -------------------------
def app():
    st.set_page_config(page_title="Career Captain - Async Matcher", layout="wide")
    st.title("🚀 Career Captain (Async Job Matcher)")

    ensure_db_tables()

    # Session defaults
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "job_results" not in st.session_state:
        st.session_state.job_results = []
    if "scrape_status" not in st.session_state:
        st.session_state.scrape_status = "idle"

    # Sidebar: login / register
    with st.sidebar:
        st.header("User Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            conn = get_db_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute("USE sra;")
                    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
                    row = cur.fetchone()
                    if row:
                        st.session_state.logged_in = True
                        st.session_state.user = row
                        st.success(f"Logged in as {row.get('username')}")
                    else:
                        st.error("Invalid username or password")
            finally:
                conn.close()

        st.markdown("---")
        st.subheader("New user? Register")
        new_user = st.text_input("New username", key="reg_user")
        new_pass = st.text_input("New password", type="password", key="reg_pass")
        new_name = st.text_input("Full name", key="reg_name")
        new_email = st.text_input("Email", key="reg_email")
        if st.button("Register"):
            conn = get_db_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute("USE sra;")
                    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    cur.execute("INSERT IGNORE INTO users (username,password,name,email,created_at) VALUES (%s,%s,%s,%s,%s)",
                                (new_user, new_pass, new_name, new_email, now))
                    conn.commit()
                st.success("Registration complete. Now login.")
            finally:
                conn.close()

    # Main layout: left upload + controls, right results
    left, right = st.columns([1, 2])
    with left:
        st.subheader("Upload Resume (PDF)")
        uploaded_file = st.file_uploader("Choose PDF", type=["pdf"])
        if uploaded_file:
            save_path = os.path.join("Uploaded_Resumes", uploaded_file.name)
            os.makedirs("Uploaded_Resumes", exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Saved resume to {save_path}")
            # parse it now
            try:
                resume_data = parse_resume(save_path)  # your parser
            except Exception as e:
                st.error(f"Parsing error: {e}")
                resume_data = {}

            # ensure some fields
            parsed_text = resume_data.get("text", "")
            parsed_skills = resume_data.get("skills", []) or extract_skills_from_text(parsed_text)
            # extract projects and internships heuristically
            projects_txt = extract_section_text(parsed_text, PROJECT_SECTION_HEADERS)
            internships_txt = extract_section_text(parsed_text, INTERNSHIP_HEADERS)
            projects_skills = extract_skills_from_text(projects_txt)
            intern_skills = extract_skills_from_text(internships_txt)

            st.markdown("**Extracted skills (full resume)**")
            st.write(parsed_skills)
            st.markdown("**Skills from Projects**")
            st.write(projects_skills)
            st.markdown("**Skills from Internships / Experience**")
            st.write(intern_skills)

            # Save resume metadata to DB (associate to user if logged in)
            if st.button("Save Resume to DB"):
                conn = get_db_conn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("USE sra;")
                        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        user_id = st.session_state.user["id"] if st.session_state.logged_in else None
                        cur.execute("""
                            INSERT INTO resumes (user_id, file_path, parsed_text, skills, projects, internships, pages, created_at)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        """, (
                            user_id,
                            save_path,
                            parsed_text,
                            ",".join(parsed_skills),
                            projects_txt,
                            internships_txt,
                            resume_data.get("no_of_pages", 1),
                            now
                        ))
                        conn.commit()
                        st.success("Resume saved.")
                finally:
                    conn.close()

            # stash parsed resume in session for matching
            st.session_state["current_resume"] = {
                "path": save_path,
                "text": parsed_text,
                "skills": parsed_skills,
                "projects_skills": projects_skills,
                "intern_skills": intern_skills,
                "pages": resume_data.get("no_of_pages", 1)
            }

        st.markdown("---")
        st.subheader("Job Search Controls")
        keywords = st.text_input("Job keywords (comma-separated)", "machine learning, data scientist")
        location = st.text_input("Location", "Chennai, India")
        max_items = st.slider("Max jobs to fetch", 1, 50, 10)

        # Get Jobs button: disabled until logged in & resume uploaded
        can_get_jobs = st.session_state.logged_in and ("current_resume" in st.session_state)
        if not can_get_jobs:
            st.button("Get Jobs (login + upload resume first)", disabled=True)
        else:
            if st.button("Get Jobs"):
                # launch background thread
                st.session_state.scrape_status = "queued"
                user_id = st.session_state.user["id"]
                resume_skills = st.session_state["current_resume"]["skills"]
                t = threading.Thread(target=background_scrape_and_match,
                                     args=(keywords, location, max_items, user_id, resume_skills),
                                     daemon=True)
                t.start()
                st.success("Started background job: fetching & matching. Check job results panel on the right.")

        st.markdown("**Scrape status:** " + str(st.session_state.scrape_status))
        st.markdown("---")
        st.markdown("⚡ Use offline mode for fast testing (no API keys). Toggle `USE_OFFLINE_JOBS` in config.")

    with right:
        st.subheader("Job Results")
        if st.session_state.get("job_results"):
            for idx, r in enumerate(st.session_state["job_results"]):
                with st.expander(f"{idx+1}. {r['title']} @ {r['company']} ({r['score']}%)"):
                    st.write("Location:", r.get("location"))
                    st.write("Job Skills:", r.get("skills"))
                    st.write("Matched:", r.get("matched"))
                    st.write("Missing:", r.get("missing"))
                    if r.get("link"):
                        st.markdown(f"[Open Job]({r.get('link')})", unsafe_allow_html=True)
        else:
            st.info("No job results yet. Click Get Jobs to start scraping & matching (or load cached jobs).")

        st.markdown("---")
        st.subheader("Cached Jobs (sample)")
        cached = load_cached_jobs()
        st.write(cached[:5])

if __name__ == "__main__":
    app()
