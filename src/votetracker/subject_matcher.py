"""
Subject matching utility for ClasseViva import.
Provides fuzzy matching and auto-suggestions for mapping ClasseViva subjects to VoteTracker subjects.
"""

from typing import List, Dict, Optional, Tuple


# Common subject keyword mappings (Italian/English variations)
SUBJECT_KEYWORDS = {
    "Math": ["matematica", "math", "algebra", "geometria"],
    "Italian": ["italiano", "italian", "lingua italiana"],
    "English": ["inglese", "english", "lingua inglese", "lingua e cultura inglese"],
    "History": ["storia", "history"],
    "Philosophy": ["filosofia", "philosophy"],
    "Physics": ["fisica", "physics"],
    "Science": ["scienze", "science", "scienze naturali"],
    "Chemistry": ["chimica", "chemistry"],
    "Biology": ["biologia", "biology"],
    "Latin": ["latino", "latin", "lingua latina"],
    "Greek": ["greco", "greek", "lingua greca"],
    "Art": ["arte", "art", "storia dell'arte", "disegno"],
    "Physical Education": ["educazione fisica", "physical education", "ed. fisica", "scienze motorie"],
    "Computer Science": ["informatica", "computer science", "info"],
    "Religion": ["religione", "religion", "irc"],
    "Geography": ["geografia", "geography"],
    "Spanish": ["spagnolo", "spanish", "lingua spagnola"],
    "French": ["francese", "french", "lingua francese"],
    "German": ["tedesco", "german", "lingua tedesca"],
}


def normalize_subject(subject: str) -> str:
    """Normalize subject name for comparison (lowercase, strip whitespace)."""
    return subject.lower().strip()


def find_best_match(cv_subject: str, vt_subjects: List[str]) -> Optional[Tuple[str, float]]:
    """
    Find the best matching VoteTracker subject for a ClasseViva subject.

    Args:
        cv_subject: ClasseViva subject name
        vt_subjects: List of existing VoteTracker subject names

    Returns:
        Tuple of (matched_subject, confidence) or None if no good match
        Confidence ranges from 0.0 to 1.0
    """
    cv_norm = normalize_subject(cv_subject)
    best_match = None
    best_score = 0.0

    for vt_subject in vt_subjects:
        vt_norm = normalize_subject(vt_subject)
        score = 0.0

        # Exact match
        if cv_norm == vt_norm:
            return (vt_subject, 1.0)

        # Check if one contains the other
        if cv_norm in vt_norm or vt_norm in cv_norm:
            score = 0.9

        # Check keyword matches
        for vt_keywords in SUBJECT_KEYWORDS.values():
            cv_in_keywords = any(keyword in cv_norm for keyword in vt_keywords)
            vt_in_keywords = any(keyword in vt_norm for keyword in vt_keywords)

            if cv_in_keywords and vt_in_keywords:
                score = max(score, 0.85)
                break

        # Check if VT subject is a keyword match for CV subject
        for canonical, keywords in SUBJECT_KEYWORDS.items():
            if normalize_subject(vt_subject) == normalize_subject(canonical):
                if any(keyword in cv_norm for keyword in keywords):
                    score = max(score, 0.8)
                    break

        # Simple word overlap
        cv_words = set(cv_norm.split())
        vt_words = set(vt_norm.split())
        if cv_words and vt_words:
            overlap = len(cv_words & vt_words)
            total = len(cv_words | vt_words)
            word_score = overlap / total if total > 0 else 0
            score = max(score, word_score * 0.7)

        if score > best_score:
            best_score = score
            best_match = vt_subject

    # Only return matches with confidence > 0.6
    if best_score > 0.6:
        return (best_match, best_score)

    return None


def suggest_canonical_name(cv_subject: str) -> Optional[str]:
    """
    Suggest a canonical subject name based on keywords.

    Args:
        cv_subject: ClasseViva subject name

    Returns:
        Suggested canonical name or None
    """
    cv_norm = normalize_subject(cv_subject)

    for canonical, keywords in SUBJECT_KEYWORDS.items():
        if any(keyword in cv_norm for keyword in keywords):
            return canonical

    return None


def get_auto_suggestions(cv_subject: str, vt_subjects: List[str]) -> Dict[str, any]:
    """
    Get auto-suggestion for mapping a ClasseViva subject.

    Args:
        cv_subject: ClasseViva subject name
        vt_subjects: List of existing VoteTracker subjects

    Returns:
        Dict with keys:
        - suggested_match: Best matching existing subject (or None)
        - confidence: Match confidence (0.0-1.0)
        - suggested_new: Suggested new subject name (or None)
        - action: Recommended action ("map", "create", or "manual")
    """
    result = {
        "suggested_match": None,
        "confidence": 0.0,
        "suggested_new": None,
        "action": "manual"
    }

    # Try to find existing match
    match = find_best_match(cv_subject, vt_subjects)
    if match:
        result["suggested_match"] = match[0]
        result["confidence"] = match[1]

        # High confidence - suggest mapping
        if match[1] > 0.8:
            result["action"] = "map"
        else:
            result["action"] = "manual"

    # If no good existing match, suggest creating a canonical name
    if not match or match[1] < 0.8:
        canonical = suggest_canonical_name(cv_subject)
        if canonical:
            result["suggested_new"] = canonical
            if not match or match[1] < 0.7:
                result["action"] = "create"

    return result
