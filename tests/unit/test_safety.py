from __future__ import annotations

import pytest

from wp_ai_ops.exceptions import SafetyViolationError
from wp_ai_ops.models import ContentSpec, Operation, SafetySpec, SelectorSpec
from wp_ai_ops.safety import (
    apply_operation_to_content,
    apply_slot_replace,
    ensure_slot_markers,
    validate_content_change,
    _apply_regex_op,
)


# --- apply_slot_replace ---


class TestApplySlotReplace:
    def test_both_markers(self, sample_html_with_slots):
        result = apply_slot_replace(sample_html_with_slots, "AI_SLOT:INTRO", "<p>New</p>")
        assert "<!-- AI_SLOT:INTRO -->" in result
        assert "<!-- /AI_SLOT:INTRO -->" in result
        assert "<p>New</p>" in result
        assert "<p>Old intro</p>" not in result

    def test_only_start_marker(self):
        content = "<h1>Hi</h1>\n<!-- AI_SLOT:INTRO -->\n<p>Rest</p>"
        result = apply_slot_replace(content, "AI_SLOT:INTRO", "<p>Inserted</p>")
        assert "<!-- AI_SLOT:INTRO -->" in result
        assert "<!-- /AI_SLOT:INTRO -->" in result
        assert "<p>Inserted</p>" in result

    def test_missing_markers_raises(self):
        content = "<h1>No slots</h1>"
        with pytest.raises(SafetyViolationError, match="Missing AI slot marker"):
            apply_slot_replace(content, "AI_SLOT:INTRO", "<p>New</p>")

    def test_multiline_slot_content(self):
        content = (
            "<!-- AI_SLOT:INTRO -->\n"
            "<p>Line 1</p>\n"
            "<p>Line 2</p>\n"
            "<!-- /AI_SLOT:INTRO -->"
        )
        result = apply_slot_replace(content, "AI_SLOT:INTRO", "<p>Replaced</p>")
        assert "<p>Replaced</p>" in result
        assert "<p>Line 1</p>" not in result
        assert "<p>Line 2</p>" not in result


# --- ensure_slot_markers ---


class TestEnsureSlotMarkers:
    def test_add_missing_slots(self):
        content = "<h1>Hello</h1>"
        result = ensure_slot_markers(content, ["AI_SLOT:INTRO", "AI_SLOT:FAQ"])
        assert "<!-- AI_SLOT:INTRO -->" in result
        assert "<!-- /AI_SLOT:INTRO -->" in result
        assert "<!-- AI_SLOT:FAQ -->" in result
        assert "<!-- /AI_SLOT:FAQ -->" in result

    def test_noop_when_all_present(self, sample_html_with_slots):
        result = ensure_slot_markers(sample_html_with_slots, ["AI_SLOT:INTRO"])
        assert result == sample_html_with_slots

    def test_partial_start_only(self):
        content = "<h1>Hello</h1>\n<!-- AI_SLOT:INTRO -->"
        result = ensure_slot_markers(content, ["AI_SLOT:INTRO"])
        assert "<!-- AI_SLOT:INTRO -->" in result
        assert "<!-- /AI_SLOT:INTRO -->" in result

    def test_partial_end_only(self):
        content = "<h1>Hello</h1>\n<!-- /AI_SLOT:INTRO -->"
        result = ensure_slot_markers(content, ["AI_SLOT:INTRO"])
        assert "<!-- AI_SLOT:INTRO -->" in result
        assert "<!-- /AI_SLOT:INTRO -->" in result


# --- _apply_regex_op ---


class TestApplyRegexOp:
    def _make_op(self, op_type, pattern, value):
        return Operation(
            op=op_type,
            scope="content",
            selector=SelectorSpec(kind="regex", value=pattern),
            content=ContentSpec(format="html", value=value),
            safety=SafetySpec(),
        )

    def test_replace(self):
        result = _apply_regex_op("Hello world", self._make_op("replace", "world", "earth"))
        assert result == "Hello earth"

    def test_append(self):
        result = _apply_regex_op("Hello world", self._make_op("append", "Hello", " dear"))
        assert result == "Hello dear world"

    def test_prepend(self):
        result = _apply_regex_op("Hello world", self._make_op("prepend", "world", "big "))
        assert result == "Hello big world"

    def test_invalid_regex(self):
        with pytest.raises(SafetyViolationError, match="Invalid regex"):
            _apply_regex_op("Hello", self._make_op("replace", "[invalid", "x"))

    def test_no_match(self):
        with pytest.raises(SafetyViolationError, match="did not match"):
            _apply_regex_op("Hello", self._make_op("replace", "missing", "x"))


# --- apply_operation_to_content ---


