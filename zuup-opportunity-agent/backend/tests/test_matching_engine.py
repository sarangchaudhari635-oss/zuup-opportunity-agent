"""
Unit tests for the Matching Engine.
Tests hard filters, semantic scoring bonuses, and pipeline logic.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from app.services.matching_engine import (
    compute_semantic_score,
    passes_hard_filters,
)


def make_profile(**kwargs):
    p = MagicMock()
    p.id = uuid4()
    p.nationality = kwargs.get("nationality", "Nepali")
    p.citizenship = kwargs.get("citizenship", ["Nepal"])
    p.gpa = kwargs.get("gpa", 3.5)
    p.gpa_scale = 4.0
    p.enrollment_status = kwargs.get("enrollment_status", "enrolled")
    p.field_of_study = kwargs.get("field_of_study", "computer science")
    p.skills = kwargs.get("skills", ["Python", "Machine Learning"])
    p.location = kwargs.get("location", "Kathmandu, Nepal")
    p.embedding = kwargs.get("embedding", [0.1] * 1536)
    p.career_goals = kwargs.get("career_goals", "AI research")
    return p


def make_opportunity(**kwargs):
    o = MagicMock()
    o.id = uuid4()
    o.title = kwargs.get("title", "Test Fellowship")
    o.organization = kwargs.get("organization", "Test Org")
    o.description = kwargs.get("description", "A great opportunity for computer science students interested in Python and Machine Learning.")
    o.type = "fellowship"
    o.deadline = kwargs.get("deadline", datetime.now(timezone.utc) + timedelta(days=30))
    o.remote_eligible = kwargs.get("remote_eligible", False)
    o.location = kwargs.get("location", "Kathmandu, Nepal")
    o.created_at = kwargs.get("created_at", datetime.now(timezone.utc) - timedelta(hours=10))
    o.embedding = kwargs.get("embedding", [0.1] * 1536)
    return o


def make_eligibility(**kwargs):
    e = MagicMock()
    e.nationality = kwargs.get("nationality", [])
    e.citizenship_required = kwargs.get("citizenship_required", [])
    e.gpa_min = kwargs.get("gpa_min", None)
    e.gpa_scale = kwargs.get("gpa_scale", 4.0)
    e.enrollment_status = kwargs.get("enrollment_status", [])
    e.field_of_study = kwargs.get("field_of_study", [])
    return e


# ─────────────────────────────────────────────────────────────
# Hard Filter Tests
# ─────────────────────────────────────────────────────────────

class TestHardFilters:

    def test_passes_when_no_eligibility(self):
        profile = make_profile()
        opp = make_opportunity()
        assert passes_hard_filters(profile, opp, None) is True

    def test_rejects_expired_opportunity(self):
        profile = make_profile()
        opp = make_opportunity(deadline=datetime.now(timezone.utc) + timedelta(hours=10))  # < 48h
        assert passes_hard_filters(profile, opp, None) is False

    def test_passes_future_deadline(self):
        profile = make_profile()
        opp = make_opportunity(deadline=datetime.now(timezone.utc) + timedelta(days=10))
        assert passes_hard_filters(profile, opp, None) is True

    def test_rejects_wrong_nationality(self):
        profile = make_profile(nationality="Indian")
        opp = make_opportunity()
        elig = make_eligibility(nationality=["American", "British"])
        assert passes_hard_filters(profile, opp, elig) is False

    def test_passes_matching_nationality(self):
        profile = make_profile(nationality="Nepali")
        opp = make_opportunity()
        elig = make_eligibility(nationality=["nepali", "Kenyan"])
        assert passes_hard_filters(profile, opp, elig) is True

    def test_rejects_gpa_below_minimum(self):
        profile = make_profile(gpa=2.5)
        opp = make_opportunity()
        elig = make_eligibility(gpa_min=3.0)
        assert passes_hard_filters(profile, opp, elig) is False

    def test_passes_gpa_above_minimum(self):
        profile = make_profile(gpa=3.7)
        opp = make_opportunity()
        elig = make_eligibility(gpa_min=3.0)
        assert passes_hard_filters(profile, opp, elig) is True

    def test_rejects_wrong_enrollment_status(self):
        profile = make_profile(enrollment_status="graduated")
        opp = make_opportunity()
        elig = make_eligibility(enrollment_status=["enrolled"])
        assert passes_hard_filters(profile, opp, elig) is False

    def test_rejects_wrong_field_of_study(self):
        profile = make_profile(field_of_study="law")
        opp = make_opportunity()
        elig = make_eligibility(field_of_study=["computer science", "engineering"])
        assert passes_hard_filters(profile, opp, elig) is False

    def test_passes_partial_field_match(self):
        profile = make_profile(field_of_study="computer science and engineering")
        opp = make_opportunity()
        elig = make_eligibility(field_of_study=["computer science"])
        assert passes_hard_filters(profile, opp, elig) is True

    def test_passes_open_eligibility(self):
        profile = make_profile()
        opp = make_opportunity()
        elig = make_eligibility()  # All empty arrays = open to all
        assert passes_hard_filters(profile, opp, elig) is True


# ─────────────────────────────────────────────────────────────
# Semantic Scoring Tests
# ─────────────────────────────────────────────────────────────

class TestSemanticScoring:

    def test_skill_bonus_applied(self):
        profile = make_profile(skills=["Python", "Machine Learning"])
        opp = make_opportunity(
            description="A fellowship for students with Python and Machine Learning skills.",
            created_at=datetime.now(timezone.utc) - timedelta(days=5),  # no recency bonus
        )
        opp.embedding = [0.5] * 1536
        profile.embedding = [0.5] * 1536
        score, breakdown = compute_semantic_score(profile, opp)
        assert breakdown["skill_bonus"] == 10.0  # 2 skills × 5

    def test_skill_bonus_capped_at_20(self):
        profile = make_profile(skills=["Python", "ML", "React", "Django", "SQL", "Java"])
        opp = make_opportunity(description="Opportunity for Python ML React Django SQL Java developers.")
        score, breakdown = compute_semantic_score(profile, opp)
        assert breakdown["skill_bonus"] <= 20.0

    def test_recency_bonus_for_new_opportunity(self):
        profile = make_profile()
        opp = make_opportunity(created_at=datetime.now(timezone.utc) - timedelta(hours=10))
        score, breakdown = compute_semantic_score(profile, opp)
        assert breakdown["recency_bonus"] == 10.0

    def test_no_recency_bonus_for_old_opportunity(self):
        profile = make_profile()
        opp = make_opportunity(created_at=datetime.now(timezone.utc) - timedelta(days=5))
        score, breakdown = compute_semantic_score(profile, opp)
        assert breakdown["recency_bonus"] == 0.0

    def test_location_bonus_for_matching_location(self):
        profile = make_profile(location="Kathmandu, Nepal")
        opp = make_opportunity(
            location="Kathmandu",
            remote_eligible=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=5),
        )
        score, breakdown = compute_semantic_score(profile, opp)
        assert breakdown["location_bonus"] == 5.0

    def test_location_bonus_for_remote(self):
        profile = make_profile(location="Kathmandu")
        opp = make_opportunity(remote_eligible=True, location="Online")
        score, breakdown = compute_semantic_score(profile, opp)
        assert breakdown["location_bonus"] == 5.0

    def test_score_capped_at_100(self):
        # Perfect cosine similarity + all bonuses should not exceed 100
        profile = make_profile(skills=["A", "B", "C", "D", "E"])
        profile.embedding = [1.0] + [0.0] * 1535
        opp = make_opportunity(
            description="A B C D E F G H I J",
            created_at=datetime.now(timezone.utc) - timedelta(hours=5),
            remote_eligible=True,
        )
        opp.embedding = [1.0] + [0.0] * 1535
        score, _ = compute_semantic_score(profile, opp)
        assert score <= 100.0

    def test_no_embedding_gives_zero_semantic(self):
        profile = make_profile(embedding=None)
        opp = make_opportunity(embedding=None)
        profile.embedding = None
        opp.embedding = None
        score, breakdown = compute_semantic_score(profile, opp)
        assert breakdown["semantic_score"] == 0.0
