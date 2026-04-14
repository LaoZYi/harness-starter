"""BM25 search helpers in agent_harness.memory (Issue #29, context-mode absorption).

Covers: tokenize, _segment_document, bm25_search, search_lessons, CLI E2E.
"""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_harness.memory import main as memory_main  # noqa: E402
from agent_harness.memory_search import (  # noqa: E402
    _segment_document,
    _tokenize,
    bm25_search,
    search_lessons,
)


class TokenizeTests(unittest.TestCase):
    def test_english_words_lowercased(self) -> None:
        self.assertEqual(_tokenize("Hello WORLD"), ["hello", "world"])

    def test_chinese_characters_are_unigrams(self) -> None:
        self.assertEqual(_tokenize("分层记忆"), ["分", "层", "记", "忆"])

    def test_mixed_chinese_english(self) -> None:
        tokens = _tokenize("/lfg 阶段 0.2")
        # Western run "lfg" + "0" + "2" + CJK unigrams "阶段"
        self.assertIn("lfg", tokens)
        self.assertIn("阶", tokens)
        self.assertIn("段", tokens)

    def test_empty_and_whitespace(self) -> None:
        self.assertEqual(_tokenize(""), [])
        self.assertEqual(_tokenize("   \n\t"), [])

    def test_punctuation_dropped(self) -> None:
        tokens = _tokenize("hello, world! 测试。")
        self.assertEqual(sorted(tokens), sorted(["hello", "world", "测", "试"]))

    def test_emoji_dropped(self) -> None:
        self.assertEqual(_tokenize("🎉 party 庆祝"), ["party", "庆", "祝"])


class SegmentDocumentTests(unittest.TestCase):
    def test_multiple_sections(self) -> None:
        text = (
            "# Title\n\nIntro ignored.\n\n"
            "## First section\nbody of first\nmore first\n\n"
            "## Second section\nbody of second\n"
        )
        segs = _segment_document(text)
        self.assertEqual(len(segs), 2)
        self.assertEqual(segs[0][0], "First section")
        self.assertIn("body of first", segs[0][1])
        self.assertEqual(segs[1][0], "Second section")
        self.assertIn("body of second", segs[1][1])

    def test_no_sections_returns_empty(self) -> None:
        self.assertEqual(_segment_document("no headings here\njust lines"), [])

    def test_empty_input_returns_empty(self) -> None:
        self.assertEqual(_segment_document(""), [])

    def test_single_section(self) -> None:
        text = "## only one\nline a\nline b"
        segs = _segment_document(text)
        self.assertEqual(len(segs), 1)
        self.assertEqual(segs[0][0], "only one")


class Bm25SearchTests(unittest.TestCase):
    def test_exact_match_scores_higher_than_partial(self) -> None:
        docs = [
            ("doc1", "apple banana cherry apple apple"),
            ("doc2", "banana cherry"),
            ("doc3", "unrelated content"),
        ]
        results = bm25_search("apple banana", docs, top=5)
        # doc1 has both query terms and higher TF; should outrank doc2
        titles = [title for _, title, _ in results]
        self.assertEqual(titles[0], "doc1")
        self.assertIn("doc2", titles)
        self.assertNotIn("doc3", titles)

    def test_empty_query_returns_empty(self) -> None:
        self.assertEqual(bm25_search("", [("a", "some text")]), [])
        self.assertEqual(bm25_search("   ", [("a", "some text")]), [])

    def test_empty_docs_returns_empty(self) -> None:
        self.assertEqual(bm25_search("query", []), [])

    def test_top_k_truncation(self) -> None:
        docs = [(f"doc{i}", "hello world") for i in range(10)]
        results = bm25_search("hello", docs, top=3)
        self.assertEqual(len(results), 3)

    def test_no_match_returns_empty(self) -> None:
        docs = [("doc1", "cat dog bird")]
        self.assertEqual(bm25_search("nonexistent", docs), [])

    def test_chinese_query(self) -> None:
        docs = [
            ("孤儿", "这是一条关于分层记忆的教训，强调 L0-L3 层级"),
            ("unrelated", "nothing related here"),
        ]
        results = bm25_search("分层记忆", docs, top=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "孤儿")

    def test_score_positive(self) -> None:
        docs = [("doc1", "alpha beta gamma")]
        results = bm25_search("alpha", docs, top=5)
        self.assertEqual(len(results), 1)
        self.assertGreater(results[0][0], 0)


