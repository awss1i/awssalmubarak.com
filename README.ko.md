<!-- i18n-source: README.md 61b2a7a54cb57bd7d47644ec1f2649f925183dc6 -->

<p align="center">
  <img src="site/assets/favicon.svg" width="80" alt="awssalmubarak.com 로고">
</p>

<h1 align="center">awssalmubarak.com</h1>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <b>한국어</b> · <a href="README.ru.md">Русский</a></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/licence-MIT-7c3aed" alt="licence"></a>
  <a href="https://awssalmubarak.com"><img src="https://img.shields.io/badge/live%20at-awssalmubarak.com-7c3aed" alt="live at awssalmubarak.com"></a>
</p>

<p align="center">
  <a href="#the-virtualized-ledger">기록</a> · <a href="#the-builds-page">빌드 페이지</a> · <a href="#how-it-works">동작 방식</a> · <a href="#run-it">실행하기</a> · <a href="#tests">테스트</a> · <a href="#layout">구조</a> · <a href="#license">라이선스</a>
</p>

---

<p align="center">
  <img src="docs/images/home.jpg" alt="홈 페이지">
</p>

---

제 개인 사이트의 소스입니다. 런타임 의존성(dependency)도 프레임워크도 없는 정적 사이트(static site)이며, Python 표준 라이브러리만 쓰는 작은 파이프라인(pipeline)이 생성합니다. 기여 페이지는 병합된 풀 리퀘스트(merged pull request)가 스무 개든 2만 개든 부드럽게 동작하고, 빌드(builds) 페이지는 빌드가 몇 개든 지금 보고 있는 미리보기만 실행합니다.

---

## <a id="the-virtualized-ledger"></a>가상화된 기록

기여 페이지는 제가 만든 병합된 풀 리퀘스트를 모두 담은 기여 기록(contributions ledger)입니다. 제가 목표로 하는 규모라면 행이 수만 개에 이르므로, 이 목록은 순수 JavaScript로 직접 구현한 가상 리스트(virtualized list)입니다. 뷰포트(viewport) 근처의 행만 DOM에 들어 있고, 저장소의 풀 리퀘스트는 그 저장소를 펼칠 때만 만들어지며, 검색은 디바운스(debounce)를 적용하고 키를 누를 때마다 페이지를 다시 만드는 대신 데이터를 필터링합니다.

그 효과를 모든 행을 한꺼번에 렌더링하는 버전과 비교해 측정했습니다. 저장소 2,500개, 병합된 풀 리퀘스트 13,724개 기준입니다.

| | 단순 구현(모두 렌더링) | 가상 리스트(이 사이트) |
|---|---|---|
| DOM 노드 | 127,306 | 281 |
| 정렬 1회 재렌더링(re-render) | 279 ms | 3 ms |
| 상호작용 가능 시간(time to interactive) | 534 ms | 312 ms |

이 숫자를 그냥 믿을 필요는 없습니다. `bench/`를 사용하면 직접 사용하는 컴퓨터에서 이 숫자를 다시 측정할 수 있습니다. 자세한 내용은 [벤치마크](bench/README.ko.md)를 참고하세요.

![기여 기록](docs/images/contributions.jpg)

---

## <a id="the-builds-page"></a>빌드 페이지

빌드 페이지는 제가 만든 도구마다 그것이 무엇인지 보여 주는 창 안에 미리보기를 담아 보여 줍니다. 명령줄 도구는 터미널에서 실행되고, 웹사이트는 브라우저 창 안에서 실시간으로 실행됩니다. 미리보기를 클릭하면 크게 열립니다. 데스크톱에서는 제목이 그대로 있고 그 아래에서 빌드만 스크롤됩니다.

라이브 미리보기(live preview)는 웹 페이지 하나 전체이므로, 이런 미리보기가 모인 페이지는 금방 무거워집니다. 브라우저 자체의 지연 로딩(lazy loading)은 다운로드를 언제 시작할지만 정합니다. 무엇도 언로드하지 않고, 브라우저에는 동영상을 지연 로딩하는 기능이 아예 없습니다. 그래서 빌드 페이지는 순수 JavaScript로 작성한 미디어 스케줄러(media scheduler)를 통해 미리보기를 로드합니다.

- 모든 미리보기는 정지 이미지(still image)로 시작합니다.
- 미리보기는 대부분 화면에 들어온 상태로 0.25초 동안 머물러야 라이브로 바뀝니다. 한 번에 라이브인 미리보기는 최대 두 개입니다.
- 멀리 스크롤되어 벗어난 미리보기는 정지 이미지로 돌아가며, 이때 그 페이지나 동영상이 해제됩니다.
- 동영상은 화면 밖에 있는 동안 일시정지하고, 탭이 백그라운드에 있는 동안에는 모든 것이 대기합니다.
- 동작 줄이기나 데이터 절약을 요청한 사람에게는 정지 이미지만 보여 줍니다.

