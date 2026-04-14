# 🧠 ResumeIQ — Smart Resume Analyzer

> **Upload your resume. Paste a job description. Get an instant AI-powered score, skill gap analysis, improvement suggestions, and a tailored PDF resume — all in one click.**

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-3.x-green?style=flat-square)
![Mobile Ready](https://img.shields.io/badge/Mobile-Responsive-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

---

## 📌 What Is This?

**ResumeIQ** is a full-stack web application that helps job seekers understand exactly why they are or aren't getting interviews. Most people apply for jobs blindly — this tool removes that guesswork entirely.

You upload your resume (PDF or DOCX), paste a job description, and within seconds the app tells you:

- Your **overall match score** (0–100%) for that specific job
- Which skills you already have that the job wants ✅
- Which skills are missing from your resume ❌
- Whether your resume would **pass an ATS filter** (the automated system companies use to reject resumes before a human ever reads them)
- Exactly **what to improve** to increase your score
- And if your score is below 75%, it **generates a brand-new tailored PDF resume** for you to download

For recruiters, the app also accepts **10+ resumes at once** and ranks all candidates from best to worst match — automatically.

---

## ✨ Features

### For Job Seekers
- **Match Score** — Overall 0–100% score for how well your resume fits the specific job
- **Semantic Score** — AI that understands *meaning*, not just word overlap (BERT-based)
- **Skills Score** — Percentage of required job skills that are present in your resume
- **ATS Score** — Checks if your resume would survive Applicant Tracking System filters
- **Match Grade** — Letter grade A+ to F with a label (Excellent, Strong, Fair, Poor)
- **Matched Skills** — Green tags: skills you already have ✅
- **Missing Skills** — Red tags: skills you need to add ❌
- **Keyword Matches** — Exact words from the job description found in your resume
- **Improvement Suggestions** — Specific, actionable tips to increase your score
- **Resume Preview** — See exactly how the parser read your uploaded file
- **Generate Optimised Resume** — Builds a fresh ATS-friendly PDF tailored to the job (shown automatically when score < 75%)

### For Recruiters
- **Multi-Resume Ranking** — Upload 2 to 20+ resumes at once against one job description
- **Candidate Leaderboard** — Ranked #1, #2, #3... with composite scores and tier badges (Top Candidate, Strong Candidate, etc.)
- **Pool Insights** — Average score, highest score, number of excellent (80%+) matches
- **Commonly Missing Skills** — Which skills the majority of candidates lack (useful for training decisions)
- **Print Rankings** — One-click print of the full leaderboard

### For Logged-In Users
- **Analysis History** — Every resume analysis saved permanently to your account
- **Progress Dashboard** — Total uploads, best score ever, average score across all analyses
- **Job Description Archive** — Expand any past record to read the full job description again
- **Resume Text View** — Tap any record to read the full text extracted from that resume

---

## 🖼️ Pages & URLs

| URL | Page | Access |
|-----|------|--------|
| `/` | Home — upload form with two tabs | Public |
| `/results` | Full analysis: scores, skills, suggestions | Login required |
| `/rank-results` | Candidate leaderboard for recruiters | Login required |
| `/generated` | Preview + download AI-generated resume | Login required |
| `/history` | All past analyses saved to your account | Login required |
| `/auth/login` | Login page | Public |
| `/auth/register` | Registration page | Public |
| `/auth/logout` | Logs out and redirects home | Login required |

---

## 🗂️ Project Structure

```
sra/
│
├── run.py                        ← Start the server: python run.py
├── config.py                     ← All settings (database, uploads, secret key)
├── requirements.txt              ← Python dependencies
├── README.md                     ← This file
│
├── app/
│   ├── __init__.py               ← Flask app factory (wires Flask-Login, DB, blueprints)
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py               ← Core routes: /, /analyze, /results, /rank, /generate
│   │   ├── auth.py               ← /auth/login, /auth/register, /auth/logout
│   │   ├── generator.py          ← /generate/resume, /generate/preview
│   │   └── history.py            ← /history (login required)
│   │
│   ├── services/                 ← The intelligence — the brain of the app
│   │   ├── __init__.py
│   │   ├── parser.py             ← Reads PDF and DOCX files, extracts raw text
│   │   ├── nlp_processor.py      ← NLP: tokenization, section detection, entity extraction
│   │   ├── skill_extractor.py    ← Finds 200+ skills with multi-word matching & alias resolution
│   │   ├── matcher.py            ← Calculates match score (BERT semantic + TF-IDF fallback)
│   │   ├── ranker.py             ← Ranks multiple candidates by composite score
│   │   └── resume_generator.py   ← Builds tailored PDF resume using ReportLab
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py           ← SQLAlchemy models: User, AnalysisResult, RankingSession
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py            ← Shared utility functions
│
├── templates/
│   ├── base.html                 ← Shared layout: nav, hamburger menu, footer, CSS variables
│   ├── index.html                ← Home page — upload form with tab switching
│   ├── results.html              ← Single resume analysis results page
│   ├── rank_results.html         ← Multi-resume candidate rankings
│   ├── generate_preview.html     ← Preview and download the AI-generated resume
│   ├── history.html              ← User's saved analysis history
│   └── auth/
│       ├── login.html            ← Login form
│       └── register.html         ← Registration form with account perks
│
├── static/
│   ├── uploads/                  ← Temporary upload storage (auto-created)
│   └── generated_resumes/        ← Generated PDF resumes (auto-created)
│
├── data/
│   └── skills_db.json            ← 200+ skills organized by category
│
├── flask_sessions/               ← Server-side session files (auto-created)
├── resume_analyzer.db            ← SQLite database (auto-created on first run)
│
├── tests/
│   ├── test_parser.py
│   └── test_matcher.py
│
|--images/
|
├── Procfile                      ← Deployment: web: gunicorn run:app
|── render.yaml                   ← Render.com auto-deploy config
|── README.md                    # This file!

```

---

## ⚙️ How It Works — The Full Pipeline

When you upload a resume and paste a job description, this is exactly what happens inside:

### Step 1 — Text Extraction (`parser.py`)
The file is read from memory without being saved to disk. For **PDFs**, the app tries **pdfminer.six** first (handles complex layouts, multi-column PDFs, scanned-like files) then falls back to **PyPDF2** if that fails. For **DOCX files**, **python-docx** reads every paragraph and table cell. Raw text is cleaned: null bytes removed, PDF artifacts stripped, whitespace normalized, non-printable characters replaced.

### Step 2 — NLP Processing (`nlp_processor.py`)
The clean text is processed using a smart fallback chain:
- **spaCy** (if installed) — Named Entity Recognition automatically finds company names, dates, locations, and the candidate's name, even on messily formatted resumes
- **NLTK** — Tokenizes text, removes stopwords ("the", "and", "is"), lemmatizes words ("running" → "run")
- **Regex fallback** — Works even if neither NLP library is available

The resume is also split into named sections: Education, Experience, Skills, Projects, Certifications, Summary, Contact.

### Step 3 — Skill Extraction (`skill_extractor.py`)
Both the resume and job description are scanned against a **200+ skill database** in 7 categories. The matching is smart in three ways:
1. **Multi-word matching**: "machine learning" is found as one skill, not two unrelated words
2. **Alias resolution**: `react`, `reactjs`, and `react.js` all map to the same canonical "react" skill so it's never counted twice
3. **Word boundary matching**: `java` never accidentally matches `javascript`

### Step 4 — Match Calculation (`matcher.py`)
The scoring engine uses multiple methods with automatic fallback:

**Primary — Semantic Similarity (BERT):**
Uses `sentence-transformers` with the `all-MiniLM-L6-v2` model. This understands meaning, not just word overlap. "Built REST APIs" and "developed RESTful services" score ~92% similar even with almost no shared words. Loads on app startup, cached in memory for all subsequent requests.

**Fallback — TF-IDF + Cosine Similarity:**
If `sentence-transformers` is not installed, scikit-learn's TF-IDF vectorizer with bigrams and cosine similarity is used automatically. Still effective, just less semantically aware.

**ATS Scoring:**
Checks: does the resume have standard section headers? Is contact info visible? Are there measurable results ("improved by 40%")? Are enough job keywords present? Real ATS systems use these same criteria.

**Final Score Formula:**
```
Overall Score = (Semantic Score × 55%) + (Skills Score × 35%) + (ATS Score × 10%)
```

### Step 5 — Resume Generation (`resume_generator.py`)
When score < 75%, a new PDF is built with **ReportLab** using all extracted data: name, email, phone, skills, education, and any experience text found. The job description keywords are woven into the summary and skills sections. Missing skills appear as a "Currently Learning" section — turning gaps into a growth story. The PDF uses a professional clean design ready to download and customize.

### Step 6 — Candidate Ranking (`ranker.py`)
Each resume goes through steps 1–4 independently. Then:
```
Composite Score = (TF-IDF × 50%) + (Skills × 35%) + (Experience Bonus × 15%)
```
Bonus: +0.5 points per matched skill beyond 5 (max +5). Everyone sorted highest to lowest, assigned rank and tier badge.

---

## 🗄️ Database

Uses **SQLite** by default — one file, zero setup. Switch to PostgreSQL for production via the `DATABASE_URL` environment variable.

### `users` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto ID |
| `name` | String(120) | Full name |
| `email` | String(120) | Unique email used for login |
| `password` | String(200) | bcrypt hash — never plain text |
| `created_at` | DateTime | Account creation time |

### `analysis_results` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto ID |
| `user_id` | Integer (FK) | Links to user |
| `filename` | String(255) | Uploaded resume filename |
| `job_description` | Text | Full job description |
| `overall_score` | Float | Final score (0–100) |
| `semantic_score` | Float | Semantic/TF-IDF score |
| `skills_score` | Float | Skills match % |
| `ats_score` | Float | ATS check score |
| `matched_skills` | JSON | Skills the user had |
| `missing_skills` | JSON | Skills they were missing |
| `grade_letter` | String | A+, A, B, C, D, F |
| `grade_label` | String | "Excellent Match" etc. |
| `suggestions` | JSON | Improvement tips |
| `resume_text` | Text | Full extracted resume text |
| `created_at` | DateTime | When analysis ran |

### `ranking_sessions` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto ID |
| `user_id` | Integer (FK) | Links to user |
| `job_description` | Text | Job description used |
| `total_candidates` | Integer | Resumes uploaded |
| `top_candidate` | String | Filename of #1 ranked resume |
| `avg_score` | Float | Average composite score |
| `results_json` | JSON | Full ranking data |
| `created_at` | DateTime | When ranking ran |

---

## 📦 Libraries Used

### Web Framework
| Library | Purpose |
|---------|---------|
| `Flask 3.x` | Web framework — routing, templates, request handling |
| `Flask-Login 0.6.x` | User authentication, `@login_required` decorator |
| `Flask-Session 0.8.x` | Server-side sessions — prevents "cookie too large" errors |
| `Flask-SQLAlchemy 3.x` | Database ORM — Python classes become DB tables |
| `Flask-Bcrypt` | Secure password hashing with bcrypt |
| `Werkzeug 3.x` | Secure filename handling, password utilities |

### NLP & AI
| Library | Purpose |
|---------|---------|
| `spacy 3.x` + `en_core_web_sm` | Named Entity Recognition — finds names, companies, dates |
| `nltk 3.x` | Tokenization, stopword removal, lemmatization |
| `sentence-transformers 2.x` | BERT semantic similarity (`all-MiniLM-L6-v2`) |
| `scikit-learn 1.x` | TF-IDF vectorization + cosine similarity (fallback) |
| `numpy 1.x` | Numerical operations for vector math |

### File Parsing
| Library | Purpose |
|---------|---------|
| `pdfminer.six` | PDF text extraction — primary, handles complex layouts |
| `PyPDF2 3.x` | PDF text extraction — fallback for simpler PDFs |
| `python-docx 1.x` | Word document (.docx) extraction |

### PDF Generation
| Library | Purpose |
|---------|---------|
| `reportlab 4.x` | Builds professional PDF resumes from scratch |

### Deployment
| Library | Purpose |
|---------|---------|
| `gunicorn` | Production WSGI server for Render/Heroku |

---

## 🚀 Running Locally

### 1. Clone
```bash
git clone https://github.com/yourusername/smart-resume-analyzer.git
cd smart-resume-analyzer
```

### 2. Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download spaCy Model
```bash
python -m spacy download en_core_web_sm
```

### 5. Initialize Database
```bash
python reset_db.py
```
This deletes any old broken database and creates a fresh one with all correct columns.

### 6. Start
```bash
python run.py
```
Open **http://127.0.0.1:5000** — register an account and start analyzing.

---

## 🔧 Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `SECRET_KEY` | Hardcoded | Signs session cookies — change in production |
| `UPLOAD_FOLDER` | `static/uploads/` | Temp storage for uploads |
| `ALLOWED_EXTENSIONS` | `{pdf, docx}` | Accepted file types |
| `MAX_CONTENT_LENGTH` | 16 MB | Max upload size |
| `SKILLS_DB_PATH` | `data/skills_db.json` | Skills database path |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///resume_analyzer.db` | Database |
| `SESSION_TYPE` | `filesystem` | Server-side sessions |
| `DEBUG` | `True` | Set `False` in production |

**Production environment variables:**
```bash
SECRET_KEY=your-long-random-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DEBUG=False
```

---

## 📊 Scoring Explained

```
Overall = (Semantic × 55%) + (Skills × 35%) + (ATS × 10%)
```

| Score Range | Grade | What It Means |
|-------------|-------|---------------|
| 85–100% | A+ | Excellent — apply with confidence |
| 75–84% | A | Strong — small gaps to close |
| 65–74% | B | Good — some work needed |
| 55–64% | C | Fair — significant gaps |
| 40–54% | D | Weak — major rework needed |
| 0–39% | F | Poor — not a good fit or resume needs heavy tailoring |

---

## 📱 Mobile & Responsive Design

The app is built mobile-first and works like a native app on phones:

- **Hamburger menu** — tap ☰ to open the full navigation drawer on mobile
- **Single-column layouts** — all grids collapse cleanly on small screens
- **Touch-friendly** — all tap targets are large enough for fingers
- **Swipeable table** — the history table scrolls horizontally on mobile
- **PWA meta tags** — "Add to Home Screen" works on iPhone and Android for a native feel
- **No horizontal overflow** — tested at 380px, 640px, 900px, 1200px

---

## 🚢 Deploying to Render.com

1. Push code to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Connect your repository
4. Add environment variables (`SECRET_KEY`, `DATABASE_URL`, `DEBUG=False`)
5. Render reads `render.yaml` and deploys automatically

The `Procfile` contains:
```
web: gunicorn run:app
```

---

## 💡 Tips for Users

- **Mirror the job description language** — if the job says "collaborative environment", use "collaborative" in your resume
- **Add a clear Skills section** — the extractor and ATS both look for it specifically
- **Use standard section headers** — "Experience", "Education", "Skills", "Projects" are recognized automatically
- **Quantify your achievements** — "reduced load time by 40%" scores higher than "improved performance"
- **Score below 75%?** — Use "Generate Optimised Resume", download the PDF, fill in the placeholder sections, then re-upload to see your new score

---

## 🛠️ Skills Database (200+ Skills, 7 Categories)

| Category | Example Skills |
|----------|---------------|
| Programming Languages | Python, Java, JavaScript, TypeScript, C++, C#, Go, Rust, R |
| Web Technologies | React, Angular, Vue, Node.js, Django, Flask, FastAPI, HTML, CSS |
| Databases | SQL, MySQL, PostgreSQL, MongoDB, Redis, SQLite, Cassandra |
| Cloud & DevOps | AWS, Azure, GCP, Docker, Kubernetes, Jenkins, GitHub Actions, Linux |
| Data Science & ML | Machine Learning, Deep Learning, NLP, TensorFlow, PyTorch, Pandas, NumPy, scikit-learn |
| Tools & Practices | Git, GitHub, Agile, Scrum, JIRA, Postman, REST APIs, CI/CD |
| Soft Skills | Leadership, Communication, Problem Solving, Teamwork |

---

*ResumeIQ — Helping you get past the ATS and into the interview room.*
