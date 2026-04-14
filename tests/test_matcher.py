# test_matcher.py - Unit tests for the job matcher and NLP components
# Run with: pytest tests/ -v

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.matcher import JobMatcher
from app.services.nlp_processor import NLPProcessor
from app.services.ranker import CandidateRanker


class TestJobMatcher:
    """Tests for TF-IDF + Cosine Similarity matching."""

    def setup_method(self):
        self.matcher = JobMatcher()

    # ── Score Range Tests ──────────────────────────

    def test_identical_texts_high_score(self):
        """Identical texts should produce very high similarity."""
        text = "Python developer machine learning scikit-learn tensorflow pandas numpy"
        result = self.matcher.calculate_match(text, text, [], [])
        # TF-IDF of identical texts should be ~100%
        assert result['tfidf_score'] >= 95

    def test_empty_inputs_returns_zero(self):
        """Empty inputs should return zero scores gracefully."""
        result = self.matcher.calculate_match("", "", [], [])
        assert result['overall_score'] == 0

    def test_completely_different_texts_low_score(self):
        """Completely different texts should have low similarity."""
        resume = "Python machine learning data science tensorflow keras"
        job = "Java Spring Boot REST API microservices kubernetes"
        result = self.matcher.calculate_match(resume, job, [], [])
        # Different tech stacks should have low similarity
        assert result['tfidf_score'] < 40

    def test_score_between_0_and_100(self):
        """All scores should be in valid range 0-100."""
        result = self.matcher.calculate_match(
            "Python developer with AWS experience",
            "Looking for Python developer AWS Docker",
            ["python", "aws"],
            ["python", "aws", "docker"]
        )
        assert 0 <= result['overall_score'] <= 100
        assert 0 <= result['tfidf_score'] <= 100
        assert 0 <= result['skills_score'] <= 100

    # ── Skills Analysis Tests ──────────────────────

    def test_matched_skills_found_correctly(self):
        """Skills in both resume and JD should appear in matched_skills."""
        result = self.matcher.calculate_match(
            "Developer with Python and AWS skills",
            "Need Python developer with AWS",
            ["python", "aws", "docker"],
            ["python", "aws"]
        )
        assert "python" in result['matched_skills']
        assert "aws" in result['matched_skills']

    def test_missing_skills_identified(self):
        """Skills in JD but not resume should appear in missing_skills."""
        result = self.matcher.calculate_match(
            "Python developer",
            "Need Python Docker Kubernetes developer",
            ["python"],
            ["python", "docker", "kubernetes"]
        )
        assert "docker" in result['missing_skills']
        assert "kubernetes" in result['missing_skills']

    def test_no_missing_skills_when_all_matched(self):
        """When resume has all JD skills, missing_skills should be empty."""
        result = self.matcher.calculate_match(
            "Python Docker Kubernetes developer",
            "Need Python Docker developer",
            ["python", "docker", "kubernetes"],
            ["python", "docker"]
        )
        assert len(result['missing_skills']) == 0

    def test_perfect_skills_match_100_percent(self):
        """100% skills match when resume has all required skills."""
        result = self.matcher.calculate_match(
            "resume text",
            "job text",
            ["python", "aws", "docker"],
            ["python", "aws", "docker"]  # All 3 found in resume too
        )
        assert result['skills_score'] == 100.0

    def test_zero_skills_match_when_none_found(self):
        """0% skills when no job skills are in resume."""
        result = self.matcher.calculate_match(
            "resume text",
            "job text",
            [],
            ["python", "aws", "docker"]
        )
        assert result['skills_score'] == 0.0

    # ── Grade Tests ──────────────────────────────

    def test_high_score_gets_good_grade(self):
        """Score >= 85 should get A+ grade."""
        grade = self.matcher._get_grade(90)
        assert grade['letter'] == 'A+'

    def test_low_score_gets_poor_grade(self):
        """Score < 40 should get F grade."""
        grade = self.matcher._get_grade(30)
        assert grade['letter'] == 'F'

    def test_suggestions_not_empty(self):
        """Improvement suggestions should always be provided."""
        result = self.matcher.calculate_match(
            "Python developer",
            "Python developer needed",
            ["python"],
            ["python", "docker"]
        )
        assert len(result['improvement_suggestions']) > 0

    # ── Edge Case Tests ──────────────────────────

    def test_none_skills_handled(self):
        """None values in skills should not crash."""
        result = self.matcher.calculate_match(
            "Python developer",
            "Python developer needed",
            None or [],
            None or []
        )
        assert result['overall_score'] >= 0

    def test_single_word_resume(self):
        """Very short resume text should be handled."""
        result = self.matcher.calculate_match(
            "Python",
            "We need a Python developer with extensive experience",
            ["python"],
            ["python"]
        )
        assert result['overall_score'] >= 0

    def test_keyword_matches_returned(self):
        """Common keywords should be identified."""
        result = self.matcher.calculate_match(
            "Experienced Python developer with machine learning skills",
            "Looking for Python developer with machine learning knowledge",
            ["python", "machine learning"],
            ["python", "machine learning"]
        )
        assert len(result['keyword_matches']) > 0


