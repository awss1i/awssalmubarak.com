#!/usr/bin/env python3
"""Refresh every repository's star count from GitHub.

Reads the distinct repos from data/entries, asks GitHub for each repo's current star count,
and rewrites data/stars.json (the one place a repo's stars live). Then refreshes each build's
star count in data/builds.json from its GitHub url. The /starpass skill runs this, then
deploy.py publishes the result.

After the per-repo lines it prints a one-line summary and a proposed commit message, the
same text in a dry run and a real run, so the skill can show it and the user can approve it.

A repo whose lookup fails keeps its existing stored count rather than being zeroed, so a
transient network error never blanks a repo. The gh binary is read from the GH_BIN
environment variable (default "gh"), so a test can point it at a stub.

Usage: refresh_stars.py [--dry-run]
--dry-run fetches and prints the changes but writes nothing.
"""
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SITE_ROOT") or os.path.dirname(HERE)
ENTRY_DIR = os.path.join(ROOT, "data", "entries")
STARS_FILE = os.path.join(ROOT, "data", "stars.json")
BUILDS_FILE = os.path.join(ROOT, "data", "builds.json")
GH_BIN = os.environ.get("GH_BIN", "gh")


def front_matter(path):
    _, front, _ = open(path, encoding="utf-8").read().split("---\n", 2)
    meta = {}
    for line in front.strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    return meta


def ledger_repos():
    repos = set()
    for path in glob.glob(os.path.join(ENTRY_DIR, "*.md")):
        repo = front_matter(path).get("repo")
        if repo:
            repos.add(repo)
    return sorted(repos)


def live_stars(owner_repo):
    """The repo's current star count from GitHub, or None if the lookup fails."""
    p = subprocess.run([GH_BIN, "api", "repos/" + owner_repo, "--jq", ".stargazers_count"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr)
        return None
    try:
        return int(p.stdout.strip())
    except ValueError:
        return None


def owner_repo_from_url(url):
    marker = "github.com/"
    if marker not in url:
        return None
    parts = url.split(marker, 1)[1].strip("/").split("/")
    if len(parts) < 2:
        return None
    return parts[0] + "/" + parts[1]


def write_json(path, data, sort_keys):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=sort_keys, ensure_ascii=False)
        f.write("\n")


def refresh_store(dry):
    old = json.load(open(STARS_FILE, encoding="utf-8")) if os.path.exists(STARS_FILE) else {}
    new = {}
    changed = set()
    for repo in ledger_repos():
        n = live_stars(repo)
        if n is None:
            kept = int(old.get(repo, 0))
            new[repo] = kept
            print("%s: lookup failed, kept %d" % (repo, kept))
            continue
        before = old.get(repo)
        new[repo] = n
        if before is None or int(before) != n:
            changed.add(repo)
        print("%s: %s -> %d" % (repo, before if before is not None else "new", n))
    if not dry:
        write_json(STARS_FILE, new, sort_keys=True)
    return new, changed


def refresh_builds(dry):
    data = json.load(open(BUILDS_FILE, encoding="utf-8"))
    changed = set()
    for b in data.get("builds", []):
        slug = owner_repo_from_url(b.get("url", ""))
        if not slug:
            continue
        n = live_stars(slug)
        if n is None:
            print("build %s: lookup failed, kept %s" % (b.get("name"), b.get("stars")))
            continue
        before = b.get("stars")
        if str(n) != before:
            b["stars"] = str(n)
            changed.add(slug)
        print("build %s: %s -> %d" % (b.get("name"), before, n))
    if changed and not dry:
        write_json(BUILDS_FILE, data, sort_keys=False)
    return changed


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if any(a in ("-h", "--help") for a in argv):
        print(__doc__.strip())
        return 0
    dry = "--dry-run" in argv
    _new, store_changed = refresh_store(dry)
    build_changed = refresh_builds(dry)
    changed = store_changed | build_changed
    n = len(changed)
    noun = "repo" if n == 1 else "repos"
    message = "stars: refresh counts, %d %s changed" % (n, noun)
    print()
    print("%d %s changed" % (n, noun))
    print("proposed commit message")
    print("    " + message)
    if dry:
        print("dry run, wrote nothing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
