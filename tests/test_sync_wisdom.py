"""Unit tests for sync-wisdom.py.

A failed fetch must never replace a skill's existing wisdom.md, and must
surface as a distinct exit code so the scheduled workflow fails loudly.
"""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# sync-wisdom.py has a hyphen, so import via importlib
_spec = importlib.util.spec_from_file_location(
    "sync_wisdom",
    os.path.join(os.path.dirname(__file__), "..", ".github", "scripts", "sync-wisdom.py"),
)
sw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sw)

GOOD_WISDOM = "# Domain Knowledge Reference\n\nLast updated: 2026-01-01\n\ngood content\n"


def _make_root(tmp: str, posts: dict) -> Path:
    """Build a repo root with skill-sources.json and existing wisdom files."""
    root = Path(tmp)
    config = {
        "baseUrl": "https://example.test",
        "skills": {name: {"posts": [{"slug": s, "url": f"/{s}/"} for s in slugs]}
                   for name, slugs in posts.items()},
    }
    (root / "skill-sources.json").write_text(json.dumps(config))
    for name in posts:
        ref = root / "skills" / name / "references"
        ref.mkdir(parents=True)
        (ref / "wisdom.md").write_text(GOOD_WISDOM)
    return root


def _fetch_failing_on(bad_slugs):
    def fake_fetch(base_url, url_path):
        slug = url_path.strip("/")
        return "" if slug in bad_slugs else f"content of {slug}"
    return fake_fetch


class TestGenerateWisdom(unittest.TestCase):

    def test_reports_failed_posts(self):
        posts = [{"slug": "ok", "url": "/ok/"}, {"slug": "bad", "url": "/bad/"}]
        with patch.object(sw, "fetch_llm_content", _fetch_failing_on({"bad"})):
            _, failures = sw.generate_wisdom("https://x", "https://x", posts)
        self.assertEqual(failures, ["bad"])

    def test_no_failures_when_all_fetched(self):
        posts = [{"slug": "ok", "url": "/ok/"}]
        with patch.object(sw, "fetch_llm_content", _fetch_failing_on(set())):
            content, failures = sw.generate_wisdom("https://x", "https://x", posts)
        self.assertEqual(failures, [])
        self.assertIn("content of ok", content)


class TestMain(unittest.TestCase):

    def test_failed_fetch_keeps_existing_file_and_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_root(tmp, {"review-a": ["bad", "ok"]})
            with patch.object(sw, "fetch_llm_content", _fetch_failing_on({"bad"})):
                rc = sw.main([], root=root)
            self.assertEqual(rc, sw.EXIT_FETCH_FAILED)
            wisdom = root / "skills" / "review-a" / "references" / "wisdom.md"
            self.assertEqual(wisdom.read_text(), GOOD_WISDOM)

    def test_other_skills_still_update_when_one_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_root(tmp, {"review-a": ["bad"], "review-b": ["ok"]})
            with patch.object(sw, "fetch_llm_content", _fetch_failing_on({"bad"})):
                rc = sw.main([], root=root)
            self.assertEqual(rc, sw.EXIT_FETCH_FAILED)
            updated = (root / "skills" / "review-b" / "references" / "wisdom.md").read_text()
            self.assertIn("content of ok", updated)

    def test_success_exits_0_and_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_root(tmp, {"review-a": ["ok"]})
            with patch.object(sw, "fetch_llm_content", _fetch_failing_on(set())):
                rc = sw.main([], root=root)
            self.assertEqual(rc, 0)
            wisdom = (root / "skills" / "review-a" / "references" / "wisdom.md").read_text()
            self.assertIn("content of ok", wisdom)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_root(tmp, {"review-a": ["ok"]})
            with patch.object(sw, "fetch_llm_content", _fetch_failing_on(set())):
                rc = sw.main(["--dry-run"], root=root)
            self.assertEqual(rc, 0)
            wisdom = (root / "skills" / "review-a" / "references" / "wisdom.md").read_text()
            self.assertEqual(wisdom, GOOD_WISDOM)


class TestStripDateLine(unittest.TestCase):

    def test_removes_only_date_line(self):
        text = "a\nLast updated: 2026-01-01\nb"
        self.assertEqual(sw.strip_date_line(text), "a\nb")


if __name__ == "__main__":
    unittest.main()
