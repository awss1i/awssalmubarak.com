#!/usr/bin/env python3
"""Reproducible benchmark for the contributions ledger.

Generates a synthetic dataset of N repositories (default 2500, which works out to roughly 14,000
merged pull requests) and writes two pages from it into bench/dist/: the real virtualized page
this site ships, and a naive page that renders every row at once. Serve the repo root, open both,
and each prints its DOM node count, re-render time and time-to-interactive in a banner at the top,
so the difference is something you measure rather than take on trust. Nothing here touches the
real entries in data/.

  python3 bench/generate.py [N]
  python3 -m http.server              # from the repo root
  then open, in a browser:
    http://localhost:8000/bench/dist/naive.html
    http://localhost:8000/bench/dist/virtual.html
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(HERE, "dist")
STACKS = ["python", "rust", "go", "typescript", "javascript", "c++", "c", "java", "ruby", "php",
          "scala", "kotlin", "swift", "docker", "kubernetes", "postgres", "mysql", "redis",
          "react", "node", "linux", "bash", "cmake", "wasm", "sql", "graphql", "grpc", "terraform"]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def sfmt(n):
    if n >= 1_000_000:
        return str(round(n / 1e6, 2)) + "M"
    if n >= 1000:
        return str(round(n / 1e3)) + "k+"
    return str(n)


def generate(n):
    random.seed(42)
    repos, seq, total, stars_sum = [], 0, 0, 0
    for i in range(n):
        prs = []
        for _ in range(random.randint(1, 10)):
            seq += 1
            total += 1
            prs.append({
                "label": "#" + str(random.randint(100, 99999)),
                "url": "https://github.com/org%d/repo-%d/pull/%d" % (i, i, random.randint(1, 99999)),
                "date": random.choice(MONTHS) + " 2026",
                "stack": random.sample(STACKS, random.randint(1, 4)),
                "origin": random.choice(["known", "found"]),
                "seq": seq,
            })
        sn = random.randint(10, 500000)
        stars_sum += sn
        repos.append({"name": "org%d/repo-%d" % (i, i), "url": "https://github.com/org%d/repo-%d" % (i, i),
                      "stars": sfmt(sn), "stars_num": sn, "top_seq": max(p["seq"] for p in prs), "prs": prs})
    return {"stats": {"merged": total, "repos": n, "stars": stars_sum, "stacks": len(STACKS)},
            "repos": repos}, total


BANNER = """<script>
window.addEventListener("load",function(){setTimeout(function(){
  var nodes=document.getElementsByTagName("*").length;
  var t0=performance.now(); if(window.__bench_rerender) window.__bench_rerender(); var ms=performance.now()-t0;
  var nav=performance.getEntriesByType("navigation")[0]||{};
  var el=document.createElement("div");
  el.style.cssText="position:fixed;left:0;right:0;top:0;z-index:99999;background:#0b0b10;color:#8ef0a0;"
    +"font:600 13px/1.5 ui-monospace,Menlo,monospace;padding:10px 14px;text-align:center;border-bottom:1px solid #2e6b3e";
  el.textContent="__LABEL__   |   DOM nodes "+nodes.toLocaleString()+"   |   re-render "+ms.toFixed(1)
    +" ms   |   interactive "+Math.round(nav.domInteractive||0)+" ms";
  document.body.appendChild(el);
},400);});
</script>"""

VIRTUAL_RERENDER = ('<script>window.__bench_rerender=function(){'
                    'var b=document.querySelector(\'#sort button[data-s="newest"]\');if(b)b.click();};</script>')

NAIVE_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>benchmark: naive render</title>
<style>__SITECSS__</style>
<style>
.wrap{max-width:1200px;margin:0 auto;padding:60px 24px 80px}
h1{font-family:var(--display);font-weight:700;font-size:40px;margin:0 0 20px}
.repo{border-bottom:1px solid var(--line)}
.repo-head{display:flex;align-items:baseline;gap:12px;padding:13px 2px}
.repo-name{font-size:16px;font-weight:600}
.repo-stars{font-size:13.5px;font-weight:600;color:var(--star);margin-left:auto;white-space:nowrap}
.repo-n{font-size:12.5px;color:var(--muted);min-width:46px;text-align:right}
.repo-prs{padding:0 2px 14px 26px}
.prline{font-family:var(--mono);font-size:12.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:5px 10px;align-items:center;padding:4px 0}
.sep{color:var(--muted);opacity:.5;font-size:11px}
.prnum{color:var(--accent);font-weight:500}
.prstack{color:var(--read)}
</style>
</head>
<body class="page contrib">
  <main class="wrap">
    <h1>Contributions (naive render)</h1>
    <div class="list" id="list"></div>
  </main>
  <script id="data" type="application/json">__DATA__</script>
  <script>
  var D = JSON.parse(document.getElementById("data").textContent);
  function esc(x){ return String(x).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function prline(pr){
    var stack=(pr.stack||[]).join(", ");
    return '<div class="prline"><a class="prnum">'+esc(pr.label)+'</a>'
      +'<span class="sep">&middot;</span><span>'+esc(pr.date)+'</span>'
      +(stack?'<span class="sep">&middot;</span><span class="prstack">'+esc(stack)+'</span>':"")
      +'<span class="sep">&middot;</span><span class="origin '+pr.origin+'">'+(pr.origin==="found"?"found &amp; fixed":"known issue")+'</span>'
      +'</div>';
  }
  function repo(r){
    return '<div class="repo open"><div class="repo-head"><span class="caret">&#9656;</span>'
      +'<span class="repo-name">'+esc(r.name)+'</span>'
      +'<span class="repo-stars">&#9733; '+esc(r.stars)+'</span>'
      +'<span class="repo-n">'+r.prs.length+' prs</span></div>'
      +'<div class="repo-prs">'+r.prs.map(prline).join("")+'</div></div>';
  }
  function render(){ document.getElementById("list").innerHTML = D.repos.map(repo).join(""); }
  render();
  window.__bench_rerender = render;
  </script>
  __BANNER__
</body>
</html>
"""


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 2500
    data, total = generate(n)
    blob = json.dumps(data, ensure_ascii=False)
    os.makedirs(DIST, exist_ok=True)

    # inline the shared stylesheet and drop the external script so the pages are self-contained
    site_css = open(os.path.join(ROOT, "site", "assets", "site.css"), encoding="utf-8").read()
    tpl = open(os.path.join(ROOT, "site", "contributions.template.html"), encoding="utf-8").read()
    virtual = (tpl.replace('<link rel="stylesheet" href="/assets/site.css">', "<style>" + site_css + "</style>")
               .replace('<script src="/assets/site.js"></script>', "")
               .replace("__DATA__", blob)
               .replace("</body>", VIRTUAL_RERENDER + BANNER.replace("__LABEL__", "VIRTUALIZED (this site)") + "\n</body>"))
    naive = (NAIVE_PAGE.replace("__SITECSS__", site_css)
             .replace("__DATA__", blob)
             .replace("__BANNER__", BANNER.replace("__LABEL__", "NAIVE (render everything)")))

    open(os.path.join(DIST, "virtual.html"), "w", encoding="utf-8").write(virtual)
    open(os.path.join(DIST, "naive.html"), "w", encoding="utf-8").write(naive)
    print("generated %d repositories, %d merged PRs (%.2f MB of data)" % (n, total, len(blob) / 1e6))
    print("wrote bench/dist/virtual.html and bench/dist/naive.html")
    print("serve the repo root (python3 -m http.server) and open both under /bench/dist/")


if __name__ == "__main__":
    main(sys.argv)
