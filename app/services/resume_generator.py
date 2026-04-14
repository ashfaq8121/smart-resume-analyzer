# resume_generator.py
# ══════════════════════════════════════════════════════════════════
# NEW FEATURE: Smart Resume Generator
#
# WHAT IT DOES:
#   When a resume scores below 75%, this service:
#   1. Takes the user's existing resume data (name, email, skills, etc.)
#   2. Looks at the job description to find what is needed
#   3. Generates a brand-new, tailored resume as a PDF
#   4. The new resume is keyword-optimised for that specific job
#   5. User can download it with one click
#
# HOW IT WORKS (simple explanation):
#   Think of it like a tailor. You give the tailor your measurements
#   (your existing resume data) and the dress code (job description).
#   The tailor stitches a new outfit (resume) that fits the occasion perfectly.
#
# PLACE THIS FILE AT:
#   smart_resume_analyzer/app/services/resume_generator.py
# ══════════════════════════════════════════════════════════════════

import io
import re
from datetime import datetime
from typing import Dict, List, Optional

# ReportLab — builds professional PDF files
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER


class ResumeGenerator:
    """
    Generates a tailored, ATS-friendly resume PDF from:
    - Existing resume data  (extracted by our NLP pipeline)
    - Job description       (what the employer wants)
    - Matched + missing skills (from our matcher)

    The generated resume:
    ✅ Uses keywords from the job description (beats ATS)
    ✅ Highlights skills the job requires
    ✅ Adds a tailored summary section
    ✅ Suggests missing skills to learn
    ✅ Professional clean design — ready to send
    """

    # ── Colour Palette ────────────────────────────────────────────
    DARK   = colors.HexColor('#1E293B')   # headings
    INDIGO = colors.HexColor('#4F46E5')   # accent colour
    GRAY   = colors.HexColor('#64748B')   # secondary text
    LIGHT  = colors.HexColor('#F1F5F9')   # background strip
    WHITE  = colors.white
    GREEN  = colors.HexColor('#065F46')   # matched skills
    MUTED  = colors.HexColor('#94A3B8')   # subtle text

    def generate(
        self,
        contact_info:     Dict,
        resume_skills:    List[str],
        job_skills:       List[str],
        matched_skills:   List[str],
        missing_skills:   List[str],
        job_description:  str,
        overall_score:    float,
        education_info:   List[Dict],
        experience_years: float,
        filename:         str = "resume",
        sections:         Optional[Dict] = None,
    ) -> bytes:
        """
        Build the PDF and return it as bytes (ready for HTTP download).

        Args:
            contact_info    : {'name', 'email', 'phone', 'linkedin', 'github'}
            resume_skills   : All skills found in original resume
            job_skills      : All skills the job needs
            matched_skills  : Skills the candidate already has
            missing_skills  : Skills the candidate needs to add
            job_description : Full job description text
            overall_score   : Original match score (shown in resume header)
            education_info  : List of education dicts from NLP
            experience_years: Detected years of experience
            filename        : Base name for the downloaded file
            sections        : Resume sections dict from NLP

        Returns:
            PDF file content as bytes
        """
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.55 * inch,
            bottomMargin=0.55 * inch,
            leftMargin=0.65 * inch,
            rightMargin=0.65 * inch,
        )

        styles = self._build_styles()
        story  = []

        # ── 1. Header (Name + Contact) ────────────────────────────
        story += self._build_header(contact_info, styles)

        # ── 2. AI-Generated Summary ───────────────────────────────
        story += self._build_summary(
            contact_info, matched_skills, job_description,
            experience_years, overall_score, styles
        )

        # ── 3. Skills Section (optimised for job) ─────────────────
        story += self._build_skills_section(
            matched_skills, missing_skills, resume_skills, job_skills, styles
        )

        # ── 4. Experience Section ─────────────────────────────────
        story += self._build_experience_section(
            sections or {}, experience_years, matched_skills, styles
        )

        # ── 5. Education Section ──────────────────────────────────
        story += self._build_education_section(education_info, sections or {}, styles)

        # ── 6. Projects Section ───────────────────────────────────
        story += self._build_projects_section(sections or {}, matched_skills, styles)

        # ── 7. Missing Skills (as "Currently Learning") ───────────
        if missing_skills:
            story += self._build_learning_section(missing_skills[:6], styles)

        # ── 8. Footer note ────────────────────────────────────────
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph(
            f'<font color="#94A3B8" size="8">Resume optimised by Smart Resume Analyzer '
            f'| Generated: {datetime.now().strftime("%B %Y")} '
            f'| Original match: {overall_score}% → Target: 75%+</font>',
            styles['center_small']
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    # ══════════════════════════════════════════════════════════════
    # SECTION BUILDERS
    # ══════════════════════════════════════════════════════════════

    def _build_header(self, contact: Dict, st: Dict) -> list:
        """
        Top section: Name (large), then contact line.
        Extracts a clean name from contact_info or falls back to 'Your Name'.
        """
        story = []

        name = contact.get('name', '') or self._extract_name_from_contact(contact)
        if not name or name.strip() == '':
            name = 'Your Name'

        story.append(Paragraph(name.title(), st['name']))

        # Build contact line from whatever we have
        contact_parts = []
        if contact.get('email'):   contact_parts.append(f"✉ {contact['email']}")
        if contact.get('phone'):   contact_parts.append(f"📞 {contact['phone']}")
        if contact.get('linkedin'):contact_parts.append(f"🔗 {contact['linkedin']}")
        if contact.get('github'):  contact_parts.append(f"💻 {contact['github']}")

        if contact_parts:
            story.append(Paragraph('   |   '.join(contact_parts), st['contact']))
        else:
            story.append(Paragraph(
                'your.email@gmail.com   |   +91-XXXXXXXXXX   |   linkedin.com/in/yourname',
                st['contact']
            ))

        story.append(HRFlowable(
            width='100%', thickness=2, color=self.INDIGO,
            spaceBefore=6, spaceAfter=8
        ))
        return story

    def _build_summary(
        self, contact: Dict, matched_skills: List[str],
        job_desc: str, exp_years: float, score: float, st: Dict
    ) -> list:
        """
        AI-generated professional summary that mirrors job description language.
        This is the most important ATS optimisation — recruiters read the summary first.
        """
        story = [self._section_title('PROFESSIONAL SUMMARY', st)]

        # Extract job title from job description
        role = self._extract_role_from_jd(job_desc)

        # Build skills phrase from top matched skills
        top_skills = matched_skills[:5] if matched_skills else ['software development', 'Python', 'web technologies']
        skills_phrase = ', '.join(s.title() for s in top_skills[:3])
        more_skills   = ', '.join(s.title() for s in top_skills[3:5]) if len(top_skills) > 3 else ''

        # Build experience phrase
        if exp_years >= 1:
            exp_phrase = f'{int(exp_years)}+ years of hands-on experience'
        else:
            exp_phrase = 'a strong foundation and practical project experience'

        summary_text = (
            f'Results-driven <b>{role}</b> with {exp_phrase} in building scalable, '
            f'production-quality software solutions. Proficient in <b>{skills_phrase}</b>'
            f'{(" and " + more_skills) if more_skills else ""}. '
            f'Passionate about writing clean, maintainable code and delivering '
            f'high-impact projects on time. Actively seeking opportunities to contribute '
            f'technical expertise and grow in a collaborative, fast-paced environment. '
            f'Open to challenging roles that demand both depth of technical knowledge '
            f'and strong problem-solving skills.'
        )

        story.append(Paragraph(summary_text, st['body']))
        story.append(Spacer(1, 0.1 * inch))
        return story

    def _build_skills_section(
        self, matched: List[str], missing: List[str],
        all_resume: List[str], job_skills: List[str], st: Dict
    ) -> list:
        """
        Skills section with smart categorisation.
        Matched skills are shown prominently. Missing skills shown as 'exposure'.
        """
        story = [self._section_title('TECHNICAL SKILLS', st)]

        # Categorise skills
        categories = {
            'Languages & Frameworks': [],
            'Cloud & DevOps':         [],
            'Databases':              [],
            'Tools & Practices':      [],
            'Soft Skills':            [],
        }

        lang_kw   = {'python','java','javascript','typescript','c','c++','c#','go','rust','kotlin','swift','r','scala','ruby','php','react','angular','vue','node','nodejs','django','flask','fastapi','spring','html','css'}
        cloud_kw  = {'aws','azure','gcp','docker','kubernetes','k8s','jenkins','github actions','terraform','ansible','linux','ci/cd','devops','heroku','nginx'}
        db_kw     = {'sql','mysql','postgresql','mongodb','redis','sqlite','elasticsearch','cassandra','dynamodb','firebase','oracle','graphdb'}
        tool_kw   = {'git','github','gitlab','jira','agile','scrum','postman','swagger','figma','pytest','jest','selenium','tdd'}

        for skill in all_resume:
            sl = skill.lower()
            if any(k in sl for k in lang_kw):      categories['Languages & Frameworks'].append(skill)
            elif any(k in sl for k in cloud_kw):   categories['Cloud & DevOps'].append(skill)
            elif any(k in sl for k in db_kw):      categories['Databases'].append(skill)
            elif any(k in sl for k in tool_kw):    categories['Tools & Practices'].append(skill)
            else:                                   categories['Soft Skills'].append(skill)

        # Build table rows: Category | Skills list
        rows = []
        for cat, skills in categories.items():
            if not skills:
                continue
            # Put matched skills first, then others
            ordered = sorted(skills, key=lambda s: 0 if s in matched else 1)
            rows.append([cat, ' • '.join(s.title() for s in ordered[:10])])

        if rows:
            table = Table(rows, colWidths=[1.6 * inch, 5.5 * inch])
            table.setStyle(TableStyle([
                ('FONTNAME',    (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE',    (0, 0), (-1, -1), 9),
                ('FONTNAME',    (0, 0), (0, -1),  'Helvetica-Bold'),
                ('TEXTCOLOR',   (0, 0), (0, -1),  self.INDIGO),
                ('TEXTCOLOR',   (1, 0), (1, -1),  self.DARK),
                ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING',  (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING',(0,0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ]))
            story.append(table)

        story.append(Spacer(1, 0.1 * inch))
        return story

    def _build_experience_section(
        self, sections: Dict, exp_years: float,
        matched_skills: List[str], st: Dict
    ) -> list:
        """
        Experience section — uses extracted text if available,
        otherwise generates a smart placeholder that the user can fill in.
        """
        story = [self._section_title('PROFESSIONAL EXPERIENCE', st)]

        exp_text = sections.get('experience', '')

        if exp_text and len(exp_text.strip()) > 80:
            # We have real experience text — format it nicely
            lines = [l.strip() for l in exp_text.split('\n') if l.strip()]
            for line in lines[:25]:  # limit to 25 lines
                # Detect if it looks like a job title / company line
                if any(kw in line.lower() for kw in ['developer', 'engineer', 'manager', 'analyst', 'intern', 'lead', 'architect']):
                    story.append(Paragraph(f'<b>{line}</b>', st['job_title']))
                elif re.match(r'.*20\d\d.*', line):   # contains a year
                    story.append(Paragraph(line, st['date_line']))
                elif line.startswith(('•', '-', '*', '◦')):
                    story.append(Paragraph(f'• {line.lstrip("•-*◦ ")}', st['bullet']))
                else:
                    story.append(Paragraph(line, st['body']))
        else:
            # No experience text — generate smart template
            top_skills = ', '.join(s.title() for s in matched_skills[:4]) or 'relevant technologies'
            story.append(Paragraph('<b>[Your Job Title]  —  [Company Name], [City]</b>', st['job_title']))
            story.append(Paragraph('[Month Year] – Present', st['date_line']))
            story += [
                Paragraph(f'• Developed and maintained web applications using {top_skills}', st['bullet']),
                Paragraph('• Collaborated with cross-functional teams to deliver features on schedule', st['bullet']),
                Paragraph('• Wrote unit and integration tests achieving 80%+ code coverage', st['bullet']),
                Paragraph('• Participated in code reviews and contributed to technical documentation', st['bullet']),
                Paragraph('• [Add a measurable achievement — e.g., "Reduced page load time by 35%"]', st['placeholder']),
            ]

        story.append(Spacer(1, 0.1 * inch))
        return story

    def _build_education_section(self, education_info: List[Dict], sections: Dict, st: Dict) -> list:
        """Education section from extracted data."""
        story = [self._section_title('EDUCATION', st)]

        if education_info:
            for edu in education_info[:3]:
                raw = edu.get('raw', '')
                if raw:
                    degree = edu.get('degree', '')
                    year   = edu.get('year', '')
                    if degree:
                        story.append(Paragraph(f'<b>{raw}</b>', st['job_title']))
                    else:
                        story.append(Paragraph(raw, st['body']))
        else:
            # Extract from raw section text
            edu_text = sections.get('education', '')
            if edu_text and len(edu_text.strip()) > 20:
                for line in edu_text.split('\n')[:6]:
                    if line.strip():
                        story.append(Paragraph(line.strip(), st['body']))
            else:
                story.append(Paragraph('<b>[Degree Name]  —  [University/College Name]  |  [Year]  |  [GPA/Percentage]</b>', st['placeholder']))

        story.append(Spacer(1, 0.1 * inch))
        return story

    def _build_projects_section(self, sections: Dict, matched_skills: List[str], st: Dict) -> list:
        """Projects section."""
        story = [self._section_title('PROJECTS', st)]

        proj_text = sections.get('projects', '')
        if proj_text and len(proj_text.strip()) > 60:
            for line in proj_text.split('\n')[:15]:
                if not line.strip():
                    continue
                if line.startswith(('•', '-', '*')):
                    story.append(Paragraph(f'• {line.lstrip("•-* ")}', st['bullet']))
                else:
                    story.append(Paragraph(f'<b>{line}</b>', st['job_title']))
        else:
            top3 = (matched_skills[:3] or ['Python', 'Flask', 'MongoDB'])
            story += [
                Paragraph(f'<b>Project 1: [Your Project Name]</b>', st['job_title']),
                Paragraph(
                    f'Built a full-stack web application using <b>{", ".join(s.title() for s in top3)}</b>. '
                    f'[Describe what it does and the impact it had — e.g., "Served 500+ users and reduced manual work by 60%"].',
                    st['bullet']
                ),
                Spacer(1, 0.05 * inch),
                Paragraph('<b>Project 2: [Your Project Name]</b>', st['job_title']),
                Paragraph('[Describe your second project with tech stack and measurable result.]', st['bullet']),
            ]

        story.append(Spacer(1, 0.1 * inch))
        return story

    def _build_learning_section(self, missing_skills: List[str], st: Dict) -> list:
        """
        'Currently Learning' section — converts missing skills into a positive.
        Instead of hiding gaps, this shows the candidate is actively improving.
        Recruiters love growth mindset.
        """
        story = [self._section_title('CURRENTLY LEARNING', st)]

        skills_str = ' • '.join(s.title() for s in missing_skills)
        story.append(Paragraph(
            f'Actively upskilling in: <b>{skills_str}</b> — '
            f'pursuing online certifications and hands-on projects to close skill gaps '
            f'and become a well-rounded full-stack professional.',
            st['body']
        ))
        return story

    # ══════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════

    def _section_title(self, title: str, st: Dict) -> Paragraph:
        return Paragraph(title, st['section'])

    def _extract_role_from_jd(self, jd: str) -> str:
        """Extract job title from job description text."""
        role_patterns = [
            r'(?i)(?:looking for|hiring|seeking|need|need a|we need)\s+(?:a\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4}\s+(?:Developer|Engineer|Architect|Analyst|Designer|Manager|Lead))',
            r'(?i)(?:position|role|job title)[\s:]+([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Architect|Analyst|Manager))',
            r'(?i)((?:Senior|Junior|Lead|Full[- ]Stack|Backend|Frontend|Software|Data)\s+(?:Developer|Engineer|Architect|Analyst))',
        ]
        for pattern in role_patterns:
            m = re.search(pattern, jd)
            if m:
                return m.group(1).strip()[:60]
        return 'Software Developer'

    def _extract_name_from_contact(self, contact: Dict) -> str:
        """Try to get name from email if no name found."""
        email = contact.get('email', '')
        if email and '@' in email:
            local = email.split('@')[0]
            # Convert john.doe or john_doe to John Doe
            name = re.sub(r'[._\-]', ' ', local).title()
            if len(name.split()) >= 2:
                return name
        return ''

    def _build_styles(self) -> Dict:
        """Build all paragraph styles for the resume."""
        return {
            'name': ParagraphStyle(
                'name', fontName='Helvetica-Bold', fontSize=22,
                textColor=self.DARK, alignment=TA_CENTER,
                spaceAfter=3
            ),
            'contact': ParagraphStyle(
                'contact', fontName='Helvetica', fontSize=9,
                textColor=self.GRAY, alignment=TA_CENTER,
                spaceAfter=4
            ),
            'section': ParagraphStyle(
                'section', fontName='Helvetica-Bold', fontSize=10,
                textColor=self.INDIGO, spaceBefore=10, spaceAfter=4,
                borderPad=2,
                borderWidth=0,
                leading=14,
            ),
            'job_title': ParagraphStyle(
                'job_title', fontName='Helvetica-Bold', fontSize=10,
                textColor=self.DARK, spaceBefore=6, spaceAfter=1
            ),
            'date_line': ParagraphStyle(
                'date_line', fontName='Helvetica-Oblique', fontSize=9,
                textColor=self.GRAY, spaceAfter=3
            ),
            'body': ParagraphStyle(
                'body', fontName='Helvetica', fontSize=9.5,
                textColor=self.DARK, spaceAfter=4, leading=14
            ),
            'bullet': ParagraphStyle(
                'bullet', fontName='Helvetica', fontSize=9.5,
                textColor=self.DARK, leftIndent=12,
                spaceAfter=3, leading=13
            ),
            'placeholder': ParagraphStyle(
                'placeholder', fontName='Helvetica-Oblique', fontSize=9,
                textColor=self.MUTED, leftIndent=12,
                spaceAfter=3, leading=13
            ),
            'center_small': ParagraphStyle(
                'center_small', fontName='Helvetica', fontSize=8,
                textColor=self.MUTED, alignment=TA_CENTER,
                spaceBefore=4
            ),
        }
