# generator.py  — Flask route for resume generation
# ══════════════════════════════════════════════════════════════════
# WHAT THIS FILE DOES:
#   Handles the HTTP request when user clicks "Generate New Resume".
#   Reads the analysis data from the session, calls ResumeGenerator,
#   and streams the PDF back to the browser as a download.
#
# PLACE THIS FILE AT:
#   smart_resume_analyzer/app/routes/generator.py
# ══════════════════════════════════════════════════════════════════

from flask import (
    Blueprint, session, send_file, flash,
    redirect, url_for, request, jsonify, render_template
)
import io
import re

generator_bp = Blueprint('generator', __name__, url_prefix='/generate')


@generator_bp.route('/resume', methods=['POST'])
def generate_resume():
    """
    POST /generate/resume

    Reads analysis results from Flask session, generates a tailored
    PDF resume, and sends it as a downloadable file.

    Called when user clicks the "Generate New Resume" button
    on the results page (shown only when score < 75%).
    """

    # ── Step 1: Get the analysis data from session ─────────────
    # The analysis results were stored in session when user analyzed
    # their resume. We reuse all that data to build the new resume.
    result_data = session.get('analysis_results')

    if not result_data:
        flash('Session expired. Please analyze your resume again first.', 'error')
        return redirect(url_for('main.index'))

    # ── Step 2: Check if score actually needs improvement ───────
    # Safety check — only generate if score is below 75%
    overall_score = result_data.get('overall_score', 0)
    if overall_score >= 75:
        flash('Your resume already scores 75% or above. No regeneration needed!', 'info')
        return redirect(url_for('main.results'))

    # ── Step 3: Extract all needed data from session ───────────
    contact_info     = result_data.get('contact_info', {})
    resume_skills    = result_data.get('resume_skills', [])
    job_skills       = result_data.get('job_skills', [])
    matched_skills   = result_data.get('matched_skills', [])
    missing_skills   = result_data.get('missing_skills', [])
    education_info   = result_data.get('education', [])
    experience_years = result_data.get('experience_years', 0)
    sections         = _get_sections_from_session(result_data)
    filename         = result_data.get('filename', 'resume.pdf')

    # Get the job description — stored in session by analyze route
    job_description  = session.get('job_description_used', '')
    if not job_description:
        # Fallback: reconstruct hint from job skills
        job_description = _build_jd_hint_from_skills(job_skills)

    # ── Step 4: Generate the PDF ───────────────────────────────
    try:
        from app.services.resume_generator import ResumeGenerator
        generator = ResumeGenerator()

        pdf_bytes = generator.generate(
            contact_info     = contact_info,
            resume_skills    = resume_skills,
            job_skills       = job_skills,
            matched_skills   = matched_skills,
            missing_skills   = missing_skills,
            job_description  = job_description,
            overall_score    = overall_score,
            education_info   = education_info,
            experience_years = experience_years,
            filename         = filename,
            sections         = sections,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error generating resume: {str(e)}', 'error')
        return redirect(url_for('main.results'))

    # ── Step 5: Build a clean download filename ────────────────
    # Extract candidate name for the filename
    name        = contact_info.get('name', '') or _name_from_filename(filename)
    clean_name  = re.sub(r'[^a-zA-Z0-9_\-]', '_', name).strip('_') or 'candidate'
    download_name = f"{clean_name}_optimised_resume.pdf"

    # ── Step 6: Send PDF to browser as a download ──────────────
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,       # forces browser to download (not open inline)
        download_name=download_name,
    )


@generator_bp.route('/preview', methods=['GET'])
def preview_page():
    """
    GET /generate/preview

    Shows a preview page before generating the resume,
    letting the user see what will be included.
    """
    result_data = session.get('analysis_results')
    if not result_data:
        flash('No analysis data found. Please analyze a resume first.', 'error')
        return redirect(url_for('main.index'))

    overall_score = result_data.get('overall_score', 0)
    if overall_score >= 75:
        flash('Your resume already scores 75%+. No improvement needed!', 'info')
        return redirect(url_for('main.results'))

    return render_template(
        'generate_preview.html',
        results=result_data,
        overall_score=overall_score,
    )


# ══════════════════════════════════════════════════════════════════
# PRIVATE HELPERS
# ══════════════════════════════════════════════════════════════════

def _get_sections_from_session(result_data: dict) -> dict:
    """
    Reconstruct a sections dict from session data.
    The full section text is not always stored, so we rebuild
    what we can from stored fields.
    """
    sections = {}

    # If raw sections were stored
    raw_sections = result_data.get('sections', {})
    if raw_sections:
        return raw_sections

    return sections


def _build_jd_hint_from_skills(job_skills: list) -> str:
    """
    Build a minimal job description from the extracted job skills.
    Used as fallback when full JD is not available in session.
    """
    if not job_skills:
        return 'Software Developer position requiring strong technical skills.'
    skills_str = ', '.join(s.title() for s in job_skills[:15])
    return (
        f'We are looking for a Software Developer with skills in: {skills_str}. '
        f'Candidate should have experience building scalable applications, '
        f'working in agile teams, and writing clean, tested code.'
    )


def _name_from_filename(filename: str) -> str:
    """Try to extract a name from the uploaded filename."""
    base = filename.rsplit('.', 1)[0]          # remove extension
    base = re.sub(r'[_\-]', ' ', base)        # underscores → spaces
    base = re.sub(r'\d+', '', base).strip()   # remove numbers
    return base.title()[:40]
