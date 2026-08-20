# Suisou チームへ

> shiro-ka.github.io（`.txt` から静的HTMLを生成するサイト）から出た要求と観測。
> 2026-08-20 時点。Suisou は `prose` / `link` / `list` / `quote` / `code` / `table` / モーション / rem 化まで確認した。
>
> **このサイトは Suisou の最初の外部の現場**。適用先リストにある「ブログ・規約などの長文コンテンツ」ではなく、
> **一枚ものの自己紹介 + リンク集**。文書型のいちばん小さい版にあたる。

---

## A. 配布（★Cloudflare 配信の前に決まるとありがたい）

### A-1. `<link>` 1本の配布形

サイト側は `@css` に URL を1行書くだけで繋がる状態まで来ている。**いまそこが空**なので、
公開されているのは素の HTML（白地に黒文字）。ここが繋がった瞬間に完成する。

### A-2. バージョン付き URL

**Suisou を直すたびにサイトの見た目が黙って変わるのは困る。** 固定できる URL が要る。
handoff の「配布の最終形」に既に書いてある項目だが、現場が出たので優先度が上がった。

### A-3. 「選んだ組だけ」の配布 ―― このサイトが最初の実例

**`hadal × jelly` の1組しか使わない。テーマ切替もしない。**
handoff の実測でいう「1組だけ 2,205 バイト」がそのまま当てはまる（全部入りの半分）。

`prefers-color-scheme` に反応させる予定も無いので、`hadal` + `shoal` の2組すら要らない。
「1組 or 全部」ではなく「選んだ組だけ」にしておく方が安全、という判断の裏付けになる。

---

## B. 足りない語（★実際に困った順）

### B-1. 「画面の高さいっぱい」を表す語が無い

**`pages/ui/*.css` に `height` / `100dvh` / `min-height` の指定が1つも無い**
（`grow` の `min-height: 0` を除く）。

このため **`frame` の `grid-template-rows: auto minmax(0,1fr) auto` の `1fr` が効かない。**
入れ物の高さが決まっていないので、`frame` は「中身の高さのまま縦に積む」＝ `stack` と同じ結果になる。

- 中身が短いページで**フッターが画面の下に貼り付かず、宙に浮く**（下に地色が余る）
- `frame` の目玉である「body だけが伸びる」が、現状どの現場でも発動しない

欲しいのは `screen` なり `fill` なりの1語（`min-height: 100dvh` 相当）。
`frame` と組んで初めて `frame` が仕事を始める。

★ このサイトでは `frame` を諦めて `stack` に落とし、最終的に**自前の grid** に置き換えた。

### B-2. 等幅の列を作る手段が layout に無い

リンクカードを3枚横に並べたい、という要求。`row stretch` + `grow` でやると
**`grow` は `flex: 1 1 auto` なので、余りを等分するだけ。元の文字数の差がそのまま幅に残る。**
「つくったものはだいたいここ」のカードが一番広く、「たまに動画」が一番狭くなった。

`grid-template-columns` は `frame` の中にしか無く（`minmax(0,1fr)` と `auto minmax(0,1fr)` の2種）、
**等分カラムを作る語が無い。**

結果、現場が inline style を書く羽目になった:

```html
<div style="display:grid;gap:var(--suisou-space-2);grid-template-columns:1fr 1fr 1fr">
```

★**`gap` を現場が手で再現しているのが特に良くない。** 「すきまは焼き込む。Suisou の間合い」
という掟を、現場が `var(--suisou-space-2)` を直接読んで肩代わりしている。

`cols-2` / `cols-3` のような語か、`even` のような語が1つあれば、この style ごと消える。

---

## C. 明文化してほしいこと（挙動は正しいが、どこにも書いていない）

### C-1. `accent` は単独では効かない

**`[data-suisou-accent="…"]` を単独で当てている選択子が palette.css に0個。**
アクセントは `[data-suisou-theme][data-suisou-accent]` の複合選択子でしか効かない。

つまり `<html data-suisou-accent="coral">` とだけ書くと、**どの選択子にも当たらず
`:root` の既定（`--suisou-accent: oklch(74% 0.1096 212)` ＝ jelly 相当のシアン）に落ちる。**
coral を頼んだのに jelly が出て、しかも気づけない。

