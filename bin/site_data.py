#!/usr/bin/env python3
"""Build data/contributions.json for the site.

Each entry is one merged PR, pure metadata, no description:
  repo, pr_label, pr_url, stack, origin (found or known), carried_from_*, date, seq.
Each repository's star count lives once in data/stars.json. build() reads it and derives the
display string (for example 11.4k+) shown next to every mention of that repo, so a count is
never copied into an entry and cannot drift.

Output feeds three pages:
  stats     the headline counts (merged, repos, stars, stacks, found, known).
  repos     every repo with its PRs, for the contributions ledger.
  recent    the 6 newest merges, flat, for the home.
  featured  a hand-picked set from data/featured.json, each with a short blurb, for the home.

quarry appends an entry through bin/add_entry.py. featured is curated by hand.
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SITE_ROOT") or os.path.dirname(HERE)
ENTRY_DIR = os.path.join(ROOT, "data", "entries")
OUT = os.path.join(ROOT, "data", "contributions.json")
FEATURED_FILE = os.path.join(ROOT, "data", "featured.json")
STARS_FILE = os.path.join(ROOT, "data", "stars.json")


def split_list(value):
    return [v.strip() for v in value.split(",") if v.strip()]


def stars_display(n):
    """Turn an exact star count into the display string, for example 11388 -> 11.4k+."""
    if n >= 1_000_000:
        return "%.1fM+" % (n / 1_000_000)
    if n >= 1000:
        return "%.1fk+" % (n / 1000)
    return "%d+" % n


def load_stars():
    if os.path.exists(STARS_FILE):
        return json.load(open(STARS_FILE, encoding="utf-8"))
    return {}


def load_entries():
    entries = []
    for path in sorted(glob.glob(os.path.join(ENTRY_DIR, "*.md"))):
        raw = open(path, encoding="utf-8").read()
        _, front, _ = raw.split("---\n", 2)
        meta = {}
        for line in front.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
        meta["seq"] = int(meta.get("seq", "0") or 0)
        meta["stack"] = split_list(meta.get("stack", ""))
        entries.append(meta)
    return entries


def pr_of(e):
    pr = {"label": e["pr_label"], "url": e["pr_url"], "date": e["date"],
          "stack": e["stack"], "origin": e["origin"]}
    if e.get("carried_from_url"):
        pr["carried"] = {"label": e["carried_from_label"], "url": e["carried_from_url"]}
    return pr


def flat_item(e, stars):
    return {"repo": e["repo"], "repo_url": e["repo_url"], "stars": stars, "pr": pr_of(e)}


def build():
    stars = load_stars()

    def repo_stars(name):
        n = int(stars.get(name, 0))
        return stars_display(n), n

    entries = sorted(load_entries(), key=lambda e: -e["seq"])
    flat = [flat_item(e, repo_stars(e["repo"])[0]) for e in entries]
    by_key = {e["repo"] + " " + e["pr_label"]: flat[i] for i, e in enumerate(entries)}

    repos = {}
    for e in entries:
        disp, num = repo_stars(e["repo"])
        r = repos.setdefault(e["repo"], {
            "name": e["repo"], "url": e["repo_url"], "stars": disp,
            "stars_num": num, "top_seq": e["seq"], "prs": [],
        })
        r["prs"].append(pr_of(e))
        r["top_seq"] = max(r["top_seq"], e["seq"])
    repo_list = sorted(repos.values(), key=lambda r: -r["stars_num"])

    featured = []
    for item in json.load(open(FEATURED_FILE, encoding="utf-8")):
        rec = by_key.get(item["key"])
        if rec:
            featured.append({"repo": rec["repo"], "repo_url": rec["repo_url"],
                             "stars": rec["stars"], "blurb": item["blurb"], "pr": rec["pr"]})

    stacks = {t for e in entries for t in e["stack"]}
    data = {
        "stats": {
            "merged": len(entries), "repos": len(repos),
            "stars": sum(r["stars_num"] for r in repo_list), "stacks": len(stacks),
            "found": sum(1 for e in entries if e["origin"] == "found"),
            "known": sum(1 for e in entries if e["origin"] == "known"),
        },
        "repos": repo_list,
        "recent": flat[:6],
        "featured": featured,
    }
    open(OUT, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
    s = data["stats"]
    print("wrote %s: %d prs, %d repos, %d stars, %d stacks | recent %d, featured %d"
          % (OUT, s["merged"], s["repos"], s["stars"], s["stacks"], len(data["recent"]), len(featured)))


if __name__ == "__main__":
    build()
