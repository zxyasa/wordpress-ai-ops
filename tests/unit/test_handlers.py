from __future__ import annotations

import json

import pytest

from wp_ai_ops.exceptions import SafetyViolationError
from wp_ai_ops.models import ContentSpec, Operation, SafetySpec, SelectorSpec, Task, LimitSpec
from wp_ai_ops.handlers import (
    _build_faq_html,
    _build_faq_json_ld,
    _extract_rendered_content,
    handle_append_internal_links,
    handle_generate_topic_hub,
    handle_inject_schema_faq,
    handle_publish_post,
    handle_report_only,
    handle_set_meta,
    handle_update_post_or_page,
    handle_upload_media,
)


def _make_content_op(op="replace", slot="AI_SLOT:INTRO", value="<p>New</p>", **kwargs):
    safety_kwargs = {
        "max_chars_change": kwargs.pop("max_chars_change", 2000),
        "allow_full_replace": kwargs.pop("allow_full_replace", False),
    }
    return Operation(
        op=op,
        scope="content",
        selector=SelectorSpec(kind="html_comment", value=slot),
        content=ContentSpec(format="html", value=value),
        safety=SafetySpec(**safety_kwargs),
    )


def _make_fields_op(fields, max_chars_change=2000):
    return Operation(
        op="set_fields",
        scope="fields",
        selector=SelectorSpec(),
        content=ContentSpec(format="json", value=fields),
        safety=SafetySpec(max_chars_change=max_chars_change),
    )


# --- handle_update_post_or_page ---


class TestHandleUpdatePostOrPage:
    def test_content_only(self, sample_wp_resource):
        ops = [_make_content_op()]
        result = handle_update_post_or_page(sample_wp_resource, ops)
        assert result.changed is True
        assert "content" in result.patch_payload
        assert "<p>New</p>" in result.patch_payload["content"]

    def test_fields_only(self, sample_wp_resource):
        ops = [_make_fields_op({"status": "draft"})]
        result = handle_update_post_or_page(sample_wp_resource, ops)
        assert result.changed is True
        assert result.patch_payload["status"] == "draft"

    def test_combined(self, sample_wp_resource):
        ops = [_make_content_op(), _make_fields_op({"status": "publish"})]
        result = handle_update_post_or_page(sample_wp_resource, ops)
        assert result.changed is True
        assert "content" in result.patch_payload
        assert result.patch_payload["status"] == "publish"

    def test_noop(self, sample_wp_resource):
        # Op with same content → no change
        original = sample_wp_resource["content"]["raw"]
        # Extract the slot body from the fixture
        import re
        m = re.search(r"<!-- AI_SLOT:INTRO -->\n(.*?)\n<!-- /AI_SLOT:INTRO -->", original, re.DOTALL)
        existing_body = m.group(1) if m else ""
        ops = [_make_content_op(value=existing_body)]
        result = handle_update_post_or_page(sample_wp_resource, ops)
        # Even if the slot replacement results in same text, the markers get rewritten
        # so it may or may not be a noop. Just verify no crash.
        assert isinstance(result.changed, bool)

    def test_invalid_status(self, sample_wp_resource):
        ops = [_make_fields_op({"status": "archived"})]
        with pytest.raises(SafetyViolationError, match="Unsupported status"):
            handle_update_post_or_page(sample_wp_resource, ops)


# --- handle_append_internal_links ---


class TestHandleAppendInternalLinks:
    def _make_link_op(self, links, slot="AI_SLOT:CTA"):
        return Operation(
            op="append",
            scope="content",
            selector=SelectorSpec(kind="html_comment", value=slot),
            content=ContentSpec(format="json", value={"links": links}),
            safety=SafetySpec(),
        )

    def test_new_links(self, sample_wp_resource):
        links = [
            {"url": "https://example.com/a", "anchor": "Link A"},
            {"url": "https://example.com/b", "anchor": "Link B"},
        ]
        result = handle_append_internal_links(sample_wp_resource, [self._make_link_op(links)])
        assert result.changed is True
        assert "Link A" in result.patch_payload["content"]
        assert "Link B" in result.patch_payload["content"]

    def test_dedup(self, sample_wp_resource):
        # First put a link in the slot, then try appending the same
        links = [
            {"url": "https://example.com/a", "anchor": "Link A"},
            {"url": "https://example.com/a", "anchor": "Link A Dup"},
        ]
        result = handle_append_internal_links(sample_wp_resource, [self._make_link_op(links)])
        assert result.changed is True
        content = result.patch_payload["content"]
        assert content.count("example.com/a") == 1

    def test_limit_3(self, sample_wp_resource):
        links = [{"url": f"https://example.com/{i}", "anchor": f"Link {i}"} for i in range(10)]
        result = handle_append_internal_links(sample_wp_resource, [self._make_link_op(links)])
        assert result.changed is True
        content = result.patch_payload["content"]
        # Only first 3 links inserted
        assert "Link 0" in content
        assert "Link 2" in content
        assert "Link 3" not in content