class TestApplyOperationToContent:
    def test_html_comment_replace(self, sample_html_with_slots):
        op = Operation(
            op="replace",
            scope="content",
            selector=SelectorSpec(kind="html_comment", value="AI_SLOT:INTRO"),
            content=ContentSpec(format="html", value="<p>New</p>"),
            safety=SafetySpec(),
        )
        after, diff = apply_operation_to_content(sample_html_with_slots, op)
        assert "<p>New</p>" in after
        assert "<p>Old intro</p>" not in after
        assert diff  # diff should be non-empty

    def test_html_comment_append(self, sample_html_with_slots):
        op = Operation(
            op="append",
            scope="content",
            selector=SelectorSpec(kind="html_comment", value="AI_SLOT:INTRO"),
            content=ContentSpec(format="html", value="<p>Appended</p>"),
            safety=SafetySpec(),
        )
        after, diff = apply_operation_to_content(sample_html_with_slots, op)
        assert "<p>Old intro</p>" in after
        assert "<p>Appended</p>" in after

    def test_html_comment_prepend(self, sample_html_with_slots):
        op = Operation(
            op="prepend",
            scope="content",
            selector=SelectorSpec(kind="html_comment", value="AI_SLOT:INTRO"),
            content=ContentSpec(format="html", value="<p>Prepended</p>"),
            safety=SafetySpec(),
        )
        after, diff = apply_operation_to_content(sample_html_with_slots, op)
        assert "<p>Old intro</p>" in after
        assert "<p>Prepended</p>" in after

    def test_regex_op(self):
        content = "<p>Hello world</p>"
        op = Operation(
            op="replace",
            scope="content",
            selector=SelectorSpec(kind="regex", value="Hello"),
            content=ContentSpec(format="html", value="Hi"),
            safety=SafetySpec(),
        )
        after, diff = apply_operation_to_content(content, op)
        assert after == "<p>Hi world</p>"

    def test_ensure_slots_with_list(self):
        content = "<h1>Hello</h1>"
        op = Operation(
            op="ensure_slots",
            scope="content",
            selector=SelectorSpec(),
            content=ContentSpec(format="json", value=["AI_SLOT:NEW"]),
            safety=SafetySpec(),
        )
        after, diff = apply_operation_to_content(content, op)
        assert "<!-- AI_SLOT:NEW -->" in after
        assert "<!-- /AI_SLOT:NEW -->" in after

    def test_ensure_slots_with_dict(self):
        content = "<h1>Hello</h1>"
        op = Operation(
            op="ensure_slots",
            scope="content",
            selector=SelectorSpec(),
            content=ContentSpec(format="json", value={"slots": ["AI_SLOT:NEW"]}),
            safety=SafetySpec(),
        )
        after, diff = apply_operation_to_content(content, op)
        assert "<!-- AI_SLOT:NEW -->" in after

    def test_unsupported_op(self, sample_html_with_slots):
        op = Operation(
            op="delete",
            scope="content",
            selector=SelectorSpec(),
            content=ContentSpec(format="html", value=""),
            safety=SafetySpec(),
        )
        with pytest.raises(SafetyViolationError, match="Unsupported content op"):
            apply_operation_to_content(sample_html_with_slots, op)

    def test_unsupported_selector_kind(self, sample_html_with_slots):
        op = Operation(
            op="replace",
            scope="content",
            selector=SelectorSpec(kind="xpath", value="//p"),
            content=ContentSpec(format="html", value=""),
            safety=SafetySpec(),
        )
        with pytest.raises(SafetyViolationError, match="Unsupported selector.kind"):
            apply_operation_to_content(sample_html_with_slots, op)


# --- validate_content_change ---


class TestValidateContentChange:
    def _make_op(self, max_chars=2000, forbid_remove=None, allow_full_replace=False):
        return Operation(
            op="replace",
            scope="content",
            selector=SelectorSpec(kind="html_comment", value="AI_SLOT:INTRO"),
            content=ContentSpec(format="html", value=""),
            safety=SafetySpec(
                max_chars_change=max_chars,
                forbid_remove=forbid_remove or [],
                allow_full_replace=allow_full_replace,
            ),
        )

    def test_pass(self):
        before = "<!-- AI_SLOT:INTRO --><p>old</p><!-- /AI_SLOT:INTRO -->"
        after = "<!-- AI_SLOT:INTRO --><p>new</p><!-- /AI_SLOT:INTRO -->"
        validate_content_change(before, after, self._make_op())

    def test_chars_delta_exceeded(self):
        with pytest.raises(SafetyViolationError, match="chars changed"):
            validate_content_change("a", "a" * 3000, self._make_op(max_chars=100))

    def test_forbid_remove_lost(self):
        with pytest.raises(SafetyViolationError, match="forbid_remove token lost"):
            validate_content_change(
                "keep ux_banner here",
                "keep here",
                self._make_op(forbid_remove=["ux_banner"]),
            )

    def test_slot_marker_lost(self):
        before = "<!-- AI_SLOT:INTRO -->\n<p>Old</p>\n<!-- /AI_SLOT:INTRO -->"
        after = "<p>Replaced everything</p>"
        with pytest.raises(SafetyViolationError, match="slot marker missing"):
            validate_content_change(before, after, self._make_op(allow_full_replace=False))
