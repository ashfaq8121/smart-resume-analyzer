import os

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    current_app,
    session,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required, current_user

from app.services.parser import ResumeParser
from app.services.nlp_processor import NLPProcessor
from app.services.skill_extractor import SkillExtractor
from app.services.matcher import JobMatcher
from app.services.ranker import CandidateRanker
from app.services.resume_generator import ResumeGenerator
from app.utils.helpers import allowed_file, format_skills_for_display


main_bp = Blueprint("main", __name__)

parser = ResumeParser()
nlp = NLPProcessor()
matcher = JobMatcher()
ranker = CandidateRanker()
_skill_extractor = None


def get_skill_extractor():
    global _skill_extractor
    if _skill_extractor is None:
        _skill_extractor = SkillExtractor(current_app.config["SKILLS_DB_PATH"])
    return _skill_extractor


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/results")
@login_required
def results():
    data = session.get("analysis_results")
    if not data:
        flash("No results to display. Please analyze a resume first.", "warning")
        return redirect(url_for("main.index"))
    return render_template("results.html", results=data)


@main_bp.route("/rank-results")
@login_required
def rank_results():
    data = session.get("ranking_results")
    if not data:
        flash("No ranking results. Please upload resumes first.", "warning")
        return redirect(url_for("main.index"))
    return render_template("rank_results.html", results=data)


@main_bp.route("/generated")
@login_required
def generated():
    data = session.get("generated_resume")
    if not data:
        flash("No generated resume found.", "warning")
        return redirect(url_for("main.index"))
    return render_template("generate_preview.html", data=data)


@main_bp.route("/analyze", methods=["POST"])
@login_required
def analyze():
    resume_file = request.files.get("resume")
    job_description = request.form.get("job_description", "").strip()

    if not resume_file or not resume_file.filename:
        flash("Please upload a resume file.", "error")
        return redirect(url_for("main.index"))

    if not job_description:
        flash("Please enter a job description.", "error")
        return redirect(url_for("main.index"))

    if not allowed_file(resume_file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
        flash("Invalid file type. Use PDF or DOCX.", "error")
        return redirect(url_for("main.index"))

    try:
        result = _process_single_resume(resume_file, job_description)

        session["analysis_results"] = result
        session["job_description_used"] = job_description
        session.modified = True

        # Save analysis to history
        try:
            from app.models.database import db, AnalysisResult

            record = AnalysisResult(
                user_id=current_user.id,
                filename=resume_file.filename,
                job_description=job_description,
                overall_score=result.get("overall_score", 0),
                semantic_score=result.get("semantic_score", 0),
                skills_score=result.get("skills_score", 0),
                ats_score=result.get("ats_score", 0),
                matched_skills=result.get("matched_skills", []),
                missing_skills=result.get("missing_skills", []),
                grade_letter=result.get("match_grade", {}).get("letter", "F"),
                grade_label=result.get("match_grade", {}).get("label", ""),
                suggestions=result.get("improvement_suggestions", []),
            )

            db.session.add(record)
            db.session.commit()
            current_app.logger.info(
                f"History saved successfully for user_id={current_user.id}, record_id={record.id}"
            )

        except Exception as db_error:
            current_app.logger.error(f"History save failed: {db_error}")
            try:
                db.session.rollback()
            except Exception:
                pass

        return redirect(url_for("main.results"))

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"Error analyzing resume: {str(e)}", "error")
        return redirect(url_for("main.index"))


@main_bp.route("/generate", methods=["POST"])
@login_required
def generate_resume():
    analysis = session.get("analysis_results")
    job_description = session.get("job_description_used", "")

    if not analysis:
        flash("Analyze a resume first.", "error")
        return redirect(url_for("main.index"))

    if not job_description:
        job_description = analysis.get("job_description", "").strip()

    if not job_description:
        flash("Job description not found. Please analyze the resume again.", "error")
        return redirect(url_for("main.results"))

    try:
        generator = ResumeGenerator()
        pdf_bytes = generator.generate(
            contact_info=analysis.get("contact_info", {}),
            resume_skills=analysis.get("resume_skills", []),
            job_skills=analysis.get("job_skills", []),
            matched_skills=analysis.get("matched_skills", []),
            missing_skills=analysis.get("missing_skills", []),
            job_description=job_description,
            overall_score=analysis.get("overall_score", 0),
            education_info=analysis.get("education", []),
            experience_years=analysis.get("experience_years", 0),
            filename=analysis.get("filename", "resume"),
            sections={}
        )

        original_name = analysis.get("filename", "resume")
        safe_name = os.path.splitext(original_name)[0]
        pdf_filename = f"{safe_name}_generated_resume.pdf"

        save_dir = os.path.join(current_app.static_folder, "generated_resumes")
        os.makedirs(save_dir, exist_ok=True)

        pdf_path = os.path.join(save_dir, pdf_filename)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        session["generated_resume"] = {
            "path": url_for("static", filename=f"generated_resumes/{pdf_filename}"),
            "original_score": analysis.get("overall_score", 0),
            "job_description": job_description,
            "filename": pdf_filename,
        }
        session.modified = True

        return redirect(url_for("main.generated"))

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"Error generating resume: {str(e)}", "error")
        return redirect(url_for("main.results"))


