# 記法ドラフト v0.3（build.py で実装済み）

> 名前は付けない。このリポジトリだけの（真剣な）お遊び。
> gridベースの超省略HTML。`.txt` で書き、ビルド時に静的HTMLへ落とす。
> ★草案。確定したらパーサ側リポジトリの README に移す。

---

## ★ Suisou との関係

**v0.1 では「言語はCSSを知らない」と書いたが、撤回する。**
Suisou 前提で属性を溶かす。汎用性は捨てる。`panel` と書いたら `data-suisou-surface="panel"` になる。

代わりに、**語彙表を手で持たない**。Suisou の `pages/ui/*.css` と `palette.css` を
パーサが読んで属性名と値の対応を作る。理由:

- Suisou はまだ固まっておらず、破壊的変更もありうる。手書きの表は必ずずれる
- 消えた値を使っていたら**ビルドが落ちる**。黙って効かないHTMLが出るより良い
- Suisou の掟1（真実の源泉は1つ）と同じ形になる

### 溶かし方

```
一意な語        … 裸で書く      panel / item / container / grow / outline / large …
ぶつかる語      … 属する先を書く  btn:icon / tag:accent / media:stack / row:ruled
値を持たない属性 … 裸で書く      root → data-suisou-root
```

ぶつかる語（実測11個）: `icon` `row` `stack` `small` `accent` `error` `success`
`warning` `bare` `block` `neutral`

`row` と `stack` は **layout が勝つ**（使用頻度が桁違い）。部品側は `row:` `media:` と書く。
★これは黙って選ぶのではなく決めた優先順位。パーサは他の候補も知っているので、
`row:` を書き忘れたときに「layout として解釈した」と言える。

### grid 宣言と Suisou layout の衝突（★唯一残る本物の干渉）

`(cols) x (rows)` は `grid-template-*` を inline style で吐く。
Suisou の `frame` も grid を組む。**同じ要素に両方書くとエラーで落とす**（黙って片方を捨てない）。

---

## 1. 構造

`<` で開き、`>` で閉じる。**インデントは構造に影響しない**（読みやすさのためだけ）。

```
<tag ~なまえ 語 語 key=value key="複数 の 値"
  中身
>
```

- `<` の直後がタグ名。省略すると `div`。`<>` は空の div
- **`~` で始まる語が「なまえ」**（0個か1個）。grid の区画割りから参照される
- **裸の語 = Suisou の語彙**。`group:value` も Suisou（値まで検証する）
- **`key=value` は素のHTML属性**。Suisou には触らない。`:` と `=` で世界が分かれる
- **行内の本文は `"…"` で囲む**。`<small "たまに動画" >`。
  ★囲まないと「キーワードか本文か」をパーサが判定できず、**キーワードのtypoが黙って本文になる**。
  囲む形なら未知の語は必ずエラーになる
- `>` だけの行が閉じ括弧
- **void 要素（`img` `meta` `link` `br` `hr` `input`）は閉じない。** ★v0.1 の穴

## 2. grid（★未実装。仕様として残すだけ）

実物（index.txt / contents/home.txt）を書いたら**一度も使わなかった**ので実装を見送った。
Suisou の `frame` / `row` / `stack` / `grow` で足りてしまう。
`(` を含む行はそうと分かるエラーで落ちる。必要になったら build.py に足す。

```
<header (auto fr auto) x (2rem)
  ~ (~brand . ~menu)
  …
>
```

- `(列) x (行)` → `grid-template-columns` / `grid-template-rows`
- トラックは**空白区切り**（CSS と同じ）。`fr` 単体は `1fr` の略。値はCSSにそのまま通す
- `x (行)` は省略可。列だけ書ける
- **`~ (…)` は省略可。書かなければ自動配置。** ★v0.1 では必須にしていたが、
  実際に書いてみたら「並べたいだけのカード3枚に名前を3つ発明させる」だけで損だった
- `~` を書くなら1行ぶんが1つ。行の数だけ並べる ＝ `grid-template-areas`。`.` は空きセル

★この `~` が「子要素を先に宣言する」の実体。別の仕組みを足さなくても、
ブロックの頭で子の顔ぶれと配置が分かる。2つの要求が1つに畳めた。

