<h1 align="center">Benchmark</h1>

<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.ko.md">한국어</a> · <a href="README.ru.md">Русский</a></p>

---

<p align="center">Two pages on this site are built to stay fast however much they list. The
contributions page virtualizes its list, and the builds page loads its previews through a media
scheduler. This folder lets you measure both, on your own machine, against simpler versions of the
same pages.</p>

---

## Contents

- [The contributions ledger](#the-contributions-ledger)
  - [Run it](#run-it)
  - [What I measured](#what-i-measured)
- [The builds page](#the-builds-page)
  - [Run the builds benchmark](#run-the-builds-benchmark)
  - [What I measured on the builds page](#what-i-measured-on-the-builds-page)

---

## The contributions ledger

The contributions page virtualizes its list. Only the rows near the viewport are in the DOM, a
repository's pull requests are built only when you expand it, and search is debounced and filters
the data rather than rebuilding the page. This benchmark compares it with a naive version that
renders every row at once.

### Run it

```
python3 bench/generate.py          # 2500 repositories, about 14,000 merged PRs
python3 bench/generate.py 5000     # or choose your own size
python3 -m http.server             # from the repo root
```

Then open both pages and read the banner across the top of each:

```
http://localhost:8000/bench/dist/naive.html
http://localhost:8000/bench/dist/virtual.html
```

Each banner reports the DOM node count, the time to re-render the whole list once, and the time to
interactive. The synthetic data uses a fixed seed, so both pages describe exactly the same
dataset, and nothing here touches the real entries in `data/`.

### What I measured

With 2,500 repositories and 13,724 merged pull requests:

| | Naive (render everything) | Virtualized (this site) |
|---|---|---|
| DOM nodes | 127,306 | 281 |
| Re-render one sort | 279 ms | 3 ms |
| Time to interactive | 534 ms | 312 ms |

The absolute numbers depend on your hardware. The shape does not. The naive page holds about 450
times more nodes in the DOM and re-renders roughly 85 times slower, and the naive version rebuilt
that whole list on every keystroke in the search box, while the real page does constant work no
matter how large the dataset gets.

---

## The builds page

The builds page shows a preview of every build, and a live preview is a whole web page. Its media
scheduler starts every preview as a still image, makes one live only once it's mostly in view,
keeps at most two live at once, and drops a preview back to its still when it scrolls far away.

`bench/builds.py` generates 300 synthetic builds that cycle through the four kinds of preview the
page can show: a terminal image, a still image, a live page and a video. It renders them through
the real builds template three ways:

- loading everything at once
- the browser's lazy loading, which can't lazy load video, so every video starts downloading
  when the page opens
- the media scheduler, which is what the site ships

Every media URL is unique, so the browser's cache can't hide a download.

### Run the builds benchmark

```
python3 bench/builds.py            # 300 builds
python3 bench/builds.py 600        # or choose your own size
python3 bench/serve.py             # serves the repo root on port 8000
```

Then open each page in Chrome:

```
http://127.0.0.1:8000/bench/dist/builds-eager.html
http://127.0.0.1:8000/bench/dist/builds-lazy.html
http://127.0.0.1:8000/bench/dist/builds-scheduled.html
```

A second after it loads, each page scrolls its list from top to bottom at 1,200 pixels a second,
then shows a banner across the top with what that cost. Add `?manual` to the address to scroll a
page yourself instead.

`bench/serve.py` replaces `python3 -m http.server` here because the numbers depend on three
things the built-in server doesn't do. It turns caching off, so every run downloads everything
again. It answers range requests, the way GitHub Pages does, because browsers fetch video in
pieces. And it counts every byte it sends. The browser's own timing can't see what a live preview
downloads inside its frame, or video that was cut short.

### What I measured on the builds page

With 300 builds, 75 of each kind, taking the middle of three runs of each page. The runs used
Playwright's Chromium 153 in its new headless mode, with a 1440 by 900 window, on an AMD Ryzen 7
255 running Linux.

| | Load everything | Browser lazy loading | Scheduler (this site) |
|---|---|---|---|
| Downloaded on open | 38.6 MB in 451 requests | 12.7 MB in 78 requests | 0.47 MB in 4 requests |
| Downloaded after scrolling everything | 48.7 MB | 48.7 MB | 38.6 MB |
| Live previews at once, at most | 75 | 75 | 2 |
| DOM nodes, at most | 29,037 | 29,037 | 6,763 |
| Long animation frames while scrolling | 7 | 3 | 0 |
| JS heap, at most | 31.8 MB | 29.1 MB | 3.6 MB |

Opening the page costs the scheduler about 80 times less than loading everything and 27 times less
than the browser's lazy loading, and its live previews stay at two however long the list gets. The
lazy loading page still downloads every video on open, and it never unloads a live page, so by the
end of the scroll it holds as much as the page that loaded everything at once.

A few things to know when reading the table:

- A long animation frame is a frame that took more than 50 ms. Headless Chromium draws without a
  real screen, so this counts slow work on the page rather than dropped frames you'd see. It
  varied the most between runs, from 0 to 66 for the browser's lazy loading.
- The DOM count includes the document of every live preview, but not what's inside an image or a
  video.
- Chrome pauses a muted video that's out of view on its own, so on every page at most one video
  played at a time. The scheduler's difference with video is that it doesn't download one until
  it's needed.