@main_bp.route("/rank", methods=["POST"])
@login_required
def rank():
    resume_files = request.files.getlist("resumes")
    job_description = request.form.get("job_description", "").strip()

    if not resume_files or not any(f.filename for f in resume_files):
        flash("Please upload at least one resume file.", "error")
        return redirect(url_for("main.index"))

    if not job_description:
        flash("Please enter a job description.", "error")
        return redirect(url_for("main.index"))

    valid_files = [
        f for f in resume_files
        if f.filename and allowed_file(f.filename, current_app.config["ALLOWED_EXTENSIONS"])
    ]

    if not valid_files:
        flash("No valid PDF/DOCX files found.", "error")
        return redirect(url_for("main.index"))

    candidates = []

    for f in valid_files:
        try:
            result = _process_single_resume(f, job_description)
            result["filename"] = f.filename
            candidates.append(result)
        except Exception as e:
            candidates.append({
                "filename": f.filename,
                "error": str(e),
                "overall_score": 0,
                "semantic_score": 0,
                "tfidf_score": 0,
                "skills_score": 0,
                "ats_score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "experience_years": 0,
                "composite_score": 0,
            })

    if not candidates:
        flash("Could not process any resumes.", "error")
        return redirect(url_for("main.index"))

    ranked = ranker.rank_candidates(candidates)
    insights = ranker.generate_ranking_insights(ranked)

    session["ranking_results"] = {
        "candidates": _trim_candidates(ranked),
        "insights": insights,
        "job_description": job_description[:300],
        "total_uploaded": len(valid_files),
    }
    session.modified = True

    return redirect(url_for("main.rank_results"))


@main_bp.route("/api/analyze", methods=["POST"])
def api_analyze():
    f = request.files.get("resume")
    jd = request.form.get("job_description", "").strip()

    if not f or not jd:
        return jsonify({"error": "Missing resume or job description"}), 400

    if not allowed_file(f.filename, current_app.config["ALLOWED_EXTENSIONS"]):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        result = _process_single_resume(f, jd)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _process_single_resume(resume_file, job_description: str) -> dict:
    se = get_skill_extractor()

    file_bytes = resume_file.read()
    filename = resume_file.filename

    if not file_bytes:
        raise ValueError(f"'{filename}' is empty.")

    resume_text = parser.extract_text_from_bytes(file_bytes, filename)
    if not resume_text or len(resume_text.strip()) < 30:
        raise ValueError(
            f"Cannot extract text from '{filename}'. Ensure it's a text-based PDF or DOCX."
        )

    nlp_result = nlp.process(resume_text)
    job_nlp = nlp.process(job_description)

    resume_skills_dict = se.extract_skills(resume_text)
    job_skills_dict = se.extract_skills(job_description)

    resume_skills = resume_skills_dict.get("all", [])
    job_skills = job_skills_dict.get("all", [])

    match_result = matcher.calculate_match(
        resume_text=nlp_result["processed_text"],
        job_description=job_nlp["processed_text"],
        resume_skills=resume_skills,
        job_skills=job_skills,
    )

    education_info = nlp.extract_education_info(
        nlp_result.get("sections", {}).get("education", "")
    )

    experience_years = nlp.extract_experience_years(resume_text)
    entities = nlp_result.get("entities", {})

    return {
        "filename": filename,
        "job_description": job_description,
        "resume_text_preview": resume_text[:250] + "..." if len(resume_text) > 250 else resume_text,
        "resume_text": resume_text,
        "contact_info": nlp_result.get("contact_info", {}),
        "entities": entities,
        "education": education_info,
        "experience_years": experience_years,
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "resume_skills_categorized": format_skills_for_display(resume_skills_dict),
        "job_skills_categorized": format_skills_for_display(job_skills_dict),
        "overall_score": match_result.get("overall_score", 0),
        "semantic_score": match_result.get("semantic_score", 0),
        "tfidf_score": match_result.get("tfidf_score", 0),
        "skills_score": match_result.get("skills_score", 0),
        "ats_score": match_result.get("ats_score", 0),
        "ats_checks": match_result.get("ats_checks", {}),
        "method_used": match_result.get("method_used", "tfidf"),
        "matched_skills": match_result.get("matched_skills", []),
        "missing_skills": match_result.get("missing_skills", []),
        "extra_skills": match_result.get("extra_skills", []),
        "keyword_matches": match_result.get("keyword_matches", [])[:15],
        "improvement_suggestions": match_result.get("improvement_suggestions", []),
        "match_grade": match_result.get(
            "match_grade",
            {"letter": "C", "label": "Average", "color": "#f59e0b"}
        ),
        "total_resume_skills": len(resume_skills),
        "total_job_skills": len(job_skills),
        "sections_found": list(nlp_result.get("sections", {}).keys()),
    }


def _trim_candidates(candidates: list) -> list:
    trimmed = []
    for c in candidates:
        t = dict(c)
        t.pop("resume_skills_categorized", None)
        t.pop("job_skills_categorized", None)
        t.pop("resume_text_preview", None)
        t.pop("resume_text", None)
        t.pop("education", None)
        t.pop("sections_found", None)
        t.pop("entities", None)
        t["matched_skills"] = t.get("matched_skills", [])[:20]
        t["missing_skills"] = t.get("missing_skills", [])[:20]
        t["keyword_matches"] = t.get("keyword_matches", [])[:10]
        t["improvement_suggestions"] = t.get("improvement_suggestions", [])[:3]
        trimmed.append(t)
    return trimmed