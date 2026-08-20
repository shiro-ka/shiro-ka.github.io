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
