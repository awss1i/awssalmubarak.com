#!/usr/bin/env python3
"""Reproducible benchmark for how the builds page loads its previews.

Generates N synthetic builds (default 300) that cycle through the four kinds of preview the page
can show: a terminal image, a still image, a live page and a video. It renders them through the
real builds template three times into bench/dist/, once per loading policy:

  builds-eager.html      every preview loads and goes live at once
  builds-lazy.html       the browser's own lazy loading (loading="lazy"), and autoplaying video,
                         because browsers have no lazy loading for video
  builds-scheduled.html  the media scheduler this site ships

Each page waits a second after it loads, scrolls its list from top to bottom at a constant
1200 px/s, then shows a banner and sets window.__bench_result with what it cost: data and requests
on open, data after scrolling everything, the most live previews and playing videos at once, the
most DOM nodes (including each live preview's document), long animation frames during the scroll,
and the JS heap where Chrome reports it. Every media URL is unique, so the browser cache can't hide
a download. Nothing here touches the real data in data/.

  python3 bench/builds.py [N]
  python3 bench/serve.py              # serves the repo root on port 8000 and counts bytes
  then open, in Chrome:
    http://127.0.0.1:8000/bench/dist/builds-eager.html
    http://127.0.0.1:8000/bench/dist/builds-lazy.html
    http://127.0.0.1:8000/bench/dist/builds-scheduled.html

bench/sample.webm is 6 seconds of the home page, recorded with Playwright at 1200x1150 and encoded
with ffmpeg:
  ffmpeg -ss 2.5 -t 6 -i recording.webm -an -vf scale=640:614 -c:v libvpx-vp9 -b:v 0 -crf 34 \\
         -row-mt 1 bench/sample.webm
It's VP9 because Playwright's Chromium can't play H.264. bench/sample-poster.jpg is its first frame.
"""
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.environ.get("BENCH_DIST") or os.path.join(HERE, "dist")
sys.path.insert(0, os.path.join(ROOT, "bin"))
import build_pages  # noqa: E402

POLICIES = ("eager", "lazy", "scheduled")
LANGUAGES = ["Python", "Rust", "Go", "TypeScript", "HTML", "C++", "Zig", "Kotlin"]


def must_replace(text, old, new, count=1):
    """Replace old with new, and fail if the template no longer contains old exactly count times."""
    found = text.count(old)
    if found != count:
        raise SystemExit("bench: expected %d of %r in the template, found %d" % (count, old[:60], found))
    return text.replace(old, new)


def must_sub(text, pattern, new, count):
    out, found = re.subn(pattern, new, text)
    if found != count:
        raise SystemExit("bench: expected %d matches of %r in the template, found %d" % (count, pattern, found))
    return out


def served(path):
    """The URL path the bench server gives a file, which serves the repo root."""
    rel = os.path.relpath(path, ROOT)
    return "/" + (rel.replace(os.sep, "/") if not rel.startswith("..") else "bench/dist/" + os.path.basename(path))


def builds(n):
    random.seed(42)
    preview = served(os.path.join(DIST, "preview.html"))
    out = []
    for i in range(n):
        kind = ("terminal", "still", "page", "video")[i % 4]
        b = {
            "name": "build-%03d" % i,
            "url": "https://github.com/example/build-%03d" % i,
            "language": random.choice(LANGUAGES),
            "stars": str(random.randint(1, 50000)),
            "tagline": "A synthetic build, number %d, for measuring how previews load." % i,
            "features": ["Its preview is a %s" % {"terminal": "terminal image", "still": "still image",
                                                  "page": "live page", "video": "video"}[kind],
                         "Every media URL in this benchmark is unique",
                         "Nothing here touches the real builds"],
            "caption": kind,
            "alt": "build %d" % i,
        }
        if kind == "terminal":
            b.update(frame="terminal", media="site/assets/assay-run.svg?n=%d" % i)
        elif kind == "still":
            b.update(frame="plain", media="site/assets/site-home-{skin}.jpg?n=%d" % i)
        elif kind == "page":
            b.update(frame="browser", address="preview.example", media="site/assets/site-home-{skin}.jpg?n=%d" % i,
                     preview={"src": "%s?n=%d" % (preview, i), "width": 1200, "height": 1087})
        else:
            b.update(frame="plain", media="bench/sample-poster.jpg?n=%d" % i, video="bench/sample.webm?n=%d" % i)
        out.append(b)
    return out