## 3. Markdown 風味

| 書く | なる |
|---|---|
| `# text` | `<h1>` … `######` まで |
| `- text` | `<li>`。連続する `-` は `<ul>` にまとまる |
| `[text](url)` | `<a href>` ★未決 |
| `![alt](src)` | `<img>` |
| `` `code` `` | `<code>` |
| `**text**` | `<strong>` |
| 裸の行 | テキスト。連続すると `<p>` |

タグ形式でも書ける。`# しろか.` と `<# しろか. >` は同じもの。
**なまえや語を付けたいときはタグ形式** … `<# ~brand s24 w700`

## 4. コンパイラ指令（`@`）

```
@lang   ja
@site   しろか.                <title> の後ろに付く固定部分
@title  ホーム                 ページ側。<title>ホーム | しろか.</title>
@desc   …
@css    https://…/suisou.css   複数可、書いた順
@icon   /img/favicon.svg
@palette hadal × jelly         html 要素に付く Suisou の色。テーマとアクセント
@content                       ★骨格に開ける穴
```

`<!DOCTYPE>` `<html>` `<head>` は書かない。指令から生成する。

**`@palette` の値は属性名を書かない。** `hadal` はテーマにしか無く `jelly` はアクセントにしか
無いので、**値が自分でどの属性のものか名乗る**。裸の語の規則（§ Suisou との関係）がそのまま効く。
どの属性が `<html>` に付くかは `palette.css` に出るかどうかで導いている（`vocab.json` の `root_attrs`）。

`×` は読み飛ばす。Suisou が handoff で「hadal × jelly」「4テーマ × 9アクセント」と
書いているのに合わせた。無くても通る。

★**両方書かないとエラー。** accent は `[theme][accent]` の複合選択子でしか効かないので、
theme を省くと指定した色が当たらず `:root` の既定にそのまま落ちる ―― しかもそれに気づけない。
`@palette coral` と書いて jelly が出るのが一番まずい失敗なので、落とす。

★以前は `@root theme:hadal accent:jelly` と書いていたが、`root` が
「文書のルート（`<html>`）」と Suisou の `data-suisou-root`（`<body>` に付く）の
両方を指していて紛らわしかったのでやめた。

**知らない指令はエラーで落ちる。** `@titel` のような書き損じが黙って捨てられない。

## 5. ファイル構成

```
index.txt         骨格。@content を1つ持つ。全ページに焼き込まれる
contents/*.txt    ページ本文。1枚が1つのHTML
img/              そのままコピー
```

`contents/home.txt` → `index.html`。`contents/works.txt` → `works.html`。

## 6. コメント ―― 無い

**コメントを持たない。** JSON と同じで、`//` で始まる行はパースエラーで落ちる。

記法そのものが「子要素を先に列挙する」形で画面の見た目に対応しているので、
**説明が要るなら記法のほうが失敗している**。説明はこのブランチの `.notes/` に置く。

黙って本文にせずエラーにしているのは、書いたコメントがそのままページに出るのが
一番まずい失敗だから。

---

## ★未決

1. **リンクの書き方**。`[ホーム](/)` か `[/] ホーム` か。★考え中。
   本文中にリンクが出る場面が来たら決める（今は nav にしか無い）
2. **`>` で始まるテキスト行**。閉じ括弧と Markdown の引用が食い合う
3. **ページ遷移**。`@view-transition { navigation: auto; }` は CSS 側の仕事。
   Suisou に入れるか、サイト固有の style.css に置くか
4. **パーサ側リポジトリ名**。言語には名前を付けないが、リポジトリ名は要る。
   `txt2html` のような味気ないものを推す（味気ないほうが企画に効く）

---

## 実装（このブランチ）

```
build.py              index.txt + contents/*.txt → dist/*.html
vocab.json            Suisou の語彙表（生成物。手で編集しない）
tools/gen_vocab.py    Suisou の css から vocab.json を作り直す
```

```sh
python3 tools/gen_vocab.py ~/dev/Suisou   # Suisou を触ったときだけ
python3 build.py --src ../shiro-ka.github.io --out dist
```

★ビルド時に Suisou を見に行かない。あちらの事故でサイトのビルドを止めないため。
`vocab.json` はこのブランチにコミットしてある。
