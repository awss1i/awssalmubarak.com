<!-- i18n-source: README.md 61b2a7a54cb57bd7d47644ec1f2649f925183dc6 -->

<p align="center">
  <img src="site/assets/favicon.svg" width="80" alt="awssalmubarak.com のロゴ">
</p>

<h1 align="center">awssalmubarak.com</h1>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="README.ko.md">한국어</a> · <a href="README.ru.md">Русский</a></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/licence-MIT-7c3aed" alt="licence"></a>
  <a href="https://awssalmubarak.com"><img src="https://img.shields.io/badge/live%20at-awssalmubarak.com-7c3aed" alt="live at awssalmubarak.com"></a>
</p>

<p align="center">
  <a href="#the-virtualized-ledger">台帳</a> · <a href="#the-builds-page">ビルドのページ</a> · <a href="#how-it-works">仕組み</a> · <a href="#run-it">実行方法</a> · <a href="#tests">テスト</a> · <a href="#layout">構成</a> · <a href="#license">ライセンス</a>
</p>

---

<p align="center">
  <img src="docs/images/home.jpg" alt="トップページ">
</p>

---

私の個人サイトのソースコードです。実行時の依存関係もフレームワークも使わない静的サイト（static site）で、Python の標準ライブラリだけで書いた小さなパイプラインで生成しています。コントリビューションのページは、マージ済みのプルリクエストが 20 件でも 2 万件でも、なめらかに動きます。ビルド（builds）のページは、ビルドがいくつ並んでいても、見ているプレビューだけを動かします。

---

## <a id="the-virtualized-ledger"></a>仮想化した台帳

コントリビューションのページは、私が作成してマージされたプルリクエストをすべて記録した台帳（ledger）です。私が目指している規模では行数が数万に達するため、リストは素の JavaScript で自前で仮想化しています。DOM に置くのはビューポート付近の行だけで、リポジトリのプルリクエストはそのリポジトリを展開したときに初めて組み立てます。検索にはデバウンスをかけ、キー入力のたびにページを組み立て直すのではなく、データを絞り込みます。

その効果を、すべての行を一度に描画する版と比べて測定しました。リポジトリ 2,500 件、マージ済みのプルリクエスト 13,724 件での結果です。

| | 単純な実装（すべて描画） | 仮想化（このサイト） |
|---|---|---|
| DOM ノード数 | 127,306 | 281 |
| 並べ替え 1 回分の再レンダリング | 279 ms | 3 ms |
| 操作可能になるまでの時間（time to interactive） | 534 ms | 312 ms |

この数値をそのまま信じる必要はありません。`bench/` を使えば、自分のマシンで同じ数値を生成し直せます。詳しくは[ベンチマーク](bench/README.ja.md)を参照してください。

![コントリビューション台帳](docs/images/contributions.jpg)

---

## <a id="the-builds-page"></a>ビルドのページ

ビルドのページには、私が作ったツールを 1 つずつ、それが何かがわかるウィンドウに入れたプレビュー付きで表示しています。コマンドラインツールはターミナルの中で動き、Web サイトはブラウザーのウィンドウの中で実際に動きます。プレビューをクリックすると、大きく表示されます。デスクトップでは、タイトルはその場に留まり、その下でビルドだけがスクロールします。

ライブプレビュー（live preview）は Web ページ 1 つ分まるごとなので、並べるとすぐに重くなります。ブラウザー自身の遅延読み込み（lazy loading）が決めるのは、ダウンロードを始めるタイミングだけです。一度読み込んだものを解放することはなく、動画にはそもそも遅延読み込みがありません。そこでビルドのページは、素の JavaScript で書いたメディアスケジューラー（media scheduler）を通してプレビューを読み込みます。

- どのプレビューも、最初は静止画（still image）です。
- プレビューがライブになるのは、大部分が画面に入り、そのまま 4 分の 1 秒とどまってからです。同時にライブになるのは最大 2 つです。
- 遠くまでスクロールされたプレビューは静止画に戻り、そのページや動画を解放します。
- 動画は画面の外にある間は一時停止し、タブがバックグラウンドにある間はすべて待機します。
- 動きを減らす設定やデータ通信量を減らす設定を選んでいる人には、静止画だけを表示します。

