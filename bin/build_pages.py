#!/usr/bin/env python3
"""Build the three site pages from the templates and the data.

  home          site/home.template.html          + stats, recent, featured, builds  -> site/index.html
  contributions site/contributions.template.html + stats, repos                     -> site/contributions/index.html
  builds        site/builds.template.html         + builds                           -> site/builds/index.html

The JSON is inlined into each page's data script, so the pages load with no further
requests beyond the shared /assets/site.css and /assets/site.js.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SITE_ROOT") or os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")


def inline(template_name, data, out_path):
    blob = json.dumps(data, ensure_ascii=False)
    assert "</script" not in blob.lower(), "data would close the script tag early"
    tpl = open(os.path.join(SITE, template_name), encoding="utf-8").read()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(tpl.replace("__DATA__", blob))
    print("wrote %s (%d bytes)" % (os.path.relpath(out_path, ROOT), os.path.getsize(out_path)))


def build():
    contrib = json.load(open(os.path.join(ROOT, "data", "contributions.json"), encoding="utf-8"))
    builds = json.load(open(os.path.join(ROOT, "data", "builds.json"), encoding="utf-8"))

    inline("home.template.html",
           {"stats": contrib["stats"], "recent": contrib["recent"],
            "featured": contrib["featured"], "builds": builds["builds"]},
           os.path.join(SITE, "index.html"))
    inline("contributions.template.html",
           {"stats": contrib["stats"], "repos": contrib["repos"]},
           os.path.join(SITE, "contributions", "index.html"))
    inline("builds.template.html",
           {"builds": builds["builds"]},
           os.path.join(SITE, "builds", "index.html"))


if __name__ == "__main__":
    build()