빌드 300개로 목록 전체를 일정한 속도로 스크롤하면서, 모든 것을 한꺼번에 로드하는 방식과 브라우저의 지연 로딩과 비교해 측정한 결과는 다음과 같습니다.

| | 모두 로드 | 브라우저 지연 로딩 | 스케줄러(이 사이트) |
|---|---|---|---|
| 열 때 다운로드한 양 | 38.6 MB | 12.7 MB | 0.47 MB |
| 동시에 라이브인 미리보기 | 75 | 75 | 2 |
| 최대 DOM 노드 | 29,037 | 29,037 | 6,763 |
| 최대 JS 힙 | 31.8 MB | 29.1 MB | 3.6 MB |

[벤치마크](bench/README.ko.md#the-builds-page)를 사용하면 직접 사용하는 컴퓨터에서도 이 결과를 측정할 수 있습니다.

![빌드 페이지](docs/images/builds.jpg)

---

## <a id="how-it-works"></a>동작 방식

이 사이트는 손으로 관리하지 않고 생성합니다. 병합된 풀 리퀘스트 하나는 `data/entries/` 안의 작은 마크다운 파일 하나입니다. `bin/site_data.py`가 이 파일들을 읽어 `data/contributions.json`을 만들고, `bin/build_pages.py`가 그 데이터를 세 페이지에 인라인으로 넣습니다. 그래서 각 페이지는 스타일시트와 폰트 외에는 추가 요청 없이 로드됩니다. `bin/deploy.py`는 빌드된 페이지를 GitHub Pages에 게시합니다. 저장소별 스타 수는 `data/stars.json` 한 곳에만 있고 `bin/refresh_stars.py`가 GitHub에서 모든 스타 수를 가져오므로, 어떤 스타 수도 항목(entry)에 복사되거나 실제 값과 어긋난 채로 남지 않습니다.

- 프레임워크도 빌드 도구도 없습니다. Python과 브라우저만 있으면 됩니다.
- 오른쪽 위의 색상 견본으로 바꾸는 테마(theme) 세 가지가 있으며, CSS 사용자 지정 속성으로 만들었습니다.
- 브라우저에서 그리는 생성형 SVG 배경이 있습니다. 홈 페이지에는 맞물린 톱니바퀴, 기록 뒤에는 git 병합 그래프, 빌드 페이지 뒤에는 제도용 청사진을 그립니다.
- 모든 페이지에 Content-Security-Policy를 적용하고, 데이터에서 온 모든 URL은 `href`에 들어가기 전에 검증합니다.

### <a id="the-three-themes"></a>세 가지 테마

| violet | slate | nordic |
|---|---|---|
| ![violet](docs/images/home.jpg) | ![slate](docs/images/theme-slate.jpg) | ![nordic](docs/images/theme-nordic.jpg) |

---

## <a id="run-it"></a>실행하기

```
python3 bin/site_data.py        # 항목을 data/contributions.json으로 변환
python3 bin/build_pages.py      # 데이터로 site/의 세 페이지를 생성
python3 -m http.server --directory site
```

그런 다음 http://localhost:8000 주소를 여세요.

---

## <a id="tests"></a>테스트

```
python3 -m unittest discover -s tests
```

테스트는 파이프라인과 페이지를 다룹니다.

- 다시 빌드해도 결과가 같고, 통계의 형태가 올바릅니다.
- 새 항목이 순번을 하나 늘리고 출력에 들어갑니다.
- 빌드된 페이지에 보안 강화 설정과 가상 리스트가 들어 있습니다.
- 빌드 페이지가 스케줄러를 통해 미리보기를 로드하고, 빌드는 스타 순서로 정렬됩니다.
- 두 벤치마크가 여전히 현재 템플릿으로 페이지를 만듭니다.
- 모든 번역이 영어 원문과 일치합니다.

---

## <a id="layout"></a>구조

```
bin/     the pipeline, reads entries, builds pages, deploys
data/    one markdown file per merged PR, plus the per-repo star counts, the builds and the featured picks
site/    the three page templates, the shared stylesheet and script, the built output
bench/   the reproducible performance benchmarks and the server that measures the builds page
tests/   the pipeline tests
```

---

## <a id="license"></a>라이선스

MIT입니다. [LICENSE](LICENSE)를 참고하세요.

---

이 문서는 [README.md](README.md)의 번역본입니다. 영어 원문과 내용이 다르면 원문이 우선합니다. 번역 오류를 발견하면 풀 리퀘스트로 수정해 주세요.
