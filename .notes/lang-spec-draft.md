# 記法ドラフト v0.2

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
- 裸の語は Suisou の語彙。`key=value` はそのまま属性
- `>` だけの行が閉じ括弧
- **void 要素（`img` `meta` `link` `br` `hr` `input`）は閉じない。** ★v0.1 の穴

## 2. grid

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
@root   theme=hadal accent=jelly   html 要素に付ける（Suisou 語彙が効く）
@content                       ★骨格に開ける穴
```

`<!DOCTYPE>` `<html>` `<head>` は書かない。指令から生成する。

## 5. ファイル構成

```
index.txt         骨格。@content を1つ持つ。全ページに焼き込まれる
contents/*.txt    ページ本文。1枚が1つのHTML
img/              そのままコピー
```

`contents/home.txt` → `index.html`。`contents/works.txt` → `works.html`。

## 6. コメント

`//` から行末。出力に残らない。

---

## ★未決

1. **リンクの書き方**。`[ホーム](/)` か `[/] ホーム` か。★考え中。
   本文中にリンクが出る場面が来たら決める（今は nav にしか無い）
2. **`>` で始まるテキスト行**。閉じ括弧と Markdown の引用が食い合う
3. **ページ遷移**。`@view-transition { navigation: auto; }` は CSS 側の仕事。
   Suisou に入れるか、サイト固有の style.css に置くか
4. **パーサ側リポジトリ名**。言語には名前を付けないが、リポジトリ名は要る。
   `txt2html` のような味気ないものを推す（味気ないほうが企画に効く）
