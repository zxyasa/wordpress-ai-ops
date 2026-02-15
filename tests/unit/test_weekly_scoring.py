from __future__ import annotations

import pytest

from wp_ai_ops.weekly_cycle import _to_float, _normalize_rate, _parse_ctr, _score_row


# --- _to_float ---


class TestToFloat:
    def test_number(self):
        assert _to_float(42) == 42.0

    def test_string_number(self):
        assert _to_float("3.14") == 3.14

    def test_percentage_string(self):
        assert _to_float("75%") == 75.0

    def test_none(self):
        assert _to_float(None) == 0.0

    def test_empty(self):
        assert _to_float("") == 0.0

    def test_invalid(self):
        assert _to_float("abc") == 0.0

    def test_custom_default(self):
        assert _to_float(None, default=99.0) == 99.0


# --- _normalize_rate ---


class TestNormalizeRate:
    def test_percentage(self):
        assert _normalize_rate(75.0) == 0.75

    def test_already_decimal(self):
        assert _normalize_rate(0.75) == 0.75

    def test_one(self):
        # 1.0 is >= 1.0, so divides by 100
        assert _normalize_rate(1.0) == 0.01

    def test_zero(self):
        assert _normalize_rate(0.0) == 0.0


# --- _parse_ctr ---


class TestParseCtr:
    def test_decimal(self):
        assert _parse_ctr(0.02) == 0.02

    def test_percentage_string(self):
        assert _parse_ctr("2%") == 0.02

    def test_whole_number(self):
        # 5 >= 1.0 so _normalize_rate divides by 100
        assert _parse_ctr(5) == 0.05

    def test_zero(self):
        assert _parse_ctr(0) == 0.0


# --- _score_row ---


class TestScoreRow:
    def test_high_impressions_low_ctr(self):
        row = _score_row("https://example.com/a", {"impressions": 500, "ctr": 0.01}, {})
        assert "high_impressions_low_ctr" in row.reasons
        assert row.score >= 3

    def test_rank_5_15(self):
        row = _score_row("https://example.com/a", {"position": 10}, {})
        assert "rank_5_15" in row.reasons
        assert row.score >= 2

    def test_high_bounce(self):
        row = _score_row("https://example.com/a", {}, {"bounce_rate": 0.80})
        assert "high_bounce" in row.reasons
        assert row.score >= 2

    def test_combined_all(self):
        row = _score_row(
            "https://example.com/a",
            {"impressions": 500, "ctr": 0.01, "position": 10},
            {"bounce_rate": 0.80},
        )
        assert row.score == 7  # 3 + 2 + 2
        assert len(row.reasons) == 3

    def test_zero_score(self):
        row = _score_row(
            "https://example.com/a",
            {"impressions": 10, "ctr": 0.10, "position": 1},
            {"bounce_rate": 0.30},
        )
        assert row.score == 0
        assert row.reasons == []

    # Boundary value tests
    def test_boundary_impressions_exactly_100_ctr_exactly_002(self):
        row = _score_row("https://example.com/a", {"impressions": 100, "ctr": 0.02}, {})
        assert "high_impressions_low_ctr" in row.reasons

    def test_boundary_position_exactly_5(self):
        row = _score_row("https://example.com/a", {"position": 5}, {})
        assert "rank_5_15" in row.reasons

    def test_boundary_position_exactly_15(self):
        row = _score_row("https://example.com/a", {"position": 15}, {})
        assert "rank_5_15" in row.reasons

    def test_boundary_bounce_exactly_070(self):
        row = _score_row("https://example.com/a", {}, {"bounce_rate": 0.70})
        assert "high_bounce" in row.reasons

    def test_boundary_impressions_99_no_trigger(self):
        row = _score_row("https://example.com/a", {"impressions": 99, "ctr": 0.01}, {})
        assert "high_impressions_low_ctr" not in row.reasons

    def test_boundary_position_4_no_trigger(self):
        row = _score_row("https://example.com/a", {"position": 4}, {})
        assert "rank_5_15" not in row.reasons

    def test_boundary_position_16_no_trigger(self):
        row = _score_row("https://example.com/a", {"position": 16}, {})
        assert "rank_5_15" not in row.reasons

    def test_boundary_bounce_069_no_trigger(self):
        row = _score_row("https://example.com/a", {}, {"bounce_rate": 0.69})
        assert "high_bounce" not in row.reasons
