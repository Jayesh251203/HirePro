import streamlit as st
import pdfplumber
import fitz
import re
import streamlit as st
import pdfplumber
import fitz  
import re
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --------------------------------------------
# PDF extractors
# --------------------------------------------
def extract_text_pdfplumber(file_bytes):
    text = []
    with pdfplumber.open(file_bytes) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)

def extract_text_pymupdf(file_bytes):
    file_bytes.seek(0)
    text = []
    doc = fitz.open(stream=file_bytes.read(), filetype="pdf")
    for page in doc:
        text.append(page.get_text("text"))
    return "\n".join(text)

# Simple normalizer
def normalize_text(s):
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s)
    return s.strip()

SKILL_PROMPT = """
Extract ONLY technical skills from the resume text below.

Return output as STRICT JSON only:
{{
  "skills": ["python", "machine learning", "react", ...]
}}

Rules:
- Only include SKILLS (programming languages, frameworks, tools, ML skills, cloud, databases).
- DO NOT include achievements, sentences, job roles, or soft skills.
- Skills must be short tokens (1–3 words).
- Return ONLY JSON — no explanation.

Resume:
---
{resume}
---
"""
def skill_and_achievement_extractor(resume_text):
    prompt = SKILL_PROMPT.format(resume=resume_text)
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        out = response.text.strip()
        out = re.sub(r"^```json|```$", "", out).strip()

        try:
            data = json.loads(out)
            skills = data.get("skills", [])
            skills = [s.lower().strip() for s in skills if isinstance(s, str)]
            return skills
        except:
            return []
    except Exception as e:
        print("LLM error:", e)
        return []
    
def parse_jd(jd_text):
    if "," in jd_text:
        # comma separated skills
        return [s.strip().lower() for s in jd_text.split(",") if s.strip()]
    else:
        # full paragraph: send raw to LLM later
        return jd_text.strip()
user_prompt = """
Hey Gemini, you have a task.

I am providing you:
1. The candidate's extracted resume skills
2. The job description requirements

Your job:
Compare the resume skills with the job description and return a JSON object with this EXACT structure:

{{
  "mapped": [],
  "substitutes": [],
  "extras": [],
  "score": 0,
  "review": ""
}}

### Behaviour Rules:

1. **mapped**  
   - Direct matches between candidate skills and JD skills.

2. **substitutes**  
   - Cases where candidate doesn't have the exact JD skill,  
     but has a related/alternative skill that implies competence.  
   - Example: JD asks for “machine learning engineer” but resume shows “tensorflow”,  
     or JD says “cloud experience” but resume says “aws”.

3. **extras**  
   - Skills the candidate has that are NOT required by JD.

4. **score (1–100)**  
   - How well the candidate fits the job **based on your comparison**.

5. **review**  
   - A short 1–2 line professional summary of the candidate’s fit.

Return ONLY the JSON. No explanation outside JSON.

Here is the data:

Resume Skills:
{resume_skills}

Job Description:
{jd_text}
"""

def call_llm_for_matching(resume_skills, jd_input, user_prompt):
    """
    Sends resume skills + JD + your custom prompt to Gemini.
    """
    final_prompt = user_prompt.format(
        resume_skills=json.dumps(resume_skills, indent=2),
        jd_text=jd_input
    )

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(final_prompt)
        text = response.text.strip()
        text = re.sub(r"^```(json)?", "", text)
        text = re.sub(r"```$", "", text)
        return text
    except Exception as e:
        return f"LLM Error: {str(e)}"

# --------------------------------------------
# STREAMLIT UI
# --------------------------------------------
st.set_page_config(page_title="HirePro – Resume Text Extractor", layout="wide")
st.title("🔥 HirePro – PDF Resume Text Extractor (Only Parsing)")

uploaded = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

# -- SESSION STATE INIT --
if "skills" not in st.session_state:
    st.session_state.skills = []

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""


# ------------------------------------------------------------
# BUTTON 1: Extract Resume + Skills
# ------------------------------------------------------------
if st.button("Extract Resume Text"):
    if not uploaded:
        st.error("Please upload a resume.")
        st.stop()

    uploaded.seek(0)
    text1 = extract_text_pdfplumber(uploaded)

    uploaded.seek(0)
    text2 = extract_text_pymupdf(uploaded)

    resume_text = normalize_text(text1 + "\n" + text2)

    st.session_state.resume_text = resume_text
    st.session_state.skills = skill_and_achievement_extractor(resume_text)

    st.success("Resume processed successfully!")

# Always show extracted skills IF available
import html  # make sure this import is at top

if st.session_state.skills:
    st.subheader("🧠 Extracted Skills ")

    skills = st.session_state.skills

    # Build pills safely
    pills_html = "".join(
        [f"<span class='pill'>{html.escape(s)}</span>" for s in skills]
    )

    st.markdown(
        f"<div class='pill-container'>{pills_html}</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
            .pill-container { 
                display: flex; 
                flex-wrap: wrap; 
                gap: 8px;
                margin-top: 10px;
            }
            .pill {
                background: #1E88E5;
                color: white;
                padding: 8px 15px;
                border-radius: 30px;
                font-size: 14px;
                display: inline-block;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# JD INPUT FIELD (always visible)
# ------------------------------------------------------------
st.session_state.jd_text = st.text_area(
    "Paste Job Description (comma-separated OR full JD)",
    value=st.session_state.jd_text
)


# ------------------------------------------------------------
# BUTTON 2: ANALYZE WITH LLM
# ------------------------------------------------------------
if st.button("Analyze with LLM"):

    skills = st.session_state.skills
    jd_text = st.session_state.jd_text

    if not skills:
        st.error("Please extract resume text first.")
        st.stop()

    if jd_text.strip() == "":
        st.error("Please paste the Job Description.")
        st.stop()

    jd_input = parse_jd(jd_text)

    # Convert JD input safely to string
    if isinstance(jd_input, list):
        jd_input_formatted = json.dumps(jd_input, indent=2)
    else:
        jd_input_formatted = jd_input

    llm_output = call_llm_for_matching(
        resume_skills=skills,
        jd_input=jd_input_formatted,
        user_prompt=user_prompt
    )

    # st.subheader("🤖 LLM Raw Response (debug)")
    # st.code(llm_output)

    # Try JSON
    try:
        parsed = json.loads(llm_output)
        st.subheader("✨ Final Parsed Output")
        # st.json(parsed)

        st.markdown("### ✔ Mapped Skills")
        st.write(parsed.get("mapped", []))

        st.markdown("### 🔄 Substitutes")
        st.write(parsed.get("substitutes", []))

        st.markdown("### ➕ Extras")
        st.write(parsed.get("extras", []))

        st.markdown("### ⭐ Score")
        st.metric("Candidate Score", f"{parsed.get('score', 0)}/100")

        st.markdown("### 📝 Review")
        st.write(parsed.get("review", ""))

    except:
        st.error("LLM did not return valid JSON.")
        st.code(llm_output)



# for activating venv : HirePro\Scripts\activate
# for running application : streamlit run app2.py