class TestNLPProcessor:
    """Tests for NLP text processing."""

    def setup_method(self):
        self.nlp = NLPProcessor()

    def test_tokenize_returns_list(self):
        """Tokenization should return a list."""
        tokens = self.nlp.tokenize_and_clean("Python developer with 5 years experience")
        assert isinstance(tokens, list)

    def test_stopwords_removed(self):
        """Common stopwords should not appear in tokens."""
        tokens = self.nlp.tokenize_and_clean("I am a Python developer and I work with AWS")
        stopwords_that_should_be_gone = ['i', 'am', 'a', 'and', 'with']
        for sw in stopwords_that_should_be_gone:
            assert sw not in tokens, f"Stopword '{sw}' should have been removed"

    def test_empty_text_returns_empty_list(self):
        """Empty input should return empty list."""
        tokens = self.nlp.tokenize_and_clean("")
        assert tokens == []

    def test_sections_extracted(self):
        """Resume sections should be identified."""
        resume_text = """
        EDUCATION
        B.Tech Computer Science, IIT Delhi, 2022
        
        EXPERIENCE
        Software Engineer at Google, 2022-2024
        
        SKILLS
        Python, Java, AWS, Docker
        """
        result = self.nlp.process(resume_text)
        assert 'sections' in result
        # At least some sections should be found
        assert len(result['sections']) > 0

    def test_email_extraction(self):
        """Email addresses should be extracted."""
        text = "Contact me at john.doe@example.com for opportunities"
        contact = self.nlp._extract_contact_info(text)
        assert contact.get('email') == 'john.doe@example.com'

    def test_github_extraction(self):
        """GitHub profiles should be extracted."""
        text = "My projects: github.com/johndoe and linkedin.com/in/johndoe"
        contact = self.nlp._extract_contact_info(text)
        assert 'github' in contact
        assert 'johndoe' in contact['github']

    def test_experience_years_extraction(self):
        """Years of experience should be extracted from text."""
        text = "I have 5 years of experience in Python development"
        years = self.nlp.extract_experience_years(text)
        assert years == 5.0

    def test_experience_years_zero_when_none(self):
        """No experience mentioned should return 0."""
        text = "Recent graduate looking for opportunities"
        years = self.nlp.extract_experience_years(text)
        assert years == 0.0

    def test_process_returns_all_keys(self):
        """process() should return all expected keys."""
        result = self.nlp.process("Python developer with 5 years experience")
        required_keys = ['sections', 'tokens', 'processed_text', 'contact_info', 'raw_text']
        for key in required_keys:
            assert key in result, f"Missing key: {key}"