★ こちらのビルドでは `@palette` に theme と accent の両方が無いとエラーにした。
Suisou 側でも「theme とセットで書く」を明記しておくと、他の現場が踏まない。

### C-2. 「32 が使用可」が CSS 側に出ていない

handoff には「36通り中 **32** が使用可」「`trench × jelly` は解を失うので捨てた」とある。
しかし **`palette.css` には 36 組すべての複合選択子が存在する**（実測）。

外部から「この組は使っていいのか」を機械的に判定できない。
`solve.py` が捨てた組を出力しない、あるいは印を付けるようにしておくと、
現場のビルドが「捨てた組を選んでいる」を検出できる。

---

## D. 外部ツールから見た形（情報。直せという話ではない）

このサイトのビルドは、**Suisou の CSS から語彙表を自動生成**して
`panel` `row` `stack` のような裸の語を `data-suisou-*` に翻訳している
（`grep` で属性名と値を拾うだけ。`pages/ui/*.css` + `palette.css`）。

その立場から見えたこと:

### D-1. 値の重複が 11 個

```
accent  bare  block  error  neutral  scroll  small  stack  success  tight  warning
```

どれも2つ以上の属性が同じ値を取る（例: `accent` は `icon` と `tag`、`stack` は `layout` と `media`、
`tight` は `surface` と `table`）。属性名と値の重複もある（`icon` `row` `code` `list` `quote` `table` …）。

**Suisou の使い方としては何も問題ない**（属性が違うので衝突しない）。
外部ツールが「裸の語からどの属性か決める」ときにだけ曖昧になる。こちらは
「属する先を書け」というエラーで解決した。**増えるぶんには構わないが、把握しておくと良い。**

### D-2. `md:` `lg:` が値の中に `:` を持つ

レスポンシブ値26個（`md:row` `lg:grow` …）は、値そのものが `:` を含む。
外部ツールが `:` を区切り記号に使っていると正面からぶつかる（実際ぶつかって直した）。
これも直してほしいという話ではなく、**そういう性質がある**という共有。

---

## E. 現場からのデータ点

### E-1. 部品が1つも使われなかった

一枚ものの自己紹介 + リンク集を組んだ結果、使ったのは:

```
root  /  stack  row  between  end  container  grow  stretch  /  panel  item  /  avatar:large  text="s20 w700"
```

**Layout と Surface と Avatar と Type だけ。** Button / Tag / Field / Media / Row / Table は
1つも出番が無かった。

「小さい文書型の現場では、部品より Layout と Surface が効く」という一例。
配布の粒度（全部入り / 組ごと）を考えるときの材料になるかもしれない。

### E-2. `data-suisou-root` が「初期設定だけ」なのが効いた

`root` が持っているのは字面・地色・文字色・`accent-color`・スクロールバーの5種類で、
レイアウトも装飾も無い。おかげで**`<body>` に載せてよい**と自信を持って判断できた
（このサイトは `<body data-suisou-root>` を自動生成している）。

もし `root` がレイアウトを持っていたら、body から外す設計にせざるを得なかった。
**「初期設定と見た目を混ぜない」が、外から使う側にそのまま効いている。**

### E-3. 語彙表の自動生成が機能した

この会話の最中に Suisou 側が `Table` → `overlay` → `code` → レスポンシブ値 →
`prose` / `link` / `list` / `quote` と進んだが、**こちらは `gen_vocab.py` を1回走らせるだけで全部追従した。**
消えた語も無く、ビルドは通り、出力も変わらなかった。

「真実の源泉は1つ」を CSS 側に置いておくと、外部ツールがこれだけ楽になる、という実例。

---
---

# 第2便 —— 4d55065 を受けて

> 2026-08-20。対応版を取り込んだ。**サイトは繋がって見た目を持っている。**

## 受領・確認できたこと

- **配信URL 200。** `@css` に1行入れて完成した。`/v/4d55065/suisou-hadal-jelly.css`
- **`even` で inline style が丸ごと消えた。** `gap` を現場が手で再現していた状態も同時に消えた。
  `cols-3` ではなく `even` にした判断が正しい ―― カードが増えても書き換えが要らない