class SearchLessonsTests(unittest.TestCase):
    def _setup_project(self, tmpdir: Path) -> Path:
        proj = tmpdir / "proj"
        (proj / ".agent-harness").mkdir(parents=True)
        (proj / ".agent-harness" / "lessons.md").write_text(
            "# Lessons\n\n"
            "## 2026-04-01 [测试] alpha beta\ncontent about alpha\n\n"
            "## 2026-04-02 [流程] 分层记忆\n记忆分层实践\n",
            encoding="utf-8",
        )
        (proj / ".agent-harness" / "task-log.md").write_text(
            "# Task Log\n\n"
            "## 2026-04-01 某任务\n完成了分层记忆\n",
            encoding="utf-8",
        )
        return proj

    def test_scope_all(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            proj = self._setup_project(Path(td))
            results = search_lessons(proj, "分层记忆", scope="all", top=5)
        titles = [t for _, t, _ in results]
        self.assertTrue(any("lessons.md" in t for t in titles))
        self.assertTrue(any("task-log.md" in t for t in titles))

    def test_scope_lessons_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            proj = self._setup_project(Path(td))
            results = search_lessons(proj, "分层记忆", scope="lessons", top=5)
        titles = [t for _, t, _ in results]
        self.assertTrue(all("task-log.md" not in t for t in titles))

    def test_scope_history_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            proj = self._setup_project(Path(td))
            results = search_lessons(proj, "分层记忆", scope="history", top=5)
        titles = [t for _, t, _ in results]
        self.assertTrue(all("lessons.md" not in t for t in titles))

    def test_missing_files_graceful(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td) / "proj"
            (proj / ".agent-harness").mkdir(parents=True)
            # No lessons.md or task-log.md
            results = search_lessons(proj, "anything", scope="all", top=5)
        self.assertEqual(results, [])

    def test_no_match_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            proj = self._setup_project(Path(td))
            results = search_lessons(proj, "zzznonexistentzzz", scope="all", top=5)
        self.assertEqual(results, [])


class CliE2ETests(unittest.TestCase):
    def test_search_subcommand_prints_results(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td) / "proj"
            (proj / ".agent-harness").mkdir(parents=True)
            (proj / ".agent-harness" / "lessons.md").write_text(
                "## 2026-04-01 [测试] alpha\ncontent alpha beta\n", encoding="utf-8"
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = memory_main(["search", "alpha", "--target", str(proj), "--top", "3"])
            self.assertEqual(rc, 0)
            out = buf.getvalue()
            self.assertIn("搜索", out)
            self.assertIn("alpha", out)

    def test_search_subcommand_no_match_prints_notice(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td) / "proj"
            (proj / ".agent-harness").mkdir(parents=True)
            (proj / ".agent-harness" / "lessons.md").write_text(
                "## something\nbody\n", encoding="utf-8"
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = memory_main(["search", "zzznotfound", "--target", str(proj)])
            self.assertEqual(rc, 0)
            self.assertIn("无命中", buf.getvalue())

    def test_search_missing_harness_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            # no .agent-harness dir
            err_buf = io.StringIO()
            with redirect_stderr(err_buf):
                rc = memory_main(["search", "alpha", "--target", td])
            self.assertEqual(rc, 2)
            self.assertIn("search 失败", err_buf.getvalue())


if __name__ == "__main__":
    unittest.main()
