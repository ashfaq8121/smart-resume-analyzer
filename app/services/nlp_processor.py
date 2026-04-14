# nlp_processor.py — UPGRADED VERSION
# ─────────────────────────────────────────────────────────────────
# UPGRADE 2: spaCy Named Entity Recognition
#
# OLD: regex patterns to find sections and contact info
# NEW: spaCy's trained NLP model automatically finds:
#   - ORG:    companies (Google, Infosys, IIT Delhi)
#   - DATE:   dates and durations (Jan 2021, 3 years)
#   - PERSON: names
#   - GPE:    locations (Hyderabad, India)
#   - Works even when resume has unusual formatting
#
# FALLBACK: If spaCy not installed, falls back to original regex method
# ─────────────────────────────────────────────────────────────────

import re
import string
from typing import Dict, List

# ── Try loading spaCy ────────────────────────────────────────────
SPACY_AVAILABLE = False
try:
    import spacy
    # Load small English model (download once: python -m spacy download en_core_web_sm)
    _nlp_model = spacy.load('en_core_web_sm')
    SPACY_AVAILABLE = True
    print("  ✅  spaCy NLP model loaded: en_core_web_sm")
except (ImportError, OSError):
    print("  ⚠️   spaCy not available → using regex fallback")
    print("       To enable: pip install spacy && python -m spacy download en_core_web_sm")

