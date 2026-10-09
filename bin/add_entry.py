#!/usr/bin/env python3
"""Append one contributions entry, pure metadata, no description.

quarry calls this at step 7 with the PR's facts as flags. It assigns the next seq and
writes data/entries/<repo-last-segment>-<pr>.md, then records the repo's current star count
in data/stars.json (the one place a repo's stars live). There is no prose to write and no
tag to pick, so filing a merge is a single call. It refuses a repo and PR already filed
unless --force is given, so re-running the step never creates a duplicate.
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SITE_ROOT") or os.path.dirname(HERE)
ENTRY_DIR = os.path.join(ROOT, "data", "entries")
STARS_FILE = os.path.join(ROOT, "data", "stars.json")

FM_ORDER = ["repo", "repo_url", "pr_label", "pr_url",
            "carried_from_label", "carried_from_url",
            "stack", "origin", "date", "seq"]


def next_seq():
    seqs = []
    for path in glob.glob(os.path.join(ENTRY_DIR, "*.md")):
        _, front, _ = open(path, encoding="utf-8").read().split("---\n", 2)
        for line in front.strip().splitlines():
            k, _, v = line.partition(":")
            if k.strip() == "seq":
                seqs.append(int(v.strip() or 0))
    return (max(seqs) + 1) if seqs else 1


def entry_path(repo, pr_label):
    stub = pr_label.lstrip("#").strip()
    base = repo.split("/")[-1] + "-" + stub
    path = os.path.join(ENTRY_DIR, base + ".md")
    if os.path.exists(path):
        base = repo.replace("/", "-") + "-" + stub
        path = os.path.join(ENTRY_DIR, base + ".md")
    return path


def record_stars(repo, count):
    """Store the repo's current star count in data/stars.json, keys sorted for a clean diff."""
    store = json.load(open(STARS_FILE, encoding="utf-8")) if os.path.exists(STARS_FILE) else {}
    store[repo] = int(count)
    with open(STARS_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def find_existing(repo, pr_label):
    """Path of the entry already filed for this repo and PR, or None."""
    for path in glob.glob(os.path.join(ENTRY_DIR, "*.md")):
        _, front, _ = open(path, encoding="utf-8").read().split("---\n", 2)
        meta = {}
        for line in front.strip().splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        if meta.get("repo") == repo and meta.get("pr_label") == pr_label:
            return path
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--repo-url", required=True)
    ap.add_argument("--pr-label", required=True, help="e.g. #6215 or a commit short sha")
    ap.add_argument("--pr-url", required=True)
    ap.add_argument("--stars-num", required=True, type=int,
                    help="the repo's current star count, e.g. 29000")
    ap.add_argument("--date", required=True, help="e.g. oct 2026")
    ap.add_argument("--stack", required=True, help="comma list, up to 5")
    ap.add_argument("--origin", required=True, choices=["found", "known"])
    ap.add_argument("--carried-label", default="")
    ap.add_argument("--carried-url", default="")
    ap.add_argument("--force", action="store_true",
                    help="overwrite the entry already filed for this repo and PR")
    a = ap.parse_args(argv)
    # stack tags are stored lowercase and trimmed so the ledger stays consistent.
    # The framing (node vs node.js) is chosen upstream against existing entries.
    a.stack = ", ".join(t.strip().lower() for t in a.stack.split(",") if t.strip())

    existing = find_existing(a.repo, a.pr_label)
    if existing and not a.force:
        print("%s %s is already filed at %s, re-run with --force to overwrite"
              % (a.repo, a.pr_label, os.path.relpath(existing, ROOT)), file=sys.stderr)
        return 1

    seq = next_seq()
    if existing:
        # a forced re-file keeps its place in the ledger
        _, front, _ = open(existing, encoding="utf-8").read().split("---\n", 2)
        for line in front.strip().splitlines():
            if line.startswith("seq:"):
                seq = int(line.split(":", 1)[1].strip() or seq)
    vals = {
        "repo": a.repo, "repo_url": a.repo_url, "pr_label": a.pr_label, "pr_url": a.pr_url,
        "carried_from_label": a.carried_label, "carried_from_url": a.carried_url,
        "stack": a.stack, "origin": a.origin,
        "date": a.date, "seq": str(seq),
    }
    lines = ["---"] + ["%s: %s" % (k, vals[k]) for k in FM_ORDER] + ["---", ""]
    path = existing if existing else entry_path(a.repo, a.pr_label)
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    record_stars(a.repo, a.stars_num)
    print("wrote %s (seq %d, %s, %d stars)" % (os.path.relpath(path, ROOT), seq, a.origin, a.stars_num))
    return 0


if __name__ == "__main__":
    sys.exit(main())
