"""Translated docs keep up with the English they were made from.

docs/i18n/rules.md describes the convention. A translation's first line records
the git blob id of its English source, so when the English changes the ids stop
matching and the stale translation is named here.
"""
import hashlib
import os
import re
import unittest
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGS = ("zh-CN", "ja", "ko", "ru")
STAMP = re.compile(r"<!-- i18n-source: (\S+) ([0-9a-f]{40}) -->")
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^#{2,6}\s+(.*?)\s*$")
ANCHOR = re.compile(r'<a id="([^"]+)"></a>')


def blob_id(path):
    """The id git gives the file's contents, the same as `git hash-object`."""
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def find_translations():
    found = []
    for path in ROOT.rglob("*.md"):
        parts = path.relative_to(ROOT).parts
        if any(p.startswith(".") or p in ("node_modules", "__pycache__") for p in parts):
            continue
        if any(path.name.endswith(".%s.md" % lang) for lang in LANGS):
            found.append(path)
    return sorted(found)


def source_of(translation):
    for lang in LANGS:
        suffix = ".%s.md" % lang
        if translation.name.endswith(suffix):
            return translation.with_name(translation.name[: -len(suffix)] + ".md")
    raise ValueError(translation)


def headings(path):
    """Heading text below the title, skipping lines inside code blocks."""
    found, in_code = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line):
            in_code = not in_code
            continue
        m = HEADING.match(line)
        if not in_code and m:
            found.append(m.group(1))
    return found


def github_ids(texts):
    """The ids GitHub gives these English headings, numbering repeats."""
    ids, seen = [], {}
    for text in texts:
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text).replace("`", "").replace("*", "")
        base = re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")
        n = seen.get(base, 0)
        seen[base] = n + 1
        ids.append(base if n == 0 else "%s-%d" % (base, n))
    return ids


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.translations = find_translations()

    def test_translations_exist(self):
        self.assertTrue(self.translations, "no translated docs found")

    def test_each_translated_doc_has_every_language(self):
        missing = []
        for source in sorted({source_of(t) for t in self.translations}):
            for lang in LANGS:
                expected = source.with_name(source.name[:-3] + ".%s.md" % lang)
                if not expected.exists():
                    missing.append(rel(expected))
        self.assertEqual(missing, [], "missing translations")

    def test_translations_match_the_current_english(self):
        for translation in self.translations:
            with self.subTest(translation=rel(translation)):
                source = source_of(translation)
                first = translation.read_text(encoding="utf-8").splitlines()[0]
                m = STAMP.fullmatch(first)
                self.assertTrue(m, "%s has no i18n-source line, run docs/i18n/stamp.py on it"
                                % rel(translation))
                self.assertEqual(m.group(1), rel(source), "wrong source named")
                self.assertEqual(
                    m.group(2), blob_id(source),
                    "%s changed after %s was translated. See what changed with "
                    "`git diff %s HEAD:%s`, update the translation, then run "
                    "`python3 docs/i18n/stamp.py %s`. docs/i18n/rules.md has the details."
                    % (rel(source), rel(translation), m.group(2), rel(source), rel(translation)))

    def test_translations_have_the_same_headings(self):
        for translation in self.translations:
            with self.subTest(translation=rel(translation)):
                english = github_ids(headings(source_of(translation)))
                anchors = []
                for text in headings(translation):
                    m = ANCHOR.match(text)
                    self.assertTrue(m, "a heading has no anchor: %s" % text)
                    anchors.append(m.group(1))
                self.assertEqual(anchors, english)


if __name__ == "__main__":
    unittest.main()