その効果を、ビルド 300 件のリスト全体を一定の速度でスクロールして、すべてを一度に読み込む版、ブラウザーの遅延読み込みと比べて測定しました。

| | すべてを読み込む | ブラウザーの遅延読み込み | スケジューラー（このサイト） |
|---|---|---|---|
| 開いたときのダウンロード量 | 38.6 MB | 12.7 MB | 0.47 MB |
| 同時に動くライブプレビュー | 75 | 75 | 2 |
| DOM ノード数の最大値 | 29,037 | 29,037 | 6,763 |
| JS ヒープの最大値 | 31.8 MB | 29.1 MB | 3.6 MB |

[ベンチマーク](bench/README.ja.md#the-builds-page)を使えば、これも自分のマシンで測定できます。

![ビルドのページ](docs/images/builds.jpg)

---

## <a id="how-it-works"></a>仕組み

このサイトは手作業で管理するのではなく、生成しています。マージ済みのプルリクエスト 1 件ごとに、`data/entries/` に小さな Markdown ファイルが 1 つあります。`bin/site_data.py` がそれらを読み込んで `data/contributions.json` を書き出し、`bin/build_pages.py` がそのデータを 3 つのページに埋め込みます。そのため、各ページはスタイルシートとフォント以外のリクエストなしで読み込めます。`bin/deploy.py` は、ビルドしたページを GitHub Pages に公開します。各リポジトリのスター数は `data/stars.json` の 1 か所だけに置き、`bin/refresh_stars.py` がすべての数を GitHub から取得します。そのため、スター数がエントリーにコピーされたり、古い値のまま放置されたりすることはありません。

- フレームワークもビルドツールも使いません。必要なのは Python とブラウザーだけです。
- 3 つのテーマ。右上のスウォッチで切り替えられ、CSS カスタムプロパティで実装しています。
- ブラウザーで描画する、プログラムで生成した SVG の背景。トップページにはかみ合う歯車、台帳の背景には git のマージグラフ、ビルドのページの背景には製図の青写真を描きます。
- すべてのページに Content-Security-Policy を設定し、データ由来の URL はすべて、`href` に入る前に検証します。

### <a id="the-three-themes"></a>3 つのテーマ

| violet | slate | nordic |
|---|---|---|
| ![violet](docs/images/home.jpg) | ![slate](docs/images/theme-slate.jpg) | ![nordic](docs/images/theme-nordic.jpg) |

---

## <a id="run-it"></a>実行方法

```
python3 bin/site_data.py        # エントリーから data/contributions.json を生成
python3 bin/build_pages.py      # データから site/ の 3 つのページを生成
python3 -m http.server --directory site
```

その後、http://localhost:8000 を開きます。

---

## <a id="tests"></a>テスト

```
python3 -m unittest discover -s tests
```

テストはパイプラインとページを対象にしています。

- 再ビルドの結果が再現でき、統計の形式が正しいこと。
- 新しいエントリーで連番が 1 つ増え、出力に反映されること。
- ビルドしたページにセキュリティ強化と仮想リスト（virtualized list）が含まれていること。
- ビルドのページがスケジューラーを通してプレビューを読み込み、ビルドがスター数の順に並ぶこと。
- 2 つのベンチマークが、現在のテンプレートからページを組み立てられること。
- すべての翻訳が英語の原文と一致していること。

---

## <a id="layout"></a>構成

```
bin/     the pipeline, reads entries, builds pages, deploys
data/    one markdown file per merged PR, plus the per-repo star counts, the builds and the featured picks
site/    the three page templates, the shared stylesheet and script, the built output
bench/   the reproducible performance benchmarks and the server that measures the builds page
tests/   the pipeline tests
```

---

## <a id="license"></a>ライセンス

MIT ライセンスです。詳しくは [LICENSE](LICENSE) を参照してください。

---

このページは [README.md](README.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。
