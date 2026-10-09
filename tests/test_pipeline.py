"""Tests for the minimal contributions ledger: add_entry.py and site_data.py.

Each test runs the real scripts against a throwaway copy of data/ via the
SITE_ROOT override, so the repo's own entries are never touched.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIN = os.path.join(ROOT, "bin")

BASE_ARGS = [
    "--repo", "test/demo", "--repo-url", "https://github.com/test/demo",
    "--pr-label", "#999", "--pr-url", "https://github.com/test/demo/pull/999",
    "--stars-num", "1200", "--date", "oct 2026",
    "--stack", "python, ci", "--origin", "found",
]


def run_bin(script, args, root):
    env = dict(os.environ, SITE_ROOT=root)
    return subprocess.run([sys.executable, os.path.join(BIN, script)] + args,
                          capture_output=True, text=True, env=env)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def max_seq(root):
    import glob
    best = 0
    for p in glob.glob(os.path.join(root, "data", "entries", "*.md")):
        for line in read(p).splitlines():
            if line.startswith("seq:"):
                best = max(best, int(line.split(":", 1)[1].strip()))
    return best


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        shutil.copytree(os.path.join(ROOT, "data"), os.path.join(self.tmp, "data"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def contributions(self):
        return json.loads(read(os.path.join(self.tmp, "data", "contributions.json")))

    def test_rebuild_is_reproducible(self):
        # generating twice from the same entries gives byte-identical output
        out = os.path.join(self.tmp, "data", "contributions.json")
        self.assertEqual(run_bin("site_data.py", [], self.tmp).returncode, 0)
        first = read(out)
        self.assertEqual(run_bin("site_data.py", [], self.tmp).returncode, 0)
        second = read(out)
        self.assertEqual(first, second)

    def test_stats_shape(self):
        self.assertEqual(run_bin("site_data.py", [], self.tmp).returncode, 0)
        st = self.contributions()["stats"]
        self.assertEqual(set(st), {"merged", "repos", "stars", "stacks", "found", "known"})
        for k, v in st.items():
            self.assertIsInstance(v, int, k)

    def test_write_increments_seq_and_appears(self):
        self.assertEqual(run_bin("site_data.py", [], self.tmp).returncode, 0)
        before = self.contributions()
        expected_seq = max_seq(self.tmp) + 1
        r = run_bin("add_entry.py", BASE_ARGS, self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "data", "entries", "demo-999.md")))
        self.assertIn("seq %d" % expected_seq, r.stdout)
        self.assertEqual(run_bin("site_data.py", [], self.tmp).returncode, 0)
        d = self.contributions()
        self.assertEqual(d["stats"]["merged"], before["stats"]["merged"] + 1)
        self.assertEqual(d["stats"]["repos"], before["stats"]["repos"] + 1)
        demo = [r for r in d["repos"] if r["name"] == "test/demo"][0]
        self.assertEqual(demo["prs"][0]["origin"], "found")
        self.assertEqual(demo["prs"][0]["stack"], ["python", "ci"])
        self.assertNotIn("prose", demo["prs"][0])

    def test_carried_from(self):
        args = BASE_ARGS + ["--carried-label", "#5",
                            "--carried-url", "https://github.com/test/demo/pull/5"]
        self.assertEqual(run_bin("add_entry.py", args, self.tmp).returncode, 0)
        self.assertEqual(run_bin("site_data.py", [], self.tmp).returncode, 0)
        demo = [r for r in self.contributions()["repos"] if r["name"] == "test/demo"][0]
        self.assertEqual(demo["prs"][0]["carried"]["label"], "#5")

    def test_add_entry_writes_star_store(self):
        # the count goes to data/stars.json, not into the entry, and site_data derives the display
        self.assertEqual(run_bin("add_entry.py", BASE_ARGS, self.tmp).returncode, 0)
        store = json.loads(read(os.path.join(self.tmp, "data", "stars.json")))
        self.assertEqual(store["test/demo"], 1200)
        entry = read(os.path.join(self.tmp, "data", "entries", "demo-999.md"))
        self.assertNotIn("stars", entry)
        self.assertEqual(run_bin("site_data.py", [], self.tmp).returncode, 0)
        demo = [r for r in self.contributions()["repos"] if r["name"] == "test/demo"][0]
        self.assertEqual(demo["stars"], "1.2k+")
        self.assertEqual(demo["stars_num"], 1200)

    def test_refresh_stars(self):
        # a stub gh reports a fixed count for any lookup; both files pick it up
        fake = os.path.join(self.tmp, "gh")
        with open(fake, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\nprint(4242)\n")
        os.chmod(fake, 0o755)
        env = dict(os.environ, SITE_ROOT=self.tmp, GH_BIN=fake)
        r = subprocess.run([sys.executable, os.path.join(BIN, "refresh_stars.py")],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        store = json.loads(read(os.path.join(self.tmp, "data", "stars.json")))
        self.assertTrue(store)
        self.assertTrue(all(v == 4242 for v in store.values()), store)
        builds = json.loads(read(os.path.join(self.tmp, "data", "builds.json")))
        self.assertEqual(builds["builds"][0]["stars"], "4242")

    def test_refuses_duplicate(self):
        import glob
        self.assertEqual(run_bin("add_entry.py", BASE_ARGS, self.tmp).returncode, 0)
        r = run_bin("add_entry.py", BASE_ARGS, self.tmp)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already filed", r.stderr.lower())
        pat = os.path.join(self.tmp, "data", "entries", "*999.md")
        self.assertEqual(len(glob.glob(pat)), 1)
        # --force overwrites the same file in place, still one entry
        self.assertEqual(run_bin("add_entry.py", BASE_ARGS + ["--force"], self.tmp).returncode, 0)
        self.assertEqual(len(glob.glob(pat)), 1)

    def test_different_repo_same_last_segment_still_files(self):
        self.assertEqual(run_bin("add_entry.py", BASE_ARGS, self.tmp).returncode, 0)
        other = ["--repo", "other/demo", "--repo-url", "https://github.com/other/demo",
                 "--pr-label", "#999", "--pr-url", "https://github.com/other/demo/pull/999",
                 "--stars-num", "1000", "--date", "oct 2026",
                 "--stack", "go", "--origin", "known"]
        self.assertEqual(run_bin("add_entry.py", other, self.tmp).returncode, 0)
        entries = os.path.join(self.tmp, "data", "entries")
        self.assertTrue(os.path.exists(os.path.join(entries, "demo-999.md")))
        self.assertTrue(os.path.exists(os.path.join(entries, "other-demo-999.md")))

    def test_built_pages_carry_hardening(self):
        # every page ships a CSP and escapes URLs, and the ledger is virtualized
        shutil.copytree(os.path.join(ROOT, "site"), os.path.join(self.tmp, "site"))
        self.assertEqual(run_bin("site_data.py", [], self.tmp).returncode, 0)
        self.assertEqual(run_bin("build_pages.py", [], self.tmp).returncode, 0)
        for rel in ("index.html", "contributions/index.html", "builds/index.html"):
            html = read(os.path.join(self.tmp, "site", rel))
            self.assertIn("Content-Security-Policy", html, rel)
            self.assertIn("function safeUrl", html, rel)
        contrib = read(os.path.join(self.tmp, "site", "contributions", "index.html"))
        self.assertIn("function renderWindow", contrib)
        self.assertIn("safeUrl(pr.url)", contrib)


if __name__ == "__main__":
    unittest.main()