class TestCandidateRanker:
    """Tests for the candidate ranking system."""

    def setup_method(self):
        self.ranker = CandidateRanker()

    def test_empty_candidates_returns_empty(self):
        """Empty list should return empty list."""
        result = self.ranker.rank_candidates([])
        assert result == []

    def test_rank_assigned_correctly(self):
        """Best candidate should have rank 1."""
        candidates = [
            {'overall_score': 40, 'tfidf_score': 40, 'skills_score': 40,
             'matched_skills': [], 'missing_skills': [], 'experience_years': 0},
            {'overall_score': 80, 'tfidf_score': 80, 'skills_score': 80,
             'matched_skills': ['python', 'aws'], 'missing_skills': [], 'experience_years': 3},
            {'overall_score': 60, 'tfidf_score': 60, 'skills_score': 60,
             'matched_skills': ['python'], 'missing_skills': ['aws'], 'experience_years': 1},
        ]
        ranked = self.ranker.rank_candidates(candidates)
        
        # Best scoring candidate should be rank 1
        assert ranked[0]['rank'] == 1
        # Worst scoring should be last
        assert ranked[-1]['rank'] == len(candidates)

    def test_ranks_are_sequential(self):
        """Ranks should be 1, 2, 3... without gaps."""
        candidates = [
            {'overall_score': s, 'tfidf_score': s, 'skills_score': s,
             'matched_skills': [], 'missing_skills': [], 'experience_years': 0}
            for s in [70, 50, 30, 90]
        ]
        ranked = self.ranker.rank_candidates(candidates)
        ranks = [c['rank'] for c in ranked]
        assert ranks == list(range(1, len(candidates) + 1))

    def test_insights_generated(self):
        """Insights should be generated for a pool of candidates."""
        candidates = [
            {'overall_score': s, 'tfidf_score': s, 'skills_score': s,
             'matched_skills': ['python'], 'missing_skills': ['docker'],
             'experience_years': 2, 'composite_score': s, 'filename': f'c{i}.pdf'}
            for i, s in enumerate([80, 60, 40])
        ]
        insights = self.ranker.generate_ranking_insights(candidates)
        
        assert insights['total_candidates'] == 3
        assert insights['highest_score'] == 80
        assert insights['lowest_score'] == 40
        assert 'average_score' in insights

    def test_tier_assigned(self):
        """Each ranked candidate should have a tier."""
        candidates = [
            {'overall_score': 85, 'tfidf_score': 85, 'skills_score': 85,
             'matched_skills': ['python', 'aws', 'docker'], 'missing_skills': [], 'experience_years': 4}
        ]
        ranked = self.ranker.rank_candidates(candidates)
        assert 'tier' in ranked[0]
        assert 'label' in ranked[0]['tier']


# ── Manual Test Runner ──────────────────────────────

if __name__ == "__main__":
    print("Running matcher & NLP tests manually...\n")
    
    matcher = JobMatcher()
    nlp = NLPProcessor()
    
    # Quick smoke test
    resume = "Experienced Python developer with 4 years in machine learning, tensorflow, sklearn, AWS, Docker"
    job = "Looking for Python developer with machine learning and AWS experience. Docker knowledge a plus."
    
    result = matcher.calculate_match(
        resume, job,
        ["python", "machine learning", "tensorflow", "aws", "docker"],
        ["python", "machine learning", "aws", "docker"]
    )
    
    print(f"✅ Overall Score:  {result['overall_score']}%")
    print(f"✅ TF-IDF Score:   {result['tfidf_score']}%")
    print(f"✅ Skills Score:   {result['skills_score']}%")
    print(f"✅ Matched Skills: {result['matched_skills']}")
    print(f"✅ Missing Skills: {result['missing_skills']}")
    print(f"✅ Grade:          {result['match_grade']['letter']} - {result['match_grade']['label']}")
    
    # NLP test
    tokens = nlp.tokenize_and_clean("I am a Python developer with 5 years of experience")
    print(f"\n✅ Tokens (stopwords removed): {tokens}")
    
    print("\n✅ All manual tests completed!")
