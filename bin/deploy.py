#!/usr/bin/env python3
"""Rebuild the site and publish it: the built HTML to the GitHub Pages repo, and the source
to the public source repo.

Runs site_data and build_pages, mirrors the built site into the awss1i.github.io Pages clone
(home at /, contributions at /contributions, builds at /builds, shared files in /assets, and a
CNAME file so GitHub Pages serves the site at the custom domain), then commits the source repo
and pushes its history to the public source remote, and amends and force pushes the Pages repo
so it keeps its single commit. The Pages publish comes first, so a source-push hiccup never
blocks the live update. quarry runs this at step 7 on the user's go.

Usage: deploy.py "owner/repo #n" [--dry-run]
-h or --help prints this and does nothing. --dry-run rebuilds and locates the Pages clone but
copies nothing and runs no git.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SITE_ROOT") or os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
USAGE = 'usage: deploy.py "owner/repo #n" [--dry-run]'
# custom domain for GitHub Pages; written as a CNAME file at the Pages repo root
DOMAIN = "awssalmubarak.com"

# built page -> path inside the Pages repo
PAGES = {
    "index.html": "index.html",
    os.path.join("contributions", "index.html"): os.path.join("contributions", "index.html"),
    os.path.join("builds", "index.html"): os.path.join("builds", "index.html"),
}


def run(args, cwd=None, check=True, quiet=False):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if p.stdout.strip() and not quiet:
        print(p.stdout.strip())
    if p.returncode != 0 and check:
        sys.stderr.write(p.stderr)
        raise SystemExit("command failed: " + " ".join(args))
    return p


def find_pages():
    sibling = os.path.join(os.path.dirname(ROOT), "awss1i.github.io")
    if os.path.isdir(os.path.join(sibling, ".git")):
        return sibling
    base = os.path.dirname(os.path.dirname(ROOT))
    for dirpath, dirs, _ in os.walk(base):
        if ".git" in dirs:
            r = subprocess.run(["git", "-C", dirpath, "remote", "get-url", "origin"],
                               capture_output=True, text=True)
            dirs[:] = []
            if "awss1i.github.io" in r.stdout:
                return dirpath
    raise SystemExit("could not find the awss1i.github.io clone")


def copy_site(pages):
    for src_rel, dst_rel in PAGES.items():
        dst = os.path.join(pages, dst_rel)
        os.makedirs(os.path.dirname(dst) or pages, exist_ok=True)
        shutil.copyfile(os.path.join(SITE, src_rel), dst)
    # shared assets at /assets (replace the folder so stale files are dropped)
    dst_assets = os.path.join(pages, "assets")
    if os.path.isdir(dst_assets):
        shutil.rmtree(dst_assets)
    shutil.copytree(os.path.join(SITE, "assets"), dst_assets)
    # drop the old per-builds asset folder if it lingers from the previous layout
    old = os.path.join(pages, "builds", "assets")
    if os.path.isdir(old):
        shutil.rmtree(old)
    # custom domain: GitHub Pages reads this file to serve the site at the custom domain
    with open(os.path.join(pages, "CNAME"), "w", encoding="utf-8") as f:
        f.write(DOMAIN + "\n")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        print("rebuilds the site, commits and pushes the source repo, then force pushes the Pages repo.")
        return 0
    dry = "--dry-run" in argv
    rest = [a for a in argv if a != "--dry-run"]
    if not rest:
        print(USAGE, file=sys.stderr)
        return 2
    message = rest[0]
    if message.startswith("-"):
        print(f"refusing {message!r} as a commit message (it looks like a flag). " + USAGE, file=sys.stderr)
        return 2

    run([sys.executable, os.path.join(HERE, "site_data.py")])
    run([sys.executable, os.path.join(HERE, "build_pages.py")])

    pages = find_pages()
    print("pages clone:", pages)
    if dry:
        print("dry run: would mirror the site, commit and push the source repo as %r, then amend and force push the Pages repo" % message)
        return 0

    copy_site(pages)

    run(["git", "-C", ROOT, "add", "-A"])
    if run(["git", "-C", ROOT, "status", "--porcelain"], quiet=True).stdout.strip():
        run(["git", "-C", ROOT, "commit", "-m", message])
    else:
        print("source repo: nothing new to commit")

    run(["git", "-C", pages, "add", "-A"])
    if run(["git", "-C", pages, "status", "--porcelain"], quiet=True).stdout.strip():
        run(["git", "-C", pages, "commit", "--amend", "--no-edit"], quiet=True)
        run(["git", "-C", pages, "push", "-f", "origin", "HEAD"])
        print("deployed to awss1i.github.io")
    else:
        print("pages: no change to publish")

    p = run(["git", "-C", ROOT, "push", "origin", "HEAD"], check=False)
    print("source repo published to its remote" if p.returncode == 0
          else "source push did not go through, run git -C %s push later to publish it" % ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
