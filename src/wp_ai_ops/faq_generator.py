from __future__ import annotations

import base64
import json
import logging
import os
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:3000]


def fetch_page_content(page_url: str, username: str, password: str) -> tuple[str, str]:
    """Return (title, plain_text) for a WP page/post. Returns ('', '') on error."""
    try:
        parsed = urlparse(page_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path.strip("/")
        slug = path.split("/")[-1] if path else "home"
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers = {"Authorization": f"Basic {credentials}"}
        for resource in ("pages", "posts"):
            api_url = f"{base_url}/wp-json/wp/v2/{resource}?slug={slug}&_fields=title,content"
            req = Request(api_url, headers=headers)
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                if data:
                    item = data[0]
                    title = item.get("title", {}).get("rendered", "")
                    content_html = item.get("content", {}).get("rendered", "")
                    return title, _strip_html(content_html)
    except Exception:
        logger.exception("Failed to fetch page content for %s", page_url)
    return "", ""


def generate_faqs(page_url: str, page_title: str, page_text: str, site_context: str = "business") -> list[dict]:
    """Generate 3-5 page-specific FAQs via Claude Haiku. Falls back to generic on any error.

    site_context: "business" (default) or "candy_blog"
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_faqs()
    try:
        import anthropic  # type: ignore

        client = anthropic.Anthropic(api_key=api_key)

        if site_context == "candy_blog":
            instructions = (
                "Write exactly 5 FAQ items for this candy/food blog post. Each FAQ should:\n"
                "- Answer a genuine question a reader would have after reading the article\n"
                "- Be specific to the product or topic on this page (not generic)\n"
                "- Have a clear, helpful answer in 1-3 sentences\n"
                "- Be appropriate for an Australian candy ecommerce blog audience\n"
            )
        else:
            instructions = (
                "Write exactly 3 FAQ items specific to this page's topic. Each FAQ should:\n"
                "- Address a real question a potential customer would ask about this specific service\n"
                "- Have a concise, helpful answer (1-2 sentences)\n"
                "- Be relevant to the local business context\n"
            )

        prompt = (
            f"You are writing FAQ content for a blog post.\n\n"
            f"Page URL: {page_url}\n"
            f"Page Title: {page_title}\n"
            f"Page Content (excerpt):\n{page_text[:2000]}\n\n"
            + instructions +
            "\nReturn ONLY a JSON array, no other text:\n"
            '[{"question": "...", "answer": "..."}, ...]'
        )
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            faqs = json.loads(match.group())
            if isinstance(faqs, list) and len(faqs) >= 1:
                return faqs[:5]
    except Exception:
        logger.exception("Failed to generate FAQs for %s", page_url)
    return _fallback_faqs()


def generate_meta(page_url: str, page_title: str, page_text: str, site_context: str = "business") -> dict:
    """Generate SEO title, description, and focus keyword via Claude Haiku.
    Returns dict with keys: title, description, keyword. Falls back to slug-based templates on error."""
    slug = page_url.rstrip("/").split("/")[-1].replace("-", " ").strip() or page_title or "guide"

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_meta(slug, site_context)
    try:
        import anthropic  # type: ignore

        client = anthropic.Anthropic(api_key=api_key)

        if site_context == "candy_blog":
            instructions = (
                "Write SEO meta for an Australian candy ecommerce blog post.\n"
                "- title: compelling, includes the main keyword, max 60 characters, no site name suffix\n"
                "- description: enticing summary that makes people want to click, max 155 characters\n"
                "- keyword: the single most important search keyword for this page (1-4 words)\n"
            )
        else:
            instructions = (
                "Write SEO meta for a local business services page.\n"
                "- title: clear and keyword-rich, max 60 characters, no site name suffix\n"
                "- description: concise value proposition, max 155 characters\n"
                "- keyword: the single most important search keyword for this page (1-4 words)\n"
            )

        prompt = (
            f"Page URL: {page_url}\n"
            f"Page Title: {page_title}\n"
            f"Page Content (excerpt):\n{page_text[:1500]}\n\n"
            + instructions +
            '\nReturn ONLY a JSON object, no other text:\n'
            '{"title": "...", "description": "...", "keyword": "..."}'
        )
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            meta = json.loads(match.group())
            if all(k in meta for k in ("title", "description", "keyword")):
                # Enforce length limits
                meta["title"] = meta["title"][:60]
                meta["description"] = meta["description"][:155]
                return meta
    except Exception:
        logger.exception("Failed to generate meta for %s", page_url)
    return _fallback_meta(slug, site_context)


def generate_intro(page_url: str, page_title: str, page_text: str, site_context: str = "business") -> str:
    """Generate a 2-3 sentence intro paragraph via Claude Haiku.
    Returns an HTML <p> string. Falls back to a safe generic paragraph on any error."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_intro(page_title or page_url)
    try:
        import anthropic  # type: ignore

        client = anthropic.Anthropic(api_key=api_key)

        if site_context == "candy_blog":
            instructions = (
                "Write a 2-3 sentence opening paragraph for this candy/food blog post. "
                "It should hook the reader, mention the main product or topic, and be written for an Australian audience. "
                "Plain text only — no headings, no bullet points."
            )
        else:
            instructions = (
                "Write a 2-3 sentence opening paragraph for this local business services page. "
                "It should clearly state what the page covers, who it's for, and why it matters. "
                "Keep it factual and direct. Plain text only — no headings, no bullet points."
            )

        prompt = (
            f"Page URL: {page_url}\n"
            f"Page Title: {page_title}\n"
            f"Page Content (excerpt):\n{page_text[:1500]}\n\n"
            + instructions +
            "\nReturn ONLY the paragraph text, no other text or formatting."
        )
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        if len(text) > 30:
            return f"<p>{text}</p>"
    except Exception:
        logger.exception("Failed to generate intro for %s", page_url)
    return _fallback_intro(page_title or page_url)


def _fallback_intro(label: str) -> str:
    slug = label.rstrip("/").split("/")[-1].replace("-", " ").strip() or label
    return f"<p>This page covers everything you need to know about {slug}.</p>"


def _fallback_meta(slug: str, site_context: str = "business") -> dict:
    if site_context == "candy_blog":
        return {
            "title": slug.title(),
            "description": f"Everything you need to know about {slug}. Shop online at Sweets World Australia.",
            "keyword": slug,
        }
    return {
        "title": f"{slug.title()} | Updated Guide",
        "description": f"Updated quick guide for {slug}. Clear answers, better structure, and next-step resources.",
        "keyword": slug,
    }


def _fallback_faqs() -> list[dict]:
    return [
        {
            "question": "What will I learn on this page?",
            "answer": "You will get a concise overview, practical steps, and links to related guides.",
        },
        {
            "question": "Who is this content for?",
            "answer": "Readers looking for a practical starting point and deeper follow-up resources.",
        },
        {
            "question": "What should I read next?",
            "answer": "Use the related links section for the next best article in the topic cluster.",
        },
    ]
