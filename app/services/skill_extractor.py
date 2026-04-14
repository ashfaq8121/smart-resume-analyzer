# skill_extractor.py - Finds skills mentioned in resume/job description text
# Uses smart multi-word matching, not just simple keyword search.

import json
import re
from typing import Dict, List, Set
from pathlib import Path


class SkillExtractor:
    """
    Extracts skills from text by matching against a comprehensive skills database.
    
    Why is this "smart"?
    - Handles multi-word skills: "machine learning", "deep learning"
    - Case-insensitive matching
    - Handles common variations: "react.js" matches "react", "Node.js" matches "nodejs"
    - Groups skills by category
    - Deduplicates results
    """

    def __init__(self, skills_db_path: str):
        """
        Load the skills database on startup.
        
        Args:
            skills_db_path: Path to skills_db.json file
        """
        self.skills_db = self._load_skills_db(skills_db_path)
        
        # Build flattened list of all skills with their categories
        # Format: [('python', 'programming_languages'), ('react', 'web_technologies'), ...]
        self.all_skills = self._build_skills_index()
        
        # Sort by length DESCENDING so multi-word skills are matched first
        # This prevents "machine" from matching before "machine learning"
        self.all_skills.sort(key=lambda x: len(x[0]), reverse=True)

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """
        Find all skills mentioned in the text.
        
        Args:
            text: Resume or job description text
            
        Returns:
            Dictionary like:
            {
                'programming_languages': ['python', 'java'],
                'databases': ['mysql', 'mongodb'],
                'all': ['python', 'java', 'mysql', 'mongodb']  # all combined
            }
        """
        if not text:
            return {'all': []}
        
        # Normalize text for matching
        normalized_text = self._normalize_text(text)
        
        found_skills = {}      # category → list of skills
        found_set = set()      # track what we've already found (avoid duplicates)
        
        for skill, category in self.all_skills:
            # Skip if we already found this skill
            if skill in found_set:
                continue
            
            # Check if this skill appears in the text
            if self._skill_in_text(skill, normalized_text):
                # Resolve alias → canonical name for consistent reporting
                canonical = getattr(self, '_alias_map', {}).get(skill, skill)

                # Skip if the canonical form was already found via another alias
                if canonical in found_set:
                    continue

                # Add to category bucket
                if category not in found_skills:
                    found_skills[category] = []
                found_skills[category].append(canonical)
                found_set.add(canonical)
                found_set.add(skill)  # also mark this alias as done
        
        # Build 'all' list from only canonical names (exclude raw alias terms)
        # found_set contains both canonical names and alias search-terms;
        # we only want canonical names in the output.
        canonical_names = set(self._alias_map.values())  # all valid canonical names
        found_skills['all'] = sorted(s for s in found_set if s in canonical_names)
        
        return found_skills

    def extract_skills_simple(self, text: str) -> List[str]:
        """
        Simplified version that returns just a flat list of all skills found.
        Easier to use when you don't need categories.
        """
        result = self.extract_skills(text)
        return result.get('all', [])

    def get_skill_categories(self, skills_list: List[str]) -> Dict[str, List[str]]:
        """
        Given a list of skill names, return them organized by category.
        Useful when you have extracted skills and want to group them.
        """
        # Build lookup: skill → category
        skill_to_category = {skill: cat for skill, cat in self.all_skills}
        
        categorized = {}
        for skill in skills_list:
            category = skill_to_category.get(skill, 'other')
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(skill)
        
        return categorized

    # ─────────────────────────────────────────────
    # PRIVATE HELPER METHODS
    # ─────────────────────────────────────────────

    def _load_skills_db(self, path: str) -> Dict:
        """Load the JSON skills database from disk."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # If DB not found, return minimal built-in skills
            return self._get_minimal_skills_db()
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in skills database: {e}")

    def _build_skills_index(self) -> List[tuple]:
        """
        Create a flat list of (search_term, canonical_skill, category) tuples.
        
        We track:
        - search_term: what we look for in text (could be an alias)
        - canonical: the display name we report back
        - category: skill category
        
        We also build a dedup set so the same canonical skill isn't reported twice.
        Returns list of (search_term, category) but populates self._alias_map
        so alias hits resolve to canonical names.
        """
        index = []
        seen_terms = set()          # avoid duplicate search terms
        self._alias_map = {}        # alias → canonical name

        for category, skills in self.skills_db.items():
            for skill in skills:
                canonical = skill.lower()

                # Build aliases for this skill (includes canonical itself)
                aliases = self._get_skill_aliases(canonical)

                for alias in aliases:
                    if alias not in seen_terms:
                        seen_terms.add(alias)
                        index.append((alias, category))
                        # Map every alias → canonical so results are consistent
                        self._alias_map[alias] = canonical

        return index

    def _get_skill_aliases(self, skill: str) -> List[str]:
        """
        Return common variations of a skill name.
        For example: 'react' → ['react', 'reactjs', 'react.js']
        """
        aliases = [skill]
        
        # React variations
        if skill == 'react':
            aliases.extend(['reactjs', 'react.js'])
        elif skill == 'reactjs':
            aliases.extend(['react', 'react.js'])
        
        # Node.js variations
        elif skill == 'nodejs':
            aliases.extend(['node.js', 'node'])
        elif skill == 'node.js':
            aliases.extend(['nodejs', 'node'])
        
        # Vue.js variations  
        elif skill == 'vue':
            aliases.extend(['vuejs', 'vue.js'])
        
        # Next.js variations
        elif skill == 'nextjs':
            aliases.extend(['next.js'])
        
        # scikit-learn variations
        elif skill == 'scikit-learn':
            aliases.extend(['sklearn', 'scikit learn'])
        elif skill == 'sklearn':
            aliases.extend(['scikit-learn', 'scikit learn'])
        
        # PostgreSQL
        elif skill == 'postgresql':
            aliases.extend(['postgres'])
        
        # Kubernetes
        elif skill == 'kubernetes':
            aliases.extend(['k8s'])
        
        # TensorFlow
        elif skill == 'tensorflow':
            aliases.extend(['tf'])
        
        # Machine Learning abbreviations
        elif skill == 'machine learning':
            aliases.extend(['ml'])
        elif skill == 'natural language processing':
            aliases.extend(['nlp'])
        elif skill == 'deep learning':
            aliases.extend(['dl'])
        
        return aliases

    def _normalize_text(self, text: str) -> str:
        """
        Prepare text for skill matching.
        - Lowercase
        - Keep letters, numbers, dots, plus signs (for C++), hash (for C#)
        - Collapse multiple spaces
        """
        text = text.lower()
        # Keep alphanumeric + common tech characters
        text = re.sub(r'[^a-z0-9\s.#+/-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def _skill_in_text(self, skill: str, normalized_text: str) -> bool:
        """
        Check if a skill appears in text using WORD BOUNDARY matching.
        
        Why word boundaries?
        - "java" should NOT match "javascript"
        - "r" (the language) should NOT match every word with 'r'
        
        We use \b which means "word boundary" in regex.
        """
        # Special case: very short skills (1-2 chars) need exact matching
        # to avoid false positives ("r" matching everywhere)
        if len(skill) <= 2:
            escaped = re.escape(skill)
            pattern = r'(?<![a-z0-9])' + escaped + r'(?![a-z0-9])'
        elif ' ' in skill:
            # Multi-word skills: build pattern word-by-word so we can
            # insert \s+ between each word (handles varying whitespace)
            # e.g. "machine learning" → r'\bmachine\s+learning\b'
            words = skill.split()
            escaped_words = [re.escape(w) for w in words]
            pattern = r'\b' + r'\s+'.join(escaped_words) + r'\b'
        else:
            # Single word: simple word-boundary match
            escaped = re.escape(skill)
            pattern = r'\b' + escaped + r'\b'
        
        return bool(re.search(pattern, normalized_text))

    def _get_minimal_skills_db(self) -> Dict:
        """Fallback if skills_db.json is not found."""
        return {
            "programming_languages": ["python", "java", "javascript", "c++", "c#", "go", "rust", "r"],
            "web_technologies": ["html", "css", "react", "angular", "vue", "nodejs", "django", "flask"],
            "databases": ["sql", "mysql", "postgresql", "mongodb", "redis", "sqlite"],
            "cloud_devops": ["aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "linux"],
            "data_science_ml": ["machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
                               "pandas", "numpy", "scikit-learn", "data analysis"],
            "tools_practices": ["git", "github", "agile", "scrum", "jira", "postman"]
        }