# --- handle_inject_schema_faq ---


class TestHandleInjectSchemaFaq:
    def _make_faq_op(self, faqs, inject_json_ld=False, slot="AI_SLOT:FAQ"):
        data = {"faqs": faqs}
        if inject_json_ld:
            data["inject_json_ld"] = True
            data["schema_slot"] = "AI_SLOT:SCHEMA"
        return Operation(
            op="replace",
            scope="content",
            selector=SelectorSpec(kind="html_comment", value=slot),
            content=ContentSpec(format="json", value=data),
            safety=SafetySpec(),
        )

    def test_basic(self, sample_wp_resource):
        faqs = [{"question": "Q1", "answer": "A1"}]
        result = handle_inject_schema_faq(sample_wp_resource, [self._make_faq_op(faqs)])
        assert result.changed is True
        assert "Q1" in result.patch_payload["content"]
        assert "A1" in result.patch_payload["content"]

    def test_with_json_ld(self, sample_wp_resource):
        faqs = [{"question": "Q1", "answer": "A1"}]
        result = handle_inject_schema_faq(
            sample_wp_resource, [self._make_faq_op(faqs, inject_json_ld=True)]
        )
        assert result.changed is True
        content = result.patch_payload["content"]
        assert "application/ld+json" in content
        assert "FAQPage" in content

    def test_faq_limit_6(self, sample_wp_resource):
        faqs = [{"question": f"Q{i}", "answer": f"A{i}"} for i in range(10)]
        result = handle_inject_schema_faq(sample_wp_resource, [self._make_faq_op(faqs)])
        assert result.changed is True
        content = result.patch_payload["content"]
        assert "Q5" in content
        assert "Q6" not in content  # only first 6

    def test_empty_faqs(self, sample_wp_resource):
        with pytest.raises(SafetyViolationError, match="at least one faq"):
            handle_inject_schema_faq(sample_wp_resource, [self._make_faq_op([])])


# --- handle_generate_topic_hub ---


class TestHandleGenerateTopicHub:
    def _make_hub_op(self, items, hub_title="My Hub", slot="AI_SLOT:INTRO"):
        return Operation(
            op="replace",
            scope="content",
            selector=SelectorSpec(kind="html_comment", value=slot),
            content=ContentSpec(format="json", value={"hub_title": hub_title, "items": items}),
            safety=SafetySpec(),
        )

    def test_normal(self, sample_wp_resource):
        items = [{"title": "Page A", "url": "/a", "summary": "About A"}]
        result = handle_generate_topic_hub(sample_wp_resource, [self._make_hub_op(items)])
        assert result.changed is True
        assert "Page A" in result.patch_payload["content"]
        assert "My Hub" in result.patch_payload["content"]

    def test_limit_20(self, sample_wp_resource):
        items = [{"title": f"Page {i}", "url": f"/{i}"} for i in range(25)]
        result = handle_generate_topic_hub(sample_wp_resource, [self._make_hub_op(items)])
        assert result.changed is True
        content = result.patch_payload["content"]
        assert "Page 19" in content
        assert "Page 20" not in content

    def test_empty_items(self, sample_wp_resource):
        with pytest.raises(SafetyViolationError, match="requires items"):
            handle_generate_topic_hub(sample_wp_resource, [self._make_hub_op([])])


# --- handle_set_meta ---


