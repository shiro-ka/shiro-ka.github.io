#!/usr/bin/env python3
"""index.txt + contents/*.txt を静的HTMLに落とす。

    python3 build.py --src . --out dist

記法は .notes/lang-spec-draft.md を見ること。
grid（`(cols) x (rows)` と `~ (…)`）は実装していない ―― 実物を書いたら一度も使わなかったため。
仕様には残してあるので、必要になったらここに足す。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

# ── HTML 側の事実 ───────────────────────────────
VOID = {"img", "meta", "link", "br", "hr", "input", "source",
        "col", "area", "base", "embed", "track", "wbr"}
# HTML の要素名。廃止されたもの（frame / marquee など）は入れない ――
# `< frame` を「div ＋ Suisou の frame」と読ませるため。
HTML_TAGS = set("""
a abbr address area article aside audio b base bdi bdo blockquote br button canvas
caption cite code col colgroup data datalist dd del details dfn dialog div dl dt em
embed fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 header hgroup hr i
iframe img input ins kbd label legend li link main map mark menu meta meter nav
noscript object ol optgroup option output p picture pre progress q rp rt ruby s samp
script search section select slot small source span strong style sub summary sup
table tbody td template textarea tfoot th thead time tr track u ul var video wbr
""".split())

# 中身が文そのものになるタグ。裸の行を <p> で包まない
TEXT_TAGS = {"p", "small", "li", "a", "span", "strong", "em", "code",
             "button", "label", "td", "th", "figcaption", "title", "summary",
             "h1", "h2", "h3", "h4", "h5", "h6"}

# ── 語彙の優先順位 ───────────────────────────────
# 黙って選ぶのではなく、決めた順序として書いておく。
FLAG = "@flag"          # 値を持たない属性として使う（data-suisou-icon など）
# コンパイラ指令。これ以外の @ は Suisou の root 属性（palette.css 由来）でなければエラー
DIRECTIVES = {"lang", "site", "title", "desc", "favicon", "css", "content", "palette"}
SEPARATOR = "×"         # @palette の読み飛ばし。Suisou が「hadal × jelly」と書くのに合わせた
OVERRIDE = {
    "icon": FLAG,       # 属性名でもあり btn の値でもある。裸なら属性名。btn 側は btn:icon
    "stack": "layout",  # layout / media 両方の値。使用頻度が桁違いなので layout
}


class BuildError(Exception):
    pass


# ── 語彙 ────────────────────────────────────────
class Vocab:
    def __init__(self, data: dict):
        self.attrs: set[str] = set(data["attrs"])
        self.root_attrs: list[str] = data["root_attrs"]   # html 要素に付くもの
        self.discouraged = {tuple(x) for x in data.get("discouraged", [])}
        self.modes: set[str] = set(data.get("layout_modes", []))
        self.values: dict[str, list[str]] = data["values"]
        self.by_attr: dict[str, list[str]] = {}
        for value, owners in self.values.items():
            for owner in owners:
                self.by_attr.setdefault(owner, []).append(value)

    def resolve(self, word: str, where: str) -> tuple[str, str | None]:
        """裸の語 → (属性名, 値)。値が None なら値なし属性。"""
        ov = OVERRIDE.get(word)
        if ov == FLAG:
            return f"data-suisou-{word}", None
        if ov:
            return f"data-suisou-{ov}", word

        owners = self.values.get(word)
        if owners:
            if len(owners) == 1:
                return f"data-suisou-{owners[0]}", word
            raise BuildError(
                f"{where}: `{word}` がどの属性の値か決まらない。"
                f"属する先を書く … " + " / ".join(f"{o}:{word}" for o in owners)
            )
        if word in self.attrs:
            return f"data-suisou-{word}", None

        near = [v for v in self.values if v.startswith(word[:2])][:4]
        hint = f"（近い語: {' '.join(near)}）" if near else ""
        raise BuildError(f"{where}: `{word}` は Suisou の語彙に無い{hint}")

    def qualified(self, group: str, value: str, where: str) -> str:
        if group not in self.attrs:
            near = " ".join(sorted(a for a in self.attrs if a.startswith(group[:3]))[:4])
            raise BuildError(
                f"{where}: `{group}:` という属性は Suisou に無い"
                + (f"（近い属性: {near}）" if near else "")
            )
        allowed = self.by_attr.get(group)
        if allowed is None:
            raise BuildError(f"{where}: `{group}` は値を取らない属性。`{group}` と裸で書く")
        if value not in allowed:
            raise BuildError(
                f"{where}: `{group}` に `{value}` という値は無い。"
                f"取れるのは … {' '.join(sorted(allowed))}"
            )
        return f"data-suisou-{group}"


# ── 木 ──────────────────────────────────────────
class Node:
    __slots__ = ("tag", "attrs", "children", "name", "grid", "areas", "line")

    def __init__(self, tag: str | None):
        self.tag = tag
        self.attrs: dict[str, str] = {}
        self.children: list = []
        self.name: str | None = None
        self.grid: tuple[str, str] | None = None   # (列, 行)
        self.areas: list[list[str]] = []           # ~ (…) の行
        self.line = 0

    @property
    def ident(self) -> str:
        """一覧から指すときの名前。~名前 が無ければタグ名。"""
        return self.name or self.tag or "?"

    def add_attr(self, key: str, value: str | None) -> None:
        if value is None:
            self.attrs.setdefault(key, None)
        elif self.attrs.get(key) is not None and self.attrs[key] != "":
            self.attrs[key] += " " + value      # 同じ属性の値は空白で足す
        else:
            self.attrs[key] = value


class Slot:
    """@content の穴。"""


# ── 行の下ごしらえ ───────────────────────────────
# 引用符の中の空白を割らないトークナイザ
TOKEN = re.compile(r'(?:[^\s"]|"[^"]*")+')
HEADING = re.compile(r'^(#{1,6})\s*(.*)$')


def extract_grid(body: str) -> tuple[tuple[str, str] | None, str]:
    """`(列) x (行)` を取り出す。引用符の中の括弧は見ない（URL に入りうる）。"""
    spans: list[tuple[int, int]] = []
    quoted = False
    depth = 0
    start = 0
    for i, ch in enumerate(body):
        if ch == '"':
            quoted = not quoted
        elif quoted:
            continue
        elif ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")":
            if depth:
                depth -= 1
                if depth == 0:
                    spans.append((start, i + 1))
    if not spans:
        return None, body

    cols = body[spans[0][0] + 1:spans[0][1] - 1].strip()
    rows = ""
    used = [spans[0]]
    if len(spans) > 1 and body[spans[0][1]:spans[1][0]].strip() == "x":
        rows = body[spans[1][0] + 1:spans[1][1] - 1].strip()
        used = [(spans[0][0], spans[1][1])]      # 間の `x` ごと消す

    out = body
    for a, b in reversed(used):
        out = out[:a] + " " + out[b:]
    return (cols, rows), out


TRACK = re.compile(r"""^(?:
    _ | auto | fr | min-content | max-content | none
  | \d+(?:\.\d+)?(?:fr|px|rem|em|%|vh|vw|dvh|dvw|ch|pt)
  | (?:minmax|repeat|fit-content|calc|clamp|min|max|var)\(.*\)
)$""", re.X)


def split_tracks(spec: str) -> list[str]:
    """空白で割る。ただし括弧の中は割らない（minmax(0, 1fr) が壊れる）。"""
    out, buf, depth = [], "", 0
    for ch in spec:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch.isspace() and depth == 0:
            if buf:
                out.append(buf)
                buf = ""
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


def track(spec: str, where: str) -> str:
    """`_` を `auto` に、`fr` を `1fr` に開く。ほかは通す前に検査する。"""
    parts = []
    for t in split_tracks(spec):
        if not TRACK.match(t):
            raise BuildError(
                f"{where}: `{t}` はトラックとして読めない。"
                "空白で区切って _ / fr / 2rem / minmax(0, 1fr) のように書く"
                + ("（カンマは使わない）" if "," in t else "")
            )
        parts.append({"_": "auto", "fr": "1fr"}.get(t, t))
    return " ".join(parts)


def unquote(s: str) -> str:
    return s[1:-1] if len(s) >= 2 and s[0] == '"' and s[-1] == '"' else s


# ── 行内の Markdown ──────────────────────────────
def inline(text: str) -> str:
    t = html.escape(text, quote=False)
    t = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)', r'<img src="\2" alt="\1">', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t


# ── 構文解析 ─────────────────────────────────────
class Parser:
    def __init__(self, vocab: Vocab, path: Path):
        self.vocab = vocab
        self.path = path
        self.directives: dict[str, list[str]] = {}
        self.root = Node(None)
        self.stack: list[Node] = [self.root]
        self.para: list[str] = []
        self.list_node: Node | None = None
        self.lineno = 0

    @property
    def where(self) -> str:
        return f"{self.path.name}:{self.lineno}"

    # -- 溜めているものを吐く --
    def flush_para(self) -> None:
        if not self.para:
            return
        text = "".join(self.para)
        parent = self.stack[-1]
        if parent.tag in TEXT_TAGS:
            parent.children.append(text)
        else:
            p = Node("p")
            p.children.append(text)
            parent.children.append(p)
        self.para = []

    def flush_list(self) -> None:
        self.list_node = None

    def flush(self) -> None:
        self.flush_para()
        self.flush_list()

    # -- 本体 --
    def parse(self, text: str):
        for i, raw in enumerate(text.splitlines(), 1):
            self.lineno = i
            line = raw.strip()
            if line.startswith("//"):
                raise BuildError(
                    f"{self.where}: コメントは無い。"
                    "説明が要る記法なら記法のほうが失敗している（仕様書 §6）"
                )
            if not line:
                self.flush()
                continue
            if line.startswith("@"):
                self.flush()
                self.directive(line)
            elif line == ">":
                self.flush()
                if len(self.stack) == 1:
                    raise BuildError(f"{self.where}: 閉じ括弧が多い")
                self.check_areas(self.stack.pop())
            elif line.startswith("<"):
                self.flush()
                self.element(line)
            elif line.startswith("~"):
                self.flush()
                self.areas(line)
            elif m := HEADING.match(line):
                self.flush()
                h = Node(f"h{len(m.group(1))}")
                h.children.append(inline(m.group(2)))
                self.stack[-1].children.append(h)
            elif line.startswith("- "):
                self.flush_para()
                if self.list_node is None:
                    self.list_node = Node("ul")
                    self.stack[-1].children.append(self.list_node)
                li = Node("li")
                li.children.append(inline(line[2:].strip()))
                self.list_node.children.append(li)
            else:
                self.flush_list()
                self.para.append(inline(line))

        self.flush()
        self.check_areas(self.root)
        if len(self.stack) != 1:
            open_tags = " ".join(n.tag or "?" for n in self.stack[1:])
            raise BuildError(f"{self.path.name}: 閉じていない要素がある … {open_tags}")
        return self.directives, self.root

    def check_areas(self, node: Node) -> None:
        """一覧と実際の子を突き合わせる。飾りにせず検査にする。"""
        if not node.areas:
            return
        listed = [n for row in node.areas for n in row if n != "."]
        actual = [c.ident for c in node.children if isinstance(c, Node)]
        unknown = [n for n in listed if n not in actual]
        if unknown:
            raise BuildError(
                f"{self.path.name}:{node.line}: 一覧に無い子がある … "
                f"{' '.join(unknown)}（実際の子: {' '.join(actual) or 'なし'}）"
            )
        # 一覧を書いたなら、それがレイアウトの本体。漏れは落とす
        # （自動配置に任せたいなら `~` を書かない）
        missing = [a for a in actual if a not in listed]
        if missing:
            raise BuildError(
                f"{self.path.name}:{node.line}: 一覧から漏れている子がある … "
                f"{' '.join(missing)}"
            )
        if not node.grid:
            if listed != actual:
                raise BuildError(
                    f"{self.path.name}:{node.line}: 一覧の順が実際と違う。"
                    f"一覧 {' '.join(listed)} / 実際 {' '.join(actual)}"
                )

    def directive(self, line: str) -> None:
        parts = line[1:].split(None, 1)
        key = parts[0]
        rest = parts[1].strip() if len(parts) > 1 else ""
        if key == "content":
            self.stack[-1].children.append(Slot())
            return
        if key not in DIRECTIVES:
            known = " ".join("@" + k for k in sorted(DIRECTIVES))
            raise BuildError(f"{self.where}: `@{key}` という指令は無い。あるのは … {known}")
        self.directives.setdefault(key, []).append(rest)

    def areas(self, line: str) -> None:
        parent = self.stack[-1]
        if parent.tag is None:
            raise BuildError(f"{self.where}: 一覧（`~`）は要素の中に書く")
        grid, rest = extract_grid(line[1:])
        if grid is None or rest.strip():
            raise BuildError(f"{self.where}: 一覧は `~ (a b c)` の形で書く")
        parent.areas.append(grid[0].split())

    def element(self, line: str) -> None:
        grid, body = extract_grid(line[1:])
        tokens = TOKEN.findall(body)
        close_here = bool(tokens) and tokens[-1] == ">"
        if close_here:
            tokens = tokens[:-1]

        # 最初の語は、HTML の要素名ならタグ。そうでなければ Suisou の語で、タグは div。
        tag = "div"
        if tokens and not self._is_modifier(tokens[0]):
            head = tokens[0]
            if re.fullmatch(r'#{1,6}', head):
                tag = f"h{len(head)}"
                tokens.pop(0)
            elif head in ("html", "head", "body"):
                raise BuildError(f"{self.where}: `{head}` は書かない。指令と骨格から生成する")
            elif head in HTML_TAGS:
                tag = head
                tokens.pop(0)
            elif head not in self.vocab.values and head not in self.vocab.attrs:
                raise BuildError(
                    f"{self.where}: `{head}` は HTML の要素名でも Suisou の語彙でもない"
                )

        node = Node(tag)
        node.grid = grid
        node.line = self.lineno
        for tok in tokens:
            self.token(node, tok)
        # 同居できないのは display / flex-direction を敷く語だけ。
        # screen や container のようなふるまいの語は一緒に書ける。
        if grid:
            clash = [v for v in node.attrs.get("data-suisou-layout", "").split()
                     if v in self.vocab.modes]
            if clash:
                raise BuildError(
                    f"{self.where}: `{' '.join(clash)}` は自前の grid と同じ要素に書けない。"
                    "どちらも display を決めるので一方が死ぬ"
                )

        self.stack[-1].children.append(node)
        if tag in VOID:
            if not close_here:
                return          # void は閉じない
            raise BuildError(f"{self.where}: `{tag}` は void 要素なので `>` で閉じない")
        if not close_here:
            self.stack.append(node)

    @staticmethod
    def _is_modifier(tok: str) -> bool:
        return tok.startswith(("~", '"')) or "=" in tok or ":" in tok

    def token(self, node: Node, tok: str) -> None:
        if tok.startswith("~"):
            node.name = tok[1:]                             # grid 用。今は出力しない
        elif tok.startswith('"'):
            node.children.append(inline(unquote(tok)))      # 行内本文
        elif "=" in tok and not tok.startswith(":"):
            key, _, val = tok.partition("=")
            node.attrs[key] = unquote(val)                  # 素の HTML 属性
        elif ":" in tok and tok not in self.vocab.values:
            group, _, val = tok.partition(":")
            node.add_attr(self.vocab.qualified(group, val, self.where), val)
        else:
            key, val = self.vocab.resolve(tok, self.where)
            node.add_attr(key, val)


# ── 出力 ────────────────────────────────────────
def esc_attr(v: str) -> str:
    """属性値。`"` で囲むので `'` は escape しない ―― CSS の文字列がそのまま読める。"""
    return (v.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace(chr(34), "&quot;"))


def add_style(node: Node, decls: list[str]) -> None:
    have = node.attrs.get("style", "")
    node.attrs["style"] = ";".join([d for d in decls] + ([have] if have else []))


def lay_grid(node: Node, where: str) -> None:
    """grid の宣言を inline style にする。Suisou に grid の語彙は無いので現場のものとして書く。"""
    cols, rows = node.grid
    decls = ["display:grid", "gap:var(--suisou-space-2)"]   # すきまは Suisou の間合いに合わせる
    if cols:
        decls.append(f"grid-template-columns:{track(cols, where)}")
    if rows:
        decls.append(f"grid-template-rows:{track(rows, where)}")
    if node.areas:
        # CSS は単引用符も受ける。属性値の中で " を使うと &quot; に化けて読めなくなる
        decls.append("grid-template-areas:" + " ".join(
            "'" + " ".join(row) + "'" for row in node.areas))
        listed = {n for row in node.areas for n in row if n != "."}
        for c in node.children:
            if isinstance(c, Node) and c.ident in listed:
                add_style(c, [f"grid-area:{c.ident}"])
    add_style(node, decls)


def render(node, out: list[str], depth: int = 0) -> None:
    if isinstance(node, Slot):
        raise BuildError("@content が骨格以外にある")
    if isinstance(node, str):
        out.append("  " * depth + node)
        return
    if node.tag is None:
        for c in node.children:
            render(c, out, depth)
        return

    if node.grid:
        lay_grid(node, f"{node.tag}:{node.line}")

    attrs = "".join(
        f" {k}" if v is None else f' {k}="{esc_attr(v)}"'
        for k, v in node.attrs.items()
    )
    pad = "  " * depth
    if node.tag in VOID:
        out.append(f"{pad}<{node.tag}{attrs}>")
        return
    if not node.children:
        out.append(f"{pad}<{node.tag}{attrs}></{node.tag}>")
        return
    if len(node.children) == 1 and isinstance(node.children[0], str):
        out.append(f"{pad}<{node.tag}{attrs}>{node.children[0]}</{node.tag}>")
        return
    out.append(f"{pad}<{node.tag}{attrs}>")
    for c in node.children:
        render(c, out, depth + 1)
    out.append(f"{pad}</{node.tag}>")


def graft(node: Node, page: Node) -> Node:
    """骨格の @content にページ本文を差し込む。"""
    new = Node(node.tag)
    new.attrs = dict(node.attrs)
    new.name, new.grid, new.areas, new.line = node.name, node.grid, node.areas, node.line
    for c in node.children:
        if isinstance(c, Slot):
            new.children.extend(page.children)
        elif isinstance(c, Node):
            new.children.append(graft(c, page))
        else:
            new.children.append(c)
    return new


def one(v: dict[str, list[str]], key: str, default: str = "") -> str:
    return v.get(key, [default])[0]


def document(shell_dir: dict, shell: Node, page_dir: dict, page: Node, vocab: Vocab) -> str:
    site = one(shell_dir, "site")
    title = one(page_dir, "title")
    full = f"{title} | {site}" if title and site else (title or site)

    root_attrs = ""
    seen: set[str] = set()
    picked: dict[str, str] = {}
    for tok in one(shell_dir, "palette").split():
        if tok == SEPARATOR:
            continue
        owners = [a for a in vocab.root_attrs if tok in vocab.by_attr.get(a, [])]
        if not owners:
            choices = " ".join(v for a in vocab.root_attrs for v in sorted(vocab.by_attr.get(a, [])))
            raise BuildError(f"@palette: `{tok}` は選べない。取れるのは … {choices}")
        attr = owners[0]
        if attr in seen:
            raise BuildError(f"@palette: {attr} を2つ書いている … `{tok}`")
        seen.add(attr)
        picked[attr] = tok
        root_attrs += f' data-suisou-{attr}="{tok}"'

    # 片方だけ書くと黙って願いと違うものが出る。
    # accent は [theme][accent] の複合選択子でしか効かないので、theme が無いと
    # 指定した色が当たらず :root の既定にそのまま落ちる ―― それに気づけない。
    if seen and (missing := [a for a in vocab.root_attrs if a not in seen]):
        raise BuildError(
            f"@palette: {' と '.join(missing)} が要る。"
            "片方だけだと指定した色が当たらず、既定のまま出る"
        )

    pair = (picked.get("theme"), picked.get("accent"))
    if pair in vocab.discouraged:
        print(f"⚠ @palette: {pair[0]} × {pair[1]} は Suisou が「見づらい」と印を付けた組。"
              "壊れてはいないが、ほかの組を選べるなら選ぶ", file=sys.stderr)

    head = [f'<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{html.escape(full)}</title>"]
    if desc := one(page_dir, "desc") or one(shell_dir, "desc"):
        head.append(f'<meta name="description" content="{html.escape(desc, quote=True)}">')
    if icon := one(shell_dir, "favicon"):
        head.append(f'<link rel="icon" href="{icon}">')
    for css in shell_dir.get("css", []):
        head.append(f'<link rel="stylesheet" href="{css}">')

    doc = Node("body")
    doc.attrs["data-suisou-root"] = None    # 初期設定（字面・地色・スクロールバー）だけ
    doc.children = graft(shell, page).children
    body: list[str] = []
    render(doc, body, 0)

    lang = one(shell_dir, "lang", "ja")
    return "\n".join([
        "<!DOCTYPE html>",
        f'<html lang="{lang}"{root_attrs}>',
        "<head>",
        *("  " + h for h in head),
        "</head>",
        *body,
        "</html>",
        "",
    ])


# ── 入口 ────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=Path("dist"))
    ap.add_argument("--vocab", type=Path, default=Path(__file__).resolve().parent / "vocab.json")
    args = ap.parse_args()

    vocab = Vocab(json.loads(args.vocab.read_text(encoding="utf-8")))

    shell_path = args.src / "index.txt"
    if not shell_path.exists():
        sys.exit(f"骨格が無い: {shell_path}")
    shell_dir, shell = Parser(vocab, shell_path).parse(shell_path.read_text(encoding="utf-8"))

    pages = sorted((args.src / "contents").glob("*.txt"))
    if not pages:
        sys.exit("contents/*.txt が無い")

    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True)

    for p in pages:
        page_dir, page = Parser(vocab, p).parse(p.read_text(encoding="utf-8"))
        name = "index" if p.stem == "home" else p.stem
        target = args.out / f"{name}.html"
        target.write_text(document(shell_dir, shell, page_dir, page, vocab), encoding="utf-8")
        print(f"{p} → {target}")

    img = args.src / "img"
    if img.is_dir():
        shutil.copytree(img, args.out / "img")
        print(f"{img} → {args.out / 'img'}")


if __name__ == "__main__":
    try:
        main()
    except BuildError as e:
        sys.exit(f"エラー … {e}")
