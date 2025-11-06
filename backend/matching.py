import spacy

# Load your trained spaCy skill NER model
model_path = r"D:\L&T Projects\Career Captain\backend\it_skill_model"
# ================================
nlp = spacy.load(model_path)

def extract_skills(text):
    """Use spaCy NER to extract skills from text."""
    doc = nlp(text)
    skills = [ent.text.lower().strip() for ent in doc.ents if ent.label_ == "SKILL"]
    return set(skills)

def match_resume_to_job(resume_text, job_data):
    """
    Match skills extracted from resume with skills in job posting.
    
    Args:
        resume_text (str): Raw text from resume.
        job_data (dict): {'skills': list of job skills}
    
    Returns:
        dict: {'score', 'matched_skills', 'missing_skills'}
    """
    # Extract skills from resume using spaCy
    resume_skills = extract_skills(resume_text)

    # Prepare job skills
    job_skills = set([s.lower().strip() for s in job_data.get("skills", [])])

    # Matched and missing
    matched_skills = resume_skills.intersection(job_skills)
    missing_skills = job_skills - matched_skills

    score = round((len(matched_skills) / len(job_skills) * 100), 2) if job_skills else 0

    return {
        "score": score,
        "matched_skills": list(matched_skills),
        "missing_skills": list(missing_skills)
    }