# a self-contained animated page standing in for a live preview: turning gears and bobbing cards,
# about 300 elements, close to the real home page's cost
def preview_page():
    teeth = "".join('<rect x="96" y="2" width="8" height="18" rx="2" transform="rotate(%d 100 100)"/>' % (i * 15)
                    for i in range(24))
    gear = '<svg class="gear" viewBox="0 0 200 200"><circle cx="100" cy="100" r="78"/>%s</svg>' % teeth
    cards = "".join('<div class="card" style="animation-delay:-%.1fs"><b>card %d</b><span>one</span><span>two</span>'
                    '<span>three</span><em>a line of text in a card</em></div>' % (i * 0.37, i) for i in range(40))
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><title>preview</title><style>"
            "body{margin:0;background:#111116;color:#ececf2;font:14px system-ui;overflow:hidden}"
            ".gear{position:absolute;width:520px;height:520px;fill:none;stroke:#b388f5;stroke-width:3;opacity:.25;"
            "animation:spin 24s linear infinite}.gear.b{right:-120px;bottom:-140px;animation-duration:36s}"
            "@keyframes spin{to{transform:rotate(360deg)}}"
            ".grid{position:relative;display:grid;grid-template-columns:repeat(5,1fr);gap:16px;padding:40px}"
            ".card{background:#1a1a22;border:1px solid #2a2a34;border-radius:14px;padding:14px;display:flex;"
            "flex-direction:column;gap:4px;animation:float 7.5s ease-in-out infinite}"
            "@keyframes float{50%{transform:translateY(-8px)}}"
            "</style></head><body>" + gear + gear.replace('class="gear"', 'class="gear b"')
            + '<div class="grid">' + cards + "</div></body></html>")


HARNESS = r"""<script>
/* the benchmark harness: after the page loads, scroll the list at a constant speed, sample what
   the previews cost, then report. it turns off settle, which would otherwise finish scrolls. */
(function(){
  "use strict";
  var LABEL = "__LABEL__", SPEED = 1200;
  var box = document.getElementById("box"); box.setAttribute("data-no-settle", "");
  var loaf = [], peakLive = 0, peakVideos = 0, peakNodes = 0, heapPeak = 0;
  try { new PerformanceObserver(function(l){ loaf.push.apply(loaf, l.getEntries()); })
          .observe({type: "long-animation-frame", buffered: true}); } catch(e) {}
  function bytes(){ return fetch("/__bench/bytes", {cache: "no-store"}).then(function(r){ return r.json(); }); }
  // a live preview counts once its frame holds a loaded page, not while it's an empty placeholder
  function loaded(f){ try { var d = f.contentDocument; return !!(d && d.URL !== "about:blank" && d.body && d.body.firstChild); } catch(e) { return false; } }
  function nodes(){ var n = document.getElementsByTagName("*").length;
    [].forEach.call(document.querySelectorAll("iframe"), function(f){ if(loaded(f)) n += f.contentDocument.getElementsByTagName("*").length; });
    return n; }
  function sample(){
    peakLive = Math.max(peakLive, [].filter.call(document.querySelectorAll("iframe"), loaded).length);
    peakVideos = Math.max(peakVideos, [].filter.call(document.querySelectorAll("video"),
      function(v){ return !v.paused && !v.ended && v.readyState > 2; }).length);
    peakNodes = Math.max(peakNodes, nodes());
    if(performance.memory) heapPeak = Math.max(heapPeak, performance.memory.usedJSHeapSize);
  }
  function mb(n){ return (n / 1048576).toFixed(2) + " MB"; }
  function banner(r){
    var el = document.createElement("div");
    el.style.cssText = "position:fixed;left:0;right:0;top:0;z-index:99999;background:#0b0b10;color:#8ef0a0;"
      + "font:600 13px/1.5 ui-monospace,Menlo,monospace;padding:10px 14px;text-align:center;border-bottom:1px solid #2e6b3e";
    el.textContent = LABEL + "   |   on open " + mb(r.open_bytes) + " in " + r.open_requests + " requests"
      + "   |   after scrolling all " + mb(r.total_bytes) + "   |   live previews at most " + r.peak_live
      + "   |   videos playing at most " + r.peak_playing_videos + "   |   DOM nodes at most " + r.peak_dom_nodes.toLocaleString()
      + "   |   long frames " + r.long_frames + " (" + r.blocking_ms + " ms blocking)"
      + (r.heap_peak_mb ? "   |   JS heap at most " + r.heap_peak_mb + " MB" : "");
    document.body.appendChild(el);
  }
  function run(){
    sample();
    bytes().then(function(open){
      var o = getComputedStyle(box).overflowY, el = (o === "auto" || o === "scroll") ? box : null;
      var max = el ? el.scrollHeight - el.clientHeight : document.documentElement.scrollHeight - innerHeight;
      var t0 = performance.now(), tick = setInterval(sample, 500);
      function step(now){
        var y = Math.min(max, (now - t0) / 1000 * SPEED);
        if(el) el.scrollTop = y; else window.scrollTo(0, y);
        if(y < max) requestAnimationFrame(step); else setTimeout(finish, 1500);
      }
      function finish(){
        clearInterval(tick); sample();
        bytes().then(function(after){
          var during = loaf.filter(function(e){ return e.startTime >= t0; });
          var r = {label: LABEL, builds: document.querySelectorAll(".build").length,
            open_bytes: open.bytes, open_requests: open.requests, total_bytes: after.bytes, total_requests: after.requests,
            peak_live: peakLive, peak_playing_videos: peakVideos, peak_dom_nodes: peakNodes,
            long_frames: during.length,
            blocking_ms: Math.round(during.reduce(function(s, e){ return s + (e.blockingDuration || 0); }, 0)),
            heap_peak_mb: heapPeak ? +(heapPeak / 1048576).toFixed(1) : null,
            scroll_seconds: +((performance.now() - t0) / 1000).toFixed(1),
            media: window.__media || null,
            // where the worst long frames spent their time, so a regression can be traced
            worst_frames: during.slice().sort(function(a, b){ return b.blockingDuration - a.blockingDuration; }).slice(0, 5)
              .map(function(e){ return {ms: Math.round(e.duration), blocking: Math.round(e.blockingDuration),
                style_layout_ms: e.styleAndLayoutStart ? Math.round(e.startTime + e.duration - e.styleAndLayoutStart) : 0,
                scripts: (e.scripts || []).map(function(s){ return (s.invoker || s.invokerType) + " " + Math.round(s.duration) + "ms"; })}; })};
          window.__bench_result = r; banner(r);
        });
      }
      requestAnimationFrame(step);
    });
  }
  // ?manual leaves the page alone, to scroll it by hand
  if(/[?&]manual\b/.test(location.search)) return;
  if(document.readyState === "complete") setTimeout(run, 1000);
  else window.addEventListener("load", function(){ setTimeout(run, 1000); });
})();
</script>"""


