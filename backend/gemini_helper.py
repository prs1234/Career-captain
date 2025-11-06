
import os
import google.generativeai as genai

# ==============================
# ✅ Configure Gemini API
# ==============================
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE"))

MODEL_NAME = "gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_NAME)


# ==============================
# 🎯 Generate Interview Questions
# ==============================
def generate_interview_questions(job: dict, num_questions: int = 5) -> list:
    """
    Generate relevant technical and behavioral interview questions for a job posting.
    """
    job_desc = (
        f"Job Title: {job.get('title')}\n"
        f"Company: {job.get('company')}\n"
        f"Location: {job.get('location')}\n"
        f"Skills Required: {', '.join(job.get('skills', []))}\n"
        f"Matched Skills: {', '.join(job.get('matched', []))}\n"
        f"Missing Skills: {', '.join(job.get('missing', []))}\n"
    )

    prompt = f"""
    You are an expert technical interviewer.
    Based on the following job profile, generate {num_questions} relevant interview questions.
    Include both conceptual and practical questions.

    {job_desc}
    """

    try:
        response = model.generate_content(prompt)
        questions_text = response.text.strip()
        questions = [q.strip("1234567890. ") for q in questions_text.split("\n") if q.strip()]
        return questions[:num_questions]
    except Exception as e:
        return [f"⚠ Error generating questions: {e}"]


# ==============================
# 🧠 Generate AI Answer
# ==============================
def summarize_skills(matched, missing, job_title):
    """
    Summarize matched & missing skills for a clear report using Gemini.
    """
    prompt = f"""
    You are an AI career analyst.
    The candidate applied for: {job_title}.

    ✅ Matched Skills: {', '.join(matched)}
    ❌ Missing Skills: {', '.join(missing)}

    Summarize:
    1. A short overview (2–3 lines) of how well the candidate fits.
    2. Which areas to improve (based on missing skills).
    3. Suggest specific online resources or platforms for upskilling (Coursera, Kaggle, etc.).
    Keep it concise and structured.
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠ Error summarizing skills: {e}"
def generate_answer(question: str) -> str:
    """
    Generate a structured interview-style answer to a question.
    """
    prompt = f"""
    You are an expert interviewer assistant.
    Provide a clear, structured, and confident interview answer to the following question:

    {question}
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠ Error generating answer: {e}"


# ==============================
# 📧 Generate Cold Email
# ==============================
def generate_cold_email(resume_path: str, job_title: str, company: str, skills: list) -> str:
    """
    Generate a personalized cold email for a job application.
    """
    prompt = f"""
    You are an AI career assistant.
    Write a short, personalized cold email to apply for the role of "{job_title}" at {company}.
    The candidate’s resume is available at: {resume_path}.
    Highlight relevant skills: {', '.join(skills)}.
    Keep it professional, concise (under 150 words), and end with a polite call to action.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠ Error generating cold email: {e}"


# ==============================
# 📘 Suggest Skill Improvements
# ==============================
def suggest_skill_improvements(missing_skills: list) -> str:
    """
    Suggest how to improve missing skills and recommend study materials.
    """
    if not missing_skills:
        return "🎉 Great job! You already have all the required skills."

    prompt = f"""
    You are an AI career mentor helping a candidate improve for job readiness.
    The candidate is missing the following skills: {', '.join(missing_skills)}.

    For each skill:
    1. Explain briefly why it is important for AI/ML/software development roles.
    2. Suggest 2–3 top resources (websites, courses, or YouTube channels) to learn it.
    3. Provide a short roadmap of how to master it.

    Present it clearly in bullet points with each skill as a separate section.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠ Error suggesting skill improvements: {e}"