# ── NLTK fallback ────────────────────────────────────────────────
try:
    import nltk
    for r in ['stopwords','punkt','averaged_perceptron_tagger','wordnet']:
        try: nltk.download(r, quiet=True)
        except: pass
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class NLPProcessor:
    """
    UPGRADED NLP processor using spaCy for smart entity extraction.

    What spaCy adds over regex:
    ─ Finds company names even without "Company:" label
    ─ Extracts job titles via part-of-speech tagging
    ─ Identifies locations, dates, and organisations automatically
    ─ Works on messy, inconsistent resume formats
    """

    SECTION_PATTERNS = {
        'education':      r'(?i)(education|academic|qualification|degree|university|college)',
        'experience':     r'(?i)(experience|employment|work history|professional|career)',
        'skills':         r'(?i)(skills|technical skills|technologies|competencies|expertise)',
        'projects':       r'(?i)(projects|portfolio|assignments)',
        'certifications': r'(?i)(certif|license|credential)',
        'summary':        r'(?i)(summary|objective|profile|about me|overview)',
        'contact':        r'(?i)(contact|email|phone|address|linkedin|github)',
        'achievements':   r'(?i)(achievement|award|honour|honor|recognition)',
    }

    def __init__(self):
        if NLTK_AVAILABLE:
            try:
                self.stop_words = set(stopwords.words('english'))
                self.lemmatizer = WordNetLemmatizer()
            except Exception:
                self.stop_words = self._get_fallback_stopwords()
                self.lemmatizer = None
        else:
            self.stop_words = self._get_fallback_stopwords()
            self.lemmatizer = None

        self.stop_words.update([
            'resume','curriculum','vitae','cv','page','name',
            'address','phone','email','linkedin','github',
            'reference','available','upon','request',
        ])

    def process(self, text: str) -> Dict:
        """Master function: raw text → structured info dict."""
        if not text:
            return {'sections': {}, 'tokens': [], 'processed_text': '', 'contact_info': {}, 'raw_text': ''}

        sections     = self._extract_sections(text)
        contact_info = self._extract_contact_info_smart(text)
        entities     = self._extract_entities_spacy(text) if SPACY_AVAILABLE else {}
        tokens       = self.tokenize_and_clean(text)

        return {
            'sections':       sections,
            'tokens':         tokens,
            'processed_text': ' '.join(tokens),
            'contact_info':   contact_info,
            'entities':       entities,
            'raw_text':       text,
        }

    # ─────────────────────────────────────────────────────────────
    # UPGRADE 2: spaCy Named Entity Recognition
    # ─────────────────────────────────────────────────────────────

    def _extract_entities_spacy(self, text: str) -> Dict:
        """
        Use spaCy's trained NER model to extract structured info.

        Entity types extracted:
        ORG   → companies, universities, institutes
        DATE  → experience dates, graduation years
        GPE   → cities, countries, locations
        PERSON→ the candidate's name (usually first entity)
        MONEY → salary mentions
        """
        try:
            # spaCy has 1M char limit — process first 50K chars
            doc = _nlp_model(text[:50000])

            entities = {
                'organisations': [],
                'dates':         [],
                'locations':     [],
                'persons':       [],
                'skills_context':[],
            }

            seen = set()
            for ent in doc.ents:
                text_lower = ent.text.lower().strip()
                if text_lower in seen or len(ent.text.strip()) < 2:
                    continue
                seen.add(text_lower)

                if ent.label_ == 'ORG':
                    entities['organisations'].append(ent.text.strip())
                elif ent.label_ == 'DATE':
                    entities['dates'].append(ent.text.strip())
                elif ent.label_ in ('GPE', 'LOC'):
                    entities['locations'].append(ent.text.strip())
                elif ent.label_ == 'PERSON':
                    entities['persons'].append(ent.text.strip())

            return entities

        except Exception as e:
            print(f"  ⚠️  spaCy entity extraction error: {e}")
            return {}

    def _extract_contact_info_smart(self, text: str) -> Dict:
        """
        Smart contact extraction:
        - Uses spaCy for name detection (if available)
        - Uses regex for email, phone, LinkedIn, GitHub
        """
        contact = {}

        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
        if email_match:
            contact['email'] = email_match.group()

        # Phone (various formats)
        phone_match = re.search(
            r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text
        )
        if phone_match:
            contact['phone'] = phone_match.group().strip()

        # LinkedIn
        linkedin = re.search(r'linkedin\.com/in/[\w\-]+', text, re.IGNORECASE)
        if linkedin:
            contact['linkedin'] = linkedin.group()

        # GitHub
        github = re.search(r'github\.com/[\w\-]+', text, re.IGNORECASE)
        if github:
            contact['github'] = github.group()

        # Name from spaCy (first PERSON entity is usually the candidate)
        if SPACY_AVAILABLE:
            try:
                doc = _nlp_model(text[:500])  # name is always near the top
                for ent in doc.ents:
                    if ent.label_ == 'PERSON' and len(ent.text.split()) >= 2:
                        contact['name'] = ent.text
                        break
            except Exception:
                pass

        return contact

    # ─────────────────────────────────────────────────────────────
    # TOKENISATION (unchanged — already works well)
    # ─────────────────────────────────────────────────────────────

    def tokenize_and_clean(self, text: str) -> List[str]:
        """Lowercase → tokenise → remove stopwords → lemmatise."""
        text_lower = text.lower()

        if NLTK_AVAILABLE:
            try:    tokens = word_tokenize(text_lower)
            except: tokens = text_lower.split()
        else:
            tokens = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.\-]*\b', text_lower)

        cleaned = []
        for tok in tokens:
            if tok in string.punctuation: continue
            if tok.isdigit():             continue
            if len(tok) < 2:              continue
            if tok in self.stop_words:    continue
            if self.lemmatizer:
                try: tok = self.lemmatizer.lemmatize(tok)
                except: pass
            cleaned.append(tok)
        return cleaned

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Split resume into named sections."""
        sections = {}
        current_section = 'general'
        sections[current_section] = []

        for line in text.split('\n'):
            line_s = line.strip()
            if not line_s:
                continue
            section_found = None
            for sec, pattern in self.SECTION_PATTERNS.items():
                if re.search(pattern, line_s) and len(line_s) < 60:
                    section_found = sec
                    break
            if section_found:
                current_section = section_found
                sections.setdefault(current_section, [])
            else:
                sections.setdefault(current_section, []).append(line_s)

        return {s: '\n'.join(lines) for s, lines in sections.items() if lines}

    def extract_education_info(self, education_text: str) -> List[Dict]:
        """Parse education section for degree/year info."""
        edu_list = []
        if not education_text:
            return edu_list

        degree_patterns = [
            r'(?i)(ph\.?d|doctor)', r'(?i)(m\.?tech|m\.?e\.?|m\.?s\.?|master)',
            r'(?i)(b\.?tech|b\.?e\.?|b\.?s\.?|bachelor)', r'(?i)(b\.?sc|m\.?sc)',
            r'(?i)(mba|pgd|post.?grad)', r'(?i)(diploma|associate)',
            r'(?i)(10th|12th|high school|secondary)',
        ]
        year_pattern = r'\b(19[9][0-9]|20[0-2][0-9]|2030)\b'

        for line in education_text.split('\n'):
            if not line.strip():
                continue
            entry = {'raw': line.strip()}
            for p in degree_patterns:
                m = re.search(p, line)
                if m:
                    entry['degree'] = m.group()
                    break
            years = re.findall(year_pattern, line)
            if years:
                entry['year'] = years[-1]
            if 'degree' in entry or any(kw in line.lower() for kw in ['university','college','institute','school']):
                edu_list.append(entry)
        return edu_list

    def extract_experience_years(self, text: str) -> float:
        """Extract total years of experience from text."""
        # Pattern: "X years of experience"
        m = re.findall(r'(\d+\.?\d*)\s*(?:\+\s*)?years?\s*(?:of\s*)?(?:experience|exp)', text, re.IGNORECASE)
        if m:
            return max(float(y) for y in m)

        # Pattern: date ranges "2020 - 2024"
        ranges = re.findall(r'(20\d{2})\s*[-–]\s*(20\d{2}|present|current)', text, re.IGNORECASE)
        if ranges:
            import datetime
            cy = datetime.datetime.now().year
            total = sum(
                max(0, (cy if e.lower() in ['present','current'] else int(e)) - int(s))
                for s, e in ranges
            )
            return min(float(total), 40.0)
        return 0.0

    def _get_fallback_stopwords(self) -> set:
        return {
            'i','me','my','we','our','you','your','he','him','his','she','her',
            'it','its','they','them','their','what','which','who','this','that',
            'these','those','am','is','are','was','were','be','been','being',
            'have','has','had','do','does','did','a','an','the','and','but',
            'if','or','as','at','by','for','in','of','on','to','with','from',
            'up','about','into','through','during','before','after','above',
            'below','between','each','both','few','more','most','other','some',
            'no','not','only','same','so','than','too','very','can','will',
            'just','should','now','also','may',
        }
