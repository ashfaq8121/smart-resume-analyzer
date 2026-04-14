# ranker.py - Ranks multiple resumes against a single job description
# This is the "hiring manager view" - which candidate is best?

from typing import Dict, List
import re


class CandidateRanker:
    """
    Ranks multiple candidates by combining:
    1. TF-IDF match score (50%) - overall content similarity
    2. Skills match score (35%) - how many required skills they have
    3. Experience bonus (15%) - years of experience (if detectable)
    
    Returns a sorted leaderboard from best to worst fit.
    """

    def rank_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """
        Given a list of match results (one per resume), sort them from best to worst.
        
        Each candidate dict has:
        - filename: name of the uploaded resume file
        - overall_score: match percentage
        - tfidf_score: TF-IDF similarity
        - skills_score: skill match percentage
        - matched_skills: list of matched skills
        - missing_skills: list of missing skills
        
        Returns same list, sorted by overall_score descending, with rank added.
        """
        if not candidates:
            return []
        
        # Calculate composite score for each candidate
        scored_candidates = []
        for candidate in candidates:
            composite = self._compute_composite_score(candidate)
            candidate_copy = dict(candidate)
            candidate_copy['composite_score'] = round(composite, 1)
            scored_candidates.append(candidate_copy)
        
        # Sort by composite score (highest first = best match)
        scored_candidates.sort(key=lambda x: x['composite_score'], reverse=True)
        
        # Add rank and tier label to each candidate
        for i, candidate in enumerate(scored_candidates):
            candidate['rank'] = i + 1
            candidate['tier'] = self._get_tier(candidate['composite_score'], i, len(scored_candidates))
        
        return scored_candidates

    def _compute_composite_score(self, candidate: Dict) -> float:
        """
        Calculate final score from multiple signals.
        
        Formula:
        composite = (tfidf_score × 0.50) + (skills_score × 0.35) + (experience_bonus × 0.15)
        
        Why these weights?
        - TF-IDF: captures overall language match (most important)
        - Skills: technical skills are crucial for most jobs
        - Experience: bonus for having relevant experience
        """
        tfidf_score = candidate.get('tfidf_score', 0)
        skills_score = candidate.get('skills_score', 0)
        
        # Experience bonus: 0-100 based on years detected
        experience_years = candidate.get('experience_years', 0)
        experience_bonus = min(experience_years * 10, 100)  # 10 points per year, max 100
        
        # Weighted composite
        composite = (
            tfidf_score * 0.50 +
            skills_score * 0.35 +
            experience_bonus * 0.15
        )
        
        # Skill depth bonus: reward candidates with MORE matched skills
        matched_count = len(candidate.get('matched_skills', []))
        if matched_count > 5:
            composite += min((matched_count - 5) * 0.5, 5)  # Small bonus, max +5 points
        
        return min(composite, 100)  # Cap at 100

    def _get_tier(self, score: float, rank: int, total: int) -> Dict:
        """
        Assign a tier label based on score AND relative rank.
        - Top performer in the pool gets special treatment
        """
        if score >= 80:
            return {'label': '🥇 Top Candidate', 'color': '#f59e0b', 'bg': '#fef3c7'}
        elif score >= 65 or (rank == 0 and total > 1):
            return {'label': '🥈 Strong Candidate', 'color': '#6366f1', 'bg': '#eef2ff'}
        elif score >= 50:
            return {'label': '🥉 Good Candidate', 'color': '#3b82f6', 'bg': '#eff6ff'}
        elif score >= 35:
            return {'label': '⚠️ Partial Match', 'color': '#f97316', 'bg': '#fff7ed'}
        else:
            return {'label': '❌ Weak Match', 'color': '#ef4444', 'bg': '#fef2f2'}

    def generate_ranking_insights(self, ranked_candidates: List[Dict]) -> Dict:
        """
        Generate summary insights about the entire candidate pool.
        Useful for the dashboard overview section.
        """
        if not ranked_candidates:
            return {}
        
        scores = [c.get('composite_score', 0) for c in ranked_candidates]
        all_matched_skills = []
        all_missing_skills = []
        
        for c in ranked_candidates:
            all_matched_skills.extend(c.get('matched_skills', []))
            all_missing_skills.extend(c.get('missing_skills', []))
        
        # Find skills that MOST candidates are missing
        # (These are the rarest/most sought-after skills)
        missing_counts = {}
        for skill in all_missing_skills:
            missing_counts[skill] = missing_counts.get(skill, 0) + 1
        
        commonly_missing = sorted(
            missing_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_candidates': len(ranked_candidates),
            'average_score': round(sum(scores) / len(scores), 1),
            'highest_score': round(max(scores), 1),
            'lowest_score': round(min(scores), 1),
            'top_candidate': ranked_candidates[0].get('filename', 'Unknown'),
            'commonly_missing_skills': [skill for skill, count in commonly_missing],
            'score_distribution': {
                'excellent': sum(1 for s in scores if s >= 80),
                'good': sum(1 for s in scores if 60 <= s < 80),
                'fair': sum(1 for s in scores if 40 <= s < 60),
                'poor': sum(1 for s in scores if s < 40),
            }
        }
