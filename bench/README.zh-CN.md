<!-- i18n-source: bench/README.md 00192a64826ed0fbc7f91c5b40fb8f2d0097b553 -->

<h1 align="center">基准测试</h1>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b> · <a href="README.ja.md">日本語</a> · <a href="README.ko.md">한국어</a> · <a href="README.ru.md">Русский</a></p>

---

<p align="center">这个网站有两个页面无论列出多少内容都能保持流畅。贡献页面使用了虚拟列表（virtualized list），作品（builds）页面则通过媒体调度器（media scheduler）加载预览。借助这个文件夹，你可以在自己的机器上测量这两个页面，对比对象是同一页面的更简单版本。</p>

---

## <a id="contents"></a>目录

- [贡献记录](#the-contributions-ledger)
  - [运行](#run-it)
  - [我的测量结果](#what-i-measured)
- [作品页面](#the-builds-page)
  - [运行作品页面的基准测试](#run-the-builds-benchmark)
  - [我在作品页面上的测量结果](#what-i-measured-on-the-builds-page)

---

## <a id="the-contributions-ledger"></a>贡献记录

贡献页面使用了虚拟列表。只有视口（viewport）附近的行才会出现在 DOM 中，一个仓库的 pull request 只有在你展开它时才会生成，搜索经过防抖（debounce）处理，只筛选数据，而不是重建页面。这个基准测试（benchmark）把它和一个一次性渲染所有行的朴素版本进行对比。

### <a id="run-it"></a>运行

```
python3 bench/generate.py          # 2500 个仓库与约 14,000 个已合并的 PR
python3 bench/generate.py 5000     # 或者自己指定规模
python3 -m http.server             # 在仓库根目录下运行
```

然后打开这两个页面，查看每个页面顶部的横幅。

```
http://localhost:8000/bench/dist/naive.html
http://localhost:8000/bench/dist/virtual.html
```

每个横幅会显示 DOM 节点数、重新渲染一次整个列表所需的时间，以及可交互时间（time to interactive）。合成数据使用固定的随机种子，所以两个页面描述的是完全相同的数据集，这里的任何操作都不会触及 `data/` 中的真实条目（entry）。

### <a id="what-i-measured"></a>我的测量结果

数据为 2,500 个仓库和 13,724 个已合并的 pull request（merged pull request）：

| | 朴素实现（全部渲染） | 虚拟列表（本站） |
|---|---|---|
| DOM 节点 | 127,306 | 281 |
| 一次排序的重新渲染 | 279 ms | 3 ms |
| 可交互时间 | 534 ms | 312 ms |

绝对数值取决于你的硬件，但两者之间的对比关系不会变。朴素版本的页面在 DOM 中保存的节点数约为虚拟列表版本的 450 倍，重新渲染约慢 85 倍。而且朴素版本在搜索框中每按一次键都会重建整个列表，而真实页面无论数据集有多大，所做的工作量都是恒定的。

---

## <a id="the-builds-page"></a>作品页面

作品页面为每个作品显示一个预览，而一个实时预览（live preview）就是一个完整的网页。它的媒体调度器让每个预览一开始都是一张静态截图（still image），只在预览大部分进入视野后才让它变成实时的，同一时间最多保持两个实时预览，并在预览滚动到远处时把它变回静态截图。

`bench/builds.py` 会生成 300 个合成作品，它们轮流使用页面能显示的四种预览：终端图像、静态截图、实时页面和视频。它通过真实的作品页面模板，用三种方式渲染这些作品：

- 一次性加载全部内容
- 浏览器的懒加载（lazy loading），它无法懒加载视频，所以页面一打开，所有视频就开始下载
- 媒体调度器，也就是本站实际使用的方式

每个媒体 URL 都是唯一的，所以浏览器缓存无法掩盖任何一次下载。

### <a id="run-the-builds-benchmark"></a>运行作品页面的基准测试

```
python3 bench/builds.py            # 300 个作品
python3 bench/builds.py 600        # 或者自己指定规模
python3 bench/serve.py             # 在 8000 端口上提供仓库根目录
```

然后在 Chrome 中打开每个页面。

```
http://127.0.0.1:8000/bench/dist/builds-eager.html
http://127.0.0.1:8000/bench/dist/builds-lazy.html
http://127.0.0.1:8000/bench/dist/builds-scheduled.html
```

每个页面加载完一秒后，会以每秒 1,200 像素的速度把列表从顶部滚动到底部，然后在顶部显示一条横幅，列出这样做的开销。在地址后面加上 `?manual`，就可以自己滚动页面。

这里用 `bench/serve.py` 代替 `python3 -m http.server`，因为这些数字依赖三件内置服务器做不到的事。它关闭了缓存，所以每次运行都会重新下载所有内容。它像 GitHub Pages 一样响应范围请求，因为浏览器是分段获取视频的。它还会统计自己发送的每一个字节。浏览器自身的计时看不到实时预览在它的框架内下载的内容，也看不到中途被打断的视频。

### <a id="what-i-measured-on-the-builds-page"></a>我在作品页面上的测量结果

数据为 300 个作品，每种预览各 75 个，每个页面运行三次，取中间值。运行使用的是 Playwright 的 Chromium 153，采用新的无头模式，窗口大小为 1440×900，机器是运行 Linux 的 AMD Ryzen 7 255。

| | 全部加载 | 浏览器懒加载 | 调度器（本站） |
|---|---|---|---|
| 打开时下载的数据 | 38.6 MB，451 个请求 | 12.7 MB，78 个请求 | 0.47 MB，4 个请求 |
| 滚动完全部内容后下载的数据 | 48.7 MB | 48.7 MB | 38.6 MB |
| 同时实时的预览（最多） | 75 | 75 | 2 |
| DOM 节点数（最多） | 29,037 | 29,037 | 6,763 |
| 滚动时的长动画帧（long animation frame） | 7 | 3 | 0 |
| JS 堆（最多） | 31.8 MB | 29.1 MB | 3.6 MB |

打开页面时，调度器的开销约为全部加载版本的八十分之一，是浏览器懒加载版本的二十七分之一，而且无论列表多长，它的实时预览都保持在两个。懒加载版本的页面在打开时仍会下载所有视频，并且从不卸载实时页面，所以滚动到最后时，它持有的内容和一次性加载全部内容的页面一样多。

阅读这张表时需要知道几点：

- 长动画帧是指耗时超过 50 ms 的帧。无头 Chromium 绘制时没有真实的屏幕，所以这个数字统计的是页面上的缓慢工作，而不是你能看到的掉帧。它是各次运行之间波动最大的一项，浏览器懒加载版本从 0 到 66 不等。
- DOM 计数包括每个实时预览的文档，但不包括图像或视频内部的内容。
- Chrome 会自动暂停不在视野中的静音视频，所以在每个页面上，同一时间最多只有一个视频在播放。调度器在视频上的区别在于，它要等到需要时才下载视频。

---

本文是 [README.md](README.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。
