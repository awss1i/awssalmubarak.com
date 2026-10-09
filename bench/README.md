<h1 align="center">Benchmark</h1>

---

<p align="center">The contributions page virtualizes its list. Only the rows near the viewport are in the DOM, a
repository's pull requests are built only when you expand it, and search is debounced and filters
the data rather than rebuilding the page. This folder lets you measure what that buys, on your own
machine, against a naive version that renders every row at once.</p>

---

## Contents

- [Run it](#run-it)
- [What I measured](#what-i-measured)

---

## Run it

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

---

## What I measured

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
