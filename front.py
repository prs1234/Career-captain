import streamlit as st
from main import match_resume_with_jobs
from backend.gemini_helper import (
    generate_interview_questions,
    generate_answer,
    generate_cold_email,
    suggest_skill_improvements,
    summarize_skills
)
from backend.auth import signup_user, login_user
from backend.database import init_db, get_db

# ================================
# App Configuration
# ================================
st.set_page_config(page_title="🚀 Career Captain - Resume Job Matcher", layout="wide")
st.title("🧠 Career Captain – AI Resume Job Matcher & Interview Coach")

# Initialize DB
init_db()

# ================================
# Initialize Session State Safely
# ================================
for key, default in {
    "user": None,
    "questions": {},
    "answers": {},
    "job_results": [],
    "emails": {},
    "skill_suggestions": {},
    "skill_summary": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ================================
# Authentication Section
# ================================
st.sidebar.header("🔒 Authentication")
auth_mode = st.sidebar.radio("Select Mode", ["Login", "Signup"])

email = st.sidebar.text_input("📧 Email")
password = st.sidebar.text_input("🔑 Password", type="password")

if auth_mode == "Signup":
    if st.sidebar.button("Create Account"):
        ok, msg = signup_user(email, password)
        st.sidebar.success(msg) if ok else st.sidebar.error(msg)

elif auth_mode == "Login":
    if st.sidebar.button("Login"):
        ok, msg = login_user(email, password)
        if ok:
            st.session_state["user"] = email
            st.sidebar.success(f"✅ {msg}")
        else:
            st.sidebar.error(msg)

# ================================
# Main Interface (After Login)
# ================================
if st.session_state["user"]:
    st.success(f"Welcome, {st.session_state['user']} 👋")

    col1, col2 = st.columns([1, 2])

    # ---------- LEFT PANEL ----------
    with col1:
        st.header("📄 Upload Resume")
        uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

        keywords = st.text_input("🔍 Job Keywords", "AI Software Engineer, Machine Learning")
        location = st.text_input("📍 Job Location", "Chennai, India")
        max_items = st.slider("📌 Number of Jobs to Fetch", 1, 20, 5)

        if st.button("🚀 Find Matching Jobs"):
            if uploaded_file:
                resume_path = "data/temp_resume.pdf"
                with open(resume_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                with st.spinner("⏳ Analyzing your resume and fetching job listings..."):
                    results = match_resume_with_jobs(resume_path, keywords, location, max_items, st.session_state["user"])

                if results:
                    st.session_state["job_results"] = results
                    st.success("✅ Job matching completed successfully!")
                else:
                    st.warning("⚠ No matching jobs found. Try adjusting your keywords or location.")
            else:
                st.error("⚠ Please upload your resume before searching.")

    # ---------- RIGHT PANEL ----------
    with col2:
        st.header("💼 Job Match Results")

        if not st.session_state["job_results"]:
            st.info("⬅ Upload your resume and click 'Find Matching Jobs' to see matches here.")
        else:
            for idx, r in enumerate(st.session_state["job_results"]):
                with st.expander(f"{r['title']} at {r['company']} ({r['score']}%)"):
                    st.subheader("📊 Skill Comparison")
                    st.write(f"🌐 **Job Skills:** {', '.join(r['skills'])}")
                    st.progress(int(r["score"]))
                    st.write(f"✅ **Matched Skills:** {', '.join(r['matched']) or 'None'}")
                    st.write(f"❌ **Missing Skills:** {', '.join(r['missing']) or 'None'}")

                    # ---- Skill Summary ----
                    if st.button(f"🧾 Summarize Skills", key=f"sum_{idx}"):
                        summary = summarize_skills(r["title"], r["matched"], r["missing"])
                        st.session_state["skill_summary"] = summary
                        st.info(summary)

                    # ---- Learning Path Suggestions ----
                    if st.button(f"📘 Suggest Learning Path", key=f"sugg_{idx}"):
                        st.session_state["skill_suggestions"][idx] = suggest_skill_improvements(r["missing"])
                    if idx in st.session_state["skill_suggestions"]:
                        st.info(st.session_state["skill_suggestions"][idx])

                    st.markdown("---")

                    # ---- Interview Questions ----
                    if st.button(f"🎯 Generate Interview Questions", key=f"gen_q_{idx}"):
                        st.session_state["questions"][idx] = generate_interview_questions(r)
                    if idx in st.session_state["questions"]:
                        for q_idx, q in enumerate(st.session_state["questions"][idx]):
                            with st.expander(f"💬 Q{q_idx + 1}: {q}"):
                                if st.button(f"💡 Generate Answer", key=f"ans_{idx}_{q_idx}"):
                                    st.session_state["answers"][(idx, q_idx)] = generate_answer(q)
                                if (idx, q_idx) in st.session_state["answers"]:
                                    st.markdown(f"**Answer:** {st.session_state['answers'][(idx, q_idx)]}")

                    st.markdown("---")

                    # ---- Cold Email ----
                    if st.button(f"📧 Generate Cold Email for {r['company']}", key=f"cold_{idx}"):
                        st.session_state["emails"][idx] = generate_cold_email(
                            "data/temp_resume.pdf", r["title"], r["company"], r["skills"]
                        )
                    if idx in st.session_state["emails"]:
                        st.success("✅ Cold Email Generated:")
                        st.markdown(st.session_state["emails"][idx])

else:
    st.info("🔐 Please log in or sign up to access Career Captain.")