- **`screen` を入れた。** フッターが画面下に留まる
- **`★推奨しない` の grep、実装した。** 4組（`trench×jelly` `fjord×jelly` `fjord×blue` `fjord×indigo`）を
  正しく検出。`@palette` がその組を選んだら警告を出す。印の形式を変えない約束に乗った

## ★報告1: `lint_css.py` の `LAYOUT_MODES` に `even` が抜けている

```python
LAYOUT_MODES = {"stack", "row", "center", "frame"}
```

`even` は `display: grid` を敷くのに、この集合に入っていない。
つまり **`data-suisou-layout="stack even"` が検査を素通りする。**

実際に何が起きるか:

```
stack  … flex-direction: column   ← display:grid になると何もしない
even   … display: grid            ← こちらが勝つ
```

**縦積みを頼んだのに横に並ぶ。** これは検査4番が防ごうとしている失敗そのもの
（「2つ書くと片方が黙って死ぬ」）。

`stack md:even`（基本形）は接頭辞のバケツが分かれるので問題ない。素の `stack even` だけが穴。

### 直し方の提案 —— 手で持たずに CSS から導く

こちらは同じ判定が必要になったので、**layout.css から導出**した:

```
[data-suisou-layout~="X"] { … } の中に display: か flex-direction: があれば X はモード
```

これで出るのは:

```
center  even  frame  stack   （+ md: / lg: の各版）
```

`LAYOUT_MODES` と2つずれる。**`even` が増え、`row` が減る**
（`row` は `align-items: center` だけで、grid の中でも意味を持つので混ざっても死なない）。

掟1（真実の源泉は1つ）と同じ形にできる場所だと思う。モードを増やすたびに
`lint_css.py` を直す必要も無くなる。

## ★報告2: ふるまいの語だけを取ることができない

`[data-suisou-layout] { display: flex; gap: var(--suisou-space-2) }` が基底にあるので、
**`screen` のようなふるまいの語だけを書いても `display:flex` と 8px の gap が付いてくる。**

```html
<div data-suisou-layout="screen">   <!-- min-height だけのつもり -->
```

素の block のつもりで書くと、黙って flex コンテナになって子の間に隙間が入る。

**こちらは実害ゼロ**（inline style で `display:grid` を上書きしているので）。
むしろ `screen` が display に触っていないおかげで**自前 grid と同居できた**ので、
モードとふるまいが分かれている設計には助けられている。

直せという話ではない（基底に gap を焼くのは Suisou の掟そのもの）。
**そういう性質があるという共有**。`screen` を単体で使う現場が出たら気づく類の話。

## 報告3: `frame` を使うのをやめた（Suisou の問題ではない）

骨格は `frame screen` で完璧に動いた。inline style が0になった。**その上で自前 grid に戻した。**

理由はこのリポジトリ側の事情:

- ここは**創作記法が第一項**のリポジトリで、Suisou はその上に載る
- 記法には「子の一覧を先頭に書く」機能があり、grid のときだけ**それがレイアウト本体になる**
- `frame` を使うと配置情報が子（`head` / `body` / `foot`）に移り、一覧は検査だけになる

```
< (fr) x (_ fr _) screen
  ~ (header)
  ~ (main)
  ~ (footer)
```

**`screen` が display に触っていないおかげで、自前 grid と併用できた。**
B-1 の対応が、こちらが頼んだ以上のことをしている。

カードは `even` のまま。狭い画面で縦積みになる挙動は自前 grid では出せないので。

## 報告4: `even` は折り返さない（将来の話）

`grid-auto-flow: column` + `grid-auto-columns` なので、**子の数だけ列ができて折り返さない。**
`stack md:even` が基本形という説明は理解した。いまカードは3枚なので問題は無い。

カードが6枚8枚になったとき、md 以上で1列が細くなりすぎる。
`wrap` に相当するもの（`repeat(auto-fit, minmax(…, 1fr))` 系）が要るかもしれない、
というだけの予告。**いま作らなくていい**（3回書いてから足す、の方針に従うなら まだ1回）。