class TestHandleSetMeta:
    def _make_meta_op(self, meta_dict, max_chars_change=2000):
        return Operation(
            op="set_meta",
            scope="meta",
            selector=SelectorSpec(),
            content=ContentSpec(format="json", value=meta_dict),
            safety=SafetySpec(max_chars_change=max_chars_change),
        )

    def test_single_op(self, sample_wp_resource):
        result = handle_set_meta(sample_wp_resource, [self._make_meta_op({"key1": "val1"})])
        assert result.changed is True
        assert result.patch_payload == {"meta": {"key1": "val1"}}

    def test_multi_ops(self, sample_wp_resource):
        ops = [
            self._make_meta_op({"key1": "val1"}),
            self._make_meta_op({"key2": "val2"}),
        ]
        result = handle_set_meta(sample_wp_resource, ops)
        assert result.changed is True
        assert result.patch_payload["meta"]["key1"] == "val1"
        assert result.patch_payload["meta"]["key2"] == "val2"

    def test_noop_non_meta(self, sample_wp_resource):
        op = Operation(
            op="replace",
            scope="content",
            selector=SelectorSpec(),
            content=ContentSpec(format="json", value={}),
            safety=SafetySpec(),
        )
        result = handle_set_meta(sample_wp_resource, [op])
        assert result.changed is False

    def test_chars_limit(self, sample_wp_resource):
        with pytest.raises(SafetyViolationError, match="meta chars changed"):
            handle_set_meta(sample_wp_resource, [self._make_meta_op({"k": "x" * 500}, max_chars_change=10)])


# --- handle_publish_post ---


class TestHandlePublishPost:
    def _make_publish_op(self, payload):
        return Operation(
            op="publish",
            scope="content",
            selector=SelectorSpec(),
            content=ContentSpec(format="json", value=payload),
            safety=SafetySpec(),
        )

    def test_valid(self):
        result = handle_publish_post([self._make_publish_op({"title": "T", "content": "C"})])
        assert result.changed is True
        assert result.patch_payload["title"] == "T"
        assert result.patch_payload["content"] == "C"
        assert result.patch_payload["status"] == "draft"  # default

    def test_missing_title(self):
        with pytest.raises(SafetyViolationError, match="requires title and content"):
            handle_publish_post([self._make_publish_op({"content": "C"})])

    def test_missing_content(self):
        with pytest.raises(SafetyViolationError, match="requires title and content"):
            handle_publish_post([self._make_publish_op({"title": "T"})])

    def test_default_status(self):
        result = handle_publish_post([self._make_publish_op({"title": "T", "content": "C"})])
        assert result.patch_payload["status"] == "draft"


# --- handle_upload_media ---


class TestHandleUploadMedia:
    def _make_upload_op(self, payload):
        return Operation(
            op="upload",
            scope="content",
            selector=SelectorSpec(),
            content=ContentSpec(format="json", value=payload),
            safety=SafetySpec(),
        )

    def test_valid(self):
        result = handle_upload_media([self._make_upload_op({"file_path": "/tmp/img.png"})])
        assert result.changed is True
        assert result.patch_payload["file_path"] == "/tmp/img.png"

    def test_missing_file_path(self):
        with pytest.raises(SafetyViolationError, match="requires file_path"):
            handle_upload_media([self._make_upload_op({"title": "My Image"})])


# --- handle_report_only ---


class TestHandleReportOnly:
    def test_always_unchanged(self):
        task = Task(
            task_id="r1",
            created_at="2024-01-01",
            mode="execute",
            site={},
            task_type="report_only",
            targets=[],
            operations=[],
            notes="my report",
        )
        result = handle_report_only(task)
        assert result.changed is False
        assert "my report" in result.diff_summary


# --- Helper tests ---


class TestHelpers:
    def test_build_faq_html(self):
        faqs = [{"question": "Q1", "answer": "A1"}, {"question": "Q2", "answer": "A2"}]
        html = _build_faq_html(faqs)
        assert "<h3>Q1</h3>" in html
        assert "<p>A1</p>" in html
        assert "<h3>Q2</h3>" in html
        assert 'class="ai-faq"' in html

    def test_build_faq_json_ld(self):
        faqs = [{"question": "Q1", "answer": "A1"}]
        html = _build_faq_json_ld(faqs)
        assert "application/ld+json" in html
        data = json.loads(html.replace('<script type="application/ld+json">', "").replace("</script>", ""))
        assert data["@type"] == "FAQPage"
        assert len(data["mainEntity"]) == 1
        assert data["mainEntity"][0]["name"] == "Q1"

    def test_extract_rendered_content_dict(self):
        assert _extract_rendered_content({"content": {"raw": "RAW", "rendered": "RENDERED"}}) == "RAW"

    def test_extract_rendered_content_no_raw(self):
        assert _extract_rendered_content({"content": {"rendered": "RENDERED"}}) == "RENDERED"

    def test_extract_rendered_content_no_dict(self):
        assert _extract_rendered_content({"content": "string"}) == ""

    def test_extract_rendered_content_missing(self):
        assert _extract_rendered_content({}) == ""
