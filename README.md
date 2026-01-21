### Career Captain – AI Resume Job Matcher & Interview Coach
Created by: Prashant Sahu
Email: prs1234hant@gmail.com

Career Captain is an AI-powered career intelligence platform that analyzes resumes, matches them with live job postings, and generates personalized insights such as missing skills, learning pathways, recruiter cold emails, and interview question–answer sets.

The system is designed with a strong AI/ML backend using Python, LLMs, vector search, and NLP pipelines, combined with a modern full-stack interface for real-world usability.

### Project Overview

Career Captain focuses on automating the job search and interview preparation process using large language models and intelligent skill-matching algorithms.

### Key capabilities include:

Resume parsing and skill extraction

Live job matching using external job data

AI-generated summaries and recommendations

Interview question and answer generation

Learning roadmap suggestions

Recruiter cold email drafting

Secure user authentication and history tracking

The backend is built for scalable AI processing, while the frontend delivers a smooth and interactive user experience.

### Core AI & Backend Capabilities

Resume Intelligence
Automatically extracts skills, experience, and keywords from uploaded resumes using NLP techniques.

Job Matching Engine
Fetches real-time job listings from Naukri via Apify and matches them with candidate profiles based on skill similarity.

Skill Gap Analysis
Identifies missing skills for each job role and highlights strengths and weaknesses.

LLM-Powered Summaries
Uses Google Gemini 2.5 Flash API to generate professional summaries and insights.

Interview Preparation
Generates role-specific interview questions and high-quality answers using LLMs.

Learning Path Suggestions
Recommends structured learning paths for missing skills.

Cold Email Generator
Creates professional recruiter outreach emails based on job role and resume data.

User Management
Implements secure authentication with hashed passwords and maintains user search history in SQLite.

### Technology Stack

Frontend
React 18, Tailwind CSS, Framer Motion, Vite, Lucide React

Backend
Python 3.10+, Streamlit, SQLite, Apify Client, Google Gemini API

AI / ML
Google Gemini 2.5 Flash, NLP Pipelines, Skill Matching Algorithms

Databases
SQLite, FAISS, Qdrant, ChromaDB

DevOps & Tools
Git, GitHub, Docker, Linux, Streamlit Cloud, Vercel, Render

Authentication
Custom SHA-256 password hashing system

### System Architecture

Backend (Python + Streamlit)
Handles AI logic, resume parsing, job matching, database management, and API communication.

Main Engine (main.py)

Fetches job data using Apify

Matches resumes with job listings

Calls Gemini API for summaries and Q&A

Stores results in SQLite

Frontend (React + Tailwind)
Provides a responsive UI for login, job search, results visualization, and AI actions.

### Project Structure

### Backend
auth.py – User authentication
database.py – SQLite management
resume_job_parser.py – Resume parsing and skill extraction
gemini_helper.py – Gemini API integration
main.py – Core AI workflow

### Frontend
CareerCaptain.jsx – Main interface
Navbar.jsx – Navigation bar
LoginForm.jsx – Authentication UI
JobCard.jsx – Job result cards
api.js – Backend API calls
App.js – Root component

### API Endpoints

POST /api/match
Uploads resume and returns matched job results

POST /api/questions
Generates interview questions

POST /api/answer
Generates AI answers

POST /api/cold_email
Creates recruiter email drafts

POST /api/suggest
Suggests learning paths

POST /api/summarize
Summarizes matched vs missing skills

### Database Schema

Database: career_captain.db

### Installation & Setup

Backend Setup

Clone the repository
git clone https://github.com/prashantsahu-ai/career-captain.git

cd career-captain/backend

Create virtual environment
python -m venv career

Activate environment
career\Scripts\activate (Windows)
source career/bin/activate (Linux/Mac)

Install dependencies
pip install -r requirements.txt

Run the backend
streamlit run front.py

Frontend Setup

cd ../frontend
npm install
npm run dev

Open in browser
http://localhost:5173

UI Overview

Login / Signup
Secure user authentication

Dashboard
Resume upload, job search, filters

Results Page
Skill match visualization, AI insights, action buttons

Interview Panel
Expandable interview questions and answers

Cold Email Generator
Role-based recruiter email drafts

### Future Enhancements

Google OAuth login
AI Career Mentor chatbot
Job alert notifications
LinkedIn and Indeed API integration
Skill trend analytics dashboard

### License

This project is licensed under the MIT License.
You are free to use, modify, and distribute it for learning or professional purposes.

### Author

Prashant Sahu
AI Engineer and Full-Stack Developer
Email: prs1234hant@gmail.com

### Focused on building production-grade AI systems that solve real-world problems using LLMs, NLP, and scalable backend architectures.


### References

Kim, Y. (2014). Convolutional Neural Networks for Sentence Classification. EMNLP.

Collobert, R., et al. (2011). Natural Language Processing (Almost) from Scratch. JMLR.

Mikolov, T., et al. (2013). Distributed Representations of Words and Phrases. NeurIPS.

Reimers, N., & Gurevych, I. (2019). Sentence-BERT. EMNLP.

Radford, A., et al. (2018). Improving Language Understanding by Generative Pre-Training. OpenAI.

Brown, T., et al. (2020). Language Models are Few-Shot Learners. NeurIPS.

Lewis, P., et al. (2020). Retrieval-Augmented Generation. NeurIPS.

Leskovec, J., Rajaraman, A., & Ullman, J.D. (2014). Mining of Massive Datasets. Cambridge Univ. Press.

Grover, A., & Leskovec, J. (2016). node2vec: Scalable Feature Learning for Networks. KDD.

Li, V. O. K., et al. (2020). Question Generation from Text — A Review. arXiv.
