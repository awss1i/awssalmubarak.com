<h1 align="center">Translating the Docs</h1>

---

<p align="center">This repository's docs are kept in English, Simplified Chinese, Japanese,
Korean and Russian. English is the source. This page is the convention every translation follows, and
<a href="glossary.md">glossary.md</a> fixes the word used for each term in each language.</p>

---

## Contents

- [What Is Translated](#what-is-translated)
- [File Names](#file-names)
- [The Language Switcher](#the-language-switcher)
- [Headings and Anchors](#headings-and-anchors)
- [What Stays in English](#what-stays-in-english)
- [Links](#links)
- [Writing](#writing)
- [Keeping Translations Current](#keeping-translations-current)
- [The Closing Note](#the-closing-note)

---

## What Is Translated

These docs have a translation in each of the four languages:

- `README.md`
- `bench/README.md`

Everything else stays in English, including the entries and other files in `data/`, which the
site's pipeline reads, the page templates in `site/`, and this page and the glossary.

To translate another doc, add all four translations in the same change and list it above.

---

## File Names

A translation sits next to its English source, with the language code before `.md`:

| Language | Code | Example |
|---|---|---|
| Simplified Chinese | `zh-CN` | `bench/README.zh-CN.md` |
| Japanese | `ja` | `bench/README.ja.md` |
| Korean | `ko` | `bench/README.ko.md` |
| Russian | `ru` | `bench/README.ru.md` |

Because a translation is in the same folder as its source, relative links and image paths work
unchanged.

---

## The Language Switcher

Every translated doc and its English source carry the same switcher, a centred line directly
under the title. The current language is bold and unlinked, the others are links, and the order
is always English, 简体中文, 日本語, 한국어, Русский. In `README.md` it looks like this.

```html
<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.ko.md">한국어</a> · <a href="README.ru.md">Русский</a></p>
```

In `README.ja.md` the same line reads like this.

```html
<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="README.ko.md">한국어</a> · <a href="README.ru.md">Русский</a></p>
```

---

## Headings and Anchors

Every heading below the title is translated, and starts with an anchor that carries the id GitHub
gives the English heading. For example, `## Run it` in English becomes this in Chinese.

```markdown
## <a id="run-it"></a>运行
```

The id is the English heading in lowercase, with spaces turned into hyphens and punctuation
removed. In-page links, the centred nav and the Contents lists keep the English fragment, like
`#run-it`, so the same link works in all five languages. A translation has the same headings in
the same order as its source, and the test checks that.

---

## What Stays in English

Keep these exactly as they are in the source:

- code blocks, except the explanatory `#` comments inside them
- commands, flags, file paths, URLs and anything else in backticks
- anything a script prints
- product and project names, like awssalmubarak.com, Python, GitHub and GitHub Pages
- acronyms, like DOM, CSS, SVG, URL and PR
- badges, and the images themselves

Translate everything else, including headings, image alt text, link text, the labels in the
centred nav, table headers and `#` comments in code blocks.

The first time a doc uses one of the glossary's terms, give the English in parentheses after the
translation, like `虚拟列表（virtualized list）`. After that, use the translation alone.

---

## Links

A link to a doc that has a translation points to the translation in the same language. A link to
an English-only file stays as it is. Keep the link's form and change only the file name.

---

## Writing

In every language, write the way the English is written, in plain, direct sentences that say who
does what. The README speaks in the first person, as Awss, so keep that voice, 我 in Chinese,
私 in Japanese, 저 in Korean and я in Russian. Don't use dashes of any kind, including the Chinese double dash
and the Japanese horizontal bar. Use a colon only to introduce a list, and don't join clauses with
a semicolon.

**Simplified Chinese.**

- Put one half-width space between Chinese and Latin letters, digits or inline code, like
  `2,500 个仓库`.
- Use full-width punctuation in prose, like `，。（）「」`, and half-width punctuation inside code.
- Address the reader as 你, never 您.

**Japanese.**

- Write in です/ます.
- Use katakana for general technical words, like ブラウザー and リポジトリ.
- Put a half-width space between Japanese and Latin letters, digits or inline code.
- Use full-width `、。` in prose, and 「」 around a UI label.

**Korean.**

- Use 합니다 for statements and 하세요 for instructions. Never address the reader as 당신.
- Write general technical words in Hangul, like 브라우저 and 저장소, and keep product names in
  English.
- Attach particles directly to Latin words and code.

**Russian.**

- Address the reader as вы, in lowercase, and give instructions in the plural imperative, like
  `Запустите`.
- A Russian past-tense verb shows the speaker's gender, like `я написал` or `я написала`. Phrase
  first-person sentences so no past-tense verb or short adjective has я as its subject, for
  example in the present tense or with `мой` and a noun.
- Write ё wherever it belongs, like `ещё` and `всё`.
- Use «» as quotation marks in prose. Straight quotes appear only inside code.
- Where Russian would join two nouns with a dash, write a verb like `является` instead, or
  rephrase the sentence, because the no-dash rule applies here too.
- Capitalise only the first word of a heading.
- Write decimals in prose with a comma, like `1,5 секунды`, and keep the point inside code.
- For Git and GitHub words, use the loanwords in the
  [Web Standards dictionary](https://github.com/web-standards/dictionary/blob/main/git.md), like
  коммит, форк and пулреквест.

---

## Keeping Translations Current

The first line of every translation records which version of its English source it was made
from, like this.

```html
<!-- i18n-source: bench/README.md 3f1c0d9e5a7b2c4d6e8f0a1b3c5d7e9f1a2b4c6d -->
```

The long hex number is the git blob id of the source file. `tests/test_translations.py` compares
it with the source as it is now, and fails when the English has changed since the translation was
made. It also fails when a translation's headings don't match its source, or when a translated doc
is missing one of the four languages. Run it with `python3 -m unittest discover -s tests`.

When the English changes:

1. See what changed with `git diff <id> HEAD:bench/README.md`, using the id from the
   translation's first line.
2. Update the matching part of all four translations.
3. Record the new version with
   `python3 docs/i18n/stamp.py bench/README.zh-CN.md bench/README.ja.md bench/README.ko.md bench/README.ru.md`.

Commit the English change and its translations together.

---

## The Closing Note

Each translation ends with a divider and this note, naming and linking its source:

- 简体中文: `本文是 [README.md](README.md) 的译文。如与英文原文不一致，以英文原文为准。如发现翻译错误，欢迎通过 pull request 修正。`
- 日本語: `このページは [README.md](README.md) の翻訳です。英語の原文と内容が異なる場合は、原文が優先されます。翻訳の誤りに気づいたら、プルリクエストで修正を送ってください。`
- 한국어: `이 문서는 [README.md](README.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.`
- Русский: `Эта страница является переводом [README.md](README.md). Если перевод расходится с английским оригиналом, верным считается оригинал. Если вы нашли ошибку в переводе, пришлите исправление через пулреквест.`