def page(policy, data):
    html = build_pages.render("builds.template.html", data)
    css = open(os.path.join(ROOT, "site", "assets", "site.css"), encoding="utf-8").read()
    js = open(os.path.join(ROOT, "site", "assets", "site.js"), encoding="utf-8").read()
    # self-contained: no web fonts (external, and they make runs flaky), the shared CSS and JS
    # inlined, no favicons, and the policy set before the page script reads it
    html = must_sub(html, r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\n', "", 1)
    html = must_sub(html, r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/[^"]*">\n', "", 1)
    html = must_sub(html, r'<link rel="(?:icon|apple-touch-icon)"[^>]*>\n', "", 3)
    html = must_replace(html, '<link rel="stylesheet" href="/assets/site.css">', "<style>" + css + "</style>")
    html = must_replace(html, '<script src="/assets/site.js"></script>', "<script>" + js + "</script>")
    html = must_replace(html, "<title>Builds</title>", "<title>benchmark: builds, %s</title>" % policy)
    html = must_replace(html, '<script id="data"',
                        '<script>window.__buildsPolicy = "%s";</script>\n  <script id="data"' % policy)
    label = {"eager": "LOAD EVERYTHING", "lazy": "BROWSER LAZY LOADING", "scheduled": "MEDIA SCHEDULER (this site)"}[policy]
    return must_replace(html, "</body>", HARNESS.replace("__LABEL__", label) + "\n</body>")


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 300
    data = {"builds": builds(n)}
    os.makedirs(DIST, exist_ok=True)
    with open(os.path.join(DIST, "preview.html"), "w", encoding="utf-8") as f:
        f.write(preview_page())
    for policy in POLICIES:
        with open(os.path.join(DIST, "builds-%s.html" % policy), "w", encoding="utf-8") as f:
            f.write(page(policy, data))
    print("generated %d builds (%d of each kind of preview)" % (n, n // 4))
    print("wrote preview.html and builds-%s.html to %s" % ("/".join(POLICIES), os.path.relpath(DIST, ROOT)))
    print("run python3 bench/serve.py and open them under http://127.0.0.1:8000/bench/dist/")


if __name__ == "__main__":
    main(sys.argv)
