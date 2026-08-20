# 引き継ぎ

> 2026-08-20。企画を立て、記法を決め、パーサを書き、公開まで通した。
> **CSS が未接続の状態で一旦止めている。** 再開するときはここから。

---

## 企画

創作記法でサイトを書く。**リポジトリに `.txt` しか見えないのに Pages が動く**という状態そのものが作品。

`main` を覗いても HTML が1バイトも無く、パーサも見えず、GitHub は
「この言語で書かれています」を1つも言えない。

```
$ curl -s https://api.github.com/repos/shiro-ka/shiro-ka.github.io/languages
{}
```

★**成立を実測で確認済み。** 言語バーはデフォルトブランチだけを見るので、
`build` ブランチに Python が何百行あっても点灯しない。

---

## いまの形

```
main    index.txt / contents/home.txt / img/ / .github/workflows/build.yml
build   build.py / vocab.json / tools/gen_vocab.py / .notes/     （orphan。歴史を共有しない）
```

main への push → ワークフローが `build` を `.build/` に取ってくる → `build.py` → Pages。

- **`build` を直したときは Actions タブから手で回す。** orphan には `.github/` が無いので
  push トリガーを作れない。`workflow_dispatch` を入れてある
- 手元では worktree で両方同時に開く … `~/dev/shiro-ka.github.io` と `~/dev/shiro-ka.github.io-build`

```sh
python3 tools/gen_vocab.py ~/dev/Suisou              # Suisou を触ったときだけ
python3 build.py --src ~/dev/shiro-ka.github.io --out dist
```

---

## ★止まっている理由 ―― CSS が繋がっていない

いま公開されているのは**素の HTML**。白地に黒文字が縦に並んでいる。
`index.txt` の `@css` はコメントアウトしてあるので 404 は出ないが、見た目は何も無い。

### ここが厄介な制約

**サイト固有の css を `main` に置けない。** 置いた瞬間に言語バーが CSS で点灯して、
上の `{}` が壊れる ―― 企画の核がそこにあるので、これは譲れない。

**逃げ道:** css を `build` ブランチに置き、`build.py` に `dist` へコピーさせる。
`img` を同じことをしているので、実装は数行。**まだ書いていない。**

`@view-transition { navigation: auto; }`（ページ遷移のクロスフェード）も同じ置き場問題。
Suisou 本体に入れるなら不要になる。

---

## ★Suisou 側と相談すること

このサイトが Suisou の**最初の現場**になる。あちらの `.notes/handoff.md` で
「保留」「まだやらない」になっている項目に、具体的な要求が出た。

| Suisou 側の未決 | このサイトから出た要求 |
|---|---|
| 配布の最終形（CDN に置いて `<link>` 1本） | **実際に要る。** ここが繋がらないと公開物が裸のまま |
| バージョン付き URL | Suisou を直すたびにサイトの見た目が黙って変わるのは困る |
| 全部入りか1組だけか | このサイトは **`hadal` × `jelly` の1組しか使わない**。「選んだ組だけ」の最初の実例 |
| テーマ切替 | このサイトには要らない。切替を捨てて半分のバイト数を取れる側の実例 |

あちらの掟「Suisou 本体に JS を持ち込まない」とは衝突しない ―― こちらも JS ゼロ。

### 使った語彙（実測）

`root` `frame` `head` `body` `foot` `row` `between` `end` `container` `stack`
`grow` `stretch` `panel` `item` `avatar:large` `text="s20 w700"`

部品は1つも使っていない（Button / Tag / Field / Media / Row いずれも出番なし）。
**Layout と Surface だけで一枚もののサイトが組める**という結果になった。

---

## 記法について分かったこと

- **grid を実装しなかった。** 企画の当初の核だったが、実物を書いたら一度も使わなかった。
  Suisou の `frame` が「2次元が要る唯一の場所」を先回りして押さえていたため。
  仕様には残してあり、`(` を含む行はそうと分かるエラーで落ちる
- **`~ (…)`（子要素を先に宣言する）も同じ理由で出番なし。** 概念は気に入っているので、
  どこかで無理やり使うかもしれない
- 行内の本文を `"…"` で囲む形にしたのは、囲まないと
  **キーワードの typo が黙って本文になる**ため。囲めば未知の語は必ずエラーになる
- `:` は Suisou、`=` は素の HTML属性

## 次にやること（再開したらここから）

1. Suisou の配信先を決める（★Suisou 側と相談）
2. `build.py` に「`build` ブランチの css を `dist` へコピー」を足す
3. `index.txt` の `@css` を繋ぐ
4. リンクの書き方を決める … `[ホーム](/)` か `[/] ホーム` か（★保留のまま）
5. 中身を足す。いまは home 1枚だけ。ナビから `works` へのリンクは消してある
